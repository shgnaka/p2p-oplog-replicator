from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    seed: int
    node_count: int
    network_profile: str
    duration_steps: int
    events: list[dict[str, Any]]


def from_dict(raw: dict[str, Any]) -> Scenario:
    return Scenario(
        scenario_id=str(raw["scenario_id"]),
        seed=int(raw["seed"]),
        node_count=int(raw["node_count"]),
        network_profile=str(raw["network_profile"]),
        duration_steps=int(raw["duration_steps"]),
        events=list(raw.get("events", [])),
    )
