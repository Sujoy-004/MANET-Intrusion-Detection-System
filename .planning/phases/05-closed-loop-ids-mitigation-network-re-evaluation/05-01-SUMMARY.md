---
phase: 05-closed-loop-ids-mitigation-network-re-evaluation
plan: 01
status: completed
wave: 1
completed_at: "2026-10-27"
requirements: [RESP-01]
artifacts:
  code:
    - simulator/aodv.py
    - ml/response.py
    - simulator/run_scenario.py
  tests:
    - tests/test_closed_loop.py
---

# Plan 05-01 Summary: Closed-Loop IDS Response Engine & AODV Route Exclusion Integration

## 1. Executive Summary

Plan 05-01 delivered the active closed-loop intrusion detection and mitigation response system for Mobile Ad-Hoc Networks (MANET). It established real-time routing exclusion and invalidation seams in RFC 3561 AODV routing, implemented the decoupled `OnlineIDS` controller utilizing the trained champion machine learning classifier (`ml/models/best_model.joblib`), wired discrete-event closed-loop execution into `SimulationRunner`, and validated the subsystem through a comprehensive automated test suite.

Key deliverables:
1. **AODV Route Exclusion & Invalidation Seams (`simulator/aodv.py`):**
   - Added `is_blacklisted_cb: Optional[Callable[[int], bool]]` and `is_node_blacklisted(node_id: int) -> bool` to `AODVNode`.
   - Updated `handle_rreq` and `handle_rrep` to immediately drop incoming packets originating from or forwarded by quarantined nodes.
   - Updated `update_route` to reject insertion of blacklisted next hops or destinations.
   - Updated `get_route` to dynamically invalidate and reject routes whose next hop or destination is quarantined.
   - Implemented `invalidate_routes_through(bad_node: int) -> List[int]` to purge and invalidate routing table entries terminating at or traversing an isolated attacker.
2. **OnlineIDS Detection Coordinator (`ml/response.py`):**
   - Implemented `BufferedEvent` and `IsolationEvent` dataclasses tracking discrete-event timeline events and mitigation actions (`STRIKE`, `QUARANTINE`, `UNBLOCK`, `ALERT_ENDPOINT_EXCLUDED`).
   - Implemented `OnlineIDS` with in-memory sliding-window event deque, batched feature assembly across the 9 non-leaking columns (`SCHEMA_COLUMNS[:9]`), and champion model inference via `predict_proba`.
   - Built 2-consecutive-window confirmation gate ($K=2$, default $\tau=0.50$, evaluation interval 1.0s, observation spacing $\ge 0.8\text{s}$) to prevent transient false-positive flapping.
   - Implemented 30.0s time-decayed quarantine duration with automatic unblocking and strike reset upon expiration (D-04, D-12).
   - Enforced traffic endpoint protection (D-11), ensuring source and destination nodes of active flows are never quarantined or severed.
3. **Simulation Runner Closed-Loop Wiring (`simulator/run_scenario.py`):**
   - Connected `OnlineIDS` lifecycle into `SimulationRunner`: conditional instantiation based on `scenario["ids"]`, binding `AODVNode.is_blacklisted_cb`, registering `_periodic_detection_loop()` SimPy process, event forwarding in `log_event`, and CSV isolation logging in `run()`.
4. **Comprehensive Automated Test Suite (`tests/test_closed_loop.py`):**
   - Created 6 unit and integration tests covering RREP/RREQ dropping, routing table exclusion/invalidation, online-offline feature parity, 2-strike quarantine accumulation and 30s decay, flow endpoint protection, and end-to-end simulation runner integration.

---

## 2. Verification Evidence

### Task 1 & 2 Verification Commands

- `tests/test_closed_loop.py` (6 passed in 6.93s):
  - `test_rrep_and_rreq_drop_filtering`: PASSED
  - `test_route_table_exclusion_and_invalidation`: PASSED
  - `test_online_ids_feature_parity`: PASSED
  - `test_strike_accumulation_and_quarantine_decay`: PASSED
  - `test_flow_endpoint_protection`: PASSED
  - `test_simulation_runner_closed_loop_integration`: PASSED

### Full Test Suite Regression

- Ran `python -m pytest tests/ -v`:
  - **56 passed, 0 failed** in 117.66s across all test suites (`test_attacks_blackhole.py`, `test_attacks_grayhole.py`, `test_closed_loop.py`, `test_feature_pipeline.py`, `test_gate2_benchmark.py`, `test_generalization.py`, `test_import_boundaries.py`, `test_ml_pipeline.py`, `test_trace_logging.py`).
