# Coding Conventions

**Analysis Date:** 2026-10-22

> **Status legend.** Every entry below is tagged.
> - **[IMPLEMENTED]** — exists in the repo today, verified by reading the file.
> - **[SPECIFIED]** — mandated or directed by `AGENTS.md` and/or `MANET_IDS_BTech_Execution_Guide.md`, with the intended repo-relative path. **Not yet built.**
>
> **Verified repo contents (2026-10-22):** only `AGENTS.md` (177 lines), `MANET_IDS_BTech_Execution_Guide.md` (391 lines), `.gitignore` (22 lines), and a git repo on branch `main` with a single commit (`2246d39 Add project spec and agent instructions`) and **no remote configured**. There is no source code, no manifest, no lint/format config, no test suite, and no CI. Do not assume any [SPECIFIED] item exists.

> **Precedence.** Where `AGENTS.md` and `MANET_IDS_BTech_Execution_Guide.md` conflict, `AGENTS.md` wins on engineering rules and the guide wins on project specification (`AGENTS.md:14-16`). This document encodes the *engineering* rules; where it names a module or path that the guide prescribes, both agree.

---

## Naming Patterns

**Files:**

- **[SPECIFIED]** Python module files are lowercase `snake_case.py`, one concern per file. The `simulator/` module set is prescribed by name and must not be renamed:
  | Module | Owns | Source |
  |---|---|---|
  | `simulator/mobility.py` | Random Waypoint motion; node speed feeds the `mobility_speed` feature | `AGENTS.md:56` |
  | `simulator/radio.py` | Transmission range / link availability; drives `neighbor_count` | `AGENTS.md:57` |
  | `simulator/aodv.py` | RREQ/RREP/RERR, sequence numbers, route table (hop count, expiry); records `route_request_rate` / `route_reply_rate` per window | `AGENTS.md:58-59` |
  | `simulator/traffic.py` | CBR/UDP flows (source–dest pairs, packet rate, payload size) | `AGENTS.md:60` |
  | `simulator/metrics.py` | PDR, throughput, end-to-end delay, packet loss, routing overhead | `AGENTS.md:64` |
  | `simulator/run_scenario.py` | CLI: `--scenario <json> --seed <int> --out <dir>` | `AGENTS.md:65` |
