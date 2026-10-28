<!-- generated-by: gsd-doc-writer -->
# Testing & Quality Assurance

This document describes the testing strategy, test suite architecture, automated verification procedures, and quality gates for the MANET Intrusion Detection and Response System.

## Test Framework & Environment

The test suite is built on **pytest 9.0.2** running under Python 3.11.8 on native Windows.

Install pytest and dependencies:

```powershell
python -m pip install pytest==9.0.2 pytest-cov==7.1.0
```

## Running Tests

### 1. Run the Complete Test Suite

Execute all 69 unit, integration, and architectural tests:

```powershell
python -m pytest
```

Expected output:
```text
======================= 69 passed in ~50s =======================
```

### 2. Run a Specific Test Module

Target individual subsystems:

```powershell
# Attack behavior tests
python -m pytest tests/test_attacks_blackhole.py
python -m pytest tests/test_attacks_grayhole.py

# Trace logging & feature pipeline tests
python -m pytest tests/test_trace_logging.py
python -m pytest tests/test_feature_pipeline.py

# ML training & evaluation tests
python -m pytest tests/test_ml_pipeline.py
python -m pytest tests/test_generalization.py

# Closed-loop IDS response & route isolation tests
python -m pytest tests/test_closed_loop.py

# Plot generation tests
python -m pytest tests/test_plots.py

# Architectural import boundary enforcement
python -m pytest tests/test_import_boundaries.py
```

### 3. Run with Test Filter or Verbose Output

```powershell
python -m pytest -v -k "anti_leakage or isolation"
```

## Test Suite Architecture

The repository contains 10 specialized test modules in `tests/` covering every architectural layer:

| Test Module | Test Count | Scope & Focus |
|---|---|---|
| `tests/test_attacks_blackhole.py` | 6 | RREP sequence spoofing, silent data packet drops, strategy registry factory. |
| `tests/test_attacks_grayhole.py` | 8 | Honest AODV control routing, probabilistic data drops, selective flow targeting. |
| `tests/test_closed_loop.py` | 9 | `OnlineIDS` controller, 2-strike confirmation, route invalidation, quarantine decay, and QoS recovery. |
| `tests/test_feature_pipeline.py` | 7 | Sliding-window aggregation, neutral fallbacks, and mathematical anti-leakage invariance ($X$ invariant to label shifts). |
| `tests/test_gate2_benchmark.py` | 1 | Multi-seed Gate 2 degradation benchmark asserting $\ge 25\%$ relative PDR drop under attack. |
| `tests/test_generalization.py` | 4 | Zero-shot attack transfer, multi-attack dataset integrity, and cross-scenario parameter grid evaluation. |
| `tests/test_import_boundaries.py` | 3 | AST-based architectural boundary check asserting `simulator/` never imports from `attacks/`. |
| `tests/test_ml_pipeline.py` | 18 | Seed-disjoint train/test partitioning, 5-fold CV tuning, locked $\text{FPR} \le 1.0\%$ gate, model persistence, and prediction parity. |
| `tests/test_plots.py` | 10 | Headless-safe figure generation, Seaborn palette application, and non-empty PNG file export verification. |
| `tests/test_trace_logging.py` | 3 | 10-column CSV trace schema enforcement, node attribution, and periodic `NODE_STATUS` telemetry frequency. |

## Mandatory Quality Gates

### Gate 1: Simulator Baseline Determinism
- **Requirement:** Running any scenario with an explicit seed yields identical traces.
- **Verification:** Verified by `tests/test_trace_logging.py` and `tests/test_feature_pipeline.py`.

### Gate 2: Measurable Attack Degradation
- **Requirement:** An attack MUST demonstrably degrade network performance before an ML detector is built.
- **Verification:** `tests/test_gate2_benchmark.py` runs baseline vs. Blackhole attack across seeds 42, 43, and 44, asserting a minimum relative PDR reduction of 25%. (Observed drops: Seed 42: 52.6%, Seed 43: 77.4%, Seed 44: 87.6%).

### Gate 3: Anti-Leakage Feature Invariance
- **Requirement:** Feature matrix $X$ must not contain oracle identifiers or ground-truth leakage.
- **Verification:** `tests/test_feature_pipeline.py::test_anti_leakage_invariance` permutes the scenario attacker label and asserts that the resulting feature matrix is byte-for-byte identical.

### Gate 4: Zero Random-Row Splitting
- **Requirement:** Training and test datasets must be disjoint across seeds and scenarios.
- **Verification:** `tests/test_ml_pipeline.py::test_split_seed_disjointness` verifies that training samples (Seeds 42 & 43) share zero simulation runs with test samples (Seed 44).

### Gate 5: False Positive Rate Gate ($\text{FPR} \le 1.0\%$)
- **Requirement:** Any model candidate exceeding 1.0% FPR is disqualified to prevent benign route teardowns.
- **Verification:** `tests/test_ml_pipeline.py` asserts that only models with $\text{FPR} \le 0.01$ qualify for champion selection.

### Gate 6: Closed-Loop QoS Recovery (Gate 7 Non-Negotiable)
- **Requirement:** The IDS must show statistically significant network recovery over unprotected AODV under attack.
- **Verification:** `tests/test_closed_loop.py` and `scripts/run_closed_loop_benchmark.py` evaluate the 3-way triad, asserting substantial PDR recovery (measured 92.9% recovery on Blackhole).

## Writing New Tests

Follow these patterns when contributing new test cases:

```python
import pytest
from simulator.run_scenario import SimulationRunner, load_scenario

def test_custom_scenario_determinism(tmp_path):
    config = load_scenario("scenarios/e1_normal_30n.json")
    
    runner1 = SimulationRunner(config, seed=100, out_dir=tmp_path / "run1")
    metrics1 = runner1.run()
    
    runner2 = SimulationRunner(config, seed=100, out_dir=tmp_path / "run2")
    metrics2 = runner2.run()
    
    assert metrics1["pdr"] == pytest.approx(metrics2["pdr"], abs=1e-5)
    assert metrics1["packets_received"] == metrics2["packets_received"]
```
