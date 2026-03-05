from __future__ import annotations

import argparse
import dataclasses
from pathlib import Path

from tools.ci_artifacts.writer import write_json, write_jsonl
from tools.harness.runner import ScenarioRunner
from tools.harness.scenario import Scenario


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


def run_suite(output_dir: Path) -> int:
    runner = ScenarioRunner()
    cases = build_cases()

    scenario_rows: list[dict] = []
    quarantine_rows: list[dict] = []
    node_hashes: dict[str, dict[str, str]] = {}

    passed = 0
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

    summary = {
        "run_id": "local",
        "suite": "conformance-A-D",
        "total_scenarios": len(cases),
        "passed_scenarios": passed,
        "failed_scenarios": len(cases) - passed,
        "conversion_rate": 1.0,
        "quarantine_rate": len(quarantine_rows) / len(cases),
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "scenario-results.jsonl", scenario_rows)
    write_jsonl(output_dir / "quarantine-records.jsonl", quarantine_rows)
    write_json(output_dir / "node-state-hashes.json", node_hashes)

    return 0 if summary["failed_scenarios"] == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="artifacts/conformance")
    args = parser.parse_args()
    return run_suite(Path(args.output_dir))


if __name__ == "__main__":
    raise SystemExit(main())
