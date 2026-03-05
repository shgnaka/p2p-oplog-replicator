import unittest

from p2p_oplog_replicator.connectivity.candidates import CandidateState, CandidateStore
from p2p_oplog_replicator.connectivity.discovery import (
    DiscoveryCoordinator,
    DiscoveryProvider,
    PeerCandidate,
)


class StaticProvider(DiscoveryProvider):
    def __init__(self, candidates):
        self._candidates = candidates

    def discover(self):
        return list(self._candidates)


class DiscoveryCandidateTests(unittest.TestCase):
    def test_coordinator_collects_from_all_providers(self):
        coordinator = DiscoveryCoordinator()
        coordinator.register_provider(StaticProvider([PeerCandidate("p1", "a1", "dht")]))
        coordinator.register_provider(StaticProvider([PeerCandidate("p2", "a2", "pex")]))

        found = coordinator.poll()

        self.assertEqual([c.peer_id for c in found], ["p1", "p2"])

    def test_candidate_lifecycle_transitions(self):
        store = CandidateStore()
        store.upsert_discovered(PeerCandidate("p1", "127.0.0.1:1", "dht"))

        store.transition("p1", CandidateState.QUEUED)
        store.transition("p1", CandidateState.DIALING)
        failed = store.transition("p1", CandidateState.FAILED)
        self.assertEqual(failed.fail_count, 1)

        store.transition("p1", CandidateState.QUEUED)
        store.transition("p1", CandidateState.DIALING)
        connected = store.transition("p1", CandidateState.CONNECTED)
        self.assertEqual(connected.fail_count, 0)

    def test_list_for_dial_prioritizes_lower_fail_count(self):
        store = CandidateStore()
        store.upsert_discovered(PeerCandidate("p1", "addr1", "dht"))
        store.upsert_discovered(PeerCandidate("p2", "addr2", "dht"))

        store.transition("p1", CandidateState.QUEUED)
        store.transition("p2", CandidateState.QUEUED)
        store.transition("p2", CandidateState.DIALING)
        store.transition("p2", CandidateState.FAILED)

        queue = store.list_for_dial()
        self.assertEqual([r.candidate.peer_id for r in queue], ["p1", "p2"])


if __name__ == "__main__":
    unittest.main()
