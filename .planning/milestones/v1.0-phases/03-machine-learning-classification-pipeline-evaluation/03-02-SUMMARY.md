---
phase: 03-machine-learning-classification-pipeline-evaluation
plan: 02
status: completed
wave: 2
completed_at: "2026-10-27"
requirements: [ML-01]
artifacts:
  code:
    - ml/train.py
  models:
    - ml/models/random_forest.joblib
    - ml/models/decision_tree.joblib
    - ml/models/svm.joblib
  tests:
    - tests/test_ml_pipeline.py
---

# Plan 03-02 Summary: Scikit-learn Classifier Pipelines & Focused Grid Search CV

## 1. Executive Summary

Plan 03-02 delivered the training and tuning engine (`ml/train.py`) for the three classical intrusion detection classifiers:
1. **Pipeline Architecture:** Every classifier candidate was implemented as a uniform Scikit-learn Pipeline with `StandardScaler()` and cost-sensitive weighting (`class_weight='balanced'`) to address class imbalance without synthetic sampling.
2. **Deterministic Hyperparameter Tuning (D-04, D-08, D-09):** Tuned with 5-fold Stratified Cross-Validation on seeds 42 & 43 (`data/train.csv`). Used multi-metric scoring with `f1_blackhole` (`make_scorer(f1_score, pos_label='Blackhole')`) as the primary refit objective.
3. **Budgeted SVM Optimization (A2):** Subsampled to 10,000 stratified rows for RBF SVM tuning with probability calculation disabled during CV (`probability=False`), completing in 61s wall time.
4. **Leakage & Orientation Isolation (T-03-02, P-2):** Verified that `ml/train.py` contains zero references to held-out test data (`test.csv`) or master data (`master.csv`), and verified that `f1_blackhole` strictly evaluates the attack class as positive.
5. **Model Persistence:** Serialized all three tuned candidates (`joblib.dump(..., compress=3)`) to `ml/models/`.

---

## 2. Model Tuning Results (5-Fold CV on `data/train.csv`)

| Candidate | Best Hyperparameters | Best CV F1 (`Blackhole`) | Fit Time | Model File | Size |
|-----------|----------------------|--------------------------|----------|------------|------|
| **Random Forest** | `n_estimators=50`, `max_depth=None` | **0.6746** | 9.05s | `ml/models/random_forest.joblib` | 231,941 B |
| **Decision Tree** | `max_depth=None`, `min_samples_split=2` | **0.5497** | 3.33s | `ml/models/decision_tree.joblib` | 5,151 B |
| **SVM (RBF)** | `C=100`, `gamma='scale'` | **0.2477** | 61.34s | `ml/models/svm.joblib` | 26,533 B |

---

## 3. Test Coverage

- `tests/test_ml_pipeline.py`:
  - `test_train_class_weight_balanced`: Verified all 3 candidate pipelines declare `class_weight='balanced'`.
  - `test_train_primary_scorer_orientation`: Verified scoring orientation yields 0.0 when predicting normal background traffic.
  - `test_train_smoke_deterministic`: Verified single-combo fits for RF, DT, and SVM run deterministically in < 15s.
  - `test_train_no_test_file_access`: Structural source check verifying `ml/train.py` has no access to held-out evaluation splits.

All 12 tests in `test_ml_pipeline.py` passed in 10.74s.
