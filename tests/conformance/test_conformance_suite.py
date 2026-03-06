import json
import tempfile
import unittest
from pathlib import Path

from tools.conformance.run_suite import GateConfig, build_cases, run_suite


class ConformanceSuiteTests(unittest.TestCase):
    def _default_gate(self) -> GateConfig:
        return GateConfig(
            min_conversion_rate=1.0,
            max_quarantine_rate=0.20,
            mandatory_tests={test_id for test_id, _ in build_cases()},
        )

    def test_suite_has_12_cases(self):
        self.assertEqual(len(build_cases()), 12)

    def test_case_groups_are_even(self):
        groups = [test_id.split("-")[0] for test_id, _ in build_cases()]
        for group in ["A", "B", "C", "D"]:
            self.assertEqual(groups.count(group), 3)

    def test_run_suite_emits_required_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            rc = run_suite(output, self._default_gate())
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
            self.assertEqual(summary["total_conversion_attempts"], 36)
            self.assertEqual(summary["quarantined_events"], 1)
            self.assertEqual(summary["quarantine_reason_totals"], {"Q_UNSUPPORTED_SCHEMA": 1})

    def test_scenario_results_has_12_lines(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            run_suite(output, self._default_gate())
            lines = (output / "scenario-results.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 12)

    def test_gate_fails_when_quarantine_threshold_too_strict(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td)
            strict_gate = GateConfig(
                min_conversion_rate=1.0,
                max_quarantine_rate=0.0,
                mandatory_tests={test_id for test_id, _ in build_cases()},
            )
            rc = run_suite(output, strict_gate)
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
