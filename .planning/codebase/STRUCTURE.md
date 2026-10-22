# Codebase Structure

**Analysis Date:** 2026-10-22

> **Status legend.**
> - **[IMPLEMENTED]** — exists in the repo today, verified by reading the file.
> - **[SPECIFIED]** — mandated or directed by `AGENTS.md` / `MANET_IDS_BTech_Execution_Guide.md`, with the intended repo-relative path. **Not yet built.**
>
> **Verified repo contents (2026-10-22):** `AGENTS.md` (177 lines), `MANET_IDS_BTech_Execution_Guide.md` (391 lines), `.gitignore` (22 lines). Git repo on branch `main`, single commit `2246d39`, **no remote configured**. **No source code, no manifest, no CI, no test suite.** Every path below marked [SPECIFIED] is a target location, not an existing file.

---

## Directory Layout

### Current state — what actually exists today

```text
[repo-root]/
├── .git/                          # git repo, branch main, 1 commit, no remote
├── .planning/                     # GSD planning artifacts (untracked, NOT gitignored)
│   └── codebase/                  # STACK.md, INTEGRATIONS.md, ARCHITECTURE.md, STRUCTURE.md
├── .gitignore                     # generated-artifact policy            [IMPLEMENTED]
├── AGENTS.md                      # binding engineering contract        [IMPLEMENTED]
└── MANET_IDS_BTech_Execution_Guide.md  # project specification          [IMPLEMENTED]
```

That is the entire tracked content. There is no `simulator/`, `attacks/`, `scenarios/`, `traces/`, `data/`, `feature_extraction/`, `ml/`, `results/`, `dashboard/`, or `docs/` directory yet.

### Target state — the layout the spec mandates

Prescribed by `AGENTS.md:113-124` and `MANET_IDS_BTech_Execution_Guide.md:158-173`. **Create these directories as you implement them; do not invent alternatives.**

```text
[repo-root]/
├── AGENTS.md                              # binding engineering contract        [IMPLEMENTED]
├── MANET_IDS_BTech_Execution_Guide.md     # project specification              [IMPLEMENTED]
├── .gitignore                             # generated-artifact policy          [IMPLEMENTED]
├── README.md                              # project overview + how to reproduce [SPECIFIED]
├── requirements.txt                       # pinned dependency manifest         [SPECIFIED]
│                                          #   NOTE: does not exist yet — see "Manifest gap"
├── simulator/                             # in-repo Python MANET simulator     [SPECIFIED]
│   ├── __init__.py
│   ├── mobility.py                        # Random Waypoint; mobility_speed
│   ├── radio.py                           # tx range / link availability; neighbor_count
│   ├── aodv.py                            # RREQ/RREP/RERR, seq nos, route table
│   ├── traffic.py                         # CBR/UDP flows
│   ├── metrics.py                         # PDR, throughput, delay, loss, overhead
│   ├── run_scenario.py                    # CLI: --scenario/--seed/--out
│   └── tests/                             # pytest lives inside the owning package
│       ├── __init__.py
│       └── test_aodv.py
├── attacks/                               # blackhole / grayhole strategies     [SPECIFIED]
│   ├── __init__.py                        # registry: attack name -> factory
│   ├── base.py                            # behaviour-flag contract / protocol
│   ├── blackhole.py                       # lying RREP
│   └── grayhole.py                        # probabilistic drop
├── scenarios/                             # one JSON config per experiment      [SPECIFIED]
│   ├── e1_normal_50n.json
│   ├── e2_blackhole_50n.json
│   └── ...
├── traces/                                # generated CSV traces               [SPECIFIED, GITIGNORED]
├── data/                                  # built datasets                     [SPECIFIED, GITIGNORED]
├── feature_extraction/                    # traces -> feature CSV               [SPECIFIED]
│   ├── __init__.py
│   ├── windows.py                         # fixed observation windows
│   ├── features.py                        # the 9 feature computations
│   ├── labels.py                          # join labels from scenarios/*.json
│   └── extract_features.py                # CLI -> data/dataset.csv
├── ml/                                    # training / eval / pipeline + model  [SPECIFIED]
│   ├── __init__.py
│   ├── dataset.py                         # load + clean
│   ├── split.py                           # group-aware splits
│   ├── train.py                           # DT -> RF -> SVM
│   ├── evaluate.py                        # metrics, confusion matrix, figures
│   ├── response.py                        # IDS alert + route exclusion
│   ├── run_evaluation.py                  # IDS-off vs IDS-on comparison driver
│   ├── plots.py                           # matplotlib/seaborn figures
│   └── models/                            # saved .joblib pipelines            [SPECIFIED]
│       └── <name>__<dataset>.joblib
├── results/                               # metrics, plots, per-run records    [SPECIFIED]
│   ├── plots/                             # committable figures                [SPECIFIED, COMMITTED]
│   └── runs/                              # per-run JSON records               [SPECIFIED, GITIGNORED]
├── dashboard/                             # optional viewer                    [SPECIFIED-OPTIONAL]
└── docs/                                  # notes, deviations, experiment log  [SPECIFIED]
    ├── experiment_log.md
    ├── deviations.md
    └── notes/
```

