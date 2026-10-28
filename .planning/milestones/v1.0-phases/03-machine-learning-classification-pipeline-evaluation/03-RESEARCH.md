# Phase 03: Machine Learning Classification Pipeline & Evaluation - Research

**Researched:** 2026-10-27
**Domain:** Classical ML classification on tabular MANET behavioral features (scikit-learn, anti-leakage seed partitioning, FPR-constrained champion selection)
**Confidence:** HIGH (all load-bearing API and data-signal claims verified by runtime probes this session on the installed stack and the real Phase 2 dataset)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Implementation Decisions (Locked)

**Dataset Splitting & Seed Partitioning**
- **D-01:** Fixed seed holdout — Seeds 42 and 43 are allocated for training and cross-validation; Seed 44 is held out strictly for final test evaluation. Guarantees zero intra-run or temporal autocorrelation leakage across splits. — **Reversibility:** costly — matches Gate 2 benchmark and defines downstream dataset partitions.
- **D-02:** Single composite scenario set with dynamic attack onset — Scenarios configure an attack `start_time` (e.g. $t = 100.0\text{s}$) where the malicious node behaves normally initially before activating Blackhole dropping and spoofing. This provides natural normal and attack phases in a single simulation timeline per seed. — **Reversibility:** costly — requires scenario runner support for attack activation time.
- **D-03:** Combined master dataset + strict train/test files — `data/train.csv` (seeds 42, 43) and `data/test.csv` (seed 44) strictly preserve the 10-column feature schema (`packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`, `neighbor_count`, `mobility_speed`, `label`). An auxiliary `data/master.csv` retains the `seed` column for auditability, and `data/dataset_manifest.json` tracks checksums, sample counts, and class distributions. — **Reversibility:** reversible
- **D-04:** Stratified 5-Fold Cross-Validation on combined Seeds 42+43 — Hyperparameter tuning (`GridSearchCV`) runs stratified 5-fold CV on training data, while Seed 44 remains untouched until final evaluation. — **Reversibility:** reversible

**Class Imbalance & Cost-Sensitive Learning**
- **D-05:** Cost-sensitive learning with `class_weight='balanced'` — Enforced across Random Forest, Decision Tree, and Support Vector Machine classifiers to penalize minority false negatives without artificial sample synthesis (SMOTE) or discarding normal traffic. — **Reversibility:** reversible
- **D-06:** Strict False Positive Rate (FPR) constraint $\le 1.0\%$ — Any model selected as the champion must achieve at least 99.0% specificity on normal traffic ($FPR \le 1.0\%$), ensuring legitimate nodes are not falsely isolated in Phase 5 routing mitigation. — **Reversibility:** one-way — binding acceptance gate for Phase 5 closed-loop mitigation.
- **D-07:** Standard string labels ('Normal' vs 'Blackhole') — Internally mapped via `LabelEncoder` or structured mapping dictionary, maintaining full forward-compatibility for multi-class classification when 'Grayhole' is introduced in Phase 4. — **Reversibility:** reversible

**Preprocessing & Pipeline Architecture**
- **D-08:** Uniform `StandardScaler` inside `sklearn.pipeline.Pipeline` — Preprocessing scaler is bundled with the estimator inside a Scikit-learn Pipeline object for all models (RF, DT, SVM), preventing test data leakage and guaranteeing a unified inference interface. — **Reversibility:** reversible
- **D-09:** Focused grid search with optional `RandomizedSearchCV` — Fast default grid on core parameters (`max_depth`, `min_samples_split`, `n_estimators`, `C`, `gamma`) completing in seconds, with optional RandomizedSearchCV capability for wider exploratory sweeps. — **Reversibility:** reversible
- **D-10:** Multi-faceted feature importance reporting — Combine native Gini impurity importance for tree models with Permutation Importance on the held-out test set (Seed 44) across all models (including SVM), writing results to `results/feature_importance.csv`. — **Reversibility:** reversible

**Model Selection Criteria & Serialization**
- **D-11:** Champion model selection by highest malicious F1-score subject to $\text{FPR} \le 1.0\%$ — Winner among RF, DT, and SVM is selected on the unseen test set (Seed 44). Tie-breaker is lower per-sample inference latency and model compactness. — **Reversibility:** reversible
- **D-12:** Model serialization via `joblib` — All tuned candidate pipelines saved to `ml/models/` (`decision_tree.joblib`, `random_forest.joblib`, `svm.joblib`), with the champion saved to `ml/models/best_model.joblib` and metadata documented in `ml/models/model_metadata.json`. — **Reversibility:** reversible
- **D-13:** Security metrics export — Tabular metrics (Accuracy, Precision, Recall, F1, FPR, TN, FP, FN, TP) exported to `results/metrics.csv`, comprehensive textual analysis to `results/evaluation_report.md`, and confusion matrix heatmaps to `results/plots/confusion_matrix_<model>.png`. — **Reversibility:** reversible
- **D-14:** Comprehensive automated test suite — Verification tests in `tests/test_ml_pipeline.py` asserting: (1) zero row overlap across seed splits, (2) strict 9-feature invariance in $X$, (3) loaded model prediction parity with in-memory model, and (4) champion model satisfies $\text{FPR} \le 1.0\%$. — **Reversibility:** reversible

### the agent's Discretion
- Primary GridSearchCV scoring metric: `make_scorer(f1_score, pos_label='Blackhole')`, supplemented by tracking `f1_macro` and `balanced_accuracy`.
- SVM scaling and runtime optimization: `SVC(kernel='rbf', probability=True, class_weight='balanced')` using stratified subsampling (e.g. 10,000 samples) during CV grid search to keep wall-clock execution under 30s.
- Detailed hyperparameter grid boundary values and convergence tolerances.

### Deferred Ideas (OUT OF SCOPE)
- Multi-class Grayhole attack classification and generalization testing (scheduled for Phase 4)
- Dynamic closed-loop routing mitigation and network QoS re-evaluation (scheduled for Phase 5)
- Interactive web dashboard and final project deliverables (scheduled for Phase 6)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-04 | Scenario- and seed-based dataset partitioner splitting train and test sets strictly across independent scenario runs (zero random row splitting) | Seed-holdout design (D-01): partition key = `seed` recorded in `master.csv`; runtime probe confirms dataset signal strength supports seed-level holdout; split-integrity test semantics defined below (Pitfall 6) |
| ML-01 | Multi-classifier training pipeline implementing Random Forest, Decision Tree, and Support Vector Machine models | All three classifier+Pipeline+GridSearchCV patterns runtime-verified on sklearn 1.8.0 with real data timings (RF grid 45.7s, DT 7.4s, SVM 6-combo grid 115.5s @10k subsample) |
| ML-02 | Security metric evaluator reporting Accuracy, Precision, Recall, F1-Score, FPR, and Confusion Matrix for malicious class detection | `confusion_matrix(labels=['Normal','Blackhole']).ravel()` → `(tn, fp, fn, tp)` orientation runtime-verified; FPR = FP/(FP+TN); full metric call set verified |
| ML-03 | Model persistence saving trained pipeline estimators and scalers to disk | `joblib.dump/load` Pipeline round-trip prediction parity runtime-verified (identical predictions); compress=3 verified |
</phase_requirements>

