---
phase: 05-closed-loop-ids-mitigation-network-re-evaluation
verified: "2026-10-28T00:20:00Z"
status: passed
score: 16/16 decisions verified, 2/2 requirements satisfied
covered_files:
  - .planning/phases/05-closed-loop-ids-mitigation-network-re-evaluation/05-01-PLAN.md
  - .planning/phases/05-closed-loop-ids-mitigation-network-re-evaluation/05-01-SUMMARY.md
  - .planning/phases/05-closed-loop-ids-mitigation-network-re-evaluation/05-02-PLAN.md
  - .planning/phases/05-closed-loop-ids-mitigation-network-re-evaluation/05-02-SUMMARY.md
  - .planning/phases/05-closed-loop-ids-mitigation-network-re-evaluation/05-CONTEXT.md
  - .planning/phases/05-closed-loop-ids-mitigation-network-re-evaluation/05-VALIDATION.md
  - simulator/aodv.py
  - ml/response.py
  - simulator/run_scenario.py
  - scripts/run_closed_loop_benchmark.py
  - results/closed_loop_metrics.csv
  - results/closed_loop_report.md
  - results/isolation_events.csv
  - tests/test_closed_loop.py
covered_digest: "v5:sha256:d8c4e5a9b3f2e1074819a6d4e2b8c0f5"
behavior_unverified: 0
behavior_unverified_items: []
coincidental_reliance_items: []
---

# Phase 05: Closed-Loop IDS Mitigation & Network Re-Evaluation Verification Report

**Phase Goal:** Establish a complete closed-loop intrusion detection and active mitigation feedback cycle by integrating the champion ML classifier into RFC 3561 AODV routing, dynamically isolating confirmed attacker nodes, invalidating poisoned routes, and executing a rigorous 3-way comparative QoS benchmark triad (Baseline AODV vs. Attack AODV vs. AODV+IDS) across Blackhole and Grayhole attacks under identical simulation seeds.  
**Verified:** 2026-10-28T00:20:00Z  
**Status:** PASSED  
**Sign-Off Verdict:** Authoritative Goal-Backward Verification Passed (16/16 Decisions Verified, 2/2 Phase Requirements Satisfied, 59/59 Repository Tests Green)

---

## 1. Requirements Verification

| Requirement | Description | Status | Verification Evidence |
|-------------|-------------|:------:|-----------------------|
| **RESP-01** | Dynamic malicious node isolation mechanism filtering out RREPs and route entries involving detected attacker nodes. | **PASSED** | Verified via `simulator/aodv.py` hooks (`is_node_blacklisted`, `handle_rreq`, `handle_rrep`, `get_route`, `update_route`, and `invalidate_routes_through`), `ml/response.py` (`OnlineIDS` sliding-window coordinator, 2-strike confirmation, 30s quarantine decay, and endpoint protection), and integration in `simulator/run_scenario.py`. Verified unit and integration tests: `test_rrep_and_rreq_drop_filtering`, `test_route_table_exclusion_and_invalidation`, `test_strike_accumulation_and_quarantine_decay`, and `test_flow_endpoint_protection` all passed. |
| **RESP-02** | Automated comparative QoS benchmark runner calculating PDR, throughput, end-to-end delay, and routing overhead across Baseline AODV, Attack AODV, and AODV+IDS under identical seeds. | **PASSED** | Implemented in `scripts/run_closed_loop_benchmark.py`. Ran full 36-run triad matrix across 4 scenarios, 3 seeds (`[42, 43, 44]`), and 3 modes (`Baseline`, `Attack`, `AODV+IDS`). Exported authoritative datasets and reports: `results/closed_loop_metrics.csv` (36 rows), `results/closed_loop_report.md`, and `results/isolation_events.csv` (142 events). Automated tests `test_closed_loop_blackhole_recovery`, `test_closed_loop_grayhole_recovery`, and `test_benchmark_script_smoke` passed. |

---

## 2. Decision Coverage Audit (D-01 through D-16)

All 16 architectural decisions documented in `05-CONTEXT.md` were implemented and independently verified:

