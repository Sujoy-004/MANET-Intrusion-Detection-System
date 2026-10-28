---
phase: 04-grayhole-attack-generalization-testing
plan: 01
status: completed
wave: 1
completed_at: "2026-10-27"
requirements: [ATK-02]
artifacts:
  scenarios:
    - scenarios/e4_grayhole_onset_30n.json
  code:
    - attacks/grayhole.py
    - attacks/base.py
    - attacks/registry.py
    - simulator/aodv.py
    - simulator/run_scenario.py
    - feature_extraction/extract_features.py
  tests:
    - tests/test_attacks_grayhole.py
---

# Plan 04-01 Summary: Grayhole Attack Strategy, Honest Routing Hook, Dynamic Scenario & Time-Aware Feature Extraction

## 1. Executive Summary

Plan 04-01 successfully implemented and verified the decoupled RFC 3561 Grayhole attack strategy and its integration into the MANET simulation and feature pipeline:
1. **Decoupled Grayhole Attack Strategy (`attacks/grayhole.py`):** Implemented `GrayholeStrategy` extending `AttackStrategy`. Grayhole complies with RFC 3561 control routing by returning `None` from `get_spoofed_rrep_params`, while selectively or probabilistically dropping data payloads in `should_drop_data` according to `drop_prob` (default: 0.5) and target flow/destination filters. Strict determinism is enforced via explicit seed / random generator.
2. **Honest AODV Route Discovery Seam (`simulator/aodv.py`):** Updated `AODVNode.handle_rreq` so that when `attack_behavior.get_spoofed_rrep_params()` returns `None`, the node avoids spoofing RREPs and falls through to normal destination checking and legitimate route forwarding.
3. **Dynamic Runner Wiring (`simulator/run_scenario.py`):** Configured `SimulationRunner` to instantiate `GrayholeStrategy` with scenario `drop_prob`, `target_flows`, `target_dests`, and explicit `self.seed`, setting `is_grayhole = True` both eagerly and via delayed onset at `attack.start_time`.
4. **Dynamic Attack Labeling (`feature_extraction/extract_features.py`):** Generalized feature labeling to dynamically detect attack type from scenario metadata. Attacker windows prior to `attack_start_time` are labeled `Normal`; post-onset windows are labeled `Grayhole` (or `Blackhole`), while benign nodes remain strictly `Normal`. Feature matrix $X$ remains 100% invariant.
5. **Scenario & Comprehensive Tests:** Created `scenarios/e4_grayhole_onset_30n.json` and 8 new unit/integration tests in `tests/test_attacks_grayhole.py` covering inheritance, honest routing, Bernoulli calibration (0.3, 0.5, 0.7), selective targeting, seed determinism, and full trace feature extraction. All 46 tests across the repository pass cleanly.

---

## 2. Verification Evidence

- `tests/test_attacks_grayhole.py` passing 8/8 tests in 8.86s:
  - `test_grayhole_strategy_inheritance`: PASSED
  - `test_grayhole_honest_routing`: PASSED
  - `test_grayhole_drop_probability_calibration[0.3]`: PASSED
  - `test_grayhole_drop_probability_calibration[0.5]`: PASSED
  - `test_grayhole_drop_probability_calibration[0.7]`: PASSED
  - `test_grayhole_selective_filtering`: PASSED
  - `test_grayhole_seed_determinism`: PASSED
  - `test_grayhole_simulation_trace_and_features`: PASSED
- Full repository regression suite: **46 passed in 41.85s**.
