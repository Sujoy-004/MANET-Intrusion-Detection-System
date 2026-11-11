<!-- generated-by: gsd-doc-writer -->
# Testing & Quality Assurance

This document describes the testing strategy, test suite architecture, automated verification procedures, and quality gates for the MANET Intrusion Detection and Response System.

## Test Framework & Environment

The test suite is built on **pytest 9.0.2** running under Python 3.11.8 on native Windows.

Install pytest and dependencies:

```powershell
python -m pip install -r requirements.txt
```

---

## Running Tests

### 1. Run the Complete Test Suite

Execute all 293 unit, integration, recovery, presentation, and architectural tests:

```powershell
python -m pytest -q
```

Expected output:
```text
290 passed, 3 skipped, 1 warning in ~450s
```

*(Note: The 3 skips occur in `tests/test_manet_workspace_pruning.py` on non-elevated Windows environments lacking symlink creation privileges; the production code and tests automatically exercise copy-based fallbacks.)*

### 2. Run AST Import Boundary Enforcement (Fast Quality Gate)

Enforce architectural layer decoupling (7 tests, ~0.26s):

```powershell
python -m pytest tests/test_manet_import_boundaries.py tests/test_import_boundaries.py -q
```

### 3. Run Legacy CLI Compatibility Suite

Assert that legacy command-line workflows maintain unchanged behavior and exit code contracts:

```powershell
python -m pytest tests/test_legacy_cli_compat.py -q
```

### 4. Run Core Simulation & ML Pipeline Tests

```powershell
# AODV route discovery recovery & quarantine guards
python -m pytest tests/test_aodv_recovery.py -q

# Attack behavior tests
python -m pytest tests/test_attacks_blackhole.py tests/test_attacks_grayhole.py -q

# Closed-loop IDS response & route isolation tests
python -m pytest tests/test_closed_loop.py -q

# ML training & evaluation tests
python -m pytest tests/test_ml_pipeline.py tests/test_generalization.py -q
```

---

## Test Suite Architecture

The repository contains **38 test modules** in `tests/` categorized into three primary architectural domains:

### 1. Core Simulation & ML Business Logic (11 Modules, 79 Tests)

| Test Module | Scope & Invariants Tested |
|---|---|
| `tests/test_aodv_recovery.py` | Bounded RREQ retries, exponential backoff, timer-generation protection, discovery cooldown, packet queue limit and buffer TTL expiration, partition recovery, late RREP handling, quarantine response guards, and elimination of RREP storm loops. |
| `tests/test_attacks_blackhole.py` | RREP sequence spoofing, silent data packet drops, strategy registry factory. |
| `tests/test_attacks_grayhole.py` | Honest AODV control routing, probabilistic data drops, selective flow targeting. |
| `tests/test_closed_loop.py` | `OnlineIDS` controller, 2-strike confirmation, route invalidation, quarantine decay, and QoS recovery. |
| `tests/test_feature_pipeline.py` | Sliding-window aggregation, neutral fallbacks, and mathematical anti-leakage invariance ($X$ invariant to label shifts). |
| `tests/test_gate2_benchmark.py` | Multi-seed Gate 2 degradation benchmark asserting $\ge 25\%$ relative PDR drop under attack. |
| `tests/test_generalization.py` | Zero-shot attack transfer, multi-attack dataset integrity, and cross-scenario parameter grid evaluation. |
| `tests/test_import_boundaries.py` | AST-based architectural check asserting `simulator/` never imports from `attacks/` and `run_scenario.py` acts as composition root. |
| `tests/test_ml_pipeline.py` | Seed-disjoint train/test partitioning, 5-fold CV tuning, locked $\text{FPR} \le 1.0\%$ gate, model persistence, and prediction parity. |
| `tests/test_plots.py` | Headless-safe figure generation, Seaborn palette application, and non-empty PNG file export verification. |
| `tests/test_trace_logging.py` | 10-column CSV trace schema enforcement, node attribution, and periodic `NODE_STATUS` telemetry frequency. |

### 2. TUI Presentation & Textual Modules (26 Modules, 205 Tests)

