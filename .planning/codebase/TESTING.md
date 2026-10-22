# Testing Patterns

**Analysis Date:** 2026-10-22

> **Status legend.**
> - **[IMPLEMENTED]** — exists in the repo today, verified by reading the file.
> - **[SPECIFIED]** — mandated or directed by `AGENTS.md` / `MANET_IDS_BTech_Execution_Guide.md`, with the intended repo-relative path. **Not yet built.**
>
> **Verified repo contents (2026-10-22):** `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md`, `.gitignore`, and a git repo on branch `main` with one commit (`2246d39`) and **no remote configured**. **There is no test file, no test directory, no `conftest.py`, no `pytest.ini`/`pyproject.toml`/`tox.ini`, no `requirements.txt`, and no CI.** Every test described below is **[SPECIFIED]** — a rule to implement, not an existing test.

---

## Executive summary — this project has two kinds of "tests"

1. **The evaluation-integrity protocol suite** — the rules that decide whether a *result is valid*. This is the project's primary test doctrine and it is fully specified today by `AGENTS.md:140-151` and `MANET_IDS_BTech_Execution_Guide.md:255-261, 311-320`. It exists conceptually before any test framework does.
2. **Unit / integration / E2E tests (pytest)** — the machinery. It is currently **absent**: pytest 9.0.2 is installed but undeclared, no test exists.

**A result that fails the protocol suite is not a result.** The two suites are not alternatives — the protocol suite must be expressed as executable tests (§ The evaluation-integrity protocol suite).

---

## Test Framework

**Runner:**

- **pytest 9.0.2** — installed in the environment (`pytest` and `pytest-cov` 7.1.0 are both importable), but **not declared in any manifest** and **not referenced by any file in the repo**. There is no test file at all.
  - **Evidence pytest is the intended runner:** `.gitignore:15` ignores `.pytest_cache/`, and `.gitignore:16` ignores `.ipynb_checkpoints/` — a Python-testing + notebook workflow. No other test runner is ignored (no `.tox/`, no `.nox/`, no `htmlcov/`).
  - **Recommended** `requirements.txt` addition (exact pin, per `AGENTS.md:107` and the pinning rule in `.planning/codebase/STACK.md:121-139`): `pytest==9.0.2` and `pytest-cov==7.1.0` — added when the suite actually lands, not before.
- **pytest-asyncio 1.3.0** is installed but **irrelevant** — this project has no async code; the simulator is a synchronous SimPy discrete-event loop. **Do not use `@pytest.mark.asyncio`** and do not add an `asyncio_mode` setting.
- **pytest-mock is NOT installed. hypothesis is NOT installed.** Use stdlib `unittest.mock` and plain `pytest.mark.parametrize` rather than adding dependencies (`AGENTS.md:155` scope discipline; no new dependency without a decision recorded in both root docs — `AGENTS.md:14-16`).
- **No `unittest`-only suite, no `nose`, no Selenium, no Playwright, no snapshot testing.** Not needed and not specified.

**Assertion Library:**

- **[SPECIFIED]** pytest's built-in bare `assert`. Do **not** subclass `unittest.TestCase` and do **not** use `assertEqual`/`assertTrue` — bare `assert` gives pytest's introspection and rewrite output.
- **[SPECIFIED]** Use `pytest.raises(...)` for exceptions, `pytest.approx(...)` for floats, `pytest.mark.parametrize` for matrices, and `pytest.mark.skip`/`skipif` only for genuinely environment-dependent cases (never to silence a failure).

**Config:**

- **[IMPLEMENTED]** None. No `pytest.ini`, no `pyproject.toml` `[tool.pytest.ini_options]`, no `tox.ini`, no `setup.cfg`, no `conftest.py`.
- **[Recommended]** Create `pyproject.toml` at the repo root with:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  pythonpath = ["."]          # makes `from simulator...` work without installing
  addopts = "-q -m 'not slow'"
  markers = ["slow: end-to-end acceptance-chain tests (minutes, not seconds)"]
  ```
  `pythonpath` requires pytest ≥ 7 (9.0.2 is installed) and removes the need for `sys.path` hacks in `conftest.py`. If `pyproject.toml` is created, it must also carry the pinned dependency list (the manifest gap recorded in `.planning/codebase/STACK.md:121-139`).

**Run Commands:**

```bash
python -m pytest                                  # run all (fast: excludes `slow`)
python -m pytest tests/ -v                        # verbose
python -m pytest tests/simulator -k aodv          # filter by path and name
python -m pytest -x -q                            # fail fast
python -m pytest -m slow                          # run the acceptance-chain E2E test
python -m pytest --cov=simulator --cov=attacks --cov=feature_extraction --cov=ml \
                  --cov-report=term-missing      # coverage
