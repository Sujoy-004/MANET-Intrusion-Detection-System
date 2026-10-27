"""Unit and integration tests for closed-loop IDS response and AODV mitigation seams."""

from __future__ import annotations

import copy
import csv
from pathlib import Path
import subprocess
import sys
from typing import Any, List, Set

import numpy as np
import pandas as pd
import pytest
import simpy

from feature_extraction.extract_features import SCHEMA_COLUMNS, extract_features_from_trace
from ml.response import OnlineIDS
from simulator.aodv import AODVNode, RREP, RREQ, RouteEntry
from simulator.run_scenario import NodeState, SimulationRunner, load_scenario


def test_rrep_and_rreq_drop_filtering():
    """Verify incoming RREP and RREQ packets from/traversing blacklisted nodes are dropped."""
    sent_packets: List[Any] = []
    logged_events: List[Any] = []
    blacklisted_nodes: Set[int] = {9}

    sim_time = 1.0

    node = AODVNode(
        node_id=1,
        get_time=lambda: sim_time,
        send_packet_cb=lambda target, msg: sent_packets.append((target, msg)),
        log_event_cb=lambda **kwargs: logged_events.append(kwargs),
        is_blacklisted_cb=lambda nid: nid in blacklisted_nodes,
    )

    # 1. RREQ from blacklisted prev_hop should be dropped immediately
    rreq_bad_hop = RREQ(rreq_id=1, originator=2, originator_seq=1, dest=1, dest_seq=0)
    node.handle_rreq(rreq_bad_hop, prev_hop=9)
    assert (2, 1) not in node.seen_rreq
    assert 2 not in node.routing_table
    assert len(sent_packets) == 0

    # 2. RREQ from blacklisted originator should be dropped immediately
    rreq_bad_orig = RREQ(rreq_id=2, originator=9, originator_seq=1, dest=1, dest_seq=0)
    node.handle_rreq(rreq_bad_orig, prev_hop=2)
    assert (9, 2) not in node.seen_rreq
    assert 9 not in node.routing_table
    assert len(sent_packets) == 0

    # 3. RREP from blacklisted prev_hop should be dropped
    rrep_bad_hop = RREP(originator=1, dest=3, dest_seq=5, hop_count=1, lifetime=10.0)
    node.handle_rrep(rrep_bad_hop, prev_hop=9)
    assert 3 not in node.routing_table
    assert len(sent_packets) == 0

    # 4. RREP for blacklisted destination should be dropped
    rrep_bad_dest = RREP(originator=1, dest=9, dest_seq=5, hop_count=1, lifetime=10.0)
    node.handle_rrep(rrep_bad_dest, prev_hop=2)
    assert 9 not in node.routing_table
    assert len(sent_packets) == 0

    # 5. Benign RREQ and RREP should be processed normally
    rreq_ok = RREQ(rreq_id=3, originator=2, originator_seq=1, dest=1, dest_seq=0)
    node.handle_rreq(rreq_ok, prev_hop=2)
    assert (2, 3) in node.seen_rreq
    assert 2 in node.routing_table
    assert len(sent_packets) == 1  # Replied with RREP to destination 1


