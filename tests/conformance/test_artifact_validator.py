import json
import tempfile
import unittest
from pathlib import Path

from tools.ci_artifacts.validate_contract import ArtifactValidationError, validate_artifacts
from tools.conformance.run_suite import GateConfig, build_cases, run_suite


class ArtifactValidatorTests(unittest.TestCase):
    def _generate(self, out: Path) -> None:
        gate = GateConfig(
            min_conversion_rate=1.0,
            max_quarantine_rate=0.20,
            mandatory_tests={tid for tid, _ in build_cases()},
        )
        rc = run_suite(out, gate)
        self.assertEqual(rc, 0)

    def test_validator_accepts_valid_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            self._generate(out)
            validate_artifacts(out)

    def test_validator_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            self._generate(out)
            (out / "summary.json").unlink()
            with self.assertRaises(ArtifactValidationError):
                validate_artifacts(out)

    def test_validator_rejects_inconsistent_summary(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            self._generate(out)
            summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
            summary["quarantined_events"] = 99
            (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            with self.assertRaises(ArtifactValidationError):
                validate_artifacts(out)


if __name__ == "__main__":
    unittest.main()