```

- **[SPECIFIED]** Invoke as **`python -m pytest`**, not bare `pytest` — the same interpreter-matching reason as `python -m pip` over bare `pip` (`AGENTS.md:107`).

---

## The evaluation-integrity protocol suite (PRIMARY doctrine)

This is the part that is genuinely this project's test spec today. Each rule is a check that must fail loudly when violated. Rule ids below are local to this document; the source column is authoritative.

| Id | Rule | Source | Executable check (what the test asserts) |
|---|---|---|---|
| **E1** | **Never split by random rows.** Rows from one simulation run are correlated; a random row split inflates scores. Hold out by **scenario / seed / configuration**. | `AGENTS.md:142-143`, `MANET_IDS_BTech_Execution_Guide.md:122, 314` | `tests/protocol/test_split_protocol.py::test_train_test_groups_are_disjoint` — `set(train[group_col]) & set(test[group_col]) == set()`. `::test_no_run_id_appears_in_both_splits`. `::test_split_helper_rejects_row_strategy` — the split helper raises if asked for a row-level split, so a random split cannot be introduced by accident. Use `sklearn.model_selection.GroupShuffleSplit` / `StratifiedGroupKFold` with group = run id (scenario × seed). |
| **E2** | **No leakage features.** No `is_attacker` column, or any field derived from the attack config rather than from observed traffic. | `AGENTS.md:145-146`, `MANET_IDS_BTech_Execution_Guide.md:315` | `tests/feature_extraction/test_no_leakage.py::test_feature_columns_match_schema` — columns are exactly the 9 prescribed features + `label` (`MANET_IDS_BTech_Execution_Guide.md:106-117`). `::test_no_attacker_identity_column` — no column matches `attacker|is_attack|attack_type|malicious|is_blackhole|is_grayhole|target`. `::test_features_are_invariant_to_attacker_identity` — build the feature table twice from the *same* trace, once with the scenario marking node 1 as the attacker and once marking node 2; the **feature columns must be byte-identical**, only `label` may differ. This is the strongest form of the check and the one worth writing. |
| **E3** | **Never report accuracy alone.** Always precision, recall, F1, false-positive rate, and a confusion matrix. | `AGENTS.md:148-149`, `MANET_IDS_BTech_Execution_Guide.md:257-261` | `tests/protocol/test_metrics_report.py::test_report_contains_full_metric_set` — the report dict/table contains `precision`, `recall`, `f1`, `false_positive_rate`, `confusion_matrix` for every classifier. `::test_accuracy_only_report_is_rejected` — the report builder raises when handed a metric set lacking any of the five. `::test_confusion_matrix_shape_matches_classes`. |
| **E4** | **Always compare against plain AODV without IDS.** Report PDR, throughput, end-to-end delay, packet loss, routing overhead **for both**. | `AGENTS.md:150-151`, `MANET_IDS_BTech_Execution_Guide.md:258, 319` | `tests/protocol/test_baseline_comparison.py::test_comparison_requires_matched_baseline_row` — the comparison builder refuses to emit a table when a matched IDS-OFF run for the same scenario+seed is absent. `::test_comparison_covers_five_network_metrics` — the table has PDR, throughput, end-to-end delay, packet loss, routing overhead columns, for both IDS OFF and IDS ON. `::test_ons_and_off_use_identical_scenario_and_seed`. |
| **E5** | **Every number in the report/README must trace to a saved experiment run + its config.** | `AGENTS.md:151`, `MANET_IDS_BTech_Execution_Guide.md:320` | `tests/protocol/test_provenance.py::test_every_metric_row_carries_a_resolvable_run_id` — each metric row has a `run_id` that resolves to a file under `results/` plus a scenario JSON path and a seed. `::test_saved_record_contains_config_hash`. |
| **E6** | **Determinism.** Every run driven by an explicit integer seed; same seed ⇒ identical traces. | `AGENTS.md:72-74`, `AGENTS.md:175-176` | `tests/simulator/test_determinism.py::test_same_seed_same_trace_bytes` — run the same tiny scenario twice with the same seed, assert **byte-identical** trace CSV. `::test_different_seed_produces_different_trace`. `::test_no_set_iteration_leaks_into_output` — a static AST scan of `simulator/` for `for … in <set-expression>` / iteration over an unordered container, plus a golden-output stability check. |
| **E7** | **Gate 2 — the attack must demonstrably change measurable network behaviour** before any detector is attempted. | `AGENTS.md:137`, `MANET_IDS_BTech_Execution_Guide.md:203, 318` | `tests/attacks/test_attack_effect.py::test_blackhole_reduces_pdr_vs_baseline` — same scenario+seed, PDR drops by a stated margin (e.g. > 5 percentage points). `::test_grayhole_reduces_pdr`. `::test_attack_does_not_change_trace_schema`. If this test fails, the **attack implementation is wrong** — do not train anything. |
| **E8** | **Gate 1 — the normal AODV simulation runs repeatably with sensible output.** | `AGENTS.md:136`, `MANET_IDS_BTech_Execution_Guide.md:154-156, 187-189` | `tests/simulator/test_baseline_aodv.py::test_packets_reach_destinations`; `::test_pdr_falls_with_distance`; `::test_hop_count_grows_with_distance`; `::test_routing_overhead_is_non_zero`; `::test_repeated_runs_are_stable`. |
| **E9** | **Import boundary — `simulator/` must not import `attacks/`.** | `AGENTS.md:67-69` | `tests/test_boundaries.py::test_simulator_does_not_import_attacks` — static AST scan of `simulator/**/*.py` for imports resolving to `attacks`. `::test_feature_extraction_does_not_import_simulator`. `::test_ml_does_not_import_simulator_or_attacks`. |
| **E10** | **Seeded RNG only** — no module-level `random` calls in library code. | `AGENTS.md:72-74` | `tests/test_boundaries.py::test_no_unseeded_random_calls` — AST scan of `simulator/`, `attacks/` for `random.<fn>()` calls that are not on an injected `random.Random` instance. |

> **How to use this table.** Each row is a *test to write*, not a test that exists. The rule ids map to future phase plans: a phase that touches `ml/` must add/extend the E1–E5 checks; a phase that touches `attacks/` must extend E7; a phase that touches `simulator/` must extend E6, E8, E9, E10.

---

## The gates (do not skip ahead)

`AGENTS.md:134-138`, `MANET_IDS_BTech_Execution_Guide.md:189, 203`.

| Gate | Rule | What must be true to pass | The check that proves it |
|---|---|---|---|
| **Gate 0** | No ML work until the normal AODV simulation runs repeatably with sensible output. | The simulator runs, packets reach destinations, metrics are plausible, and repeated runs agree. | E8 + E6 |
| **Gate 1** | No detector until the attack demonstrably changes measurable network behaviour. | Blackhole/grayhole measurably reduces PDR (and changes delay/throughput) versus baseline on the same scenario+seed. | E7 |
| **Gate 2** | Data generation → baseline model → comparison → generalization, **in that order**. | The dataset exists, a baseline classifier is trained, it is compared against others, and it is then tested on unseen seeds/configurations. | E1 + E3 + E4, plus `tests/ml/test_generalization.py` |
| **Checkpoint** | **Mentor checkpoint rule:** at the end of each week freeze a working version. If an advanced feature threatens the core demonstration, cut the advanced feature and keep the baseline. | The committed tree on `main` runs the acceptance chain end to end. | E11 (acceptance chain), run manually at the checkpoint |

**Gate discipline rule for implementers:** a gate is a *stopping condition*, not a formality. When a gate is unmet, the correct next action is to fix the layer below it — not to start the layer above it anyway. The known failure points in § Known failure points → diagnosis are all symptoms of skipping a gate.

---

## Known failure points → diagnosis

Reproduced from `AGENTS.md:169-177` and `MANET_IDS_BTech_Execution_Guide.md:311-320`. **Check this table before debugging anything else** — every row below has a named root cause, and the diagnosis is a rule violation, not a code bug.

| Observed symptom | Diagnosis | Rule violated | Check to run |
|---|---|---|---|
| Model looks great on test data | Suspect **random row split** or **leakage** | E1 / E2 (`AGENTS.md:142-146`) | `tests/protocol/test_split_protocol.py`, `tests/feature_extraction/test_no_leakage.py` |
| Accuracy high but recall terrible | **Class imbalance**; report the full metric set | E3 (`AGENTS.md:148-149`) | `tests/protocol/test_metrics_report.py` — assert F1/recall/FPR are all present and sane |
| Attack has no measurable effect | The **attack implementation is wrong**; validate the attack *before* training anything | Gate 1 (`AGENTS.md:137`) | `tests/attacks/test_attack_effect.py` |
| Results change between identical runs | Missing **explicit seed** and/or **non-deterministic iteration order over sets** | E6 (`AGENTS.md:72-74`, `AGENTS.md:175-176`) | `tests/simulator/test_determinism.py` |
| "ML improves the network" but no baseline table | The **baseline-comparison rule was violated**; the claim is unverifiable | E4 (`AGENTS.md:150-151`) | `tests/protocol/test_baseline_comparison.py` |
| Too little data | Generate multiple independent seeds and configurations | `MANET_IDS_BTech_Execution_Guide.md:316` | `tests/ml/test_dataset.py::test_dataset_spans_multiple_seeds` |
| Overfitting / excellent test accuracy on nearly identical simulations | Not proof of robustness — test on unseen seeds, node counts, mobility conditions | `MANET_IDS_BTech_Execution_Guide.md:220-225, 317` | `tests/ml/test_generalization.py` |
| Unverified numbers in the report | Every number must trace back to a saved experiment | E5 (`AGENTS.md:151`) | `tests/protocol/test_provenance.py` |

---

## Test File Organization

**Location:**

- **[SPECIFIED — recommended]** A **`tests/` package at the repo root**, mirroring the source tree:
  ```text
  tests/
  ├── conftest.py                 # shared fixtures: tiny scenario builder, seeded rng, tmp paths
  ├── factories.py                # scenario / trace-row / feature-table factories
  ├── protocol/                   # E1–E5 — the evaluation-integrity suite
  │   ├── test_split_protocol.py
  │   ├── test_metrics_report.py
  │   ├── test_baseline_comparison.py
  │   └── test_provenance.py
  ├── simulator/                  # E6, E8, E9, E10
  │   ├── test_mobility.py
  │   ├── test_radio.py
  │   ├── test_aodv.py
  │   ├── test_traffic.py
  │   ├── test_metrics.py
  │   ├── test_determinism.py
  │   └── test_baseline_aodv.py
  ├── attacks/                    # E7
  │   ├── test_blackhole.py
  │   └── test_grayhole.py
  ├── feature_extraction/         # E2
  │   ├── test_extract_features.py
  │   └── test_no_leakage.py
  ├── ml/                         # E1, E3, E4
  │   ├── test_train.py
  │   ├── test_evaluate.py
  │   ├── test_generalization.py
  │   └── test_dataset.py
  ├── test_boundaries.py          # E9, E10 — static import / RNG scans
  └── test_acceptance_chain.py    # E11 — the deliverable's definition of success
  ```
- **Rationale for the root `tests/` directory:** the protocol suite spans packages (it imports `simulator/` + `attacks/` + `feature_extraction/` + `ml/` together), so it cannot live inside any one package's test dir. A single root `tests/` keeps one obvious entry point and matches pytest's default `rootdir` collection.
- **Known tension (must be resolved explicitly):** `AGENTS.md:113-124` lists the top-level layout and does **not** include `tests/`; `.planning/codebase/STACK.md:198` suggests per-package test dirs (e.g. `simulator/tests/`) to keep the layout exact. **Decision:** use the root `tests/` layout above, and **add `tests/` to the layout block in `AGENTS.md` in the same commit** (`AGENTS.md:14-16`). If a per-package layout is preferred instead, `tests/simulator/` → `simulator/tests/` etc. and the same `AGENTS.md` update is required — but then the cross-package protocol suite still needs a home.
- **[SPECIFIED]** `tests/` must be **committed** (it is code). It is not covered by any current ignore rule; `.gitignore:9-16` already ignores `__pycache__/`, `*.py[cod]`, `*.egg-info/`, `.venv/`, `venv/`, `.pytest_cache/`, `.ipynb_checkpoints/`.

**Naming:**

- **[SPECIFIED]** `test_<module>.py` — matches the module under test (`simulator/aodv.py` → `test_aodv.py`).
- **[SPECIFIED]** Test functions: `test_<behaviour>_<expectation>` in `snake_case`, and **the expectation must be in the name** — `test_blackhole_reduces_pdr_vs_baseline`, not `test_blackhole`. A reader who sees only the test name should learn the invariant.
- **[SPECIFIED]** Use pytest's default discovery patterns: files matching `test_*.py` or `*_test.py`; functions matching `test_*`. Do not write custom `pytest_collect_file` hooks.

**Structure:**

See the tree above. One `conftest.py` per directory is allowed, but keep fixtures in the **nearest** `conftest.py` that owns them.

---

## Test Structure

**Suite Organization:**

```python
"""Blackhole must reduce packet delivery relative to the clean baseline.

Both runs use the same scenario and the same seed, so the only difference is
the injected attack behaviour. See AGENTS.md:86-87 (the attack's effect must
live in the network behaviour) and AGENTS.md:137 (gate 1).
"""