| Test Module | Scope & Invariants Tested |
|---|---|
| `tests/test_manet_adapters.py` | One-way data adapters (diagnostics, scenario, execution, workspace). |
| `tests/test_manet_app_launch.py` | Headless app lifecycle, pilot initialization, screen installation. |
| `tests/test_manet_command_palette.py` | Command resolution, search filtering, action dispatching. |
| `tests/test_manet_command_registry.py` | Command provider registration and execution safety. |
| `tests/test_manet_compact.py` | Compact density layout breakpoints and reflow behavior. |
| `tests/test_manet_console.py` | In-app debug console and log output. |
| `tests/test_manet_dashboard_workspace.py` | Executive grid status card rendering and CTA button handlers. |
| `tests/test_manet_diagnostics_probe.py` | Runtime probe health checks and dependency evaluation. |
| `tests/test_manet_entry.py` | CLI main entrypoint and arguments validation. |
| `tests/test_manet_history_screen.py` | Experiment history list, record filtering, and run selection. |
| `tests/test_manet_import_boundaries.py` | AST boundary checks: `manet/` never imports core business packages; no OS execution primitives in `manet/commands/`. |
| `tests/test_manet_live_run_screen.py` | Virtual time progress, live packet counters, cancellation controls. |
| `tests/test_manet_manifest_artifacts.py` | Atomic JSON manifest creation, schema validation, SHA-256 checksums. |
| `tests/test_manet_navigation.py` | Global keybindings (`[S]`, `[R]`, `[O]`, `[P]`, `[F1]`, `[Esc]`). |
| `tests/test_manet_paths.py` | Centralized path resolution and repository root anchoring. |
| `tests/test_manet_results_screen.py` | QoS scorecard presentation, threshold badges, trace tabs. |
| `tests/test_manet_scenario_adapter.py` | Preset scenario loading, JSON validation, and error trapping. |
| `tests/test_manet_simulation_config.py` | 2-tier scenario validation (Tier 1 schema, Tier 2 physical invariants). |
| `tests/test_manet_simulation_runner_compat.py` | Subprocess and stepping runner contract parity. |
| `tests/test_manet_simulation_workflow.py` | 3-step wizard flow, parameter submission, pre-flight review. |
| `tests/test_manet_stepping_equivalence.py` | In-process SimPy stepping byte-identical trace parity vs. baseline runner. |
| `tests/test_manet_supervisor_lifecycle.py` | Background execution supervisor, worker states, and safe shutdown. |
| `tests/test_manet_telemetry_bounded.py` | Synchronized ring-buffer, drop-oldest overflow, thread safety. |
| `tests/test_manet_theme.py` | SOC dark palette, contrast modes, CSS variable compliance. |
| `tests/test_manet_workspace_allocation.py` | Unique run directory generation and experiment ID sanitization. |
| `tests/test_manet_workspace_pruning.py` | Safe run deletion, preview modal, symlink vs copy fallback. |

### 3. Packaging & Regression Harness (1 Module, 9 Tests)

| Test Module | Scope & Invariants Tested |
|---|---|
| `tests/test_legacy_cli_compat.py` | Subprocess regression harness asserting exact exit codes, stdout schemas, and trace parity for legacy entry points (`simulator.run_scenario`, `ml.train`, `ml.evaluate`, `verify_gate2_impact`, `build_dataset --help`, and negative argument paths). |

---

## Hermetic Test Workspace Isolation

The test configuration in [tests/conftest.py](tests/conftest.py) defines an `autouse=True` fixture that automatically patches `WorkspaceAdapter.__init__` with a temporary directory (`tmp_path`) for every test execution.

- **Guarantees:** Tests never pollute or delete real experiment runs in `.manet-workspace/`.
- **Opt-out:** Tests testing authentic workspace paths can mark `@pytest.mark.no_workspace_patch`.

---

## Mandatory Quality Gates

### Gate 1: Simulator Baseline Determinism
Running any scenario with an explicit seed yields identical traces. Verified by `tests/test_trace_logging.py` and `tests/test_feature_pipeline.py`.

### Gate 2: Measurable Attack Degradation
An attack MUST demonstrably degrade network performance before an ML detector is built. Verified by `tests/test_gate2_benchmark.py` (relative PDR drops $\ge 25\%$).

### Gate 3: Anti-Leakage Feature Invariance
Feature matrix $X$ must not contain oracle identifiers or ground-truth leakage. Verified by `tests/test_feature_pipeline.py::test_anti_leakage_invariance`.

### Gate 4: Zero Random-Row Splitting
Training and test datasets must be disjoint across seeds and scenarios. Verified by `tests/test_ml_pipeline.py::test_split_seed_disjointness`.

### Gate 5: False Positive Rate Gate ($\text{FPR} \le 1.0\%$)
Any model candidate exceeding 1.0% FPR is disqualified to prevent benign route teardowns. Enforced by `ml/evaluate.py` and asserted by `tests/test_ml_pipeline.py`.

### Gate 6: Closed-Loop QoS Recovery
The IDS must show statistically significant network recovery over unprotected AODV under attack. In the 300s Seed-42 reference benchmark, PDR recovers from 18.10% (under Blackhole attack) back to 62.93% (restoring 95.51% of baseline delivery).

### Gate 7: AST Import Boundary Separation
- `manet/` must never import from business modules (`simulator`, `attacks`, `feature_extraction`, `ml`).
- `manet/commands/` must never import OS execution primitives (`subprocess`, `shutil`, `os`).
- `simulator/` must never import from `attacks/`.
Verified statically by `tests/test_manet_import_boundaries.py` and `tests/test_import_boundaries.py`.