def test_route_table_exclusion_and_invalidation():
    """Verify route insertion rejection, route lookup invalidation, and invalidate_routes_through."""
    blacklisted_nodes: Set[int] = {8}
    sim_time = 1.0

    node = AODVNode(
        node_id=1,
        get_time=lambda: sim_time,
        send_packet_cb=lambda target, msg: None,
        log_event_cb=lambda **kwargs: None,
        is_blacklisted_cb=lambda nid: nid in blacklisted_nodes,
    )

    # 1. update_route with blacklisted next_hop or dest rejected
    assert node.update_route(dest=5, next_hop=8, hop_count=1, dest_seq=1, lifetime=10.0) is False
    assert 5 not in node.routing_table
    assert node.update_route(dest=8, next_hop=2, hop_count=1, dest_seq=1, lifetime=10.0) is False
    assert 8 not in node.routing_table

    # 2. Add valid routes through node 4 and node 3
    assert node.update_route(dest=10, next_hop=4, hop_count=2, dest_seq=1, lifetime=10.0) is True
    assert node.update_route(dest=11, next_hop=4, hop_count=3, dest_seq=1, lifetime=10.0) is True
    assert node.update_route(dest=12, next_hop=3, hop_count=1, dest_seq=1, lifetime=10.0) is True

    # 3. get_route returns valid route before blacklist
    assert node.get_route(10) is not None
    assert node.get_route(10).next_hop == 4

    # Now blacklist node 4 dynamically
    blacklisted_nodes.add(4)
    # get_route(10) should detect blacklisted next_hop, invalidate entry, and return None
    assert node.get_route(10) is None
    assert node.routing_table[10].is_valid is False

    # 4. invalidate_routes_through should purge all entries using bad_node
    blacklisted_nodes.clear()
    node.routing_table[10].is_valid = True  # re-enable for testing purge
    severed = node.invalidate_routes_through(4)
    assert set(severed) == {10, 11}
    assert node.routing_table[10].is_valid is False
    assert node.routing_table[11].is_valid is False
    assert node.routing_table[12].is_valid is True  # Route through 3 still valid


def test_online_ids_feature_parity():
    """Verify that features computed online by OnlineIDS match offline extract_features_from_trace."""
    env = simpy.Environment()
    aodv_nodes: dict[int, AODVNode] = {}
    nodes = {
        0: NodeState(node_id=0, x=0, y=0, speed=2.0, neighbors=[1]),
        1: NodeState(node_id=1, x=100, y=100, speed=3.0, neighbors=[0, 2]),
        2: NodeState(node_id=2, x=200, y=200, speed=1.5, neighbors=[1]),
    }

    ids = OnlineIDS(
        env=env,
        aodv_nodes=aodv_nodes,
        nodes=nodes,
        model_path="ml/models/best_model.joblib",
        window_size=5.0,
        eval_interval=1.0,
    )

    trace_records = [
        {"time": 5.0, "src": 0, "dst": 2, "pkt_id": 1, "type": "DATA_SENT", "hop_count": 0, "dropped_by": "", "node_id": 0, "speed": 2.0, "neighbor_count": 5},
        {"time": 5.001, "src": 0, "dst": -1, "pkt_id": 0, "type": "NODE_STATUS", "hop_count": 0, "dropped_by": "", "node_id": 0, "speed": 2.0, "neighbor_count": 5},
        {"time": 5.001, "src": 1, "dst": -1, "pkt_id": 0, "type": "NODE_STATUS", "hop_count": 0, "dropped_by": "", "node_id": 1, "speed": 3.0, "neighbor_count": 4},
        {"time": 5.001, "src": 2, "dst": -1, "pkt_id": 0, "type": "NODE_STATUS", "hop_count": 0, "dropped_by": "", "node_id": 2, "speed": 1.5, "neighbor_count": 6},
        {"time": 5.01, "src": 0, "dst": 2, "pkt_id": 1, "type": "DATA_FWD", "hop_count": 1, "dropped_by": "", "node_id": 1, "speed": 3.0, "neighbor_count": 4},
        {"time": 5.02, "src": 0, "dst": 2, "pkt_id": 1, "type": "DATA_RECV", "hop_count": 2, "dropped_by": "", "node_id": 2, "speed": 1.5, "neighbor_count": 6},
        {"time": 6.0, "src": 0, "dst": 2, "pkt_id": 2, "type": "DATA_SENT", "hop_count": 0, "dropped_by": "", "node_id": 0, "speed": 2.0, "neighbor_count": 5},
        {"time": 6.01, "src": 0, "dst": 2, "pkt_id": 2, "type": "DATA_DROP", "hop_count": 1, "dropped_by": "1", "node_id": 1, "speed": 3.0, "neighbor_count": 4},
        {"time": 7.0, "src": 1, "dst": 2, "pkt_id": 3, "type": "RREQ", "hop_count": 0, "dropped_by": "", "node_id": 1, "speed": 3.0, "neighbor_count": 4},
        {"time": 7.5, "src": 1, "dst": 0, "pkt_id": 4, "type": "RREP", "hop_count": 1, "dropped_by": "", "node_id": 1, "speed": 3.0, "neighbor_count": 4},
        {"time": 10.0, "src": 1, "dst": -1, "pkt_id": 0, "type": "NODE_STATUS", "hop_count": 0, "dropped_by": "", "node_id": 1, "speed": 3.0, "neighbor_count": 4},
    ]

    # Ingest into OnlineIDS
    for r in trace_records:
        ids.ingest_event(
            sim_time=r["time"],
            src=r["src"],
            dst=r["dst"],
            pkt_id=r["pkt_id"],
            pkt_type=r["type"],
            hop_count=r["hop_count"],
            dropped_by=r["dropped_by"],
            node_id=r["node_id"],
            speed=r["speed"],
            neighbor_count=r["neighbor_count"],
        )

    # Compute features online for node 1 at now=10.0
    online_feats = ids.compute_features_for_node(1, now=10.0)
    assert online_feats is not None

    # Compute features offline via extract_features_from_trace
    trace_df = pd.DataFrame(trace_records)
    scenario_cfg = {"nodes": 3, "attack": {"enabled": False}}
    offline_df = extract_features_from_trace(
        trace_df=trace_df,
        scenario_config=scenario_cfg,
        window_size=5.0,
        step_size=1.0,
        warmup=10.0,
    )

    # In offline_df, rows correspond to nodes 0, 1, 2 at t=10.0
    # Node 1 is the second row (index 1)
    offline_row = offline_df.iloc[1]

    feature_cols = SCHEMA_COLUMNS[:9]
    for col in feature_cols:
        online_val = online_feats[col]
        offline_val = offline_row[col]
        np.testing.assert_allclose(
            online_val,
            offline_val,
            rtol=1e-5,
            atol=1e-5,
            err_msg=f"Feature {col} mismatch: online={online_val}, offline={offline_val}",
        )