**Do not create** `src/`, `lib/`, `app/`, `core/`, a root-level `tests/`, or a root-level `notebooks/` — they would make the repo diverge from the prescribed layout in `AGENTS.md:113-124`. The one exception, `notebooks/`, is still better placed inside an owning directory (recommend `docs/notebooks/`) so the root stays exactly as specified.

---

## Directory Purposes

### `simulator/` — the in-repo pure-Python MANET simulator
- **Purpose:** Module A of the guide (`MANET_IDS_BTech_Execution_Guide.md:83-92`). Replaces NS-3 entirely. Owns nodes, mobility, radio, AODV, traffic and network metrics.
- **Contains:** one module per concern — `mobility.py`, `radio.py`, `aodv.py`, `traffic.py`, `metrics.py` — plus the CLI runner `run_scenario.py` (`AGENTS.md:54-65`).
- **Key files:** `simulator/aodv.py` (the heart: RREQ/RREP/RERR, sequence numbers, route table with hop count and expiry, and the per-window `route_request_rate` / `route_reply_rate` counters — `AGENTS.md:58-59`), `simulator/run_scenario.py` (the composition root and the only sanctioned import point for `attacks/`).
- **Git:** **commit** — this is the primary source deliverable (`MANET_IDS_BTech_Execution_Guide.md:324-325`).
- **Hard rule:** no module here imports `attacks/` or `ml/` (`AGENTS.md:67-69`).

### `attacks/` — malicious node behaviour strategies
- **Purpose:** Module B of the guide (`MANET_IDS_BTech_Execution_Guide.md:94-100`). Selects malicious nodes and implements attack-specific abnormal behaviour as **node behaviour flags** on the AODV node: a lying reply (blackhole) and probabilistic drop (grayhole) (`AGENTS.md:61-63`).
- **Contains:** `base.py` (the shared behaviour-flag contract), `blackhole.py`, `grayhole.py`, and a small registry in `__init__.py` mapping the scenario's `attack` string to a factory.
- **Key files:** `attacks/blackhole.py`, `attacks/grayhole.py`.
- **Git:** **commit**.
- **Hard rule:** the package must not import `simulator/` — the contract is the flags it sets, not simulator classes. `attacks/` is imported **only** by `simulator/run_scenario.py`.

### `scenarios/` — experiment configuration
- **Purpose:** One JSON config per experiment/scenario (`AGENTS.md:116`). Carries node count, area, mobility model and speed, traffic flows and rates, seed, and optionally the attack type and attacker node id.
- **Contains:** `*.json` only.
- **Key files:** every file in it. Each is the **sole legitimate source of ground-truth labels** for the runs it produced (`AGENTS.md:84-85`).
- **Git:** **commit** (`AGENTS.md:129` — "Commit code, scenario configs, small sample data, plots, and docs").

### `traces/` — raw packet-event traces
- **Purpose:** The immutable record of what happened on the network, and the only thing the ML side sees about the network.
- **Contains:** `*.csv`, one row per packet event, columns beginning `time, src, dst, pkt_id, type, hop_count, dropped_by, ...` (`AGENTS.md:81-83`).
- **Git:** **gitignored** — `.gitignore:2` (`traces/`). "Do not commit huge generated trace files to GitHub" (`MANET_IDS_BTech_Execution_Guide.md:175`).

