from __future__ import annotations

import argparse
import json
from pathlib import Path


class ArtifactValidationError(Exception):
    pass


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def validate_artifacts(output_dir: Path) -> None:
    required = [
        output_dir / "summary.json",
        output_dir / "scenario-results.jsonl",
        output_dir / "quarantine-records.jsonl",
        output_dir / "node-state-hashes.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise ArtifactValidationError(f"missing required artifacts: {missing}")

    summary = _read_json(output_dir / "summary.json")
    required_summary_keys = {
        "total_scenarios",
        "passed_scenarios",
        "failed_scenarios",
        "conversion_rate",
        "quarantine_rate",
        "failed_test_ids",
        "mandatory_failed_test_ids",
        "gate_min_conversion_rate",
        "gate_max_quarantine_rate",
    }
    missing_summary_keys = sorted(required_summary_keys - set(summary.keys()))
    if missing_summary_keys:
        raise ArtifactValidationError(f"summary missing keys: {missing_summary_keys}")

    scenarios = _read_jsonl(output_dir / "scenario-results.jsonl")
    if len(scenarios) != summary["total_scenarios"]:
        raise ArtifactValidationError("scenario-results count does not match summary.total_scenarios")

    test_ids = [row.get("test_id") for row in scenarios]
    if any(tid is None for tid in test_ids):
        raise ArtifactValidationError("scenario-results contains row without test_id")
    if len(test_ids) != len(set(test_ids)):
        raise ArtifactValidationError("scenario-results test_id values are not unique")

    failed_from_rows = sorted(row["test_id"] for row in scenarios if not row.get("success", False))
    if failed_from_rows != sorted(summary["failed_test_ids"]):
        raise ArtifactValidationError("summary.failed_test_ids inconsistent with scenario-results")

    if summary["failed_scenarios"] != len(summary["failed_test_ids"]):
        raise ArtifactValidationError("summary.failed_scenarios inconsistent with failed_test_ids")
    if summary["passed_scenarios"] + summary["failed_scenarios"] != summary["total_scenarios"]:
        raise ArtifactValidationError("summary pass/fail counts inconsistent")

    for key in ["conversion_rate", "quarantine_rate", "gate_min_conversion_rate", "gate_max_quarantine_rate"]:
        value = float(summary[key])
        if value < 0.0 or value > 1.0:
            raise ArtifactValidationError(f"summary.{key} out of range [0,1]")

    hashes = _read_json(output_dir / "node-state-hashes.json")
    if sorted(hashes.keys()) != sorted(test_ids):
        raise ArtifactValidationError("node-state-hashes keys must match scenario test_ids")

    for row in _read_jsonl(output_dir / "quarantine-records.jsonl"):
        if "test_id" not in row or "scenario_id" not in row:
            raise ArtifactValidationError("quarantine-records rows must include test_id and scenario_id")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/conformance")
    args = parser.parse_args()

    try:
        validate_artifacts(Path(args.output_dir))
    except ArtifactValidationError as exc:
        print(f"artifact validation failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
