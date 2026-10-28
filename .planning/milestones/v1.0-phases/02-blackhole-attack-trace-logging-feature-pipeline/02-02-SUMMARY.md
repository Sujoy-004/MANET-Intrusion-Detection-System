# Phase 02 Plan 02 Summary: Enhanced Trace Logging & Gate 2 Benchmark

## Overview
Enhanced the simulation trace logging system to generate self-contained 10-column event logs embedding in-band `NODE_STATUS` telemetry once per second across all nodes (satisfying DATA-01). Implemented the automated multi-seed Gate 2 verification benchmark proving that the Blackhole attack causes $\ge 25\%$ relative PDR degradation across seeds 42, 43, and 44 under identical baseline conditions (satisfying ATK-01 and non-negotiable Gate 2).

## Implementation Details
1. **10-Column Unified Trace Schema (`simulator/run_scenario.py`):**
   - Updated header: `["time", "src", "dst", "pkt_id", "type", "hop_count", "dropped_by", "node_id", "speed", "neighbor_count"]`.
   - Updated `log_event` to accept acting `node_id`, `speed`, and `neighbor_count`.
   - Wired packet events (`DATA_SENT`, `DATA_FWD`, `DATA_RECV`, `DATA_DROP`, `RREQ`, `RREP`, `RERR`) to record the acting `node_id`.
   - Added periodic telemetry generator `_periodic_status_logger` running at 1.0s intervals, logging node speed and dynamic neighbor counts for all nodes.

2. **Telemetry-Resilient QoS Metrics (`simulator/metrics.py`):**
   - Verified `compute_metrics_from_df` ignores non-packet telemetry rows (`NODE_STATUS`) when calculating PDR, throughput, packet loss, and routing overhead.
   - Updated fallback dataframe builder to support both 7-column and 10-column formats.

3. **Gate 2 Verification Benchmark Script (`scripts/verify_gate2_impact.py`):**
   - Runs paired simulations (`e1_normal_30n.json` vs `e2_blackhole_30n.json`) across seeds 42, 43, 44.
   - Computes QoS metrics and evaluates relative PDR drop: $(PDR_{base} - PDR_{atk}) / PDR_{base}$.
   - Asserts $\ge 25\%$ degradation threshold on every seed.
   - Outputs a formatted comparison table and exits 0 on success, 1 on failure.

4. **Automated Test Suite (`tests/`):**
   - `tests/test_trace_logging.py`: Asserts exact 10 columns, verifies 1.0s periodic `NODE_STATUS` rows across all 30 nodes, and checks acting `node_id` recording.
   - `tests/test_gate2_benchmark.py`: Integration test verifying Gate 2 quantitative degradation threshold.

## Verification
- Gate 2 Multi-Seed Benchmark (`python scripts/verify_gate2_impact.py`):
  - Seed 42: Base PDR 7.12% -> Atk PDR 3.38% (Relative Drop: **52.60%**) -> PASSED
  - Seed 43: Base PDR 42.46% -> Atk PDR 9.61% (Relative Drop: **77.36%**) -> PASSED
  - Seed 44: Base PDR 37.65% -> Atk PDR 4.66% (Relative Drop: **87.62%**) -> PASSED
  - Result: All seeds exceed 25% degradation threshold.
- Pytest suite: `python -m pytest tests/test_trace_logging.py tests/test_gate2_benchmark.py -v` (4 passed in 1.85s).
