import base64
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from p2p_oplog_replicator.crypto.signature import Ed25519Verifier
from p2p_oplog_replicator.sync.errors import ValidationError
from p2p_oplog_replicator.sync.idempotency.index import EventIdempotencyIndex
from p2p_oplog_replicator.sync.materialized_view.store import MaterializedViewStore
from p2p_oplog_replicator.sync.validation import EventEnvelopeValidator


def _canonical_payload(event: dict) -> bytes:
    return json.dumps({k: v for k, v in event.items() if k != "signature"}, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sign(private_key: Ed25519PrivateKey, event: dict) -> dict:
    signed = dict(event)
    signed["signature"] = base64.b64encode(private_key.sign(_canonical_payload(signed))).decode("ascii")
    return signed


class E2SyncCoreFlowTests(unittest.TestCase):
    def test_validation_idempotency_and_lww_convergence(self):
        private = Ed25519PrivateKey.generate()
        public = private.public_key()
        keys = {"alice": base64.b64encode(public.public_bytes_raw()).decode("ascii")}

        validator = EventEnvelopeValidator(Ed25519Verifier(keys))
        idempotency = EventIdempotencyIndex()
        materialized = MaterializedViewStore()

        malformed = _sign(
            private,
            {
                "event_id": "bad-1",
                "event_version": "lww_v1",
                "merge_strategy": "lww_tombstone",
                "causal": {"type": "lamport_v1", "lamport": -1, "node_id": "n1"},
                "command_schema": "todo.v1",
                "command": {"op": "set", "key": "k", "value": "bad"},
                "author": "alice",
                "created_at": "2026-03-06T00:00:00Z",
            },
        )

        with self.assertRaises(ValidationError):
            validator.validate(malformed)

        e1 = _sign(
            private,
            {
                "event_id": "e1",
                "event_version": "lww_v1",
                "merge_strategy": "lww_tombstone",
                "causal": {"type": "lamport_v1", "lamport": 1, "node_id": "n1"},
                "command_schema": "todo.v1",
                "command": {"op": "set", "key": "k", "value": "v1"},
                "author": "alice",
                "created_at": "2026-03-06T00:00:01Z",
            },
        )
        e2_delete = _sign(
            private,
            {
                "event_id": "e2",
                "event_version": "lww_v1",
                "merge_strategy": "lww_tombstone",
                "causal": {"type": "lamport_v1", "lamport": 3, "node_id": "n1"},
                "command_schema": "todo.v1",
                "command": {"op": "delete", "key": "k"},
                "author": "alice",
                "created_at": "2026-03-06T00:00:02Z",
            },
        )
        e3_stale = _sign(
            private,
            {
                "event_id": "e3",
                "event_version": "lww_v1",
                "merge_strategy": "lww_tombstone",
                "causal": {"type": "lamport_v1", "lamport": 2, "node_id": "n1"},
                "command_schema": "todo.v1",
                "command": {"op": "set", "key": "k", "value": "stale"},
                "author": "alice",
                "created_at": "2026-03-06T00:00:03Z",
            },
        )

        applied_count = 0
        for event in [e1, e1, e2_delete, e3_stale]:
            validated = validator.validate(event).event
            if idempotency.register(validated):
                materialized.apply_event(validated)
                applied_count += 1

        self.assertEqual(applied_count, 3)
        self.assertIsNone(materialized.visible_value("k"))


if __name__ == "__main__":
    unittest.main()
