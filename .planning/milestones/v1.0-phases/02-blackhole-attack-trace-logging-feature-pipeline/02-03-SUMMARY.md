# Phase 02 Plan 03 Summary: Sliding-Window Feature Extractor & Non-Leaking Dataset Pipeline

## Overview
Constructed the sliding-window feature extractor (`feature_extraction/extract_features.py`) assembling standardized 10-column tabular datasets from raw packet simulation traces (satisfying DATA-02). Enforced strict anti-leakage isolation protocols (DATA-03, D-08) preventing node identities or oracle markers from leaking into feature matrix $X$, and verified that neutral zero-traffic handling prevents NaN corruption on idle nodes (D-07). Generated the initial 34,800-sample balanced dataset (`data/dataset_sample.csv`) across paired normal and blackhole simulations.

## Implementation Details
1. **Sliding-Window Feature Extractor (`feature_extraction/extract_features.py`):**
   - Implemented `extract_features_from_trace` aggregating backward in time over window interval $[t - W, t]$ with configurable window (default 5.0s), step (default 1.0s), warmup (default 10.0s), and min-packet threshold (default 0).
   - Computes all 9 behavioral features: `packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`, `neighbor_count`, `mobility_speed`.
   - Neutral baseline zero-traffic handling: sets forward ratio to `1.0` and drop ratio to `0.0` when total traffic is zero (D-07).
   - In-band telemetry aggregation: calculates `neighbor_count` and `mobility_speed` from embedded `NODE_STATUS` rows without external state files (D-06).
   - Target column `label`: assigned `"Blackhole"` if node is an attacker, otherwise `"Normal"`, derived exclusively from scenario configuration.
   - Provides full CLI `--trace`, `--scenario`, `--out`, `--window`, `--step`, `--warmup`, `--min-packets`.

2. **Anti-Leakage Protocols & Test Suite (`tests/test_feature_pipeline.py`):**
   - `test_schema_columns_exact_match`: Asserts output dataframe matches exact 10 schema columns in specified order.
   - `test_no_nan_or_inf_in_features`: Asserts zero NaN, null, or infinite values in feature matrix.
   - `test_neutral_zero_traffic_fallback`: Confirms idle nodes receive neutral 1.0 forward ratio.
   - `test_zero_identity_in_features`: Confirms no node IDs, IPs, coordinates, timestamps, seeds, or scenarios exist in feature column headers.
   - `test_anti_leakage_invariance`: Proves that modifying the scenario ground truth label changes ONLY the target column `label`, while the feature matrix $X$ remains 100% numerically identical.

3. **End-to-End Dataset Generator (`scripts/generate_datasets.py`):**
   - Simulates baseline normal and blackhole scenarios across seeds 42 and 43 (300s each).
   - Extracts sliding-window features for each run and concatenates them into `data/dataset_sample.csv`.
   - Produced 34,800 total samples (34,220 Normal [98.33%], 580 Blackhole [1.67%]).

## Verification
- Automated feature tests: `python -m pytest tests/test_feature_pipeline.py -v` (5 passed in 11.53s).
- Full test suite: `python -m pytest tests/ -v` (18 passed in 11.80s).
- Sample dataset generated: `data/dataset_sample.csv` (34,800 rows, 10 columns, 0 NaNs).
