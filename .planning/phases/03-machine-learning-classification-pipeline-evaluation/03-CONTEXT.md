# Phase 03: Machine Learning Classification Pipeline & Evaluation - Context

**Gathered:** 2026-10-25  
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers a complete classical machine learning classification and evaluation pipeline using Scikit-learn. It ingests the non-leaking sliding-window behavioral datasets produced in Phase 2, partitions data strictly across simulation seeds (Seeds 42 & 43 for training/validation, Seed 44 strictly held out for testing), trains and tunes Random Forest, Decision Tree, and Support Vector Machine classifiers with cost-sensitive learning to counter the ~1.7% attack rarity, enforces a strict False Positive Rate constraint ($\le 1.0\%$), and serializes the winning model pipeline and scaler to `ml/models/` for closed-loop IDS mitigation.
</domain>

<decisions>
## Implementation Decisions

### Dataset Splitting & Seed Partitioning
- **D-01:** Fixed seed holdout — Seeds 42 and 43 are allocated for training and cross-validation; Seed 44 is held out strictly for final test evaluation. Guarantees zero intra-run or temporal autocorrelation leakage across splits. — **Reversibility:** costly — matches Gate 2 benchmark and defines downstream dataset partitions.
- **D-02:** Single composite scenario set with dynamic attack onset — Scenarios configure an attack `start_time` (e.g. $t = 100.0\text{s}$) where the malicious node behaves normally initially before activating Blackhole dropping and spoofing. This provides natural normal and attack phases in a single simulation timeline per seed. — **Reversibility:** costly — requires scenario runner support for attack activation time.
- **D-03:** Combined master dataset + strict train/test files — `data/train.csv` (seeds 42, 43) and `data/test.csv` (seed 44) strictly preserve the 10-column feature schema (`packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`, `neighbor_count`, `mobility_speed`, `label`). An auxiliary `data/master.csv` retains the `seed` column for auditability, and `data/dataset_manifest.json` tracks checksums, sample counts, and class distributions. — **Reversibility:** reversible
- **D-04:** Stratified 5-Fold Cross-Validation on combined Seeds 42+43 — Hyperparameter tuning (`GridSearchCV`) runs stratified 5-fold CV on training data, while Seed 44 remains untouched until final evaluation. — **Reversibility:** reversible

### Class Imbalance & Cost-Sensitive Learning
- **D-05:** Cost-sensitive learning with `class_weight='balanced'` — Enforced across Random Forest, Decision Tree, and Support Vector Machine classifiers to penalize minority false negatives without artificial sample synthesis (SMOTE) or discarding normal traffic. — **Reversibility:** reversible
- **D-06:** Strict False Positive Rate (FPR) constraint $\le 1.0\%$ — Any model selected as the champion must achieve at least 99.0% specificity on normal traffic ($FPR \le 1.0\%$), ensuring legitimate nodes are not falsely isolated in Phase 5 routing mitigation. — **Reversibility:** one-way — binding acceptance gate for Phase 5 closed-loop mitigation.
- **D-07:** Standard string labels ('Normal' vs 'Blackhole') — Internally mapped via `LabelEncoder` or structured mapping dictionary, maintaining full forward-compatibility for multi-class classification when 'Grayhole' is introduced in Phase 4. — **Reversibility:** reversible

### Preprocessing & Pipeline Architecture
- **D-08:** Uniform `StandardScaler` inside `sklearn.pipeline.Pipeline` — Preprocessing scaler is bundled with the estimator inside a Scikit-learn Pipeline object for all models (RF, DT, SVM), preventing test data leakage and guaranteeing a unified inference interface. — **Reversibility:** reversible
- **D-09:** Focused grid search with optional `RandomizedSearchCV` — Fast default grid on core parameters (`max_depth`, `min_samples_split`, `n_estimators`, `C`, `gamma`) completing in seconds, with optional RandomizedSearchCV capability for wider exploratory sweeps. — **Reversibility:** reversible
- **D-10:** Multi-faceted feature importance reporting — Combine native Gini impurity importance for tree models with Permutation Importance on the held-out test set (Seed 44) across all models (including SVM), writing results to `results/feature_importance.csv`. — **Reversibility:** reversible

