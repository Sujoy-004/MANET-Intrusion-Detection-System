---
phase: 08-operational-dashboard
plan: 02
subsystem: tui-workspace
tags:
  - tui
  - textual
  - executive-grid
  - dashboard
  - responsive
requires:
  - phase: 08-operational-dashboard
    plan: "08-01"
provides:
  - capability: executive-grid-workspace
  - capability: top-status-cards
  - capability: cta-hero-panel
  - capability: recent-experiments-table
  - capability: workspace-rails
affects:
  - manet/widgets/
  - manet/screens/
  - tests/test_manet_dashboard_workspace.py
tech-stack:
  added: []
  patterns:
    - responsive executive grid layout reflowing down to 80x24 terminal dimensions
    - periodic non-blocking background diagnostics polling every 4 seconds
    - honest empty-state CTA guidance vs read-only recent experiments presentation
key-files:
  created:
    - manet/widgets/status_bar.py
    - manet/widgets/notification_rail.py
    - manet/widgets/nav_rail.py
    - manet/widgets/cta_hero.py
    - manet/widgets/recent_experiments.py
  modified:
    - manet/widgets/dashboard_cards.py
    - manet/widgets/__init__.py
    - manet/screens/main_workspace.py
    - tests/test_manet_dashboard_workspace.py
decisions:
  - "Top status cards render System Health, Component Capabilities with inline contextual badges, and Active Workload distinguishing engine ready (offline) from running state per D-01, D-03, TUI-06, and TUI-08"
  - "Lower split body displays CtaHeroPanel when .manet-workspace/ has no past runs, and mounts RecentExperimentsTable when runs exist per D-04 and TUI-07"
  - "MainWorkspace mounts StatusBar, NotificationRail, and NavRail fulfilling Phase 7 deferred D-03 session shell mounting contract (D-05)"
  - "Periodic non-blocking background polling every 4.0s refreshes diagnostic capability state without creating widget memory leaks (D-02)"
  - "Executive Grid CSS reflows horizontal multi-column cards into a vertical single-column stream under Screen.-compact down to 80x24 (D-01)"
metrics:
  duration: 12m
  completed_date: "2026-11-07"
status: complete
actuals:
  tokens: 9549
  tasks: 3
  commits: 3
  plan_head_before: "c4d23221fe682e610347a709c3cf5ed9f21ed2d6"
  plan_head_after: "96cd97fce6955a0958e7b0b387ae293d3357e68f"
---

# Phase 08 Plan 02: Executive Grid Layout and Operational UI Widgets Summary

Operational dashboard visual flight deck assembling top status cards with inline capability badges, persistent workspace rails, responsive executive grid reflow down to 80x24, and guided first-run CTA transitioning to read-only recent experiments.

## Key Deliverables

1. **Top Status Cards (`manet/widgets/dashboard_cards.py`):**
   - `SystemHealthCard`: Real-time Python runtime version, host platform, and dependency availability summary with green/amber indicators.
   - `ComponentCapabilitiesCard`: Scenario count, dataset status (`data/train.csv`, `test.csv`), and champion model artifact (`ml/models/best_model.joblib`) with inline contextual badges (`VERIFIED`, `UNAVAILABLE`, `PARTIAL (Grayhole F1: 0.0 - Ineffective Detection)`) and remediation commands.
   - `ActiveWorkloadCard`: Workload execution state (`IDLE (No active simulation)`) and routing engine availability (`AODV Engine Ready (Offline)`), strictly distinguishing routing engine readiness from running state without false claims.

2. **Persistent Workspace Rails (`manet/widgets/`):**
   - `StatusBar`: Persistent system indicators (`System Ready`, `Workspace: Nominal`, `Engine: Offline Ready`).
   - `NotificationRail`: Dismissible alert notice rail backed by bounded in-memory `NotificationAdapter`.
   - `NavRail`: Quick action shortcuts (`[S]` Simulation notice, `[R]` Results notice, `[Ctrl+O]` Console, `[Ctrl+P]` Palette, `[F1]` Help) reconciling logs/diagnostics navigation honestly.

3. **Lower Split-Body Widgets (`manet/widgets/cta_hero.py`, `recent_experiments.py`):**
   - `CtaHeroPanel`: Guided empty-state orienting users when `.manet-workspace/` has no runs, explaining pending Phase 9 simulation workflow without claiming `[S]` launches simulations.
   - `RecentExperimentsTable`: Read-only `DataTable` presenting past runs (`Run ID`, `Scenario`, `Seed`, `Status`, `PDR`, `Date`) with sanitized values preventing markup injection (T-08-05).

4. **Upgraded MainWorkspace Executive Grid (`manet/screens/main_workspace.py`):**
   - Hierarchical structure composed within `#workspace-box`: `#top-cards-container`, `#lower-body-container` (`#main-content-panel` + `#nav-rail-panel`), `#notification-rail`, and `#status-bar`.
   - Responsive CSS reflow: 3-column horizontal cards on normal terminals (`Screen.-normal`), reflowing to single-column vertical cards on compact viewports (`Screen.-compact`) down to 80x24.
   - Periodic non-blocking background polling (`set_interval(4.0)`) updating diagnostics without UI freeze or object churn (D-02, T-08-04).
   - Screen bindings (`s`, `r`, `escape`) providing safe interactive feedback via `NotificationRail`.

## Test Results

- All 11 workspace and compact tests pass:
  - `tests/test_manet_dashboard_workspace.py`: 8 passed
  - `tests/test_manet_compact.py`: 3 passed
- Combined adapter & workspace suite: 16 passed in 2.73s.
- Full `manet` test suite: 63 passed in 15.16s.
- AST import boundary check: strictly 0 forbidden imports.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. All widgets render dynamic data from adapters, probes, and filesystem inspection without mock numbers or hardcoded test values.

## Threat Flags

None. No new network endpoints, secret access, or unauthorized file writes introduced; all dynamic string values are sanitized via `rich.markup.escape`.

## Self-Check: PASSED

- FOUND: `manet/widgets/status_bar.py`
- FOUND: `manet/widgets/notification_rail.py`
- FOUND: `manet/widgets/nav_rail.py`
- FOUND: `manet/widgets/cta_hero.py`
- FOUND: `manet/widgets/recent_experiments.py`
- FOUND: `manet/widgets/dashboard_cards.py`
- FOUND: `manet/screens/main_workspace.py`
- FOUND: `tests/test_manet_dashboard_workspace.py`
- FOUND commit: `ceff235`
- FOUND commit: `a78190d`
- FOUND commit: `96cd97f`
