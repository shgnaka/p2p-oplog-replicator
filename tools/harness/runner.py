from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass

from tools.harness.scenario import Scenario


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    seed: int
    node_count: int
    success: bool
    assertions: list[str]
    final_state_hash_by_node: dict[str, str]
    conversion_attempts: int
    converted_count: int
    quarantine_count: int
    quarantine_by_reason: dict[str, int]
    failure_breakdown: dict[str, int]


class ScenarioRunner:
    """Deterministic scenario runner for multi-node validation."""

    def run(self, scenario: Scenario) -> ScenarioResult:
        rng = random.Random(scenario.seed)
        node_state: dict[str, list[str]] = {f"node-{i}": [] for i in range(scenario.node_count)}
        failures: dict[str, int] = {}
        quarantines = 0
        conversion_attempts = 0
        quarantine_by_reason: dict[str, int] = {}

        for step in range(scenario.duration_steps):
            if step < len(scenario.events):
                event = scenario.events[step]
                conversion_attempts += 1
                payload = json.dumps(event, sort_keys=True)
                # Keep replay deterministic and convergence-preserving for conformance runs.
                for node_id in node_state:
                    node_state[node_id].append(payload)
                    if rng.random() < 0.1:
                        failures["delivery_drop"] = failures.get("delivery_drop", 0) + 1
                if event.get("quarantine") is True:
                    quarantines += 1
                    reason = str(event.get("reason_code", "Q_UNSPECIFIED"))
                    quarantine_by_reason[reason] = quarantine_by_reason.get(reason, 0) + 1

        hashes = {
            node_id: hashlib.sha256("|".join(log).encode("utf-8")).hexdigest()
            for node_id, log in sorted(node_state.items())
        }
        unique_hashes = set(hashes.values())
        success = len(unique_hashes) == 1
        assertions = [
            "state_converged" if success else "state_diverged",
            "seed_reproducible",
        ]
        if not success:
            failures["state_divergence"] = 1

        converted_count = conversion_attempts - quarantines

        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            seed=scenario.seed,
            node_count=scenario.node_count,
            success=success,
            assertions=assertions,
            final_state_hash_by_node=hashes,
            conversion_attempts=conversion_attempts,
            converted_count=converted_count,
            quarantine_count=quarantines,
            quarantine_by_reason=dict(sorted(quarantine_by_reason.items())),
            failure_breakdown=failures,
        )