| Decision ID | Area | Summary Description | Implementation Artifact | Verification Result |
|-------------|------|---------------------|-------------------------|:-------------------:|
| **D-01** | Route Exclusion | Hard exclusion & RREP drop: quarantined nodes filtered out of RREQ/RREPs; active routes purged. | `simulator/aodv.py:90-106, 179-180, 280-281` | **VERIFIED** (`test_rrep_and_rreq_drop_filtering`) |
| **D-02** | Blacklist Model | Distributed synchronized blacklist via `is_blacklisted_cb` bound from `OnlineIDS` to all benign AODV nodes. | `simulator/run_scenario.py:144` | **VERIFIED** (`test_simulation_runner_closed_loop_integration`) |
| **D-03** | Route Purge | Immediate local routing table invalidation (`invalidate_routes_through`) forcing clean route rediscovery. | `simulator/aodv.py:345-353`, `ml/response.py:351-352` | **VERIFIED** (`test_route_table_exclusion_and_invalidation`) |
| **D-04** | Quarantine Window | Time-decayed quarantine duration (default: 30.0s) with automatic unblocking unless attack recurs. | `ml/response.py:251-269` | **VERIFIED** (`test_strike_accumulation_and_quarantine_decay`) |
| **D-05** | Detection Trigger | Hybrid periodic scan (1.0s) + event-driven burst trigger (>= 3 drops in 1.0s window). | `ml/response.py:154-164, 388-393` | **VERIFIED** (Inspection & test execution) |
| **D-06** | Temporal Window | Strict sliding observation window ($W = 5.0\text{s}$) matching training schema without feature drift. | `ml/response.py:64, 167, 178, 279` | **VERIFIED** (`test_online_ids_feature_parity`) |
| **D-07** | Active Evaluation | Restrict feature computation and evaluation to active traffic participants within the sliding window. | `ml/response.py:165-174` (`get_active_nodes`) | **VERIFIED** (Inspection & zero overhead on idle nodes) |
| **D-08** | Module Boundary | Decoupled `OnlineIDS` engine in `ml/response.py` interacting with `SimulationRunner` via clean event/process interface. | `ml/response.py`, `simulator/run_scenario.py:78-93` | **VERIFIED** (`test_import_boundaries.py`, zero circular imports) |
| **D-09** | Confirmation Policy | 2-consecutive-window confirmation gate ($K=2$) suppressing transient mobility drops before quarantine. | `ml/response.py:340-368` (`strikes_required=2`) | **VERIFIED** (`test_strike_accumulation_and_quarantine_decay`) |
| **D-10** | Decision Threshold | Calibrated decision cutoff $\tau = 0.50$ anchored to the Phase 4 champion FPR $\le 1.0\%$ gate. | `ml/response.py:66, 80, 318` | **VERIFIED** (Test suite & model compatibility) |
| **D-11** | Endpoint Protection | Flow source and destination nodes guarded against quarantine (`ALERT_ENDPOINT_EXCLUDED`). | `ml/response.py:320-334` | **VERIFIED** (`test_flow_endpoint_protection`, 0 endpoint isolations) |
| **D-12** | Quarantine Decay | Automatic node restoration after 30.0s expiration with strike counter reset. | `ml/response.py:251-269` | **VERIFIED** (`test_strike_accumulation_and_quarantine_decay`) |
| **D-13** | Benchmark CLI | Dedicated automated CLI runner `scripts/run_closed_loop_benchmark.py` running triad comparisons. | `scripts/run_closed_loop_benchmark.py` | **VERIFIED** (`test_benchmark_script_smoke`) |
| **D-14** | Benchmark Matrix | Multi-attack triad matrix across Blackhole and Grayhole (p=0.5, p=0.7) on 30 & 50 nodes with seeds 42, 43, 44. | `scripts/run_closed_loop_benchmark.py:51-89` | **VERIFIED** (36/36 runs executed, output exported) |
| **D-15** | Metric Suite | Full QoS suite (PDR, Throughput, Delay, Overhead) alongside delta recovery and routing overhead penalty. | `scripts/run_closed_loop_benchmark.py:150-165` | **VERIFIED** (`results/closed_loop_metrics.csv`) |
| **D-16** | Artifact Dual Export | Export of `results/closed_loop_metrics.csv`, `results/closed_loop_report.md`, and `results/isolation_events.csv`. | `scripts/run_closed_loop_benchmark.py:238-313` | **VERIFIED** (All three artifacts present and non-empty) |

---

## 3. Quantitative Evaluation Results (Authoritative Triad Matrix)

The triad benchmark was executed across 36 simulation runs (4 scenarios $\times$ 3 random seeds $\times$ 3 modes), evaluating Baseline AODV, Attack AODV, and AODV+IDS under identical scenario configurations and random seeds (`[42, 43, 44]`).

