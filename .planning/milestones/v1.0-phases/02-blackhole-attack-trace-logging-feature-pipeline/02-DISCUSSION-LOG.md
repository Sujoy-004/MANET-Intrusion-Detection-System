# Phase 02: Blackhole Attack, Trace Logging & Feature Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-10-25  
**Phase:** 02-blackhole-attack-trace-logging-feature-pipeline  
**Areas discussed:** Attacker Injection & Strategy Parameters, Sliding-Window Aggregation & Timing, Feature Extraction Calculation & Schema, Attack Impact Verification Gate (Gate 2)

---

## Attacker Injection & Strategy Parameters

### Question 1: How should the Blackhole attack strategy and node placement be implemented?

| Option | Description | Selected |
|--------|-------------|:--------:|
| Configurable node ID in scenario JSON | Spoofs dest_seq = incoming_seq + 1000, hop_count = 1, and drops all intercepted DATA packets | |
| Extreme sequence spoofing | Sets dest_seq = 4294967295 (max uint32) to guarantee route preference, hop_count = 1 | |
| Dynamic flow-intercept placement | Scenario runner dynamically selects a node located on the multi-hop path between active CBR flows | ✓ |
| You decide | Follow standard AODV Blackhole literature | |

**User's choice:** Dynamic flow-intercept placement: Scenario runner dynamically selects a node located on the multi-hop path between active CBR flows.  
**Notes:** Guarantees that the attacker is actively positioned where CBR flows will be intercepted, avoiding dead scenarios where the attacker is never queried.

### Question 2: How should the Blackhole forge its spoofed RREP fields?

| Option | Description | Selected |
|--------|-------------|:--------:|
| Sequence bump (+1000) | dest_seq = max(known_seq, rreq.dest_seq) + 1000 and advertised hop_count = 1 | |
| Extreme sequence | dest_seq = 4294967295 (max uint32) and hop_count = 1 | |
| Configurable in scenario JSON | Allow custom sequence offset (e.g. +500 to +10000) and custom hop count | ✓ |
| You decide | Sequence bump + 1000, hop_count = 1 | |

**User's choice:** Configurable in scenario JSON: allow custom sequence offset (e.g. +500 to +10000) and custom hop count.  
**Notes:** Provides flexibility across experiment configurations while having standard defaults (+1000 offset, hop count 1).

---

## Sliding-Window Aggregation & Timing

### Question 3: What sliding window size (W) and step size (Δt) should be used for feature extraction?

| Option | Description | Selected |
|--------|-------------|:--------:|
| 10s window / 5s step | Standard 50% overlap for traffic density balance | |
| Fine-grained 5s window / 1s step | Higher sample density for ML training | ✓ |
| Non-overlapping 10s tumbling window | Window = 10s, step = 10s for strict window independence | |
| You decide | 10s window, 5s step | |

**User's choice:** Fine-grained 5-second window with 1-second step for higher sample density.  
**Notes:** Generates a richer, fine-grained tabular dataset capturing short-term transient behaviors.

### Question 4: How should simulation warmup and idle node windows be handled?

| Option | Description | Selected |
|--------|-------------|:--------:|
| Discard warmup (10s) and filter inactive nodes | Exclude nodes with 0 observed events | |
| Discard warmup (10s) but retain all nodes | Set zero-traffic ratios safely to 0.0 | |
| Configurable flags | Include all windows from t = 0 with configurable --warmup flag (default 10.0s) and --min-packets filter | ✓ |
| You decide | Discard 10s warmup, safe zero-division handling | |

**User's choice:** Include all windows from t = 0 with a configurable --warmup flag (default 10.0s) and --min-packets filter.  
**Notes:** Downstream extractor will provide both options via CLI flags, defaulting to 10.0s warmup and filtering idle nodes when min-packets is set.

---

## Feature Extraction Calculation & Schema

