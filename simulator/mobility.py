"""Random Waypoint (RWP) mobility model for MANET nodes.

Implements deterministic node movement dynamics with configurable speed,
pause times, and spatial boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Generator, List, Tuple

import simpy


def random_position(rng: random.Random, area: List[float] | Tuple[float, float]) -> Tuple[float, float]:
    """Generate a uniform random position within area [width, height]."""
    width, height = float(area[0]), float(area[1])
    return (rng.uniform(0.0, width), rng.uniform(0.0, height))


@dataclass
class MobilityState:
    """Tracks current coordinates, destination, and velocity of a node."""
    node_id: int
    x: float
    y: float
    current_speed: float = 0.0


class RandomWaypoint:
    """Manages SimPy discrete-event Random Waypoint movement for a node."""

    def __init__(
        self,
        env: simpy.Environment,
        node_id: int,
        area: List[float] | Tuple[float, float],
        speed_range: Tuple[float, float] = (1.0, 10.0),
        pause_time: float = 5.0,
        rng: random.Random = None,
        initial_pos: Tuple[float, float] | None = None,
        boundary: str = "wrap",
    ):
        self.env = env
        self.node_id = node_id
        self.area = (float(area[0]), float(area[1]))
        self.vmin, self.vmax = float(speed_range[0]), float(speed_range[1])
        self.pause_time = float(pause_time)
        self.rng = rng if rng is not None else random.Random()
        self.boundary = boundary

        init_x, init_y = initial_pos if initial_pos is not None else random_position(self.rng, self.area)
        self.state = MobilityState(node_id=node_id, x=init_x, y=init_y)
        self.action_process = self.env.process(self._run())

    def _run(self) -> Generator[simpy.Event, None, None]:
        """Main mobility event loop: travel to waypoint, pause, repeat."""
        width, height = self.area
        while True:
            # 1. Pick target waypoint
            target_x = self.rng.uniform(0.0, width)
            target_y = self.rng.uniform(0.0, height)
            speed = self.rng.uniform(self.vmin, self.vmax)
            self.state.current_speed = speed

            dist = math.hypot(target_x - self.state.x, target_y - self.state.y)
            if dist > 1e-6 and speed > 1e-6:
                travel_time = dist / speed
                yield self.env.timeout(travel_time)

            # Arrived at destination
            self.state.x = target_x
            self.state.y = target_y
            self.state.current_speed = 0.0

            # 2. Pause time
            if self.pause_time > 0:
                yield self.env.timeout(self.pause_time)
