import asyncio
import unittest

from p2p_oplog_replicator.connectivity.quic.contracts import PeerEndpoint, WireEnvelope
from p2p_oplog_replicator.connectivity.quic.runtime import AsyncioQuicTransport
from p2p_oplog_replicator.connectivity.session import SessionManager


class Sink:
    def __init__(self):
        self.messages = []

    def on_message(self, session_id: str, envelope: WireEnvelope) -> None:
        self.messages.append((session_id, envelope))


class RuntimeUnitTests(unittest.IsolatedAsyncioTestCase):
    async def test_two_node_handshake_and_message(self):
        sink_a = Sink()
        sink_b = Sink()
        sessions_a = SessionManager()
        sessions_b = SessionManager()

        a = AsyncioQuicTransport("node-a", sessions_a, sink_a)
        b = AsyncioQuicTransport("node-b", sessions_b, sink_b)

        host_b, port_b = await b.start("127.0.0.1", 0)
        await a.start("127.0.0.1", 0)

        sid_a = await a.connect(PeerEndpoint(peer_id="node-b", host=host_b, port=port_b))
        await asyncio.sleep(0.05)
        await a.send(sid_a, WireEnvelope(msg_type="PUSH", payload={"x": 1}))
        await asyncio.sleep(0.05)

        self.assertTrue(sessions_a.has_session("node-b"))
        self.assertTrue(sessions_b.has_session("node-a"))
        self.assertEqual(len(sink_b.messages), 1)
        self.assertEqual(sink_b.messages[0][1].msg_type, "PUSH")

        await a.disconnect(sid_a, reason="test-close")
        await asyncio.sleep(0.05)
        self.assertFalse(sessions_a.has_session("node-b"))

        await a.stop()
        await b.stop()


if __name__ == "__main__":
    unittest.main()
