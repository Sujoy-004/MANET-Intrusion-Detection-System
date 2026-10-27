---
phase: 03-machine-learning-classification-pipeline-evaluation
plan: 03
status: completed
wave: 3
completed_at: "2026-10-27"
requirements: [ML-02, ML-03]
artifacts:
  code:
    - ml/evaluate.py
  models:
    - ml/models/best_model.joblib
    - ml/models/model_metadata.json
  results:
    - results/metrics.csv
    - results/feature_importance.csv
    - results/evaluation_report.md
    - results/plots/confusion_matrix_random_forest.png
    - results/plots/confusion_matrix_decision_tree.png
    - results/plots/confusion_matrix_svm.png
  tests:
    - tests/test_ml_pipeline.py
---

# Plan 03-03 Summary: Seed-44 Evaluation, FPR Gate & Champion Model Persistence

## 1. Executive Summary

Plan 03-03 completed Phase 3 by evaluating all three tuned classifier pipelines against the strictly held-out seed 44 test dataset (`data/test.csv`, 8,700 samples), applying the locked False Positive Rate acceptance gate (D-06), selecting and serializing the champion pipeline, and exporting the full benchmark reporting suite:
1. **Security Metric Evaluation (ML-02, D-13):** Every candidate model was evaluated with explicit orientation on `"Blackhole"` as the positive class (`confusion_matrix(labels=['Normal', 'Blackhole'])`). Computed unrounded Accuracy, Precision, Recall, F1, False Positive Rate, and confusion matrix counts.
2. **False Positive Rate Acceptance Gate (D-06):** Enforced locked acceptance gate $\text{FPR} \le 0.01$ (1.0%).
   - **Decision Tree:** Passed gate ($\text{FPR} = 0.0009 \le 0.01$) with **$\text{F1} = 0.7040$**, Precision = 0.9339, Recall = 0.5650.
   - **Random Forest:** Passed gate ($\text{FPR} = 0.0058 \le 0.01$) with $\text{F1} = 0.6356$, Precision = 0.7030, Recall = 0.5800.
   - **SVM:** Failed gate ($\text{FPR} = 0.1011 > 0.01$) and was disqualified.
3. **Champion Selection (D-11, D-12):** `decision_tree` was selected as champion by virtue of achieving the highest F1 score under the FPR gate, lowest inference latency (1.43 ms), and compact disk footprint (5,399 bytes). Serialized to `ml/models/best_model.joblib`.
4. **Predict Proba Parity & Interface (ML-03):** Verified `predict_proba` interface compatibility and positive class indexing via `classes_` lookup.
5. **Artifact Suite & Documentation (D-10):** Produced `results/metrics.csv`, `results/feature_importance.csv` (Gini + Permutation), `results/evaluation_report.md`, and 3 confusion matrix heatmaps under `results/plots/`.
6. **Full-Suite Acceptance:** All 38 tests across the test suite passed in 30.05 seconds.

---

## 2. Benchmark Security Metrics (Seed 44 Held-Out Test Set)

| Model | Accuracy | Precision | Recall | F1 (`Blackhole`) | FPR | Status |
|-------|----------|-----------|--------|------------------|-----|--------|
| **Decision Tree** (Champion) | **0.9891** | **0.9339** | **0.5650** | **0.7040** | **0.0009** (0.09%) | **PASSED GATE & SELECTED** |
| **Random Forest** | 0.9847 | 0.7030 | 0.5800 | 0.6356 | 0.0058 (0.58%) | **PASSED GATE** |
| **SVM (RBF)** | 0.8826 | 0.0424 | 0.1900 | 0.0693 | 0.1011 (10.11%) | Disqualified ($\text{FPR} > 1.0\%$) |

---

## 3. Confusion Matrix Breakdown

- **Decision Tree (Champion):**
  - True Negatives ($\text{Normal} \to \text{Normal}$): 8,492
  - False Positives ($\text{Normal} \to \text{Blackhole}$): 8 (0.09% FPR)
  - False Negatives ($\text{Blackhole} \to \text{Normal}$): 87
  - True Positives ($\text{Blackhole} \to \text{Blackhole}$): 113
- **Random Forest:**
  - True Negatives: 8,451 | False Positives: 49 (0.58% FPR) | False Negatives: 84 | True Positives: 116
- **SVM:**
  - True Negatives: 7,641 | False Positives: 859 (10.11% FPR) | False Negatives: 162 | True Positives: 38

---

## 4. Top Feature Importances (Permutation on Held-Out Split)

1. `packet_drop_ratio` (Importance: 0.7251)
2. `packet_forward_ratio` (Importance: 0.0841)
3. `route_reply_rate` (Importance: 0.0000)
4. `route_request_rate` (Importance: 0.0000)
5. `avg_delay` (Importance: 0.0000)

---

## 5. Test Suite Verification

18 tests in `tests/test_ml_pipeline.py` passing:
- Split disjointness & row count conservation
- Schema exactness & no NaN/Inf
- Manifest SHA-256 match & class distribution match
- Deterministic simulation rebuild
- Balanced class weights & scorer orientation
- Single-combo smoke fits for all models
- Structural test isolation guard (`test_train_no_test_file_access`)
- Metric column validation & mathematical FPR check
- FPR gate enforcement & champion selection check
- Champion prediction parity & `predict_proba` interface check
- Full export artifact validation
- Deterministic evaluation output check

Total project test suite: **38 passed in 30.05s**.
