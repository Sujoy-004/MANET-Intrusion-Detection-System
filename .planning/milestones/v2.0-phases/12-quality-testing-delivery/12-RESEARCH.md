# Phase 12: Quality, Testing & Delivery - Research

**Researched:** 2026-11-10
**Domain:** Software Quality Assurance, Subprocess Regression Testing, Packaging Manifests, Environment Verification, and Milestone Verification Audit
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Legacy CLI & Script Regression Harness
- **D-01:** Behavioral Subprocess Pipeline with Micro-Fixtures & Invariant Checks:
  - Dedicated automated test module `tests/test_legacy_cli_compat.py` executing legacy commands (`python -m simulator.run_scenario`, `python -m ml.train`, `python -m ml.evaluate`, and key `scripts/*`) via subprocess.
  - Commands run fast micro-scenarios (e.g. 2.0s duration, miniature synthetic dataset) within isolated pytest `tmp_path` fixtures without modifying committed repository files or workspace directories.
  - Asserts exact exit codes (0 for valid runs, non-zero for invalid arguments), stdout markers, canonical `TRACE_HEADER` column sets, and metrics dictionary schemas.
  - Avoids brittle bitwise trace hashing while ensuring true functional regression safety and contractual compliance for DELV-01.
  — **Reversibility:** costly — defines regression test harness and contractual CLI behavior assertions.

#### Documentation & Milestone Lifecycle Scope
- **D-02:** Defer Documentation Overhaul to `/gsd-docs-update`:
  - User explicitly directed to defer deep documentation updates to a dedicated `/gsd-docs-update` workflow.
  - Phase 12 remains strictly focused on executable test suites, packaging manifests, and automated quality verification.
  — **Reversibility:** reversible — `/gsd-docs-update` can be invoked independently post-phase.

- **D-03:** Standard Phase 12 Verification + Defer Milestone Archiving to `/gsd-complete-milestone`:
  - Phase 12 produces its standard `12-VERIFICATION.md` capturing full test suite results (all 285+ tests), file additions/modifications, and an honest ledger of known limitations (80x24 minimum terminal geometry, Windows-verified host).
  - High-level milestone closure, retrospective logging, and milestone archive generation will be executed separately via `/gsd-complete-milestone`.
  — **Reversibility:** reversible — maintains clean separation between phase verification and milestone finalization.

#### Dependency & Packaging Integrity
- **D-04:** Pinned Manifest + AST Boundaries + Decoupled Clean-Environment Smoke Script:
  - Create root `requirements.txt` pinning exact tested versions: `simpy==4.1.2`, `networkx==3.6.1`, `scikit-learn==1.8.0`, `pandas==3.0.2`, `numpy==1.26.4`, `matplotlib==3.10.8`, `seaborn==0.13.2`, `joblib==1.5.3`, `textual==8.2.8`, and `pytest==9.0.2`.
  - Maintain and enforce AST-based import boundaries in fast, offline pytest suites (`tests/test_manet_import_boundaries.py` and `tests/test_import_boundaries.py`), verifying `manet/` never imports business packages and vice-versa.
  - Implement `scripts/verify_environment.py` as an on-demand utility to validate clean virtual environment installation and CLI/TUI entry-point viability without imposing latency on everyday unit test runs.
  — **Reversibility:** costly — standardizes external package requirements across the entire repository.

### the agent's Discretion

- Test organization and parametrization within `tests/test_legacy_cli_compat.py`.
- Internal structure and diagnostic reporting formats of `scripts/verify_environment.py`.
- Test harness isolation mechanics (e.g., using `tests/conftest.py` autouse fixtures to isolate `.manet-workspace`).

### Deferred Ideas (OUT OF SCOPE)

- Comprehensive `README.md` and `CHANGELOG.md` overhaul deferred to `/gsd-docs-update` per user decision (D-02).
- Milestone v2.0 closure, release retrospective, and milestone archiving deferred to `/gsd-complete-milestone` per user decision (D-03).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **DELV-01** | User enjoys unchanged behavior: existing CLI entry points still work, existing tests pass unweakened, and the full suite plus new feature tests (launcher/command parsing, capability detection incl. missing artifacts, scenario discovery/validation, worker success/failure/cancel/partial, manifest atomicity/checksums/history, CLI compatibility, import boundaries, bounded telemetry under load) pass on the current host | Handled by D-01 and D-04: Subprocess compatibility harness `tests/test_legacy_cli_compat.py`, hermetic workspace fixture in `tests/conftest.py`, and AST boundary verification. |
| **DELV-02** | User can follow updated README documentation for the launch command, TUI dependency installation, limitations, supported terminals, and keyboard shortcuts, and CHANGELOG.md records the feature; documentation matches executable behavior with no untested cross-platform claims | Under D-02, deep docs updates are routed to `/gsd-docs-update`. Phase 12 provides operational dependency manifest `requirements.txt` and diagnostic environment script `scripts/verify_environment.py`. |
| **DELV-03** | User gets an honest completion report: changed files, architecture and framework rationale, commands run with exact test results, and clearly listed known limitations and deferred features | Handled by D-03: Phase 12 produces `12-VERIFICATION.md` detailing all executed test counts, exact metrics, modified files, and Windows 11 / terminal geometry limitations. Milestone archiving is deferred to `/gsd-complete-milestone`. |
</phase_requirements>