from simulator.run_scenario import run_scenario
from simulator.metrics import compute_metrics


def test_blackhole_reduces_pdr_vs_baseline(tiny_scenario, tmp_path):
    baseline = compute_metrics(run_scenario(tiny_scenario, seed=1, out=tmp_path / "base"))
    attacked = compute_metrics(
        run_scenario(tiny_scenario, seed=1, out=tmp_path / "attack", attack="blackhole")
    )

    assert attacked.pdr < baseline.pdr - 0.05
```

**Patterns:**

- **[SPECIFIED]** **Setup via pytest fixtures, never `setUp` methods.** Use `tmp_path` for anything a test writes; a test must never write into `traces/`, `data/`, or `results/`.
- **[SPECIFIED]** **Keep simulation fixtures tiny.** 3–6 nodes, 1 flow, 5–10 simulated seconds. The full workload is cheap (`AGENTS.md:78-80`: 50 nodes / 8 flows / 10 pps / 300 s simulated = 0.83 s wall, ~70k events/sec), but the suite should still run in seconds, not minutes.
- **[SPECIFIED]** **Assert on the metric, not on log output.** Parse the returned metrics or the written artifact; never assert on a printed string.
- **[SPECIFIED]** Use `pytest.mark.parametrize` for small matrices (node count, mobility speed, drop probability, seed) rather than one test per case.
- **[SPECIFIED]** **Test both the happy path and the boundary**: zero flows, a single node, a node that never moves, a window with no packets (division-by-zero guard in every rate metric).
- **[SPECIFIED]** **Every test must be independent** — no ordering dependencies, no shared mutable state, no reliance on a previous test's artifacts. A test that only passes after another test ran is a bug.
- **[SPECIFIED]** **Float comparisons:** use `pytest.approx(expected, rel=0.01, abs=1e-3)` for network metrics. Never assert exact float equality for metrics. **Do** assert exact byte equality for the determinism check (E6).

---

## Mocking

**Framework:**

- **[SPECIFIED]** stdlib `unittest.mock` (`monkeypatch`, `unittest.mock.patch`). **pytest-mock is not installed** and must not be added without a decision.
- **[SPECIFIED]** Prefer **fakes and injection over patching**: the simulator already takes an injected attack object and an injected `rng` — use that seam instead of monkeypatching module attributes.

**Patterns:**

```python
import pytest
from pathlib import Path


