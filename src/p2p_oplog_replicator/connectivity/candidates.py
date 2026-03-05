from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from p2p_oplog_replicator.connectivity.discovery import PeerCandidate


class CandidateState(str, Enum):
    DISCOVERED = "discovered"
    QUEUED = "queued"
    DIALING = "dialing"
    CONNECTED = "connected"
    FAILED = "failed"
    DEAD = "dead"


@dataclass(frozen=True)
class CandidateRecord:
    candidate: PeerCandidate
    state: CandidateState
    fail_count: int = 0


class CandidateStore:
    """State machine for peer candidate lifecycle."""

    def __init__(self) -> None:
        self._records: dict[str, CandidateRecord] = {}

    def upsert_discovered(self, candidate: PeerCandidate) -> CandidateRecord:
        existing = self._records.get(candidate.peer_id)
        if existing is None:
            record = CandidateRecord(candidate=candidate, state=CandidateState.DISCOVERED)
            self._records[candidate.peer_id] = record
            return record
        # Keep previous state unless candidate was marked dead.
        if existing.state == CandidateState.DEAD:
            return existing
        updated = replace(existing, candidate=candidate)
        self._records[candidate.peer_id] = updated
        return updated

    def transition(self, peer_id: str, next_state: CandidateState) -> CandidateRecord:
        current = self._records[peer_id]
        allowed = {
            CandidateState.DISCOVERED: {CandidateState.QUEUED, CandidateState.DEAD},
            CandidateState.QUEUED: {CandidateState.DIALING, CandidateState.DEAD},
            CandidateState.DIALING: {
                CandidateState.CONNECTED,
                CandidateState.FAILED,
                CandidateState.DEAD,
            },
            CandidateState.CONNECTED: {CandidateState.FAILED, CandidateState.DEAD},
            CandidateState.FAILED: {
                CandidateState.QUEUED,
                CandidateState.DIALING,
                CandidateState.DEAD,
            },
            CandidateState.DEAD: set(),
        }
        if next_state not in allowed[current.state]:
            raise ValueError(f"invalid transition: {current.state.value} -> {next_state.value}")

        fail_count = current.fail_count + 1 if next_state == CandidateState.FAILED else current.fail_count
        if next_state == CandidateState.CONNECTED:
            fail_count = 0
        updated = replace(current, state=next_state, fail_count=fail_count)
        self._records[peer_id] = updated
        return updated

    def get(self, peer_id: str) -> CandidateRecord:
        return self._records[peer_id]

    def list_for_dial(self) -> list[CandidateRecord]:
        return sorted(
            (r for r in self._records.values() if r.state in {CandidateState.QUEUED, CandidateState.FAILED}),
            key=lambda r: (r.fail_count, r.candidate.peer_id),
        )

    def list_by_state(self, state: CandidateState) -> list[CandidateRecord]:
        return sorted(
            (r for r in self._records.values() if r.state == state),
            key=lambda r: r.candidate.peer_id,
        )
