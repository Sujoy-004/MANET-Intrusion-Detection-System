"""Attacks package for MANET adversarial simulation.

This package provides standalone attack strategies decoupled from the simulator.
No module in this package may import from `simulator/`.
"""

from __future__ import annotations

from attacks.base import AttackStrategy
from attacks.blackhole import BlackholeStrategy
from attacks.registry import create_attack_strategy

__all__ = [
    "AttackStrategy",
    "BlackholeStrategy",
    "create_attack_strategy",
]
