from __future__ import annotations

from pathlib import Path

from p2p_oplog_replicator.persistence.file_backend import DurableJsonLineFileStore


class AppendOnlyEventLog:
    """Durable append-only JSONL log for validated events."""

    def __init__(self, file_path: Path) -> None:
        self._store = DurableJsonLineFileStore(file_path)

    def append(self, event: dict) -> int:
        self._store.append_json_line(event)
        return self.count()

    def read_all(self) -> list[dict]:
        return self._store.read_json_lines()

    def count(self) -> int:
        return len(self.read_all())
