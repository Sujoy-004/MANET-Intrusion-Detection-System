---
status: complete
phase: 04-grayhole-attack-generalization-testing
source:
  - .planning/phases/04-grayhole-attack-generalization-testing/04-01-SUMMARY.md
  - .planning/phases/04-grayhole-attack-generalization-testing/04-02-SUMMARY.md
started: "2026-10-27T09:00:00Z"
updated: "2026-10-27T10:00:00Z"
---

# User Acceptance Testing (UAT) — Phase 04: Grayhole Attack & Generalization Testing

## Overview
Automated verification of decoupled RFC 3561 Grayhole attack behavior, honest route discovery with probabilistic/selective packet dropping, dynamic onset feature labeling, multi-attack seed-partitioned datasets, zero-shot transfer evaluation, unified Random Forest model training satisfying FPR <= 1.0% gate, and 3-axis generalization stress matrix across speed, drop probability, and node density.

---

## Tests

### 1. Decoupled Grayhole Attack Strategy & Honest Routing Seam (ATK-02)
expected: GrayholeStrategy extends AttackStrategy, returns None from get_spoofed_rrep_params to preserve RFC 3561 route discovery without spoofing, and drops data packets according to drop_prob.
evidence: tests/test_attacks_grayhole.py::test_grayhole_strategy_inheritance and test_grayhole_honest_routing passed. In a 30-node simulation, Grayhole generated zero spoofed RREPs and legitimately established multi-hop data forwarding paths.
result: pass

### 2. Bernoulli Drop Calibration & Selective Packet Filtering (ATK-02)
expected: GrayholeStrategy statistically matches configured drop probabilities (0.3, 0.5, 0.7) within standard error tolerances, and correctly filters by target flows or destination nodes.
evidence: tests/test_attacks_grayhole.py::test_grayhole_drop_probability_calibration[0.3, 0.5, 0.7] and test_grayhole_selective_filtering passed across 1,000 trials per rate.
result: pass

### 3. Dynamic Attack Onset & Time-Aware Multi-Class Feature Labeling (DATA-02, DATA-03)
expected: Sliding-window feature extraction dynamically inspects scenario metadata. Attacker windows prior to attack onset are labeled Normal; post-onset windows are labeled Grayhole (or Blackhole). Feature values in matrix X remain strictly invariant to label changes.
evidence: tests/test_attacks_grayhole.py::test_grayhole_simulation_trace_and_features passed. Pre-onset windows for attacker node are 100% Normal, post-onset are Grayhole, and non-attacker nodes remain Normal.
result: pass

### 4. Multi-Attack Seed-Disjoint Dataset Architecture (DATA-04)
expected: scripts/build_dataset.py --multi-attack creates seed-partitioned train (seeds 42 & 43: 34,800 rows) and test (seed 44: 17,400 rows) sets with zero random-row splitting and verified SHA-256 manifest.
evidence: tests/test_generalization.py::test_multi_attack_dataset_structure passed. Manifest checksums match disk files byte-for-byte; train and test sets have disjoint seed sets {42, 43} and {44}.
result: pass

### 5. Zero-Shot Attack Transfer Benchmark (ML-02)
expected: Evaluates the Phase 3 Blackhole-trained champion model against held-out Grayhole test traffic without retraining, quantifying out-of-distribution transfer recall and normal FPR.
evidence: ml/generalization.py::run_zero_shot_evaluation executed on seed 44 test data: Phase 3 Decision Tree achieved 28.0% zero-shot Grayhole recall with 0.088% False Positive Rate on normal traffic.
result: pass

### 6. Unified Retrained Champion Pipeline & FPR Acceptance Gate (ML-01, ML-02)
expected: Retrained classifier pipelines on multi-attack train set; selects champion satisfying FPR <= 1.0% gate with highest F1 score; serializes to ml/models/best_model.joblib.
evidence: Executed python -m ml.train and python -m ml.evaluate. Random Forest achieved F1 = 0.7593 with FPR = 0.0099 (0.99% <= 1.0% gate), outperforming Decision Tree (FPR 1.25% - disqualified) and SVM (FPR 2.37% - disqualified). Champion saved to ml/models/best_model.joblib.
result: pass

### 7. 3-Axis Generalization Stress Matrix & Boundary Analysis (ML-02)
expected: scripts/run_generalization_matrix.py evaluates an 18-cell benchmark matrix across speeds (1, 5, 10 m/s), drop probabilities (0.3, 0.5, 0.7), and network densities (30, 50 nodes). Exports summary CSV, markdown report, and boundary plots.
evidence: tests/test_generalization.py passed all tests. Generated results/generalization_metrics.csv (18 rows), results/generalization_report.md, results/plots/grayhole_detection_boundary.png, and results/plots/generalization_matrix.png.
result: pass

---

## Summary

- **Total Tests:** 7
- **Passed:** 7
- **Issues:** 0
- **Final Verdict:** PASS