### Question 5: How should topology features (`neighbor_count`, `mobility_speed`) be captured alongside packet traces?

| Option | Description | Selected |
|--------|-------------|:--------:|
| Snapshot at window boundary t | Extract from simulation node state at timestamp t | |
| Event trace logging | Log periodic NODE_STATUS events (time, node_id, speed, neighbor_count) directly into the trace CSV | ✓ |
| Trace-only inference | Infer neighbor_count from unique 1-hop transmitters and compute speed from RWP logs | |
| You decide | Snapshot at window timestamp t | |

**User's choice:** Event trace logging: Log periodic NODE_STATUS events (time, node_id, speed, neighbor_count) directly into the trace CSV.  
**Notes:** Keeps the generated trace completely self-contained and reproducible without out-of-band state files.

### Question 6: How should forwarding and drop ratios be computed when a node receives 0 packets to forward in a window?

| Option | Description | Selected |
|--------|-------------|:--------:|
| Neutral baseline | packet_forward_ratio = 1.0, packet_drop_ratio = 0.0 when 0 forwarding packets received | ✓ |
| Zero assignment | packet_forward_ratio = 0.0, packet_drop_ratio = 0.0 | |
| Filter-based | Exclude windows where received packets < min_packets threshold | |
| You decide | Neutral 1.0 forward ratio for 0-packet windows | |

**User's choice:** Neutral baseline: packet_forward_ratio = 1.0, packet_drop_ratio = 0.0 when 0 forwarding packets received (avoids falsely penalizing idle nodes).  
**Notes:** Prevents division-by-zero errors and avoids misclassifying innocent idle nodes as malicious droppers.

---

## Attack Impact Verification Gate (Gate 2)

### Question 7: What threshold should be required by the Gate 2 automated verification script?

| Option | Description | Selected |
|--------|-------------|:--------:|
| Relative PDR drop (>= 25%) | Require at least 25% relative reduction in overall PDR across paired seeds | ✓ |
| Stringent drop (>= 40%) | Require at least 40% PDR reduction | |
| Multi-metric composite | PDR drop >= 20% AND packet loss increase >= 20% AND throughput drop >= 20% | |
| You decide | Relative PDR drop >= 25% across paired baseline/attack seeds | |

**User's choice:** Relative PDR drop: Require at least 25% relative reduction in overall PDR (e.g. baseline 85% -> attack <= 60%) across paired seeds.  
**Notes:** Enforces Gate 2 quantitatively before dataset generation and training begin.

### Question 8: How should the Gate 2 automated verification check be structured?

| Option | Description | Selected |
|--------|-------------|:--------:|
| Dedicated script with comparative table | Run 3 paired seeds (42, 43, 44), print side-by-side QoS comparison, and assert >= 25% PDR drop | ✓ |
| Pytest unit/integration test | Fast single-seed automated test integrated into pytest suite | |
| Multi-mobility benchmark | Test across multiple mobility speeds (1 m/s and 10 m/s) | |
| You decide | Dedicated 3-seed script with comparative table and assertion | |

**User's choice:** Dedicated script with comparative table: Run 3 paired seeds (42, 43, 44), print side-by-side QoS comparison, and assert >= 25% PDR drop.  
**Notes:** Provides a clear academic verification artifact showing side-by-side metrics across Baseline vs Blackhole under multiple seeds.

---

## the agent's Discretion

- CLI argument names and defaults for the feature extractor (e.g. `python -m feature_extraction.extract_features --trace <csv> --scenario <json> --out <csv> --window 5.0 --step 1.0 --warmup 10.0`).
- Modular package layout for `attacks/` (e.g. `attacks/blackhole.py` implementing `BlackholeStrategy`) decoupled from `simulator/`.

## Deferred Ideas

- Grayhole attack implementation (scheduled for Phase 4)
- Machine learning classification pipeline (scheduled for Phase 3)
- Dynamic closed-loop routing mitigation (scheduled for Phase 5)
