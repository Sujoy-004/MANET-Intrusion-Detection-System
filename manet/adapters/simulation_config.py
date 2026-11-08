"""Two-tier parameter validator and custom scenario configuration builder."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from manet.runtime.paths import get_project_root

# Standard validation bounds
MIN_NODES: int = 2
MAX_NODES: int = 100
MIN_DURATION: float = 10.0
MAX_DURATION: float = 3600.0
DEFAULT_CUSTOM_DURATION: float = 100.0
DEFAULT_SEED: int = 42

DEFAULT_RADIO_RANGE: float = 250.0
DEFAULT_LOSS_PROBABILITY: float = 0.0
DEFAULT_RATE_PPS: float = 4.0
DEFAULT_SPEED_RANGE: list[float] = [1.0, 20.0]
DEFAULT_PAUSE_TIME: float = 0.0
DEFAULT_AREA: list[int] = [1000, 1000]


# ---------------------------------------------------------------------------
# Tier 1: Local Scalar Blur Validators
# ---------------------------------------------------------------------------

def validate_node_count(val: Any) -> tuple[bool, str | None]:
    """Validate node count is an integer within [MIN_NODES, MAX_NODES]."""
    try:
        ival = int(val)
        if MIN_NODES <= ival <= MAX_NODES:
            return True, None
        return False, f"Node count must be an integer between {MIN_NODES} and {MAX_NODES}"
    except (TypeError, ValueError):
        return False, "Node count must be an integer"


def validate_duration(val: Any) -> tuple[bool, str | None]:
    """Validate simulation duration is a number within [MIN_DURATION, MAX_DURATION]."""
    try:
        fval = float(val)
        if MIN_DURATION <= fval <= MAX_DURATION:
            return True, None
        return False, f"Duration must be a number between {MIN_DURATION} and {MAX_DURATION} seconds"
    except (TypeError, ValueError):
        return False, "Duration must be a valid number"


def validate_seed(val: Any) -> tuple[bool, str | None]:
    """Validate seed is a non-negative integer within [0, 2147483647]."""
    try:
        ival = int(val)
        if 0 <= ival <= 2147483647:
            return True, None
        return False, "Seed must be an integer between 0 and 2,147,483,647"
    except (TypeError, ValueError):
        return False, "Seed must be an integer"


def validate_radio_range(val: Any) -> tuple[bool, str | None]:
    """Validate radio range is a positive float between 10.0 and 2000.0 meters."""
    try:
        fval = float(val)
        if 10.0 <= fval <= 2000.0:
            return True, None
        return False, "Radio range must be between 10.0 and 2000.0 meters"
    except (TypeError, ValueError):
        return False, "Radio range must be a valid number"


def validate_loss_probability(val: Any) -> tuple[bool, str | None]:
    """Validate packet loss probability is a float between 0.0 and 1.0."""
    try:
        fval = float(val)
        if 0.0 <= fval <= 1.0:
            return True, None
        return False, "Loss probability must be between 0.0 and 1.0"
    except (TypeError, ValueError):
        return False, "Loss probability must be a valid number"


class SimulationConfigValidator:
    """Two-tier validation engine encapsulating scalar and structural checks."""

    validate_node_count = staticmethod(validate_node_count)
    validate_duration = staticmethod(validate_duration)
    validate_seed = staticmethod(validate_seed)
    validate_radio_range = staticmethod(validate_radio_range)
    validate_loss_probability = staticmethod(validate_loss_probability)


# ---------------------------------------------------------------------------
# Tier 2: Structural Cross-Field Invariant Validator
# ---------------------------------------------------------------------------

def validate_structural_invariants(
    config: dict[str, Any],
    model_path: Path | None = None,
) -> list[str]:
    """Validate cross-field invariants and champion model presence for IDS enablement.

    Checks:
    - nodes >= MIN_NODES
    - duration > 0
    - Each flow satisfies 0 <= src < nodes, 0 <= dst < nodes, and src != dst
    - If ids.enabled is True, model_path (default ml/models/best_model.joblib) must exist and be non-empty.
    """
    errors: list[str] = []

    # 1. Node count invariant
    nodes = config.get("nodes")
    try:
        nodes_int = int(nodes)  # type: ignore[arg-type]
        if nodes_int < MIN_NODES:
            errors.append(f"Node count must be at least {MIN_NODES}, got {nodes_int}")
    except (TypeError, ValueError):
        errors.append("Invalid or missing 'nodes' count in configuration")
        nodes_int = 0

    # 2. Duration invariant
    duration = config.get("duration")
    try:
        duration_float = float(duration)  # type: ignore[arg-type]
        if duration_float <= 0:
            errors.append(f"Simulation duration must be greater than 0, got {duration_float}")
    except (TypeError, ValueError):
        errors.append("Invalid or missing 'duration' in configuration")

    # 3. Flows endpoint invariant
    flows = config.get("flows", [])
    if not isinstance(flows, list):
        errors.append("'flows' must be a list of flow specifications")
    else:
        for idx, flow in enumerate(flows):
            if not isinstance(flow, dict):
                errors.append(f"Flow #{idx} must be a dictionary")
                continue
            src = flow.get("src")
            dst = flow.get("dst")
            if src is None or dst is None:
                errors.append(f"Flow #{idx} missing required 'src' or 'dst'")
                continue
            try:
                src_int = int(src)
                dst_int = int(dst)
            except (TypeError, ValueError):
                errors.append(f"Flow #{idx} src and dst must be integers")
                continue

            if src_int < 0 or (nodes_int > 0 and src_int >= nodes_int):
                errors.append(f"Flow #{idx} source node {src_int} out of range [0, {nodes_int - 1}]")
            if dst_int < 0 or (nodes_int > 0 and dst_int >= nodes_int):
                errors.append(f"Flow #{idx} destination node {dst_int} out of range [0, {nodes_int - 1}]")
            if src_int == dst_int:
                errors.append(f"Flow #{idx} source ({src_int}) cannot equal destination ({dst_int})")

    # 4. Mobility speed ordering invariant (min_speed < max_speed)
    mobility = config.get("mobility", {})
    if isinstance(mobility, dict) and "speed_range" in mobility:
        speed = mobility.get("speed_range")
        if not (isinstance(speed, (list, tuple)) and len(speed) == 2):
            errors.append("Mobility 'speed_range' must be a list or tuple of two numbers")
        else:
            try:
                lo = float(speed[0])
                hi = float(speed[1])
                if not (math.isfinite(lo) and math.isfinite(hi)):
                    errors.append("Mobility 'speed_range' values must be finite numbers")
                elif lo >= hi:
                    errors.append(f"Mobility speed_range minimum ({lo}) must be strictly less than maximum ({hi})")
            except (TypeError, ValueError):
                errors.append("Mobility 'speed_range' must contain numeric values")

    # 5. IDS gating invariant
    ids_cfg = config.get("ids", {})
    if isinstance(ids_cfg, dict) and ids_cfg.get("enabled", False):
        target_model = model_path if model_path is not None else (get_project_root() / "ml" / "models" / "best_model.joblib")
        exists_and_non_empty = False
        try:
            if target_model.is_file() and target_model.stat().st_size > 0:
                exists_and_non_empty = True
        except (OSError, ValueError):
            exists_and_non_empty = False

        if not exists_and_non_empty:
            errors.append(
                "IDS enabled but champion model artifact (ml/models/best_model.joblib) does not exist on disk. "
                "Run: python scripts/build_dataset.py --multi-attack && python -m ml.train && python -m ml.evaluate"
            )

    return errors


# ---------------------------------------------------------------------------
# Custom Scenario Builder
# ---------------------------------------------------------------------------

def build_custom_configuration(
    nodes: int = 30,
    duration: float = DEFAULT_CUSTOM_DURATION,
    seed: int = DEFAULT_SEED,
    attack_type: str = "None",
    ids_enabled: bool = False,
    advanced_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete scenario configuration dictionary matching SimulationRunner schema."""
    adv = advanced_params or {}

    area = list(adv.get("area", DEFAULT_AREA))
    speed_range = list(adv.get("speed_range", DEFAULT_SPEED_RANGE))
    pause_time = float(adv.get("pause_time", DEFAULT_PAUSE_TIME))
    boundary = str(adv.get("boundary", "wrap"))
    radio_range = float(adv.get("radio_range", DEFAULT_RADIO_RANGE))
    loss_prob = float(adv.get("loss_probability", DEFAULT_LOSS_PROBABILITY))
    rate_pps = float(adv.get("rate_pps", DEFAULT_RATE_PPS))

    # Construct default flows if not supplied
    if "flows" in adv and isinstance(adv["flows"], list):
        flows = adv["flows"]
    else:
        dst_node = (nodes - 1) if nodes > 1 else 1
        flow_duration = max(float(duration) - 4.0, 1.0)
        flows = [
            {
                "flow_id": 0,
                "src": 0,
                "dst": dst_node,
                "rate_pps": rate_pps,
                "start_time": 2.0,
                "duration": flow_duration,
            }
        ]

    # Construct attack configuration
    attack_str = attack_type.strip()
    is_attack = attack_str.lower() not in ("none", "")
    attack_cfg: dict[str, Any] = {
        "enabled": is_attack,
        "type": attack_str if is_attack else "None",
        "attackers": "dynamic",
    }
    if is_attack:
        if attack_str.lower() == "grayhole":
            attack_cfg["drop_prob"] = float(adv.get("drop_prob", 0.5))
            if "start_time" in adv:
                attack_cfg["start_time"] = float(adv["start_time"])
        elif attack_str.lower() == "blackhole":
            attack_cfg["seq_offset"] = int(adv.get("seq_offset", 1000))
            attack_cfg["spoofed_hops"] = int(adv.get("spoofed_hops", 1))
            if "start_time" in adv:
                attack_cfg["start_time"] = float(adv["start_time"])

    config: dict[str, Any] = {
        "scenario_id": f"custom_{nodes}n_{attack_str.lower()}",
        "description": f"Custom {nodes}-node scenario with {attack_str} attack",
        "nodes": int(nodes),
        "area": area,
        "duration": float(duration),
        "seed": int(seed),
        "mobility": {
            "model": "random_waypoint",
            "speed_range": speed_range,
            "pause_time": pause_time,
            "boundary": boundary,
        },
        "radio": {
            "range": radio_range,
            "loss_probability": loss_prob,
        },
        "traffic": {
            "protocol": "CBR_UDP",
            "packet_size": 512,
        },
        "flows": flows,
        "attack": attack_cfg,
        "ids": {
            "enabled": bool(ids_enabled),
            "model_path": "ml/models/best_model.joblib",
        },
    }

    return config


class CustomScenarioBuilder:
    """Builder class for constructing custom simulation configurations."""

    build = staticmethod(build_custom_configuration)


__all__ = [
    "MIN_NODES",
    "MAX_NODES",
    "MIN_DURATION",
    "MAX_DURATION",
    "DEFAULT_CUSTOM_DURATION",
    "DEFAULT_SEED",
    "DEFAULT_RADIO_RANGE",
    "DEFAULT_LOSS_PROBABILITY",
    "DEFAULT_RATE_PPS",
    "DEFAULT_SPEED_RANGE",
    "DEFAULT_PAUSE_TIME",
    "DEFAULT_AREA",
    "validate_node_count",
    "validate_duration",
    "validate_seed",
    "validate_radio_range",
    "validate_loss_probability",
    "SimulationConfigValidator",
    "validate_structural_invariants",
    "build_custom_configuration",
    "CustomScenarioBuilder",
]
