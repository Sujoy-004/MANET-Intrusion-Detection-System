"""Unit tests for MANET TUI adapters.

Verifies:
- StatusAdapter distinguishes routing engine availability from workload execution state (D-05)
- WorkspaceAdapter conducts strictly read-only discovery without mutating the filesystem
- NotificationAdapter uses a bounded queue capped at maxlen (20) to prevent memory leaks
- All modules under manet/adapters/ maintain strict zero-import boundary against business packages
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from manet.adapters.navigation import NavigationAdapter, QUICK_ACTIONS
from manet.adapters.notifications import NotificationAdapter
from manet.adapters.status import StatusAdapter, WorkloadStatus
from manet.adapters.workspace import ExperimentSummary, WorkspaceAdapter


def test_status_adapter_distinguishes_engine_and_execution_state():
    """Verify StatusAdapter returns IDLE workload state alongside AODV Engine Ready."""
    adapter = StatusAdapter()
    status = adapter.get_status()

    assert isinstance(status, WorkloadStatus)
    assert status.workload_state == "IDLE"
    assert status.engine_state == "AODV Engine Ready (Offline)"
    assert "No active simulation" in status.description


def test_workspace_adapter_read_only_discovery(tmp_path: Path):
    """Verify WorkspaceAdapter discovers experiments without creating directories or mutating files."""
    workspace_dir = tmp_path / ".manet-workspace"

    # 1. Non-existent directory: returns empty list and does NOT create directory
    adapter = WorkspaceAdapter(workspace_root=workspace_dir)
    assert not workspace_dir.exists()
    assert adapter.list_recent_experiments() == []
    assert not adapter.has_experiments()
    assert not workspace_dir.exists(), "WorkspaceAdapter must be strictly read-only and never create directories"

    # 2. Populated workspace with valid manifests
    workspace_dir.mkdir()
    run_1 = workspace_dir / "exp_001"
    run_1.mkdir()
    manifest_data = {
        "experiment_id": "exp_001",
        "scenario_name": "e1_normal_30n",
        "seed": 42,
        "status": "COMPLETED",
        "created_at": "2026-11-07T10:00:00Z",
        "pdr": 0.945,
    }
    (run_1 / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

    run_2 = workspace_dir / "exp_002"
    run_2.mkdir()
    summary_data = {
        "experiment_id": "exp_002",
        "scenario_name": "e2_blackhole_30n",
        "seed": 99,
        "status": "COMPLETED",
        "created_at": "2026-11-07T10:05:00Z",
        "pdr": 0.123,
    }
    (run_2 / "run_summary.json").write_text(json.dumps(summary_data), encoding="utf-8")

    assert adapter.has_experiments()
    recent = adapter.list_recent_experiments(limit=5)
    assert len(recent) == 2
    exp_ids = {r.experiment_id for r in recent}
    assert "exp_001" in exp_ids
    assert "exp_002" in exp_ids

    exp_1 = next(r for r in recent if r.experiment_id == "exp_001")
    assert exp_1.scenario_name == "e1_normal_30n"
    assert exp_1.seed == 42
    assert exp_1.pdr == 0.945


def test_notification_adapter_bounded_queue():
    """Verify NotificationAdapter caps in-memory queue at maxlen=20 during rapid notifications."""
    adapter = NotificationAdapter(maxlen=20)
    assert adapter.get_active_notice() is None
    assert adapter.get_all_notices() == []

    # Add 50 notices rapidly
    for i in range(50):
        adapter.add_notice(f"Notice message {i}", level="info")

    notices = adapter.get_all_notices()
    assert len(notices) == 20, f"Expected strictly 20 notices, got {len(notices)}"
    assert notices[0] == "Notice message 30"
    assert notices[-1] == "Notice message 49"
    assert adapter.get_active_notice() == "Notice message 49"

    # Test clear
    adapter.clear()
    assert adapter.get_active_notice() is None
    assert adapter.get_all_notices() == []


def test_navigation_adapter_quick_actions():
    """Verify NavigationAdapter defines expected navigation actions and shortcuts."""
    adapter = NavigationAdapter()
    actions = adapter.get_quick_actions()
    assert len(actions) == 5

    action_map = {a.id: a for a in actions}
    assert "simulation" in action_map
    assert action_map["simulation"].shortcut == "s"
    assert "Phase 9" in action_map["simulation"].label

    assert "results" in action_map
    assert action_map["results"].shortcut == "r"
    assert "Phase 11" in action_map["results"].label

    assert "console" in action_map
    assert action_map["console"].shortcut == "ctrl+o"

    assert "palette" in action_map
    assert action_map["palette"].shortcut == "ctrl+p"

    assert "help" in action_map
    assert action_map["help"].shortcut == "f1"


def test_adapters_ast_import_boundaries():
    """Verify manet/adapters/ never imports simulator, attacks, feature_extraction, or ml."""
    repo_root = Path(__file__).resolve().parent.parent
    adapters_dir = repo_root / "manet" / "adapters"
    assert adapters_dir.is_dir()

    forbidden_roots = ("simulator", "attacks", "feature_extraction", "ml")
    py_files = sorted(adapters_dir.rglob("*.py"))
    assert len(py_files) > 0

    for py_file in py_files:
        with open(py_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(py_file))

        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.append(node.module)

        violations = [
            imp
            for imp in imported
            if any(imp == root or imp.startswith(f"{root}.") for root in forbidden_roots)
        ]
        assert (
            len(violations) == 0
        ), f"Architectural violation in {py_file.relative_to(repo_root)}: imports business packages: {violations}"
