"""Registry and factory for attack strategy instantiation."""

from __future__ import annotations

from typing import Any, Dict, Type

from attacks.base import AttackStrategy
from attacks.blackhole import BlackholeStrategy

_REGISTRY: Dict[str, Type[AttackStrategy]] = {
    "blackhole": BlackholeStrategy,
}


def create_attack_strategy(attack_type: str, **kwargs: Any) -> AttackStrategy:
    """Instantiate an AttackStrategy by name.

    Args:
        attack_type: Name of attack (e.g. "Blackhole", case-insensitive).
        **kwargs: Strategy-specific parameters (e.g. seq_offset, spoofed_hops).

    Returns:
        Configured AttackStrategy instance.

    Raises:
        ValueError: If attack_type is not registered.
    """
    key = attack_type.strip().lower()
    strategy_cls = _REGISTRY.get(key)
    if strategy_cls is None:
        valid_types = ", ".join(f"'{k}'" for k in sorted(_REGISTRY.keys()))
        raise ValueError(f"Unknown attack type '{attack_type}'. Registered types: {valid_types}")
    return strategy_cls(**kwargs)
