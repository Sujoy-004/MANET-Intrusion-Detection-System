"""Unit tests for DiagnosticsProbe runtime capability detection.

Verifies:
- Dependency detection maps sklearn to scikit-learn without PackageNotFoundError
- Scenario probing distinguishes valid JSON presets from malformed files
- Dataset detection checks train.csv and test.csv via stat() with zero mock rows
- Missing model binary reports UNAVAILABLE with full CLI remediation
- Corrupted or missing model metadata reports UNAVAILABLE without crashing
- Dynamic metrics extraction badges Grayhole F1 of 0.0 as PARTIAL / Ineffective Detection
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from manet.adapters.diagnostics import (
    CapabilityStatus,
    DiagnosticsProbe,
    DiagnosticsReport,
    REQUIRED_PACKAGES,
)


def test_diagnostics_dependencies_sklearn_mapping():
    """Verify scikit-learn distribution lookup succeeds without PackageNotFoundError."""
    probe = DiagnosticsProbe()
    deps = probe.probe_dependencies()

    for pkg in REQUIRED_PACKAGES:
        assert pkg in deps, f"Expected {pkg} in probe_dependencies results"
        available, version = deps[pkg]
        assert available is True, f"Expected package {pkg} to be available in test environment"
        assert version != "missing", f"Expected installed version for {pkg}, got {version}"

    # Specifically verify sklearn mapping
    assert deps["sklearn"][0] is True
    assert deps["sklearn"][1] != "missing"
    assert not deps["sklearn"][1].startswith("Error")


def test_diagnostics_scenarios_valid_and_malformed(tmp_path: Path):
    """Verify distinguishing valid scenario JSON presets from corrupted/malformed files."""
    scenarios_dir = tmp_path / "scenarios"
    scenarios_dir.mkdir(parents=True)

    # 1. Initially empty directory
    probe_empty = DiagnosticsProbe(repo_root=tmp_path)
    res_empty = probe_empty.probe_scenarios()
    assert res_empty.state == "UNAVAILABLE"
    assert "No scenario files found" in res_empty.details

    # 2. Add 2 valid scenarios and 1 malformed JSON
    (scenarios_dir / "valid_1.json").write_text(
        json.dumps({"scenario_id": "test_1", "nodes": 10, "attack": None}),
        encoding="utf-8",
    )
    (scenarios_dir / "valid_2.json").write_text(
        json.dumps({"scenario_id": "test_2", "nodes": 20, "attack": "blackhole"}),
        encoding="utf-8",
    )
    (scenarios_dir / "corrupted.json").write_text(
        "{ invalid json syntax",
        encoding="utf-8",
    )

    probe = DiagnosticsProbe(repo_root=tmp_path)
    res = probe.probe_scenarios()
    assert res.state == "VERIFIED"
    assert "2 valid presets available" in res.details
    assert "corrupted.json" in res.details

    # 3. Only malformed files present
    (scenarios_dir / "valid_1.json").unlink()
    (scenarios_dir / "valid_2.json").unlink()
    res_only_corrupt = probe.probe_scenarios()
    assert res_only_corrupt.state == "UNAVAILABLE"
    assert "No valid presets found" in res_only_corrupt.details


def test_diagnostics_datasets_present_and_missing(tmp_path: Path):
    """Assert honest VERIFIED / UNAVAILABLE with exact remediation command."""
    data_dir = tmp_path / "data"

    # Missing datasets
    probe = DiagnosticsProbe(repo_root=tmp_path)
    res_missing = probe.probe_datasets()
    assert res_missing.state == "UNAVAILABLE"
    assert "data/train.csv" in res_missing.details
    assert "data/test.csv" in res_missing.details
    assert res_missing.remediation == "Run python scripts/build_dataset.py --multi-attack"

    # Both datasets present
    data_dir.mkdir(parents=True)
    (data_dir / "train.csv").write_text("header,col\n1,2\n", encoding="utf-8")
    (data_dir / "test.csv").write_text("header,col\n3,4\n", encoding="utf-8")

    res_present = probe.probe_datasets()
    assert res_present.state == "VERIFIED"
    assert "train.csv" in res_present.details
    assert "test.csv" in res_present.details
    assert "bytes" in res_present.details
    assert res_present.remediation is None


def test_diagnostics_model_binary_missing_with_metadata(tmp_path: Path):
    """Assert state UNAVAILABLE and full remediation when binary is missing."""
    models_dir = tmp_path / "ml" / "models"
    models_dir.mkdir(parents=True)

    # Metadata exists, but best_model.joblib is missing
    metadata_content = {
        "champion": "random_forest",
        "test_metrics": {"f1_blackhole": 0.8, "f1_grayhole": 0.0, "fpr": 0.01},
    }
    (models_dir / "model_metadata.json").write_text(
        json.dumps(metadata_content), encoding="utf-8"
    )

    probe = DiagnosticsProbe(repo_root=tmp_path)
    res = probe.probe_model_artifact()

    assert res.state == "UNAVAILABLE"
    assert "Model binary not found" in res.details
    assert "best_model.joblib missing" in res.details
    assert "historical metadata available" in res.details
    assert res.remediation == (
        "Run python scripts/build_dataset.py --multi-attack && "
        "python -m ml.train && python -m ml.evaluate"
    )


def test_diagnostics_model_corrupted_metadata(tmp_path: Path):
    """Verify graceful error handling on malformed JSON without crashing."""
    models_dir = tmp_path / "ml" / "models"
    models_dir.mkdir(parents=True)

    (models_dir / "best_model.joblib").write_bytes(b"dummy joblib binary payload")
    (models_dir / "model_metadata.json").write_text("{ malformed json content", encoding="utf-8")

    probe = DiagnosticsProbe(repo_root=tmp_path)
    res = probe.probe_model_artifact()

    assert res.state == "UNAVAILABLE"
    assert "Metadata missing/corrupt" in res.details
    assert res.remediation == "Re-evaluate model: python -m ml.evaluate"


def test_diagnostics_model_dynamic_metrics_and_grayhole_badge(tmp_path: Path):
    """Assert metrics are parsed dynamically and Grayhole F1 0.0 is explicitly badged as ineffective."""
    models_dir = tmp_path / "ml" / "models"
    models_dir.mkdir(parents=True)
    (models_dir / "best_model.joblib").write_bytes(b"dummy joblib binary payload")

    # Case A: Grayhole F1 is 0.0 -> Must badge PARTIAL and Ineffective Detection
    meta_gh_zero = {
        "champion": "random_forest",
        "test_metrics": {
            "f1_blackhole": 0.759259,
            "f1_grayhole": 0.0,
            "fpr": 0.009941,
        },
    }
    (models_dir / "model_metadata.json").write_text(
        json.dumps(meta_gh_zero), encoding="utf-8"
    )

    probe = DiagnosticsProbe(repo_root=tmp_path)
    res = probe.probe_model_artifact()

    assert res.state == "PARTIAL"
    assert "Random Forest" in res.details
    assert "BH F1: 0.7593" in res.details
    assert "PARTIAL (Grayhole F1: 0.0 - Ineffective Detection)" in res.details
    assert "FPR: 0.0099" in res.details
    assert res.remediation == "Multi-attack tuning required for Grayhole detection"

    # Case B: Missing metric keys -> Must render "N/A" instead of hardcoding 0.0
    meta_missing_keys = {
        "champion": "decision_tree",
        "test_metrics": {
            "f1_blackhole": 0.65,
            # f1_grayhole and fpr omitted
        },
    }
    (models_dir / "model_metadata.json").write_text(
        json.dumps(meta_missing_keys), encoding="utf-8"
    )

    res_missing = probe.probe_model_artifact()
    assert "Decision Tree" in res_missing.details
    assert "BH F1: 0.6500" in res_missing.details
    assert "GH F1: N/A" in res_missing.details
    assert "FPR: N/A" in res_missing.details

    # Case C: Positive Grayhole F1 -> VERIFIED
    meta_gh_effective = {
        "champion": "random_forest",
        "test_metrics": {
            "f1_blackhole": 0.92,
            "f1_grayhole": 0.88,
            "fpr": 0.005,
        },
    }
    (models_dir / "model_metadata.json").write_text(
        json.dumps(meta_gh_effective), encoding="utf-8"
    )

    res_effective = probe.probe_model_artifact()
    assert res_effective.state == "VERIFIED"
    assert "GH F1: 0.8800" in res_effective.details
    assert res_effective.remediation is None


def test_diagnostics_probe_all():
    """Verify probe_all returns a cohesive DiagnosticsReport."""
    probe = DiagnosticsProbe()
    report = probe.probe_all()

    assert isinstance(report, DiagnosticsReport)
    assert report.python_version[1] is True
    assert len(report.dependencies) == 9
    assert isinstance(report.scenarios, CapabilityStatus)
    assert isinstance(report.datasets, CapabilityStatus)
    assert isinstance(report.model_artifact, CapabilityStatus)
