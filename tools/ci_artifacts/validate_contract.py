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
        "total_conversion_attempts",
        "converted_events",
        "quarantined_events",
        "quarantine_reason_totals",
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

    quarantine_rows = _read_jsonl(output_dir / "quarantine-records.jsonl")
    quarantine_reason_totals: dict[str, int] = {}
    quarantined_events = 0
    for row in quarantine_rows:
        if "test_id" not in row or "scenario_id" not in row:
            raise ArtifactValidationError("quarantine-records rows must include test_id and scenario_id")
        count = int(row.get("quarantine_count", 0))
        quarantined_events += count
        for reason, reason_count in dict(row.get("quarantine_by_reason", {})).items():
            quarantine_reason_totals[str(reason)] = quarantine_reason_totals.get(str(reason), 0) + int(reason_count)

    scenario_conversion_attempts = sum(int(row.get("conversion_attempts", 0)) for row in scenarios)
    scenario_converted = sum(int(row.get("converted_count", 0)) for row in scenarios)

    if int(summary["total_conversion_attempts"]) != scenario_conversion_attempts:
        raise ArtifactValidationError("summary.total_conversion_attempts inconsistent with scenario-results")
    if int(summary["converted_events"]) != scenario_converted:
        raise ArtifactValidationError("summary.converted_events inconsistent with scenario-results")
    if int(summary["quarantined_events"]) != quarantined_events:
        raise ArtifactValidationError("summary.quarantined_events inconsistent with quarantine-records")

    expected_reason_totals = dict(sorted(quarantine_reason_totals.items()))
    if dict(summary["quarantine_reason_totals"]) != expected_reason_totals:
        raise ArtifactValidationError("summary.quarantine_reason_totals inconsistent with quarantine-records")


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
