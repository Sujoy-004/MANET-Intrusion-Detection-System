"""Regression and integration tests for AODV route-discovery recovery lifecycle.

Verifies:
- Per-destination route discovery state and SimPy timeout scheduling
- Bounded retransmission attempts and exponential backoff
- Duplicate concurrent discovery prevention
- Pending-state cleanup upon valid RREP reception
- Blacklisted RREP rejection without clearing discovery state or flushing buffers
- Elimination of the blacklisted RREP storm loop under Online IDS
- Buffer capacity limits, packet expiration, and graceful flushing
- Deterministic recovery from temporary network partitions
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, List, Optional, Set, Tuple

import pytest
import simpy

from ml.response import OnlineIDS
from simulator.aodv import AODVNode, DiscoveryState, RREP, RREQ, RouteEntry
from simulator.metrics import compute_metrics
from simulator.run_scenario import NodeState, SimulationRunner
from simulator.traffic import DataPacket


def test_duplicate_concurrent_discovery_prevention():
    """Verify initiate_route_discovery rejects concurrent discovery for same destination."""
    sent: List[Any] = []
    events: List[Any] = []
    node = AODVNode(
        node_id=0,
        get_time=lambda: 10.0,
        send_packet_cb=lambda target, msg: sent.append((target, msg)),
        log_event_cb=lambda **kwargs: events.append(kwargs),
    )

    # First initiation succeeds
    assert node.initiate_route_discovery(dest=5) is True
    assert 5 in node.pending_rreqs
    assert len(sent) == 1

    # Second concurrent initiation must be rejected
    assert node.initiate_route_discovery(dest=5) is False
    assert len(sent) == 1  # No duplicate RREQ broadcast


def test_rreq_timeout_and_bounded_retries():
    """Verify RREQ retries with exponential backoff and eventual retry exhaustion."""
    env = simpy.Environment()
    sent_rreqs: List[Tuple[float, int, RREQ]] = []
    events: List[Any] = []

    def schedule_timer(delay: float, cb: Any):
        def _proc():
            yield env.timeout(delay)
            cb()
        return env.process(_proc())

    node = AODVNode(
        node_id=0,
        get_time=lambda: env.now,
        send_packet_cb=lambda target, msg: sent_rreqs.append((env.now, target, msg)),
        log_event_cb=lambda **kwargs: events.append(kwargs),
        schedule_timer_cb=schedule_timer,
        rreq_timeout=2.0,
        rreq_retries=2,
        discovery_cooldown=3.0,
        backoff_mult=2.0,
    )

    # Buffer a packet and initiate discovery
    pkt = DataPacket(pkt_id=1, src=0, dst=5, payload_size=512, timestamp=env.now)
    node.buffer_packet(pkt)
    assert node.initiate_route_discovery(dest=5) is True

    # At t=0: initial RREQ sent (retries=0, timeout=2.0)
    assert len(sent_rreqs) == 1
    assert sent_rreqs[0][0] == pytest.approx(0.0)
    assert 5 in node.pending_rreqs
    assert node.discovery_states[5].retries == 0

    # Advance to t=2.0: first timeout fires -> retry 1 sent (retries=1, timeout=4.0)
    env.run(until=2.1)
    assert len(sent_rreqs) == 2
    assert sent_rreqs[1][0] == pytest.approx(2.0)
    assert node.discovery_states[5].retries == 1

    # Advance to t=6.0: second timeout fires -> retry 2 sent (retries=2, timeout=8.0)
    env.run(until=6.1)
    assert len(sent_rreqs) == 3
    assert sent_rreqs[2][0] == pytest.approx(6.0)
    assert node.discovery_states[5].retries == 2

    # Advance to t=14.0: third timeout fires -> retries exhausted!
    env.run(until=14.1)
    assert len(sent_rreqs) == 3  # No further RREQs sent
    assert 5 not in node.pending_rreqs
    assert 5 not in node.discovery_states
    assert node.is_discovery_in_cooldown(5) is True
    # Buffered packet must have been dropped upon exhaustion
    assert 5 not in node.packet_buffer or len(node.packet_buffer[5]) == 0
    drop_events = [e for e in events if e.get("pkt_type") == "DATA_DROP"]
    assert len(drop_events) >= 1


def test_pending_state_cleanup_on_valid_rrep():
    """Verify valid RREP cleans up pending state, cancels timers, and establishes route."""
    env = simpy.Environment()
    sent: List[Any] = []
    events: List[Any] = []

    def schedule_timer(delay: float, cb: Any):
        def _proc():
            yield env.timeout(delay)
            cb()
        return env.process(_proc())

    node = AODVNode(
        node_id=0,
        get_time=lambda: env.now,
        send_packet_cb=lambda target, msg: sent.append((target, msg)),
        log_event_cb=lambda **kwargs: events.append(kwargs),
        schedule_timer_cb=schedule_timer,
    )

    node.initiate_route_discovery(dest=7)
    assert 7 in node.pending_rreqs
    assert 7 in node.discovery_states

    # Valid RREP arrives from neighbor 2 for dest 7
    rrep = RREP(originator=0, dest=7, dest_seq=10, hop_count=1, lifetime=10.0)
    accepted = node.handle_rrep(rrep, prev_hop=2)

    assert accepted is True
    assert 7 not in node.pending_rreqs
    assert 7 not in node.discovery_states
    assert node.get_route(7) is not None
    assert node.get_route(7).next_hop == 2

    # Ensure timer does not retransmit after cancellation
    initial_sent_count = len(sent)
    env.run(until=10.0)
    assert len(sent) == initial_sent_count  # No timeout retransmissions occurred


def test_blacklisted_rrep_rejection():
    """Verify RREP from blacklisted node is rejected and does not clear pending discovery."""
    blacklisted: Set[int] = {21}
    node = AODVNode(
        node_id=8,
        get_time=lambda: 10.0,
        send_packet_cb=lambda target, msg: None,
        log_event_cb=lambda **kwargs: None,
        is_blacklisted_cb=lambda nid: nid in blacklisted,
    )

    node.initiate_route_discovery(dest=1)
    assert 1 in node.pending_rreqs
    assert 1 in node.discovery_states

    # Blackhole attacker 21 sends spoofed RREP
    malicious_rrep = RREP(originator=8, dest=1, dest_seq=1000, hop_count=1, lifetime=10.0)
    accepted = node.handle_rrep(malicious_rrep, prev_hop=21)

    # Must be completely rejected
    assert accepted is False
    assert node.get_route(1) is None
    # Discovery state must NOT be prematurely cleared by rejected RREP
    assert 1 in node.pending_rreqs
    assert 1 in node.discovery_states


def test_no_buffer_flushing_following_rejected_rrep():
    """Verify rejected RREP never triggers packet buffer flushing."""
    env = simpy.Environment()
    runner = SimulationRunner(
        scenario_config={
            "name": "test_no_flush",
            "nodes": 3,
            "area": [500, 500],
            "radio": {"range": 250},
            "mobility": {"model": "RandomWaypoint", "speed_range": [0, 0]},
            "duration": 50,
            "flows": [],
        },
        seed=42,
    )
    runner.initialize_nodes()

    # Manually configure nodes 0 (source), 1 (attacker), 2 (destination)
    runner.nodes[0].neighbors = {1}
    runner.nodes[1].neighbors = {0, 2}
    runner.nodes[2].neighbors = {1}

    # Buffer a packet at node 0 for dest 2
    pkt = DataPacket(pkt_id=99, src=0, dst=2, payload_size=512, timestamp=0.0)
    runner.aodv_nodes[0].buffer_packet(pkt)
    runner.aodv_nodes[0].initiate_route_discovery(dest=2)

    # Attacker 1 is blacklisted in online IDS or callback
    runner.aodv_nodes[0].is_blacklisted_cb = lambda nid: nid == 1

    # Attacker 1 transmits RREP to node 0
    bad_rrep = RREP(originator=0, dest=2, dest_seq=500, hop_count=1, lifetime=10.0)
    runner.send_network_message(src=1, target=0, msg=bad_rrep)

    # Let transmission process run
    env_runner = runner.env
    env_runner.run(until=0.01)

    # Verify RREP was rejected: no route installed and buffer was NOT flushed
    assert runner.aodv_nodes[0].get_route(2) is None
    assert len(runner.aodv_nodes[0].packet_buffer.get(2, [])) == 1
    assert runner.aodv_nodes[0].packet_buffer[2][0].pkt_id == 99


def test_packet_buffer_limits_and_expiration():
    """Verify buffer enforces max queue capacity and max buffer lifetime."""
    current_time = 100.0
    events: List[Any] = []
    node = AODVNode(
        node_id=0,
        get_time=lambda: current_time,
        send_packet_cb=lambda target, msg: None,
        log_event_cb=lambda **kwargs: events.append(kwargs),
        max_buffer_per_dest=3,
        max_buffer_time=10.0,
    )

    # 1. Enforce queue limit: adding 4 packets should drop oldest
    for pid in range(1, 5):
        pkt = DataPacket(pkt_id=pid, src=0, dst=1, payload_size=512, timestamp=current_time)
        node.buffer_packet(pkt)

    buf = node.packet_buffer[1]
    assert len(buf) == 3
    # Packet 1 was dropped, packets 2, 3, 4 remain
    assert [p.pkt_id for p in buf] == [2, 3, 4]
    drops = [e for e in events if e.get("pkt_type") == "DATA_DROP" and e.get("pkt_id") == 1]
    assert len(drops) == 1

    # 2. Enforce expiration: advance time by 15s (> max_buffer_time=10s)
    current_time = 115.0
    eligible = node.get_buffered_packets(dest=1)
    # All 3 remaining packets should have expired
    assert len(eligible) == 0
    assert 1 not in node.packet_buffer


def test_late_stale_rrep_handling():
    """Verify late or lower sequence number RREPs do not overturn newer routes."""
    current_time = 50.0
    node = AODVNode(
        node_id=0,
        get_time=lambda: current_time,
        send_packet_cb=lambda target, msg: None,
        log_event_cb=lambda **kwargs: None,
    )

    # Route already known with seq 20 via hop 1
    node.update_route(dest=5, next_hop=1, hop_count=2, dest_seq=20, lifetime=10.0)

    # Stale RREP arrives with lower seq 10 and more hops via hop 2
    stale_rrep = RREP(originator=0, dest=5, dest_seq=10, hop_count=3, lifetime=10.0)
    accepted = node.handle_rrep(stale_rrep, prev_hop=2)

    assert accepted is False
    route = node.get_route(5)
    assert route.next_hop == 1
    assert route.dest_seq == 20


def test_deterministic_network_partition_recovery():
    """Verify node recovers and delivers buffered packets when partitioned network reconnects."""
    scenario = {
        "name": "partition_recovery",
        "nodes": 3,
        "area": [1000, 1000],
        "radio": {"range": 150},
        "mobility": {"model": "RandomWaypoint", "speed_range": [0, 0]},
        "duration": 100,
        "flows": [],
    }
    runner = SimulationRunner(scenario_config=scenario, seed=42)
    runner.initialize_nodes()

    # Controlled positions: Node 0 at (0, 0), Node 1 at (100, 0), Node 2 initially at (500, 0) (partitioned)
    pos = {0: (0.0, 0.0), 1: (100.0, 0.0), 2: (500.0, 0.0)}
    runner.get_node_position = lambda nid: pos[nid]
    runner.update_topology()

    # Send data from Node 0 to Node 2 at t=0
    pkt = DataPacket(pkt_id=101, src=0, dst=2, payload_size=512, timestamp=0.0)
    runner.send_data_packet(pkt)

    # Run for 5 seconds: Node 0 tries discovery, times out, retries
    runner.env.run(until=5.0)
    assert runner.aodv_nodes[0].get_route(2) is None
    # Packet is still buffered
    assert len(runner.aodv_nodes[0].packet_buffer.get(2, [])) > 0

    # At t=5.0, Node 2 moves into range at (180, 0) -> partition heals!
    pos[2] = (180.0, 0.0)
    runner.update_topology()

    # Run until t=30.0: next retry succeeds, route discovers via Node 1, packet is delivered!
    runner.env.run(until=30.0)

    delivered = [
        row for row in runner.trace_rows
        if row[4] == "DATA_RECV" and row[1] == 0 and row[2] == 2 and row[3] == 101
    ]
    assert len(delivered) == 1, "Buffered packet was not delivered following partition recovery"


def test_blackhole_ids_quarantine_no_rreq_storm_integration():
    """Verify that in Blackhole scenario with IDS enabled, attacker is quarantined without RREQ storm.
    
    Verifies:
    1. Attacker is successfully quarantined by OnlineIDS.
    2. RREQ count remains bounded (< 500), proving complete elimination of the 16k storm loop.
    3. Routing overhead remains normal (< 0.20 vs prototype 5.30).
    4. PDR significantly recovers (> 50% vs attack 18.10%).
    5. No pending discoveries or buffered packets leak at simulation end.
    """
    with open("scenarios/e2_blackhole_30n.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    # Enable Online IDS with standard configuration
    ids_cfg = config.setdefault("ids", {})
    ids_cfg["enabled"] = True
    ids_cfg["model_path"] = "ml/models/best_model.joblib"
    ids_cfg["threshold"] = 0.50
    ids_cfg["quarantine_duration"] = 30.0
    ids_cfg["strikes_required"] = 2

    runner = SimulationRunner(scenario_config=config, seed=42)
    metrics = runner.run()

    # 1. Attacker node 21 must be quarantined
    assert runner.online_ids is not None
    assert len(runner.online_ids.isolation_events) > 0
    isolated_nodes = set(runner.online_ids.quarantined_nodes.keys())
    # Attacker ID for e2_blackhole_30n is 21
    assert 21 in runner.attacker_ids
    assert any(ev.node_id == 21 for ev in runner.online_ids.isolation_events)

    # 2. Control packet counts and storm elimination
    rreq_count = sum(1 for row in runner.trace_rows if row[4] == "RREQ")
    rrep_count = sum(1 for row in runner.trace_rows if row[4] == "RREP")
    assert rreq_count < 500, f"RREQ storm detected: {rreq_count} RREQs (must be < 500)"
    assert metrics["routing_overhead"] < 0.20, f"High overhead: {metrics['routing_overhead']:.4f} (must be < 0.20)"

    # 3. PDR recovery
    assert metrics["pdr"] > 0.50, f"PDR failed to recover: {metrics['pdr']*100:.2f}%"

    # 4. Clean pending and buffer state
    total_pending = sum(len(node.pending_rreqs) for node in runner.aodv_nodes.values())
    total_buffered = sum(sum(len(q) for q in node.packet_buffer.values()) for node in runner.aodv_nodes.values())
    assert total_pending == 0, f"Stale pending discoveries remain: {total_pending}"
    assert total_buffered == 0, f"Buffered packets leaked: {total_buffered}"
