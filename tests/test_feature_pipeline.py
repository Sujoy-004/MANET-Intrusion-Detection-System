"""Automated unit and anti-leakage invariance tests for feature engineering."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from feature_extraction.extract_features import (
    SCHEMA_COLUMNS,
    extract_features_from_trace,
)
from simulator.run_scenario import SimulationRunner, load_scenario


@pytest.fixture(scope="module")
def sample_trace(tmp_path_factory) -> tuple[pd.DataFrame, dict]:
    """Generate a quick 20s simulation trace for feature testing."""
    tmp = tmp_path_factory.mktemp("feat_data")
    trace_path = tmp / "sample_trace.csv"
    scenario_path = Path("scenarios/e2_blackhole_30n.json")
    scenario = load_scenario(scenario_path)

    runner = SimulationRunner(scenario_config=scenario, seed=42, out_path=trace_path)
    runner.run(duration=20.0)

    df = pd.read_csv(trace_path)
    return df, scenario


def test_schema_columns_exact_match(sample_trace):
    """Verify output DataFrame columns match SCHEMA_COLUMNS in exact order."""
    trace_df, scenario = sample_trace
    feats = extract_features_from_trace(trace_df, scenario, window_size=5.0, step_size=1.0, warmup=10.0)

    assert list(feats.columns) == SCHEMA_COLUMNS
    assert len(feats.columns) == 10
    assert not feats.empty


def test_no_nan_or_inf_in_features(sample_trace):
    """Verify zero NaN, null, or infinite values in extracted feature matrix."""
    trace_df, scenario = sample_trace
    feats = extract_features_from_trace(trace_df, scenario, window_size=5.0, step_size=1.0, warmup=10.0)

    # Check numeric columns
    numeric_df = feats.iloc[:, :-1]
    assert not numeric_df.isna().any().any()
    assert np.isfinite(numeric_df.to_numpy(dtype=float)).all()


def test_neutral_zero_traffic_fallback(sample_trace):
    """Verify idle nodes with 0 forward and 0 drop packets receive neutral 1.0 and 0.0."""
    trace_df, scenario = sample_trace
    feats = extract_features_from_trace(trace_df, scenario, window_size=5.0, step_size=1.0, warmup=10.0)

    # In a 30-node network with 6 flows, several peripheral nodes carry no data traffic
    zero_traffic_rows = feats[(feats["packet_forward_ratio"] == 1.0) & (feats["packet_drop_ratio"] == 0.0)]
    assert not zero_traffic_rows.empty, "Expected idle nodes with neutral forward ratio = 1.0"


def test_zero_identity_in_features(sample_trace):
    """Verify no identity, coordinate, or metadata leak into feature column names."""
    trace_df, scenario = sample_trace
    feats = extract_features_from_trace(trace_df, scenario)

    forbidden_cols = ["node_id", "id", "ip", "src", "dst", "x", "y", "time", "scenario", "seed", "dropped_by"]
    for col in forbidden_cols:
        assert col not in feats.columns, f"Forbidden leakage column found in features: {col}"


def test_anti_leakage_invariance(sample_trace):
    """Verify that toggling the ground-truth label does NOT alter any feature column in X."""
    trace_df, scenario = sample_trace

    # Run 1: Attacker is node 14
    scen_1 = dict(scenario)
    scen_1["attack"] = {"enabled": True, "type": "Blackhole", "attackers": [14]}
    df1 = extract_features_from_trace(trace_df, scen_1, window_size=5.0, step_size=1.0, warmup=10.0)

    # Run 2: Attacker is node 20
    scen_2 = dict(scenario)
    scen_2["attack"] = {"enabled": True, "type": "Blackhole", "attackers": [20]}
    df2 = extract_features_from_trace(trace_df, scen_2, window_size=5.0, step_size=1.0, warmup=10.0)

    # The first 9 columns (feature matrix X) must be numerically identical
    assert df1.iloc[:, :-1].equals(df2.iloc[:, :-1]), "Feature matrix X changed when attack label changed! Identity leakage detected."

    # Labels must differ according to the scenario definition
    assert not df1["label"].equals(df2["label"]), "Labels did not change as expected"
