<!-- generated-by: gsd-doc-writer -->
# Configuration Guide

This document defines the configuration schemas, simulation parameters, scenario JSON specifications, TUI session settings, and runtime hyperparameters for the MANET Intrusion Detection and Response System.

## Overview

The system requires no external environment variables or database credentials. All runtime behavior is driven declaratively by:
1. **Scenario Configuration Files (`scenarios/*.json`):** Defines topology, mobility, traffic flows, and attack parameters.
2. **CLI Flags (`simulator/run_scenario.py`):** Controls seed determinism, output paths, and closed-loop IDS activation.
3. **Hyperparameter Constants:** Controls sliding-window feature extraction and `OnlineIDS` isolation timing.
4. **TUI Session Settings (`manet/runtime/settings.py`):** Controls display accessibility, animation speed, and density.

---

## Scenario Configuration Schema

Scenario files are declarative JSON documents loaded by `simulator.run_scenario.load_scenario()` and validated by `manet.adapters.simulation_config.validate_scenario_config()`.

### Full Example Schema (`scenarios/e4_grayhole_onset_30n.json`)

```json
{
  "simulation_time": 100.0,
  "area": {
    "width": 1000.0,
    "height": 1000.0
  },
  "nodes": 30,
  "radio_range": 250.0,
  "mobility": {
    "model": "RandomWaypoint",
    "min_speed": 1.0,
    "max_speed": 20.0,
    "pause_time": 2.0
  },
  "traffic": [
    {
      "src": 0,
      "dst": 29,
      "packet_rate": 2.0,
      "payload_size": 512,
      "start_time": 5.0
    },
    {
      "src": 5,
      "dst": 20,
      "packet_rate": 2.0,
      "payload_size": 512,
      "start_time": 5.0
    }
  ],
  "attacks": [
    {
      "type": "grayhole",
      "strategy_params": {
        "drop_probability": 0.5,
        "intercept_mode": "flow_intercept"
      },
      "onset_time": 30.0
    }
  ]
}
```

### Scenario Validation Tiers

The simulation workflow wizard enforces a two-tier validation pipeline:

- **Tier 1 (Schema Structure):** Asserts required root fields (`simulation_time`, `area`, `nodes`, `radio_range`, `mobility`, `traffic`, `attacks`) and verifies primitive data types.
- **Tier 2 (Physical Invariants):**
  - `nodes >= 2`
  - `area.width > 0` and `area.height > 0`
  - `radio_range > 0`
  - `min_speed < max_speed` (rejects equal, inverted, NaN, or infinite speeds)
  - `min_speed >= 0` and `pause_time >= 0`
  - Traffic flow endpoints: `0 <= src < nodes`, `0 <= dst < nodes`, and `src != dst`
  - `packet_rate > 0` and `payload_size > 0`
  - Attack parameters: `0.0 <= drop_probability <= 1.0`, `onset_time >= 0`

---

## TUI Session Settings (`SessionSettings`)

Defined in [manet/runtime/settings.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/manet/runtime/settings.py):

| Setting | Default | Description |
|---|---|---|
| `high_contrast` | `False` | Toggles high-contrast border and text styles for accessibility. |
| `reduced_motion` | `False` | Disables smooth progress animations and pulsing status badges. |
| `compact_density` | `False` | Adjusts layout padding and card heights for dense 80×24 viewing. |

> **Architectural Constraint:** `SessionSettings` is strictly in-memory. Settings reset on every launch and are never persisted to disk.

---

## Workspace Manifest Schema (`manifest.json`)

Every simulation run executed via the TUI produces a structured `manifest.json` in `.manet-workspace/<experiment_id>/`:

```json
{
  "experiment_id": "exp_20261111_110500_a1b2",
  "run_tag": "seed42_blackhole_ids",
  "created_at": "2026-11-11T11:05:00.000Z",
  "completed_at": "2026-11-11T11:05:01.200Z",
  "status": "COMPLETED",
  "scenario": {
    "name": "e2_blackhole_30n",
    "seed": 42,
    "duration": 300.0,
    "nodes": 30,
    "ids_enabled": true
  },
  "qos_scorecard": {
    "pdr": 0.6293,
    "throughput_kbps": 53.44,
    "avg_delay_ms": 102.29,
    "routing_overhead": 0.1302
  },
  "checksums": {
    "scenario.json": "sha256:...",
    "trace.csv": "sha256:...",
    "isolation.log": "sha256:..."
  }
}
```

---

## AODV Protocol Hyperparameters

Defined in [simulator/aodv.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/simulator/aodv.py):

| Parameter | Default Value | Description |
|---|---|---|
| `DEFAULT_RREQ_TIMEOUT` | `2.0` s | Initial wait duration before retrying an unreplied Route Request (RREQ). |
| `DEFAULT_RREQ_RETRIES` | `2` | Number of retries (2 retries, 3 total discovery attempts: 2s -> 4s -> 8s) before entering cooldown. |
| `DEFAULT_BACKOFF_MULT` | `2.0` | Exponential backoff multiplier applied to discovery timeout per retry. |
| `DEFAULT_DISCOVERY_COOLDOWN` | `2.0` s | Cooldown quiet period following exhausted retries before a fresh RREQ can be issued. |
| `DEFAULT_MAX_BUFFER_PER_DEST` | `100` packets | Per-destination buffer queue capacity during discovery (oldest dropped first). |
| `DEFAULT_MAX_BUFFER_TIME` | `20.0` s | Time-To-Live threshold after which buffered data packets expire and are dropped. |
| `DEFAULT_ACTIVE_ROUTE_TIMEOUT` | `10.0` s | Active route lifetime before entry expiration without traffic refresh. |

---

## Feature Extraction & Machine Learning Hyperparameters

Defined in [feature_extraction/extract_features.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/feature_extraction/extract_features.py) and [ml/dataset.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/ml/dataset.py):

| Parameter | Default Value | Description |
|---|---|---|
| `WINDOW_SIZE` ($W$) | `10.0` s | Backward temporal sliding-window duration for traffic aggregation. |
| `WINDOW_STEP` ($S$) | `2.0` s | Step increment between consecutive temporal feature evaluation points. |
| `FPR_THRESHOLD` | `0.01` (1.0%) | Maximum permissible False Positive Rate for champion model qualification. |
| `FEATURE_COLUMNS` | 9 features | `packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`, `neighbor_count`, `mobility_speed` |

---

## Closed-Loop Online IDS Hyperparameters

Defined in [ml/response.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/ml/response.py):

| Parameter | Default Value | Description |
|---|---|---|
| `EVAL_INTERVAL` | `5.0` s | Periodic interval between real-time inference checks in the simulator. |
| `CONFIRMATION_STRIKES` ($K$) | `2` | Number of consecutive positive attack predictions required before isolating a node. |
| `PROB_THRESHOLD` ($\tau$) | `0.50` | Minimum malicious class prediction probability required to register a strike. |
| `QUARANTINE_DURATION` | `30.0` s | Elapsed time before an isolated node's quarantine decays and route probing can resume. |

---

## Command-Line Configuration Flags

The primary CLI runner [simulator/run_scenario.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/simulator/run_scenario.py) accepts:

```text
--scenario PATH    Path to declarative scenario JSON file (required)
--seed INT         Random seed for deterministic mobility, radio, and attacks (required)
--out DIR          Directory where generated trace CSVs and logs will be saved (required)
--ids              Enable real-time closed-loop Online IDS detection and mitigation (optional)
```
