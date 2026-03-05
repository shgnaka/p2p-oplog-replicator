import unittest

from p2p_oplog_replicator.connectivity.session import Session, SessionManager
from p2p_oplog_replicator.connectivity.transport_bridge.bridge import TransportBridge
from p2p_oplog_replicator.protocol.messages import (
    MalformedMessageError,
    decode_message,
    encode_message,
)


class RecordingTransport:
    def __init__(self):
        self.sent = []

    def send(self, session_id: str, payload: bytes) -> None:
        self.sent.append((session_id, payload))


class ProtocolBridgeTests(unittest.TestCase):
    def test_encode_decode_roundtrip(self):
        message = {
            "type": "HELLO",
            "node_id": "n1",
            "protocol_version": "v1",
            "capabilities": ["sync"],
            "timestamp": "2026-03-05T00:00:00Z",
        }
        decoded = decode_message(encode_message(message))
        self.assertEqual(decoded["type"], "HELLO")

    def test_malformed_message_rejected(self):
        with self.assertRaises(MalformedMessageError):
            decode_message(b'{"type":"ACK"}')

    def test_bridge_send_broadcast_and_incoming(self):
        sessions = SessionManager()
        sessions.register_connected(Session(peer_id="p1", session_id="s1"))
        sessions.register_connected(Session(peer_id="p2", session_id="s2"))
        transport = RecordingTransport()
        bridge = TransportBridge(sessions=sessions, transport=transport)

        hello = {
            "type": "HELLO",
            "node_id": "n1",
            "protocol_version": "v1",
            "capabilities": ["sync"],
            "timestamp": "2026-03-05T00:00:00Z",
        }
        bridge.send("p1", hello)
        bridge.broadcast(hello, exclude_peers={"p1"})

        self.assertEqual([sid for sid, _ in transport.sent], ["s1", "s2"])

        ack = {
            "type": "ACK",
            "ack_for": "hello-1",
            "status": "ok",
            "timestamp": "2026-03-05T00:00:00Z",
        }
        incoming = bridge.handle_incoming("s1", encode_message(ack))
        self.assertEqual(incoming.peer_id, "p1")
        self.assertEqual(incoming.message["type"], "ACK")


if __name__ == "__main__":
    unittest.main()
