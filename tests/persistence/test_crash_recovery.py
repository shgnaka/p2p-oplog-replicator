import json
import tempfile
import unittest
from pathlib import Path

from p2p_oplog_replicator.migration.quarantine.store import QuarantineRecord, QuarantineStore
from p2p_oplog_replicator.sync.idempotency.index import PersistentEventIdempotencyIndex
from p2p_oplog_replicator.sync.log.event_log import AppendOnlyEventLog


class CrashRecoveryTests(unittest.TestCase):
    def test_event_log_tolerates_truncated_trailing_line(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            log = AppendOnlyEventLog(path)
            log.append({"event_id": "e1", "payload": 1})
            with path.open("a", encoding="utf-8") as fh:
                fh.write('{"event_id":"broken"')

            reloaded = AppendOnlyEventLog(path)
            events = reloaded.read_all()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event_id"], "e1")

    def test_quarantine_store_tolerates_truncated_line(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "quarantine.jsonl"
            store = QuarantineStore(path)
            store.append(
                QuarantineRecord(
                    event_id="e1",
                    decision="QUARANTINE",
                    reason_code="Q_TEST",
                    adapter_version="v1",
                    captured_at="2026-03-05T00:00:00Z",
                    source_peer="p1",
                    explain="ok",
                    event_snapshot={"event_id": "e1"},
                )
            )
            with path.open("a", encoding="utf-8") as fh:
                fh.write('{"event_id":"broken"')

            reloaded = QuarantineStore(path)
            records = reloaded.read_all()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].event_id, "e1")

    def test_persistent_index_recovers_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "index.json"
            idx = PersistentEventIdempotencyIndex(path)
            idx.register({"event_id": "e1", "payload": {"v": 1}})

            # Simulate restart.
            idx2 = PersistentEventIdempotencyIndex(path)
            self.assertTrue(idx2.has("e1"))

    def test_persistent_index_ignores_corrupt_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "index.json"
            path.write_text('{"records":', encoding="utf-8")
            idx = PersistentEventIdempotencyIndex(path)
            self.assertFalse(idx.has("e1"))
            idx.register({"event_id": "e1", "payload": {"v": 1}})
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("e1", raw["records"])


if __name__ == "__main__":
    unittest.main()
