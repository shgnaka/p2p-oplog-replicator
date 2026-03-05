from __future__ import annotations

from dataclasses import dataclass

from p2p_oplog_replicator.sync.reducer.lww import EntityRecord, EventClock, LwwTombstoneReducer


@dataclass(frozen=True)
class ApplyResult:
    key: str
    changed: bool
    tombstone: bool


class MaterializedViewStore:
    """Applies LWW+tombstone records and exposes current visible state."""

    def __init__(self, reducer: LwwTombstoneReducer | None = None) -> None:
        self._reducer = reducer or LwwTombstoneReducer()
        self._records: dict[str, EntityRecord] = {}

    def apply_event(self, event: dict) -> ApplyResult:
        command = event["command"]
        key = command["key"]
        op = command["op"]
        value = command.get("value")

        incoming = EntityRecord(
            key=key,
            value=None if op == "delete" else value,
            tombstone=(op == "delete"),
            clock=EventClock(lamport=event["causal"]["lamport"], author=event["author"]),
        )

        current = self._records.get(key)
        winner = self._reducer.choose_winner(current=current, incoming=incoming)
        changed = winner != current
        self._records[key] = winner
        return ApplyResult(key=key, changed=changed, tombstone=winner.tombstone)

    def visible_value(self, key: str):
        record = self._records.get(key)
        if record is None or record.tombstone:
            return None
        return record.value

    def record(self, key: str) -> EntityRecord | None:
        return self._records.get(key)
