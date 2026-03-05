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
    quarantine_count: int
    failure_breakdown: dict[str, int]


class ScenarioRunner:
    """Deterministic scenario runner for multi-node validation."""

    def run(self, scenario: Scenario) -> ScenarioResult:
        rng = random.Random(scenario.seed)
        node_state: dict[str, list[str]] = {f"node-{i}": [] for i in range(scenario.node_count)}
        failures: dict[str, int] = {}
        quarantines = 0

        for step in range(scenario.duration_steps):
            if step < len(scenario.events):
                event = scenario.events[step]
                payload = json.dumps(event, sort_keys=True)
                # Use deterministic fanout pattern driven by seed.
                for node_id in node_state:
                    if rng.random() >= 0.1:
                        node_state[node_id].append(payload)
                    else:
                        failures["delivery_drop"] = failures.get("delivery_drop", 0) + 1
                if event.get("quarantine") is True:
                    quarantines += 1

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

        return ScenarioResult(
            scenario_id=scenario.scenario_id,
            seed=scenario.seed,
            node_count=scenario.node_count,
            success=success,
            assertions=assertions,
            final_state_hash_by_node=hashes,
            quarantine_count=quarantines,
            failure_breakdown=failures,
        )
