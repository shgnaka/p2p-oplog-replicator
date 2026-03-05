import unittest

from p2p_oplog_replicator.connectivity.quic.contracts import WireEnvelope
from p2p_oplog_replicator.connectivity.quic.framing import FrameError, decode_frame, encode_frame


class FramingTests(unittest.TestCase):
    def test_encode_decode_roundtrip(self):
        envelope = WireEnvelope(msg_type="HELLO", payload={"node_id": "n1"})
        decoded = decode_frame(encode_frame(envelope))
        self.assertEqual(decoded.msg_type, "HELLO")
        self.assertEqual(decoded.payload["node_id"], "n1")

    def test_decode_invalid_structure(self):
        with self.assertRaises(FrameError):
            decode_frame(b'{"type":"HELLO"}\n')


if __name__ == "__main__":
    unittest.main()
