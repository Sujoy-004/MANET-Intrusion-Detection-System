# Phase 03: Machine Learning Classification Pipeline & Evaluation - Pattern Map

**Mapped:** 2026-10-27
**Files analyzed:** 11 (9 code/config files + 1 artifact + 1 package marker)
**Analogs found:** 11 / 11 (all analogs verified git-tracked via `git ls-files`; `ml/` itself is greenfield — no sklearn code exists in the repo yet)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/build_dataset.py` (new) | script (CLI orchestrator) | batch, file-I/O | `scripts/generate_datasets.py` | exact |
| `ml/dataset.py` (new) | service (dataset builder) | batch, file-I/O (CSV + JSON manifest) | `scripts/generate_datasets.py` (orchestration) + `feature_extraction/extract_features.py:18-29` (schema) | role-match |
| `ml/train.py` (new) | service (training/tuning) | batch, transform | `scripts/generate_datasets.py` (module scaffold only) | no analog for sklearn logic — use RESEARCH.md Patterns 1/5/6 |
| `ml/evaluate.py` (new) | service (evaluator/champion gate) | batch, file-I/O (metrics.csv, plots, report, joblib) | `scripts/verify_gate2_impact.py` + `simulator/metrics.py` | role-match |
| `ml/__init__.py` (new) | package marker | — | `feature_extraction/__init__.py` | exact |
| `tests/test_ml_pipeline.py` (new) | test (acceptance gates) | batch verification | `tests/test_feature_pipeline.py` + `tests/test_gate2_benchmark.py` | exact |
| `scenarios/e3_blackhole_onset_30n.json` (new, template for seeds 42/43/44) | config | — | `scenarios/e2_blackhole_30n.json` | exact |
| `simulator/run_scenario.py` (modify) | orchestrator (simulator core) | event-driven | self — research-verified seams at lines 122-150, 319, 471-481 | exact (self) |
| `feature_extraction/extract_features.py` (modify) | transformer (sliding-window) | streaming/transform over trace rows | self — seam at line 189 + signature lines 32-40 | exact (self) |
| `tests/test_feature_pipeline.py` (modify) | test | batch verification | self — extends `test_anti_leakage_invariance` (lines 71-89) | exact (self) |
| `.gitignore` (modify) | config | — | self — extend lines 5-7 results pattern | exact (self) |
| `ml/models/model_metadata.json` (artifact, runtime-written) | artifact | file-I/O | pattern: `data/dataset_manifest.json` design (D-03) in RESEARCH.md | no analog (artifact) |

## Pattern Assignments

### `scripts/build_dataset.py` (script, batch file-I/O)

**Analog:** `scripts/generate_datasets.py` — exact match: same role (scripts/ CLI running seeded sims → features → CSV) and same data flow.

**Module scaffold + sys.path bootstrap** (generate_datasets.py lines 1-19):
```python
"""Automated end-to-end dataset generation pipeline producing sample training data."""

import json
from pathlib import Path
import sys
from typing import List

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import pandas as pd

