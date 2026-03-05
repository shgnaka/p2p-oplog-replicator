from __future__ import annotations

from typing import Protocol


class JsonLineAppendStore(Protocol):
    """Durable append store for JSON line entries."""

    def append_json_line(self, record: dict) -> None:
        ...

    def read_json_lines(self) -> list[dict]:
        ...


class AtomicJsonStore(Protocol):
    """Durable atomic snapshot store for JSON objects."""

    def load_json(self) -> dict:
        ...

    def store_json(self, payload: dict) -> None:
        ...
