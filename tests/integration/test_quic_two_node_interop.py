import asyncio
import unittest

from p2p_oplog_replicator.connectivity.quic.contracts import PeerEndpoint, WireEnvelope
from p2p_oplog_replicator.connectivity.quic.runtime import AsyncioQuicTransport
from p2p_oplog_replicator.connectivity.session import SessionEventSink, SessionManager


class RecordingSink:
    def __init__(self):
        self.messages = []

    def on_message(self, session_id: str, envelope: WireEnvelope) -> None:
        self.messages.append((session_id, envelope))


class RecordingSessionSink(SessionEventSink):
    def __init__(self):
        self.events = []

    def on_event(self, event) -> None:
        self.events.append(event)


class TwoNodeInteropTests(unittest.IsolatedAsyncioTestCase):
    async def test_connect_send_disconnect_reconnect(self):
        sessions_a = SessionManager()
        sessions_b = SessionManager()
        ses_sink_a = RecordingSessionSink()
        ses_sink_b = RecordingSessionSink()
        sessions_a.register_sink(ses_sink_a)
        sessions_b.register_sink(ses_sink_b)

        msg_sink_a = RecordingSink()
        msg_sink_b = RecordingSink()

        node_a = AsyncioQuicTransport("node-a", sessions_a, msg_sink_a)
        node_b = AsyncioQuicTransport("node-b", sessions_b, msg_sink_b)

        host_b, port_b = await node_b.start("127.0.0.1", 0)
        await node_a.start("127.0.0.1", 0)

        sid_1 = await node_a.connect(PeerEndpoint(peer_id="node-b", host=host_b, port=port_b))
        await asyncio.sleep(0.05)
        await node_a.send(sid_1, WireEnvelope(msg_type="PUSH", payload={"step": 1}))
        await asyncio.sleep(0.05)

        self.assertTrue(sessions_a.has_session("node-b"))
        self.assertTrue(sessions_b.has_session("node-a"))
        self.assertEqual(msg_sink_b.messages[-1][1].payload["step"], 1)

        await node_a.disconnect(sid_1, reason="test-disconnect")
        await asyncio.sleep(0.05)
        self.assertFalse(sessions_a.has_session("node-b"))

        sid_2 = await node_a.connect(PeerEndpoint(peer_id="node-b", host=host_b, port=port_b))
        await asyncio.sleep(0.05)
        await node_a.send(sid_2, WireEnvelope(msg_type="PUSH", payload={"step": 2}))
        await asyncio.sleep(0.05)

        self.assertNotEqual(sid_1, sid_2)
        self.assertEqual(msg_sink_b.messages[-1][1].payload["step"], 2)

        event_types_a = [e.event_type.value for e in ses_sink_a.events]
        event_types_b = [e.event_type.value for e in ses_sink_b.events]
        self.assertGreaterEqual(event_types_a.count("connected"), 2)
        self.assertGreaterEqual(event_types_a.count("disconnected"), 1)
        self.assertGreaterEqual(event_types_b.count("connected"), 2)

        await node_a.stop()
        await node_b.stop()


if __name__ == "__main__":
    unittest.main()