def test_strike_accumulation_and_quarantine_decay(tmp_path: Path):
    """Verify 1-strike tolerance, 2-strike quarantine enactment, and 30s quarantine decay."""
    env = simpy.Environment()
    aodv_node = AODVNode(
        node_id=2,
        get_time=lambda: env.now,
        send_packet_cb=lambda t, m: None,
        log_event_cb=lambda **kw: None,
    )
    aodv_nodes = {2: aodv_node}
    nodes = {2: NodeState(node_id=2, x=50, y=50, speed=3.5, neighbors=[1, 3, 4, 5, 6])}

    log_file = tmp_path / "isolation_events.csv"
    ids = OnlineIDS(
        env=env,
        aodv_nodes=aodv_nodes,
        nodes=nodes,
        model_path="ml/models/best_model.joblib",
        window_size=5.0,
        eval_interval=1.0,
        strikes_required=2,
        quarantine_duration=30.0,
        isolation_log_path=log_file,
    )

    # Ingest persistent packet drops and spoofed replies by node 2 in window [0, 5.0]
    for t in [1.0, 2.0, 3.0, 4.0]:
        ids.ingest_event(sim_time=t, src=1, dst=3, pkt_id=int(t*10), pkt_type="DATA_DROP", hop_count=2, dropped_by=2, node_id=2, speed=3.5, neighbor_count=5)
        ids.ingest_event(sim_time=t, src=2, dst=1, pkt_id=int(t*10+5), pkt_type="RREP", hop_count=2, node_id=2, speed=3.5, neighbor_count=5)
        ids.ingest_event(sim_time=t, src=2, dst=-1, pkt_id=0, pkt_type="NODE_STATUS", hop_count=0, node_id=2, speed=3.5, neighbor_count=5)

    # Advance clock to 5.0s and evaluate: strike 1 should be recorded
    env.run(until=5.0)
    ids.step_detection(now=5.0)

    assert ids.strikes.get(2, 0) == 1
    assert ids.is_blacklisted(2) is False
    assert any(ev.action == "STRIKE" and ev.node_id == 2 for ev in ids.isolation_events)

    # Ingest another drop in next second and advance clock to 6.0s
    ids.ingest_event(sim_time=5.5, src=1, dst=3, pkt_id=55, pkt_type="DATA_DROP", hop_count=2, dropped_by=2, node_id=2, speed=3.5, neighbor_count=5)
    ids.ingest_event(sim_time=5.5, src=2, dst=1, pkt_id=65, pkt_type="RREP", hop_count=2, node_id=2, speed=3.5, neighbor_count=5)
    ids.ingest_event(sim_time=5.5, src=2, dst=-1, pkt_id=0, pkt_type="NODE_STATUS", hop_count=0, node_id=2, speed=3.5, neighbor_count=5)

    env.run(until=6.0)
    ids.step_detection(now=6.0)

    # Strike 2 should trigger quarantine for 30s (until 36.0s)
    assert ids.strikes[2] == 2
    assert ids.is_blacklisted(2) is True
    assert ids.quarantined_nodes[2] == 36.0
    assert any(ev.action == "QUARANTINE" and ev.node_id == 2 for ev in ids.isolation_events)

    # Advance clock halfway (t=20.0s): node should remain quarantined
    env.run(until=20.0)
    assert ids.is_blacklisted(2) is True

    # Advance clock past quarantine expiration (t=36.1s)
    env.run(until=36.1)
    ids.step_detection(now=36.1)

    # Node should be unblocked and strikes reset to 0
    assert ids.is_blacklisted(2) is False
    assert ids.strikes.get(2, 0) == 0
    assert any(ev.action == "UNBLOCK" and ev.node_id == 2 for ev in ids.isolation_events)

    # Test writing log
    ids.write_isolation_log()
    assert log_file.exists()
    with open(log_file, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) >= 3


