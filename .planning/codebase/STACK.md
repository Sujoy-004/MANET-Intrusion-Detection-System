# Technology Stack

**Analysis Date:** 2026-10-22

> **Status legend.** Every entry below is tagged.
> - **[IMPLEMENTED]** — exists in the repo today, verified by reading the file.
> - **[SPECIFIED]** — mandated or directed by `AGENTS.md` and/or `MANET_IDS_BTech_Execution_Guide.md`, with the intended repo-relative path. **Not yet built.**
>
> **Verified repo contents (2026-10-22):** only `AGENTS.md` (177 lines), `MANET_IDS_BTech_Execution_Guide.md` (391 lines), `.gitignore` (22 lines), and a git repo on branch `main` with a single commit (`2246d39 Add project spec and agent instructions`) and **no remote configured**. There is no source code, no manifest, no CI, and no test suite. Do not assume any of the [SPECIFIED] items exist.

## Languages

**Primary:**
- **Python 3.11.8** — the *only* language in this project. Simulator, feature extraction, ML training/evaluation, response logic, plots, and (optionally) the dashboard are all Python. **[IMPLEMENTED]** (runtime present) / **[SPECIFIED]** (all code paths).
  - Interpreter on this machine: `C:\Program Files\Python311\python.exe`
  - Rationale: `AGENTS.md:25` — "**Python only** — simulator *and* ML. No C++ anywhere."

**Secondary:**
- **None.** C++ is explicitly forbidden — `AGENTS.md:25`, `AGENTS.md:30-31` ("Never attempt to install or build NS-3, `ns-3-dev`, or a C++ toolchain here. It will fail and it is out of scope."), and `MANET_IDS_BTech_Execution_Guide.md:143` ("Python only (3.11+). No C++, no compiler toolchain").
- **No C/C++/Cython/Rust/Go/TypeScript** anywhere, including build scripts and vendored native extensions.
- **Notebook format (`.ipynb`)** is permitted as an *analysis* surface (JupyterLab is installed, `AGENTS.md:95`), but the durable logic MUST live in importable `.py` modules so the pipeline is scriptable and reproducible. `MANET_IDS_BTech_Execution_Guide.md:309` — "Do not create a situation where only one student can run the project."

**Explicitly dropped (do not reintroduce):**
- **NS-3 / ns-3-dev** — dropped in favour of the in-repo simulator (`AGENTS.md:26`, `MANET_IDS_BTech_Execution_Guide.md:10-12`, `MANET_IDS_BTech_Execution_Guide.md:85`).
- **C++/Ubuntu** — dropped in favour of Windows-native Python (`AGENTS.md:27`).
- **`ns.py` (PyPI)** — evaluated and rejected: it is a wired IP-flow simulator (ports, schedulers, TCP/BBR, FatTree) with no wireless, mobility, or AODV layer (`AGENTS.md:43-45`).
- **Deep learning, federated learning, blockchain, mobile app** — out of scope per `AGENTS.md:155` and `MANET_IDS_BTech_Execution_Guide.md:59`.

## Runtime

**Environment:**
- **CPython 3.11.8** — 64-bit, native Windows install at `C:\Program Files\Python311\python.exe`. **[IMPLEMENTED]**
- Target floor is **3.11+** per `MANET_IDS_BTech_Execution_Guide.md:143` and `MANET_IDS_BTech_Execution_Guide.md:151`.
- No alternative interpreters (PyPy, Conda, micromamba, uv-managed shims) are in use. Do not add one — `AGENTS.md:107` requires `python -m pip`, which only works if the interpreter is the plain CPython install.

**Package Manager:**
- **pip 26.1.2** — resolved to `C:\Users\KIIT0001\AppData\Roaming\Python\Python311\site-packages\pip` (user site-packages, not a venv). **[IMPLEMENTED]**
- **Invocation convention (binding, `AGENTS.md:107`):** always `python -m pip ...`, never bare `pip`. Rationale: bare `pip` can resolve to a different interpreter than the one running the code. Examples:
  - `python -m pip install -r requirements.txt`
  - `python -m pip install "scikit-learn==1.8.0"`
