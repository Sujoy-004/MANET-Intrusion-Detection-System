"""Unit-disk radio propagation and dynamic neighbor discovery model.

Calculates wireless link availability based on Euclidean distance thresholds
and optional probabilistic packet/link loss.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Sequence, Tuple


def calculate_distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """Compute Euclidean distance between two 2D coordinates."""
    return math.hypot(pos2[0] - pos1[0], pos2[1] - pos1[1])


def get_neighbors(
    node_id: int,
    positions: Sequence[Tuple[float, float]],
    range_m: float = 250.0,
    rng: random.Random | None = None,
    loss_prob: float = 0.0,
) -> List[int]:
    """Find 1-hop neighbors within transmission range with optional probabilistic loss.

    Args:
        node_id: The query node's index.
        positions: Sequence of (x, y) coordinates for all nodes in order of index.
        range_m: Maximum radio transmission range in meters.
        rng: Deterministic random generator for loss decisions.
        loss_prob: Probability of transmission loss within range.

    Returns:
        Sorted list of connected neighbor node IDs.
    """
    my_pos = positions[node_id]
    neighbors: List[int] = []

    for other_id, other_pos in enumerate(positions):
        if other_id == node_id:
            continue
        dist = calculate_distance(my_pos, other_pos)
        if dist <= range_m:
            if loss_prob > 0.0 and rng is not None:
                if rng.random() < loss_prob:
                    continue
            neighbors.append(other_id)

    return sorted(neighbors)


def compute_all_neighbors(
    positions: Dict[int, Tuple[float, float]],
    range_m: float = 250.0,
    rng: random.Random | None = None,
    loss_prob: float = 0.0,
) -> Dict[int, List[int]]:
    """Compute 1-hop neighbor adjacency table for all nodes.

    Deterministic iteration order over sorted node IDs.
    """
    sorted_node_ids = sorted(positions.keys())
    pos_list = [positions[nid] for nid in sorted_node_ids]
    adj: Dict[int, List[int]] = {}

    for nid in sorted_node_ids:
        adj[nid] = get_neighbors(
            node_id=nid,
            positions=pos_list,
            range_m=range_m,
            rng=rng,
            loss_prob=loss_prob,
        )

    return adj