def test_flow_endpoint_protection():
    """Verify that flow endpoints (sources/dests) are guarded from quarantine under high drop ratio."""
    env = simpy.Environment()
    aodv_node = AODVNode(
        node_id=0,
        get_time=lambda: env.now,
        send_packet_cb=lambda t, m: None,
        log_event_cb=lambda **kw: None,
    )
    aodv_nodes = {0: aodv_node}
    nodes = {0: NodeState(node_id=0, x=10, y=10, speed=3.5, neighbors=[1, 2, 3, 4, 5])}

    # Node 0 is a registered flow endpoint (e.g. CBR source)
    flow_endpoints = {0, 1}

    ids = OnlineIDS(
        env=env,
        aodv_nodes=aodv_nodes,
        nodes=nodes,
        model_path="ml/models/best_model.joblib",
        window_size=5.0,
        eval_interval=1.0,
        flow_endpoints=flow_endpoints,
    )

    # Ingest drop events and replies for node 0
    for t in [1.0, 2.0, 3.0, 4.0]:
        ids.ingest_event(sim_time=t, src=0, dst=1, pkt_id=int(t), pkt_type="DATA_DROP", hop_count=2, dropped_by=0, node_id=0, speed=3.5, neighbor_count=5)
        ids.ingest_event(sim_time=t, src=0, dst=1, pkt_id=int(t+10), pkt_type="RREP", hop_count=2, node_id=0, speed=3.5, neighbor_count=5)
        ids.ingest_event(sim_time=t, src=0, dst=-1, pkt_id=0, pkt_type="NODE_STATUS", hop_count=0, node_id=0, speed=3.5, neighbor_count=5)

    env.run(until=5.0)
    ids.step_detection(now=5.0)

    # Node 0 should be flagged with an alert but NEVER quarantined
    assert ids.is_blacklisted(0) is False
    assert ids.strikes.get(0, 0) == 0
    endpoint_alerts = [ev for ev in ids.isolation_events if ev.action == "ALERT_ENDPOINT_EXCLUDED" and ev.node_id == 0]
    assert len(endpoint_alerts) > 0
    assert len(endpoint_alerts) > 0


