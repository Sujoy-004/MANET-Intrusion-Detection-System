"""CLI entry point and composition root for MANET simulations.

Handles deterministic scenario execution, SimPy environment lifecycle,
and trace logging.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass, field
import json
from pathlib import Path
import random
from typing import Any, Dict, List, Optional

import simpy


@dataclass
class NodeState:
    """Represents node state during simulation."""
    node_id: int
    x: float = 0.0
    y: float = 0.0
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
        self.trace_rows: List[List[Any]] = []

    def initialize_nodes(self) -> None:
        """Initialize node states and initial random positions uniformly."""
        num_nodes = int(self.scenario.get("nodes", 30))
        area = self.scenario.get("area", [1000, 1000])
        max_x, max_y = float(area[0]), float(area[1])

        # Use sorted keys / explicit indexing for determinism
        for node_id in range(num_nodes):
            x = self.rng.uniform(0.0, max_x)
            y = self.rng.uniform(0.0, max_y)
            self.nodes[node_id] = NodeState(node_id=node_id, x=x, y=y)

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

        # Minimal initial trace event as tracer slice proof
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
