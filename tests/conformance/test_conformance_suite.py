import json
import tempfile
import unittest
from pathlib import Path

from tools.conformance.run_suite import build_cases, run_suite


class ConformanceSuiteTests(unittest.TestCase):
    def test_suite_has_12_cases(self):
        self.assertEqual(len(build_cases()), 12)

    def test_case_groups_are_even(self):
        groups = [test_id.split("-")[0] for test_id, _ in build_cases()]
        for group in ["A", "B", "C", "D"]:
            self.assertEqual(groups.count(group), 3)

    def test_run_suite_emits_required_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            rc = run_suite(output)
            self.assertEqual(rc, 0)
            for name in [
                "summary.json",
                "scenario-results.jsonl",
                "quarantine-records.jsonl",
                "node-state-hashes.json",
            ]:
                self.assertTrue((output / name).exists())

            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["total_scenarios"], 12)
            self.assertEqual(summary["failed_scenarios"], 0)

    def test_scenario_results_has_12_lines(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            run_suite(output)
            lines = (output / "scenario-results.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 12)


if __name__ == "__main__":
    unittest.main()
