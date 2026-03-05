from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from p2p_oplog_replicator.connectivity.session import SessionManager
from p2p_oplog_replicator.protocol.messages import decode_message, encode_message


class Transport(Protocol):
    def send(self, session_id: str, payload: bytes) -> None:
        ...


@dataclass(frozen=True)
class ReceivedMessage:
    peer_id: str
    session_id: str
    message: dict


class TransportBridge:
    def __init__(self, sessions: SessionManager, transport: Transport) -> None:
        self._sessions = sessions
        self._transport = transport

    def send(self, peer_id: str, message: dict) -> None:
        session = self._sessions.get_session(peer_id)
        self._transport.send(session.session_id, encode_message(message))

    def broadcast(self, message: dict, exclude_peers: set[str] | None = None) -> None:
        excluded = exclude_peers or set()
        payload = encode_message(message)
        for session in self._sessions.list_sessions():
            if session.peer_id in excluded:
                continue
            self._transport.send(session.session_id, payload)

    def request_recovery(self, peer_id: str, cursor: str, limit: int, timestamp: str) -> None:
        request = {
            "type": "REQUEST",
            "request_id": f"recovery:{peer_id}:{cursor}",
            "cursor": cursor,
            "limit": limit,
            "timestamp": timestamp,
        }
        self.send(peer_id, request)

    def handle_incoming(self, session_id: str, payload: bytes) -> ReceivedMessage:
        session = self._sessions.find_by_session_id(session_id)
        if session is None:
            raise KeyError(f"unknown session_id: {session_id}")
        return ReceivedMessage(
            peer_id=session.peer_id,
            session_id=session_id,
            message=decode_message(payload),
        )