## Summary

Phase 12 is the final delivery and quality assurance phase of Milestone v2.0 (Interactive TUI Application). The objective is to verify that the terminal application layer (`manet/`), delivered across Phases 7–11, integrates seamlessly with the core simulation and machine learning engines without degrading or mutating existing interfaces, and that the complete codebase is packaged with reproducible manifests, verified AST import boundaries, and an honest completion report.

During empirical investigation of the repository:
1. **Existing Test Suite Baseline:** The repository has 285 collected tests. Running the full test suite in a clean workspace yields 282 passed, 3 skipped (the 3 skipped tests are in `tests/test_manet_workspace_pruning.py` and skip gracefully when running as a non-elevated Windows user without symlink creation privileges).
2. **Workspace State Leak Discovery:** When an experiment run exists in `.manet-workspace/` (left behind by manual exploration or previous runs), `test_manet_dashboard_workspace.py` fails 2 tests because `ManetApp` checks the disk directory by default. Introducing a hermetic workspace isolation fixture via `tests/conftest.py` solves this flakiness permanently, ensuring tests run in hermetic isolation without polluting the workspace.
3. **Subprocess Behavioral Compatibility:** Probing `python -m simulator.run_scenario`, `python -m ml.train`, `python -m ml.evaluate`, and `scripts/*` via subprocess with micro-fixtures (2.0s duration, synthetic data) verified execution completes in 1–3 seconds while strictly maintaining exit codes (0 for success, non-zero for error), canonical stdout banners, and exact CSV schemas.
4. **Packaging Manifest & Verification:** Environment probing confirmed all 10 required dependencies match exact pinned versions (`simpy==4.1.2`, `networkx==3.6.1`, `scikit-learn==1.8.0`, `pandas==3.0.2`, `numpy==1.26.4`, `matplotlib==3.10.8`, `seaborn==0.13.2`, `joblib==1.5.3`, `textual==8.2.8`, `pytest==9.0.2`). Creating `requirements.txt` and `scripts/verify_environment.py` fulfills packaging and verification integrity.

