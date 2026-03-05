from __future__ import annotations

import argparse
import dataclasses
from datetime import datetime, timezone
from pathlib import Path

from tools.ci_artifacts.writer import write_json, write_jsonl
from tools.harness.runner import ScenarioRunner
from tools.harness.scenario import Scenario


@dataclasses.dataclass(frozen=True)
class GateConfig:
    min_conversion_rate: float
    max_quarantine_rate: float
    mandatory_tests: set[str]


def build_cases() -> list[tuple[str, Scenario]]:
    # 12 cases, 3 in each A-D group.
    cases: list[tuple[str, Scenario]] = []
    groups = ["A", "B", "C", "D"]
    idx = 1
    for group in groups:
        for n in range(1, 4):
            test_id = f"{group}-{n:02d}"
            cases.append(
                (
                    test_id,
                    Scenario(
                        scenario_id=f"CONF-{test_id}",
                        seed=100 + idx,
                        node_count=3,
                        network_profile="lan" if group in {"A", "B"} else "nat",
                        duration_steps=3,
                        events=[
                            {"id": f"e{idx}-1", "group": group},
                            {"id": f"e{idx}-2", "group": group, "quarantine": group == "D" and n == 3},
                            {"id": f"e{idx}-3", "group": group},
                        ],
                    ),
                )
            )
            idx += 1
    return cases


def run_suite(output_dir: Path, gate: GateConfig) -> int:
    runner = ScenarioRunner()
    cases = build_cases()

    scenario_rows: list[dict] = []
    quarantine_rows: list[dict] = []
    node_hashes: dict[str, dict[str, str]] = {}

    passed = 0
    failed_test_ids: list[str] = []
    for test_id, scenario in cases:
        result = runner.run(scenario)
        row = dataclasses.asdict(result)
        row["test_id"] = test_id
        scenario_rows.append(row)
        node_hashes[test_id] = result.final_state_hash_by_node
        if result.quarantine_count > 0:
            quarantine_rows.append(
                {
                    "test_id": test_id,
                    "scenario_id": result.scenario_id,
                    "quarantine_count": result.quarantine_count,
                }
            )
        if result.success:
            passed += 1
        else:
            failed_test_ids.append(test_id)

    conversion_rate = passed / len(cases)
    quarantine_rate = len(quarantine_rows) / len(cases)
    mandatory_failed = sorted(tid for tid in failed_test_ids if tid in gate.mandatory_tests)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_id": "local",
        "suite": "conformance-A-D",
        "total_scenarios": len(cases),
        "passed_scenarios": passed,
        "failed_scenarios": len(cases) - passed,
        "conversion_rate": conversion_rate,
        "quarantine_rate": quarantine_rate,
        "failed_test_ids": sorted(failed_test_ids),
        "mandatory_failed_test_ids": mandatory_failed,
        "gate_min_conversion_rate": gate.min_conversion_rate,
        "gate_max_quarantine_rate": gate.max_quarantine_rate,
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "scenario-results.jsonl", scenario_rows)
    write_jsonl(output_dir / "quarantine-records.jsonl", quarantine_rows)
    write_json(output_dir / "node-state-hashes.json", node_hashes)

    ok = True
    if summary["failed_scenarios"] > 0:
        ok = False
    if summary["conversion_rate"] < gate.min_conversion_rate:
        ok = False
    if summary["quarantine_rate"] > gate.max_quarantine_rate:
        ok = False
    if mandatory_failed:
        ok = False
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/conformance")
    parser.add_argument("--min-conversion-rate", type=float, default=1.0)
    parser.add_argument("--max-quarantine-rate", type=float, default=0.20)
    parser.add_argument(
        "--mandatory-tests",
        default="A-01,A-02,A-03,B-01,B-02,B-03,C-01,C-02,C-03,D-01,D-02,D-03",
    )
    args = parser.parse_args()
    gate = GateConfig(
        min_conversion_rate=args.min_conversion_rate,
        max_quarantine_rate=args.max_quarantine_rate,
        mandatory_tests=set(x.strip() for x in args.mandatory_tests.split(",") if x.strip()),
    )
    return run_suite(Path(args.output_dir), gate)


if __name__ == "__main__":
    raise SystemExit(main())