- **Virtualenv (`.venv/`)** — `AGENTS.md:151` and `MANET_IDS_BTech_Execution_Guide.md:151` recommend "create a project virtual environment", and `.gitignore:13-14` already ignores `.venv/` and `venv/`. **[SPECIFIED]** — no `.venv/` exists in the repo yet. A future implementer MUST decide (venv) and record the decision; note that `python -m pip` still works inside an activated venv.
- **Lockfile: MISSING.** There is no `requirements.txt`, no `pyproject.toml`, no `Pipfile`, no `poetry.lock`, no `uv.lock`. **[GAP — see "Manifest gap" below]**

**Other tools:**
- **Git 2.50.1.windows.1** — version control, branch `main`, no remote. **[IMPLEMENTED]**
- **VS Code** — installed at `C:\Users\KIIT0001\AppData\Local\Programs\Microsoft VS Code\bin\code`. **[IMPLEMENTED]** (recommended editor, `MANET_IDS_BTech_Execution_Guide.md:146`).

## Frameworks

**Core:**
- **SimPy 4.1.2** — the discrete-event clock for the whole simulator. `AGENTS.md:49-50`: "`Environment`, `env.process`, `env.timeout`. Installed (pure Python, compiles nothing)."
  - **[SPECIFIED]** consumption points: `simulator/mobility.py` (waypoint ticks), `simulator/radio.py` (link availability), `simulator/aodv.py` (RREQ/RREP/RERR timers, route expiry), `simulator/traffic.py` (CBR/UDP packet generation), `simulator/metrics.py` (windowing), `simulator/run_scenario.py` (CLI driver).
  - **SimPy 4.x API trap:** `simpy.Environment.__init__(self, initial_time: SimTime = 0)` has **no `seed` parameter** and `env.random` **does not exist** (verified on 4.1.2). The old SimPy 3.x `env.seed()` / `env.random` API is gone. Determinism MUST come from an explicit `random.Random(seed)` instance that you thread through the simulator — see "Determinism" below.
  - `simpy.util` is a subpackage and is **not** auto-imported; `import simpy.util` explicitly if you use `simpy.util.start()`.
- **NetworkX 3.6.1** — topology graph, neighbor sets, route-graph analysis. `AGENTS.md:51`. **[SPECIFIED]** consumption points: `simulator/radio.py` (link graph), `simulator/aodv.py` (neighbor/route graphs), `simulator/metrics.py` (graph analysis), `feature_extraction/` (graph-derived features if any).
- **scikit-learn 1.8.0** — the entire ML engine (`ml/`). `AGENTS.md:95`, `MANET_IDS_BTech_Execution_Guide.md:8`. **[SPECIFIED]**
  - Required APIs, all verified present in 1.8.0: `sklearn.tree.DecisionTreeClassifier`, `sklearn.ensemble.RandomForestClassifier`, `sklearn.svm.SVC`, `sklearn.model_selection.GroupShuffleSplit`, `sklearn.model_selection.StratifiedGroupKFold`, `sklearn.metrics.classification_report` / `confusion_matrix` / `precision_score` / `recall_score` / `f1_score`, `sklearn.pipeline.Pipeline`, `sklearn.preprocessing.StandardScaler`.
  - **Scenario/seed-based holdout is a hard rule, not a nicety** — `AGENTS.md:142-143` ("Never split by random rows… Hold out by **scenario / seed / configuration**"). Use `GroupShuffleSplit` / `StratifiedGroupKFold` with a group column = run id (scenario × seed). `train_test_split(..., test_size=...)` on raw rows is a rule violation, not just a bad practice.
  - Save the model **and** the preprocessing pipeline (`MANET_IDS_BTech_Execution_Guide.md:127`, deliverable in `MANET_IDS_BTech_Execution_Guide.md:329`) — use `sklearn.pipeline.Pipeline` so scaler + classifier persist together, and `joblib.dump` (joblib 1.5.3 is installed as a scikit-learn dependency) into `ml/`.

**Data / numeric:**
- **pandas 3.0.2** — trace parsing, feature-table assembly, dataset cleaning, metric tables. **[SPECIFIED]** — `feature_extraction/`, `ml/`.
- **numpy 1.26.4** — numeric core. **[SPECIFIED]**
- **scipy 1.17.1** — present in the environment; a transitive dependency of scikit-learn, not a declared one. Use only if genuinely needed (e.g. `scipy.stats` for report statistics) and declare it explicitly if you do.

