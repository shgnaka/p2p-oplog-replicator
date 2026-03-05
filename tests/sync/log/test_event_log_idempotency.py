import tempfile
import unittest
from pathlib import Path

from p2p_oplog_replicator.sync.errors import ValidationError
from p2p_oplog_replicator.sync.idempotency.index import EventIdempotencyIndex
from p2p_oplog_replicator.sync.log.event_log import AppendOnlyEventLog


class EventLogIdempotencyTests(unittest.TestCase):
    def test_append_only_log_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            log = AppendOnlyEventLog(Path(td) / "events.jsonl")
            log.append({"event_id": "e1", "value": 1})
            log.append({"event_id": "e2", "value": 2})
            self.assertEqual(log.count(), 2)
            self.assertEqual([e["event_id"] for e in log.read_all()], ["e1", "e2"])

    def test_idempotency_duplicate_is_noop(self):
        idx = EventIdempotencyIndex()
        event = {"event_id": "e1", "payload": {"v": 1}}
        self.assertTrue(idx.register(event))
        self.assertFalse(idx.register(event))

    def test_idempotency_conflict_raises(self):
        idx = EventIdempotencyIndex()
        idx.register({"event_id": "e1", "payload": {"v": 1}})
        with self.assertRaises(ValidationError) as err:
            idx.register({"event_id": "e1", "payload": {"v": 2}})
        self.assertEqual(err.exception.detail.code, "ERR_EVENT_ID_CONFLICT")


if __name__ == "__main__":
    unittest.main()
