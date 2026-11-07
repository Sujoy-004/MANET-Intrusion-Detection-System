# Phase 8: Operational Dashboard - Context

**Gathered:** 2026-11-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 delivers the real Operational Dashboard on the `manet/` TUI main workspace, replacing placeholder static text with live, honest runtime capability diagnostics, active workload monitoring, and recent experiment summaries. It inspects Python version, required dependency availability (`simpy`, `networkx`, `sklearn`, `pandas`, `numpy`, `matplotlib`, `seaborn`), scenario files (`scenarios/*.json`), processed datasets (`data/processed/`), and champion ML model artifacts (`ml/models/champion_model.joblib`) with timestamp and version provenance. Explicit capability states (verified, experimental, partial, unavailable) are surfaced with zero mock values; Grayhole detection F1 of 0.0 is explicitly presented as ineffective detection. Phase 8 also provides a guided first-run experience when `.manet-workspace/` has no experiments and quick navigation to simulation, results, logs, and help. It does NOT implement simulation execution workflows (Phase 9), background worker processes (Phase 10), or persistent manifest history browsing (Phase 11).

</domain>

<decisions>
## Implementation Decisions

### Layout & Information Hierarchy
- **D-01:** Top Status Cards with Split Body (Executive Grid) layout. The operational dashboard organizes high-level system diagnostics across top status cards (System Health, Component Capabilities, Active Workload/Threat Status), with a split lower body dedicated to Recent Experiments / First-Run CTA and quick navigation shortcuts. Responsive `HORIZONTAL_BREAKPOINTS` automatically reflow multi-column cards into a single vertical stream on compact viewports (down to 80x24). — **Reversibility:** costly — defines the widget composition and mounting hierarchy of `MainWorkspace`.

### Capability Diagnostics & Refresh Behavior
- **D-02:** Periodic Background Polling (every 3–5 seconds). Capability diagnostics evaluate system readiness on startup (`on_mount`) and periodically re-scan filesystem indicators (presence of scenario JSONs, datasets, and trained model artifacts) using lightweight, non-blocking file stat checks. This automatically discovers newly trained models or datasets without requiring an application restart. — **Reversibility:** reversible — timer interval and probe logic live in a self-contained diagnostic provider.

### Missing Component & Warning Presentation
- **D-03:** Inline Contextual Badges within Capability Cards. Missing components, unverified artifacts, and degraded models are rendered as inline badges directly inside their respective capability cards (e.g., `[amber]PARTIAL (Grayhole F1: 0.0)[/]`, `[red]UNAVAILABLE[/]`, `[green]VERIFIED[/]`). This preserves screen real estate and visual balance on compact terminals while maintaining absolute operational honesty per TUI-08 without intrusive top alert banners. — **Reversibility:** reversible.

### First-Run & Empty State Experience
- **D-04:** Guided Call-to-Action (CTA) Hero Panel. When launching the application on a fresh environment where no experiments exist in `.manet-workspace/`, the lower body displays a prominent, guided CTA panel orienting the user to their first action (e.g., "Ready for Simulation • Press [S] to configure and launch your first MANET scenario"). Once an experiment completes, the panel transitions to display the Recent Experiments summary table. — **Reversibility:** reversible.

### the agent's Discretion
- Concrete diagnostic probe adapter architecture (e.g. `manet/adapters/diagnostics.py` or `manet/runtime/diagnostics.py`).
- Exact card styling, borders, and badge text typography using existing Textual theme tokens (`$primary`, `$secondary`, `$success`, `$warning`, `$error`).
- Detailed metadata formatting for the champion model (e.g. training timestamp, accuracy, precision, recall, and Grayhole F1 callout).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engineering contract & specs
- `GEMINI.md` — binding contract: Python 3.11+, pure-Python SimPy discrete-event simulator, determinism, pathlib, zero mock values.
- `CHANGELOG.md` — authoritative project history and version records.
- `.planning/REQUIREMENTS.md` — TUI-06, TUI-07, TUI-08 (dashboard diagnostics, workload/experiment summaries, explicit capability states).
- `.planning/ROADMAP.md` — Phase 8 goal, dependencies, and success criteria.
- `MANET_IDS_BTech_Execution_Guide.md` — domain context on AODV routing, attack classes, Grayhole F1 0.0 baseline interpretation.

### Prior Phase Context
- `.planning/phases/07-tui-shell-application-frame/07-CONTEXT.md` — Phase 7 decisions (D-01..D-21): SOC dark theme, keyboard navigation (`Ctrl+P`, `Ctrl+O`, `F1`), responsive breakpoints, offline-first execution.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `manet/screens/main_workspace.py`: Current workspace shell to be upgraded from placeholder text to the live Executive Grid.
- `manet/runtime/theme.py`: Theme variables (`$primary`, `$secondary`, `$surface`, `$background`, `$success`, `$warning`, `$error`).
- `manet/commands/registry.py`: Command registry providing global shortcuts and navigation actions.
- `scenarios/`: Real scenario JSON definitions to be counted and validated by diagnostics.
- `ml/models/champion_model.joblib`: Real serialized champion model artifact to inspect for provenance and evaluation metrics.

### Established Patterns
- Absolute imports within `manet` package (`from manet.screens import ...`).
- Pure presentation layer: TUI widgets never alter simulation business logic or re-train models directly.
- Standard Textual widgets: `Static`, `Label`, `Container`, `Horizontal`, `Vertical`, `DataTable`.

### Integration Points
- `manet/screens/main_workspace.py` composition: replace `Static(WORKSPACE_CONTENT)` with `DashboardCards` / `DiagnosticsPane` and `RecentExperiments` / `CtaPanel`.
- Diagnostics adapter: lightweight utility reading environment (`sys.version`, package imports), `scenarios/`, `data/`, and `ml/models/`.

</code_context>

<specifics>
## Specific Ideas

- Capability status tags should follow strict honesty:
  - SimPy / NetworkX / Scikit-learn: `VERIFIED`
  - Scenarios: `VERIFIED ({count} scenarios available)` or `UNAVAILABLE`
  - Champion Model: `PARTIAL (Blackhole: 1.0 F1, Grayhole: 0.0 F1)` or `UNAVAILABLE`
  - Workload state: `IDLE (No active simulation)`
- Keyboard shortcuts clearly visible on dashboard footer / quick action panel: `[S] New Simulation`, `[R] Results / History`, `[O] Console`, `[P] Palette`, `[F1] Help`.

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