**Visualization / analysis:**
- **matplotlib 3.10.8** — figures in `results/plots/`. **[SPECIFIED]**
- **seaborn 0.13.2** — confusion matrices, PR/F1 comparison bars (suggested plots at `MANET_IDS_BTech_Execution_Guide.md:263-270`). **[SPECIFIED]**
- **JupyterLab 4.5.6** (+ `ipykernel 7.2.0`, `notebook 7.5.0`) — optional analysis surface. **[SPECIFIED]** as optional (`MANET_IDS_BTech_Execution_Guide.md:147`, `AGENTS.md:95`).
  - On headless/scripted runs, set `matplotlib.use("Agg")` before `pyplot` import in any script that renders to `results/plots/`.

**Testing:**
- **pytest 9.0.2** — installed in the environment but **not declared anywhere** and **not used by any repo file** (there is no test suite, and `.gitignore:15` ignores `.pytest_cache/`, implying pytest is the expected runner). **[SPECIFIED — to be adopted]** See `CONVENTIONS.md` / `TESTING.md` from the quality mapper for the conventions to follow.
- **No `unittest`-only, no `nose`, no Hypothesis** in the environment. Prefer pytest.

**Optional dashboard (NOT in the critical path):**
- **FastAPI 0.135.2**, **Flask 3.1.3**, **uvicorn 0.42.0**, **dash 4.1.0**, **plotly 6.7.0** are all present in the environment, but **none is referenced by the spec as a required dependency**. `MANET_IDS_BTech_Execution_Guide.md:147` lists "Flask/FastAPI dashboard" as *Optional*; `MANET_IDS_BTech_Execution_Guide.md:74` and `MANET_IDS_BTech_Execution_Guide.md:332` list the web dashboard as a *stretch* feature; `AGENTS.md:166-167` is emphatic — "A dashboard is secondary to this chain. Do not build one before the chain works."
- **Rule:** do not import a web framework into `simulator/`, `feature_extraction/`, or `ml/`. A dashboard lives only under `dashboard/` and only after the acceptance chain in `AGENTS.md:163-166` works end to end.

## Key Dependencies

**Critical (the project cannot exist without these):**
- **simpy 4.1.2** — the event clock. Without it there is no simulator. `AGENTS.md:49-50`.
- **networkx 3.6.1** — topology and neighbor sets. `AGENTS.md:51`.
- **scikit-learn 1.8.0** — the detectors. `AGENTS.md:95`, `MANET_IDS_BTech_Execution_Guide.md:8`.
- **pandas 3.0.2** — trace → feature table → dataset. `AGENTS.md:95`.
- **numpy 1.26.4** — numeric substrate. `AGENTS.md:95`.

**Infrastructure:**
- **matplotlib 3.10.8** — plots required by the deliverables (`MANET_IDS_BTech_Execution_Guide.md:329`).
- **seaborn 0.13.2** — confusion matrices and comparison charts.
- **scipy 1.17.1** — transitive via scikit-learn; declare explicitly only if imported directly.
- **jupyterlab 4.5.6** — optional analysis notebooks.
- **pytest 9.0.2** — [SPECIFIED] the intended test runner; not yet declared in any manifest.

**Present in the environment but NOT part of the specified stack (do not silently adopt):**
- `xgboost 3.2.0`, `shap 0.51.0` — stretch features only, and only after the core works (`MANET_IDS_BTech_Execution_Guide.md:70-72`).
- `fastapi`, `flask`, `uvicorn`, `dash`, `plotly` — dashboard only, and the dashboard is the *last* phase.
- `requests 2.32.5`, `pydantic 2.12.5` — there is no network service to call; adding HTTP clients to the pipeline is a smell.
- `joblib 1.5.3` — legitimately useful for model persistence; it is also scikit-learn's own dependency, so it will be present transitively.
- `tqdm`, `click`, `pyyaml` — `click` is a plausible choice for the `simulator/run_scenario.py` CLI (`AGENTS.md:65` specifies `--scenario <json> --seed <int> --out <dir>`), but stdlib `argparse` is sufficient and adds no dependency. **Use `argparse` unless there is a strong reason not to** — the project rule is the smallest change that solves the problem.

**Rejected candidates (documented so nobody re-litigates them):**
- `ns.py` — wired IP-flow simulator, no wireless/mobility/AODV (`AGENTS.md:43-45`).
- `pymansim`, `manet`, `aodv`, `ns3` on PyPI — **all absent** from PyPI (`AGENTS.md:41-42`).
- GitHub-hosted MANET/AODV simulators — search returns only 0–1★ student repos (`AGENTS.md:42-43`).

