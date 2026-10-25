"""CLI entry point and composition root for MANET simulations.

Handles deterministic scenario execution, SimPy environment lifecycle,
Random Waypoint mobility, unit-disk radio connectivity, RFC 3561 AODV routing,
CBR/UDP traffic generation, and trace logging.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
import json
from pathlib import Path
import random
from typing import Any, Dict, Generator, List, Optional, Tuple

import networkx as nx
import simpy

from attacks.registry import create_attack_strategy
from simulator.aodv import AODVNode, RERR, RREP, RREQ, RouteEntry
from simulator.metrics import compute_metrics
from simulator.mobility import RandomWaypoint, random_position
from simulator.radio import calculate_distance, compute_all_neighbors, get_neighbors
from simulator.traffic import CBRTraffic, DataPacket, generate_flows


@dataclass
class NodeState:
    """Represents node state during simulation."""
    node_id: int
    x: float = 0.0
    y: float = 0.0
    speed: float = 0.0
    neighbors: List[int] = field(default_factory=list)


class SimulationRunner:
    """Orchestrates deterministic simulation execution."""

    TRACE_HEADER = ["time", "src", "dst", "pkt_id", "type", "hop_count", "dropped_by"]
    HOP_DELAY = 0.002  # 2ms wireless propagation and MAC processing delay per hop

    def __init__(self, scenario_config: Dict[str, Any], seed: int, out_path: Optional[Path] = None):
        self.scenario = scenario_config
        self.seed = seed
        self.out_path = Path(out_path) if out_path else None
        self.rng = random.Random(seed)
        self.env = simpy.Environment()

        self.nodes: Dict[int, NodeState] = {}
        self.mobility_models: Dict[int, RandomWaypoint] = {}
        self.aodv_nodes: Dict[int, AODVNode] = {}
        self.traffic_flows: List[CBRTraffic] = []
        self.trace_rows: List[List[Any]] = []
        self.attacker_ids: List[int] = []

        self._pkt_counter = 1

        # Config extraction
        self.area = self.scenario.get("area", [1000, 1000])
        self.radio_range = float(self.scenario.get("radio", {}).get("range", 250.0))
        self.loss_prob = float(self.scenario.get("radio", {}).get("loss_probability", 0.0))
        self.duration = float(self.scenario.get("duration", 300.0))

    def next_pkt_id(self) -> int:
        """Generate unique monotonic packet ID."""
        pid = self._pkt_counter
        self._pkt_counter += 1
        return pid

    def initialize_nodes(self) -> None:
        """Initialize node states, mobility models, and AODV engines."""
        num_nodes = int(self.scenario.get("nodes", 30))
        mob_cfg = self.scenario.get("mobility", {})
        speed_range = tuple(mob_cfg.get("speed_range", [1.0, 10.0]))
        pause_time = float(mob_cfg.get("pause_time", 5.0))
        boundary = mob_cfg.get("boundary", "wrap")

        # Deterministic generation for each node in sorted order
        for node_id in range(num_nodes):
            init_pos = random_position(self.rng, self.area)
            mob = RandomWaypoint(
                env=self.env,
                node_id=node_id,
                area=self.area,
                speed_range=speed_range,
                pause_time=pause_time,
                rng=self.rng,
                initial_pos=init_pos,
                boundary=boundary,
            )
            self.mobility_models[node_id] = mob
            self.nodes[node_id] = NodeState(
                node_id=node_id,
                x=init_pos[0],
                y=init_pos[1],
            )

            # Initialize AODV node
            aodv_node = AODVNode(
                node_id=node_id,
                get_time=lambda: self.env.now,
                send_packet_cb=lambda target, msg, src=node_id: self.send_network_message(src, target, msg),
                log_event_cb=self.log_event,
            )
            self.aodv_nodes[node_id] = aodv_node

        # Initial neighbor discovery
        self.update_topology()

        # Attack configuration wiring
        self.attacker_ids = []
        attack_cfg = self.scenario.get("attack", {})
        if attack_cfg.get("enabled", False):
            attack_type = attack_cfg.get("type", "Blackhole")
            attackers_spec = attack_cfg.get("attackers", "dynamic")
            if attackers_spec == "dynamic" or attackers_spec == [] or attackers_spec is None:
                chosen_id = self.select_dynamic_attacker(self.scenario.get("flows", []))
                attackers_list = [chosen_id]
            elif isinstance(attackers_spec, list):
                attackers_list = attackers_spec
            elif isinstance(attackers_spec, int):
                attackers_list = [attackers_spec]
            else:
                attackers_list = []

            self.attacker_ids = attackers_list
            seq_offset = int(attack_cfg.get("seq_offset", 1000))
            spoofed_hops = int(attack_cfg.get("spoofed_hops", 1))
            for aid in self.attacker_ids:
                if aid in self.aodv_nodes:
                    strategy = create_attack_strategy(attack_type, seq_offset=seq_offset, spoofed_hops=spoofed_hops)
                    self.aodv_nodes[aid].attack_behavior = strategy
                    if attack_type.lower() == "blackhole":
                        self.aodv_nodes[aid].is_blackhole = True

        # Start periodic topology refresh process
        self.env.process(self._periodic_topology_refresh())

    def select_dynamic_attacker(self, flows: List[Dict[str, Any]]) -> int:
        """Select intermediate node along active CBR flow paths to guarantee interception."""
        G = nx.Graph()
        for nid, node_state in self.nodes.items():
            G.add_node(nid)
            for nb in node_state.neighbors:
                G.add_edge(nid, nb)

        # Protect flow endpoints from being selected as malicious nodes
        endpoints = set(f["src"] for f in flows) | set(f["dst"] for f in flows)

        # Step 1: Count intermediate occurrences on shortest multi-hop flow paths
        path_intermediates: Dict[int, int] = {}
        for f in flows:
            s, d = f["src"], f["dst"]
            if nx.has_path(G, s, d):
                p = nx.shortest_path(G, s, d)
                for node in p[1:-1]:
                    if node not in endpoints:
                        path_intermediates[node] = path_intermediates.get(node, 0) + 1

        if path_intermediates:
            # Pick intermediate node appearing on the most paths, breaking ties by degree and lowest node ID
            return max(path_intermediates.keys(), key=lambda n: (path_intermediates[n], G.degree[n], -n))

        # Step 2: Fallback to non-endpoint neighbors of active sources
        source_nbrs: Dict[int, int] = {}
        for f in flows:
            s = f["src"]
            for nbr in G.neighbors(s):
                if nbr not in endpoints:
                    source_nbrs[nbr] = source_nbrs.get(nbr, 0) + G.degree[nbr]
        if source_nbrs:
            return max(source_nbrs.keys(), key=lambda n: (source_nbrs[n], -n))

        # Step 3: Fallback to highest betweenness centrality among non-endpoints
        bc = nx.betweenness_centrality(G)
        candidates = {n: bc[n] for n in sorted(G.nodes) if n not in endpoints}
        if candidates:
            return max(candidates.keys(), key=lambda n: (candidates[n], -n))

        # Final deterministic fallback
        non_endpoints = [n for n in sorted(self.nodes.keys()) if n not in endpoints]
        return non_endpoints[0] if non_endpoints else 0

    def get_node_position(self, node_id: int) -> Tuple[float, float]:
        """Get current (x, y) coordinates for a node."""
        mob = self.mobility_models[node_id]
        return (mob.state.x, mob.state.y)

    def get_all_positions(self) -> Dict[int, Tuple[float, float]]:
        """Get positions for all nodes keyed by sorted node ID."""
        return {nid: self.get_node_position(nid) for nid in sorted(self.nodes.keys())}

    def update_topology(self) -> None:
        """Recalculate dynamic neighbor sets for all nodes."""
        positions = self.get_all_positions()
        all_neighbors = compute_all_neighbors(
            positions=positions,
            range_m=self.radio_range,
            rng=self.rng,
            loss_prob=self.loss_prob,
        )
        for nid, nbs in all_neighbors.items():
            node = self.nodes[nid]
            node.x, node.y = positions[nid]
            node.speed = self.mobility_models[nid].state.current_speed
            node.neighbors = nbs

    def _periodic_topology_refresh(self, interval: float = 1.0) -> Generator[simpy.Event, None, None]:
        """Periodically refresh topology and neighbor tables."""
        while True:
            yield self.env.timeout(interval)
            self.update_topology()

    def send_network_message(self, src: int, target: int, msg: Any) -> None:
        """Schedule message transmission across the wireless medium."""
        self.env.process(self._transmit_process(src, target, msg))

    def _transmit_process(self, src: int, target: int, msg: Any) -> Generator[simpy.Event, None, None]:
        """Deliver routing control messages with simulated wireless delay."""
        yield self.env.timeout(self.HOP_DELAY)

        # Broadcast
        if target == -1:
            neighbors = list(self.nodes[src].neighbors)
            for nbr in sorted(neighbors):
                if isinstance(msg, RREQ):
                    self.aodv_nodes[nbr].handle_rreq(msg, prev_hop=src)
                elif isinstance(msg, RERR):
                    self.aodv_nodes[nbr].handle_rerr(msg, prev_hop=src)
        else:
            # Unicast
            if target in self.nodes[src].neighbors:
                if isinstance(msg, RREP):
                    self.aodv_nodes[target].handle_rrep(msg, prev_hop=src)
                    # Check if destination reached and pending buffered data packets can now be sent
                    if msg.originator == target:
                        self._flush_packet_buffer(target, msg.dest)
                elif isinstance(msg, RREQ):
                    self.aodv_nodes[target].handle_rreq(msg, prev_hop=src)
                elif isinstance(msg, RERR):
                    self.aodv_nodes[target].handle_rerr(msg, prev_hop=src)
            else:
                # Link broken during unicast
                self.log_event(
                    sim_time=self.env.now,
                    src=src,
                    dst=target,
                    pkt_id=0,
                    pkt_type="LINK_BROKEN",
                    hop_count=1,
                    dropped_by=src,
                )
                self.aodv_nodes[src].send_rerr(target)

    def send_data_packet(self, pkt: DataPacket) -> None:
        """Entry point for application CBR traffic generator."""
        self.log_event(
            sim_time=self.env.now,
            src=pkt.src,
            dst=pkt.dst,
            pkt_id=pkt.pkt_id,
            pkt_type="DATA_SENT",
            hop_count=0,
        )
        self.env.process(self._route_and_forward_data(pkt, current_hop=pkt.src))

    def _route_and_forward_data(self, pkt: DataPacket, current_hop: int) -> Generator[simpy.Event, None, None]:
        """Hop-by-hop forwarding of application data packets using AODV routes."""
        if current_hop == pkt.dst:
            self.log_event(
                sim_time=self.env.now,
                src=pkt.src,
                dst=pkt.dst,
                pkt_id=pkt.pkt_id,
                pkt_type="DATA_RECV",
                hop_count=pkt.hop_count,
            )
            return

        aodv_node = self.aodv_nodes[current_hop]

        # Check for attack injection behavior
        if aodv_node.attack_behavior is not None and hasattr(aodv_node.attack_behavior, "should_drop_data") and aodv_node.attack_behavior.should_drop_data(pkt.src, pkt.dst, pkt.pkt_id):
            self.log_event(
                sim_time=self.env.now,
                src=pkt.src,
                dst=pkt.dst,
                pkt_id=pkt.pkt_id,
                pkt_type="DATA_DROP",
                hop_count=pkt.hop_count,
                dropped_by=current_hop,
            )
            return

        if aodv_node.is_blackhole:
            self.log_event(
                sim_time=self.env.now,
                src=pkt.src,
                dst=pkt.dst,
                pkt_id=pkt.pkt_id,
                pkt_type="DATA_DROP",
                hop_count=pkt.hop_count,
                dropped_by=current_hop,
            )
            return

        if aodv_node.is_grayhole and self.rng.random() < aodv_node.grayhole_drop_prob:
            self.log_event(
                sim_time=self.env.now,
                src=pkt.src,
                dst=pkt.dst,
                pkt_id=pkt.pkt_id,
                pkt_type="DATA_DROP",
                hop_count=pkt.hop_count,
                dropped_by=current_hop,
            )
            return

        route = aodv_node.get_route(pkt.dst)
        if route is None:
            # Buffer packet at source if route not yet discovered
            if current_hop == pkt.src:
                if pkt.dst not in aodv_node.packet_buffer:
                    aodv_node.packet_buffer[pkt.dst] = []
                aodv_node.packet_buffer[pkt.dst].append(pkt)
                if pkt.dst not in aodv_node.pending_rreqs:
                    aodv_node.initiate_route_discovery(pkt.dst)
            else:
                # Intermediate node lost route
                self.log_event(
                    sim_time=self.env.now,
                    src=pkt.src,
                    dst=pkt.dst,
                    pkt_id=pkt.pkt_id,
                    pkt_type="DATA_DROP",
                    hop_count=pkt.hop_count,
                    dropped_by=current_hop,
                )
                aodv_node.send_rerr(pkt.dst)
            return

        next_hop = route.next_hop
        yield self.env.timeout(self.HOP_DELAY)

        # Check link availability
        if next_hop in self.nodes[current_hop].neighbors:
            pkt.hop_count += 1
            self.log_event(
                sim_time=self.env.now,
                src=pkt.src,
                dst=pkt.dst,
                pkt_id=pkt.pkt_id,
                pkt_type="DATA_FWD",
                hop_count=pkt.hop_count,
            )
            self.env.process(self._route_and_forward_data(pkt, current_hop=next_hop))
        else:
            # Link failed
            self.log_event(
                sim_time=self.env.now,
                src=pkt.src,
                dst=pkt.dst,
                pkt_id=pkt.pkt_id,
                pkt_type="DATA_DROP",
                hop_count=pkt.hop_count,
                dropped_by=current_hop,
            )
            aodv_node.send_rerr(pkt.dst)

    def _flush_packet_buffer(self, node_id: int, dest: int) -> None:
        """Send all packets waiting for route discovery to destination."""
        aodv_node = self.aodv_nodes[node_id]
        buffered = aodv_node.packet_buffer.pop(dest, [])
        for pkt in buffered:
            self.env.process(self._route_and_forward_data(pkt, current_hop=node_id))

    def initialize_traffic(self) -> None:
        """Initialize CBR application flows from scenario config."""
        flows_cfg = self.scenario.get("flows", [])
        self.traffic_flows = generate_flows(
            env=self.env,
            flow_configs=flows_cfg,
            send_fn=self.send_data_packet,
            get_pkt_id_fn=self.next_pkt_id,
        )

    def log_event(
        self,
        sim_time: float,
        src: int,
        dst: int,
        pkt_id: int,
        pkt_type: str,
        hop_count: int,
        dropped_by: Optional[int] = None,
    ) -> None:
        """Record a packet event in the trace log."""
        dropped_str = str(dropped_by) if dropped_by is not None else ""
        self.trace_rows.append([
            f"{sim_time:.6f}",
            src,
            dst,
            pkt_id,
            pkt_type,
            hop_count,
            dropped_str,
        ])

    def write_traces(self) -> None:
        """Write collected trace events to CSV file."""
        if not self.out_path:
            return

        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.out_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.TRACE_HEADER)
            writer.writerows(self.trace_rows)

    def run(self, duration: Optional[float] = None) -> Dict[str, float]:
        """Run the simulation up to duration seconds and compute metrics."""
        sim_duration = duration if duration is not None else self.duration
        self.initialize_nodes()
        self.initialize_traffic()

        self.env.run(until=sim_duration)
        self.write_traces()

        metrics = compute_metrics(self.trace_rows, sim_duration=sim_duration)
        return metrics


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Deterministic MANET Simulator Runner")
    parser.add_argument("--scenario", type=str, required=True, help="Path to scenario JSON config")
    parser.add_argument("--seed", type=int, required=True, help="Explicit integer seed for determinism")
    parser.add_argument("--out", type=str, required=True, help="Output path for CSV trace log")
    return parser.parse_args(args)


def load_scenario(path: Path | str) -> Dict[str, Any]:
    """Load and parse scenario configuration JSON."""
    scenario_path = Path(path)
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")
    with open(scenario_path, "r", encoding="utf-8") as f:
        return json.load(f)


def main(args: Optional[List[str]] = None) -> None:
    """CLI execution entrypoint."""
    parsed = parse_args(args)
    scenario_config = load_scenario(parsed.scenario)
    runner = SimulationRunner(
        scenario_config=scenario_config,
        seed=parsed.seed,
        out_path=Path(parsed.out),
    )
    metrics = runner.run()

    print("\n=== Simulation Results ===")
    print(f"Packet Delivery Ratio (PDR): {metrics['pdr'] * 100:.2f}%")
    print(f"Throughput: {metrics['throughput_bps'] / 1000.0:.2f} kbps")
    print(f"Average Delay: {metrics['avg_delay_s'] * 1000.0:.2f} ms")
    print(f"Packet Loss Ratio: {metrics['packet_loss_ratio'] * 100:.2f}%")
    print(f"Routing Overhead: {metrics['routing_overhead']:.4f}")
    print(f"Packets Sent: {int(metrics['data_sent'])}, Received: {int(metrics['data_received'])}")
    print(f"Trace written to: {parsed.out}\n")


if __name__ == "__main__":
    main()
