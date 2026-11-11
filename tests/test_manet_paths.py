"""Tests verifying repository-root path anchoring independent of process working directory (IN-06)."""

from __future__ import annotations

import os
from pathlib import Path
import pytest

from manet.adapters.scenario import ScenarioAdapter
from manet.adapters.simulation_config import validate_structural_invariants
from manet.adapters.workspace import WorkspaceAdapter
from manet.runtime.paths import get_project_root
from manet.screens.simulation_workflow import SimulationWorkflowScreen
from manet.widgets.wizard_step_review import StepReviewWidget


@pytest.mark.real_workspace_defaults
def test_repo_root_anchoring_outside_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify default adapters, validators, and widgets resolve to repo root when cwd is outside repo (IN-06)."""
    repo_root = get_project_root()
    assert (repo_root / "scenarios").is_dir()
    assert (repo_root / "manet").is_dir()

    # Change current working directory to an isolated temp directory outside the repository
    outside_dir = tmp_path / "outside_sandbox"
    outside_dir.mkdir()
    monkeypatch.chdir(outside_dir)
    assert Path.cwd() == outside_dir

    # 1. get_project_root still resolves to the repository root
    assert get_project_root() == repo_root

    # 2. ScenarioAdapter default discovers real presets from repo root
    adapter = ScenarioAdapter()
    assert adapter.scenarios_dir == repo_root / "scenarios"
    presets = adapter.list_presets()
    assert len(presets) == 5

    # 3. Structural invariant validator default finds champion model in repo root
    valid_ids_config = {
        "nodes": 20,
        "duration": 50.0,
        "flows": [{"src": 0, "dst": 1}],
        "ids": {"enabled": True},
    }
    # Champion model exists on disk in repo root (ml/models/best_model.joblib), so no missing model error
    errs = validate_structural_invariants(valid_ids_config)
    assert not any("champion model artifact" in e for e in errs)

    # 4. WorkspaceAdapter default targets repo root workspace
    workspace = WorkspaceAdapter()
    assert workspace.workspace_root == repo_root / ".manet-workspace"

    # 5. SimulationWorkflowScreen and StepReviewWidget defaults target repo root
    screen = SimulationWorkflowScreen()
    assert screen.scenario_adapter.scenarios_dir == repo_root / "scenarios"
    assert screen.workspace_adapter.workspace_root == repo_root / ".manet-workspace"
    assert screen.model_path == repo_root / "ml" / "models" / "best_model.joblib"

    review = StepReviewWidget()
    assert review.model_path == repo_root / "ml" / "models" / "best_model.joblib"
    assert review.workspace_root == repo_root / ".manet-workspace"
