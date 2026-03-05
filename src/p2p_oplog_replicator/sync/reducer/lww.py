from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventClock:
    lamport: int
    author: str


@dataclass(frozen=True)
class EntityRecord:
    key: str
    value: object | None
    tombstone: bool
    clock: EventClock


class LwwTombstoneReducer:
    """Deterministic LWW reducer with tombstone semantics."""

    def choose_winner(self, current: EntityRecord | None, incoming: EntityRecord) -> EntityRecord:
        if current is None:
            return incoming
        if self._clock_gt(incoming.clock, current.clock):
            return incoming
        return current

    @staticmethod
    def _clock_gt(a: EventClock, b: EventClock) -> bool:
        # Deterministic tie-break: higher lamport first, then lexical author.
        return (a.lamport, a.author) > (b.lamport, b.author)