### `data/` — built datasets
- **Purpose:** The joined, labelled feature table consumed by the ML engine.
- **Contains:** `*.csv` — the 9 features + `label` + the `run_id` group column.
- **Git:** **gitignored** — `.gitignore:3` (`data/`). `AGENTS.md:118` adds "keep samples", but **`.gitignore` has no `!data/samples/` negation** — see "Git policy gap" below.

### `feature_extraction/` — traces → features
- **Purpose:** Module C of the guide (`MANET_IDS_BTech_Execution_Guide.md:102-117`). Converts raw traces into one row per observation window or node, using the fixed 9-feature schema.
- **Contains:** windowing, per-feature computation, label joining from `scenarios/*.json`, and the dataset-building CLI.
- **Key files:** `feature_extraction/features.py` (the schema lives here), `feature_extraction/labels.py` (the only place `scenarios/*.json` is read for ground truth), `feature_extraction/extract_features.py`.
- **Git:** **commit**.

### `ml/` — the ML engine and the IDS response
- **Purpose:** Module D (`MANET_IDS_BTech_Execution_Guide.md:119-126`) and Module E (`:128-133`). Clean → split → train → evaluate → persist; then threshold → alert → isolate → re-evaluate.
- **Contains:** `dataset.py`, `split.py`, `train.py`, `evaluate.py`, `response.py`, `run_evaluation.py`, `plots.py`, and `models/` for the saved pipelines.
- **Key files:** `ml/split.py` (the scenario/seed holdout — `AGENTS.md:142-143`), `ml/response.py` (the IDS response logic), `ml/run_evaluation.py` (the IDS-off vs IDS-on driver), `ml/models/*.joblib` (model **and** preprocessing pipeline — `MANET_IDS_BTech_Execution_Guide.md:126-127,329`).
- **Git:** **commit the code.** The model binary is a stated deliverable (`:329`) — decide and record whether the `.joblib` is committed or archived alongside the report.
- **Hard rule — the layer split:** the *model layer* (`ml/dataset.py`, `ml/split.py`, `ml/train.py`, `ml/evaluate.py`) reads only `data/*.csv` and imports nothing from `simulator/` or `attacks/`. Only the *integration module* (`ml/run_evaluation.py`, `ml/response.py`) may import `simulator/`, because the re-evaluation run is by definition a simulation. `simulator/` must never import `ml/`.

### `results/` — metrics, plots and per-run records
- **Purpose:** Where every reported number lives, and where every number can be traced back to.
- **Contains:** `plots/` (committable figures — `MANET_IDS_BTech_Execution_Guide.md:263-270`), `runs/` (per-run JSON records tying a metric set to its config + seed), and comparison tables.
- **Key files:** `results/plots/*.png`, `results/runs/<run_id>.json`.
- **Git:** **bulk ignored, plots committed** — `.gitignore:5-7`:
  ```gitignore
  results/*
  !results/plots/
  ```
  The `!results/plots/` negation re-includes the `plots/` directory and, because `results/*` matches only one path level, everything under `results/plots/` is committable. `results/runs/` and any other subdirectory stays ignored.

### `dashboard/` — optional viewer
- **Purpose:** A lightweight results viewer. **Phase 5 only** (`MANET_IDS_BTech_Execution_Guide.md:66`).
- **Contains:** a local web app reading `results/`.
- **Git:** **commit** the source.
- **Hard rule:** do not build it before the acceptance chain works end to end (`AGENTS.md:166-167`). It binds to `127.0.0.1` and has no auth.

### `docs/` — notes, deviations, experiment log
- **Purpose:** The narrative record. `AGENTS.md:123` — "notes, deviations, experiment log".
- **Contains:** `docs/experiment_log.md` (what was run, with which config and seed, and what came out), `docs/deviations.md` (where the implementation departs from the guide and why), `docs/notes/` (analysis notebooks and one-off write-ups).
- **Key files:** `docs/experiment_log.md` is the single place that maps a headline number in the report to the run that produced it (`AGENTS.md:151`).
- **Git:** **commit** (`AGENTS.md:129`).

