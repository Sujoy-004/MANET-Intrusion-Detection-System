"""Unit tests for headless publication plotting library (ml/plots.py).

Verifies requirement RESP-03, headless execution safety (matplotlib Agg backend),
300 DPI image generation, column validation, and end-to-end figure generation.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from PIL import Image
import pytest

from ml.plots import (
    TRIAD_PALETTE,
    _load_and_validate_df,
    generate_all_figures,
    plot_classifier_comparison,
    plot_confusion_matrices,
    plot_executive_dashboard,
    plot_feature_importance,
    plot_generalization_stress,
    plot_qos_recovery_triad,
    plot_quarantine_timeline,
)


@pytest.fixture
def mock_closed_loop_df() -> pd.DataFrame:
    """Create a minimal mock closed loop DataFrame."""
    scenarios = ["30n_blackhole", "30n_grayhole_p50"]
    modes = ["Baseline", "Attack", "AODV+IDS"]
    seeds = [42, 43]
    records = []
    for sc in scenarios:
        for m in modes:
            for s in seeds:
                records.append({
                    "scenario": sc,
                    "nodes": 30,
                    "attack_type": "Blackhole" if "blackhole" in sc else "Grayhole",
                    "drop_prob": 1.0 if "blackhole" in sc else 0.5,
                    "seed": s,
                    "mode": m,
                    "pdr": 0.65 if m == "Baseline" else (0.15 if m == "Attack" else 0.60),
                    "throughput_kbps": 45.0 if m == "Baseline" else (10.0 if m == "Attack" else 42.0),
                    "avg_delay_ms": 5.0,
                    "packet_loss_ratio": 0.35 if m == "Baseline" else (0.85 if m == "Attack" else 0.40),
                    "routing_overhead": 0.05 if m == "Baseline" else (0.08 if m == "Attack" else 0.07),
                    "delta_pdr_abs": 0.45 if m == "AODV+IDS" else 0.0,
                    "recovery_ratio": 90.0 if m == "AODV+IDS" else 0.0,
                    "overhead_cost": 0.02 if m == "AODV+IDS" else 0.0,
                })
    return pd.DataFrame(records)


@pytest.fixture
def mock_metrics_df() -> pd.DataFrame:
    """Create a minimal mock metrics DataFrame."""
    return pd.DataFrame([
        {
            "model": "random_forest",
            "accuracy": 0.974,
            "precision": 0.421,
            "recall": 0.308,
            "f1_blackhole": 0.759,
            "fpr": 0.0099,
            "tn": 16831,
            "fp": 169,
            "fn": 277,
            "tp": 123,
        },
        {
            "model": "decision_tree",
            "accuracy": 0.950,
            "precision": 0.163,
            "recall": 0.283,
            "f1_blackhole": 0.677,
            "fpr": 0.0342,
            "tn": 16419,
            "fp": 581,
            "fn": 287,
            "tp": 113,
        },
        {
            "model": "svm",
            "accuracy": 0.547,
            "precision": 0.048,
            "recall": 0.998,
            "f1_blackhole": 0.555,
            "fpr": 0.4638,
            "tn": 9115,
            "fp": 7885,
            "fn": 1,
            "tp": 399,
        },
    ])


@pytest.fixture
def mock_importance_df() -> pd.DataFrame:
    """Create a minimal mock feature importance DataFrame."""
    features = ["packet_drop_ratio", "hop_count", "packet_forward_ratio"]
    records = []
    for f in features:
        records.append({
            "model": "random_forest",
            "feature": f,
            "source": "permutation",
            "importance_mean": 0.21 if f == "packet_drop_ratio" else 0.15,
            "importance_std": 0.01,
        })
        records.append({
            "model": "random_forest",
            "feature": f,
            "source": "gini",
            "importance_mean": 0.10 if f == "packet_drop_ratio" else 0.08,
            "importance_std": 0.0,
        })
    return pd.DataFrame(records)


@pytest.fixture
def mock_generalization_df() -> pd.DataFrame:
    """Create a minimal mock generalization DataFrame."""
    records = []
    for speed in [1.0, 5.0, 10.0]:
        for drop_prob in [0.3, 0.5, 0.7]:
            for nodes in [30, 50]:
                records.append({
                    "nodes": nodes,
                    "speed": speed,
                    "drop_prob": drop_prob,
                    "seed": 44,
                    "pdr": 0.65,
                    "throughput_kbps": 45.0,
                    "packet_loss_rate": 0.35,
                    "avg_delay_sec": 0.005,
                    "accuracy": 0.98,
                    "precision": 0.85,
                    "recall": 0.80 if speed == 1.0 else (0.50 if speed == 5.0 else 0.10),
                    "f1": 0.82 if speed == 1.0 else (0.55 if speed == 5.0 else 0.15),
                    "fpr": 0.005,
                    "grayhole_recall": 0.80,
                    "tp": 30,
                    "fp": 5,
                    "fn": 10,
                    "tn": 1400,
                })
    return pd.DataFrame(records)


@pytest.fixture
def mock_events_df() -> pd.DataFrame:
    """Create a minimal mock isolation events DataFrame."""
    return pd.DataFrame([
        {
            "sim_time": 5.5,
            "scenario_name": "30n_blackhole",
            "seed": 42,
            "node_id": 21,
            "strike_count": 1,
            "prob_malicious": 0.78,
            "predicted_type": "Blackhole",
            "action": "STRIKE",
            "quarantine_until": 0.0,
            "reason": "Strike 1",
        },
        {
            "sim_time": 7.0,
            "scenario_name": "30n_blackhole",
            "seed": 42,
            "node_id": 21,
            "strike_count": 2,
            "prob_malicious": 0.78,
            "predicted_type": "Blackhole",
            "action": "QUARANTINE",
            "quarantine_until": 37.0,
            "reason": "Confirmed quarantine",
        },
        {
            "sim_time": 37.0,
            "scenario_name": "30n_blackhole",
            "seed": 42,
            "node_id": 21,
            "strike_count": 0,
            "prob_malicious": 0.0,
            "predicted_type": "Normal",
            "action": "UNBLOCK",
            "quarantine_until": 0.0,
            "reason": "Unblocked",
        },
    ])


def test_matplotlib_agg_backend():
    """Verify that Agg backend is active and headless safe."""
    assert matplotlib.get_backend().lower() == "agg"


def test_load_and_validate_df(tmp_path):
    """Verify CSV validation and missing column checks."""
    csv_file = tmp_path / "test.csv"
    pd.DataFrame({"a": [1, 2], "b": [3, 4]}).to_csv(csv_file, index=False)

    # Valid load
    df = _load_and_validate_df(csv_file, ["a", "b"])
    assert len(df) == 2

    # Missing column
    with pytest.raises(ValueError, match="missing required columns"):
        _load_and_validate_df(csv_file, ["a", "c"])

    # Non-existent file
    with pytest.raises(FileNotFoundError):
        _load_and_validate_df(tmp_path / "non_existent.csv", ["a"])


def test_plot_executive_dashboard(mock_closed_loop_df, tmp_path):
    """Verify 4-panel executive dashboard generation at 300 DPI."""
    out_file = tmp_path / "qos_recovery_triad_dashboard.png"
    result = plot_executive_dashboard(mock_closed_loop_df, out_file, dpi=300)

    assert result == out_file
    assert out_file.is_file()
    assert out_file.stat().st_size > 5000  # Valid binary image

    with Image.open(out_file) as img:
        assert img.format == "PNG"
        # At 300 DPI, 14x10 inches should have width >= 3000px
        assert img.size[0] >= 3000
        assert img.size[1] >= 2000


def test_plot_qos_recovery_triad(mock_closed_loop_df, tmp_path):
    """Verify 4 standalone QoS recovery figures are created."""
    results = plot_qos_recovery_triad(mock_closed_loop_df, tmp_path, dpi=300)

    assert len(results) == 4
    expected_names = [
        "qos_pdr_recovery.png",
        "qos_throughput_recovery.png",
        "qos_delay_impact.png",
        "qos_routing_overhead_penalty.png",
    ]
    for expected in expected_names:
        p = tmp_path / expected
        assert p.is_file()
        assert p.stat().st_size > 3000
        with Image.open(p) as img:
            assert img.format == "PNG"


def test_plot_classifier_comparison(mock_metrics_df, tmp_path):
    """Verify classifier comparison chart with FPR gate."""
    out_file = tmp_path / "classifier_comparison_metrics.png"
    result = plot_classifier_comparison(mock_metrics_df, out_file, dpi=300)

    assert result == out_file
    assert out_file.is_file()
    assert out_file.stat().st_size > 5000
    with Image.open(out_file) as img:
        assert img.format == "PNG"
        assert img.size[0] >= 2500


def test_plot_feature_importance(mock_importance_df, tmp_path):
    """Verify Random Forest Permutation vs Gini feature ranking chart."""
    out_file = tmp_path / "feature_importance_ranking.png"
    result = plot_feature_importance(mock_importance_df, out_file, dpi=300)

    assert result == out_file
    assert out_file.is_file()
    assert out_file.stat().st_size > 5000
    with Image.open(out_file) as img:
        assert img.format == "PNG"


def test_plot_generalization_stress(mock_generalization_df, tmp_path):
    """Verify mobility speed and drop rate stress curves."""
    results = plot_generalization_stress(mock_generalization_df, tmp_path, dpi=300)

    assert len(results) == 2
    expected_names = ["stress_mobility_vs_recall.png", "stress_droprate_vs_pdr.png"]
    for expected in expected_names:
        p = tmp_path / expected
        assert p.is_file()
        assert p.stat().st_size > 3000
        with Image.open(p) as img:
            assert img.format == "PNG"


def test_plot_quarantine_timeline(mock_events_df, tmp_path):
    """Verify quarantine timeline swimlane plot."""
    out_file = tmp_path / "mitigation_quarantine_timeline.png"
    result = plot_quarantine_timeline(mock_events_df, out_file, dpi=300)

    assert result == out_file
    assert out_file.is_file()
    assert out_file.stat().st_size > 5000
    with Image.open(out_file) as img:
        assert img.format == "PNG"


def test_plot_confusion_matrices(mock_metrics_df, tmp_path):
    """Verify standardized confusion matrices for 3 models."""
    results = plot_confusion_matrices(mock_metrics_df, tmp_path, dpi=300)

    assert len(results) == 3
    expected_names = [
        "confusion_matrix_random_forest.png",
        "confusion_matrix_decision_tree.png",
        "confusion_matrix_svm.png",
    ]
    for expected in expected_names:
        p = tmp_path / expected
        assert p.is_file()
        assert p.stat().st_size > 3000
        with Image.open(p) as img:
            assert img.format == "PNG"


def test_generate_all_figures_end_to_end(tmp_path):
    """Verify complete portfolio generation from authoritative results directory."""
    results_dir = Path("results")
    if not results_dir.is_dir() or not (results_dir / "closed_loop_metrics.csv").is_file():
        pytest.skip("Authoritative results/ directory not available for end-to-end test")

    out_dir = tmp_path / "plots"
    generated = generate_all_figures(results_dir=results_dir, plots_dir=out_dir, dpi=300)

    assert len(generated) == 13
    for name, path in generated.items():
        assert path.is_file()
        assert path.stat().st_size > 3000
        with Image.open(path) as img:
            assert img.format == "PNG"
