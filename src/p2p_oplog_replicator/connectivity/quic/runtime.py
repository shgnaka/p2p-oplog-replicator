from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass

from p2p_oplog_replicator.connectivity.quic.contracts import (
    IncomingMessageSink,
    PeerEndpoint,
    QuicTransport,
    WireEnvelope,
)
from p2p_oplog_replicator.connectivity.quic.framing import decode_frame, encode_frame
from p2p_oplog_replicator.connectivity.session import Session, SessionManager


@dataclass
class _SessionWire:
    peer_id: str
    session_id: str
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    recv_task: asyncio.Task | None = None


class AsyncioQuicTransport(QuicTransport):
    """Socket-backed transport runtime with HELLO/ACK handshake semantics.

    This provides real network interoperability on local TCP streams and is
    designed to be swappable with a full QUIC backend later.
    """

    def __init__(self, local_node_id: str, sessions: SessionManager, sink: IncomingMessageSink) -> None:
        self._local_node_id = local_node_id
        self._sessions = sessions
        self._sink = sink
        self._server: asyncio.AbstractServer | None = None
        self._session_by_id: dict[str, _SessionWire] = {}

    async def start(self, host: str, port: int) -> tuple[str, int]:
        self._server = await asyncio.start_server(self._handle_incoming_connection, host, port)
        sock = self._server.sockets[0]
        bound_host, bound_port = sock.getsockname()[:2]
        return str(bound_host), int(bound_port)

    async def stop(self) -> None:
        session_ids = list(self._session_by_id.keys())
        for session_id in session_ids:
            await self.disconnect(session_id, reason="transport-stop")
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def connect(self, endpoint: PeerEndpoint) -> str:
        reader, writer = await asyncio.open_connection(endpoint.host, endpoint.port)
        session_id = self._new_session_id(endpoint.peer_id)
        wire = _SessionWire(peer_id=endpoint.peer_id, session_id=session_id, reader=reader, writer=writer)

        hello = WireEnvelope(msg_type="HELLO", payload={"node_id": self._local_node_id})
        writer.write(encode_frame(hello))
        await writer.drain()

        ack_frame = await reader.readline()
        ack = decode_frame(ack_frame)
        if ack.msg_type != "ACK":
            writer.close()
            await writer.wait_closed()
            raise ValueError("expected ACK during handshake")

        self._register_wire(wire)
        return session_id

    async def send(self, session_id: str, envelope: WireEnvelope) -> None:
        wire = self._session_by_id[session_id]
        wire.writer.write(encode_frame(envelope))
        await wire.writer.drain()

    async def disconnect(self, session_id: str, reason: str) -> None:
        wire = self._session_by_id.pop(session_id, None)
        if wire is None:
            return
        if wire.recv_task is not None:
            wire.recv_task.cancel()
        if self._sessions.has_session(wire.peer_id):
            self._sessions.disconnect(wire.peer_id, reason=reason)
        wire.writer.close()
        await wire.writer.wait_closed()

    async def _handle_incoming_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        hello_raw = await reader.readline()
        hello = decode_frame(hello_raw)
        if hello.msg_type != "HELLO":
            writer.close()
            await writer.wait_closed()
            return

        peer_id = str(hello.payload["node_id"])
        session_id = self._new_session_id(peer_id)
        wire = _SessionWire(peer_id=peer_id, session_id=session_id, reader=reader, writer=writer)

        ack = WireEnvelope(msg_type="ACK", payload={"node_id": self._local_node_id})
        writer.write(encode_frame(ack))
        await writer.drain()

        self._register_wire(wire)

    def _register_wire(self, wire: _SessionWire) -> None:
        self._session_by_id[wire.session_id] = wire
        self._sessions.register_connected(Session(peer_id=wire.peer_id, session_id=wire.session_id))
        wire.recv_task = asyncio.create_task(self._recv_loop(wire))

    async def _recv_loop(self, wire: _SessionWire) -> None:
        try:
            while True:
                frame = await wire.reader.readline()
                if not frame:
                    break
                envelope = decode_frame(frame)
                if envelope.msg_type in {"HELLO", "ACK"}:
                    continue
                self._sink.on_message(wire.session_id, envelope)
        finally:
            if wire.session_id in self._session_by_id:
                await self.disconnect(wire.session_id, reason="peer-closed")

    @staticmethod
    def _new_session_id(peer_id: str) -> str:
        return f"{peer_id}:{uuid.uuid4().hex[:8]}"