### `results/plots/` — figures (the only committable generated output)
- **Purpose:** Confusion matrix per classifier, precision/recall/F1 comparison bars, PDR vs. number of malicious nodes, throughput vs. attack intensity, end-to-end delay with IDS OFF vs ON, detection rate vs. mobility speed (`MANET_IDS_BTech_Execution_Guide.md:263-270`).
- **Git:** **commit** (`.gitignore:7`).

---

## Key File Locations

**Entry Points:**
- `simulator/run_scenario.py` — the primary CLI. `--scenario <json> --seed <int> --out <dir>` (`AGENTS.md:65`). The composition root; the only sanctioned importer of `attacks/`. **Invoke as a module:** `python -m simulator.run_scenario ...` — the file-path form double-imports modules and creates two copies of the same dataclass (see `.planning/codebase/CONVENTIONS.md`).
- `feature_extraction/extract_features.py` — dataset builder CLI. **[SPECIFIED — filename recommended; the spec fixes the directory, not the file name]**
- `ml/train.py` — training CLI (Decision Tree → Random Forest → SVM). **[SPECIFIED — filename recommended]**
- `ml/evaluate.py` — metrics, confusion matrix, comparison table, figures. **[SPECIFIED — filename recommended]**
- `ml/response.py` + `ml/run_evaluation.py` — IDS threshold → alert → isolation → IDS-off/IDS-on comparison. **[SPECIFIED — location recommended]**
- `dashboard/` — optional local viewer, Phase 5. **[SPECIFIED-OPTIONAL]**

**Configuration:**
- `scenarios/*.json` — the authoritative configuration **and** the ground-truth label source (`AGENTS.md:84-85,116`). One file per experiment.
- `requirements.txt` — pinned dependency manifest. **[SPECIFIED — does not exist yet.]**
- `.gitignore` — the generated-artifact policy (`AGENTS.md:126-127`).

**Core Logic:**
- `simulator/aodv.py` — RREQ/RREP/RERR, sequence numbers, route table with hop count and expiry; per-window `route_request_rate` / `route_reply_rate` (`AGENTS.md:58-59`).
- `simulator/metrics.py` — PDR, throughput, end-to-end delay, packet loss, routing overhead (`AGENTS.md:64`).
- `simulator/mobility.py` — Random Waypoint; source of `mobility_speed` (`AGENTS.md:56`).
- `simulator/radio.py` — transmission range / link availability; source of `neighbor_count` (`AGENTS.md:57`).
- `simulator/traffic.py` — CBR/UDP flows: source–dest pairs, packet rate, payload size (`AGENTS.md:60`).
- `attacks/blackhole.py`, `attacks/grayhole.py` — the node behaviour flags (`AGENTS.md:61-63`).
- `feature_extraction/features.py` — the 9-feature schema (`MANET_IDS_BTech_Execution_Guide.md:104-117`).
- `feature_extraction/labels.py` — the only reader of `scenarios/*.json` for ground truth.
- `ml/split.py` — group-aware splitting (`AGENTS.md:142-143`).
- `ml/response.py` — the detection-threshold and route-exclusion logic (`MANET_IDS_BTech_Execution_Guide.md:129-133`).

**Testing:**
- `simulator/tests/` — pytest for the engine. **[SPECIFIED — no test suite exists today.]**
- `attacks/tests/` — pytest for the behaviour flags.
- `feature_extraction/tests/` — pytest for windowing and the schema.
- `ml/tests/` — pytest for splitting, training and the response loop.
- **Rule:** tests live **inside the owning package**, not in a root-level `tests/`. A root `tests/` directory would break the prescribed layout (`AGENTS.md:113-124`) and is explicitly flagged as a thing not to invent in the stack analysis.
- **Recorded tension:** `AGENTS.md:113-124` does not list a `tests/` directory, but a test suite is required. The per-package choice (`simulator/tests/`, `attacks/tests/`, `feature_extraction/tests/`, `ml/tests/`) is the agreed answer and **must be written into `AGENTS.md` in the same commit** that first creates it (`AGENTS.md:14-16`). See also `.planning/codebase/CONVENTIONS.md` § Import Organization.
- **Rule:** the highest-value test in this project is the **determinism test** — same scenario + same seed ⇒ byte-identical trace (`AGENTS.md:72-74`). Second highest is the **baseline-equals-clean-simulation test** — a run with no attack must be indistinguishable from a run built by a code path that knows nothing about attacks.