- **[SPECIFIED]** `attacks/` is a **top-level package** (the guide's Module B) containing Blackhole and Grayhole implemented as **node behaviour flags** on the AODV node — a lying reply (blackhole) and probabilistic drop (grayhole) (`AGENTS.md:61-63`, `MANET_IDS_BTech_Execution_Guide.md:94-100`).
  - Recommended file names (not fixed by the contract): `attacks/blackhole.py`, `attacks/grayhole.py`, `attacks/__init__.py`.
  - `attacks/__init__.py` exports the two behaviour constructors; it holds no logic.
- **[SPECIFIED]** `feature_extraction/` — traces → feature CSV (`AGENTS.md:119`). Recommended: `feature_extraction/extract_features.py`.
- **[SPECIFIED]** `ml/` — training/eval/pipeline code + the saved model (`AGENTS.md:120`). Recommended: `ml/dataset.py`, `ml/split.py`, `ml/train.py`, `ml/evaluate.py`, `ml/response.py`, `ml/run_evaluation.py`, `ml/plots.py`, `ml/models/`. (Feature computation lives in `feature_extraction/features.py` — there is no `ml/features.py`.)
- **[SPECIFIED]** `dashboard/` — optional viewer, last phase only (`AGENTS.md:122`, `AGENTS.md:166-167`).
- **[SPECIFIED]** `docs/` — notes, deviations, experiment log (`AGENTS.md:123`).
- **[IMPLEMENTED]** No source file of any kind exists yet. The only real files are `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md`, `.gitignore`.

- **Recommended (not yet fixed by the contract) — adopt these when the files are created.** The authoritative version of this list lives in `.planning/codebase/STRUCTURE.md` § "Naming Conventions"; keep the two in sync.
  - Test files: `test_<module>.py` matching the module under test — `simulator/aodv.py` → `test_aodv.py`. Tests live **inside the owning package** (`simulator/tests/`, `attacks/tests/`, `feature_extraction/tests/`, `ml/tests/`) — see `.planning/codebase/STRUCTURE.md` § "Where to Add New Code".
  - Scenario configs: `scenarios/<experiment-id>_<variant>.json`, using the guide's experiment ids — e.g. `scenarios/e1_normal_30n.json`, `scenarios/e2_blackhole_center.json`, `scenarios/e8_unseen_seed7.json` (`MANET_IDS_BTech_Execution_Guide.md:244-253`).
  - **Run id (the single join key across every artifact):** `run_id = "<scenario_stem>__s<seed>"` — e.g. `e1_normal_30n__s7`. The double underscore separates the scenario from the seed so the id can be split back apart mechanically. This is what makes every reported number traceable to its run (`AGENTS.md:151`).
  - Trace artifacts: `traces/<run_id>.csv` — e.g. `traces/e1_normal_30n__s7.csv` (`traces/` is gitignored — `.gitignore:2`).
  - Dataset artifacts: `data/<dataset-name>.csv` — e.g. `data/dataset.csv` (`data/` is gitignored — `.gitignore:3`).
  - Run records: `results/runs/<run_id>.json` — e.g. `results/runs/e1_normal_30n__s7.json` (bulk `results/*` ignored, `results/plots/` committed — `.gitignore:5-7`).
  - Model artifacts: `ml/models/<model_name>__<dataset_stem>.joblib`.
  - Figures: `results/plots/<metric>_<comparison>.png` (committed — `.gitignore:7`).

**Directories:**

- **[SPECIFIED]** The top-level layout is fixed (`AGENTS.md:113-124`, `MANET_IDS_BTech_Execution_Guide.md:160-173`):
  ```text
  simulator/            # in-repo Python MANET simulator (replaces ns3/)
  attacks/              # blackhole / grayhole behaviour strategies (injected into the simulator)
  scenarios/            # one JSON config per experiment/scenario
  traces/               # generated CSV traces          (gitignored)
  data/                 # built datasets                (gitignored, keep samples)
  feature_extraction/   # traces -> feature CSV
  ml/                   # training/eval/pipeline code + saved model
  results/              # metrics, plots, per-run records (gitignored except plots)
  dashboard/            # optional viewer
  docs/                 # notes, deviations, experiment log
  ```
- **[SPECIFIED]** Do not introduce `src/`, `lib/`, `app/`, or a `main.py` root script. The layout above is the contract.
- **[SPECIFIED]** One documented tension: `AGENTS.md:113-124` does **not** list a `tests/` directory, and `.planning/codebase/STACK.md:198` suggests per-package test dirs (e.g. `simulator/tests/`) to keep the layout exact. A test directory is nonetheless required (see `.planning/codebase/TESTING.md`). **Whichever location is chosen must be recorded in `AGENTS.md` in the same commit** (`AGENTS.md:14-16`).

**Functions:**

- **[SPECIFIED by example]** `snake_case`, verb-first, no abbreviations: `run_scenario()`, `simulate()`, `compute_pdr()`, `extract_features()`, `load_scenario()`, `train_baseline()`, `evaluate_split()`.
- **[SPECIFIED by example]** The CLI verb set is fixed by `AGENTS.md:65`: `--scenario`, `--seed`, `--out`.

**Variables:**

- **[SPECIFIED]** `snake_case`. Simulation-domain names to use consistently: `node_id`, `seed`, `rng`, `sim_time`, `window_start`, `window_end`, `attacker_id`, `drop_probability`, `route_request_rate`, `route_reply_rate`, `pdr`, `throughput`, `end_to_end_delay`, `packet_loss`, `routing_overhead`.
- **[SPECIFIED]** Feature column names are fixed and snake_case (`MANET_IDS_BTech_Execution_Guide.md:106-117`): `packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`, `neighbor_count`, `mobility_speed`, `label`. Do not rename, re-case, or reorder these — downstream code and the report depend on them.
- **[SPECIFIED]** Label values are fixed strings: `Normal`, `Blackhole`, `Grayhole` (`MANET_IDS_BTech_Execution_Guide.md:117`).

**Types:**

- **[SPECIFIED]** Use stdlib `dataclasses` for structured records — `AGENTS.md:52` ("stdlib `dataclasses` / `json` / `csv` for scenarios, traces, and metrics").
- **[SPECIFIED]** Dataclass names are `PascalCase`; fields are `snake_case`. Recommended set: `ScenarioConfig`, `NodeState`, `RouteEntry`, `PacketEvent`, `TraceRow`, `FeatureRow`, `RunMetrics`, `AttackBehavior`.
- **[SPECIFIED]** Every dataclass that carries a number must document its **unit** and its **source** (observed trace vs. scenario config) in its docstring. Units are: times in *simulated seconds*, rates in *per window*, delays in *simulated seconds* (never wall clock).

---

## Code Style

**Formatting:**

- **[IMPLEMENTED]** No formatter is configured and none is mandated: no `.ruff.toml`, no `pyproject.toml`, no `setup.cfg`, no `.pre-commit-config.yaml`, no `.editorconfig`. `AGENTS.md` and `MANET_IDS_BTech_Execution_Guide.md` mandate no formatting tool.
- **[SPECIFIED]** Write PEP 8: 4-space indent, UTF-8 source, no tabs, ≤ 100 columns (≤ 88 preferred for code; the 100 limit accommodates the trace-schema strings).
- **[SPECIFIED]** Keep the trace header on one line so it is greppable and diffable:
  `time, src, dst, pkt_id, type, hop_count, dropped_by, ...` (`AGENTS.md:81-83`).
- **[Recommended]** `ruff` 0.16.1 and `black` 26.3.1 are installed in the environment but undeclared and unused. If either is adopted it must be **non-blocking on day one** and must **not reformat existing files as a side effect of an unrelated change**. Record the choice in `AGENTS.md` in the same commit (`AGENTS.md:14-16`).

**Linting:**

- **[IMPLEMENTED]** None configured.
- **[SPECIFIED]** Regardless of tooling, these are hard rules:
  - No bare `except:` and no `except Exception: pass`.
  - No module-level mutable global state (no module-level caches, no module-level `random.Random()`).
  - No `print()` in library code — use `logging` (§ Logging). `print()` is allowed only in `simulator/run_scenario.py` and other CLI entry points.
  - No `# type: ignore` / `# noqa` without a trailing comment explaining why.
  - Every public function and every dataclass has a docstring.
  - No wildcard imports (`from x import *`).
- **[Recommended]** `ruff check` with `E` (pycodestyle errors), `F` (pyflakes), `I` (import sorting) is a safe minimal default. It is not currently installed as a project dependency, so this stays optional.

---

## Import Organization

**Order:**

1. **stdlib** — `dataclasses`, `json`, `csv`, `argparse`, `logging`, `pathlib`, `random`, `sys`
2. **third-party** — `simpy`, `networkx`, `numpy`, `pandas`, `sklearn`, `matplotlib`/`seaborn`
3. **first-party** — `simulator.*`, `attacks.*`, `feature_extraction.*`, `ml.*`

**Path Aliases:**

- **[IMPLEMENTED]** None. No `pyproject.toml`, no `setup.cfg`, no `conftest.py` path manipulation.
- **[SPECIFIED]** First-party imports use **absolute package paths** — `from simulator.aodv import AodvNode`, never relative `..aodv` hops across packages.
- **[SPECIFIED]** Every package directory MUST contain an `__init__.py` so that `python -m simulator.run_scenario` resolves without installing the repo.
- **[SPECIFIED]** Run entry points as modules, never as file paths:
  ```bash
  python -m simulator.run_scenario --scenario scenarios/e1_normal_30n.json --seed 1 --out traces/
  ```
  `python simulator/run_scenario.py` breaks package-relative imports and double-imports modules (two distinct `ScenarioConfig` classes) — it is a bug, not a style choice.
- **[SPECIFIED]** **Import boundary — the single most important import rule in this repo:** `simulator/` must **not** import `attacks/` (`AGENTS.md:67-69`). Attack behaviour is injected by the scenario runner, which keeps the simulator attack-agnostic and lets the *same* simulator code produce the clean baseline used for the IDS-off comparison.
  - The dependency arrow is: **runner → simulator ← attacks**. The runner constructs both and hands the attack object to the node.
  - **[Recommended]** Keep the arrow symmetric — `attacks/` should also not import `simulator/`. Implement the blackhole/grayhole behaviours as duck-typed behaviour objects that the AODV node consults (`node.attack_behavior` is `None` for a clean node), so the attack package has no simulator dependency at all.
  - **[Recommended]** `feature_extraction/` reads only `traces/*.csv` + `scenarios/*.json`; it must not import `simulator/`. It operates on artifacts, so the dataset can be rebuilt from archived traces without re-simulating.
  - **[Recommended]** `ml/` — the **model layer** (`ml/dataset.py`, `ml/split.py`, `ml/train.py`, `ml/evaluate.py`) reads only `data/*.csv`; it must not import `simulator/` or `attacks/`. **Documented exception:** the **integration module** (`ml/run_evaluation.py`, `ml/response.py`) may import `simulator/`, because the IDS-off/IDS-on re-evaluation run is by definition a simulation. The arrow points upward only — `simulator/` must never import `ml/`. Record the exception in `docs/deviations.md` when Phase 4 is built. See `.planning/codebase/ARCHITECTURE.md` § L7.
  - **[Recommended]** `dashboard/` reads only `results/`.
- **Circular imports:** none are permitted. The allowed dependency graph is a DAG: `simulator ← attacks`, `feature_extraction`, `ml`, `dashboard`. If you hit an import cycle, the fix is to move the shared type into the lower package — never to break the cycle with a local import inside a function.

---

## Error Handling

**Patterns:**

- **[IMPLEMENTED]** No error-handling framework, no custom exception hierarchy. Stdlib exceptions only.
- **[SPECIFIED]** Validate the scenario JSON **once, at load time**, before the simulation clock starts. A malformed config must fail in under a second, not after 300 simulated seconds. Raise `ValueError` with a message naming the offending key and file.
- **[SPECIFIED]** Fail fast and loudly. Never catch-and-ignore:
  - ❌ `except Exception: pass`
  - ❌ `try: ... except: continue` inside a packet loop
  - ✅ catch the *specific* exception you can handle, handle it, and re-raise otherwise
- **[SPECIFIED]** At the CLI boundary (`simulator/run_scenario.py` and any other entry point) catch only the **expected** failure classes — `FileNotFoundError`, `json.JSONDecodeError`, `ValueError` — print a one-line message to `stderr`, and `sys.exit(2)`. Let unexpected exceptions propagate with their traceback.
- **[SPECIFIED]** `KeyboardInterrupt` → exit code 130.
- **[SPECIFIED]** A failed run must not leave a partial trace file that a later step mistakes for a complete run. Either write to a temp name and rename on success, or record the completed row count and a completion flag in the run record under `results/`.
- **[SPECIFIED]** Never "fix" a failed run by relaxing an assertion, widening a tolerance, or dropping a scenario. A failing run is information.

---

## Logging

**Framework:**

- **[IMPLEMENTED]** No logging framework is configured and no logging library is used. Stdlib `logging` is available and is the correct choice — do not add `loguru` or `structlog`.
- **[SPECIFIED]** No secret values exist anywhere in this project, so no secret-redaction logic is needed. Do not add it speculatively.

**Patterns:**

- **[SPECIFIED]** Every module that logs does:
  ```python
  import logging

  logger = logging.getLogger(__name__)
  ```
  Never `logging.basicConfig()` in a library module — only in the CLI entry point.
- **[SPECIFIED]** `simulator/run_scenario.py` configures the root logger from a `--log-level` flag (default `INFO`, choices `DEBUG`/`INFO`/`WARNING`/`ERROR`).
- **[SPECIFIED]** **Console output is for the operator; `results/` is for the record.** Every run writes a machine-readable record under `results/` capturing: scenario config path, seed, config hash, the metric set, and a timestamp — so every number in the report can be traced to a saved run (`AGENTS.md:151`, `MANET_IDS_BTech_Execution_Guide.md:320`).
- **[SPECIFIED]** Never log per-packet events at `INFO`. The forwarding path is the hot path (~70k events/sec measured, `AGENTS.md:80`); per-packet logging at `INFO` will dominate run time. Per-packet detail belongs at `DEBUG` and is off by default.

---

## Comments

**When to Comment:**

- **[SPECIFIED]** Comment the *why* and the *contract*, never the *what*. The codebase is a research artifact whose correctness rests on rules that are invisible in the code — those rules get comments.
- **[SPECIFIED]** Mandatory comment sites (each exists because a contract rule depends on it):
  1. Top of `simulator/aodv.py` — the node carries **behaviour flags**; the simulator stays attack-agnostic and must never import `attacks/` (`AGENTS.md:61-69`).
  2. At the trace writer in `simulator/` — *features are derived from traces, never embedded in them* (`AGENTS.md:83`).
  3. At the label-join step in `feature_extraction/` — *labels come from the scenario config, never from the trace* (`AGENTS.md:84-85`).
  4. At the split call in `ml/` — *hold out by scenario/seed group; a random row split inflates scores* (`AGENTS.md:142-143`).
  5. At every `random`/`rng` use — which seed source it draws from, and that the seed is the only source of nondeterminism (`AGENTS.md:72-74`).
  6. At any metric function — which simulated-time quantity it reports and in what unit.
- **[SPECIFIED]** Do not write comments that describe tutorial-era pandas 2 behaviour or pre-revision NS-3 architecture; both are superseded (`AGENTS.md:98-105`, `MANET_IDS_BTech_Execution_Guide.md:10-12`).

**JSDoc/TSDoc (Python analogue — PEP 257):**

- **[SPECIFIED]** Module docstring on every module: one paragraph stating purpose **and the invariant it protects**.
- **[SPECIFIED]** Class docstring on every dataclass: what each field means, its unit, and where the value comes from (observed vs. configured).
- **[SPECIFIED]** Function docstring: one-line summary, then `Args:`, `Returns:`, and `Raises:` where it raises. Private helpers (`_`-prefixed) need only a one-line summary — but a non-obvious helper gets a full docstring.

---

## Function Design

**Size:**

- **[SPECIFIED]** Keep functions short and single-purpose. AODV message handling, metric computation, and feature extraction are each separate functions — do not write one `run()` that does topology, routing, and metrics.
- **[SPECIFIED]** The packet-forwarding path is a hot path. Per-packet work must be O(1) with no heavy allocation — do not construct dataclasses per packet in the forwarding loop; write scalars or reuse a buffer.

**Parameters:**

- **[SPECIFIED]** Pass an explicit `rng: random.Random` into every stochastic component. **Never call the `random` module globals inside library code** — that is how runs stop being reproducible.
- **[SPECIFIED]** Accept `seed: int` at the entry point and thread it down. No component re-seeds; no component invents a seed.
- **[SPECIFIED]** Use keyword-only arguments for optional behaviour switches, e.g. `run_scenario(..., *, attack=None, log_level="INFO")`.
- **[SPECIFIED]** Pass the window explicitly into metric functions (`window_start`, `window_end`) rather than reading a global clock — this is what makes `route_request_rate` / `route_reply_rate` per-window metrics well-defined (`AGENTS.md:59`).

**Return Values:**

- **[SPECIFIED]** Return dataclasses or dicts, not long tuples. `RunMetrics` with named fields beats `return pdr, tput, delay, loss, overhead` — a 5-tuple is exactly the kind of thing that gets read in the wrong order during a baseline comparison.
- **[SPECIFIED]** Return `None` only from genuinely side-effect-only functions.
- **[SPECIFIED]** Metric functions return floats in **simulated time**; never wall-clock durations.

---

## Module Design

**Exports:**

- **[SPECIFIED]** Each package's public API is re-exported from its `__init__.py` with an explicit `__all__` list.
- **[SPECIFIED]** No wildcard imports anywhere, in either direction.
- **[SPECIFIED]** Private helpers are prefixed with `_` and are not exported.

**Barrel Files:**

- **[SPECIFIED]** `__init__.py` in each package re-exports the package's public surface and contains **no logic**.
- **[SPECIFIED]** An `__init__.py` must not import a submodule that imports the package root — that is the classic barrel-file cycle. Import the submodule, not the package, from inside submodules.

---

## Determinism Convention (binding)

- **[SPECIFIED]** Every run is driven by an **explicit integer seed**. Same seed ⇒ identical traces (`AGENTS.md:72-74`). The `--seed <int>` flag on `simulator/run_scenario.py` is the only supported source (`AGENTS.md:65`).
- **[SPECIFIED]** `simpy.Environment` in SimPy 4.1.2 has **no `seed` parameter** and **no `env.random`** (verified on the installed 4.1.2). The 3.x `env.seed()` / `env.random` API is gone. Create `rng = random.Random(seed)` in `simulator/run_scenario.py` and pass it explicitly into mobility waypoint choice, radio loss, attack drop decisions, and traffic jitter.
- **[SPECIFIED]** **Never iterate over a `set`** where the order affects behaviour — sort it: `sorted(node_ids)`. This is the classic source of "identical runs differ" (`AGENTS.md:175-176`).
- **[SPECIFIED]** Never derive run-affecting values from `id()`, `hash()`, `time.time()`, `uuid4()`, `os.urandom`, or filesystem ordering.
- **[SPECIFIED]** The time base is **simulated seconds** from the SimPy clock (`env.now()`), monotonic, starting at 0. Wall-clock durations never enter a trace or a metric.
- **[SPECIFIED]** Re-running the same scenario + seed must produce a **byte-identical** trace. Treat any diff as a bug, not a tolerance.
- **[Recommended]** Add a `--seed` to every stage that consumes randomness (feature windowing, dataset assembly, model training) and record the seed in the run record.

---

## Environment Conventions (version gotchas are conventions, not trivia)

`AGENTS.md:89-107` records the verified environment. These are **rules to code against**, not trivia — each one will silently break a copied tutorial snippet.

| Package | Installed | Convention to follow |
|---|---|---|
| **pandas** | 3.0.2 (not 2.x) | Copy-on-Write is **always on**; the `pd.options.mode.copy_on_write` toggle is deprecated and inert — never write it. **`DataFrame.applymap` is REMOVED** — use `DataFrame.map` (elementwise) or `Series.map`. String columns default to the **`str` dtype**, not `object` — never `astype("object")` to "restore" pandas 2, and never write `dtype="object"` filters. Use `df = df.assign(...)` rather than mutating a view in place. |
| **numpy** | 1.26.4 (**not** 2.x) | numpy 2 migration notes do **not** apply (`AGENTS.md:103`). Stay on the 1.26 API surface: `np.float_`, `np.int_`, `np.NaN` behave as in 1.x. Do not apply 2.x copy/dtype-promotion changes. |
| **scikit-learn** | 1.8.0 | Newer than most tutorial pins (most assume 1.0–1.2) — **check the sklearn API notes before copying any snippet** (`AGENTS.md:105`). The project APIs are stable and present: `DecisionTreeClassifier`, `RandomForestClassifier`, `SVC`, `GroupShuffleSplit`, `StratifiedGroupKFold`, `Pipeline`, `StandardScaler`, `classification_report`, `confusion_matrix`. Use `GroupShuffleSplit`/`StratifiedGroupKFold` for the mandated group holdout. |
| **SimPy** | 4.1.2 | 3.x `env.seed()` / `env.random` removed — see § Determinism Convention. `import simpy.util` explicitly if you use `simpy.util.start()`; it is not auto-imported. |
| **Python** | 3.11.8 | 3.11+ floor (`MANET_IDS_BTech_Execution_Guide.md:143`). `tomllib` is in the stdlib, so a `pyproject.toml` can be read without a dependency. |
| **pip** | 26.1.2 | **Always `python -m pip ...`, never bare `pip`** (`AGENTS.md:107`) — bare `pip` can resolve to a different interpreter than the one running the code. |

- **[SPECIFIED]** **No new runtime dependency without an explicit decision** recorded in `AGENTS.md` and `MANET_IDS_BTech_Execution_Guide.md` in the same commit (`AGENTS.md:14-16`, `AGENTS.md:36-37`). The specified stack (SimPy, NetworkX, scikit-learn, pandas, numpy, matplotlib, seaborn) covers the whole scope.
- **[Recommended]** Use stdlib `argparse` for the CLI, not `click`/`typer` — the smallest change that solves the problem.

---

## Data and Artifact Conventions

- **[SPECIFIED]** **Trace format.** CSV, one row per packet event, header beginning `time, src, dst, pkt_id, type, hop_count, dropped_by, ...`, written to `traces/` (`AGENTS.md:81-83`).
  - Define the header **once**, as a module-level constant (e.g. `TRACE_HEADER` in `simulator/`), and import it wherever it is needed — the feature extractor, the tests, and the writer must agree by construction, not by copy-paste.
  - Keep the column set stable. Downstream code depends on it.
- **[SPECIFIED]** Traces contain **observed network behaviour only**. No feature columns, no label column, no attacker id, no scenario metadata beyond what was actually observed.
- **[SPECIFIED]** **Features are derived from traces, never embedded in them** (`AGENTS.md:83`).
- **[SPECIFIED]** **Labels come from the scenario config** (which node is the attacker, which attack), **never from the trace** (`AGENTS.md:84-85`). This is what keeps the dataset ground truth honest.
- **[SPECIFIED]** **No leakage features.** Never add a column that directly reveals attacker identity or the attack label — no `is_attacker`, no `attack_type`, no field derived from the attack config rather than from observed traffic (`AGENTS.md:145-146`, `MANET_IDS_BTech_Execution_Guide.md:315`).
- **[SPECIFIED]** **Keep the attack's effect in the network behaviour** (drops, PDR), not in a flag the metrics can read directly (`AGENTS.md:86-87`). Otherwise detection becomes trivial and the result is worthless.
- **[SPECIFIED]** Scenarios are JSON (stdlib `json`), one config per experiment, under `scenarios/` (`AGENTS.md:116`). The scenario is the **single source of truth** for node count, area, mobility, traffic, seed, attack type, and attacker node id.
- **[SPECIFIED]** Metrics and run records are JSON under `results/`.
- **[SPECIFIED]** **Git policy** (`AGENTS.md:126-130`, `MANET_IDS_BTech_Execution_Guide.md:175`, `.gitignore:1-7`): commit code, scenario configs, small sample data, plots, and docs. **Never commit large generated trace files.** `traces/` and `data/` stay ignored; bulk `results/` stays ignored but `results/plots/` is committable.
- **[SPECIFIED]** Every result must be traceable back to a saved run + its config (`AGENTS.md:130`, `AGENTS.md:151`).
- **[SPECIFIED]** **Windows-safe paths.** The repo root path contains spaces (`C:\Users\KIIT0001\Documents\projects\Machine Learning-Based Intrusion Detection System for MANET`). Use `pathlib.Path` everywhere; never build paths with `+` or hard-coded separators; always quote paths in shell commands.

---

## Command-Line Interface Convention

- **[SPECIFIED]** `simulator/run_scenario.py` exposes exactly `--scenario <json> --seed <int> --out <dir>` (`AGENTS.md:65`).
- **[Recommended]** Add `--log-level` (default `INFO`) and, for the matrix runner, `--attacker` / `--nodes` overrides that **write the effective config back out as JSON** so the run record is never inferred.
- **[SPECIFIED]** Flags are kebab-case; arguments take a value with a space (`--seed 7`), not `=`.
- **[Recommended]** Exit codes: `0` success, `2` invalid input/config, `130` interrupt.
- **[SPECIFIED]** Every other stage is invoked the same way: `python -m feature_extraction.extract_features --traces traces/ --out data/`, `python -m ml.train --dataset data/… --model ml/model.joblib`.

---

## Documentation Sync Rule (binding)

- **[SPECIFIED]** `AGENTS.md` and `MANET_IDS_BTech_Execution_Guide.md` must be changed **together in the same commit** (`AGENTS.md:14-16`, `AGENTS.md:36-37`). Never leave them disagreeing.
- **[SPECIFIED]** Any architecture change is mirrored into the guide in the same change (`AGENTS.md:36-37`).
- **[SPECIFIED]** `docs/` holds notes, deviations, and the experiment log (`AGENTS.md:123`). A deviation from the guide is recorded in `docs/` **and** in both root documents.

---

## Scope Discipline (binding — affects what code may exist)

- **[SPECIFIED]** Do not start with six attacks, deep learning, federated learning, blockchain, or a mobile app (`AGENTS.md:155`, `MANET_IDS_BTech_Execution_Guide.md:59`).
- **[SPECIFIED]** Attack order: **Blackhole first**, then Grayhole, then flooding/DoS only if the first two are stable (`AGENTS.md:156-157`, `MANET_IDS_BTech_Execution_Guide.md:55`).
- **[SPECIFIED]** Do not claim the model "detects all MANET attacks." State exactly which attacks, traffic conditions, mobility models, and simulator settings were evaluated (`AGENTS.md:161`, `MANET_IDS_BTech_Execution_Guide.md:79`).
- **[SPECIFIED]** A dashboard is secondary to the acceptance chain — do not build one before the chain works (`AGENTS.md:166-167`).
- **[SPECIFIED]** **Mentor checkpoint rule:** at the end of each week freeze a working version. If an advanced feature threatens the core demonstration, cut the advanced feature and keep the baseline (`AGENTS.md:158-159`, `MANET_IDS_BTech_Execution_Guide.md:387`).

---

## Checklist for future implementers

1. **Python only.** No C++, no C toolchain, no NS-3 (`AGENTS.md:25-31`).
2. **Stay inside the prescribed layout** (`AGENTS.md:113-124`).
3. **Respect the import boundary** — `simulator/` never imports `attacks/` (`AGENTS.md:67-69`).
4. **`python -m pip`, never bare `pip`** (`AGENTS.md:107`).
5. **Seed everything.** `random.Random(seed)` threaded explicitly; never iterate a `set` (`AGENTS.md:72-74`, `AGENTS.md:175-176`).
6. **Traces hold observations only**; features are derived, never embedded; labels come from the scenario config (`AGENTS.md:83-85`).
7. **No leakage columns** — ever (`AGENTS.md:145-146`).
8. **Use `pathlib.Path`**; the repo path contains spaces.
9. **No new dependency without a decision** recorded in both root docs in the same commit (`AGENTS.md:14-16`).
10. **Do not skip the gates** — simulator → attack validation → data → baseline model → comparison → generalization, in that order (`AGENTS.md:134-138`).
11. **Report the full metric set** — precision, recall, F1, false-positive rate, confusion matrix; never accuracy alone (`AGENTS.md:148-149`).
12. **Every number traces to a saved run + its config** (`AGENTS.md:151`).
13. **Keep generated data out of git**; commit code, scenarios, small samples, plots, docs (`.gitignore:1-7`).
14. **Keep `AGENTS.md` and the guide in sync** (`AGENTS.md:14-16`).

---

*Convention analysis: 2026-10-22 — derived from `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md`, `.gitignore`, the existing `.planning/codebase/STACK.md` and `.planning/codebase/INTEGRATIONS.md`, and direct inspection of the installed Python 3.11.8 environment (pandas 3.0.2, numpy 1.26.4, scikit-learn 1.8.0, simpy 4.1.2, networkx 3.6.1, pytest 9.0.2, pytest-cov 7.1.0, ruff 0.16.1, black 26.3.1). No packages were installed and no network or package-manager write commands were run.*
