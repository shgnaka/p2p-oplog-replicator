from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from tools.harness.runner import ScenarioResult


def write_result_json(result: ScenarioResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True), encoding="utf-8")
