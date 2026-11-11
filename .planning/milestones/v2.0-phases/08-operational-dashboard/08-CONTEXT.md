# Phase 8: Operational Dashboard - Context

**Gathered:** 2026-11-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 delivers the real Operational Dashboard on the `manet/` TUI main workspace (`MainWorkspace`), replacing placeholder static text with live, honest runtime capability diagnostics, active workload monitoring, and recent experiment summaries. It inspects Python version, required dependency availability (`simpy`, `networkx`, `sklearn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pytest`, `joblib`), scenario files (`scenarios/*.json`), documented dataset artifacts (`data/train.csv`, `data/test.csv`), and champion ML model artifact (`ml/models/best_model.joblib`) with metadata provenance from `ml/models/model_metadata.json`. Explicit capability states (verified, experimental, partial, unavailable) are surfaced with zero mock values; Grayhole detection F1 of 0.0 is explicitly presented as ineffective detection. Serialized `.joblib` files and `data/*.csv` are gitignored and may be absent on fresh clones—missing artifacts must be reported as `UNAVAILABLE` with factual CLI remediation context, never masked by mock data. Phase 8 also provides a guided first-run experience when `.manet-workspace/` has no experiments and quick navigation to simulation, results, logs, and help. It does NOT implement simulation execution workflows (Phase 9), background worker processes or live telemetry streaming (Phase 10), or persistent manifest history browsing (Phase 11).

</domain>

<decisions>
## Implementation Decisions

### Layout & Information Hierarchy
- **D-01:** Top Status Cards with Split Body (Executive Grid) layout. The operational dashboard organizes high-level system diagnostics across top status cards (System Health, Component Capabilities, Active Workload/Threat Status), with a split lower body dedicated to Recent Experiments / First-Run CTA and quick navigation shortcuts. Responsive `HORIZONTAL_BREAKPOINTS` automatically reflow multi-column cards into a single vertical stream on compact viewports (down to 80x24). — **Reversibility:** costly — defines the widget composition and mounting hierarchy of `MainWorkspace`.

### Capability Diagnostics & Refresh Behavior
- **D-02:** Periodic Background Polling (every 3–5 seconds). Capability diagnostics evaluate system readiness on startup (`on_mount`) and periodically re-scan filesystem indicators (presence of scenario JSONs, `data/train.csv`, `data/test.csv`, and `ml/models/best_model.joblib`) using lightweight, non-blocking file stat checks. This automatically discovers newly trained models or datasets without requiring an application restart. — **Reversibility:** reversible — timer interval and probe logic live in a self-contained diagnostic provider.

### Missing Component & Warning Presentation
- **D-03:** Inline Contextual Badges within Capability Cards. Missing components, unverified artifacts, and degraded models are rendered as inline badges directly inside their respective capability cards (e.g., `[amber]PARTIAL (Grayhole F1: 0.0)[/]`, `[red]UNAVAILABLE[/]`, `[green]VERIFIED[/]`). This preserves screen real estate and visual balance on compact terminals while maintaining absolute operational honesty per TUI-08 without intrusive top alert banners. — **Reversibility:** reversible.

### First-Run & Empty State Experience
- **D-04:** Guided Call-to-Action (CTA) Hero Panel. When launching the application on a fresh environment where no experiments exist in `.manet-workspace/`, the lower body displays a prominent, guided CTA panel orienting the user to their first action and explaining project state without claiming that pressing [S] launches or configures a simulation now (Phase 9 owns the simulation configuration workflow; [S] currently surfaces an informative pending notice). Once an experiment completes in future phases, the panel transitions to display the read-only Recent Experiments summary table. — **Reversibility:** reversible.

### Mounting Contract from Phase 7 (Deferred D-03 Option-A)
- **D-05:** Session Shell Mounting Contract. Carry forward Phase 7's deferred D-03 contract by structuring `MainWorkspace` with `StatusBar`, `NotificationRail`, and `NavRail` under `manet/widgets/` backed by clean noop adapter interfaces under `manet/adapters/`. This establishes the mounting points for Phase 10/11 background workers and history without re-architecting the shell. — **Reversibility:** costly — pins the adapter interface boundaries across the app.

### the agent's Discretion
- Concrete diagnostic probe adapter implementation (`manet/adapters/diagnostics.py`).
- Exact card styling, borders, and badge text typography using existing Textual theme tokens (`$primary`, `$secondary`, `$success`, `$warning`, `$error`).
- Detailed metadata formatting from `ml/models/model_metadata.json` (timestamp, architecture, hyperparameters, precision, recall, and Grayhole F1 callout).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engineering contract & specs
- `GEMINI.md` — binding contract: Python 3.11+, pure-Python SimPy discrete-event simulator, determinism, pathlib, zero mock values.
- `CHANGELOG.md` — authoritative project history and version records.
- `README.md` — documented setup, dataset building (`python scripts/build_dataset.py --multi-attack`), and training pipeline (`python -m ml.train`, `python -m ml.evaluate`).
- `.gitignore` — tracks gitignored patterns: `data/`, `traces/`, and `ml/models/*.joblib`.
- `ml/models/model_metadata.json` — tracked provenance source for the champion model (`ml/models/best_model.joblib`), evaluation scores, parameters, and F1 metrics.
- `.planning/REQUIREMENTS.md` — TUI-06, TUI-07, TUI-08 (dashboard diagnostics, workload/experiment summaries, explicit capability states).
- `.planning/ROADMAP.md` — Phase 8 goal, dependencies, and success criteria.
- `MANET_IDS_BTech_Execution_Guide.md` — domain context on AODV routing, attack classes, Grayhole F1 0.0 baseline interpretation.

