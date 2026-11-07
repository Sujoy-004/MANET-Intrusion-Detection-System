"""Unit tests for SimulationConfigValidator, CustomScenarioBuilder, and SimulationLaunchRequest."""

from __future__ import annotations

import ast
from pathlib import Path
import pytest

from manet.adapters.handoff import SimulationLaunchRequest
from manet.adapters.simulation_config import (
    DEFAULT_CUSTOM_DURATION,
    DEFAULT_SEED,
    MAX_DURATION,
    MAX_NODES,
    MIN_DURATION,
    MIN_NODES,
    CustomScenarioBuilder,
    SimulationConfigValidator,
    build_custom_configuration,
    validate_duration,
    validate_loss_probability,
    validate_node_count,
    validate_radio_range,
    validate_seed,
    validate_structural_invariants,
)


def test_two_tier_validation_and_model_gate(tmp_path: Path):
    """Verify Tier 1 scalar validators, Tier 2 structural invariants, and IDS champion model gating."""
    # ---------------------------------------------------------
    # Tier 1: Scalar Validators
    # ---------------------------------------------------------
    # Node count: [MIN_NODES, MAX_NODES] -> [2, 100]
    ok, err = validate_node_count(30)
    assert ok and err is None
    ok, err = validate_node_count("2")
    assert ok and err is None
    ok, err = validate_node_count(100)
    assert ok and err is None
    ok, err = validate_node_count(1)
    assert not ok and "between 2 and 100" in str(err)
    ok, err = validate_node_count(101)
    assert not ok and "between 2 and 100" in str(err)
    ok, err = validate_node_count("invalid")
    assert not ok and "must be an integer" in str(err)

    # Duration: [MIN_DURATION, MAX_DURATION] -> [10.0, 3600.0]
    ok, err = validate_duration(100.0)
    assert ok and err is None
    ok, err = validate_duration(10.0)
    assert ok and err is None
    ok, err = validate_duration(3600.0)
    assert ok and err is None
    ok, err = validate_duration(9.9)
    assert not ok and "between 10.0 and 3600.0" in str(err)
    ok, err = validate_duration(3601.0)
    assert not ok and "between 10.0 and 3600.0" in str(err)
    ok, err = validate_duration("not-a-number")
    assert not ok and "valid number" in str(err)

    # Seed: non-negative integer
    ok, err = validate_seed(42)
    assert ok and err is None
    ok, err = validate_seed("0")
    assert ok and err is None
    ok, err = validate_seed(-1)
    assert not ok and "between 0 and" in str(err)
    ok, err = validate_seed("abc")
    assert not ok and "must be an integer" in str(err)

    # Radio range: [10.0, 2000.0]
    ok, err = validate_radio_range(250.0)
    assert ok and err is None
    ok, err = validate_radio_range(5.0)
    assert not ok and "between 10.0 and 2000.0" in str(err)

    # Loss probability: [0.0, 1.0]
    ok, err = validate_loss_probability(0.05)
    assert ok and err is None
    ok, err = validate_loss_probability(1.5)
    assert not ok and "between 0.0 and 1.0" in str(err)

    # ---------------------------------------------------------
    # Tier 2: Structural Invariants & Flow Endpoints
    # ---------------------------------------------------------
    valid_config = build_custom_configuration(nodes=30, duration=100.0, seed=42)
    errors = validate_structural_invariants(valid_config)
    assert len(errors) == 0, f"Expected no errors for default custom configuration, got {errors}"

    # Flow source >= nodes
    bad_src_config = {
        "nodes": 10,
        "duration": 50.0,
        "flows": [{"src": 10, "dst": 2}],
    }
    errs = validate_structural_invariants(bad_src_config)
    assert any("source node 10 out of range [0, 9]" in e for e in errs)

    # Flow destination >= nodes
    bad_dst_config = {
        "nodes": 10,
        "duration": 50.0,
        "flows": [{"src": 2, "dst": 12}],
    }
    errs = validate_structural_invariants(bad_dst_config)
    assert any("destination node 12 out of range [0, 9]" in e for e in errs)

    # Flow source == destination
    same_endpoint_config = {
        "nodes": 10,
        "duration": 50.0,
        "flows": [{"src": 3, "dst": 3}],
    }
    errs = validate_structural_invariants(same_endpoint_config)
    assert any("source (3) cannot equal destination (3)" in e for e in errs)

    # Negative endpoint
    neg_endpoint_config = {
        "nodes": 10,
        "duration": 50.0,
        "flows": [{"src": -1, "dst": 5}],
    }
    errs = validate_structural_invariants(neg_endpoint_config)
    assert any("source node -1 out of range" in e for e in errs)

    # ---------------------------------------------------------
    # Tier 2: IDS Champion Model Gate
    # ---------------------------------------------------------
    model_file = tmp_path / "best_model.joblib"
    ids_config = {
        "nodes": 20,
        "duration": 100.0,
        "flows": [{"src": 0, "dst": 1}],
        "ids": {"enabled": True},
    }

    # Case A: Model does not exist
    errs_missing_model = validate_structural_invariants(ids_config, model_path=model_file)
    assert len(errs_missing_model) == 1
    assert "IDS enabled but champion model artifact (ml/models/best_model.joblib) does not exist on disk" in errs_missing_model[0]
    assert "python scripts/build_dataset.py --multi-attack && python -m ml.train && python -m ml.evaluate" in errs_missing_model[0]

    # Case B: Model exists but is 0 bytes (empty)
    model_file.write_bytes(b"")
    errs_empty_model = validate_structural_invariants(ids_config, model_path=model_file)
    assert len(errs_empty_model) == 1
    assert "IDS enabled but champion model artifact" in errs_empty_model[0]

    # Case C: Model exists and is non-empty
    model_file.write_bytes(b"dummy-joblib-content")
    errs_valid_model = validate_structural_invariants(ids_config, model_path=model_file)
    assert len(errs_valid_model) == 0


