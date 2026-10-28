<!-- generated-by: gsd-doc-writer -->
# Configuration Guide

This document defines the configuration schemas, simulation parameters, scenario JSON specifications, and runtime hyperparameters for the MANET Intrusion Detection and Response System.

## Overview

The system requires no external environment variables or database credentials. All runtime behavior is driven declaratively by:
1. **Scenario Configuration Files (`scenarios/*.json`):** Defines topology, mobility, traffic flows, and attack parameters.
2. **CLI Flags (`simulator/run_scenario.py`):** Controls seed determinism, output paths, and closed-loop IDS activation.
3. **Hyperparameter Constants:** Controls sliding-window feature extraction and `OnlineIDS` isolation timing.

## Scenario Configuration Schema

Scenario files are declarative JSON documents loaded by `simulator.run_scenario.load_scenario()`.

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

### Parameter Reference Table

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `simulation_time` | float | Yes | - | Total duration of the simulation in simulated seconds. |
| `area.width` | float | Yes | - | Width of the 2D simulation bounding box in meters. |
| `area.height` | float | Yes | - | Height of the 2D simulation bounding box in meters. |
| `nodes` | int | Yes | - | Total count of mobile nodes in the network. |
| `radio_range` | float | Yes | - | Maximum Euclidean transmission distance $R$ in meters. Nodes with $d \le R$ form 1-hop links. |
| `mobility.model` | string | Yes | - | Mobility model name (currently `"RandomWaypoint"`). |
| `mobility.min_speed` | float | Yes | - | Minimum node kinematic velocity in meters/second. |
| `mobility.max_speed` | float | Yes | - | Maximum node kinematic velocity in meters/second. |
| `mobility.pause_time` | float | Yes | - | Pause duration at each waypoint target before selecting the next destination. |
| `traffic` | array | Yes | - | Array of CBR/UDP flow definition objects. |
| `traffic[].src` | int | Yes | - | Node ID of the traffic source. |
| `traffic[].dst` | int | Yes | - | Node ID of the traffic destination. |
| `traffic[].packet_rate`| float | Yes | - | Transmission frequency in packets per simulated second. |
| `traffic[].payload_size`| int | No | 512 | Packet payload size in bytes. |
| `traffic[].start_time` | float | No | 0.0 | Simulated time in seconds when packet transmission begins. |
| `attacks` | array | No | `[]` | Array of adversarial injection strategy configurations. |

## Attack Configuration Specifications

Adversarial injections are defined in the `attacks` array.

### 1. Blackhole Attack Configuration

```json
{
  "type": "blackhole",
  "strategy_params": {
    "intercept_mode": "flow_intercept"
  },
  "onset_time": 20.0
}
```

- `type`: `"blackhole"`
- `intercept_mode`:
  - `"flow_intercept"` (default): Automatically selects an intermediate node positioned along active application paths to ensure data interception.
  - `"fixed"`: Targets a specific node ID by adding `"attacker_id": <int>` to the configuration.
- `onset_time`: Simulated time in seconds when malicious behavior activates. Before `onset_time`, the node behaves as a normal, honest AODV router.

### 2. Grayhole Attack Configuration

```json
{
  "type": "grayhole",
  "strategy_params": {
    "drop_probability": 0.5,
    "intercept_mode": "flow_intercept"
  },
  "onset_time": 30.0
}
```

- `type`: `"grayhole"`
- `strategy_params.drop_probability`: Floating point value between $0.0$ and $1.0$. Specifies the Bernoulli probability with which intercepted transit data packets are dropped.
- `strategy_params.target_flows`: (Optional) Array of flow tuples `[[src, dst], ...]` to drop selectively. If omitted, all intercepted flows are dropped with `drop_probability`.
- `strategy_params.drop_control`: (Optional, boolean, default: `false`). If `true`, routing control packets (RREQs/RREPs) are dropped as well. Default `false` enforces honest AODV route participation with selective data plane dropping.

## Feature Extraction & Machine Learning Hyperparameters

Defined in [feature_extraction/extract_features.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/feature_extraction/extract_features.py) and [ml/dataset.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/ml/dataset.py):

| Parameter | Default Value | Description |
|---|---|---|
| `WINDOW_SIZE` ($W$) | `10.0` s | Backward temporal sliding-window duration for traffic aggregation. |
| `WINDOW_STEP` ($S$) | `2.0` s | Step increment between consecutive temporal feature evaluation points. |
| `FPR_THRESHOLD` | `0.01` (1.0%) | Maximum permissible False Positive Rate for champion model qualification. |
| `FEATURE_COLUMNS` | 9 features | `packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`, `neighbor_count`, `mobility_speed` |

## Closed-Loop Online IDS Hyperparameters

Defined in [ml/response.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/ml/response.py):

| Parameter | Default Value | Description |
|---|---|---|
| `EVAL_INTERVAL` | `5.0` s | Periodic interval between real-time inference checks in the simulator. |
| `CONFIRMATION_STRIKES` ($K$) | `2` | Number of consecutive positive attack predictions required before isolating a node. |
| `PROB_THRESHOLD` ($\tau$) | `0.50` | Minimum malicious class prediction probability required to register a strike. |
| `QUARANTINE_DURATION` | `30.0` s | Elapsed time before an isolated node's quarantine decays and route probing can resume. |

## Command-Line Configuration Flags

The primary CLI runner [simulator/run_scenario.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/simulator/run_scenario.py) accepts the following arguments:

```text
--scenario PATH    Path to declarative scenario JSON file (required)
--seed INT         Random seed for deterministic mobility, radio, and attacks (required)
--out DIR          Directory where generated trace CSVs and logs will be saved (required)
--ids              Enable real-time closed-loop Online IDS detection and mitigation (optional)
```
