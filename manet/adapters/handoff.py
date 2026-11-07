"""Simulation launch execution handoff contract and request dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SimulationLaunchRequest:
    """Immutable handoff request containing all parameters needed to launch an experiment."""

    experiment_id: str
    scenario_name: str
    seed: int
    config: dict[str, Any]
    workspace_dir: Path
    created_at: str
    ids_enabled: bool


__all__ = ["SimulationLaunchRequest"]