## Summary

Phase 3 is a greenfield ML module (`ml/`) plus a dataset-partitioning layer (`scripts/build_dataset.py`), consuming the verified Phase 2 feature pipeline. Every sklearn API pattern the phase needs was **probed live this session** against the installed stack (sklearn 1.8.0, pandas 3.0.2, numpy 1.26.4, joblib 1.5.3, pytest 9.0.2) — no new packages are required. The decisive research finding is a **signal-strength probe on the real Phase 2 dataset** (`data/dataset_sample.csv`, 34,800 rows, 580 Blackhole [1.67%]): Random Forest and Decision Tree **pass the D-06 FPR ≤ 1.0% gate with near-default settings** (FPR 0.49% / 0.50%, F1 0.83/0.83), while **SVM with default C/gamma fails it badly (FPR 11.5%)** — but a small tuned grid (C=10, γ=0.01) brings SVM to FPR 0.04% (PASS). The champion-selection logic in D-11 already handles a gate-failing SVM gracefully (it simply loses); the planner must NOT write a test asserting all three models pass the gate (the discussion-log variant of D-14 said so, but CONTEXT.md governs: champion-only).

Three non-obvious engineering points dominate the phase: (1) **D-02's attack `start_time` is a simulator seam change**, not just an ML concern — the attack strategy is wired via duck-typed hooks (`attack_behavior`), and the cleanest onset implementation is a SimPy `env.timeout(start_time)` activation process in `SimulationRunner` that assigns the strategy at `t = start_time`, leaving `aodv.py` and the strategy classes untouched; (2) **pre-onset attacker windows must be labeled `'Normal'`, not `'Blackhole'`** — the current extractor labels by node identity only, which would inject ~31% contradictory label noise into the minority class under the composite-onset design; (3) **`SVC.classes_` returns `['Blackhole', 'Normal']` alphabetically** — any `predict_proba` column indexing by position (`[:, 1]`) is a latent Phase 5 bug; index via `classes_` lookup.

