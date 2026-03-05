from __future__ import annotations

import json
from pathlib import Path


class AppendOnlyEventLog:
    """Simple JSONL append-only log for validated events."""

    def __init__(self, file_path: Path) -> None:
        self._path = file_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append(self, event: dict) -> int:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        return self.count()

    def read_all(self) -> list[dict]:
        out: list[dict] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                out.append(json.loads(line))
        return out

    def count(self) -> int:
        with self._path.open("r", encoding="utf-8") as fh:
            return sum(1 for _ in fh)