def test_run_scenario_rejects_missing_scenario_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_scenario(Path(tmp_path) / "does_not_exist.json", seed=1, out=tmp_path)


def test_invalid_scenario_fails_before_simulation_starts(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"nodes": -1}), encoding="utf-8")

    with pytest.raises(ValueError, match="nodes"):
        run_scenario(bad, seed=1, out=tmp_path)
```

**What to Mock:**

- Only slow, external, or non-deterministic things: a specific clock value, an external file read, `sys.argv` for CLI parsing.
- Filesystem writes: use `tmp_path`, **not** a mock.
- Time: inject a fixed window (`window_start`, `window_end`) into metric functions rather than freezing the clock.

**What NOT to Mock (hard rules for this project):**

- **Do NOT mock the simulator, the attack behaviour, the RNG, or the metric computation.** Mocking the simulator turns an integration test into a test of the mock; mocking `random` breaks the determinism contract under test; mocking `compute_pdr` means the thing under test is never executed.
- **Do NOT patch `simulator.aodv.AodvNode.handle_rreq` to fake a blackhole.** Use the real `attacks/blackhole.py` injection — that is precisely the seam `AGENTS.md:61-69` created.
- **Do NOT patch `random.Random` to force a draw.** Pass `seed=`.
- **Do NOT patch `simulator.metrics.*`** in a metrics test.
- **DO** use `monkeypatch.setenv`/`setattr` for CLI-level configuration.

---

## Fixtures and Factories

**Test Data:**

```python
# tests/conftest.py
import json
import random
from pathlib import Path

