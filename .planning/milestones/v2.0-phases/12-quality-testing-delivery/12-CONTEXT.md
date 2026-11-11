# Phase 12: Quality, Testing & Delivery - Context

**Gathered:** 2026-11-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 12 delivers final quality assurance, regression verification, packaging manifest standardization, and complete test suite validation for Milestone v2.0 (Interactive TUI Application). It verifies that:
1. The full existing test suite passes unweakened alongside new feature and regression tests covering all TUI capabilities and architectural invariants on the native Windows 11 host (DELV-01).
2. Legacy command-line workflows (`python -m simulator.run_scenario`, `scripts/*`, and `python -m ml.train` / `ml.evaluate`) retain unchanged behavior, expected exit codes, and output schema contracts without regression.
3. Packaging integrity is formalized via an exact, pinned `requirements.txt` and AST import boundary validation, accompanied by an on-demand environment verification script (`scripts/verify_environment.py`).
4. A complete, honest verification audit (`12-VERIFICATION.md`) documents test suite execution results, modified files, and architectural limitations.

Per explicit user direction, deep documentation updates (`README.md`, terminal guides) are deferred to a dedicated `/gsd-docs-update` workflow, and milestone-level archival/reporting is deferred to `/gsd-complete-milestone`.

</domain>

<decisions>
## Implementation Decisions

### Legacy CLI & Script Regression Harness
- **D-01:** Behavioral Subprocess Pipeline with Micro-Fixtures & Invariant Checks:
  - Dedicated automated test module `tests/test_legacy_cli_compat.py` executing legacy commands (`python -m simulator.run_scenario`, `python -m ml.train`, `python -m ml.evaluate`, and key `scripts/*`) via subprocess.
  - Commands run fast micro-scenarios (e.g. 2.0s duration, miniature synthetic dataset) within isolated pytest `tmp_path` fixtures without modifying committed repository files or workspace directories.
  - Asserts exact exit codes (0 for valid runs, non-zero for invalid arguments), stdout markers, canonical `TRACE_HEADER` column sets, and metrics dictionary schemas.
  - Avoids brittle bitwise trace hashing while ensuring true functional regression safety and contractual compliance for DELV-01.
  — **Reversibility:** costly — defines regression test harness and contractual CLI behavior assertions.

### Documentation & Milestone Lifecycle Scope
- **D-02:** Defer Documentation Overhaul to `/gsd-docs-update`:
  - User explicitly directed to defer deep documentation updates to a dedicated `/gsd-docs-update` workflow.
  - Phase 12 remains strictly focused on executable test suites, packaging manifests, and automated quality verification.
  — **Reversibility:** reversible — `/gsd-docs-update` can be invoked independently post-phase.

- **D-03:** Standard Phase 12 Verification + Defer Milestone Archiving to `/gsd-complete-milestone`:
  - Phase 12 produces its standard `12-VERIFICATION.md` capturing full test suite results (all 285+ tests), file additions/modifications, and an honest ledger of known limitations (80x24 minimum terminal geometry, Windows-verified host).
  - High-level milestone closure, retrospective logging, and milestone archive generation will be executed separately via `/gsd-complete-milestone`.
  — **Reversibility:** reversible — maintains clean separation between phase verification and milestone finalization.

### Dependency & Packaging Integrity
- **D-04:** Pinned Manifest + AST Boundaries + Decoupled Clean-Environment Smoke Script:
  - Create root `requirements.txt` pinning exact tested versions: `simpy==4.1.2`, `networkx==3.6.1`, `scikit-learn==1.8.0`, `pandas==3.0.2`, `numpy==1.26.4`, `matplotlib==3.10.8`, `seaborn==0.13.2`, `joblib==1.5.3`, `textual==8.2.8`, and `pytest==9.0.2`.
  - Maintain and enforce AST-based import boundaries in fast, offline pytest suites (`tests/test_manet_import_boundaries.py` and `tests/test_import_boundaries.py`), verifying `manet/` never imports business packages and vice-versa.
  - Implement `scripts/verify_environment.py` as an on-demand utility to validate clean virtual environment installation and CLI/TUI entry-point viability without imposing latency on everyday unit test runs.
  — **Reversibility:** costly — standardizes external package requirements across the entire repository.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` § Phase 12 — [Phase 12 goals, success criteria, and requirement mappings]
- `.planning/REQUIREMENTS.md` § DELV-01, DELV-02, DELV-03 — [Quality, verification, and delivery requirements]
- `.planning/STATE.md` — [Current repository state and verified test metrics (282 passed, 3 skipped)]

### Architecture & Dependencies
- `.planning/codebase/STACK.md` — [Exact verified dependencies, Python 3.11 Windows runtime, and version traps]
- `.planning/codebase/TESTING.md` — [Test suite layout, pytest conventions, and execution patterns]
- `tests/test_manet_import_boundaries.py` — [AST import boundary validation between `manet/` and business logic]
- `tests/test_import_boundaries.py` — [Core simulator and attack package import boundaries]

### Entry Points to Verify
- `simulator/run_scenario.py` — [Legacy simulation CLI entry point: `python -m simulator.run_scenario`]
- `ml/train.py` — [Legacy ML training CLI: `python -m ml.train`]
- `ml/evaluate.py` — [Legacy ML evaluation CLI: `python -m ml.evaluate`]
- `scripts/verify_gate2_impact.py` — [Benchmark verification script]
- `manet/__main__.py` & `bootstrap.py` — [TUI launcher entry point: `python -m manet`]

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/conftest.py` & pytest `tmp_path`: Provides safe, isolated filesystem workspaces for running subprocess tests without polluting the repository.
- `simulator.run_scenario.SimulationRunner`: The underlying runner invoked by both CLI and TUI.
- Existing AST test patterns in `tests/test_manet_import_boundaries.py`: Can be leveraged/extended for packaging and entry point verification.

### Established Patterns
- Absolute imports throughout all packages (`from simulator.aodv import ...`).
- Subprocess execution with explicit root anchoring (`cwd=PROJECT_ROOT`, `sys.executable`).
- Zero mock data in tests; authentic execution on Windows.

### Integration Points
- `tests/test_legacy_cli_compat.py`: New regression test module covering legacy CLIs and scripts.
- `requirements.txt`: Root dependency manifest with exact `==` pins.
- `scripts/verify_environment.py`: Standalone environment verification script.
- `.planning/phases/12-quality-testing-delivery/12-VERIFICATION.md`: Phase verification report.

</code_context>

<specifics>
## Specific Ideas

- Ensure `tests/test_legacy_cli_compat.py` uses tiny durations (e.g., 2.0s or minimal steps) and `--out tmp_path` so the full regression suite completes in seconds on Windows.
- Standardize `requirements.txt` with exact version equality pins matching `.planning/codebase/STACK.md`.

</specifics>

<deferred>
## Deferred Ideas

- Comprehensive `README.md` and `CHANGELOG.md` overhaul deferred to `/gsd-docs-update` per user decision.
- Milestone v2.0 closure, release retrospective, and milestone archiving deferred to `/gsd-complete-milestone` per user decision.

</deferred>

---

*Phase: 12-Quality, Testing & Delivery*
*Context gathered: 2026-11-10*