Wall-clock budget is comfortable: the entire phase (dataset regeneration for 3 seeds + grids + evaluation + tests) computes in **under ~10 minutes** on this machine. The one discretion-area refinement: SVM grid search at 10k stratified subsample takes ~2 minutes for a 6-combo grid — the "under 30s" figure in the discretion notes is not achievable at that grid size (documented in Assumptions Log A2; the area is explicitly the agent's discretion, so this is a refinement, not a re-decision).

**Primary recommendation:** Build `ml/` as a thin, deterministic sklearn pipeline layer — `ml/dataset.py` (seed-partitioned builder with time-aware labels + manifest), `ml/train.py` (three tuned Pipelines, `GridSearchCV` multi-metric `refit='f1_blackhole'`, probability=False during CV), `ml/evaluate.py` (seed-44 metrics, champion gate, plots, report, importances) — with the attack-onset activation added as a SimPy process in `simulator/run_scenario.py`, and all gates enforced in `tests/test_ml_pipeline.py`.

## Architectural Responsibility Map

| Capability | Primary Tier (module) | Secondary Tier | Rationale |
|------------|----------------------|----------------|-----------|
| Attack onset activation (`attack.start_time`) | `simulator/run_scenario.py` (SimulationRunner) | — (attacks/ untouched) | Strategy assignment is a runner concern; duck-typed `attack_behavior=None` before onset = perfectly normal node; import boundary (simulator ⊄ attacks) preserved |
| Time-aware window labeling | `feature_extraction/extract_features.py` (extended, backward-compatible) | `ml/dataset.py` | Labels are ground-truth-only metadata; extractor owns label assignment; dataset builder passes `start_time` through |
| Seed-partitioned dataset build + manifest | `ml/dataset.py` + `scripts/build_dataset.py` CLI | simulator, feature_extraction | Orchestrates seeded runs; owns `master.csv` (seed column), `train.csv`, `test.csv`, manifest checksums |
| Classifier training & tuning | `ml/train.py` | — | Pure sklearn: Pipeline + GridSearchCV stratified 5-fold on seeds 42+43 |
| Security metric evaluation | `ml/evaluate.py` | — | Pure sklearn.metrics on untouched seed 44; champion gate (D-06/D-11) |
| Model persistence | `ml/train.py` (candidates) + `ml/evaluate.py` (champion) | — | joblib dump/load; metadata JSON |
| Acceptance gates (D-14) | `tests/test_ml_pipeline.py` | — | Independent of training code; asserts artifacts satisfy gates |
| Network QoS comparison vs plain AODV | — (Phase 5, RESP-02) | — | Out of scope this phase; ml/evaluate must still export per-model artifacts Phase 5 can consume |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scikit-learn | 1.8.0 (installed) [VERIFIED: runtime probe `python -c`, this session] | Pipeline, StandardScaler, RF/DT/SVC, GridSearchCV, metrics, permutation_importance | Project-standard since init; APIs probed live this session |
| pandas | 3.0.2 (installed) [VERIFIED: runtime probe] | CSV dataset I/O, schema manipulation, feature grouping | Phase 2 pattern; 3.x gotchas documented in AGENTS.md |
| numpy | 1.26.4 (installed) [VERIFIED: runtime probe] | Feature matrix X as ndarray, RNG seeding | 1.26.x pinned (AGENTS.md: numpy 2 migration notes do NOT apply) |
| joblib | 1.5.3 (installed) [VERIFIED: runtime probe] | Pipeline serialization (`joblib.dump/load`, compress=3) | sklearn's own recommended persistence path [CITED: scikit-learn.org/stable/model_persistence.html] |
| pytest | 9.0.2 (installed) [VERIFIED: runtime probe; `__pycache__` filenames] | D-14 acceptance test suite | Existing 18-test suite runs green in 9.25s |
| matplotlib + seaborn | 3.10.8 / 0.13.2 (installed) [VERIFIED: runtime probe] | Confusion-matrix heatmaps (D-13) | Phase 2 established styling patterns |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hashlib (stdlib) | — | SHA-256 checksums in `dataset_manifest.json` (D-03) | Manifest build |
| pathlib (stdlib) | — | Windows-native path handling | Everywhere (Phase 2 established pattern) |
| argparse (stdlib) | — | CLI for `scripts/build_dataset.py` | Consistent with existing scripts |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `class_weight='balanced'` | SMOTE / undersampling | REJECTED by D-05 (locked: no synthesis, no discarding); probe shows balanced weights + strong signal suffice |
| `GridSearchCV` | `RandomizedSearchCV` | D-09 locks focused grid as default; RandomizedSearchCV optional extra, don't build unless grids underperform |
| `joblib` | `skops.io` | skops is safer (non-pickle) but adds a dependency; joblib is D-12-locked and single-user local trust is acceptable |
| `LabelEncoder` | explicit mapping dict `{'Normal': 0, 'Blackhole': 1}` / native string labels | See Pitfall 2 — native string labels + explicit `pos_label='Blackhole'` is safer than LabelEncoder's alphabetical mapping |

**Installation:**
```bash
# Nothing to install — the full stack is present and verified:
python -c "import sklearn, pandas, numpy, joblib, pytest, matplotlib, seaborn"
```

**Version verification:** All versions confirmed live this session (see Core table). No registry lookups needed — zero new packages.

## Package Legitimacy Audit

> Required whenever this phase installs external packages.

**No external packages are installed in this phase.** The entire stack (scikit-learn 1.8.0, pandas 3.0.2, numpy 1.26.4, joblib 1.5.3, pytest 9.0.2, matplotlib 3.10.8, seaborn 0.13.2) is already installed and import-verified this session [VERIFIED: runtime probe]. No `pip install` occurs in any planned task; no legitimacy gate runs required.

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
 scenario JSONs (seeds 42,43,44; attack.start_time=100.0)
        │
        ▼
 SimulationRunner.run(seed) ── attack onset: env.timeout(100.0) ──► attack_behavior assigned
        │                                                            (None before → normal node)
        ▼
 traces/*.csv  (packet events + NODE_STATUS, gitignored)
        │
        ▼
 feature_extraction.extract_features_from_trace()
   • sliding-window 9 features
   • time-aware label: Blackhole iff (node is attacker AND t ≥ start_time)
        │
        ▼
 ml/dataset.py ──► data/master.csv (11 cols: 10 schema + seed)
        │          ├─► data/train.csv  (seeds 42,43 — exactly 10 cols)
        │          ├─► data/test.csv   (seed 44    — exactly 10 cols)
        │          └─► data/dataset_manifest.json (sha256, counts, class dist)
        │
        ▼
 ml/train.py ── Pipeline([StandardScaler, clf]) × {RF, DT, SVM}
   • GridSearchCV(cv=StratifiedKFold(5), scoring={f1_blackhole, f1_macro, balanced_accuracy},
                  refit='f1_blackhole')  on train.csv ONLY (seeds 42+43)
   • SVM: stratified 10k subsample, probability=False during CV
        │
        ▼
 ml/evaluate.py ── seed 44 test set (UNTOUCHED until now)
   • full metrics (acc/prec/rec/F1/FPR/TN/FP/FN/TP) → results/metrics.csv
   • confusion heatmaps → results/plots/confusion_matrix_<model>.png
   • Gini + permutation importance → results/feature_importance.csv
   • champion = max F1(Blackhole) s.t. FPR ≤ 1.0% → ml/models/best_model.joblib
   • final refit with probability=True (predictions unchanged — verified)
   • inference latency + model size (D-11 tie-breakers)
        │
        ▼
 tests/test_ml_pipeline.py ── D-14 gates: seed disjointness, 9-feature
   invariance, load parity, champion FPR ≤ 1.0%
```

**Primary use-case trace:** scenario JSON → seeded simulation → trace → features → master/train/test → GridSearchCV on train → seed-44 evaluation → champion joblib → tests assert gates. Every arrow is deterministic given the seed.

### Recommended Project Structure
```
ml/
├── __init__.py           # package marker
├── dataset.py            # build_master + partition_by_seed + write_manifest
├── train.py              # build_pipelines(), tune_all(), save candidates
├── evaluate.py           # evaluate_on_test(), select_champion(), exports
├── models/               # joblib artifacts (see Assumption A3: git policy)
└── (artifacts: decision_tree.joblib, random_forest.joblib, svm.joblib, best_model.joblib, model_metadata.json)
scripts/
└── build_dataset.py      # CLI orchestrator: run sims → features → master → train/test + manifest
results/
├── metrics.csv
├── feature_importance.csv
├── evaluation_report.md
└── plots/                # only results/ subdir not gitignored
tests/
└── test_ml_pipeline.py   # D-14 acceptance gates
```

### Pattern 1: Uniform Pipeline with multi-metric GridSearchCV (D-04/D-05/D-08/D-09)
**What:** One `Pipeline([('scaler', StandardScaler()), ('clf', <estimator>)])` per model family; a scoring dict tracks the locked primary metric plus discretion supplements; `refit` names the primary metric.
**When to use:** Every training path; never fit a bare estimator (scaler must travel with the model for Phase 5 inference).
**Example:**
```python
# Source: runtime probe this session (sklearn 1.8.0) + scikit-learn.org plot_multi_metric_evaluation
from sklearn.metrics import make_scorer, f1_score

scoring = {
    "f1_blackhole": make_scorer(f1_score, pos_label="Blackhole"),   # D-11 primary
    "f1_macro": "f1_macro",                                          # discretion tracker
    "balanced_accuracy": "balanced_accuracy",                        # discretion tracker
}
grid = GridSearchCV(
    pipeline, param_grid,
    scoring=scoring, refit="f1_blackhole",
    cv=5,  # int cv -> StratifiedKFold for classifiers [CITED: sklearn GridSearchCV docs]
    n_jobs=1, return_train_score=False,   # serial grid; RF uses n_jobs=-1 internally
)
grid.fit(X_train, y_train)   # train.csv rows ONLY (seeds 42+43); seed 44 never passed
best = grid.best_estimator_  # fully refit Pipeline on all of train.csv
```
**Verified wall-clock on real data (26.1k train rows):** DT 8-combo×5 folds = 7.4s; RF 6-combo×5 folds = 45.7s (serial); SVM 6-combo×5 folds @10k subsample = 115.5s [VERIFIED: runtime probe].

### Pattern 2: Binary confusion-matrix orientation and FPR (D-06/D-13)
**What:** Fixed `labels=['Normal', 'Blackhole']` ordering makes `.ravel()` yield `(tn, fp, fn, tp)` with Blackhole as the positive class — the security framing.
**Example:**
```python
# Source: runtime probe this session; scikit-learn.org model_evaluation docs
tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=["Normal", "Blackhole"]).ravel()
fpr = fp / (fp + tn)          # D-06 gate: fpr <= 0.01
```
Probe-verified: constructed case yielded tn=7 fp=1 fn=1 tp=1, FPR=0.125 — orientation confirmed.

### Pattern 3: Attack onset activation — SimPy timeout strategy swap (D-02)
**What:** In `SimulationRunner`, when `attack.start_time` is configured, schedule a SimPy process that waits `start_time` then assigns the strategy. Before activation `attack_behavior` is `None`, so the node is a completely normal AODV node (both hook sites no-op).
**When to use:** `ml/dataset.py`'s composite runs. Zero changes to `aodv.py` or `attacks/` — the existing duck-typed hooks carry it.
**Verified hook sites (both already context-free of time — that's why the runner-side swap is the clean seam):**
```python
# Source: [VERIFIED: simulator/run_scenario.py:319] — data-drop hook
if aodv_node.attack_behavior is not None and hasattr(aodv_node.attack_behavior, "should_drop_data") and aodv_node.attack_behavior.should_drop_data(pkt.src, pkt.dst, pkt.pkt_id):

# Source: [VERIFIED: simulator/aodv.py:183-191] — spoofed-RREP hook
if (
    self.attack_behavior is not None
    and hasattr(self.attack_behavior, "get_spoofed_rrep_params")
    and self.node_id != rreq.dest
    and rreq.originator != self.node_id
):
    spoofed_seq, spoofed_hops = self.attack_behavior.get_spoofed_rrep_params(
        rreq.dest, rreq.dest_seq
    )
```
**Current eager assignment (what onset replaces):**
```python
# Source: [VERIFIED: simulator/run_scenario.py:141-146]
for aid in self.attacker_ids:
    if aid in self.aodv_nodes:
        strategy = create_attack_strategy(attack_type, seq_offset=seq_offset, spoofed_hops=spoofed_hops)
        self.aodv_nodes[aid].attack_behavior = strategy
        if attack_type.lower() == "blackhole":
            self.aodv_nodes[aid].is_blackhole = True
```
**Recommended implementation (sketch):**
```python
def _delayed_attack_activation(self, aid, strategy, start_time, attack_type):
    yield self.env.timeout(start_time)
    self.aodv_nodes[aid].attack_behavior = strategy
    if attack_type.lower() == "blackhole":
        self.aodv_nodes[aid].is_blackhole = True
# in attack wiring: if attack_cfg.get("start_time") is None → eager (backward compat);
# else env.process(self._delayed_attack_activation(...)) scheduled at setup (before env.run()).
```

### Pattern 4: Time-aware window labeling (D-02 × DATA-03)
**What:** Under composite onset, a window row is `Blackhole` iff the node is an attacker **and** the attack is active at that window time: `label = "Blackhole" if (nid in attacker_nodes and t >= attack_start_time) else "Normal"`.
**Why it is mandatory:** The current extractor labels by node identity alone:
```python
# Source: [VERIFIED: feature_extraction/extract_features.py:189]
label = "Blackhole" if nid in attacker_nodes else "Normal"
```
With onset at t=100s, the attacker's ~90 pre-onset windows per seed carry fully normal features but (under identity labeling) a `'Blackhole'` label — ~31% contradictory noise in the minority class (180 noisy rows vs ~580 total Blackhole rows at current composition). Time-aware labeling keeps X untouched (anti-leakage invariance holds: `start_time` is scenario ground-truth metadata feeding only the target column) and preserves the Phase 2 test pattern (`tests/test_feature_pipeline.py::test_anti_leakage_invariance`).
**Implementation:** extend `extract_features_from_trace` with optional `attack_start_time: Optional[float] = None` (None ⇒ current identity behavior — Phase 2 tests and Gate 2 scripts stay green).

### Pattern 5: SVM probability only on the final refit (D-09 discretion refinement)
**What:** Grid-search SVMs with `probability=False` (Platt scaling adds ~10x fit cost: 1.47s → 16.9s per 10k-row fit [VERIFIED: probe]); after champion selection, refit the winning SVM config with `probability=True` and re-run the full seed-44 evaluation on that saved pipeline.
**Why safe:** runtime-verified — same-config refit with `probability=True` produced **identical** hard predictions on 3,000 test rows [VERIFIED: runtime probe `svc_probability_refit_predict_parity: identical=True`].
**Why needed:** Phase 5 (RESP-01, guide Module E) wants "alert when confidence exceeds a predefined threshold" → the persisted champion should expose `predict_proba`.

### Pattern 6: `predict_proba` column indexing (D-12 forward-compat)
**What:** With string labels, `SVC.classes_` is **alphabetical**: `['Blackhole', 'Normal']` [VERIFIED: runtime probe]. RF/DT `classes_` follow `np.unique` — also alphabetical here.
**Rule:** never index `proba[:, 1]` assuming "positive last". Always resolve the positive column via `classes_`:
```python
pos_col = list(pipe.classes_).index("Blackhole")   # 0 for binary string labels!
p_blackhole = pipe.predict_proba(X)[:, pos_col]
```
This is the trap Phase 5 threshold logic would fall into — encode the lookup in `ml/evaluate.py` from day one.

### Anti-Patterns to Avoid
- **Random row splitting anywhere in the train/test path:** D-01 forbids it; even the "validation probe" in this research that used a row split is labeled as probe-only. The production partition key is the seed.
- **`LabelEncoder.fit_transform` then `pos_label=1`:** alphabetical fit gives `Blackhole→0`, `Normal→1` — a default `pos_label=1` then measures the *Normal* class. Either keep native string labels with explicit `pos_label='Blackhole'`, or use an explicit mapping dict `{'Normal': 0, 'Blackhole': 1}` (D-07 allows both; the dict is the safer one).
- **Fitting the scaler outside the Pipeline** (`scaler.fit(X_train)` then transforming test data in evaluate scripts): duplicates what the Pipeline already does and invites leakage; D-08 mandates the Pipeline.
- **Asserting all three models pass the FPR gate:** SVM is the marginal model; CONTEXT.md D-14 gates the champion only.
- **Iteration over unordered `set()` in code that feeds training/eval order:** AGENTS.md known-failure — identical runs must stay identical; sort node IDs everywhere (existing code already does `sorted(...)`).
- **Committing generated data/models:** `.gitignore` covers `data/` and `results/*` except `results/plots/` [VERIFIED: .gitignore:2-7]; decide the `ml/models/*.joblib` policy explicitly (Assumption A3).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stratified folds for CV | Custom fold loops over seeds/balanced subsets | `GridSearchCV(cv=5)` (int → StratifiedKFold for classifiers) [CITED: sklearn docs] | Hand-rolled folds reintroduce exactly the imbalance errors D-04/D-05 exist to prevent |
| Balanced class weighting | Manual weight dicts computed from value_counts | `class_weight='balanced'` (D-05-locked) | Identical math (`n/(2·n_c)`), zero bug surface |
| Confusion-matrix bookkeeping | Hand-built counting loops over y pairs | `confusion_matrix(labels=['Normal','Blackhole']).ravel()` | Orientation is the whole game; verified convention exists |
| F1/FPR/precision/recall per class | Custom ratio functions | `f1_score/precision_score/recall_score(pos_label='Blackhole')`, `accuracy_score`, `balanced_accuracy_score` | String pos_label works natively on sklearn 1.8 (probe-verified) |
| Model persistence format | Custom npz/pickle schemas | `joblib.dump(..., compress=3)` / `joblib.load` [CITED: model_persistence docs] | Round-trip parity probe-verified; metadata JSON complements it |
| Stratified subsampling for SVM | Reservoir/numpy choice tricks | `train_test_split(train_size=10000, stratify=y, random_state=0)` | Deterministic + class-ratio preserving |
| Feature importance | Hand-written ablation loops | `clf.feature_importances_` (Gini) + `sklearn.inspection.permutation_importance` [CITED: sklearn docs] | Standard estimators + per-repeat std for significance |
| Confusion-matrix plots | Custom matplotlib matrix code | `seaborn.heatmap(cm, annot=True, fmt='d', ...)` | Existing styling pattern; Agg backend |

**Key insight:** every one of these is either D-locked or has a probe-verified call signature — the risk in this phase is *methodology* (splitting, labeling, orientation), not API wrangling. Hand-rolling any of the above would add unverified code where a verified primitive exists.

## Common Pitfalls

### Pitfall 1: Pre-onset attacker windows labeled `'Blackhole'` (D-02 mislabeling)
**What goes wrong:** Identity-based labeling (current extractor line 189) + composite onset ⇒ attacker node's ~90 normal-behavior windows per seed are labeled Blackhole while looking statistically normal ⇒ ~31% label noise in the minority class ⇒ depressed recall, unstable CV.
**Why it happens:** Phase 2's extractor predates the onset concept (attacks were active from t=0).
**How to avoid:** Time-aware labeling (Pattern 4): `Blackhole iff nid in attacker_nodes and t >= attack.start_time`, passed from scenario config through `ml/dataset.py`.
**Warning signs:** CV f1_blackhole ≪ probe baseline (0.83); inspect class-conditional feature means of training rows — mislabeled rows pull Blackhole means toward Normal.

### Pitfall 2: `LabelEncoder` alphabetical mapping flips the positive class
**What goes wrong:** `LabelEncoder().fit(['Blackhole','Normal'])` → `Blackhole→0, Normal→1`; a then-default `pos_label=1` (or `proba[:,1]`) silently evaluates *Normal* as positive — precision/recall/F1/FPR all measure the wrong class, and a "perfect" report is wrong.
**Why it happens:** Encoder maps by sorted order; thresholds default to "last column".
**How to avoid:** Native string labels end-to-end + explicit `pos_label='Blackhole'` everywhere, or an explicit mapping dict; for proba columns always resolve via `classes_` (Pattern 6).
**Warning signs:** recall ≫ drop-signal plausibility, or FPR computed against the wrong diagonal; assert `classes_` in the parity test.

### Pitfall 3: SVM failing the FPR gate at default hyperparameters
**What goes wrong:** `SVC(class_weight='balanced')` with default C=1/γ='scale' hit **FPR 11.49%** on real data (probe) — 11x over the D-06 gate.
**Why it happens:** balanced weights inflate the minority decision region; unscaled C/gamma mismatched to feature scales.
**How to avoid:** SVM grid must include larger C values (probe: C=10, γ=0.01 → FPR 0.04%, PASS) and scaled features (D-08 provides). Champion selection (D-11) tolerates a gate-failing SVM — it just loses; do **not** assert the gate on all three models.
**Warning signs:** `results/metrics.csv` SVM row FPR > 0.01 while RF passes → expected; all three failing → re-tune before selection.

### Pitfall 4: `predict_proba` column-position assumptions
**What goes wrong:** `proba[:, 1]` is `P(Normal)` for string-label SVCs (`classes_=['Blackhole','Normal']` — verified), so any confidence-threshold code written "positive last" flags normals.
**How to avoid:** Pattern 6 (`list(pipe.classes_).index('Blackhole')`); assert column semantics in the parity test.
**Warning signs:** Phase 5 isolation of legit nodes despite passing row-level FPR gate.

### Pitfall 5: "Under 30s" SVM CV budget is not real (D-09 discretion refinement)
**What goes wrong:** Planning an SVM grid expecting 30s wall-clock; actual measured: 115.5s for a 6-combo×5-fold grid on a 10k stratified subsample (probability=False); each `probability=True` 10k fit = 16.9s.
**How to avoid:** Budget SVM CV at ~2 min (or shrink grid to 3-4 combos / 5k subsample); probability=False during CV, True on final refit (Pattern 5). RF/DT grids are genuinely fast (7.4s / 45.7s measured).
**Warning signs:** timeout-style test wrappers around training; training scripts that re-run grids on every test invocation (grids live in `ml/train.py`, never in tests).

### Pitfall 6: "Zero row overlap" test implemented as feature-row equality
**What goes wrong:** A test asserting no identical feature vectors across train/test **will flake** — neutral zero-traffic fallback rows (fwd=1.0, drop=0.0, delay=0, rates=0, throughput=0) recur legitimately in every seed; thousands of rows share near-degenerate values.
**Why it happens:** The meaningful invariant is *provenance disjointness*, not value disjointness.
**How to avoid:** Assert via `data/master.csv`: `set(train_seeds) ⊆ {42,43}`, `set(test_seeds) == {44}`, `len(train)+len(test) == len(master)`, schema exactness of train/test (10 cols, order), and manifest checksums match. That is the D-14 (1) test done right.
**Warning signs:** a flaky equality test failing only on some builds.

### Pitfall 7: pandas 3.0 dtype drift on CSV round-trips
**What goes wrong:** Label column comes back as `str` dtype (not `object`) [VERIFIED: runtime probe — roundtrip dtype check; AGENTS.md documents pandas 3.x `str` default]; tests comparing dtypes to `'object'` fail; `DataFrame.applymap` no longer exists.
**How to avoid:** Assert schema by column names/order (and numeric dtype for the 9 features), not `object`; use `DataFrame.map` if ever needed.
**Warning signs:** dtype assertions in `test_ml_pipeline.py` failing while data is fine.

### Pitfall 8: Nondeterminism creeping into "identical" runs
**What goes wrong:** Same seed ⇒ different dataset/model ⇒ manifest checksums drift, gate tests flake.
**Why it happens:** Missing `random_state` (RF/DT/SVC, train_test_split subsample), `cv` shuffling, or set-order iteration.
**How to avoid:** `random_state=42` on every estimator and subsampler; `cv=5` int (StratifiedKFold, shuffle=False → deterministic) [CITED: sklearn docs]; sorted iteration (AGENTS.md rule).
**Warning signs:** two runs of `build_dataset.py` producing different manifest hashes.

### Pitfall 9: Model/artifact placement vs `.gitignore`
**What goes wrong:** `data/` is fully gitignored and `results/*` ignored except `results/plots/` [VERIFIED: .gitignore:2-7] — a manifest/report expected in git won't be; `ml/models/` is currently NOT ignored, so multi-MB joblibs will be silently staged.
**How to avoid:** Keep `data/` ignored (manifest regenerates deterministically with seeds); explicitly add `ml/models/*.joblib` to `.gitignore` while committing `model_metadata.json` (Assumption A3), or consciously commit small champion artifacts.
**Warning signs:** `git status` showing 50MB blobs after training.

## Code Examples

### Dataset partitioning with manifest (DATA-04, D-03)
```python
# Source: pattern grounded in [VERIFIED: scripts/generate_datasets.py:8-10] sys.path bootstrap
#         and [VERIFIED: feature_extraction/extract_features.py:18-29] schema
import hashlib, json
from pathlib import Path
import pandas as pd

SCHEMA_COLUMNS = [  # verbatim from feature_extraction/extract_features.py:18-29
    "packet_forward_ratio", "packet_drop_ratio", "avg_delay",
    "route_request_rate", "route_reply_rate", "throughput",
    "hop_count", "neighbor_count", "mobility_speed", "label",
]
TRAIN_SEEDS = (42, 43)   # D-01
TEST_SEEDS = (44,)       # D-01

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

master = pd.concat(run_frames, ignore_index=True)          # 10 schema cols + 'seed'
train = master[master["seed"].isin(TRAIN_SEEDS)][SCHEMA_COLUMNS]
test  = master[master["seed"].isin(TEST_SEEDS)][SCHEMA_COLUMNS]
# assert len(train) + len(test) == len(master) and no seed overlap
# write train.csv / test.csv (10 cols exactly) + master.csv (11) + manifest
```

### The three tuned pipelines (ML-01, D-05/D-08)
```python
# Source: runtime-probed signatures (sklearn 1.8.0) this session
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC

def build_pipelines():
    return {
        "random_forest": (
            Pipeline([("scaler", StandardScaler()),
                      ("clf", RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=-1))]),
            {"clf__n_estimators": [50, 100], "clf__max_depth": [8, 12, None]},
        ),
        "decision_tree": (
            Pipeline([("scaler", StandardScaler()),
                      ("clf", DecisionTreeClassifier(class_weight="balanced", random_state=42))]),
            {"clf__max_depth": [4, 8, 12, None], "clf__min_samples_split": [2, 10]},
        ),
        "svm": (
            Pipeline([("scaler", StandardScaler()),
                      ("clf", SVC(kernel="rbf", class_weight="balanced", random_state=42))]),
            {"clf__C": [1, 10, 100], "clf__gamma": ["scale", 0.01]},   # probe: C=10,gamma=0.01 -> FPR 0.04%
        ),
    }
```

### Champion selection with the FPR gate (D-06/D-11)
```python
# Source: orientation verified via probe (Pattern 2); selection logic per D-11
rows = []
for name, pipe in fitted.items():
    yp = pipe.predict(X_test)                      # X_test = seed-44 rows ONLY
    tn, fp, fn, tp = confusion_matrix(y_test, yp, labels=["Normal", "Blackhole"]).ravel()
    fpr = fp / (fp + tn)
    rows.append({"model": name, "accuracy": accuracy_score(y_test, yp),
                 "precision": precision_score(y_test, yp, pos_label="Blackhole"),
                 "recall": recall_score(y_test, yp, pos_label="Blackhole"),
                 "f1_blackhole": f1_score(y_test, yp, pos_label="Blackhole"),
                 "fpr": fpr, "tn": tn, "fp": fp, "fn": fn, "tp": tp})
eligible = [r for r in rows if r["fpr"] <= 0.01]
if not eligible:
    raise RuntimeError("No candidate satisfies D-06 FPR gate — do NOT silently select; escalate.")
champion = max(eligible, key=lambda r: r["f1_blackhole"])
```

### Persistence + parity (ML-03, D-12/D-14)
```python
# Source: probe-verified roundtrip parity (joblib 1.5.3, sklearn 1.8.0)
import joblib
joblib.dump(champion, "ml/models/best_model.joblib", compress=3)
loaded = joblib.load("ml/models/best_model.joblib")
assert (loaded.predict(X_slice) == champion.predict(X_slice)).all()   # D-14 (3)
```

### Confusion-matrix heatmap (D-13)
```python
# Source: established repo styling (AGENTS.md); seaborn 0.13.2 + matplotlib Agg
import matplotlib
matplotlib.use("Agg")            # headless Windows-safe
import seaborn as sns
import matplotlib.pyplot as plt
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["Normal", "Blackhole"], yticklabels=["Normal", "Blackhole"])
plt.xlabel("Predicted"); plt.ylabel("Actual")
plt.savefig(f"results/plots/confusion_matrix_{name}.png", dpi=150, bbox_inches="tight")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Random row `train_test_split` for IDS datasets | Scenario/seed-level holdout (this phase, D-01) | Locked in project decisions | Eliminates autocorrelation-inflated scores (AGENTS.md rule 4) |
| SMOTE for rare-attack classes | `class_weight='balanced'` cost-sensitive learning | D-05 locked | No synthetic points; probe shows it suffices at 1.4-1.7% rarity |
| `sklearn.metrics.plot_confusion_matrix` | Removed from sklearn; use seaborn heatmap on `confusion_matrix` | long since | All custom plot code must use heatmap pattern above |
| accuracy-only reporting | full security metric set (D-06/D-13, AGENTS.md rule 6) | Locked | metrics.csv schema below |
| pickle/protocol defaults | joblib with compress (D-12) [CITED: model_persistence docs] | stable | Deterministic, compact artifacts |

**Deprecated/outdated:**
- `plot_confusion_matrix`, `applymap` (pandas), numpy-2-only APIs — none available here; AGENTS.md documents the pandas 3.x and numpy 1.26 realities.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | "Single composite scenario set" (D-02) means **one attack-configured run per seed** (onset t=100s ⇒ normal phase 0–100s + attack phase 100–300s), and the Phase 3 dataset is built from those 3 runs only (no separate pure-normal `e1` runs in the dataset) | Architecture Patterns / Pitfall 1 | If the intent was paired runs (e1 + attack-with-onset per seed), dataset has ~2x more (duplicate-ish) normal rows — mostly harmless to metrics but 2x generation time and heavier files; cheap to add later |
| A2 | SVM CV wall-clock of "under 30s" (discretion note) is relaxed to ~2 min for a 6-combo grid @10k subsample (measured 115.5s) — within the agent's-discretion area, refinement not re-decision | Standard Stack / Pitfall 5 | If user insists on <30s: shrink SVM grid to 3 combos or subsample 5k (probe-supported) |
| A3 | Trained `.joblib` artifacts are gitignored (add `ml/models/*.joblib`), `model_metadata.json` committed — models regenerate deterministically from seeds | Pitfall 9 | If user prefers committing models: champion RF ≈ low-MB joblib is committable; SVC candidate may be tens of MB |
| A4 | Attack `start_time` concrete value = 100.0s as given in D-02 example; onset must be < warmup+flow ramp-up margin (flows start 5–30s) so pre-onset attacker windows actually carry traffic | Architecture Patterns | A later onset (e.g. 250s) would starve the attack phase of windows; 100.0s is safe with 300s duration |
| A5 | Pre-onset attacker rows are statistically Normal enough that labeling them Normal does not confuse the classifier (probe: class separation is carried by drop/forward ratios, which are ~Normal pre-onset) | Pitfall 1 | If some pre-onset attacker traffic looks attack-like (it shouldn't — strategy is `None`), labels are still honest; risk negligible |
| A6 | Seed-44 FPR behaves like the probe row-split FPR (RF 0.49% → gate PASS with margin) | Open Questions / champion gate | Probe used row-split; seed-44 is the real gate. If seed-44 FPR > 1% for ALL candidates: escalate (Open Question 2) rather than relax D-06 (one-way gate) |

**Empty-table note:** not empty — six assumptions, all flagged for the planner.

## Open Questions (RESOLVED)

*All three questions were resolved during phase planning (2026-10-27) — each question's recommended answer was adopted and is implemented in the Phase 3 plans cited below. No unresolved question remains.*

1. **Composite dataset composition (A1) — one run per seed vs paired runs?**
   - What we know: D-02's wording ("natural normal and attack phases in a single simulation timeline per seed") literally describes one timeline per seed; discussion log line 30 says the same.
   - What's unclear: whether the user also wants the pure-normal `e1` runs folded into the ML dataset.
   - Recommendation: build Reading A (composite-only); it satisfies D-02 verbatim and halves generation. Adding `e1` rows later is a one-line change.
   - **RESOLVED:** Reading A adopted — composite-only build, one attack-configured composite run per seed, no pure-normal `e1` runs in the ML dataset. Landed in 03-01-PLAN.md `ml/dataset.py` (`build_master`/`build_composite_run` — one composite run per seed over 42/43/44, no e1 scenario in the build path). Adding `e1` rows later remains a one-line change.

2. **Contingency if no candidate passes the FPR gate on seed 44 (A6):**
   - What we know: probe shows RF passes at 0.49% with margin on a row-split; SVM reaches 0.04% when tuned.
   - What's unclear: exact seed-44 behavior until the real split is built.
   - Recommendation: plan a fallback chain — widen RF/DT grid slightly → widen SVM grid → human checkpoint. Never relax D-06 silently (one-way gate).
   - **RESOLVED:** The escalate-don't-relax fallback chain is encoded in 03-03-PLAN.md `select_champion` — no eligible candidate ⇒ `RuntimeError` naming the chain (widen RF/DT grids once → widen SVM grid once → re-run → checkpoint:human-verify); the 0.01 bound is hard-coded (`FPR_GATE`), never CLI-parameterizable, and never silently relaxed (D-06 one-way gate, prohibition P-3).

3. **Trained-model git policy (A3):**
   - What we know: `.gitignore` already excludes `data/`; `ml/models/` currently untracked-new territory; RF champion is small, SVM candidate may be large.
   - Recommendation: ignore `*.joblib`, commit `model_metadata.json` (records test metrics, params, selection rationale per D-12).
   - **RESOLVED:** Adopted as recommended — `ml/models/*.joblib` gitignored (binaries regenerate deterministically from seeds), `ml/models/model_metadata.json` committed. Landed in 03-01-PLAN.md Task 2's `.gitignore` rule (03-01 must_haves artifact row); 03-03-PLAN.md Task 3 re-audits the hygiene fix-forward.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | everything | ✓ | 3.11.8 | — (project-pinned) |
| scikit-learn | ML-01/02/03 | ✓ | 1.8.0 | — |
| pandas | dataset I/O | ✓ | 3.0.2 | — |
| numpy | feature matrices | ✓ | 1.26.4 | — |
| joblib | ML-03 persistence | ✓ | 1.5.3 | — |
| scipy | SVC internals | ✓ | 1.17.1 | — |
| matplotlib / seaborn | D-13 plots | ✓ | 3.10.8 / 0.13.2 | — |
| pytest | D-14 gates | ✓ | 9.0.2 | — |
| simpy | dataset build (runs sims) | ✓ | 4.1.2 | — |
| networkx | dynamic attacker selection | ✓ | 3.6.1 | — |

**Missing dependencies with no fallback:** none — verified by import probe this session.
**Missing dependencies with fallback:** none needed.
**Existing Phase 2 assets the phase reuses:** `data/dataset_sample.csv` is NOT in git (`data/` ignored) — the dataset builder regenerates all runs deterministically from seeds; current `generate_datasets.py` builds seeds `[42, 43]` only [VERIFIED: scripts/generate_datasets.py:23] and must be superseded by the seed-44-capable builder.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 [VERIFIED: runtime probe + `__pycache__` filenames] |
| Config file | none — repo-root invocation, default discovery (`tests/test_*.py`) |
| Quick run command | `python -m pytest tests/test_ml_pipeline.py -v` |
| Full suite command | `python -m pytest tests/ -v` (current baseline: 18 passed in 9.25s [VERIFIED: runtime probe]) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-04 | Train/test seed disjointness + count conservation + master consistency (Pitfall 6 semantics) | unit (data) | `python -m pytest tests/test_ml_pipeline.py -v -k split` | ❌ Wave 0 |
| DATA-04 | train.csv/test.csv match SCHEMA_COLUMNS exactly (10 cols, order); no NaN/inf in X | unit (data) | `python -m pytest tests/test_ml_pipeline.py -v -k schema` | ❌ Wave 0 |
| DATA-04 | Manifest checksums/counts/class-dists match files on disk | unit (data) | `python -m pytest tests/test_ml_pipeline.py -v -k manifest` | ❌ Wave 0 |
| ML-01 | All three Pipelines fit on train.csv; GridSearchCV completes deterministically | unit (smoke) | `python -m pytest tests/test_ml_pipeline.py -v -k train` | ❌ Wave 0 |
| ML-01 | Time-aware labeling: pre-onset attacker window labeled 'Normal' (extends Phase 2 invariance pattern) | unit | `python -m pytest tests/test_feature_pipeline.py -v -k onset` | ❌ Wave 0 |
| ML-02 | metrics.csv contains Accuracy/Precision/Recall/F1/FPR/TN/FP/FN/TP per model; FPR = fp/(fp+tn) sanity | unit (data) | `python -m pytest tests/test_ml_pipeline.py -v -k metrics` | ❌ Wave 0 |
| ML-02 | Champion FPR ≤ 1.0% on seed-44 test set (D-06/D-14-4) | acceptance (artifacts) | `python -m pytest tests/test_ml_pipeline.py -v -k fpr_gate` | ❌ Wave 0 |
| ML-03 | All 4 joblib files + model_metadata.json exist; loaded model predicts identically to in-memory refit (D-14-3); `classes_` assert | acceptance (artifacts) | `python -m pytest tests/test_ml_pipeline.py -v -k persistence` | ❌ Wave 0 |

Artifact-dependent tests (`fpr_gate`, `persistence`): mark `pytest.mark.skipif(not Path("ml/models/best_model.joblib").exists(), reason="run scripts/build_dataset.py + ml/train.py first")` — the plan's execution order produces the artifacts before the gate runs.

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_ml_pipeline.py -v` (+ affected existing test file)
- **Per wave merge:** `python -m pytest tests/ -v` (full suite; budget stays ≈ 1 min with ML tests)
- **Phase gate:** full suite green + champion gate PASS before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_ml_pipeline.py` — all rows of the test map above (Wave 0 task)
- [ ] No conftest.py exists — if tests need shared fixture (e.g., tiny synthetic dataset builder), add `tests/conftest.py`
- [ ] Framework install: none — pytest already present

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1` (config.json [VERIFIED: .planning/config.json:48-49]).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Offline research pipeline; no user accounts, no network listeners |
| V3 Session Management | no | No sessions exist |
| V4 Access Control | no | Local single-user artifacts; OS filesystem permissions suffice |
| V5 Input Validation | **yes** | Dataset schema validation is the security-relevant surface: assert exact SCHEMA_COLUMNS membership/order, numeric dtypes, zero NaN/inf before training (extends tested Phase 2 invariants into `ml/dataset.py` + `tests/test_ml_pipeline.py`) |
| V6 Cryptography | no crypto use; hashing only | SHA-256 via stdlib `hashlib` for manifest checksums (integrity, not secrecy) — never hand-rolled |

### Known Threat Patterns for {offline sklearn pipeline}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Label leakage into X (the IDS analog of tampered evaluation) | Tampering (of results) | Scenario-ground-truth only in `label`; invariance tests (Phase 2 pattern + D-14-2); leakage features forbidden (AGENTS.md rule 5) |
| Split leakage via random row splits | Information Disclosure | Seed-holdout (D-01) + split-integrity tests (Pitfall 6 semantics) |
| Malicious model artifacts (pickle deserialization) | Tampering | Load only artifacts this repo produced (joblib = pickle-backed [CITED: model_persistence docs]); skops noted as safer alternative if policy changes; no external model files |
| Silent metric drift / flaky gates | Repudiation | Full determinism (random_state=42 everywhere, sorted iteration), manifest checksums, never accuracy-only (AGENTS.md rule 6) |

## Sources

### Primary (HIGH confidence)
- Runtime probes this session on installed stack (sklearn 1.8.0, pandas 3.0.2, numpy 1.26.4, joblib 1.5.3, pytest 9.0.2): API patterns, class ordering, confusion orientation, probability-refit parity, gate achievability, and all wall-clock numbers — probed against the real `data/dataset_sample.csv`
- In-repo reads with verbatim quotes: `feature_extraction/extract_features.py:18-29, 189`; `simulator/run_scenario.py:45, 57, 122-146, 319`; `simulator/aodv.py:183-191`; `scripts/generate_datasets.py:8-10, 23`; `scenarios/e2_blackhole_30n.json:71-78`; `.gitignore:1-7`; `.planning/config.json:48-49`; `tests/test_import_boundaries.py:23-40`
- `AGENTS.md` — binding engineering contract (non-negotiables 1–11, environment pins)

### Secondary (MEDIUM confidence — official docs via Context7)
- [CITED: scikit-learn.org/stable/auto_examples/model_selection/plot_multi_metric_evaluation.html] — multi-metric scoring dict + `refit='<name>'` pattern
- [CITED: scikit-learn.org/stable/modules/permutation_importance.html] — `permutation_importance` usage and result fields
- [CITED: scikit-learn.org/stable/model_persistence.html] — joblib/pickle persistence, protocol=5
- [CITED: scikit-learn.org/stable/modules/model_evaluation.html] — confusion-matrix ravel convention
- [CITED: scikit-learn.org GridSearchCV/SVC docs (via Context7)] — int `cv` → StratifiedKFold for classifiers; `SVC(probability=True)` enables `predict_proba` at fit-time cost

### Tertiary (LOW confidence)
- none

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new packages; every planned call signature probed live on the pinned versions
- Architecture: HIGH for data/training/evaluation flow (probe-grounded); MEDIUM for D-02 composite-onset reading (A1 interpretation)
- Pitfalls: HIGH — 3 of 9 verified on real data (SVM gate failure, classes_ ordering, dtype drift), remainder grounded in locked decisions and AGENTS.md
- Data signal: HIGH — real-dataset probe with concrete metric outputs

**Research date:** 2026-10-27
**Valid until:** 2026-11-26 (30 days — pinned local stack; re-probe only if versions change)