**Documentation:**
- `AGENTS.md` — binding engineering contract. Wins on engineering rules.
- `MANET_IDS_BTech_Execution_Guide.md` — project specification. Wins on project scope.
- `docs/experiment_log.md` — the run-by-run narrative.
- `docs/deviations.md` — departures from the guide, with reasons.
- `README.md` — **[SPECIFIED]** how to reproduce the acceptance chain on demand (`MANET_IDS_BTech_Execution_Guide.md:379`).

---

## Naming Conventions

**Files:**
- **Python modules:** `snake_case.py` — `mobility.py`, `radio.py`, `aodv.py`, `traffic.py`, `metrics.py`, `run_scenario.py`, `blackhole.py`, `grayhole.py`, `extract_features.py`, `train.py`, `evaluate.py`, `response.py`, `run_evaluation.py`. This follows PEP 8 and matches the names already used in the spec (`AGENTS.md:56-65`).
- **Tests:** `test_<subject>.py` with `test_<behaviour>()` functions, e.g. `simulator/tests/test_aodv.py` → `test_rreq_increases_request_rate()`. Name the test after the behaviour, not the implementation.
- **Scenario configs:** `e<n>_<experiment>_<variant>.json`, using the guide's experiment IDs (`MANET_IDS_BTech_Execution_Guide.md:244-253`):
  - `e1_normal_50n.json`
  - `e2_blackhole_50n.json`
  - `e4_mobility_high.json`
  - `e6_grayhole_drop30.json`
  - `e8_unseen_seed.json`
  The `e<n>_` prefix makes the experiment matrix greppable and keeps the mapping to the guide's table visible in the file tree.
- **Traces:** `<run_id>.csv`, where **`run_id = "<scenario_stem>__s<seed>"`** — e.g. `traces/e1_normal_50n__s1.csv`. Double underscore separates the scenario from the seed so the id can be split back apart mechanically. This single convention satisfies traceability at every stage.
- **Datasets:** `data/<name>.csv` — `data/dataset.csv` for the canonical build, `data/<name>_v2.csv` for a schema revision (regenerate rather than patch).
- **Model artifacts:** `ml/models/<model_name>__<dataset_stem>.joblib` — e.g. `ml/models/random_forest__dataset.joblib`. Model name and dataset stem in the filename so an artifact is never ambiguous about what produced it.
- **Figures:** `results/plots/<figure_slug>.png` — `confusion_matrix_random_forest.png`, `pdr_vs_malicious_nodes.png`, `delay_ids_off_vs_on.png`. Lowercase, underscores, no spaces, no dates in the name (the run id goes in the figure title or caption).
- **Run records:** `results/runs/<run_id>.json` — the same `run_id` as the trace. This is the join key between a number in the report and the run that produced it.

**Directories:**
- `snake_case` throughout: `simulator/`, `attacks/`, `scenarios/`, `traces/`, `data/`, `feature_extraction/`, `ml/`, `results/`, `dashboard/`, `docs/`. `feature_extraction/` is the only multi-word directory and its name is fixed by the spec — do not "fix" it to `features/` or `feature_extractor/`.

**Python identifiers (PEP 8):**
- Functions and variables: `snake_case` — `compute_pdR` is wrong; use `compute_pdr`.
- Classes: `PascalCase` — `AodvNode`, `RadioModel`, `RandomWaypointMobility`, `BlackholeBehaviour`.
- Constants: `UPPER_SNAKE_CASE` — `DEFAULT_WINDOW_SECONDS`, `TRACE_COLUMNS`.
- Private helpers: leading underscore — `_route_lookup()`.
- Note the one domain exception: the feature column `route_request_rate` and `route_reply_rate` are snake_case, and the packet type codes in the trace (`rreq`, `rrep`, `rerr`, `data`) are **lowercase**, because they are data values consumed by `feature_extraction/`, not Python identifiers.

