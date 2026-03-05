from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


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
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append(self, record: QuarantineRecord) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) + "\n")

    def read_all(self) -> list[QuarantineRecord]:
        out: list[QuarantineRecord] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                out.append(QuarantineRecord(**raw))
        return out