def test_simulation_runner_closed_loop_integration(tmp_path: Path):
    """Run an end-to-end 20s scenario with IDS enabled and verify isolation execution."""
    iso_log = tmp_path / "test_iso_log.csv"
    trace_log = tmp_path / "test_trace.csv"

    scenario_cfg = {
        "name": "closed_loop_test",
        "duration": 20.0,
        "nodes": 15,
        "area": [500, 500],
        "radio": {"range": 250.0, "loss_probability": 0.0},
        "mobility": {"speed_range": [1.0, 5.0], "pause_time": 2.0, "boundary": "wrap"},
        "flows": [{"src": 0, "dst": 14, "rate_pps": 5.0, "start_time": 1.0, "end_time": 19.0}],
        "attack": {
            "enabled": True,
            "type": "Blackhole",
            "attackers": "dynamic",
            "start_time": 2.0,
        },
        "ids": {
            "enabled": True,
            "window_size": 5.0,
            "eval_interval": 1.0,
            "threshold": 0.50,
            "quarantine_duration": 30.0,
            "strikes_required": 2,
            "isolation_log_path": str(iso_log),
        },
    }

    runner = SimulationRunner(
        scenario_config=scenario_cfg,
        seed=42,
        out_path=trace_log,
    )

    metrics = runner.run(duration=20.0)

    # 1. Simulation completes and returns metrics
    assert "pdr" in metrics
    assert metrics["data_sent"] > 0

    # 2. OnlineIDS was instantiated and ran
    assert runner.online_ids is not None
    assert runner.online_ids.isolation_log_path == iso_log

    # 3. Isolation log was exported and contains events
    assert iso_log.exists()
    with open(iso_log, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) > 0

    # 4. Attacker was targeted by isolation logic
    attacker_id = runner.attacker_ids[0]
    targeted_events = [ev for ev in runner.online_ids.isolation_events if ev.node_id == attacker_id]
    assert len(targeted_events) > 0


def test_closed_loop_blackhole_recovery():
    """Verify that AODV+IDS delivers statistically significant PDR recovery under Blackhole attacks."""
    e2_path = Path("scenarios/e2_blackhole_30n.json")
    base_cfg = load_scenario(e2_path)
    seed = 42
    sim_duration = 40.0

    # 1. Plain Baseline (no attack, no IDS)
    cfg_base = copy.deepcopy(base_cfg)
    cfg_base["attack"]["enabled"] = False
    cfg_base["ids"] = {"enabled": False}
    m_base = SimulationRunner(cfg_base, seed=seed).run(duration=sim_duration)

    # 2. Attack without IDS (attack enabled, no IDS)
    cfg_att = copy.deepcopy(base_cfg)
    cfg_att["attack"]["enabled"] = True
    cfg_att["ids"] = {"enabled": False}
    m_att = SimulationRunner(cfg_att, seed=seed).run(duration=sim_duration)

    # 3. Closed-Loop AODV+IDS
    cfg_ids = copy.deepcopy(base_cfg)
    cfg_ids["attack"]["enabled"] = True
    cfg_ids["ids"] = {
        "enabled": True,
        "model_path": "ml/models/best_model.joblib",
        "threshold": 0.50,
        "window_size": 5.0,
        "quarantine_duration": 30.0,
        "strikes_required": 2,
    }
    m_ids = SimulationRunner(cfg_ids, seed=seed).run(duration=sim_duration)

    pdr_base = m_base["pdr"]
    pdr_att = m_att["pdr"]
    pdr_ids = m_ids["pdr"]
    delta_pdr_abs = pdr_ids - pdr_att
    recovery_ratio = (delta_pdr_abs / (pdr_base - pdr_att)) * 100.0

    # Assertions
    assert pdr_att < pdr_base, f"Attack did not degrade PDR: base={pdr_base}, att={pdr_att}"
    assert pdr_ids > pdr_att, f"AODV+IDS did not improve PDR: ids={pdr_ids}, att={pdr_att}"
    assert delta_pdr_abs > 0.15, f"PDR recovery too low: delta={delta_pdr_abs:.4f} <= 0.15"
    assert recovery_ratio >= 50.0, f"Recovery ratio too low: {recovery_ratio:.1f}% < 50.0%"


