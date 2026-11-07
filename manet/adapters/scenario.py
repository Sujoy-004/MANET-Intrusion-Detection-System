"""Scenario adapter discovering authentic preset scenarios from scenarios/*.json without business package imports."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScenarioPreset:
    """Frozen representation of an authentic scenario preset."""

    scenario_id: str
    description: str
    nodes: int
    duration: float
    attack_type: str
    flow_count: int
    raw_config: dict[str, Any]


class ScenarioAdapter:
    """Discovers and parses scenario presets from JSON files on disk."""

    def __init__(self, scenarios_dir: Path | None = None) -> None:
        self.scenarios_dir = scenarios_dir or (Path.cwd() / "scenarios")

    def list_presets(self) -> list[ScenarioPreset]:
        """Discover all *.json files in scenarios_dir, sorted deterministically by filename."""
        if not self.scenarios_dir.is_dir():
            return []

        presets: list[ScenarioPreset] = []
        for json_path in sorted(self.scenarios_dir.glob("*.json"), key=lambda p: p.name):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    continue
                # Validate minimal required fields: scenario_id or nodes
                if "scenario_id" not in data and "nodes" not in data:
                    continue

                flows = data.get("flows", [])
                flow_count = len(flows) if isinstance(flows, list) else 0

                attack_info = data.get("attack", {})
                attack_type = "None"
                if isinstance(attack_info, dict):
                    attack_type = str(attack_info.get("type", "None"))

                preset = ScenarioPreset(
                    scenario_id=str(data.get("scenario_id", json_path.stem)),
                    description=str(data.get("description", "No description")),
                    nodes=int(data.get("nodes", 30)),
                    duration=float(data.get("duration", 300.0)),
                    attack_type=attack_type,
                    flow_count=flow_count,
                    raw_config=data,
                )
                presets.append(preset)
            except Exception:
                continue

        return presets

    def get_preset(self, scenario_id: str) -> ScenarioPreset | None:
        """Find a scenario preset by scenario_id, returning None if not found."""
        for preset in self.list_presets():
            if preset.scenario_id == scenario_id:
                return preset
        return None


__all__ = ["ScenarioPreset", "ScenarioAdapter"]