**Feature columns and labels:**
- Feature columns are exactly the 9 names in the guide's schema table (`MANET_IDS_BTech_Execution_Guide.md:104-117`): `packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`, `neighbor_count`, `mobility_speed`. Do not rename, re-spell (`neighbour_count`), or reorder them — the dataset, the saved pipeline, and the report all depend on these exact strings.
- The `label` column values are Title Case: `Normal`, `Blackhole`, `Grayhole` (`MANET_IDS_BTech_Execution_Guide.md:117`).
- The group column for scenario/seed holdout: `run_id` (the convention above). It is **not** part of the feature set — exclude it from the model input matrix, use it only as the split key.

**Trace columns:**
- Fixed and stable: `time, src, dst, pkt_id, type, hop_count, dropped_by, ...` (`AGENTS.md:81-83`). `feature_extraction/` and every notebook depend on this set. If a column must be added, add it at the end, regenerate all traces, and note the schema change in `docs/deviations.md`.

**Import ordering (PEP 8 / isort convention, in absence of a linter):**
1. stdlib
2. third-party (`simpy`, `networkx`, `numpy`, `pandas`, `sklearn`, `joblib`, `matplotlib`, `seaborn`)
3. first-party (`simulator`, `attacks`, `feature_extraction`, `ml`)

Within each group, alphabetical. There is no linter configured in the repo, so this is a convention to follow by hand, not a check that will catch violations.

---

## Where to Add New Code

This is the section a future `/gsd-execute-phase` run will consult first. **Follow it exactly — the layout is prescribed by `AGENTS.md:113-124` and the guide's structure (`MANET_IDS_BTech_Execution_Guide.md:158-173`).**

### New simulator module (a new network subsystem — energy model, antenna, a new metric)
- **Put it in:** `simulator/<name>.py`
- **Rules:** must not import `attacks/` or `ml/`; must take the seeded `random.Random` instance as an argument rather than creating its own; must emit trace rows rather than writing files; must preserve the trace column set.
- **Register it in:** `simulator/run_scenario.py`, so the composition root stays the only wiring point.
- **Place it in the DAG correctly:** `mobility → radio → aodv → traffic → metrics` (see ARCHITECTURE.md, "Intra-package dependency order").

### New attack (a new malicious behaviour)
- **Put it in:** `attacks/<name>.py`, and add its factory to the registry in `attacks/__init__.py`.
- **Rules:** it must express itself as **node behaviour flags**, not as a branch inside the routing protocol (`AGENTS.md:61-63`); it must not import `simulator/`; it must not write a field into the trace that reveals itself.
- **Add a scenario** to exercise it: `scenarios/e<n>_<name>_*.json`.
- **Order discipline:** Blackhole → Grayhole → flooding/DoS only if the first two are stable (`AGENTS.md:157`). Do not add a fourth attack before the first three work.

### New scenario configuration (a new experiment)
- **Put it in:** `scenarios/e<n>_<experiment>_<variant>.json`
- **Rules:** valid JSON; one file per experiment; it is the source of truth for the run *and* the labels, so it must be committed; keep the schema identical across files so `feature_extraction/labels.py` can read them uniformly.
- **Never** put a scenario's seed inside the file and also pass `--seed` on the command line with a different value — pick one owner. The CLI flag is the spec'd surface (`AGENTS.md:65`); the file's `seed` field, if present, should be the default the runner falls back to.

### New feature (a new column in the dataset)
- **Put it in:** `feature_extraction/features.py` (the computation) and register it in the column list there.
- **Rules:** it must be derivable **from trace rows only** — never from the attack config, never from a node flag (`AGENTS.md:83,145-146`). Add the column to the dataset schema doc in `docs/`.
- **Regenerate** `data/dataset.csv` and retrain; do not hand-patch a CSV.

### New ML model
- **Put it in:** `ml/` — either a new module `ml/<name>.py` (e.g. `ml/svm_baseline.py`) or a branch in `ml/train.py`, and register it in the baseline-comparison loop so it is evaluated under the **same** train/test protocol as the others (`MANET_IDS_BTech_Execution_Guide.md:215-216`). **Note:** `ml/models/` holds saved `.joblib` artifacts, not Python source — do not put a module there.
- **Rules:** it must be wrapped in a `sklearn.pipeline.Pipeline` so the preprocessing travels with it; it must be evaluated with the full metric set (precision, recall, F1, FPR, confusion matrix) — never accuracy alone (`AGENTS.md:148-149`); it must use the group-aware split, not a random row split.
- **Order:** Decision Tree → Random Forest → SVM/XGBoost. **Tune only after a baseline exists** (`MANET_IDS_BTech_Execution_Guide.md:126`). XGBoost and ensembles are stretch features — only after the core works (`MANET_IDS_BTech_Execution_Guide.md:70`).

