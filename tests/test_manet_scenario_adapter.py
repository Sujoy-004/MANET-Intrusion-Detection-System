"""Unit tests for ScenarioAdapter authentic preset discovery and schema parsing."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import pytest

from manet.adapters.scenario import ScenarioAdapter, ScenarioPreset


def test_tracer_preset_discovery_and_schema():
    """Verify ScenarioAdapter discovers all 5 authentic scenario presets from scenarios/*.json."""
    repo_root = Path(__file__).resolve().parent.parent
    scenarios_dir = repo_root / "scenarios"
    adapter = ScenarioAdapter(scenarios_dir)

    presets = adapter.list_presets()
    assert len(presets) == 5, f"Expected exactly 5 presets, got {len(presets)}"

    preset_map = {p.scenario_id: p for p in presets}
    expected_ids = {
        "e1_normal_30n",
        "e2_blackhole_30n",
        "e3_blackhole_onset_30n",
        "e4_grayhole_50n",
        "e4_grayhole_onset_30n",
    }
    assert set(preset_map.keys()) == expected_ids

    # Check e1_normal_30n
    e1 = preset_map["e1_normal_30n"]
    assert e1.nodes == 30
    assert e1.duration == 300.0
    assert e1.attack_type == "None"
    assert e1.flow_count == 6
    assert "Baseline 30-node" in e1.description
    assert isinstance(e1.raw_config, dict)

    # Check e2_blackhole_30n
    e2 = preset_map["e2_blackhole_30n"]
    assert e2.nodes == 30
    assert e2.duration == 300.0
    assert e2.attack_type == "Blackhole"
    assert e2.flow_count == 6
    assert "Blackhole" in e2.description

    # Check e3_blackhole_onset_30n
    e3 = preset_map["e3_blackhole_onset_30n"]
    assert e3.nodes == 30
    assert e3.duration == 300.0
    assert e3.attack_type == "Blackhole"
    assert e3.flow_count == 6
    assert "onset at 100s" in e3.description

    # Check e4_grayhole_50n
    e4 = preset_map["e4_grayhole_50n"]
    assert e4.nodes == 50
    assert e4.duration == 60.0
    assert e4.attack_type == "Grayhole"
    assert e4.flow_count == 6
    assert "50-node dense" in e4.description

    # Check e4_grayhole_onset_30n
    e4_onset = preset_map["e4_grayhole_onset_30n"]
    assert e4_onset.nodes == 30
    assert e4_onset.duration == 300.0
    assert e4_onset.attack_type == "Grayhole"
    assert e4_onset.flow_count == 6
    assert "Grayhole attacker" in e4_onset.description

    # Test get_preset helper
    retrieved = adapter.get_preset("e1_normal_30n")
    assert retrieved is not None
    assert retrieved.scenario_id == "e1_normal_30n"

    missing = adapter.get_preset("non_existent_preset")
    assert missing is None


def test_malformed_json_handling(tmp_path: Path):
    """Verify malformed, non-dict, and invalid JSON files are gracefully skipped."""
    # Malformed syntax
    bad_syntax = tmp_path / "bad_syntax.json"
    bad_syntax.write_text("{not valid json", encoding="utf-8")

    # Non-dict JSON (array)
    array_json = tmp_path / "array.json"
    array_json.write_text("[1, 2, 3]", encoding="utf-8")

    # Dict without scenario_id or nodes
    empty_dict = tmp_path / "empty_dict.json"
    empty_dict.write_text('{"foo": "bar"}', encoding="utf-8")

    # Valid scenario JSON
    valid_json = tmp_path / "valid.json"
    valid_data = {
        "scenario_id": "test_preset",
        "description": "Valid test scenario",
        "nodes": 10,
        "duration": 50.0,
        "attack": {"type": "Blackhole"},
        "flows": [{"src": 0, "dst": 1}],
    }
    valid_json.write_text(json.dumps(valid_data), encoding="utf-8")

    adapter = ScenarioAdapter(tmp_path)
    presets = adapter.list_presets()

    assert len(presets) == 1
    assert presets[0].scenario_id == "test_preset"
    assert presets[0].nodes == 10
    assert presets[0].duration == 50.0
    assert presets[0].attack_type == "Blackhole"
    assert presets[0].flow_count == 1


def test_duplicate_scenario_id_deduplication(tmp_path: Path):
    """Verify duplicate scenario_id across files preserves first-match and records diagnostic (CR-01)."""
    file1 = tmp_path / "01_first.json"
    file2 = tmp_path / "02_second.json"

    data1 = {
        "scenario_id": "duplicate_id",
        "description": "First file with duplicate id",
        "nodes": 20,
        "duration": 100.0,
        "flows": [{"src": 0, "dst": 1}],
    }
    data2 = {
        "scenario_id": "duplicate_id",
        "description": "Second file with duplicate id",
        "nodes": 40,
        "duration": 200.0,
        "flows": [{"src": 0, "dst": 2}],
    }
    file1.write_text(json.dumps(data1), encoding="utf-8")
    file2.write_text(json.dumps(data2), encoding="utf-8")

    adapter = ScenarioAdapter(tmp_path)
    presets = adapter.list_presets()

    assert len(presets) == 1, f"Expected 1 deduplicated preset, got {len(presets)}"
    assert presets[0].scenario_id == "duplicate_id"
    assert presets[0].description == "First file with duplicate id"
    assert presets[0].nodes == 20
    assert len(adapter.diagnostics) == 1
    assert "Duplicate scenario_id 'duplicate_id'" in adapter.diagnostics[0]
    assert "02_second.json" in adapter.diagnostics[0]

    retrieved = adapter.get_preset("duplicate_id")
    assert retrieved is not None
    assert retrieved.description == "First file with duplicate id"


def test_missing_or_empty_directory(tmp_path: Path):
    """Verify missing directory or empty directory returns empty list."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    adapter_empty = ScenarioAdapter(empty_dir)
    assert adapter_empty.list_presets() == []

    non_existent = tmp_path / "missing_dir"
    adapter_missing = ScenarioAdapter(non_existent)
    assert adapter_missing.list_presets() == []


def test_scenario_adapter_has_no_business_imports():
    """Verify manet/adapters/scenario.py does not import simulator, attacks, feature_extraction, or ml."""
    scenario_py = Path(__file__).resolve().parent.parent / "manet" / "adapters" / "scenario.py"
    with open(scenario_py, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(scenario_py))

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
