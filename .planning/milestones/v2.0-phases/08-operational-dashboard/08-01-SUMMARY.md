---
phase: 08-operational-dashboard
plan: 01
subsystem: tui-adapters
tags:
  - tui
  - adapters
  - diagnostics
  - zero-mock
  - textual
requires:
  - phase: 07-tui-shell-application-frame
provides:
  - capability: zero-mock-diagnostics-probe
  - capability: decoupled-presentation-adapters
affects:
  - manet/adapters/
  - manet/widgets/
  - manet/screens/
tech-stack:
  added: []
  patterns:
    - non-blocking AST-isolated environment and artifact probing
    - decoupled adapter protocols for status, workspace, navigation, and notifications
    - bounded in-memory notice queue with deque(maxlen=20)
key-files:
  created:
    - manet/adapters/__init__.py
    - manet/adapters/diagnostics.py
    - manet/adapters/status.py
    - manet/adapters/workspace.py
    - manet/adapters/navigation.py
    - manet/adapters/notifications.py
    - manet/widgets/__init__.py
    - manet/widgets/dashboard_cards.py
    - tests/test_manet_diagnostics_probe.py
    - tests/test_manet_adapters.py
    - tests/test_manet_dashboard_workspace.py
  modified:
    - manet/screens/main_workspace.py
decisions:
  - "DiagnosticsProbe queries runtime packages via importlib.util.find_spec and importlib.metadata.version without loading backend packages, avoiding AST boundary violations"
  - "sklearn mapped to scikit-learn distribution name to avoid PackageNotFoundError"
  - "Missing binary best_model.joblib reports UNAVAILABLE with full CLI remediation even if historical metadata exists"
  - "Grayhole F1 of 0.0 dynamically badged as PARTIAL (Grayhole F1: 0.0 - Ineffective Detection) to maintain academic honesty"
  - "WorkspaceAdapter strictly inspects .manet-workspace in read-only fashion without creating directories"
  - "NotificationAdapter uses collections.deque(maxlen=20) to bound in-memory notification retention"
metrics:
  duration: 8m
  completed_date: "2026-11-07"
status: complete
actuals:
  tokens: 8750
  tasks: 3
  commits: 3
  plan_head_before: "d39d511fb55ba06dfb2d05aa6dfd014d302a40ca"
  plan_head_after: "063efe24092bc3c93ee483de464de8dd36fa5a05"
---

# Phase 08 Plan 01: Foundational Adapter Layer and Tracer Slice Summary

Zero-mock runtime diagnostics probe and decoupled presentation adapter interfaces establishing honest system capability reporting and clean architectural boundaries for the MANET IDS Operational Dashboard.

## Key Deliverables

1. **End-to-End Vertical Tracer Slice:**
   - Mounted `SystemHealthCard` on `MainWorkspace` within `#workspace-box`, verified by headless Textual pilot test `test_tracer_diagnostic_card_mount`.
   - Preserved backward-compatible `#workspace-box` ID and classes so compact breakpoint tests continue to pass unweakened.

2. **Zero-Mock Capability Diagnostics (`DiagnosticsProbe`):**
   - Implemented `CapabilityStatus` and `DiagnosticsReport` frozen dataclasses.
   - Probes runtime Python version (requires >= 3.11) and 9 core dependencies (`simpy`, `networkx`, `sklearn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pytest`, `joblib`) using `importlib.util.find_spec` and `importlib.metadata.version` with `sklearn` -> `scikit-learn` distribution mapping, strictly avoiding business logic imports.
   - Probes scenario presets in `scenarios/*.json`, distinguishing valid presets from malformed files.
   - Probes `data/train.csv` and `data/test.csv` via `pathlib.Path.stat()`, returning `VERIFIED` with exact file sizes or `UNAVAILABLE` with factual CLI remediation (`Run python scripts/build_dataset.py --multi-attack`).
   - Probes `ml/models/best_model.joblib` and `ml/models/model_metadata.json`, distinguishing missing binary from historical metadata, dynamically extracting evaluation metrics, and explicitly badging Grayhole F1 of 0.0 as `PARTIAL (Grayhole F1: 0.0 - Ineffective Detection)` per TUI-08 and D-03.
   - Handles corrupted or missing metadata gracefully without crashing.

3. **Decoupled Adapter Layer (`manet/adapters/`):**
   - `StatusAdapter`: Returns `WorkloadStatus` distinguishing active workload state (`IDLE`) from routing engine readiness (`AODV Engine Ready (Offline)`).
   - `WorkspaceAdapter`: Strictly read-only discovery of `.manet-workspace/` experiment summaries without creating directories or mutating files.
   - `NavigationAdapter`: Centralizes quick navigation targets and shortcuts (`simulation` [S], `results` [R], `console` [Ctrl+O], `palette` [Ctrl+P], `help` [F1]).
   - `NotificationAdapter`: Implements bounded in-memory notice queue using `collections.deque(maxlen=20)` preventing memory leaks.

## Test Results

- All 13 plan-specific unit, pilot, and AST boundary tests pass:
  - `tests/test_manet_diagnostics_probe.py`: 7 passed
  - `tests/test_manet_adapters.py`: 5 passed
  - `tests/test_manet_dashboard_workspace.py`: 1 passed
- Full MANET test suite: 56 passed in 9.47s.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. All probe methods query real filesystem and environment state without mock numbers or hardcoded scores.

## Self-Check: PASSED

- FOUND: `manet/adapters/__init__.py`
- FOUND: `manet/adapters/diagnostics.py`
- FOUND: `manet/adapters/status.py`
- FOUND: `manet/adapters/workspace.py`
- FOUND: `manet/adapters/navigation.py`
- FOUND: `manet/adapters/notifications.py`
- FOUND: `manet/widgets/__init__.py`
- FOUND: `manet/widgets/dashboard_cards.py`
- FOUND: `manet/screens/main_workspace.py`
- FOUND: `tests/test_manet_diagnostics_probe.py`
- FOUND: `tests/test_manet_adapters.py`
- FOUND: `tests/test_manet_dashboard_workspace.py`
- FOUND commit: `5a23da4`
- FOUND commit: `c90a946`
- FOUND commit: `063efe2`
