from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from p2p_oplog_replicator.persistence.file_backend import DurableJsonLineFileStore


@dataclass(frozen=True)
class QuarantineRecord:
    event_id: str
    decision: str
    reason_code: str
    adapter_version: str
    captured_at: str
    source_peer: str
    explain: str
    event_snapshot: dict


class QuarantineStore:
    def __init__(self, path: Path) -> None:
        self._store = DurableJsonLineFileStore(path)

    def append(self, record: QuarantineRecord) -> None:
        self._store.append_json_line(asdict(record))

    def read_all(self) -> list[QuarantineRecord]:
        out: list[QuarantineRecord] = []
        for raw in self._store.read_json_lines():
            out.append(QuarantineRecord(**raw))
        return out

    def count(self) -> int:
        return len(self._store.read_json_lines())

    def count_by_reason(self) -> dict[str, int]:
        rows = self._store.read_json_lines()
        counter = Counter(str(row.get("reason_code", "")) for row in rows)
        return dict(sorted(counter.items()))

    def filter_by_reason(self, reason_code: str) -> list[QuarantineRecord]:
        return [record for record in self.read_all() if record.reason_code == reason_code]