### New test
- **Put it in:** `<owning_package>/tests/test_<subject>.py` — e.g. `simulator/tests/test_aodv.py`, `attacks/tests/test_blackhole.py`, `feature_extraction/tests/test_features.py`, `ml/tests/test_split.py`.
- **Do NOT create a root-level `tests/`** — it would diverge from the prescribed layout.
- **Highest-value tests to write first:** (1) determinism — same scenario + seed ⇒ byte-identical trace; (2) baseline purity — a run with no attack behaves identically to a run through a code path that knows nothing about attacks; (3) leakage guard — assert the feature table contains no column derived from the attack config; (4) group split — assert no `run_id` appears in both train and test.

### New figure / plot
- **Put it in:** `ml/plots.py` (the figure code), writing to `results/plots/<figure_slug>.png`. Set `matplotlib.use("Agg")` before importing `pyplot` so the script runs headless.

### New run record / result artifact
- **Put it in:** `results/runs/<run_id>.json` — gitignored, consistent with `results/*` in `.gitignore:6`. The record must carry the scenario path, the seed, the metric set and a timestamp (`AGENTS.md:151`).

### New documentation, note, or deviation
- **Put it in:** `docs/` — `docs/experiment_log.md` for run records, `docs/deviations.md` for departures from the guide, `docs/notes/` for one-off analysis and notebooks.
- **Also update:** `AGENTS.md` and `MANET_IDS_BTech_Execution_Guide.md` in the **same commit** if the change is architectural (see the sync rule below).

### New dashboard view
- **Put it in:** `dashboard/` — and only after the acceptance chain works end to end (`AGENTS.md:166-167`).

### New dependency
- **Put it in:** `requirements.txt` at the repo root, pinned with `==` (not `>=`).
- **Also update:** `AGENTS.md` (its environment section, `AGENTS.md:89-96`) **and** `MANET_IDS_BTech_Execution_Guide.md` (its environment table, `:139-147`) in the same commit — the two documents list the environment independently and they must not drift.
- **Before adding one:** check whether the stdlib or an already-installed package does the job. The project rule is the smallest change that solves the problem.

---

## Special Directories

### `traces/`
- **Purpose:** Generated packet-event traces.
- **Generated:** Yes — every run rewrites it.
- **Committed:** No — `.gitignore:2`.
- **Regenerate by:** `python -m simulator.run_scenario --scenario <json> --seed <n> --out traces/`

### `data/`
- **Purpose:** Built datasets (feature tables).
- **Generated:** Yes.
- **Committed:** No — `.gitignore:3`.
- **Regenerate by:** `python -m feature_extraction.extract_features --traces traces/ --scenarios scenarios/ --out data/dataset.csv`

### `results/`
- **Purpose:** Metrics, comparison tables, per-run records, figures.
- **Generated:** Yes — mostly.
- **Committed:** **Partially.** `results/*` is ignored (`.gitignore:6`); `results/plots/` is re-included (`.gitignore:7`), so **figures are committed and everything else is not**.
- **Regenerate by:** re-running the experiments.

### `ml/models/`
- **Purpose:** Saved model + preprocessing pipeline artifacts (`.joblib`).
- **Generated:** Yes — by `ml/train.py`.
- **Committed:** **Decide and record.** The model is a stated deliverable (`MANET_IDS_BTech_Execution_Guide.md:329`) and the demo needs it, so committing it is the pragmatic choice; note the decision in `docs/`. It is *not* covered by any `.gitignore` rule today, so it will be committed by default.

### `docs/`
- **Purpose:** Notes, deviations, experiment log, analysis notebooks.
- **Generated:** No — hand-written.
- **Committed:** Yes.

### `dashboard/`
- **Purpose:** Optional local results viewer.
- **Generated:** No.
- **Committed:** Yes.