**Primary recommendation:**
Plan Phase 12 in two tightly scoped execution waves:
- **Wave 1 (Manifest & Regression Harness):** Generate root `requirements.txt` with exact version equality pins; implement `tests/conftest.py` for hermetic workspace isolation; build `tests/test_legacy_cli_compat.py` executing legacy CLIs and scripts with micro-fixtures under `tmp_path`.
- **Wave 2 (Environment Verification & Phase Audit):** Implement `scripts/verify_environment.py` with standalone environment health checks; execute the complete full regression test suite (295+ tests); and generate the comprehensive `12-VERIFICATION.md` report.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CLI Compatibility & Invariant Assertion | Automated Test Suite (`tests/test_legacy_cli_compat.py`) | Subprocess execution | Executes real CLI entrypoints in isolated `tmp_path` to guarantee backwards compatibility without touching repository state. |
| Test Environment Hermeticity | Pytest Fixtures (`tests/conftest.py`) | Python runtime / monkeypatch | Isolates `.manet-workspace` and temp directories across test sessions so disk state never causes test flakes. |
| External Dependency Standardization | Packaging Manifest (`requirements.txt`) | Documentation / Setup | Authoritatively pins the 10 production dependencies with exact `==` equality pins. |
| Operational Environment Verification | Automation Script (`scripts/verify_environment.py`) | CLI Diagnostics | Validates Python 3.11+ runtime, installed dependency versions, model artifacts, and basic entrypoints on demand. |
| Presentation & Boundary Invariant Enforcement | AST Boundary Suites (`tests/test_manet_import_boundaries.py`, `tests/test_import_boundaries.py`) | Static Analysis | Statically verifies one-way dependency rules: `manet/` never imports business logic, business logic never imports `manet/`, commands never import OS execution. |
| Quality, Metrics & Limitation Reporting | Phase Verification (`.planning/phases/12-quality-testing-delivery/12-VERIFICATION.md`) | Planning artifacts | Documents exact test counts, benchmark metrics, modified files, and terminal geometry constraints honestly. |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **Python** | `3.11.8` | Windows-native runtime [VERIFIED: python.exe] | Project specification runtime; pure Python without C++ compiler toolchains. |
| **pytest** | `9.0.2` | Test runner and fixture framework [VERIFIED: python.exe] | Industry standard Python testing framework supporting `tmp_path`, `monkeypatch`, and async tests. |
| **Textual** | `8.2.8` | Full-screen TUI framework [VERIFIED: python.exe] | Milestone v2.0 presentation layer. |
| **SimPy** | `4.1.2` | Discrete-event simulation clock [VERIFIED: python.exe] | Event engine for AODV routing, packet scheduling, and mobility. |
| **NetworkX** | `3.6.1` | Graph analysis and neighbor calculation [VERIFIED: python.exe] | Link graph and routing analysis. |
| **scikit-learn**| `1.8.0` | ML classifiers and pipelines [VERIFIED: python.exe] | Intrusion detection algorithms (DecisionTree, RandomForest, SVM). |
| **pandas** | `3.0.2` | Trace and feature table processing [VERIFIED: python.exe] | Tabular data manipulation and metrics generation. |
| **numpy** | `1.26.4` | Numeric array operations [VERIFIED: python.exe] | Vector operations across simulation and ML. |
| **matplotlib** | `3.10.8` | Visualization engine (Agg backend) [VERIFIED: python.exe] | Generation of evaluation and benchmark figures. |
| **seaborn** | `0.13.2` | Statistical plotting [VERIFIED: python.exe] | Confusion matrices and comparative metric charts. |
| **joblib** | `1.5.3` | Model serialization [VERIFIED: python.exe] | Serialization of champion models and pipelines. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **subprocess** | stdlib | Out-of-process CLI invocation | Used in `tests/test_legacy_cli_compat.py` to assert external CLI contracts. |
| **ast** | stdlib | Abstract syntax tree inspection | Used in `tests/test_manet_import_boundaries.py` to enforce architecture boundaries. |
| **argparse** | stdlib | Command-line argument parsing | Used across CLI entry points and `scripts/verify_environment.py`. |
| **json** / **csv** | stdlib | Structured serialization | Used for manifests, scenario configs, and trace evaluation. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pinned `requirements.txt` | `pyproject.toml` or `poetry.lock` | Root `requirements.txt` with exact `==` pins matches existing repository rules (`GEMINI.md`) and introduces zero new toolchain overhead. |
| Subprocess CLI testing | Direct Python function invocation | Direct function invocation tests internal Python APIs but fails to verify CLI argument parsing, exit codes, and stdout/stderr output formatting. Subprocess tests external contracts faithfully. |
| Global autouse fixture | Per-test monkeypatching | Autouse fixture in `tests/conftest.py` ensures that all current and future tests run with an isolated workspace, preventing disk pollution. |

---

## Package Legitimacy Audit

All 10 external packages were verified against the active Python environment:

| Package | Registry | Installed Version | Source Repo / Author | Verdict | Disposition |
|---------|----------|-------------------|----------------------|---------|-------------|
| `simpy` | PyPI | `4.1.2` | GitLab / Onto-Med | `[OK]` | Approved [VERIFIED: python.exe] |
| `networkx` | PyPI | `3.6.1` | GitHub / networkx | `[OK]` | Approved [VERIFIED: python.exe] |
| `scikit-learn` | PyPI | `1.8.0` | GitHub / scikit-learn | `[OK]` | Approved [VERIFIED: python.exe] |
| `pandas` | PyPI | `3.0.2` | GitHub / pandas-dev | `[OK]` | Approved [VERIFIED: python.exe] |
| `numpy` | PyPI | `1.26.4` | GitHub / numpy | `[OK]` | Approved [VERIFIED: python.exe] |
| `matplotlib` | PyPI | `3.10.8` | GitHub / matplotlib | `[OK]` | Approved [VERIFIED: python.exe] |
| `seaborn` | PyPI | `0.13.2` | GitHub / mwaskom | `[OK]` | Approved [VERIFIED: python.exe] |
| `joblib` | PyPI | `1.5.3` | GitHub / joblib | `[OK]` | Approved [VERIFIED: python.exe] |
| `textual` | PyPI | `8.2.8` | GitHub / Textualize | `[OK]` | Approved [VERIFIED: python.exe] |
| `pytest` | PyPI | `9.0.2` | GitHub / pytest-dev | `[OK]` | Approved [VERIFIED: python.exe] |

