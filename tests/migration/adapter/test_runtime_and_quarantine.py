import tempfile
import unittest
from pathlib import Path

from p2p_oplog_replicator.migration.adapter.runtime import LwwToCrdtAdapter
from p2p_oplog_replicator.migration.quarantine.store import QuarantineRecord, QuarantineStore


def make_event(**overrides):
    event = {
        "event_id": "e1",
        "event_version": "lww_v1",
        "command_schema": "todo.v1",
        "command": {"op": "set", "key": "k", "value": "v"},
        "causal": {"lamport": 1, "node_id": "n1"},
    }
    event.update(overrides)
    return event


class AdapterAndQuarantineTests(unittest.TestCase):
    def test_convert_supported_event(self):
        decision = LwwToCrdtAdapter().convert(make_event())
        self.assertEqual(decision.decision, "APPLY")
        self.assertEqual(len(decision.crdt_ops), 1)

    def test_quarantine_unsupported_schema(self):
        decision = LwwToCrdtAdapter().convert(make_event(command_schema="unknown.v1"))
        self.assertEqual(decision.decision, "QUARANTINE")
        self.assertEqual(decision.reason_code, "Q_UNSUPPORTED_SCHEMA")

    def test_quarantine_invalid_lamport_clock(self):
        decision = LwwToCrdtAdapter().convert(make_event(causal={"lamport": -1, "node_id": "n1"}))
        self.assertEqual(decision.decision, "QUARANTINE")
        self.assertEqual(decision.reason_code, "Q_INVALID_CAUSAL_CLOCK")

    def test_quarantine_missing_command_key(self):
        decision = LwwToCrdtAdapter().convert(make_event(command={"op": "set", "value": "v"}))
        self.assertEqual(decision.decision, "QUARANTINE")
        self.assertEqual(decision.reason_code, "Q_MISSING_COMMAND_KEY")

    def test_quarantine_unsupported_command_op(self):
        decision = LwwToCrdtAdapter().convert(make_event(command={"op": "merge", "key": "k"}))
        self.assertEqual(decision.decision, "QUARANTINE")
        self.assertEqual(decision.reason_code, "Q_UNSUPPORTED_COMMAND_OP")

    def test_quarantine_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            store = QuarantineStore(Path(td) / "q.jsonl")
            record = QuarantineRecord(
                event_id="e2",
                decision="QUARANTINE",
                reason_code="Q_NON_CONVERTIBLE_COMMAND",
                adapter_version="adapter_v1",
                captured_at="2026-03-05T00:00:00Z",
                source_peer="p1",
                explain="bad op",
                event_snapshot={"event_id": "e2"},
            )
            store.append(record)
            loaded = store.read_all()
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].reason_code, "Q_NON_CONVERTIBLE_COMMAND")

    def test_quarantine_store_reason_aggregation(self):
        with tempfile.TemporaryDirectory() as td:
            store = QuarantineStore(Path(td) / "q.jsonl")
            store.append(
                QuarantineRecord(
                    event_id="e1",
                    decision="QUARANTINE",
                    reason_code="Q_UNSUPPORTED_SCHEMA",
                    adapter_version="adapter_v1",
                    captured_at="2026-03-05T00:00:00Z",
                    source_peer="p1",
                    explain="schema",
                    event_snapshot={"event_id": "e1"},
                )
            )
            store.append(
                QuarantineRecord(
                    event_id="e2",
                    decision="QUARANTINE",
                    reason_code="Q_UNSUPPORTED_SCHEMA",
                    adapter_version="adapter_v1",
                    captured_at="2026-03-05T00:00:01Z",
                    source_peer="p2",
                    explain="schema",
                    event_snapshot={"event_id": "e2"},
                )
            )
            store.append(
                QuarantineRecord(
                    event_id="e3",
                    decision="QUARANTINE",
                    reason_code="Q_UNSUPPORTED_COMMAND_OP",
                    adapter_version="adapter_v1",
                    captured_at="2026-03-05T00:00:02Z",
                    source_peer="p3",
                    explain="op",
                    event_snapshot={"event_id": "e3"},
                )
            )

            self.assertEqual(store.count(), 3)
            self.assertEqual(
                store.count_by_reason(),
                {
                    "Q_UNSUPPORTED_COMMAND_OP": 1,
                    "Q_UNSUPPORTED_SCHEMA": 2,
                },
            )
            filtered = store.filter_by_reason("Q_UNSUPPORTED_SCHEMA")
            self.assertEqual(len(filtered), 2)


if __name__ == "__main__":
    unittest.main()