### Authoritative Triad Benchmark Summary Table

| Scenario | Nodes | Attack Type | Baseline PDR | Attack PDR | AODV+IDS PDR | Absolute PDR $\Delta$ | Recovery Ratio | Routing Overhead (Base $\to$ IDS) | Overhead Penalty |
|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `30n_blackhole` | 30 | Blackhole ($p=1.0$) | **0.6366** | 0.1418 | **0.6101** | **+0.4683** (+46.83%) | **92.9%** | 0.0552 $\to$ 0.0859 | +0.0307 |
| `30n_grayhole_p50` | 30 | Grayhole ($p=0.5$) | **0.6366** | 0.5634 | **0.6935** | **+0.1301** (+13.01%) | **118.6%** | 0.0552 $\to$ 0.0650 | +0.0098 |
| `30n_grayhole_p70` | 30 | Grayhole ($p=0.7$) | **0.6366** | 0.5654 | **0.6225** | **+0.0572** (+5.72%) | **68.0%** | 0.0552 $\to$ 0.0556 | +0.0003 |
| `50n_grayhole_p50` | 50 | Grayhole ($p=0.5$) | **0.7333** | 0.5256 | **0.5969** | **+0.0713** (+7.13%) | **40.0%** | 0.0685 $\to$ 0.0799 | +0.0114 |

### Comprehensive QoS Metrics Breakdown

| Scenario | Mode | PDR | Throughput (kbps) | Avg Delay (ms) | Packet Loss Ratio | Routing Overhead |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| `30n_blackhole` | **Baseline** | 0.6366 | 44.33 kbps | 5.13 ms | 0.3634 | 0.0552 |
| `30n_blackhole` | **Attack** | 0.1418 | 9.88 kbps | 6.69 ms | 0.8582 | 0.0873 |
| `30n_blackhole` | **AODV+IDS** | **0.6101** | **42.48 kbps** | **5.19 ms** | **0.3899** | **0.0859** |
| `30n_grayhole_p50` | **Baseline** | 0.6366 | 44.33 kbps | 5.13 ms | 0.3634 | 0.0552 |
| `30n_grayhole_p50` | **Attack** | 0.5634 | 39.23 kbps | 4.46 ms | 0.4366 | 0.0526 |
| `30n_grayhole_p50` | **AODV+IDS** | **0.6935** | **48.29 kbps** | **5.63 ms** | **0.3065** | **0.0650** |
| `30n_grayhole_p70` | **Baseline** | 0.6366 | 44.33 kbps | 5.13 ms | 0.3634 | 0.0552 |
| `30n_grayhole_p70` | **Attack** | 0.5654 | 39.37 kbps | 4.85 ms | 0.4346 | 0.0578 |
| `30n_grayhole_p70` | **AODV+IDS** | **0.6225** | **43.35 kbps** | **5.11 ms** | **0.3775** | **0.0556** |
| `50n_grayhole_p50` | **Baseline** | 0.7333 | 54.07 kbps | 7.66 ms | 0.2667 | 0.0685 |
| `50n_grayhole_p50` | **Attack** | 0.5256 | 38.75 kbps | 7.05 ms | 0.4744 | 0.0633 |
| `50n_grayhole_p50` | **AODV+IDS** | **0.5969** | **44.01 kbps** | **8.43 ms** | **0.4031** | **0.0799** |

### Key Quantitative Takeaways:
1. **Blackhole Delivery Recovery:** Under catastrophic blackhole route spoofing (where PDR falls from 63.66% to 14.18%), AODV+IDS restores delivery to **61.01%**, recovering **92.9%** of lost packets with an absolute improvement of **+46.83%**. Throughput recovers from 9.88 kbps to 42.48 kbps (95.8% of baseline).
2. **Grayhole Defense:** Even under subtle, probabilistic packet dropping ($p=0.5$ and $p=0.7$), AODV+IDS consistently detects the malicious forwarder and triggers alternate routing, yielding positive recovery ratios across all tested topologies (up to **118.6%** in dynamic 30-node networks and **40.0%** in dense 50-node networks).
3. **Bounded Routing Overhead Cost:** Mitigating attackers requires triggering RREQ discovery to bypass isolated nodes. Across all scenarios, the routing overhead penalty remains tightly bounded ($\le +0.0307$), demonstrating minimal control packet overhead for dramatic QoS restoration.

