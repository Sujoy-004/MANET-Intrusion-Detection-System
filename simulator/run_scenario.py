"""CLI entry point and composition root for MANET simulations.

Handles deterministic scenario execution, SimPy environment lifecycle,
mobility, radio connectivity, and trace logging.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
import json
from pathlib import Path
import random
from typing import Any, Dict, Generator, List, Optional, Tuple

import simpy

from simulator.mobility import RandomWaypoint, random_position
from simulator.radio import calculate_distance, compute_all_neighbors, get_neighbors


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

    def __init__(self, scenario_config: Dict[str, Any], seed: int, out_path: Optional[Path] = None):
        self.scenario = scenario_config
        self.seed = seed
        self.out_path = Path(out_path) if out_path else None
        self.rng = random.Random(seed)
        self.env = simpy.Environment()
        self.nodes: Dict[int, NodeState] = {}
        self.mobility_models: Dict[int, RandomWaypoint] = {}
        self.trace_rows: List[List[Any]] = []

        # Config extraction
        self.area = self.scenario.get("area", [1000, 1000])
        self.radio_range = float(self.scenario.get("radio", {}).get("range", 250.0))
        self.loss_prob = float(self.scenario.get("radio", {}).get("loss_probability", 0.0))

    def initialize_nodes(self) -> None:
        """Initialize node states, mobility models, and initial positions."""
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

        # Initial neighbor discovery
        self.update_topology()

        # Start periodic topology refresh process
        self.env.process(self._periodic_topology_refresh())

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

    def run(self, duration: Optional[float] = None) -> None:
        """Run the simulation up to duration seconds."""
        sim_duration = duration if duration is not None else float(self.scenario.get("duration", 300.0))
        self.initialize_nodes()

        # Log initialization event
        if self.nodes:
            self.log_event(
                sim_time=self.env.now,
                src=0,
                dst=min(1, len(self.nodes) - 1),
                pkt_id=0,
                pkt_type="INIT",
                hop_count=0,
                dropped_by=None,
            )

        self.env.run(until=sim_duration)
        self.write_traces()


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
    runner.run()


if __name__ == "__main__":
    main()