def test_closed_loop_grayhole_recovery():
    """Verify that AODV+IDS delivers positive PDR recovery under Grayhole attacks."""
    e2_path = Path("scenarios/e2_blackhole_30n.json")
    base_cfg = load_scenario(e2_path)
    seed = 42
    sim_duration = 40.0

    # 1. Plain Baseline
    cfg_base = copy.deepcopy(base_cfg)
    cfg_base["attack"]["enabled"] = False
    cfg_base["ids"] = {"enabled": False}
    m_base = SimulationRunner(cfg_base, seed=seed).run(duration=sim_duration)

    # 2. Grayhole Attack (p=0.5)
    cfg_att = copy.deepcopy(base_cfg)
    cfg_att["attack"] = {
        "enabled": True,
        "type": "Grayhole",
        "drop_prob": 0.5,
        "attackers": "dynamic",
    }
    cfg_att["ids"] = {"enabled": False}
    m_att = SimulationRunner(cfg_att, seed=seed).run(duration=sim_duration)

    # 3. Grayhole with AODV+IDS
    cfg_ids = copy.deepcopy(base_cfg)
    cfg_ids["attack"] = {
        "enabled": True,
        "type": "Grayhole",
        "drop_prob": 0.5,
        "attackers": "dynamic",
    }
    cfg_ids["ids"] = {
        "enabled": True,
        "model_path": "ml/models/best_model.joblib",
        "threshold": 0.50,
        "window_size": 5.0,
        "quarantine_duration": 30.0,
        "strikes_required": 2,
    }
    m_ids = SimulationRunner(cfg_ids, seed=seed).run(duration=sim_duration)

    pdr_att = m_att["pdr"]
    pdr_ids = m_ids["pdr"]

    # Assert positive recovery on subtle attack
    assert pdr_ids > pdr_att, f"AODV+IDS did not improve Grayhole PDR: ids={pdr_ids}, att={pdr_att}"


def test_benchmark_script_smoke(tmp_path: Path):
    """Verify that scripts/run_closed_loop_benchmark.py runs in smoke mode and writes valid outputs."""
    out_dir = tmp_path / "bench_results"
    cmd = [
        sys.executable,
        "scripts/run_closed_loop_benchmark.py",
        "--smoke",
        "--duration",
        "20.0",
        "--out-dir",
        str(out_dir),
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert res.returncode == 0, f"Benchmark script failed: {res.stderr}\n{res.stdout}"

    # Verify metrics CSV
    csv_file = out_dir / "closed_loop_metrics.csv"
    assert csv_file.exists(), "closed_loop_metrics.csv was not created"
    df_metrics = pd.read_csv(csv_file)
    assert len(df_metrics) == 3, f"Expected 3 triad rows in smoke mode, got {len(df_metrics)}"
    assert set(df_metrics["mode"].tolist()) == {"Baseline", "Attack", "AODV+IDS"}

    # Verify Markdown report
    md_file = out_dir / "closed_loop_report.md"
    assert md_file.exists(), "closed_loop_report.md was not created"
    report_text = md_file.read_text(encoding="utf-8")
    assert "# Closed-Loop IDS Mitigation & Network Re-Evaluation Report" in report_text
    assert "Triad Benchmark Results" in report_text

    # Verify isolation events CSV
    events_file = out_dir / "isolation_events.csv"
    assert events_file.exists(), "isolation_events.csv was not created"
    with open(events_file, mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) > 0, "No isolation events were recorded in smoke run"

