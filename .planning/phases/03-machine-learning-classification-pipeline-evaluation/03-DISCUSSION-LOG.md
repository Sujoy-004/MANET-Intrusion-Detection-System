# Phase 03: Machine Learning Classification Pipeline & Evaluation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-25  
**Phase:** 03-Machine Learning Classification Pipeline & Evaluation  
**Areas discussed:** Dataset Splitting & Seed Partitioning, Class Imbalance & Cost-Sensitive Learning, Preprocessing & Pipeline Architecture, Model Selection Criteria & Serialization  

---

## Dataset Splitting & Seed Partitioning

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed seed holdout | Seeds 42 & 43 for Train/Validation, Seed 44 strictly held out for Final Test | ✓ |
| GroupShuffleSplit / StratifiedGroupKFold | Split grouped by seed/run_id | |
| Hybrid approach | Cross-validation on train seeds, separate test seed | |

**User's choice:** Fixed seed holdout (Seeds 42 & 43 for Train/Validation, Seed 44 strictly held out for Final Test)  
**Notes:** Aligns with Gate 2 verification benchmark and guarantees zero intra-run or cross-seed leakage.

| Option | Description | Selected |
|--------|-------------|----------|
| Symmetrically paired runs | Train set has (Normal, Blackhole) for 42+43; Test has (Normal, Blackhole) for 44 | |
| Single composite scenario set | Each seed runs both normal and attack phases in a single timeline | ✓ |
| Cross-scenario testing | Train on 30-node, test on different speed/density | |

**User's choice:** Single composite scenario set — Each seed runs both normal and attack phases in a single timeline  
**Notes:** Clarified that scenarios specify an attack `start_time` (e.g. $t = 100\text{s}$) where the node behaves normally initially before activating Blackhole behavior.

| Option | Description | Selected |
|--------|-------------|----------|
| Strict 10-column train.csv and test.csv + dataset_manifest.json | Strict 10-column files with sidecar JSON | ✓ (Combined) |
| master.csv with seed column | Include master CSV with seed column for manual inspection | ✓ (Combined) |

**User's choice:** Combine option 1 & 2  
**Notes:** `data/train.csv` and `data/test.csv` are strictly 10 columns conforming to the Phase 2 feature schema, while `data/master.csv` retains the `seed` column for auditability, and `data/dataset_manifest.json` tracks checksums, row counts, and class distributions.

---

## Class Imbalance & Cost-Sensitive Learning

| Option | Description | Selected |
|--------|-------------|----------|
| Cost-sensitive learning | class_weight='balanced' across all models (RF, DT, SVM) | ✓ |
| Hybrid | class_weight='balanced' + threshold tuning | |
| Random undersampling | Undersample majority class on training set only | |

**User's choice:** Cost-sensitive learning with class_weight='balanced' across all models (RF, DT, SVM)  
**Notes:** Penalizes minority false negatives without artificial sample generation or discarding normal traffic.

| Option | Description | Selected |
|--------|-------------|----------|
| Hard constraint FPR <= 1.0% | At least 99% normal specificity to prevent accidental node isolation | ✓ |
| Soft constraint FPR <= 3.0% | More leeway for recall | |
| No hard constraint | Rank purely by F1 | |

**User's choice:** Hard constraint of FPR <= 1.0% (at least 99% normal specificity)  
**Notes:** In MANET routing, false positives mistakenly isolate legitimate forwarding nodes and degrade network PDR.

| Option | Description | Selected |
|--------|-------------|----------|
| Standard string labels | 'Normal' vs 'Blackhole' mapped via LabelEncoder / mapping dict | ✓ |
| Binary integer encoding | Strict 0/1 integer encoding throughout | |

**User's choice:** Standard string labels ('Normal' vs 'Blackhole') internally mapped via LabelEncoder/mapping dict  
**Notes:** Guarantees clean forward-compatibility for multi-class classification when Grayhole is introduced in Phase 4.

---

## Preprocessing & Pipeline Architecture

| Option | Description | Selected |
|--------|-------------|----------|
| Uniform StandardScaler in Pipeline | Unified StandardScaler inside sklearn Pipeline for all models | ✓ |
| Model-specific pipelines | StandardScaler only for SVM, raw features for trees | |
| RobustScaler in Pipeline | Resilient to bursty delay/throughput outliers | |

**User's choice:** Uniform StandardScaler inside an sklearn Pipeline for all models  
**Notes:** Standardizing numeric features does not alter tree partition decisions and guarantees a unified, leak-free inference pipeline.

| Option | Description | Selected |
|--------|-------------|----------|
| Focused grid search | DT: max_depth [4, 8, 12, None], min_samples_split [2, 10]; RF: n_estimators [50, 100] | ✓ (Combined) |
| Wider grid with RandomizedSearchCV | 50 iterations exploring broader parameter space | ✓ (Combined) |

**User's choice:** Combine option 1 & 2  
**Notes:** Fast default focused grid search completing in seconds, with optional RandomizedSearchCV capability for broader parameter space exploration.

| Option | Description | Selected |
|--------|-------------|----------|
| Native Gini feature importances | Export to results/feature_importance.csv | ✓ (Combined) |
| Permutation Importance on test set | Model-agnostic validation on unseen test set (Seed 44) | ✓ (Combined) |

**User's choice:** Combine option 1 & 2  
**Notes:** Tree models report MDI/Gini importance, and all models (including SVM) are evaluated using Permutation Importance on the held-out test set (Seed 44).

---

## Model Selection Criteria & Serialization

| Option | Description | Selected |
|--------|-------------|----------|
| Full model serialization | Save all tuned models in ml/models/ + best_model.joblib + model_metadata.json | ✓ |
| Save only best model | Save only best_model.joblib | |

**User's choice:** Save all tuned models in ml/models/ (decision_tree.joblib, random_forest.joblib, svm.joblib) + symlink/copy to best_model.joblib + model_metadata.json recording test metrics, parameters, and selection rationale.

| Option | Description | Selected |
|--------|-------------|----------|
| Tabular metrics + MD report + Seaborn plots | results/metrics.csv, results/evaluation_report.md, results/plots/ heatmaps | ✓ |
| Console output only | Print to console and single summary JSON | |

**User's choice:** Save tabular comparison to results/metrics.csv, full textual breakdown to results/evaluation_report.md, and seaborn confusion matrix heatmaps to results/plots/.

| Option | Description | Selected |
|--------|-------------|----------|
| Comprehensive test suite | Assert zero row overlap, 9-feature invariance, parity, FPR <= 1.0% | ✓ |
| Basic sanity test | Check file existence and loading | |

**User's choice:** Comprehensive test suite asserting: (1) zero row overlap across seed splits, (2) strict 9-feature invariance in X, (3) loaded model prediction parity with in-memory model, (4) all 3 models evaluated with FPR <= 1.0%.

---

## Agent's Discretion

- **Primary GridSearchCV scorer:** Primary optimization metric set to `make_scorer(f1_score, pos_label='Blackhole')` supplemented by tracking `f1_macro` and `balanced_accuracy`.
- **SVM convergence & runtime optimization:** Configured with `SVC(kernel='rbf', probability=True, class_weight='balanced')` utilizing stratified subsampling (e.g. 10k samples) during CV grid search to keep wall-clock time under 30s.
- **Champion model selection tie-breaker:** Select highest malicious-class F1-score subject to $\text{FPR} \le 1.0\%$ on held-out Seed 44; break ties using per-sample inference latency and model compactness.

---

## Deferred Ideas

- None — discussion stayed strictly within the Phase 3 boundary.