from feature_extraction.extract_features import (
    SCHEMA_COLUMNS,
    extract_features_from_trace,
)
from simulator.run_scenario import SimulationRunner, load_scenario
```
Copy this bootstrap verbatim — every new `scripts/*.py` and `ml/*.py` module must handle repo-root sys.path identically for standalone invocation.

**Seeded run loop pattern** (generate_datasets.py lines 41-74):
```python
for seed in seeds:
    # 1. Normal run
    trace_normal = trace_dir / f"e1_normal_seed{seed}.csv"
    print(f"\n[Seed {seed}] Simulating Normal Baseline -> {trace_normal.name} ...")
    runner_norm = SimulationRunner(normal_cfg, seed=seed, out_path=trace_normal)
    runner_norm.run(duration=duration)
    df_norm_trace = pd.read_csv(trace_normal)
    feats_norm = extract_features_from_trace(
        trace_df=df_norm_trace,
        scenario_config=normal_cfg,
        window_size=5.0,
        step_size=1.0,
        warmup=10.0,
    )
    ...
    # 2. Blackhole run — passes the runner-resolved dynamic attacker back to the extractor
    feats_bh = extract_features_from_trace(
        ...,
        attacker_ids=runner_bh.attacker_ids,   # runner owns dynamic attacker selection
    )
```
Key wiring: `SimulationRunner(scenario_config=cfg, seed=seed, out_path=trace)` → `runner.run(duration)` → `pd.read_csv(trace)` → `extract_features_from_trace(..., attacker_ids=runner.attacker_ids)`. For Phase 3 composite onset runs, pass the onset time through to the extractor (see `extract_features.py` assignment below).

**Result summary / dataset write pattern** (generate_datasets.py lines 76-97):
```python
combined_df = pd.concat(all_dfs, ignore_index=True)
...
sample_out_path = out_dir / "dataset_sample.csv"
combined_df.to_csv(sample_out_path, index=False)
...
counts = combined_df["label"].value_counts().to_dict()
print(f"Total samples:     {total_samples}")
print(f"Normal samples:    {normal_cnt} ({100 - bh_pct:.2f}%)")
print(f"Blackhole samples: {bh_cnt} ({bh_pct:.2f}%)")
print(f"Schema columns:    {list(combined_df.columns)}")
print(f"Missing values:    {combined_df.isna().sum().sum()}")
```
Same banner style (`"=" * 80` headers) for the build summary; `build_dataset.py` adds the seed column before concat and splits on it (D-01) instead of writing one flat file.

**Directory creation pattern** (generate_datasets.py lines 29-30):
```python
trace_dir.mkdir(parents=True, exist_ok=True)
out_dir.mkdir(parents=True, exist_ok=True)
```

**CLI entrypoint pattern** (generate_datasets.py lines 102-103; run_scenario.py lines 484-490 for argparse):
```python
if __name__ == "__main__":
    generate_all_datasets()
```
`build_dataset.py` should follow the argparse + `parse_args(args=None)` signature style used in `simulator/run_scenario.py:484-490` and `feature_extraction/extract_features.py:213-223` (testable `args` param).

---

### `ml/dataset.py` (service, batch file-I/O)

**Analog:** `scripts/generate_datasets.py` (orchestration body — see above) + `feature_extraction/extract_features.py` (schema source, below). The manifest is greenfield — use the RESEARCH.md dataset-partitioning example as the spec.

**Schema source — copy verbatim, never redeclare by hand** (extract_features.py lines 18-29):
```python
SCHEMA_COLUMNS = [
    "packet_forward_ratio",
    "packet_drop_ratio",
    "avg_delay",
    "route_request_rate",
    "route_reply_rate",
    "throughput",
    "hop_count",
    "neighbor_count",
    "mobility_speed",
    "label",
]
```
Import `SCHEMA_COLUMNS` from `feature_extraction.extract_features` (as generate_datasets.py:15-18 does); train/test CSVs write exactly these 10 columns in this order; `master.csv` = these 10 + `seed`.

**Ground-truth-from-scenario-config discipline** (extract_features.py lines 62-77) — the same "labels/attacker metadata come from config, never from trace" rule that governs the manifest:
```python
attacker_nodes: Set[int] = set()
if attacker_ids is not None:
    attacker_nodes = set(attacker_ids)
else:
    attack_cfg = scenario_config.get("attack", {})
    if attack_cfg.get("enabled", False):
        attackers_spec = attack_cfg.get("attackers", [])
        ...
```

**Manifest checksum pattern (greenfield — stdlib hashlib, per RESEARCH.md Code Examples):**
```python
# Source: RESEARCH.md "Dataset partitioning with manifest" + stdlib hashlib
# (no repo analog yet; follow the pathlib + json conventions shown in generate_datasets.py)
def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

master = pd.concat(run_frames, ignore_index=True)          # 10 schema cols + 'seed'
train = master[master["seed"].isin((42, 43))][SCHEMA_COLUMNS]   # D-01
test  = master[master["seed"].isin((44,))][SCHEMA_COLUMNS]
# assert len(train) + len(test) == len(master); write manifest with checksums/counts/class-dists
```

---

### `ml/train.py` (service, batch transform — **no repo analog for the sklearn core**)

**Analog for module scaffold only:** `scripts/generate_datasets.py` (sys.path bootstrap lines 8-11, docstring style, `__main__` guard). **All sklearn patterns come from RESEARCH.md** (runtime-probed this session on the installed stack); the repo has zero sklearn code, so do not look for one.

**The three tuned pipelines** (RESEARCH.md "The three tuned pipelines", probe-verified signatures):
```python
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

**Multi-metric GridSearchCV** (RESEARCH.md Pattern 1, probe-verified wall-clock: DT 7.4s / RF 45.7s / SVM 115.5s @10k):
```python
scoring = {
    "f1_blackhole": make_scorer(f1_score, pos_label="Blackhole"),   # D-11 primary
    "f1_macro": "f1_macro",                                          # discretion tracker
    "balanced_accuracy": "balanced_accuracy",                        # discretion tracker
}
grid = GridSearchCV(
    pipeline, param_grid,
    scoring=scoring, refit="f1_blackhole",
    cv=5,  # int cv -> StratifiedKFold for classifiers
    n_jobs=1, return_train_score=False,
)
grid.fit(X_train, y_train)   # train.csv rows ONLY (seeds 42+43); seed 44 never passed
```

**Candidate persistence** (RESEARCH.md "Persistence + parity"):
```python
joblib.dump(pipeline, f"ml/models/{name}.joblib", compress=3)
```

---

### `ml/evaluate.py` (service, batch + file-I/O)

**Analog:** `scripts/verify_gate2_impact.py` — gate-loop + row-collection + pass/fail semantics; `simulator/metrics.py` — structured metric computation and dict return.

**Gate-verification loop pattern** (verify_gate2_impact.py lines 15-21, 35-61):
```python
def run_benchmark(
    base_scenario_path: Path = Path("scenarios/e1_normal_30n.json"),
    atk_scenario_path: Path = Path("scenarios/e2_blackhole_30n.json"),
    seeds: List[int] = [42, 43, 44],
    duration: float = 300.0,
    min_relative_drop: float = 0.25,
) -> Tuple[bool, List[Dict[str, float]]]:
    ...
    results = []
    all_passed = True
    for seed in seeds:
        ...
        results.append({...})
    ...
    return all_passed, results
```
Copy this shape for `evaluate_on_test()`: function taking paths/duration defaults, accumulating per-model result dicts, returning `(all_passed, rows)`. The per-model rows feed `results/metrics.csv` exactly as benchmark rows feed the gate report.

**Structured metric computation pattern** (simulator/metrics.py lines 17-34, 37-60) — named dataclass / dict of computed fields, guard clauses on empty/degenerate input, helper-per-metric:
```python
@dataclass
class NetworkMetrics:
    pdr: float
    throughput_bps: float
    ...
def compute_pdr(data_sent: int, data_received: int) -> float:
    if data_sent <= 0:
        return 0.0
    return float(data_received) / float(data_sent)
```
`ml/evaluate.py` mirrors this: one small helper per metric, guards against division-by-zero, and the confusion-matrix orientation fixed by labels order:
```python
# RESEARCH.md Pattern 2 (probe-verified orientation):
tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=["Normal", "Blackhole"]).ravel()
fpr = fp / (fp + tn)          # D-06 gate: fpr <= 0.01
```

**Exit-code semantics** (verify_gate2_impact.py lines 72-74):
```python
if __name__ == "__main__":
    success, _ = run_benchmark()
    sys.exit(0 if success else 1)
```
`ml/evaluate.py`'s champion gate should follow the same non-zero-exit-on-gate-failure discipline.

**Champion selection with gate + escalation** (RESEARCH.md "Champion selection with the FPR gate"):
```python
eligible = [r for r in rows if r["fpr"] <= 0.01]
if not eligible:
    raise RuntimeError("No candidate satisfies D-06 FPR gate — do NOT silently select; escalate.")
champion = max(eligible, key=lambda r: r["f1_blackhole"])
```

**predict_proba column rule — encode here from day one** (RESEARCH.md Pattern 6, probe-verified):
```python
pos_col = list(pipe.classes_).index("Blackhole")   # 0 for binary string labels!
p_blackhole = pipe.predict_proba(X)[:, pos_col]
```

**Confusion-matrix heatmap** (RESEARCH.md, established repo styling):
```python
import matplotlib
matplotlib.use("Agg")            # headless Windows-safe
import seaborn as sns
import matplotlib.pyplot as plt
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["Normal", "Blackhole"], yticklabels=["Normal", "Blackhole"])
plt.xlabel("Predicted"); plt.ylabel("Actual")
plt.savefig(f"results/plots/confusion_matrix_{name}.png", dpi=150, bbox_inches="tight")
```

---

### `tests/test_ml_pipeline.py` (test, batch verification)

**Analog:** `tests/test_feature_pipeline.py` — structure, fixtures, and anti-leakage invariance style; `tests/test_gate2_benchmark.py` — artifact/gate test that imports a script function.

**Fixture pattern** (test_feature_pipeline.py lines 15-27):
```python
@pytest.fixture(scope="module")
def sample_trace(tmp_path_factory) -> tuple[pd.DataFrame, dict]:
    """Generate a quick 20s simulation trace for feature testing."""
    tmp = tmp_path_factory.mktemp("feat_data")
    trace_path = tmp / "sample_trace.csv"
    scenario_path = Path("scenarios/e2_blackhole_30n.json")
    scenario = load_scenario(scenario_path)
    runner = SimulationRunner(scenario_config=scenario, seed=42, out_path=trace_path)
    runner.run(duration=20.0)
    df = pd.read_csv(trace_path)
    return df, scenario
```
Reuse the `tmp_path_factory` + `scope="module"` pattern for any synthetic tiny dataset fixture (RESEARCH.md Wave 0 note: `tests/conftest.py` does not exist yet — create it only if shared fixtures are needed).

**Schema/NaN assertion style** (test_feature_pipeline.py lines 30-48):
```python
assert list(feats.columns) == SCHEMA_COLUMNS
assert len(feats.columns) == 10
...
numeric_df = feats.iloc[:, :-1]
assert not numeric_df.isna().any().any()
assert np.isfinite(numeric_df.to_numpy(dtype=float)).all()
```
This is the pattern for the D-14 (2) test (9-feature invariance in X). Note Pitfall 7: assert by column names/order and numeric dtypes — never compare to dtype `'object'` (pandas 3.x returns `str`).

**Leakage invariance test to extend for onset labeling** (test_feature_pipeline.py lines 71-89):
```python
def test_anti_leakage_invariance(sample_trace):
    # Run 1: Attacker is node 14
    scen_1 = dict(scenario)
    scen_1["attack"] = {"enabled": True, "type": "Blackhole", "attackers": [14]}
    df1 = extract_features_from_trace(trace_df, scen_1, ...)
    # Run 2: Attacker is node 20
    scen_2 = dict(scenario)
    scen_2["attack"] = {"enabled": True, "type": "Blackhole", "attackers": [20]}
    df2 = extract_features_from_trace(trace_df, scen_2, ...)
    assert df1.iloc[:, :-1].equals(df2.iloc[:, :-1]), "Feature matrix X changed when attack label changed!..."
    assert not df1["label"].equals(df2["label"]), "Labels did not change as expected"
```
The new onset test follows this exact shape: two scenario configs differing only in `attack.start_time`, asserting X columns identical while labels differ pre/post onset.

**Artifact-gate test style** (test_gate2_benchmark.py lines 1-23):
```python
from scripts.verify_gate2_impact import run_benchmark

def test_gate2_quantitative_impact():
    passed, results = run_benchmark(...)
    assert passed, f"Gate 2 benchmark failed: {results}"
    assert results[0]["passed"] is True
```
D-14 artifact tests (`fpr_gate`, `persistence`) follow this import-the-function style, plus the skipif guard from RESEARCH.md:
```python
@pytest.mark.skipif(not Path("ml/models/best_model.joblib").exists(), reason="run scripts/build_dataset.py + ml/train.py first")
```
**Pitfall 6 (do not copy wrongly):** the split-integrity test must assert provenance (`set(train_seeds) ⊆ {42,43}`, `set(test_seeds) == {44}`, `len(train)+len(test) == len(master)`, manifest checksums) — **never** feature-vector equality across splits (neutral rows recur legitimately and will flake).

---

### `scenarios/e3_blackhole_onset_30n.json` (config)

**Analog:** `scenarios/e2_blackhole_30n.json` — exact: copy the full structure and add only the onset key.

**Full template** (e2_blackhole_30n.json lines 1-10, 71-78):
```json
{
  "scenario_id": "e2_blackhole_30n",
  "description": "30-node MANET scenario with dynamic Blackhole attacker",
  "nodes": 30,
  "area": [1000, 1000],
  "duration": 300.0,
  "mobility": { "model": "random_waypoint", "speed_range": [1.0, 10.0], "pause_time": 5.0, "boundary": "wrap" },
  "radio": { "range": 250, "loss_probability": 0.01 },
  "traffic": { "protocol": "CBR_UDP", "packet_size": 512 },
  "flows": [ { "flow_id": 0, "src": 0, "dst": 15, "rate_pps": 4.0, "start_time": 5.0, "duration": 280.0 }, ... ],
  "attack": {
    "enabled": true,
    "type": "Blackhole",
    "attackers": "dynamic",
    "seq_offset": 1000,
    "spoofed_hops": 1
  }
}
```
Phase 3 adds `attack.start_time` (e.g. `100.0`) inside the existing `attack` block — note `flows[].start_time` already uses this key name for flow start, so keep `attack.start_time` namespaced under `attack` (do not add a top-level `start_time`). Onset must be < warmup+flow ramp-up margin (flows start 5-30s; onset 100.0s is safe per RESEARCH.md A4).

---

### `simulator/run_scenario.py` (modify — orchestrator, event-driven)

**Analog:** self. The onset feature must slot into the **existing attack-wiring block**, not restructure anything. Research-verified seams:

**Attack wiring — the eager assignment to gate behind `start_time`** (run_scenario.py lines 122-150):
```python
# Attack configuration wiring
self.attacker_ids = []
attack_cfg = self.scenario.get("attack", {})
if attack_cfg.get("enabled", False):
    attack_type = attack_cfg.get("type", "Blackhole")
    attackers_spec = attack_cfg.get("attackers", "dynamic")
    if attackers_spec == "dynamic" or attackers_spec == [] or attackers_spec is None:
        chosen_id = self.select_dynamic_attacker(self.scenario.get("flows", []))
        attackers_list = [chosen_id]
    elif isinstance(attackers_spec, list):
        attackers_list = attackers_spec
    elif isinstance(attackers_spec, int):
        attackers_list = [attackers_spec]
    else:
        attackers_list = []

    self.attacker_ids = attackers_list
    seq_offset = int(attack_cfg.get("seq_offset", 1000))
    spoofed_hops = int(attack_cfg.get("spoofed_hops", 1))
    for aid in self.attacker_ids:
        if aid in self.aodv_nodes:
            strategy = create_attack_strategy(attack_type, seq_offset=seq_offset, spoofed_hops=spoofed_hops)
            self.aodv_nodes[aid].attack_behavior = strategy
            if attack_type.lower() == "blackhole":
                self.aodv_nodes[aid].is_blackhole = True

# Start periodic processes
self.env.process(self._periodic_topology_refresh())
self.env.process(self._periodic_status_logger())
```
**Implementation shape (RESEARCH.md Pattern 3):** when `attack_cfg.get("start_time")` is present, keep attacker selection/`self.attacker_ids` intact but replace the eager strategy assignment with a scheduled SimPy process (registered in this block, alongside the two `env.process(...)` calls at lines 149-150):
```python
def _delayed_attack_activation(self, aid, strategy, start_time, attack_type):
    yield self.env.timeout(start_time)
    self.aodv_nodes[aid].attack_behavior = strategy
    if attack_type.lower() == "blackhole":
        self.aodv_nodes[aid].is_blackhole = True
# if attack_cfg.get("start_time") is None → eager (backward compat);
# else env.process(self._delayed_attack_activation(...))
```
Zero changes to `aodv.py` or `attacks/` — the duck-typed hooks carry it. Before activation `attack_behavior is None` ⇒ perfectly normal node.

**Hook sites the swap relies on (must remain untouched):** run_scenario.py line 319 (data-drop hook):
```python
if aodv_node.attack_behavior is not None and hasattr(aodv_node.attack_behavior, "should_drop_data") and aodv_node.attack_behavior.should_drop_data(pkt.src, pkt.dst, pkt.pkt_id):
```
and simulator/aodv.py lines 183-191 (spoofed-RREP hook):
```python
if (
    self.attack_behavior is not None
    and hasattr(self.attack_behavior, "get_spoofed_rrep_params")
    and self.node_id != rreq.dest
    and rreq.originator != self.node_id
):
    spoofed_seq, spoofed_hops = self.attack_behavior.get_spoofed_rrep_params(rreq.dest, rreq.dest_seq)
```

**Determinism conventions to preserve:** `self.rng = random.Random(seed)` (line 49); periodic loggers iterate `sorted(self.nodes.keys())` (line 157) — any new process/loop must keep sorted iteration (AGENTS.md known-failure).

---

### `feature_extraction/extract_features.py` (modify — transformer, streaming/transform)

**Analog:** self. One surgical extension, backward-compatible.

**Function signature to extend** (extract_features.py lines 32-40):
```python
def extract_features_from_trace(
    trace_df: pd.DataFrame,
    scenario_config: Dict[str, Any],
    window_size: float = 5.0,
    step_size: float = 1.0,
    warmup: float = 10.0,
    min_packets: int = 0,
    attacker_ids: Optional[List[int]] = None,
) -> pd.DataFrame:
```
Add `attack_start_time: Optional[float] = None` — `None` ⇒ current identity behavior (Phase 2 tests + Gate 2 scripts stay green).

**Label line to make time-aware** (extract_features.py line 189 — the only line whose behavior changes):
```python
# 10: Ground truth label strictly from scenario metadata
label = "Blackhole" if nid in attacker_nodes else "Normal"
```
becomes (RESEARCH.md Pattern 4):
```python
label = "Blackhole" if (nid in attacker_nodes and t >= attack_start_time) else "Normal"
```
where `t` is the current window time from `time_steps` (line 100). The attacker set itself still comes from config (lines 62-77 above); `start_time` is scenario ground-truth metadata feeding only the label column — X stays untouched, preserving `test_anti_leakage_invariance`.

**CLI plumbing precedent** (extract_features.py lines 213-223): if `start_time` is exposed via CLI, follow the existing `--warmup`-style argument pattern (`type=float, default=...`).

---

### `.gitignore` (modify — config)

**Analog:** self — extend the existing comment-annotated blocks (lines 1-7):
```gitignore
# Generated simulation output — reproducible from a seed, never commit (guide §4)
traces/
data/

# Experiment output: keep plots, drop bulk per-run records
results/*
!results/plots/
```
Add `ml/models/*.joblib` (ignore binary artifacts — regenerate deterministically from seeds) while `ml/models/model_metadata.json` remains committable; keep `data/` ignored — the manifest regenerates with seeds (RESEARCH.md Pitfall 9 / A3). Note `results/*` + `!results/plots/` means new subdirs like `results/plots/` are already handled.

---

## Shared Patterns

### Repo-root sys.path bootstrap
**Source:** `scripts/generate_datasets.py:8-11` (also `scripts/verify_gate2_impact.py:7-10`)
**Apply to:** `scripts/build_dataset.py`, `ml/dataset.py`, `ml/train.py`, `ml/evaluate.py`, `tests/test_ml_pipeline.py`
```python
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
```

### Determinism (seeds + sorted iteration)
**Source:** `simulator/run_scenario.py:49` (`self.rng = random.Random(seed)`), `:157` (`sorted(self.nodes.keys())`)
**Apply to:** every estimator/subsampler in `ml/train.py` (`random_state=42`), `ml/dataset.py` loops, any set iteration feeding training/eval order (sort node/seed IDs)
```python
self.rng = random.Random(seed)
for nid in sorted(self.nodes.keys()):
```

### Ground truth from scenario config only (anti-leakage)
**Source:** `feature_extraction/extract_features.py:62-77` (attacker set), `:188-189` (label comment discipline)
**Apply to:** time-aware labeling in the extractor, `ml/dataset.py` manifest metadata, `tests/test_ml_pipeline.py` leakage assertions. Labels derive from scenario metadata, never from trace values or anything in X.

### Gate verification with row collection + pass/fail + non-zero exit
**Source:** `scripts/verify_gate2_impact.py:15-21, 35-61, 72-74`
**Apply to:** `ml/evaluate.py` (champion gate, metrics rows) and D-14 artifact tests
```python
results.append({...})
...
return all_passed, results
...
sys.exit(0 if success else 1)
```

### Progress/summary banner printing
**Source:** `scripts/generate_datasets.py:37-39, 88-97`; `scripts/verify_gate2_impact.py:29-33`
**Apply to:** `scripts/build_dataset.py` output and `ml/evaluate.py` report generation
```python
print("=" * 80)
print("DATASET GENERATION PIPELINE")
print("=" * 80)
```

### Pathlib Windows-native paths + explicit mkdir
**Source:** `scripts/generate_datasets.py:4, 29-30`; `simulator/run_scenario.py:48`
**Apply to:** all new modules (`data/`, `ml/models/`, `results/`, `results/plots/`)
```python
out_dir.mkdir(parents=True, exist_ok=True)
self.out_path = Path(out_path) if out_path else None
```

### Docstring + testable-CLI conventions
**Source:** every existing module (module docstring line 1; `parse_args(args: Optional[List[str]] = None)` in `run_scenario.py:484-490`, `extract_features.py:213-223`)
**Apply to:** all new `ml/*.py` and `scripts/build_dataset.py` — module docstring states the pipeline purpose; CLI functions accept an injectable `args` list for tests.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `ml/train.py` (sklearn core) | service | batch transform | Zero sklearn code exists in the repo (no prior ML module). Use RESEARCH.md Patterns 1/5/6 + Code Examples — all runtime-probed on the installed stack this session. Scaffold conventions come from `scripts/generate_datasets.py`. |
| `ml/dataset.py` manifest (checksums/JSON) | service | file-I/O | No JSON/checksum manifest exists anywhere in the codebase. Stdlib `hashlib.sha256` + `json.dump`, spec'd in RESEARCH.md (D-03). |
| `ml/evaluate.py` (GridSearchCV result handling, permutation importance, champion gate) | service | batch | No sklearn.metrics or sklearn.inspection usage exists yet. Follow RESEARCH.md Patterns 2/6 and the gate-loop analog from `verify_gate2_impact.py`. |
| `ml/models/model_metadata.json` | artifact | file-I/O | Runtime-generated artifact; structure defined by D-12 in RESEARCH.md, not by any existing file. |

## Metadata

**Analog search scope:** `scripts/`, `ml/` (confirmed absent), `simulator/`, `feature_extraction/`, `tests/`, `scenarios/`, repo root
**Files scanned:** 14 (10 Python modules, 2 scenario JSONs, 1 `.gitignore`, glob for skills/`ml/` layout)
**Tracked-source gate:** all 9 named analog paths verified git-tracked via `git ls-files` (non-empty output); no gitignored mirrors named.
**Pattern extraction date:** 2026-10-27