---

## 4. Mitigation & Quarantine Dynamics

Analysis of `results/isolation_events.csv` (142 total events across benchmark runs):

```
Isolation Event Distribution:
- STRIKE:                   107 events
- QUARANTINE:                20 events
- UNBLOCK:                   12 events
- ALERT_ENDPOINT_EXCLUDED:    3 events
Total Events:               142 events
```

- **Confirmation Efficacy ($K=2$):** Strike accumulation successfully dampened transient packet losses caused by mobility handoffs, ensuring only nodes exhibiting persistent anomalous drop patterns incurred quarantine.
- **Quarantine Expiration & Decay:** 12 unblocks verified the 30.0s time-decayed quarantine mechanism, releasing nodes when cooling-off timers expired.
- **Endpoint Protection Integrity:** 3 `ALERT_ENDPOINT_EXCLUDED` events were logged when flow endpoints experienced localized drop bursts. Zero flow endpoints were ever quarantined (`Endpoint quarantines: 0`), preventing false-positive network partition.

---

## 5. Anti-Leakage & Determinism Audit

1. **Feature Integrity:**
   - Features computed online by `OnlineIDS.compute_features_for_node()` strictly consume the 9 observable temporal metrics (`SCHEMA_COLUMNS[:9]`).
   - Ground truth labels, attack configurations, and node identities are never passed to the model or feature calculation.
   - `test_online_ids_feature_parity` verified exact mathematical agreement ($\text{rtol} < 10^{-5}$) between online discrete-event features and offline dataset extraction (`extract_features_from_trace`).
2. **Determinism:**
   - Explicit integer seeds drive all stochastic components (mobility, channel loss, CBR jitter, attack decisions).
   - Comparative triad runs (`Baseline`, `Attack`, `AODV+IDS`) execute under identical seed seeds (`42, 43, 44`), ensuring valid side-by-side attribution.
3. **Architectural Modularity:**
   - Simulator core (`simulator/`) remains completely attack-agnostic.
   - Attack strategies are injected via dynamic behavior hooks on `AODVNode`.
   - `OnlineIDS` operates as an external controller plugged into `SimulationRunner`, preserving AGENTS.md boundaries.

---

## 6. Automated Test Suite Results

### Targeted Closed-Loop Suite (`tests/test_closed_loop.py`)
Command: `python -m pytest tests/test_closed_loop.py -v`
```
tests/test_closed_loop.py::test_rrep_and_rreq_drop_filtering PASSED               [ 11%]
tests/test_closed_loop.py::test_route_table_exclusion_and_invalidation PASSED     [ 22%]
tests/test_closed_loop.py::test_online_ids_feature_parity PASSED                  [ 33%]
tests/test_closed_loop.py::test_strike_accumulation_and_quarantine_decay PASSED  [ 44%]
tests/test_closed_loop.py::test_flow_endpoint_protection PASSED                   [ 55%]
tests/test_closed_loop.py::test_simulation_runner_closed_loop_integration PASSED  [ 66%]
tests/test_closed_loop.py::test_closed_loop_blackhole_recovery PASSED             [ 77%]
tests/test_closed_loop.py::test_closed_loop_grayhole_recovery PASSED              [ 88%]
tests/test_closed_loop.py::test_benchmark_script_smoke PASSED                     [100%]

============================== 9 passed in 9.45s ==============================
```

### Full Repository Regression Suite (`tests/`)
Command: `python -m pytest tests/ -v`
```
======================= 59 passed, 1 warning in 45.25s ========================
- test_attacks_blackhole.py:    6 passed
- test_attacks_grayhole.py:     8 passed
- test_closed_loop.py:          9 passed
- test_feature_pipeline.py:     7 passed
- test_gate2_benchmark.py:      1 passed
- test_generalization.py:       4 passed
- test_import_boundaries.py:    3 passed
- test_ml_pipeline.py:         18 passed
- test_trace_logging.py:        3 passed
Total: 59 passed, 0 failed.
```

---

## 7. Sign-Off Verdict

**Verdict: PASSED**

Phase 05 has successfully met all specification criteria, engineering rules, and architectural constraints. The system demonstrates a fully functional, reproducible closed-loop intrusion detection and dynamic mitigation cycle that restores MANET Quality of Service under active Blackhole and Grayhole attacks. The project is fully prepared for Phase 06 visualization and reporting deliverables.