### Prior Phase Context
- `.planning/phases/07-tui-shell-application-frame/07-CONTEXT.md` — Phase 7 decisions (D-01..D-21): SOC dark theme, keyboard navigation (`Ctrl+P`, `Ctrl+O`, `F1`), responsive breakpoints, offline-first execution.
- `.planning/phases/07-tui-shell-application-frame/07-VERIFICATION.md` — Phase 7 verified completion (12/12 must-haves, 122 tests green, CR-01 fixed, CR-02 deferred to Phase 8).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `manet/screens/main_workspace.py`: Current workspace shell to be upgraded from placeholder text to the live Executive Grid.
- `manet/runtime/theme.py`: Theme variables (`$primary`, `$secondary`, `$surface`, `$background`, `$success`, `$warning`, `$error`).
- `manet/commands/registry.py`: Command registry providing global shortcuts and navigation actions.
- `scenarios/`: Real scenario JSON definitions to be counted and validated by diagnostics.
- `ml/models/best_model.joblib`: Serialized champion model artifact (if generated).
- `ml/models/model_metadata.json`: Tracked JSON metadata providing champion model provenance (Random Forest, F1 0.7593, FPR 0.0099, Grayhole F1 0.0).
- `data/train.csv`, `data/test.csv`: Dataset files generated by `scripts/build_dataset.py`.

### Established Patterns
- Absolute imports within `manet` package (`from manet.screens import ...`).
- Pure presentation layer: TUI widgets never alter simulation business logic or re-train models directly.
- Standard Textual widgets: `Static`, `Label`, `Container`, `Horizontal`, `Vertical`, `DataTable`.
- Safe file probing: checking file existence and timestamps without holding file locks on Windows.

### Integration Points
- `manet/screens/main_workspace.py` composition: mount `DashboardCards` / `DiagnosticsPane` and `RecentExperiments` / `CtaPanel`.
- `manet/widgets/`: mount `StatusBar`, `NotificationRail`, `NavRail` adhering to D-03.
- `manet/adapters/`: define noop adapter interfaces for status, notifications, and navigation.
- Diagnostics adapter (`manet/adapters/diagnostics.py`): lightweight probe reading environment (`sys.version`, package imports), `scenarios/`, `data/`, and `ml/models/`.

</code_context>

<specifics>
## Specific Ideas

- Capability status tags should follow strict honesty:
  - Runtime Environment: `VERIFIED (Python 3.11.x, SimPy, NetworkX, Scikit-learn)` (mapping `sklearn` to distribution `scikit-learn` for metadata lookup)
  - Scenarios: `VERIFIED ({count} valid scenarios available in scenarios/)` (distinguishing valid presets from malformed JSON)
  - Datasets: `VERIFIED (data/train.csv, data/test.csv present)` or `UNAVAILABLE (Run python scripts/build_dataset.py --multi-attack)`
  - Champion Model:
    - If `ml/models/best_model.joblib` exists: metrics extracted dynamically from `model_metadata.json` (e.g. `PARTIAL (Random Forest: Blackhole F1 {val}, Grayhole F1 0.0 [Ineffective Detection])`). Missing metrics must not default to 0.0.
    - If `ml/models/best_model.joblib` missing: `UNAVAILABLE (Run python scripts/build_dataset.py --multi-attack && python -m ml.train && python -m ml.evaluate)`, explicitly distinguishing missing model binary from available historical metadata.
  - Active Workload: Workload: `IDLE (No active simulation)`; Engine State: `AODV Engine Ready (Offline)` (distinguishing engine availability from execution state, never claiming AODV is actively running when idle).
- Keyboard shortcuts and navigation:
  - `[S] Simulation (Phase 9 Notice)`, `[R] Results (Phase 11 Notice)`, `[Ctrl+O] Console (Logs/Diagnostics)`, `[Ctrl+P] Palette`, `[F1] Help`.
  - Reconcile the logs navigation requirement via `[Ctrl+O] Console` without advertising an unimplemented dedicated logs screen.
  - Keyboard bindings for S/R must be scoped to `MainWorkspace` so they never interfere with typing in the console input.
  - `NotificationAdapter` must have a bounded in-memory queue to safely handle repeated shortcut presses.
  - Workspace inspection in `WorkspaceAdapter` is strictly read-only; no mock runs are invented.

</specifics>

<deferred>
## Deferred Ideas

- In-TUI live model retraining / evaluation workload runner — Phase 10 / future scope (TUI-MLWORK).
- Full interactive experiment replay and packet-level animation — future milestone (VIZ-01).
- Advanced metric export center (PDF/HTML report generation) — future milestone.

### Reviewed Todos (not folded)
None — no pending todos existed.

</deferred>

---

*Phase: 08-Operational Dashboard*
*Context gathered: 2026-11-07*
