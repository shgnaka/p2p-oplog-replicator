import unittest

from p2p_oplog_replicator.persistence.contracts import AtomicJsonStore, JsonLineAppendStore


class ContractsSmokeTests(unittest.TestCase):
    def test_contracts_are_importable(self):
        # Runtime smoke only: confirms contract symbols are available.
        self.assertIsNotNone(JsonLineAppendStore)
        self.assertIsNotNone(AtomicJsonStore)


if __name__ == "__main__":
    unittest.main()
