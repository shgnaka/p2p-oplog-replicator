from __future__ import annotations

import json
import os
from pathlib import Path

from p2p_oplog_replicator.persistence.contracts import AtomicJsonStore, JsonLineAppendStore


def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _fsync_file(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_dir(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class DurableJsonLineFileStore(JsonLineAppendStore):
    """JSONL append store with flush+fsync and trailing-corruption tolerance."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

    def append_json_line(self, record: dict) -> None:
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(_canonical_json(record) + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    def read_json_lines(self) -> list[dict]:
        rows: list[dict] = []
        with self._path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    # Tolerate truncated trailing line on crash.
                    continue
        return rows


class DurableAtomicJsonFileStore(AtomicJsonStore):
    """Atomic JSON snapshot store using temp-file + os.replace + fsync(dir)."""

    def __init__(self, path: Path, default_payload: dict | None = None) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._default = default_payload or {}
        if not self._path.exists():
            self.store_json(self._default)

    def load_json(self) -> dict:
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return dict(self._default)

    def store_json(self, payload: dict) -> None:
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(_canonical_json(payload), encoding="utf-8")
        _fsync_file(tmp)
        os.replace(tmp, self._path)
        _fsync_dir(self._path.parent)