import pytest


@pytest.fixture
def tiny_scenario(tmp_path: Path) -> Path:
    """3 nodes, 1 flow, 10 simulated seconds — enough to exercise AODV."""
    config = {
        "nodes": 3,
        "area": {"x": 100.0, "y": 100.0},
        "mobility": {"model": "random_waypoint", "speed": 1.0},
        "traffic": {"flows": [{"src": 0, "dst": 1, "rate_pps": 2, "payload_bytes": 512}]},
        "duration_s": 10.0,
    }
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


@pytest.fixture
def seeded_rng() -> random.Random:
    """Deterministic RNG for tests. Never use the `random` module globals."""
    return random.Random(1234)
```

**Location:**

- **[SPECIFIED]** `tests/conftest.py` for cross-suite fixtures; `tests/<package>/conftest.py` for package-local ones. Fixtures live in the **nearest** `conftest.py` that owns them; do not import fixtures across packages.
- **[Recommended]** `tests/factories.py` for **factories** (functions that build a value with parameters) and `tests/conftest.py` for **fixtures** (functions that provide a ready-to-use value). Do not put factory logic in `conftest.py`.

**Factory pattern:**

```python
# tests/factories.py
def make_scenario(tmp_path, **overrides) -> Path:
    config = {"nodes": 5, "area": {"x": 100.0, "y": 100.0},
              "mobility": {"model": "random_waypoint", "speed": 1.0},
              "traffic": {"flows": []}, "duration_s": 10.0}
    config.update(overrides)
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path
```

- **[SPECIFIED]** **The label source in a test fixture is the scenario config — never a hard-coded column.** When a test needs an attack, the scenario JSON carries the attack block and the *test* reads the expected label from that same config. This mirrors the production rule (`AGENTS.md:84-85`) and stops the test suite itself from encoding a leak.
- **[SPECIFIED]** A test that needs a ground-truth label must build it the way production does — from the scenario — or the test is asserting against a different contract than the system uses.

---

## Coverage

**Requirements:**

- **[IMPLEMENTED]** None enforced. There is no `pytest-cov` configuration, no `coverage` config (`.coveragerc`, `pyproject.toml [tool.coverage]`), no coverage badge, and no CI to fail a threshold. `pytest-cov` 7.1.0 and `coverage` 7.13.5 are installed but undeclared.
- **[Recommended]** Once the suite exists, set floors in `pyproject.toml`:
  | Package | Suggested floor | Rationale |
  |---|---|---|
  | `simulator/` | 80% line | the AODV/metrics core; gate 1 and gate 2 depend on it |
  | `attacks/` | 80% | two small modules; the effect test must be meaningful |
  | `feature_extraction/` | 85% | the feature schema and the leakage guard are the contract |
  | `ml/` | 70% | pipeline shape and metric computation, not hyper-parameter branches |
- **Coverage is a floor, not a goal.** The protocol suite (E1–E10) matters more than a percentage — a 95%-covered suite that never checks the split protocol is worthless for this project.

**View Coverage:**

```bash
python -m pytest --cov=simulator --cov=attacks --cov=feature_extraction --cov=ml \
                  --cov-report=term-missing