## Configuration

**Environment:**
- **No environment variables are required** for the specified pipeline. Everything is driven by:
  - **Scenario JSON files** under `scenarios/` — one config per experiment/scenario (`AGENTS.md:116`). These are the single source of truth for node count, area, mobility, traffic, seed, attack type, and attacker node id. They are the *only* legitimate source of ground-truth labels (`AGENTS.md:84-85`).
  - **The `--seed` CLI argument** to `simulator/run_scenario.py` (`AGENTS.md:65`).
  - There is no `.env` file, no `.env.example`, no dotenv loader, and none is needed. If a future phase adds one, it must hold only non-secret local settings and must be gitignored.
- **Secrets: none.** This project has no credentials of any kind. Do not introduce secret management for a simulation that runs entirely on the local filesystem.

**Build:**
- **No build system.** No `setup.py`, `setup.cfg`, `pyproject.toml`, `Makefile`, `tox.ini`, or `noxfile.py`. This is an application/experiment repo, not a distributable package — a `pyproject.toml` is still the right place to pin the toolchain if you add one.
- **No linter/formatter config.** No `.ruff.toml`, `.flake8`, `setup.cfg`, `.pylintrc`, `.editorconfig`, `.pre-commit-config.yaml`, or `.prettierrc`. `AGENTS.md` and the guide mandate **no** formatting tool. A future implementer MAY add `ruff` (not installed today) but MUST keep it non-blocking on day one and MUST NOT reformat existing files as a side effect of an unrelated change.

**Manifest gap (MUST be closed before Phase 1 execution):**
- **No `requirements.txt` and no `pyproject.toml` exist.** Every dependency in this document is currently pinned only in prose inside `AGENTS.md:89-96`. That is a real, live risk: `AGENTS.md:151` and `MANET_IDS_BTech_Execution_Guide.md:279` both require "install dependencies, **record versions**", and `AGENTS.md:151` requires every reported number to trace back to a saved run — which requires a reproducible environment.
- **A future implementer MUST create `requirements.txt`** (repo root) pinning the exact versions below, or equivalently a `pyproject.toml` with a `[project].dependencies` list and pinned versions. Recommended content, matching the verified environment:

  ```text
  simpy==4.1.2
  networkx==3.6.1
  scikit-learn==1.8.0
  pandas==3.0.2
  numpy==1.26.4
  scipy==1.17.1
  matplotlib==3.10.8
  seaborn==0.13.2
  ```

  Add `jupyterlab==4.5.6` and `pytest==9.0.2` only when the notebooks and the test suite actually land — do not add aspirational dependencies.
- **Pin exactly, do not use `>=`.** The version traps below (§ Version traps) are the reason: a `pandas>=2` pin would let a future `pip install` pull pandas 4.x and silently change semantics.
- Do not add a `requirements-dev.txt` split until a second developer actually needs it (YAGNI).
- **Do not add a lockfile generator** (`pip-tools`, `poetry`, `uv`) — plain `requirements.txt` with `==` pins is sufficient and matches the "smallest change" rule.

**Git / artifact policy:**
- **`.gitignore` [IMPLEMENTED]** already encodes the artifact policy: `traces/` and `data/` ignored (`.gitignore:1-3`); `results/*` ignored with `!results/plots/` un-ignored so plots are committable (`.gitignore:5-7`); Python caches, `.venv/`, `venv/`, `.pytest_cache/`, `.ipynb_checkpoints/` ignored (`.gitignore:9-16`).
- **Commit policy (`AGENTS.md:126-130`, `MANET_IDS_BTech_Execution_Guide.md:175`):** commit code, scenario configs, small sample data, plots, and docs. **Never commit large generated trace files.** Every result must be traceable back to a saved run.
- Branch is `main`; **no remote is configured** (`AGENTS.md:6-7`). Do not add one, push, or set up CI without an explicit decision.

## Platform Requirements

