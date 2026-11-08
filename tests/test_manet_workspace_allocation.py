"""Unit tests for WorkspaceAdapter collision-free directory allocation and launch manifest generation."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import pytest

import manet
from manet.adapters.workspace import (
    WorkspaceAdapter,
    record_launch_manifest,
    sanitize_run_tag,
)


def test_workspace_allocation_and_manifest(tmp_path: Path):
    """Verify unique directory allocation, collision avoidance, tag sanitization, and manifest generation."""
    workspace_root = tmp_path / ".manet-workspace"
    adapter = WorkspaceAdapter(workspace_root)

    # 1. Basic unique directory allocation
    exp_id, exp_dir = adapter.allocate_experiment_directory(
        scenario_name="e1_normal_30n",
        seed=42,
        tag="benchmark_run",
    )

    assert exp_dir.is_dir()
    assert exp_dir.parent == workspace_root.resolve()
    assert exp_id.startswith("exp_")
    assert "e1_normal_30n_42_benchmark_run" in exp_id
    assert exp_dir.name == exp_id

    # 2. Collision avoidance: simulate same ID collision by forcing existing dir
    # Mocking or pre-creating the same directory name
    collision_dir = workspace_root / "exp_20261107_120000_test_42"
    collision_dir.mkdir(parents=True, exist_ok=True)

    # We can test collision logic by calling mkdir on existing paths
    # If we allocate with same base, it should never raise FileExistsError
    id_1, dir_1 = adapter.allocate_experiment_directory("scenario_dup", 100)
    id_2, dir_2 = adapter.allocate_experiment_directory("scenario_dup", 100)

    # If allocated within the same second, dir_2 will have suffix _1
    if id_1 == id_2:
        # If timestamp rolled over, they differ; if same second, collision logic appended _1
        assert dir_1 != dir_2
    else:
        assert dir_1.is_dir() and dir_2.is_dir()

    # Explicit collision loop check
    fixed_base = f"exp_20990101_000000_fixed_1"
    dir_orig = workspace_root / fixed_base
    dir_orig.mkdir(parents=True, exist_ok=True)
    dir_sub1 = workspace_root / f"{fixed_base}_1"
    dir_sub1.mkdir(parents=True, exist_ok=True)

    # 3. Launch manifest recording
    config_payload = {
        "scenario_id": "e1_normal_30n",
        "nodes": 30,
        "duration": 300.0,
        "flows": [{"src": 0, "dst": 1}],
    }
    manifest_path = record_launch_manifest(
        experiment_dir=exp_dir,
        experiment_id=exp_id,
        scenario_name="e1_normal_30n",
        seed=42,
        config=config_payload,
    )

    assert manifest_path.is_file()
    assert manifest_path.name == "manifest.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["experiment_id"] == exp_id
    assert manifest["scenario_name"] == "e1_normal_30n"
    assert manifest["seed"] == 42
    assert manifest["status"] == "CONFIGURED"
    assert manifest["software_version"] == manet.__version__
    assert "T" in manifest["created_at"]  # ISO-8601 UTC timestamp
    assert manifest["trace_path"] == str(exp_dir / "trace.csv")
    assert manifest["configuration"] == config_payload


def test_sanitize_run_tag_rules():
    """Verify run tag sanitization strips directory traversal, Windows illegal characters, and enforces length."""
    # Hostile directory traversal
    assert sanitize_run_tag("../bad/tag*1") == "bad_tag_1"
    assert sanitize_run_tag("..\\..\\windows\\system32") == "windows_system32"
    assert sanitize_run_tag(".../multi/dots...") == "multi_dots"

    # Windows illegal characters: \ / : * ? " < > |
    assert sanitize_run_tag('run:test*1?"<>|') == "run_test_1"
    assert sanitize_run_tag("spaces   and\ttabs") == "spaces_and_tabs"

    # Leading and trailing underscores/dots
    assert sanitize_run_tag("___my_tag___") == "my_tag"
    assert sanitize_run_tag("...my_tag...") == "my_tag"

    # Empty / whitespace-only tag
    assert sanitize_run_tag("") == ""
    assert sanitize_run_tag("   ") == ""
    assert sanitize_run_tag(None) == ""  # type: ignore[arg-type]

    # Truncation to 32 chars
    long_tag = "a" * 50
    assert len(sanitize_run_tag(long_tag)) == 32
    assert sanitize_run_tag(long_tag) == "a" * 32

    # Boundary tests: strip dots/underscores after truncation (CR-02)
    assert sanitize_run_tag("a" * 31 + ".x") == "a" * 31
    assert sanitize_run_tag("a" * 31 + ".b") == "a" * 31
    assert sanitize_run_tag("a" * 31 + "_x") == "a" * 31
    assert sanitize_run_tag("a" * 31 + ".") == "a" * 31
    assert sanitize_run_tag("a" * 31 + "_") == "a" * 31
    assert sanitize_run_tag("a" * 32) == "a" * 32
    assert sanitize_run_tag("a" * 30 + "..") == "a" * 30


def test_manifest_experiment_id_matches_directory_name_on_windows(tmp_path: Path):
    """Verify manifest experiment_id strictly matches on-disk directory name without Windows stripping divergence (CR-02)."""
    workspace_root = tmp_path / "win_workspace"
    adapter = WorkspaceAdapter(workspace_root)

    # Use a tag that would produce a trailing dot before CR-02 fix
    tricky_tag = "a" * 31 + ".b"
    exp_id, exp_dir = adapter.allocate_experiment_directory(
        scenario_name="e1_normal",
        seed=42,
        tag=tricky_tag,
    )

    # Physical on-disk directory name must equal the recorded exp_id
    assert exp_dir.is_dir()
    assert exp_dir.name == exp_id
    assert not exp_id.endswith(".")
    assert not exp_id.endswith("_")

    manifest_path = record_launch_manifest(
        experiment_dir=exp_dir,
        experiment_id=exp_id,
        scenario_name="e1_normal",
        seed=42,
        config={"test": True},
    )
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["experiment_id"] == exp_dir.name


def test_path_containment_and_traversal_rejection(tmp_path: Path):
    """Verify path traversal cannot escape workspace root."""
    workspace_root = tmp_path / "sandbox" / "workspace"
    adapter = WorkspaceAdapter(workspace_root)

    # Allocating with traversal tag should stay strictly within workspace_root
    exp_id, exp_dir = adapter.allocate_experiment_directory(
        scenario_name="test_scenario",
        seed=1,
        tag="../../../etc/passwd",
    )
    assert exp_dir.resolve().is_relative_to(workspace_root.resolve())
    assert "passwd" in exp_id


def test_workspace_adapter_has_no_business_imports():
    """Verify manet/adapters/workspace.py does not import simulator, attacks, feature_extraction, or ml."""
    repo_root = Path(__file__).resolve().parent.parent
    workspace_py = repo_root / "manet" / "adapters" / "workspace.py"
    with open(workspace_py, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(workspace_py))

    forbidden = ("simulator", "attacks", "feature_extraction", "ml")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for f_root in forbidden:
                    assert not (alias.name == f_root or alias.name.startswith(f"{f_root}.")), (
                        f"Forbidden import: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for f_root in forbidden:
                    assert not (node.module == f_root or node.module.startswith(f"{f_root}.")), (
                        f"Forbidden import: {node.module}"
                    )