python -m pytest --cov=simulator --cov-report=html    # writes htmlcov/
```

- **[SPECIFIED]** **`.gitignore` gap:** `htmlcov/`, `.coverage`, and `.coverage.*` are **not** currently ignored (`.gitignore:9-16` lists only `__pycache__/`, `*.py[cod]`, `*.egg-info/`, `.venv/`, `venv/`, `.pytest_cache/`, `.ipynb_checkpoints/`). **Add them in the same commit that turns coverage on**, so the artifact policy stays accurate (`.gitignore` *is* the artifact policy).

---

## Test Types

**Unit Tests:**

- Pure functions with no I/O and no simulation: metric math in `simulator/metrics.py`, windowing and feature math in `feature_extraction/`, the metric computation in `ml/`, scenario-config validation, and the attack drop-probability logic in `attacks/`.
- Target: under 50 ms each; no fixture may start a SimPy clock.

**Integration Tests:**

- In-process, real components, real files:
  - Run a tiny scenario end to end through `simulator/` and assert on the written trace and the returned metrics.
  - Inject `attacks/blackhole.py` and assert the PDR drop (E7).
  - Run `feature_extraction/` over a real trace CSV into a `tmp_path` feature CSV and assert the schema.
  - Train a `DecisionTreeClassifier` on a small synthetic feature table and assert the metric set (E3).
  - Assert the trace file has the prescribed header (`AGENTS.md:81-83`).

**E2E Tests:**

- **[SPECIFIED]** The **acceptance chain** is the deliverable's definition of success (`AGENTS.md:163-166`, `MANET_IDS_BTech_Execution_Guide.md:379`):
  `launch simulation → generate normal/attack traffic → extract features → run trained IDS → identify malicious node → trigger response → show measurable improvement vs. baseline AODV`
- Implement it as **one** test, `tests/test_acceptance_chain.py::test_full_chain_improves_over_baseline`, marked `@pytest.mark.slow` and excluded by the default `addopts` (`-m 'not slow'`). Run it explicitly with `python -m pytest -m slow` — it is the pre-report verification step.
- It must assert: the trained IDS flags the injected attacker; re-running the same scenario with the response enabled yields **higher PDR** than the baseline run (E4).
- **Not used:** browser tests, load tests, snapshot testing. If the optional `dashboard/` is ever built, browser testing may be added — but not now (`AGENTS.md:166-167`).

---

## Common Patterns

**Async Testing:**

- **Not applicable.** There is no async code. The simulator is a synchronous SimPy discrete-event loop driven by `env.process` / `env.timeout` (`AGENTS.md:49-50`). Do not add `@pytest.mark.asyncio`, `asyncio_mode`, or any `pytest-asyncio` configuration — `pytest-asyncio` happens to be installed and that is not a reason to use it.

**Error Testing:**

```python
def test_missing_scenario_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_scenario(tmp_path / "nope.json", seed=1, out=tmp_path)


def test_invalid_scenario_config_fails_fast(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"nodes": -1}), encoding="utf-8")

    with pytest.raises(ValueError, match="nodes"):
        run_scenario(bad, seed=1, out=tmp_path)
```

- **[SPECIFIED]** Use `pytest.raises(ExcType)` with a `match=` on the message. **Never `pytest.raises(Exception)`** — it is too broad and hides the wrong-exception bug. Assert the **specific** type.
- **[SPECIFIED]** A bad config must raise **before any simulated time is consumed**. A test that must wait 300 simulated seconds to fail has the wrong error boundary.
- **[SPECIFIED]** Test the CLI's exit codes too (`2` for invalid input, `130` for interrupt) with `subprocess.run([...], returncode=...)` or `pytest.raises(SystemExit)`.

**Determinism Testing:**

```python
def test_same_seed_produces_identical_trace(tiny_scenario, tmp_path):
    a = run_scenario(tiny_scenario, seed=7, out=tmp_path / "a")
    b = run_scenario(tiny_scenario, seed=7, out=tmp_path / "b")

    assert (tmp_path / "a" / TRACE_FILENAME).read_bytes() == \
           (tmp_path / "b" / TRACE_FILENAME).read_bytes()