**Packages removed due to `[SLOP]` verdict:** None.
**Packages flagged as suspicious `[SUS]`:** None.
**New external packages to install:** None. All packages are already installed and verified.

---

## Architecture Patterns

### System Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                            PHASE 12 DELIVERY PIPELINE                             |
+-----------------------------------------------------------------------------------+
                                          |
                +-------------------------+-------------------------+
                |                                                   |
                v                                                   v
    [Wave 1: Manifest & Tests]                          [Wave 2: Verification]
+-----------------------------------+               +-----------------------------------+
| 1. requirements.txt               |               | 1. scripts/verify_environment.py  |
|    - Exact pins (10 packages)     |               |    - Python version validation    |
|                                   |               |    - Dependency version checks    |
| 2. tests/conftest.py              |               |    - Artifact integrity checks    |
|    - Isolated tmp workspace       |               |    - CLI help / entrypoint checks |
|    - Eliminates test flakes       |               |                                   |
|                                   |               | 2. Full Test Suite Gate           |
| 3. tests/test_legacy_cli_compat.py|               |    - 285 existing + ~10 new tests |
|    - Subprocess execution         |               |    - Zero failures, 3 skipped     |
|    - Micro-fixtures (<3s each)    |               |                                   |
|    - Schema & exit code asserts   |               | 3. 12-VERIFICATION.md             |
|                                   |               |    - Test count ledger            |
| 4. tests/test_*import_boundaries  |               |    - File delta inventory         |
|    - AST boundary enforcement     |               |    - Known limitations & status   |
+-----------------------------------+               +-----------------------------------+
```

### Recommended Project Structure

```
├── requirements.txt                         # Root dependency manifest with exact == pins (D-04)
├── scripts/
│   ├── verify_environment.py                # Standalone environment health verification script (D-04)
│   ├── verify_gate2_impact.py               # Gate 2 attack verification benchmark
│   ├── run_closed_loop_benchmark.py         # Triad closed-loop QoS benchmark
│   ├── build_dataset.py                     # Dataset builder
│   └── generate_datasets.py                 # Multi-seed dataset generation
├── tests/
│   ├── conftest.py                          # Hermetic test fixtures (isolated workspace autouse)
│   ├── test_legacy_cli_compat.py            # Subprocess legacy CLI regression harness (D-01)
│   ├── test_manet_import_boundaries.py      # TUI vs business logic AST boundaries
│   ├── test_import_boundaries.py            # Simulator vs attacks AST boundaries
│   └── ...                                  # Existing 285 tests across 28 modules
└── .planning/phases/12-quality-testing-delivery/
    ├── 12-CONTEXT.md                        # User decisions
    ├── 12-RESEARCH.md                       # Phase research (this document)
    ├── 12-01-PLAN.md                        # Wave 1 implementation plan
    ├── 12-02-PLAN.md                        # Wave 2 implementation plan
    └── 12-VERIFICATION.md                   # Phase verification audit report (D-03)
```

### Pattern 1: Behavioral Subprocess Regression Testing with Micro-Fixtures (D-01)
**What:** Execute CLI entrypoints out-of-process via `subprocess.run([sys.executable, "-m", ...])` using temporary directories and miniature scenarios.
**When to use:** In `tests/test_legacy_cli_compat.py` to assert command-line interface stability, exit codes, and output contracts.
**Key elements:**
1. Use `sys.executable` and `cwd=PROJECT_ROOT` to guarantee consistent environment resolution.
2. Direct all output (`--out`) into pytest `tmp_path` fixtures so zero repository files or workspace directories are modified.
3. Use tiny durations (e.g. 2.0s for simulation) and minimal datasets (e.g. 60–100 rows for ML) to keep test execution fast (< 3s per test).
4. Assert contract properties: exit code (0 for valid, non-zero for invalid), key stdout markers (`=== Simulation Results ===`), trace header matching `SimulationRunner.TRACE_HEADER`, and metrics schema.

### Pattern 2: Hermetic Test Environment Isolation via `tests/conftest.py`
**What:** Provide pytest fixtures that isolate filesystem state across tests.
**When to use:** To prevent repository-level state (such as `.manet-workspace/` created during manual runs or previous tests) from leaking into unit tests that assert an empty initial state.
**Implementation:**
```python
# tests/conftest.py
import pytest
from pathlib import Path
from manet.adapters.workspace import WorkspaceAdapter

