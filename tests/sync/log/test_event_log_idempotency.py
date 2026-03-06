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

    def test_read_slice_supports_offset_and_limit(self):
        with tempfile.TemporaryDirectory() as td:
            log = AppendOnlyEventLog(Path(td) / "events.jsonl")
            for i in range(5):
                log.append({"event_id": f"e{i}", "value": i})

            window = log.read_slice(offset=1, limit=2)
            self.assertEqual([e["event_id"] for e in window], ["e1", "e2"])
            tail = log.read_slice(offset=3)
            self.assertEqual([e["event_id"] for e in tail], ["e3", "e4"])

    def test_read_slice_rejects_negative_offset_or_limit(self):
        with tempfile.TemporaryDirectory() as td:
            log = AppendOnlyEventLog(Path(td) / "events.jsonl")
            log.append({"event_id": "e1", "value": 1})
            with self.assertRaises(ValueError):
                log.read_slice(offset=-1)
            with self.assertRaises(ValueError):
                log.read_slice(offset=0, limit=-1)

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
