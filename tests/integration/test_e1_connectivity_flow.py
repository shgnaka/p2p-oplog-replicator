import random
import unittest

from p2p_oplog_replicator.connectivity.candidates import CandidateState, CandidateStore
from p2p_oplog_replicator.connectivity.dialer import ConnectError, DialScheduler, RetryPolicy
from p2p_oplog_replicator.connectivity.discovery import DiscoveryCoordinator, DiscoveryProvider, PeerCandidate
from p2p_oplog_replicator.connectivity.session import Session, SessionManager
from p2p_oplog_replicator.protocol.messages import decode_message, encode_message


class StaticProvider(DiscoveryProvider):
    def __init__(self, candidates):
        self._candidates = candidates

    def discover(self):
        return list(self._candidates)


class FlakyConnector:
    def __init__(self):
        self.calls = 0

    def connect(self, candidate):
        self.calls += 1
        if self.calls == 1:
            raise ConnectError("transient failure")
        return Session(peer_id=candidate.peer_id, session_id=f"session-{self.calls}")


class E1ConnectivityFlowTests(unittest.TestCase):
    def test_discovery_to_retry_to_connected_and_message_contract(self):
        coordinator = DiscoveryCoordinator()
        coordinator.register_provider(
            StaticProvider([
                PeerCandidate("peer-a", "10.0.0.1:1", "dht"),
                PeerCandidate("peer-b", "10.0.0.2:1", "dht"),
            ])
        )
        coordinator.register_provider(
            StaticProvider([
                PeerCandidate("peer-a", "10.0.9.9:1", "pex"),
            ])
        )

        discovered = coordinator.poll()
        self.assertEqual([p.peer_id for p in discovered], ["peer-a", "peer-b"])

        store = CandidateStore()
        for candidate in discovered:
            store.upsert_discovered(candidate)
            store.transition(candidate.peer_id, CandidateState.QUEUED)

        sessions = SessionManager()
        scheduler = DialScheduler(
            candidate_store=store,
            connector=FlakyConnector(),
            session_manager=sessions,
            retry_policy=RetryPolicy(base_delay_seconds=1.0, max_delay_seconds=2.0, jitter_ratio=0.0, max_retries=3),
            rng=random.Random(0),
        )

        scheduler.run_once(now_seconds=0.0)
        scheduler.run_once(now_seconds=1.0)

        self.assertTrue(sessions.has_session("peer-a"))

        request = {
            "type": "REQUEST",
            "request_id": "recovery-1",
            "cursor": "cursor-1",
            "limit": 10,
            "timestamp": "2026-03-06T00:00:00Z",
        }
        decoded = decode_message(encode_message(request))
        self.assertEqual(decoded["type"], "REQUEST")


if __name__ == "__main__":
    unittest.main()