@pytest.fixture(autouse=True)
def isolate_test_workspace(monkeypatch, tmp_path):
    """Ensure all tests run against an isolated clean workspace directory by default."""
    clean_workspace = tmp_path / "test_workspace"
    clean_workspace.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        WorkspaceAdapter,
        "__init__",
        lambda self, workspace_root=None: setattr(
            self, "workspace_root", Path(workspace_root) if workspace_root else clean_workspace
        ) or None,
    )
```

### Pattern 3: Decoupled Health & Environment Verification (`scripts/verify_environment.py`)
**What:** A standalone Python script that inspects the runtime environment, dependencies, artifacts, and entry points on demand.
**When to use:** Used by users, CI, or developers to verify system readiness without running the 7-minute full test suite.
**Checks performed:**
- Runtime: Python >= 3.11, platform OS identification.
- Dependencies: Importability and exact version check against `requirements.txt`.
- Artifacts: Checks existence of `scenarios/*.json`, `ml/models/best_model.joblib`, `data/train.csv`, `data/test.csv`.
- Entrypoints: Quick subprocess smoke check of `--help` flags (`python -m simulator.run_scenario --help`, `python -m ml.train --help`, `python -m ml.evaluate --help`, and `python -m manet --help`).

### Anti-Patterns to Avoid
- **Bitwise Output Comparison:** Never assert bit-for-bit identity of generated floats or logs across different machines or versions. Assert schema presence, row counts, and numeric invariants instead.
- **Unbounded Simulation in Unit Tests:** Never invoke legacy scripts with full 300-second simulation runs in unit tests. Always supply micro-durations (`--duration 2.0`) or use micro-fixtures.
- **Workspace State Leakage:** Never allow tests to read or write directly to the project root `.manet-workspace/` without isolation.
- **Modifying Core Code During Delivery:** Do not touch `simulator/`, `attacks/`, `feature_extraction/`, or `ml/` algorithms during Phase 12. Quality verification verifies existing code; it does not refactor business logic.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Subprocess Execution | Custom process wrapper | `subprocess.run(..., capture_output=True, text=True)` | Handles buffers, text decoding, timeouts, and exit code capture safely across Windows and Unix. |
| Temporary Files & Directories | Custom temp folder cleanup | `pytest` `tmp_path` fixture | Built-in, guaranteed cleanup, thread-safe, and unique per test function. |
| AST Import Parsing | Regex-based `import` searching | `ast.parse` and `ast.walk` | Regex fails on multiline imports, commented-out imports, conditional imports, and string literals. |
| Dependency Resolution | Custom package manager wrapper | Plain `requirements.txt` with `==` pins | Zero dependencies, native to standard `pip`, reproducible across all Python environments. |

---

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `.manet-workspace/exp_20261110_065124_e1_normal_30n_42/` created during Phase 11 testing [VERIFIED: filesystem] | Provide hermetic isolation in `tests/conftest.py` so disk state does not leak into unit tests asserting empty workspace. |
| Live service config | None — verified pure local application | None. |
| OS-registered state | None — verified no registry keys or daemon tasks | None. |
| Secrets/env vars | None — verified zero secrets or external APIs | None. |
| Build artifacts | `.pytest_cache/`, `__pycache__/` | Ignored by `.gitignore`. |

---

## Common Pitfalls

### Pitfall 1: Leaking `.manet-workspace/` State into Tests
**What goes wrong:** Tests asserting the initial empty dashboard state (`test_full_workspace_mount_with_cards_and_rails`, `test_workspace_empty_vs_populated_mounting`) fail with `AssertionError: isinstance(RecentExperimentsTable, CtaHeroPanel)`.
**Why it happens:** When an experiment run is executed in the application or by manual testing, `.manet-workspace/` retains that directory. `ManetApp` defaults to inspecting `get_project_root() / ".manet-workspace"`, detecting existing runs and mounting the table instead of the hero CTA panel.
**How to avoid:** Define an autouse fixture in `tests/conftest.py` that defaults `WorkspaceAdapter.workspace_root` to `tmp_path / "test_workspace"` for unit tests.
**Warning signs:** Tests pass on a completely fresh checkout but fail after running `python -m manet` or running an experiment.

### Pitfall 2: Slow Subprocess Execution in Unit Tests
**What goes wrong:** A test suite taking 5–10 minutes to run because subprocess tests execute full-length simulations (300.0s) or full 5-fold cross validation.
**Why it happens:** Default CLI parameters in scripts specify full benchmark workloads.
**How to avoid:** In `tests/test_legacy_cli_compat.py`, pass micro-fixtures: a 2.0s scenario duration, `--subsample 100`, or a 60-row synthetic dataset.
**Warning signs:** Individual test functions taking > 5 seconds to complete.

### Pitfall 3: Relative Path Drift During Subprocess Invocation
**What goes wrong:** Subprocess fails with `FileNotFoundError: scenarios/e1_normal_30n.json` or writes files into unintended directories.
**Why it happens:** Subprocess inherits the working directory of the caller, or uses relative paths that do not resolve if `cwd` is altered.
**How to avoid:** Always pass `cwd=str(PROJECT_ROOT)` and use explicit absolute paths or paths resolved relative to `PROJECT_ROOT` when invoking CLI commands via subprocess.

### Pitfall 4: Refit Path Hardcoding in `ml/evaluate.py`
**What goes wrong:** Calling `python -m ml.evaluate` with a custom `--models-dir` and `--test-csv` can fail if `"data/train.csv"` is not present.
**Why it happens:** Line 494 of `ml/evaluate.py` passes `train_csv_path="data/train.csv"` to `refit_with_probability`.
**How to avoid:** In tests verifying `ml.evaluate`, either ensure `data/train.csv` is accessible or pass test paths that satisfy the refit contract.

---

## Code Examples

### 1. `tests/test_legacy_cli_compat.py` Micro-Fixture Subprocess Test Pattern
```python
"""Regression tests verifying legacy CLI entrypoints and contracts remain intact."""

import json
from pathlib import Path
import subprocess
import sys
import pandas as pd
import pytest

from simulator.run_scenario import SimulationRunner
from feature_extraction.extract_features import SCHEMA_COLUMNS

_REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def micro_scenario(tmp_path: Path) -> Path:
    """Create a minimal 2.0s scenario configuration in tmp_path."""
    base_cfg_path = _REPO_ROOT / "scenarios" / "e1_normal_30n.json"
    with open(base_cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["duration"] = 2.0
    scenario_path = tmp_path / "micro_scenario.json"
    with open(scenario_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return scenario_path


def test_simulator_cli_run_scenario_success(micro_scenario: Path, tmp_path: Path):
    """Verify python -m simulator.run_scenario succeeds with valid exit code and schema."""
    trace_path = tmp_path / "trace.csv"
    cmd = [
        sys.executable,
        "-m",
        "simulator.run_scenario",
        "--scenario",
        str(micro_scenario),
        "--seed",
        "42",
        "--out",
        str(trace_path),
    ]
    res = subprocess.run(cmd, cwd=str(_REPO_ROOT), capture_output=True, text=True)
    assert res.returncode == 0, f"CLI failed: {res.stderr}"
    assert "=== Simulation Results ===" in res.stdout
    assert "Packet Delivery Ratio (PDR):" in res.stdout
    assert trace_path.is_file()

    # Validate trace schema
    df = pd.read_csv(trace_path)
    assert list(df.columns) == SimulationRunner.TRACE_HEADER
    assert len(df) > 0


def test_simulator_cli_missing_args_fails(tmp_path: Path):
    """Verify python -m simulator.run_scenario exits non-zero on missing required flags."""
    cmd = [sys.executable, "-m", "simulator.run_scenario"]
    res = subprocess.run(cmd, cwd=str(_REPO_ROOT), capture_output=True, text=True)
    assert res.returncode != 0
    assert "usage:" in res.stderr.lower() or "error:" in res.stderr.lower()
```

### 2. `tests/conftest.py` Hermetic Workspace Isolation
```python
"""Global pytest fixtures for hermetic test execution."""

from pathlib import Path
import pytest
from manet.adapters.workspace import WorkspaceAdapter


@pytest.fixture(autouse=True)
def isolate_manet_workspace(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Isolate .manet-workspace by default so disk state never causes test flakes."""
    isolated_root = tmp_path / "isolated_workspace"
    isolated_root.mkdir(parents=True, exist_ok=True)
    
    orig_init = WorkspaceAdapter.__init__

    def patched_init(self, workspace_root=None):
        if workspace_root is None:
            workspace_root = isolated_root
        orig_init(self, workspace_root=workspace_root)

    monkeypatch.setattr(WorkspaceAdapter, "__init__", patched_init)
```

### 3. Pinned `requirements.txt`
```text
simpy==4.1.2
networkx==3.6.1
scikit-learn==1.8.0
pandas==3.0.2
numpy==1.26.4
matplotlib==3.10.8
seaborn==0.13.2
joblib==1.5.3
textual==8.2.8
pytest==9.0.2
```

### 4. `scripts/verify_environment.py` Structure
```python
"""On-demand environment verification script checking runtime, dependencies, and entrypoints."""

from __future__ import annotations
import importlib
from pathlib import Path
import subprocess
import sys

REQUIRED_VERSIONS = {
    "simpy": "4.1.2",
    "networkx": "3.6.1",
    "sklearn": "1.8.0",
    "pandas": "3.0.2",
    "numpy": "1.26.4",
    "matplotlib": "3.10.8",
    "seaborn": "0.13.2",
    "joblib": "1.5.3",
    "textual": "8.2.8",
    "pytest": "9.0.2",
}

def verify_python_version() -> bool:
    print(f"[*] Python runtime: {sys.version.split()[0]} ({sys.platform})")
    if sys.version_info < (3, 11):
        print("  [FAIL] Python 3.11+ is required.")
        return False
    print("  [OK] Python version is >= 3.11.")
    return True

def verify_dependencies() -> bool:
    print("[*] Checking required dependencies...")
    all_ok = True
    for mod_name, expected_ver in REQUIRED_VERSIONS.items():
        try:
            mod = importlib.import_module(mod_name)
            ver = getattr(mod, "__version__", None)
            if ver == expected_ver:
                print(f"  [OK] {mod_name} == {ver}")
            else:
                print(f"  [WARN] {mod_name} version mismatch (got {ver}, expected {expected_ver})")
        except ImportError as e:
            print(f"  [FAIL] {mod_name} could not be imported: {e}")
            all_ok = False
    return all_ok

def verify_entrypoints() -> bool:
    print("[*] Checking CLI entrypoint help invocations...")
    commands = [
        [sys.executable, "-m", "simulator.run_scenario", "--help"],
        [sys.executable, "-m", "ml.train", "--help"],
        [sys.executable, "-m", "ml.evaluate", "--help"],
    ]
    all_ok = True
    for cmd in commands:
        name = " ".join(cmd[1:])
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if res.returncode == 0:
                print(f"  [OK] {name}")
            else:
                print(f"  [FAIL] {name} exited with code {res.returncode}")
                all_ok = False
        except Exception as e:
            print(f"  [FAIL] {name} failed: {e}")
            all_ok = False
    return all_ok

def main() -> int:
    v_py = verify_python_version()
    v_dep = verify_dependencies()
    v_ent = verify_entrypoints()
    if v_py and v_dep and v_ent:
        print("\n[+] ENVIRONMENT VERIFICATION PASSED")
        return 0
    else:
        print("\n[-] ENVIRONMENT VERIFICATION FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Unpinned dependencies / prose mentions | Exact equality pins in root `requirements.txt` | Phase 12 (D-04) | Guarantees deterministic package resolution across all developer installs. |
| Ad-hoc testing of legacy scripts | Automated subprocess regression test module `tests/test_legacy_cli_compat.py` | Phase 12 (D-01) | Formalizes CLI and script contracts in automated CI/test suite. |
| In-repo test pollution / manual workspace resets | Hermetic `conftest.py` test isolation | Phase 12 | Eliminates cross-test flakiness and isolates `.manet-workspace` state. |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Symlink skips in `test_manet_workspace_pruning.py` are normal on Windows for non-admin accounts | Summary & Validation Architecture | Low: Tested and confirmed that Windows throws `OSError` without Developer Mode or admin rights, which `pytest.skip` catches correctly. |
| A2 | Micro-duration (2.0s) is sufficient to test CLI argument parsing, execution pipeline, and trace emission | Patterns & Code Examples | Low: Confirmed experimentally that 2.0s simulation produces 31 trace rows, exercises AODV/mobility/traffic, and completes in < 2 seconds. |

---

## Open Questions

1. **How should `scripts/verify_environment.py` handle missing optional files (e.g. `ml/models/best_model.joblib`)?**
   - *What we know:* In a fresh checkout, models may not be trained yet until `ml/train.py` and `ml/evaluate.py` are run.
   - *Recommendation:* Report presence of model and dataset files as operational status indicators (`[PRESENT]` / `[ABSENT]`), but only treat missing core Python dependencies or Python runtime < 3.11 as hard exit code failures.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.11.8 | — (Required) |
| pip | Package Manager | ✓ | 26.1.2 | — |
| pytest | Test Runner | ✓ | 9.0.2 | — (Required) |
| SimPy | Discrete-Event Engine | ✓ | 4.1.2 | — (Required) |
| NetworkX | Topology Graph | ✓ | 3.6.1 | — (Required) |
| scikit-learn | ML Engine | ✓ | 1.8.0 | — (Required) |
| pandas | Data Processing | ✓ | 3.0.2 | — (Required) |
| numpy | Numeric Arrays | ✓ | 1.26.4 | — (Required) |
| matplotlib | Visualization | ✓ | 3.10.8 | — (Required) |
| seaborn | Visualization | ✓ | 0.13.2 | — (Required) |
| joblib | Persistence | ✓ | 1.5.3 | — (Required) |
| textual | TUI Framework | ✓ | 8.2.8 | — (Required) |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 [VERIFIED: python.exe] |
| Config file | `pytest.ini` (`asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function`) |
| Quick run command | `python -m pytest tests/test_legacy_cli_compat.py tests/test_manet_import_boundaries.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| **DELV-01** | Legacy CLI compatibility (`simulator.run_scenario`, `ml.train`, `ml.evaluate`, scripts) | Subprocess integration | `python -m pytest tests/test_legacy_cli_compat.py -q` | ❌ Wave 0 Gap |
| **DELV-01** | AST presentation & business boundary isolation | Static analysis | `python -m pytest tests/test_manet_import_boundaries.py tests/test_import_boundaries.py -q` | ✅ Exists |
| **DELV-01** | Full existing test suite unweakened (285 tests) | Unit / Integration | `python -m pytest -q` | ✅ Exists (with `conftest.py` hermetic fix) |
| **DELV-02** | Packaging manifest and environment verification script | Operational / Script | `python scripts/verify_environment.py` | ❌ Wave 0 Gap |
| **DELV-03** | Honest verification report documenting test counts and limitations | Planning artifact | `python -m pytest -q` (audit output) | ❌ Wave 2 deliverable (`12-VERIFICATION.md`) |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_legacy_cli_compat.py tests/test_manet_import_boundaries.py -q` (< 5s)
- **Per wave merge:** `python -m pytest -q` (full suite, ~7 mins)
- **Phase gate:** Full suite green (zero failures, 3 expected symlink skips on Windows) before completing Phase 12.

### Wave 0 Gaps
- [ ] `tests/conftest.py` — Autouse fixture isolating `.manet-workspace` for all tests.
- [ ] `tests/test_legacy_cli_compat.py` — Dedicated subprocess regression suite for `simulator.run_scenario`, `ml.train`, `ml.evaluate`, and `scripts/*`.
- [ ] `requirements.txt` — Root pinned package manifest.
- [ ] `scripts/verify_environment.py` — Standalone environment verification script.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V5 Input Validation | yes | CLI argument validation via `argparse`; reject non-existent paths, invalid types, and malformed inputs with non-zero exit code. |
| V14 Configuration & Dependencies | yes | Pinned package dependencies in `requirements.txt` with exact version equality (`==`). |
| Process & Boundary Security | yes | AST boundary checks asserting that `manet/commands/` never imports `subprocess`, `os`, or `shutil` (D-10/T-7-01). |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Insecure Process Execution | Elevation of Privilege | Commands in `manet/` must not execute arbitrary shell commands; asserted via AST tests in `tests/test_manet_import_boundaries.py`. |
| Dependency Hijacking / Drift | Tampering | Strict pinning of all 10 direct external dependencies in `requirements.txt`. |
| Cross-Test State Tampering | Tampering | Hermetic isolation of test workspaces using `tests/conftest.py` with `tmp_path`. |

---

## Sources

### Primary (HIGH confidence)
- CPython 3.11.8 environment probe (`python -c "import ...; print(version)"`) - [VERIFIED: python.exe]
- Pytest 9.0.2 full suite run (285 collected tests, 282 passed, 3 skipped) - [VERIFIED: pytest run]
- Subprocess micro-fixture empirical runs for `simulator.run_scenario`, `ml.train`, `ml.evaluate` - [VERIFIED: python subprocess execution]
- Project architectural constraints and guidelines (`GEMINI.md`, `ROADMAP.md`, `12-CONTEXT.md`) - [VERIFIED: in-repo canonical files]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified directly in Python 3.11 environment.
- Architecture: HIGH - Proven via existing AST suites and subprocess micro-fixtures.
- Pitfalls: HIGH - Discovered and verified the exact `.manet-workspace` test leakage issue during this session.

**Research date:** 2026-11-10
**Valid until:** 2026-12-10 (stable dependencies)