### `.planning/`
- **Purpose:** GSD planning artifacts — the project's decision and plan memory. Currently holds `codebase/STACK.md`, `codebase/INTEGRATIONS.md`, `codebase/ARCHITECTURE.md`, `codebase/STRUCTURE.md`.
- **Generated:** Partly — produced by GSD tooling, hand-edited over time.
- **Committed:** **Undecided.** `git status` currently shows `?? .planning/` — the directory is untracked and **not** listed in `.gitignore`. *Recommendation:* commit it. It contains no secrets, and it is the only durable record of why the architecture looks the way it does. If the team prefers it local, add `.planning/` to `.gitignore` in the same commit that creates it, and say so in `docs/deviations.md`.

### `simulator/tests/`, `attacks/tests/`, `feature_extraction/tests/`, `ml/tests/`
- **Purpose:** pytest suites, one per owning package.
- **Generated:** No.
- **Committed:** Yes. `.gitignore:15` ignores `.pytest_cache/`, so the runner is expected to be pytest.

---

## The documentation-sync rule (a hard project rule)

`AGENTS.md:14-16` and `AGENTS.md:36-37`:

> **Precedence:** where the two conflict, `AGENTS.md` wins on engineering rules and the guide wins on project specification. **Keep both files in sync** — change one, change the other in the same commit. Never leave them disagreeing.

> The guide has been revised for this architecture. When you change the architecture again, update the guide in the same change — never leave the two files disagreeing.

**What this means operationally:**

- These two files are the **only** place the target architecture is written down. There is no `docs/architecture.md` in the prescribed layout — the architecture *is* `AGENTS.md` § "Recommended simulator" plus the guide §3.
- Any change to the directory layout, the module list, the import boundary, the CLI contract, the feature schema, the trace schema, or the dependency set **must** touch both files in the same commit.
- The precedence rule resolves genuine conflicts: `AGENTS.md` decides *how* (engineering rules — determinism, import boundary, no leakage, grouped holdout); the guide decides *what* (project scope — phases, experiment matrix, feature schema, metrics, deliverables).
- The two files currently agree that: the language is Python only; NS-3 is dropped; the platform is Windows-native; `simulator/` must not import `attacks/`; the pipeline shape is `simulator → traces → features → dataset → ML → IDS response → network re-evaluation`; and the target layout is the one in "Target state" above.

---

## Two gaps to close early

### Manifest gap
- **No `requirements.txt` and no `pyproject.toml` exist.** Every dependency version is currently pinned only in prose inside `AGENTS.md:89-96` and the guide's environment table (`MANET_IDS_BTech_Execution_Guide.md:139-147`).
- **Create `requirements.txt` at the repo root before the first simulation run**, with exact `==` pins matching the verified environment: `simpy==4.1.2`, `networkx==3.6.1`, `scikit-learn==1.8.0`, `pandas==3.0.2`, `numpy==1.26.4`, `scipy==1.17.1`, `matplotlib==3.10.8`, `seaborn==0.13.2`. Add `pytest` and `jupyterlab` only when those land.
- **Do not use `>=` pins** — the pandas 3.x / numpy 1.26.x / scikit-learn 1.8.0 behaviour differences are exactly the traps a loose pin would walk into.
- Install with `python -m pip install -r requirements.txt`, never bare `pip` (`AGENTS.md:107`).

### Git policy gap — sample data has no carve-out
- `AGENTS.md:118` says `data/` is "gitignored, **keep samples**", but `.gitignore:3` ignores `data/` wholesale with **no** `!data/samples/` negation, and `traces/` has no sample carve-out either.
- **Two ways to resolve, pick one and record it in `docs/deviations.md`:** (a) add `!data/samples/` (and, if wanted, `!traces/samples/`) to `.gitignore`; or (b) keep small committed samples under `docs/samples/`, which is already committable.
- Option (a) is more discoverable; option (b) touches nothing that is already specified. Either is acceptable — the current state, where samples are silently impossible to commit, is the only unacceptable option.

---

*Structure analysis: 2026-10-22 — derived from `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md`, `.gitignore`, `git log` / `git status` / `git remote -v`, a full recursive directory listing of the repository, and the existing `.planning/codebase/STACK.md` and `.planning/codebase/INTEGRATIONS.md` from the tech mapping pass. No packages were installed and no network or package-manager write commands were run.*
