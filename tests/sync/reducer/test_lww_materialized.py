import unittest

from p2p_oplog_replicator.sync.materialized_view.store import MaterializedViewStore


def event(event_id: str, lamport: int, author: str, op: str, key: str, value=None):
    return {
        "event_id": event_id,
        "author": author,
        "causal": {"lamport": lamport},
        "command": {"op": op, "key": key, "value": value},
    }


class LwwMaterializedTests(unittest.TestCase):
    def test_lww_higher_lamport_wins(self):
        store = MaterializedViewStore()
        store.apply_event(event("e1", lamport=1, author="alice", op="set", key="k", value="v1"))
        store.apply_event(event("e2", lamport=2, author="bob", op="set", key="k", value="v2"))
        self.assertEqual(store.visible_value("k"), "v2")

    def test_tie_break_by_author(self):
        store = MaterializedViewStore()
        store.apply_event(event("e1", lamport=3, author="alice", op="set", key="k", value="a"))
        store.apply_event(event("e2", lamport=3, author="bob", op="set", key="k", value="b"))
        self.assertEqual(store.visible_value("k"), "b")

    def test_tombstone_prevents_stale_replay_resurrection(self):
        store = MaterializedViewStore()
        store.apply_event(event("e1", lamport=2, author="alice", op="set", key="k", value="live"))
        store.apply_event(event("e2", lamport=3, author="alice", op="delete", key="k"))
        store.apply_event(event("e3", lamport=1, author="alice", op="set", key="k", value="stale"))
        self.assertIsNone(store.visible_value("k"))


if __name__ == "__main__":
    unittest.main()
