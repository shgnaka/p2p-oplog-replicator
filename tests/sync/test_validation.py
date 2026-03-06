import base64
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from p2p_oplog_replicator.crypto.signature import Ed25519Verifier
from p2p_oplog_replicator.sync.errors import ValidationError
from p2p_oplog_replicator.sync.validation import EventEnvelopeValidator


def canonical_payload(event: dict) -> bytes:
    return json.dumps({k: v for k, v in event.items() if k != "signature"}, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ValidationTests(unittest.TestCase):
    def setUp(self):
        private = Ed25519PrivateKey.generate()
        public = private.public_key()
        self._private = private
        self._member_keys = {"alice": base64.b64encode(public.public_bytes_raw()).decode("ascii")}

    def signed_event(self) -> dict:
        event = {
            "event_id": "e1",
            "event_version": "lww_v1",
            "merge_strategy": "lww_tombstone",
            "causal": {"type": "lamport_v1", "lamport": 1, "node_id": "n1"},
            "command_schema": "todo.v1",
            "command": {"op": "set", "key": "k", "value": "v"},
            "author": "alice",
            "created_at": "2026-03-05T00:00:00Z",
        }
        sig = self._private.sign(canonical_payload(event))
        event["signature"] = base64.b64encode(sig).decode("ascii")
        return event

    def test_valid_event_passes(self):
        validator = EventEnvelopeValidator(Ed25519Verifier(self._member_keys))
        validated = validator.validate(self.signed_event())
        self.assertTrue(validated.canonical_payload)

    def test_invalid_signature_fails(self):
        event = self.signed_event()
        event["signature"] = base64.b64encode(b"invalid").decode("ascii")
        validator = EventEnvelopeValidator(Ed25519Verifier(self._member_keys))
        with self.assertRaises(ValidationError) as err:
            validator.validate(event)
        self.assertEqual(err.exception.detail.code, "ERR_SIG_INVALID")

    def test_missing_field_fails(self):
        event = self.signed_event()
        event.pop("event_id")
        validator = EventEnvelopeValidator(Ed25519Verifier(self._member_keys))
        with self.assertRaises(ValidationError) as err:
            validator.validate(event)
        self.assertEqual(err.exception.detail.code, "ERR_SCHEMA_UNKNOWN")

    def test_invalid_causal_lamport_fails(self):
        event = self.signed_event()
        event["causal"]["lamport"] = -1
        event["signature"] = base64.b64encode(self._private.sign(canonical_payload(event))).decode("ascii")
        validator = EventEnvelopeValidator(Ed25519Verifier(self._member_keys))
        with self.assertRaises(ValidationError):
            validator.validate(event)

    def test_invalid_command_op_fails(self):
        event = self.signed_event()
        event["command"]["op"] = "upsert"
        event["signature"] = base64.b64encode(self._private.sign(canonical_payload(event))).decode("ascii")
        validator = EventEnvelopeValidator(Ed25519Verifier(self._member_keys))
        with self.assertRaises(ValidationError):
            validator.validate(event)

    def test_set_without_value_fails(self):
        event = self.signed_event()
        event["command"].pop("value")
        event["signature"] = base64.b64encode(self._private.sign(canonical_payload(event))).decode("ascii")
        validator = EventEnvelopeValidator(Ed25519Verifier(self._member_keys))
        with self.assertRaises(ValidationError):
            validator.validate(event)


if __name__ == "__main__":
    unittest.main()
