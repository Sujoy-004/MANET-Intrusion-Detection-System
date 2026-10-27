"""Unit and integration tests for RFC 3561 Grayhole attack strategy and pipeline."""

import math
import os
import random
import tempfile
import pandas as pd
import pytest

from attacks.base import AttackStrategy
from attacks.grayhole import GrayholeStrategy
from attacks.registry import create_attack_strategy
from feature_extraction.extract_features import SCHEMA_COLUMNS, extract_features_from_trace
from simulator.run_scenario import SimulationRunner, load_scenario


def test_grayhole_strategy_inheritance():
    """Verify GrayholeStrategy inherits from AttackStrategy and is registered."""
    strategy = create_attack_strategy("grayhole", drop_prob=0.5, seed=42)
    assert isinstance(strategy, AttackStrategy)
    assert isinstance(strategy, GrayholeStrategy)
    assert strategy.drop_prob == 0.5


def test_grayhole_honest_routing():
    """Verify Grayhole emits no spoofed RREP parameters (honest control routing)."""
    strategy = GrayholeStrategy(drop_prob=0.5, seed=42)
    params = strategy.get_spoofed_rrep_params(dest=10, rreq_dest_seq=5)
    assert params is None, "Grayhole must return None for spoofed RREP to participate honestly in AODV"


@pytest.mark.parametrize("target_p", [0.3, 0.5, 0.7])
def test_grayhole_drop_probability_calibration(target_p: float):
    """Verify empirical drop rates match target drop_prob within 99% binomial confidence."""
    n_trials = 2000
    strategy = GrayholeStrategy(drop_prob=target_p, seed=123)
    drops = sum(strategy.should_drop_data(pkt_src=1, pkt_dst=2, pkt_id=i) for i in range(n_trials))
    empirical_p = drops / n_trials

    # 99% confidence interval z = 2.576
    std_err = math.sqrt(target_p * (1.0 - target_p) / n_trials)
    margin = 2.576 * std_err
    assert abs(empirical_p - target_p) <= margin, (
        f"Empirical drop rate {empirical_p:.4f} diverged from target {target_p} (margin {margin:.4f})"
    )


def test_grayhole_selective_filtering():
    """Verify selective dropping modes respect flow and destination target filters."""
    # Target only flow (1, 2)
    flow_strategy = GrayholeStrategy(drop_prob=1.0, target_flows=[(1, 2)], seed=42)
    assert flow_strategy.should_drop_data(1, 2, 10) is True
    assert flow_strategy.should_drop_data(1, 3, 11) is False
    assert flow_strategy.should_drop_data(3, 2, 12) is False

    # Target only destination 5
    dest_strategy = GrayholeStrategy(drop_prob=1.0, target_dests=[5], seed=42)
    assert dest_strategy.should_drop_data(0, 5, 20) is True
    assert dest_strategy.should_drop_data(1, 5, 21) is True
    assert dest_strategy.should_drop_data(0, 4, 22) is False


def test_grayhole_seed_determinism():
    """Verify explicit seed guarantees bit-exact reproducible drop decisions."""
    strat1 = GrayholeStrategy(drop_prob=0.5, seed=999)
    strat2 = GrayholeStrategy(drop_prob=0.5, seed=999)

    decisions1 = [strat1.should_drop_data(1, 2, i) for i in range(100)]
    decisions2 = [strat2.should_drop_data(1, 2, i) for i in range(100)]
    assert decisions1 == decisions2


def test_grayhole_simulation_trace_and_features():
    """Verify e4_grayhole_onset_30n runs cleanly and produces valid Normal & Grayhole features."""
    cfg = load_scenario("scenarios/e4_grayhole_onset_30n.json")
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_path = os.path.join(tmpdir, "trace_grayhole_test.csv")
        runner = SimulationRunner(cfg, seed=42, out_path=trace_path)
        # Run 60s for fast verification (onset is at 100s in full scenario, test with onset at 20s)
        test_cfg = dict(cfg)
        test_cfg["duration"] = 60.0
        test_cfg["attack"] = dict(cfg["attack"])
        test_cfg["attack"]["start_time"] = 20.0

        runner = SimulationRunner(test_cfg, seed=42, out_path=trace_path)
        runner.run(60.0)

        # Attacker node flag
        assert len(runner.attacker_ids) == 1
        attacker_id = runner.attacker_ids[0]
        assert runner.aodv_nodes[attacker_id].is_grayhole is True

        # Trace exists and has events
        assert os.path.exists(trace_path)
        trace_df = pd.read_csv(trace_path)
        assert not trace_df.empty

        # Feature extraction
        features_df = extract_features_from_trace(
            trace_df=trace_df,
            scenario_config=test_cfg,
            attacker_ids=runner.attacker_ids,
            attack_start_time=20.0,
        )

        assert list(features_df.columns) == SCHEMA_COLUMNS
        labels = set(features_df["label"].unique())
        assert labels == {"Normal", "Grayhole"}
        assert (features_df["label"] == "Grayhole").sum() > 0
        assert (features_df["label"] == "Normal").sum() > 0