**Development:**
- **Windows 10/11, native.** No WSL, no Linux VM, no Docker, no container, no compiler toolchain (`AGENTS.md:27`, `MANET_IDS_BTech_Execution_Guide.md:141`).
- **Verified absences on this machine:** no `gcc` on PATH, no `cmake` on PATH, no `docker` on PATH. A `wsl.exe` stub exists at `C:\Windows\System32\wsl.exe` (it ships with Windows) but **no WSL distribution is installed** per `AGENTS.md:91` — do not attempt `wsl --install`; that is out of scope and will fail.
- **Every path in scripts must be Windows-safe.** Use `pathlib.Path`, never hard-coded `/` or `\` separators, and never `os.path.join` string concatenation. The repo root path itself contains spaces (`C:\Users\KIIT0001\Documents\projects\Machine Learning-Based Intrusion Detection System for MANET`) — always quote paths in shell commands.
- **No native compilation is permitted or needed.** SimPy, NetworkX, scikit-learn, pandas, numpy, scipy, matplotlib, seaborn are all available as pure-Python or prebuilt Windows wheels. If a future `pip install` tries to build from source, something was pinned wrong.
- **No GPU required.** scikit-learn CPU is sufficient; do not add torch/tensorflow/cuda.
- **Simulated time ≠ wall time.** `AGENTS.md:75-80` records a representative workload (50 nodes / 8 flows / 10 pps / 300 s simulated, blackhole attacker) completing in **0.83 s wall** at ~70k events/sec. If a run is slow, per-packet Python overhead is the culprit — **profile before increasing node count**. Do not "fix" slowness by reaching for Cython/Numba.

**Production:**
- **Not applicable — this project has no production deployment.** There is no server, no cloud target, no container image, no release pipeline. The "deployment" of this project is a **local, on-demand, reproducible run** of the acceptance chain (`AGENTS.md:163-166`, `MANET_IDS_BTech_Execution_Guide.md:379`).
- The nearest thing to a shipped artifact is: committed source + scenario configs + `results/plots/` figures + a saved model artifact + the project report and presentation (`MANET_IDS_BTech_Execution_Guide.md:322-334`).
- If a local dashboard is built, it binds to `127.0.0.1` on a free port and is started manually; it is never exposed beyond the host.

## Version traps (read before copying any tutorial snippet)

These are the failures that will bite any future executor. `AGENTS.md:98-105` names them; the specifics below were verified against the installed versions on 2026-10-22.

**pandas 3.0.2 — not 2.x.**
- **Copy-on-Write is always on.** The old `pd.options.mode.copy_on_write = True` toggle is deprecated and inert. Code that relies on mutating a DataFrame in place and then observing the change in a *different* view will silently misbehave. Write `df = df.assign(...)` / `df["col"] = ...` on a single object and pass explicit copies when handing data to another component.
- **`DataFrame.applymap` is REMOVED.** Verified: `hasattr(df, "applymap") == False`. Use **`DataFrame.map`** (elementwise) or `Series.map` (verified present).
- **String columns default to the `str` dtype**, not `object`. Verified: `pd.DataFrame({"b": ["x","y"]})["b"].dtype` → `str`. Consequences: `dtype="object"` filters and `isinstance` checks written for pandas 2 will not match; `pd.NA` semantics differ from `None`/`NaN`; `groupby` on string keys behaves slightly differently. Do not write `astype("object")` to "restore" pandas 2 behaviour.
- pandas 3.x also tightened `groupby`/`merge` null handling and deprecates several 2.x behaviours. When a snippet from a 2.x-era tutorial misbehaves, check the pandas 3 release notes before debugging your own logic.

**numpy 1.26.4 — NOT numpy 2.x.**
- Do **not** apply numpy 2 migration notes (copy semantics changes, `np.string_`/`np.float_` removals, the new dtype promotion rules, `copy=False` meaning changes). Those do not apply here (`AGENTS.md:103`).
- Stay on the numpy 1.26 API surface. `np.float_`, `np.int_`, `np.NaN` behave as in 1.x.

**scikit-learn 1.8.0 — newer than most tutorial pins.**
- Almost every blog post assumes 1.0–1.2. Verify API before copying (`AGENTS.md:105`).
- Known deltas to watch: estimator tag system replaced `_get_tags`/`_more_tags` (only relevant if you write a custom estimator), `OneHotEncoder` `sparse` → `sparse_output` (since 1.2), `get_feature_names_out` naming, and deprecation of several `n_features_in_` adjacent behaviours. The APIs this project needs (`DecisionTreeClassifier`, `RandomForestClassifier`, `SVC`, `GroupShuffleSplit`, `StratifiedGroupKFold`, `Pipeline`, `StandardScaler`, `classification_report`, `confusion_matrix`) are all verified present and stable in 1.8.0.

**SimPy 4.1.2 — the 3.x API is gone.**
- `simpy.Environment(initial_time=0)` — **no `seed` argument**; `env.random` **does not exist**; `env.seed()` is removed. The 3.x `simpy.seed()` global is gone.
- **Consequence for determinism:** create `rng = random.Random(seed)` in `simulator/run_scenario.py` and pass it explicitly into every stochastic component (mobility waypoint choice, radio loss, attack drop decisions, traffic jitter). Do not rely on `random` module globals and do not rely on SimPy to seed anything. `AGENTS.md:72-74` — "every run is driven by an explicit integer seed. Same seed ⇒ identical traces."
- Also avoid iterating over a `set` when order affects behaviour — that is the classic source of "identical runs differ" (`AGENTS.md:175-176`). Use `sorted(...)` on any set-derived ordering.

**Python 3.11.8 — minor, but relevant:**
- `tomllib` is available in the stdlib (3.11+), so a `pyproject.toml` can be read without a dependency.
- Exception groups (`except*`) and `asyncio.TaskGroup` exist — useful if the optional dashboard or an async ingestion path is ever needed, but not required by the specified pipeline.
- `datetime.UTC` alias exists; prefer `datetime.timezone.utc` only if you must support 3.10.

**Windows filesystem traps:**
- Repo root path contains **spaces** — always quote in shell commands.
- `.gitignore` uses forward slashes; Git on Windows handles that fine.
- Windows file locking can make `pandas` fail to write a CSV that is still open in Excel — close the file before regenerating, or write to a temp name and rename.
- Long paths: keep trace output paths shallow; do not nest `traces/<scenario>/<seed>/<window>/` excessively.

## Rules for future implementers

1. **Python only.** No `.cpp`, no `.h`, no `setup.py` with `ext_modules`, no `pybind11`, no CMakeLists, no NS-3 submodule. `AGENTS.md:25,30-31`.
2. **Stay inside the prescribed layout** (`AGENTS.md:113-124`, `MANET_IDS_BTech_Execution_Guide.md:160-173`): `simulator/`, `attacks/`, `scenarios/`, `traces/`, `data/`, `feature_extraction/`, `ml/`, `results/`, `dashboard/`, `docs/`. Do not invent `src/`, `lib/`, `tests/` at the root — if you need a test directory, put it inside the owning package (e.g. `simulator/tests/`) so the layout in `AGENTS.md` stays true.
3. **Respect the import boundary:** `simulator/` must **not** import `attacks/` (`AGENTS.md:67-69`). Attack behaviour is injected by the scenario runner. This is what keeps the simulator attack-agnostic and lets the same code produce the clean baseline.
4. **No new runtime dependencies without a decision.** The stack above is sufficient for the whole specified scope (simulator → features → DT/RF/SVM → response → plots). Adding a package requires an explicit decision recorded in both `AGENTS.md` and `MANET_IDS_BTech_Execution_Guide.md` in the same commit (`AGENTS.md:14-16`, `AGENTS.md:36-37`).
5. **Create `requirements.txt` with exact pins** before the first simulation run (see Manifest gap). `python -m pip install -r requirements.txt`, never bare `pip`.
6. **Every number in a report or README must trace to a saved run + its config** (`AGENTS.md:151`, `MANET_IDS_BTech_Execution_Guide.md:320`). Store per-run records under `results/` and keep the scenario JSON that produced them.
7. **Keep `AGENTS.md` and `MANET_IDS_BTech_Execution_Guide.md` in sync.** Where they conflict, `AGENTS.md` wins on engineering rules and the guide wins on project specification (`AGENTS.md:14-16`). Change one → change the other in the same commit.
8. **Do not skip the gates** (`AGENTS.md:134-138`): (1) no ML work until normal AODV runs repeatably, (2) no detector until the attack demonstrably changes measurable behaviour, (3) data → baseline model → comparison → generalization, in that order.
9. **Report the full metric set** — precision, recall, F1, false-positive rate, confusion matrix — never accuracy alone (`AGENTS.md:148-149`, `MANET_IDS_BTech_Execution_Guide.md:261`).
10. **Keep generated data out of git.** `traces/`, `data/`, and bulk `results/` stay ignored; only `results/plots/` is committable (`.gitignore:1-7`).

---

*Stack analysis: 2026-10-22 — derived from `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md`, `.gitignore`, and direct inspection of the installed Python 3.11.8 environment. No packages were installed and no network/package-manager write commands were run.*