def test_build_custom_configuration():
    """Verify CustomScenarioBuilder builds schema conforming to SimulationRunner requirements."""
    cfg = build_custom_configuration(
        nodes=25,
        duration=120.0,
        seed=1337,
        attack_type="Blackhole",
        ids_enabled=False,
        advanced_params={
            "radio_range": 300.0,
            "loss_probability": 0.02,
            "speed_range": [2.0, 15.0],
            "pause_time": 10.0,
            "rate_pps": 5.0,
            "seq_offset": 500,
            "spoofed_hops": 2,
        },
    )

    assert cfg["nodes"] == 25
    assert cfg["duration"] == 120.0
    assert cfg["seed"] == 1337
    assert cfg["radio"]["range"] == 300.0
    assert cfg["radio"]["loss_probability"] == 0.02
    assert cfg["mobility"]["speed_range"] == [2.0, 15.0]
    assert cfg["mobility"]["pause_time"] == 10.0
    assert cfg["attack"]["enabled"] is True
    assert cfg["attack"]["type"] == "Blackhole"
    assert cfg["attack"]["seq_offset"] == 500
    assert cfg["attack"]["spoofed_hops"] == 2
    assert cfg["ids"]["enabled"] is False

    flows = cfg["flows"]
    assert len(flows) == 1
    assert flows[0]["src"] == 0
    assert flows[0]["dst"] == 24
    assert flows[0]["rate_pps"] == 5.0

    # Also test Grayhole attack construction
    gh_cfg = build_custom_configuration(
        nodes=40,
        duration=80.0,
        seed=999,
        attack_type="Grayhole",
        ids_enabled=True,
        advanced_params={"drop_prob": 0.75, "start_time": 20.0},
    )
    assert gh_cfg["attack"]["type"] == "Grayhole"
    assert gh_cfg["attack"]["drop_prob"] == 0.75
    assert gh_cfg["attack"]["start_time"] == 20.0
    assert gh_cfg["ids"]["enabled"] is True


def test_simulation_launch_request():
    """Verify SimulationLaunchRequest frozen dataclass."""
    req = SimulationLaunchRequest(
        experiment_id="exp_20261107_120000_custom_42",
        scenario_name="custom_30n_none",
        seed=42,
        config={"nodes": 30},
        workspace_dir=Path(".manet-workspace/exp_1"),
        created_at="2026-11-07T12:00:00Z",
        ids_enabled=False,
    )
    assert req.experiment_id == "exp_20261107_120000_custom_42"
    assert req.seed == 42
    assert req.ids_enabled is False

    with pytest.raises(Exception):
        req.seed = 99  # frozen dataclass mutation attempt


def test_simulation_config_adapter_has_no_business_imports():
    """Verify manet/adapters/simulation_config.py and handoff.py do not import business packages."""
    repo_root = Path(__file__).resolve().parent.parent
    for mod_name in ("simulation_config.py", "handoff.py"):
        mod_path = repo_root / "manet" / "adapters" / mod_name
        with open(mod_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(mod_path))

        forbidden = ("simulator", "attacks", "feature_extraction", "ml")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for f_root in forbidden:
                        assert not (alias.name == f_root or alias.name.startswith(f"{f_root}.")), (
                            f"{mod_name} has forbidden import: {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for f_root in forbidden:
                        assert not (node.module == f_root or node.module.startswith(f"{f_root}.")), (
                            f"{mod_name} has forbidden import: {node.module}"
                        )
