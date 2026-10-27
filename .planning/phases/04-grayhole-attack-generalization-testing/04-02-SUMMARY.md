---
phase: 04-grayhole-attack-generalization-testing
plan: 02
status: completed
wave: 2
completed_at: "2026-10-27"
requirements: [ATK-02]
artifacts:
  scenarios:
    - scenarios/e4_grayhole_50n.json
  code:
    - ml/generalization.py
    - ml/dataset.py
    - scripts/build_dataset.py
    - ml/train.py
    - ml/evaluate.py
    - scripts/run_generalization_matrix.py
  tests:
    - tests/test_generalization.py
    - tests/test_ml_pipeline.py
  reports_and_plots:
    - results/generalization_report.md
    - results/generalization_metrics.csv
    - results/plots/grayhole_detection_boundary.png
    - results/plots/generalization_matrix.png
    - results/evaluation_report.md
    - results/metrics.csv
---

# Plan 04-02 Summary: Zero-Shot Transfer, Multi-Attack Dataset & Model Training, and Generalization Stress Matrix

## 1. Executive Summary

Plan 04-02 achieved comprehensive evaluation, training, and stress testing across the multi-attack MANET landscape:
1. **Track A (Zero-Shot Transfer Evaluation):** Evaluated the Phase 3 champion (`ml/models/best_model.joblib`) against unseen Grayhole test traffic without retraining. The Blackhole-trained model successfully detected Grayhole windows with a 28.0% transfer recall while preserving an ultra-low False Positive Rate of 0.088% ($\text{FPR} = 0.00088 \le 0.0100$).
2. **Track B (Multi-Attack Modeling & Retraining):**
   - Extended `scripts/build_dataset.py` with `--multi-attack` to construct the unified multi-attack dataset combining Normal, Blackhole, and Grayhole traffic under strict seed holdout (train: seeds 42+43, 34,800 rows; test: seed 44, 17,400 rows).
   - Retrained and tuned Scikit-learn pipelines (Random Forest, Decision Tree, SVM) with `StandardScaler` and cost-sensitive class balancing.
   - Evaluated on untouched Seed 44 test data: **Random Forest** achieved F1 = 0.7593 with $\text{FPR} = 0.0099 \le 0.0100$, satisfying the locked FPR gate. It was serialized to `ml/models/best_model.joblib` with verified `predict_proba` support, ready for Phase 5 closed-loop mitigation.
3. **Track C (Generalization Stress Matrix & Boundary Analysis):**
   - Implemented `scripts/run_generalization_matrix.py` executing an 18-cell benchmark matrix varying mobility speeds (1.0, 5.0, 10.0 m/s), drop probabilities (0.3, 0.5, 0.7), and network densities (30 and 50 nodes).
   - Characterized the empirical detection boundary: at low/moderate speeds (1–5 m/s), Grayhole drop behavior is cleanly identified (recall up to 93.3% at $\text{FPR} \le 0.82\%$). At high speeds (10 m/s), natural mobility link breakages produce background packet losses that define the boundary of purely drop-based detection.
   - Exported `results/generalization_report.md`, `results/generalization_metrics.csv`, `results/plots/grayhole_detection_boundary.png`, and `results/plots/generalization_matrix.png`.
4. **Automated Verification:** All 50 unit and integration tests across the repository pass cleanly in 50.28s.

---

## 2. Key Metrics Summary

### Track A: Zero-Shot Transfer
- **Evaluated Model:** Phase 3 Decision Tree Champion
- **Test Set (Seed 44):** 17,400 samples (17,000 Normal, 200 Blackhole, 200 Grayhole)
- **Zero-Shot Grayhole Recall:** 28.0% (56/200 detected)
- **Normal False Positive Rate:** 0.088% (15/17,000)

### Track B: Unified Retrained Champion
- **Champion Model:** Random Forest (`class_weight='balanced_subsample'`, `n_estimators=50`)
- **Multi-Attack Test Accuracy:** 97.44%
- **Malicious Attack F1:** 0.7593
- **Normal False Positive Rate:** **0.99%** ($\le 1.0\%$ gate satisfied)
- **Inference Latency:** 0.004 ms/sample

### Track C: Generalization Benchmark Sample Cells
- **30 Nodes, 1.0 m/s, Drop 0.5:** PDR 66.1% | GH Recall 86.7% | FPR 0.00%
- **30 Nodes, 5.0 m/s, Drop 0.5:** PDR 65.7% | GH Recall 64.4% | FPR 0.76%
- **50 Nodes, 1.0 m/s, Drop 0.5:** PDR 61.9% | GH Recall 91.1% | FPR 0.12%
- **50 Nodes, 5.0 m/s, Drop 0.5:** PDR 56.4% | GH Recall 37.8% | FPR 0.57%
