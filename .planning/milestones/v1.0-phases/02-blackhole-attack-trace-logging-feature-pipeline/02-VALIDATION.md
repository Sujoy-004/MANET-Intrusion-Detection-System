# Phase 02: Blackhole Attack, Trace Logging & Feature Pipeline — Nyquist Validation Framework

**Phase:** 02 — Blackhole Attack, Trace Logging & Feature Pipeline  
**Type:** Verification & Validation Matrix  
**Status:** Active  
**Date:** 2026-10-25  

---

## 1. Executive Summary

This validation document establishes the formal verification protocols for Phase 02 of the MANET ML IDS project. It enforces the binding engineering contracts specified in `AGENTS.md`, the architectural boundaries, anti-leakage invariant protocols, and the non-negotiable Gate 2 quantitative network impact benchmark ($\ge 25\%$ relative PDR drop across seeds 42, 43, 44) required before advancing to Phase 03 ML classification.

---

## 2. Requirements to Validation Matrix

| Req ID | Requirement Statement | Validation Method | Verification Target / Test |
|---|---|---|---|
| **ATK-01** | Decoupled Blackhole attack strategy advertising highest destination sequence number and 1-hop distance in spoofed RREP, silently dropping all intercepted data traffic. | Unit & Integration Test | `tests/test_attacks_blackhole.py`, `scripts/verify_gate2_impact.py` |
| **ATK-03** | Scenario configuration runner injecting attacker behaviors at runtime without modifying baseline simulator code. | AST Boundary & Scenario Test | `tests/test_import_boundaries.py`, `scenarios/e2_blackhole_30n.json` |
| **DATA-01** | Packet-level CSV event trace logger recording timestamp, event type, node ID, packet ID, packet type, source, destination, hop count, speed, and neighbor count. | Schema & Telemetry Test | `tests/test_trace_logging.py` |
| **DATA-02** | Sliding-window feature extractor aggregating backward in time ($t - W \le t_{event} \le t$) per node/flow calculating forwarding ratio, drop ratio, delay, RREQ rate, RREP rate, throughput, hop count, neighbor count, and speed. | Pipeline Unit Test | `tests/test_feature_pipeline.py` |
| **DATA-03** | Anti-leakage feature pipeline ensuring zero direct ground-truth metadata in feature matrix $X$. | Invariance & Schema Audit | `tests/test_feature_pipeline.py::test_anti_leakage_invariance` |

---

## 3. Plan Wave Dependencies & Execution Sequence

```
  ┌─────────────────────────────────────────────────────────┐
  │ Wave 1: Plan 02-01                                      │
  │ Decoupled Blackhole Attack Strategy & Dynamic Placement │
  │ (ATK-01, ATK-03)                                        │
  └────────────────────────────┬────────────────────────────┘
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Wave 2: Plan 02-02                                      │
  │ Enhanced Trace Logging & Gate 2 Benchmark               │
  │ (DATA-01, ATK-01)                                       │
  └────────────────────────────┬────────────────────────────┘
                               │
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │ Wave 3: Plan 02-03                                      │
  │ Sliding-Window Feature Extractor & Non-Leaking Pipeline │
  │ (DATA-02, DATA-03)                                      │
  └─────────────────────────────────────────────────────────┘
```

---

## 4. Verification Test Suites & Acceptance Commands

### Suite 1: Attack Behavior & Decoupled Boundaries (Wave 1)
```powershell
python -m pytest tests/test_attacks_blackhole.py tests/test_import_boundaries.py -v
```
- **Criteria:**
  - `BlackholeStrategy` spoofed sequence parameter generation: `dest_seq = max(1, rreq.dest_seq) + seq_offset` (default +1000).
  - Intercepted packet drop rule evaluates to `True` for application data.
  - AST boundary audit asserts 0 modules in `simulator/` import `attacks/` (only composition root `run_scenario.py`).

### Suite 2: Enhanced Trace Logging & Gate 2 Quantitative Benchmark (Wave 2)
```powershell
python -m pytest tests/test_trace_logging.py tests/test_gate2_benchmark.py -v
python scripts/verify_gate2_impact.py
```
- **Criteria:**
  - Trace header contains exactly 10 columns: `time,src,dst,pkt_id,type,hop_count,dropped_by,node_id,speed,neighbor_count`.
  - Periodic `NODE_STATUS` telemetry rows appear at 1.0s intervals for every node with valid positive speed and non-negative integer neighbor count.
  - Across seeds 42, 43, 44, relative Packet Delivery Ratio (PDR) drop:
    $$\text{Relative Drop} = \frac{\text{PDR}_{\text{base}} - \text{PDR}_{\text{atk}}}{\text{PDR}_{\text{base}}} \ge 25.0\%$$
  - `verify_gate2_impact.py` outputs formatted QoS table and exits with code 0.

### Suite 3: Sliding-Window Feature Extraction & Anti-Leakage (Wave 3)
```powershell
python -m pytest tests/test_feature_pipeline.py -v
python scripts/generate_datasets.py
```
- **Criteria:**
  - Feature dataset columns match exact 10 schema columns:
    `packet_forward_ratio,packet_drop_ratio,avg_delay,route_request_rate,route_reply_rate,throughput,hop_count,neighbor_count,mobility_speed,label`.
  - Inactive / idle nodes receive neutral values: `packet_forward_ratio = 1.0`, `packet_drop_ratio = 0.0` (zero division-by-zero errors or `NaN`s).
  - Invariance test passes: altering ground-truth labels leaves feature matrix $X$ (first 9 columns) 100% numerically identical.
  - `data/dataset_sample.csv` contains balanced or representative distributions of `Normal` and `Blackhole` classes.

---

## 5. Full Phase 02 Nyquist Gate Sign-Off Command

To execute the entire Phase 02 test and validation suite in one step:

```powershell
python -m pytest tests/ -v && python scripts/verify_gate2_impact.py && python scripts/generate_datasets.py
```

All commands must exit with status 0 with zero warnings of architectural boundary violations or missing columns.
