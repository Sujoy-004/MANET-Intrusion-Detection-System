---
phase: 05-closed-loop-ids-mitigation-network-re-evaluation
plan: 02
status: complete
completed_at: "2026-10-28T00:15:30+05:30"
files_modified:
  - scripts/run_closed_loop_benchmark.py
  - tests/test_closed_loop.py
  - results/closed_loop_metrics.csv
  - results/closed_loop_report.md
  - results/isolation_events.csv
verification:
  test_command: "python -m pytest tests/test_closed_loop.py -v"
  full_test_command: "python -m pytest tests/ -v"
  tests_passed: 59
  tests_failed: 0
  exit_code: 0
---

# Plan 05-02 Summary: Comparative QoS Benchmarking Pipeline & Triad Evaluation

## Overview
Successfully implemented and executed the automated comparative QoS benchmarking pipeline (`scripts/run_closed_loop_benchmark.py`). Evaluated the 3-way comparison triad (`Baseline AODV` vs. `Attack AODV` vs. `AODV+IDS`) across Blackhole and Grayhole attacks on 30-node and 50-node topologies under identical simulation seeds (`[42, 43, 44]`).

## Deliverables & Achievements

1. **Automated Triad Benchmark Orchestrator (`scripts/run_closed_loop_benchmark.py`)**:
   - Provides CLI flags (`--smoke`, `--seeds`, `--out-dir`, `--duration`).
   - Implements strict seed pairing across all 3 comparison modes (`Baseline`, `Attack`, `AODV+IDS`).
   - Automatically computes QoS metrics (PDR, throughput, delay, packet loss, routing overhead) alongside comparative deltas ($\Delta\text{PDR}_{\text{abs}}$, % recovery ratio, routing overhead penalty).
   - Generates dual output formats: raw tabular CSV (`results/closed_loop_metrics.csv`) and structured summary report (`results/closed_loop_report.md`), alongside consolidated quarantine logging (`results/isolation_events.csv`).

2. **End-to-End Recovery & Benchmark Test Suite (`tests/test_closed_loop.py`)**:
   - Added `test_closed_loop_blackhole_recovery`: Verifies that AODV+IDS achieves statistically significant PDR recovery ($\Delta\text{PDR}_{\text{abs}} > 0.15$ and recovery ratio $\ge 50.0\%$) under Blackhole attacks.
   - Added `test_closed_loop_grayhole_recovery`: Verifies positive PDR recovery on subtle Grayhole attacks ($p=0.5$).
   - Added `test_benchmark_script_smoke`: Tests CLI execution in smoke mode, validating exit code 0 and non-empty artifact generation.

3. **Authoritative Triad Benchmark Matrix Results**:
   - Executed full matrix: 4 scenarios $\times$ 3 seeds $\times$ 3 modes = 36 simulation runs in 52.73s.
   - **30-Node Blackhole ($p=1.0$):**
     - Baseline PDR: `0.6366` | Attack PDR: `0.1418` | AODV+IDS PDR: `0.6101`
     - $\Delta\text{PDR}_{\text{abs}} = \mathbf{+0.4683}$ (+46.83% absolute improvement)
     - Recovery Ratio: $\mathbf{92.9\%}$ of lost baseline packets restored
     - Routing Overhead Cost: $+0.0307$ (bounded adaptation cost)
   - **30-Node Grayhole ($p=0.5$):**
     - Baseline PDR: `0.6366` | Attack PDR: `0.5634` | AODV+IDS PDR: `0.6935`
     - $\Delta\text{PDR}_{\text{abs}} = \mathbf{+0.1301}$ | Recovery Ratio: $\mathbf{118.6\%}$
   - **30-Node Grayhole ($p=0.7$):**
     - Baseline PDR: `0.6366` | Attack PDR: `0.5654` | AODV+IDS PDR: `0.6225`
     - $\Delta\text{PDR}_{\text{abs}} = \mathbf{+0.0572}$ | Recovery Ratio: $\mathbf{68.0\%}$
   - **50-Node Grayhole ($p=0.5$):**
     - Baseline PDR: `0.7333` | Attack PDR: `0.5256` | AODV+IDS PDR: `0.5969`
     - $\Delta\text{PDR}_{\text{abs}} = \mathbf{+0.0713}$ | Recovery Ratio: $\mathbf{40.0\%}$
   - Logged 142 isolation and alert events into `results/isolation_events.csv` with zero endpoint false isolations.

## Verification
- `python scripts/run_closed_loop_benchmark.py --smoke --duration 30.0` passed in 2.61s.
- `python -m pytest tests/test_closed_loop.py -k "recovery or smoke" -v` passed (3/3 passed).
- Repository-wide regression run `python -m pytest tests/ -v` passed (59/59 passed in 142.68s).
