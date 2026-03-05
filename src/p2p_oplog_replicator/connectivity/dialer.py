from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol

from p2p_oplog_replicator.connectivity.candidates import CandidateState, CandidateStore
from p2p_oplog_replicator.connectivity.discovery import PeerCandidate
from p2p_oplog_replicator.connectivity.session import Session, SessionManager


class ConnectError(Exception):
    pass


class QuicConnector(Protocol):
    def connect(self, candidate: PeerCandidate) -> Session:
        ...


@dataclass(frozen=True)
class RetryPolicy:
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 8.0
    jitter_ratio: float = 0.1
    max_retries: int = 3

    def delay_seconds(self, fail_count: int, rng: random.Random) -> float:
        exp = min(self.base_delay_seconds * (2 ** max(fail_count - 1, 0)), self.max_delay_seconds)
        jitter = exp * self.jitter_ratio
        return exp + rng.uniform(-jitter, jitter)


class DialScheduler:
    """Attempts dials and applies retry/backoff transitions."""

    def __init__(
        self,
        candidate_store: CandidateStore,
        connector: QuicConnector,
        session_manager: SessionManager,
        retry_policy: RetryPolicy | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self._store = candidate_store
        self._connector = connector
        self._sessions = session_manager
        self._policy = retry_policy or RetryPolicy()
        self._rng = rng or random.Random(0)
        self._next_retry_at: dict[str, float] = {}

    def run_once(self, now_seconds: float) -> None:
        for record in self._store.list_for_dial():
            peer_id = record.candidate.peer_id
            next_allowed = self._next_retry_at.get(peer_id, 0.0)
            if now_seconds < next_allowed:
                continue

            if record.state == CandidateState.FAILED:
                self._store.transition(peer_id, CandidateState.QUEUED)
            self._store.transition(peer_id, CandidateState.DIALING)

            try:
                session = self._connector.connect(record.candidate)
            except ConnectError:
                failed = self._store.transition(peer_id, CandidateState.FAILED)
                if failed.fail_count >= self._policy.max_retries:
                    self._store.transition(peer_id, CandidateState.DEAD)
                    self._next_retry_at.pop(peer_id, None)
                else:
                    self._store.transition(peer_id, CandidateState.QUEUED)
                    delay = self._policy.delay_seconds(failed.fail_count, self._rng)
                    self._next_retry_at[peer_id] = now_seconds + delay
                continue

            self._store.transition(peer_id, CandidateState.CONNECTED)
            self._next_retry_at.pop(peer_id, None)
            self._sessions.register_connected(session)