### Model Selection Criteria & Serialization
- **D-11:** Champion model selection by highest malicious F1-score subject to $\text{FPR} \le 1.0\%$ — Winner among RF, DT, and SVM is selected on the unseen test set (Seed 44). Tie-breaker is lower per-sample inference latency and model compactness. — **Reversibility:** reversible
- **D-12:** Model serialization via `joblib` — All tuned candidate pipelines saved to `ml/models/` (`decision_tree.joblib`, `random_forest.joblib`, `svm.joblib`), with the champion saved to `ml/models/best_model.joblib` and metadata documented in `ml/models/model_metadata.json`. — **Reversibility:** reversible
- **D-13:** Security metrics export — Tabular metrics (Accuracy, Precision, Recall, F1, FPR, TN, FP, FN, TP) exported to `results/metrics.csv`, comprehensive textual analysis to `results/evaluation_report.md`, and confusion matrix heatmaps to `results/plots/confusion_matrix_<model>.png`. — **Reversibility:** reversible
- **D-14:** Comprehensive automated test suite — Verification tests in `tests/test_ml_pipeline.py` asserting: (1) zero row overlap across seed splits, (2) strict 9-feature invariance in $X$, (3) loaded model prediction parity with in-memory model, and (4) champion model satisfies $\text{FPR} \le 1.0\%$. — **Reversibility:** reversible

### the agent's Discretion
- Primary GridSearchCV scoring metric: `make_scorer(f1_score, pos_label='Blackhole')`, supplemented by tracking `f1_macro` and `balanced_accuracy`.
- SVM scaling and runtime optimization: `SVC(kernel='rbf', probability=True, class_weight='balanced')` using stratified subsampling (e.g. 10,000 samples) during CV grid search to keep wall-clock execution under 30s.
- Detailed hyperparameter grid boundary values and convergence tolerances.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engineering Contract & Specification
- `AGENTS.md` — Non-negotiable engineering rules (no random row splitting, anti-leakage, full security metrics beyond accuracy, pure Python 3.11, Windows-native)
- `MANET_IDS_BTech_Execution_Guide.md` § Module D — ML classification pipeline specifications, feature schema, and evaluation criteria
- `.planning/PROJECT.md` — Core value and key decisions
- `.planning/REQUIREMENTS.md` — Requirements DATA-04, ML-01, ML-02, ML-03
- `.planning/ROADMAP.md` § Phase 3 — Phase goals and success criteria
- `.planning/phases/02-blackhole-attack-trace-logging-feature-pipeline/02-CONTEXT.md` — Feature extraction and schema definitions
- `.planning/phases/02-blackhole-attack-trace-logging-feature-pipeline/02-VALIDATION.md` — Phase 02 Nyquist validation framework: requirements-to-validation matrix and Gate 2 ≥25% PDR-drop benchmark
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `feature_extraction/extract_features.py` — Sliding-window feature extractor producing the 10-column CSV format
- `simulator/run_scenario.py` — Scenario execution engine producing raw packet traces
- `scenarios/e1_normal_30n.json` & `scenarios/e2_blackhole_30n.json` — Baseline and attack scenario templates
- `data/dataset_sample.csv` — Verified 34,800-row sample dataset (Normal: 34,220, Blackhole: 580)

### Established Patterns
- Pure Python 3.11 with Scikit-learn 1.8.0, Pandas 3.0.2, and NumPy 1.26.4
- Strict seed determinism (seeds 42, 43, 44)
- Pathlib-based Windows path handling
- Matplotlib / Seaborn visualization styling

### Integration Points
- `scripts/build_dataset.py` (or `ml/dataset.py`) to generate and partition multi-seed datasets into `data/train.csv` and `data/test.csv`
- `ml/train.py` to train and tune RF, DT, and SVM models using Scikit-learn Pipelines
- `ml/evaluate.py` to calculate full security metrics, generate confusion matrices, and serialize `ml/models/best_model.joblib`
- `tests/test_ml_pipeline.py` to enforce automated pipeline verification gates
</code_context>

<specifics>
## Specific Ideas

- Seeds 42 and 43 for train/validation; Seed 44 strictly held out for final test evaluation.
- Scenario attack `start_time` (e.g. $t = 100\text{s}$) to generate composite normal/attack timelines per seed.
- Cost-sensitive `class_weight='balanced'` to overcome ~1.7% minority attack rarity.
- Hard constraint of $\text{FPR} \le 1.0\%$ to avoid isolating legitimate routers in Phase 5.
- Scikit-learn `Pipeline([('scaler', StandardScaler()), ('classifier', ...)])` serialized with `joblib.dump`.
- Export results to `results/metrics.csv`, `results/evaluation_report.md`, and `results/plots/confusion_matrix_<model>.png`.
</specifics>

<deferred>
## Deferred Ideas

- Multi-class Grayhole attack classification and generalization testing (scheduled for Phase 4)
- Dynamic closed-loop routing mitigation and network QoS re-evaluation (scheduled for Phase 5)
- Interactive web dashboard and final project deliverables (scheduled for Phase 6)
</deferred>

---

*Phase: 03-Machine Learning Classification Pipeline & Evaluation*  
*Context gathered: 2026-10-25*
