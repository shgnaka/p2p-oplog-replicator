import random
import unittest

from p2p_oplog_replicator.connectivity.candidates import CandidateState, CandidateStore
from p2p_oplog_replicator.connectivity.dialer import ConnectError, DialScheduler, RetryPolicy
from p2p_oplog_replicator.connectivity.discovery import PeerCandidate
from p2p_oplog_replicator.connectivity.session import Session, SessionEventSink, SessionManager


class RecordingSink(SessionEventSink):
    def __init__(self):
        self.events = []

    def on_event(self, event):
        self.events.append(event)


class FakeConnector:
    def __init__(self, fail_times=0):
        self.fail_times = fail_times
        self.calls = 0

    def connect(self, candidate):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ConnectError("dial failed")
        return Session(peer_id=candidate.peer_id, session_id=f"s-{self.calls}")


class DialerSessionTests(unittest.TestCase):
    def test_scheduler_retries_and_then_connects(self):
        store = CandidateStore()
        peer = PeerCandidate("p1", "127.0.0.1:1", "dht")
        store.upsert_discovered(peer)
        store.transition("p1", CandidateState.QUEUED)

        connector = FakeConnector(fail_times=1)
        sessions = SessionManager()
        sink = RecordingSink()
        sessions.register_sink(sink)

        scheduler = DialScheduler(
            candidate_store=store,
            connector=connector,
            session_manager=sessions,
            retry_policy=RetryPolicy(base_delay_seconds=1.0, max_delay_seconds=2.0, jitter_ratio=0.0, max_retries=3),
            rng=random.Random(0),
        )

        scheduler.run_once(now_seconds=0.0)
        self.assertEqual(store.get("p1").state, CandidateState.QUEUED)
        scheduler.run_once(now_seconds=1.0)
        self.assertEqual(store.get("p1").state, CandidateState.CONNECTED)
        self.assertTrue(sessions.has_session("p1"))
        self.assertEqual(len(sink.events), 1)

    def test_scheduler_marks_dead_after_retry_cap(self):
        store = CandidateStore()
        peer = PeerCandidate("p2", "127.0.0.1:2", "dht")
        store.upsert_discovered(peer)
        store.transition("p2", CandidateState.QUEUED)

        scheduler = DialScheduler(
            candidate_store=store,
            connector=FakeConnector(fail_times=10),
            session_manager=SessionManager(),
            retry_policy=RetryPolicy(base_delay_seconds=1.0, max_delay_seconds=2.0, jitter_ratio=0.0, max_retries=2),
            rng=random.Random(0),
        )

        scheduler.run_once(now_seconds=0.0)
        self.assertEqual(store.get("p2").state, CandidateState.QUEUED)
        scheduler.run_once(now_seconds=1.0)
        self.assertEqual(store.get("p2").state, CandidateState.DEAD)

    def test_session_manager_emits_disconnect(self):
        sessions = SessionManager()
        sink = RecordingSink()
        sessions.register_sink(sink)

        sessions.register_connected(Session(peer_id="p3", session_id="s1"))
        disconnected = sessions.disconnect("p3", reason="peer-closed")

        self.assertTrue(disconnected)
        self.assertEqual([e.event_type.value for e in sink.events], ["connected", "disconnected"])

    def test_session_manager_disconnect_is_idempotent_for_missing_peer(self):
        sessions = SessionManager()
        sink = RecordingSink()
        sessions.register_sink(sink)

        disconnected = sessions.disconnect("unknown-peer", reason="missing")

        self.assertFalse(disconnected)
        self.assertEqual(sink.events, [])


if __name__ == "__main__":
    unittest.main()
