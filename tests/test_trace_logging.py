"""Unit tests verifying trace CSV schema, event types, and periodic telemetry intervals."""

from pathlib import Path
import pandas as pd
import pytest

from simulator.run_scenario import SimulationRunner, load_scenario
from simulator.metrics import compute_metrics


def test_trace_logging_10_columns(tmp_path: Path):
    """Verify trace output has 10 columns and valid headers."""
    scenario_path = Path("scenarios/e1_normal_30n.json")
    assert scenario_path.exists()
    scenario = load_scenario(scenario_path)

    out_trace = tmp_path / "test_trace.csv"
    runner = SimulationRunner(scenario_config=scenario, seed=42, out_path=out_trace)
    metrics = runner.run(duration=5.0)

    assert out_trace.exists()
    df = pd.read_csv(out_trace)

    expected_cols = [
        "time", "src", "dst", "pkt_id", "type",
        "hop_count", "dropped_by", "node_id", "speed", "neighbor_count"
    ]
    assert list(df.columns) == expected_cols
    assert not df.empty

    # Check metrics succeeded
    assert "pdr" in metrics
    assert "throughput_bps" in metrics


def test_periodic_node_status_telemetry(tmp_path: Path):
    """Verify NODE_STATUS events occur every 1.0s for all 30 nodes."""
    scenario_path = Path("scenarios/e1_normal_30n.json")
    scenario = load_scenario(scenario_path)

    out_trace = tmp_path / "test_status.csv"
    runner = SimulationRunner(scenario_config=scenario, seed=42, out_path=out_trace)
    runner.run(duration=5.0)

    df = pd.read_csv(out_trace)
    status_df = df[df["type"] == "NODE_STATUS"]
    assert not status_df.empty

    # At 5.0 seconds duration, intervals at 1.0, 2.0, 3.0, 4.0 (and possibly 5.0)
    # Each interval should log 30 nodes
    timestamps = sorted(status_df["time"].round(2).unique())
    assert len(timestamps) >= 4
    for ts in timestamps[:4]:
        count_at_ts = len(status_df[status_df["time"].round(2) == ts])
        assert count_at_ts == 30, f"Expected 30 nodes at time {ts}, got {count_at_ts}"

    # Verify speed is non-negative float and neighbor_count is non-negative int
    assert (status_df["speed"].astype(float) >= 0.0).all()
    assert (status_df["neighbor_count"].astype(int) >= 0).all()
    assert (status_df["node_id"].astype(int) >= 0).all()


def test_packet_events_acting_node_id(tmp_path: Path):
    """Verify packet events record the acting node_id."""
    scenario_path = Path("scenarios/e2_blackhole_30n.json")
    scenario = load_scenario(scenario_path)

    out_trace = tmp_path / "test_acting_node.csv"
    runner = SimulationRunner(scenario_config=scenario, seed=42, out_path=out_trace)
    runner.run(duration=15.0)

    df = pd.read_csv(out_trace)
    pkt_events = df[df["type"] != "NODE_STATUS"]
    assert not pkt_events.empty
    assert pkt_events["node_id"].notna().all()
    assert (pkt_events["node_id"].astype(int) >= 0).all()
