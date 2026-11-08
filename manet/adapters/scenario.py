"""Scenario adapter discovering authentic preset scenarios from scenarios/*.json without business package imports."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from manet.runtime.paths import get_project_root


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
        self.scenarios_dir = scenarios_dir or (get_project_root() / "scenarios")
        self.diagnostics: list[str] = []

    def list_presets(self) -> list[ScenarioPreset]:
        """Discover all *.json files in scenarios_dir, sorted deterministically by filename.

        Preserves first-match semantics on duplicate scenario_id values and logs diagnostics.
        """
        self.diagnostics.clear()
        if not self.scenarios_dir.is_dir():
            self.diagnostics.append(f"Scenarios directory not found: {self.scenarios_dir}")
            return []

        presets: list[ScenarioPreset] = []
        seen_ids: dict[str, Path] = {}

        for json_path in sorted(self.scenarios_dir.glob("*.json"), key=lambda p: p.name):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    self.diagnostics.append(f"Skipping {json_path.name}: Root JSON structure must be a dictionary")
                    continue
                # Validate minimal required fields: scenario_id or nodes
                if "scenario_id" not in data and "nodes" not in data:
                    self.diagnostics.append(f"Skipping {json_path.name}: Missing required 'scenario_id' or 'nodes'")
                    continue

                raw_config = dict(data)
                raw_config["_source_path"] = str(json_path)

                scenario_id = str(data.get("scenario_id", json_path.stem))
                if scenario_id in seen_ids:
                    self.diagnostics.append(
                        f"Duplicate scenario_id '{scenario_id}' in {json_path.name}; "
                        f"already loaded from {seen_ids[scenario_id].name}. Skipping duplicate."
                    )
                    continue

                flows = data.get("flows", [])
                flow_count = len(flows) if isinstance(flows, list) else 0

                attack_info = data.get("attack", {})
                attack_type = "None"
                if isinstance(attack_info, dict):
                    attack_type = str(attack_info.get("type", "None"))

                preset = ScenarioPreset(
                    scenario_id=scenario_id,
                    description=str(data.get("description", "No description")),
                    nodes=int(data.get("nodes", 30)),
                    duration=float(data.get("duration", 300.0)),
                    attack_type=attack_type,
                    flow_count=flow_count,
                    raw_config=raw_config,
                )
                seen_ids[scenario_id] = json_path
                presets.append(preset)
            except (json.JSONDecodeError, OSError, ValueError, KeyError) as exc:
                self.diagnostics.append(f"Skipping malformed scenario file {json_path.name}: {exc}")
                continue

        return presets

    def get_preset(self, scenario_id: str) -> ScenarioPreset | None:
        """Find a scenario preset by scenario_id, returning None if not found."""
        for preset in self.list_presets():
            if preset.scenario_id == scenario_id:
                return preset
        return None


__all__ = ["ScenarioPreset", "ScenarioAdapter"]
