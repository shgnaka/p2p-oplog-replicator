import json
import tempfile
import unittest
from pathlib import Path

from tools.harness.report import write_result_json
from tools.harness.runner import ScenarioRunner
from tools.harness.scenario import from_dict


class HarnessTests(unittest.TestCase):
    def test_runner_is_seed_reproducible(self):
        scenario = from_dict(
            {
                "scenario_id": "H-01",
                "seed": 7,
                "node_count": 3,
                "network_profile": "lan",
                "duration_steps": 3,
                "events": [{"id": "e1"}, {"id": "e2"}, {"id": "e3"}],
            }
        )
        runner = ScenarioRunner()
        a = runner.run(scenario)
        b = runner.run(scenario)
        self.assertEqual(a.final_state_hash_by_node, b.final_state_hash_by_node)
        self.assertEqual(a.assertions, b.assertions)

    def test_report_output_contains_required_fields(self):
        scenario = from_dict(
            {
                "scenario_id": "H-02",
                "seed": 1,
                "node_count": 2,
                "network_profile": "nat",
                "duration_steps": 1,
                "events": [{"id": "e1", "quarantine": True, "reason_code": "Q_UNSUPPORTED_SCHEMA"}],
            }
        )
        result = ScenarioRunner().run(scenario)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "result.json"
            write_result_json(result, path)
            raw = json.loads(path.read_text(encoding="utf-8"))
        for key in [
            "scenario_id",
            "seed",
            "node_count",
            "success",
            "assertions",
            "final_state_hash_by_node",
            "conversion_attempts",
            "converted_count",
            "quarantine_count",
            "quarantine_by_reason",
            "failure_breakdown",
        ]:
            self.assertIn(key, raw)


if __name__ == "__main__":
    unittest.main()