```

- **[SPECIFIED]** Assert **byte equality of the file**, not equality of parsed values — byte equality catches column-order drift, float formatting drift, and row-order drift that a parsed comparison would hide.
- **[SPECIFIED]** Also assert that a *different* seed produces a *different* trace, otherwise the "seed" is not actually wired through.

**Parametrization:**

```python
@pytest.mark.parametrize("nodes", [20, 30, 50])
@pytest.mark.parametrize("speed", [1.0, 5.0, 10.0])
def test_scenario_matrix_runs(nodes, speed, scenario_factory, tmp_path):
    scenario = scenario_factory(nodes=nodes, speed=speed)
    metrics = compute_metrics(run_scenario(scenario, seed=1, out=tmp_path))
    assert 0.0 <= metrics.pdr <= 1.0
```

- **[SPECIFIED]** Parametrize the experiment matrix axes the guide defines (E1–E8: node count, mobility speed, traffic load, drop rate) rather than writing one test per cell.

**Float and Ratio Testing:**

- **[SPECIFIED]** PDR, throughput, delay, packet loss, routing overhead are floats. Use `pytest.approx` with `rel=0.01`.
- **[SPECIFIED]** Guard the divide-by-zero: every rate metric must return `0.0` (not `NaN`) for a window with zero packets. Write that test — empty windows are common in a MANET and `NaN` silently poisons a dataset.

**Dataset and Label Testing:**

- **[SPECIFIED]** `tests/ml/test_dataset.py::test_dataset_spans_multiple_seeds_and_configs` — the built dataset contains more than one seed and more than one configuration (`MANET_IDS_BTech_Execution_Guide.md:316`).
- **[SPECIFIED]** `::test_label_values_are_from_the_allowed_set` — `label ∈ {Normal, Blackhole, Grayhole}` (`MANET_IDS_BTech_Execution_Guide.md:117`).
- **[SPECIFIED]** `::test_labels_are_joined_from_scenario_config` — the label column is reproducible from the scenario JSON alone, and **not** from any trace column (E2).

---

## Test coverage gaps (what is untested today)

Everything. This table is the work list for a future phase; each row names the file where the test will live and the file whose behaviour it protects.

| Untested area | What is not tested | Files that will exist | Risk if untested | Priority |
|---|---|---|---|---|
| **Simulator core** | No test of any kind | `simulator/mobility.py`, `simulator/radio.py`, `simulator/aodv.py`, `simulator/traffic.py`, `simulator/metrics.py` | Gate 1 can never be cleared; a broken simulator looks like a broken detector | **High** |
| **Attack effectiveness** | No proof that blackhole/grayhole change measurable behaviour | `attacks/blackhole.py`, `attacks/grayhole.py` | Training on data where the attack has no effect — the "results look great but nothing happened" case (`AGENTS.md:173-174`) | **High** |
| **Determinism** | No proof that the same seed gives the same trace | `simulator/run_scenario.py` | "Multiple seeds" in the experiment matrix is unreproducible (`AGENTS.md:74`) | **High** |
| **Split protocol** | No check that the holdout is group-aware | `ml/` training code | Inflated scores; the exact failure the contract warns about (`AGENTS.md:142-143`) | **High** |
| **Leakage guard** | No check that features are observation-only | `feature_extraction/extract_features.py` | A trivial detector; the result is worthless (`AGENTS.md:145-146`) | **High** |
| **Metric set** | No check that the full metric set is reported | `ml/` evaluation code | "Accuracy only" claims (`AGENTS.md:148-149`) | **High** |
| **Baseline comparison** | No check that IDS-OFF baseline rows exist | `ml/` comparison code | "ML improves the network" with no baseline table (`AGENTS.md:177`) | **High** |
| **Trace schema** | No check that the header matches `time, src, dst, pkt_id, type, hop_count, dropped_by, ...` | `simulator/` trace writer | A silent schema change breaks every downstream artefact | Medium |
| **Import boundaries** | No static check that `simulator/` avoids `attacks/` | `simulator/`, `attacks/` | The simulator stops being attack-agnostic; the baseline comparison becomes invalid | Medium |
| **Acceptance chain** | The full E2E chain is never run as one test | all of the above | The deliverable's definition of success is unverified (`AGENTS.md:163-166`) | Medium |
| **Model persistence** | No test that the saved model + preprocessing pipeline reload and reproduce the same predictions | `ml/` model artifact | The deliverable "trained model + preprocessing pipeline" is not reproducible (`MANET_IDS_BTech_Execution_Guide.md:127, 329`) | Medium |
| **Response mechanism** | No test that a flagged node is actually avoided in route selection | `simulator/aodv.py` route selection + response hook | The "trigger response" half of the acceptance chain is unproven | Medium |
| **Generalization** | No test on unseen seeds/configurations | `ml/` evaluation code | "Excellent test accuracy on nearly identical simulations is not proof of robustness" (`MANET_IDS_BTech_Execution_Guide.md:317`) | Medium |
| **CI** | No pipeline runs the suite | — | Regressions land silently | Low (no remote exists — `AGENTS.md:6-7`) |

---

## Specified gaps to close (and the decision each requires)

| Gap | Current state | Recommended fix | Decision needed |
|---|---|---|---|
| **pytest not a declared dependency** | pytest 9.0.2 installed, undeclared, unused | Add `pytest==9.0.2` (and `pytest-cov==7.1.0`) to a new `requirements.txt` at the repo root | Record in `AGENTS.md` + the guide in the same commit (`AGENTS.md:14-16`) |
| **No test directory** | none exists | Create root `tests/` (see § Test File Organization) | Add `tests/` to the layout block in `AGENTS.md:113-124` in the same commit |
| **No `conftest.py` / no `pythonpath`** | imports of `simulator.*` will fail from a bare pytest run | `pyproject.toml` with `[tool.pytest.ini_options] pythonpath = ["."]`, or a `sys.path` insert in `tests/conftest.py` | Pick one; prefer `pyproject.toml` (it also carries the dependency pins) |
| **No manifest at all** | no `requirements.txt`, no `pyproject.toml` | Create `requirements.txt` with exact `==` pins (see `.planning/codebase/STACK.md:121-139`) | Required before the first simulation run; `AGENTS.md:151` requires recorded versions |
| **No coverage config** | `pytest-cov` installed, unconfigured | Add `[tool.coverage.report] fail_under` and the per-package floors | Non-blocking on day one; do not fail the build until the suite exists |
| **`.gitignore` missing coverage artefacts** | `htmlcov/`, `.coverage` not ignored | Add them to `.gitignore` in the same commit that enables coverage | Keep `.gitignore` truthful — it is the artifact policy |
| **No CI** | no `.github/workflows/`, no remote configured | Do not add CI yet — there is no remote to trigger it (`AGENTS.md:6-7`) | Revisit when a remote is deliberately added |
| **No "slow" marker** | — | Define `markers = ["slow: ..."]` and `addopts = "-m 'not slow'"` when the acceptance-chain test lands | — |

---

## Rules for future implementers

1. **A result that fails the protocol suite is not a result.** Express E1–E10 as executable tests before publishing any number.
2. **Never split by random rows** — hold out by scenario/seed/configuration (`AGENTS.md:142-143`).
3. **Never let a leakage column into the feature table** (`AGENTS.md:145-146`).
4. **Never report accuracy alone** — precision, recall, F1, false-positive rate, confusion matrix, always (`AGENTS.md:148-149`).
5. **Always produce the matched IDS-OFF baseline** for the same scenario and seed (`AGENTS.md:150-151`).
6. **Every number traces to a saved run + its config** (`AGENTS.md:151`).
7. **Same seed ⇒ byte-identical trace.** Assert file bytes, not parsed values.
8. **Validate the attack before training anything** (gate 1). If the PDR does not move, the attack is broken — not the model.
9. **Check the failure-point table before debugging** (§ Known failure points → diagnosis). Every symptom there names a rule, not a code bug.
10. **Do not mock the simulator, the attack, the RNG, or the metrics.** Use the injection seams the architecture already provides.
11. **Never write into `traces/`, `data/`, or `results/` from a test** — use `tmp_path`.
12. **Keep the test suite fast.** Tiny scenarios; the acceptance chain is the only slow test and it is marked `slow`.
13. **Do not skip the gates** (`AGENTS.md:134-138`), and honour the mentor checkpoint rule — cut the advanced feature, keep the baseline (`AGENTS.md:158-159`).
14. **No new test dependency** (no `pytest-mock`, no `hypothesis`) without a decision recorded in both root docs in the same commit (`AGENTS.md:14-16`).

---

*Testing analysis: 2026-10-22 — derived from `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md`, `.gitignore`, the existing `.planning/codebase/STACK.md` and `.planning/codebase/INTEGRATIONS.md`, and direct inspection of the installed Python 3.11.8 environment (pytest 9.0.2, pytest-cov 7.1.0, pytest-asyncio 1.3.0, coverage 7.13.5, ruff 0.16.1, black 26.3.1 present; pytest-mock and hypothesis absent). No packages were installed and no network or package-manager write commands were run.*
