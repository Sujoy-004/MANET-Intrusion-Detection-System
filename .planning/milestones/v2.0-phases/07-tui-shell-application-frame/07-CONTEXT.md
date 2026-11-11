# Phase 7: TUI Shell & Application Frame - Context

**Gathered:** 2026-11-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 delivers the `manet/` TUI application frame: the `python -m manet` launcher (no flags, offline-first), full-screen keyboard-first navigation with a searchable global command palette and a structured application-only command console, the dark SOC control-center theme (cyan navigation / blue info / green healthy / amber warning / red critical) with reduced-motion and high-contrast session options, terminal-size adaptation including compact mode, visible keyboard focus and shortcut hints, a modular architecture (screens / widgets / commands / adapters / runtime) containing placeholder surfaces for the deferred Phase 8–11 screens, and honest app identity (`MANET IDS`). It does NOT implement dashboard diagnostics (Phase 8), simulation workflow (Phase 9), background execution (Phase 10), results/experiment records (Phase 11), or the test/docs integration gate (Phase 12). Existing CLI entry points (`python -m simulator.run_scenario`, `scripts/*`, `python -m ml.train/evaluate`) remain the automation surface and behave unchanged.

</domain>

<decisions>
## Implementation Decisions

### Interface & Navigation (from user's Requirement Discovery Decision Record — approved 58-question record, 2026-11-06)
- **D-01:** [informational] (phase-wide standing decision — realized and verified by executed plans 07-01..04; not per-plan trackable) Hybrid interface — full-screen dashboard, interactive forms, live monitoring, keyboard navigation, plus command-entry capability (record Q1). — **Reversibility:** reversible
- **D-02:** [informational] (phase-wide standing decision — realized and verified by executed plans 07-01..04; not per-plan trackable) Keyboard + mouse interaction with a global searchable command palette; arrows navigate, Enter selects, Esc goes back, dedicated shortcuts for common actions (record Q2, final selection C). — **Reversibility:** reversible
- **D-03:** Screen organization is a hybrid information architecture: workspace-based navigation, global command palette, contextual submenus, persistent notifications, active workload indicators, global system status (record Q55). — **Reversibility:** costly — layout shell determines where every later screen's notifications/status/workload indicators mount
- **D-04:** App identity is exactly `MANET IDS`; no separate product branding (record Q50). — **Reversibility:** reversible

### Visual Design & Accessibility
- **D-05:** [informational] (phase-wide standing decision — realized and verified by executed plans 07-01..04; not per-plan trackable) Premium cybersecurity/SOC control-center aesthetic: dark, high contrast, structured panels, live telemetry placeholders, professional readable typography (record Q15). — **Reversibility:** reversible
- **D-06:** Color semantics fixed: multi-color SOC interface on dark background — cyan navigation, blue information, green healthy, amber warnings, red critical (record Q31). — **Reversibility:** reversible
- **D-07:** [informational] (phase-wide standing decision — realized and verified by executed plans 07-01..04; not per-plan trackable) Animations are performance-bounded and honest: progress indicators, live metric transitions, event highlighting allowed; NO decorative animation that hurts performance; effects automatically reduce on limited terminals; reduced visual effects as a session accessibility option (record Q32 final C, constrained by the task spec). — **Reversibility:** reversible
- **D-08:** Accessibility: readable labels, configurable colors, high-contrast mode, reduced visual effects, alternative status indicators (not color-only), screen-reader-friendly output where Textual supports it, configurable text density, visible keyboard focus indicators, contextual help (record Q28 final C). — **Reversibility:** reversible
- **D-09:** Session-only application settings: preferences reset on exit, no persistent configuration profiles; persistent experiment history/research artifacts live independently (record Q13 final A). — **Reversibility:** reversible

### Command Surface
- **D-10:** Command interface = global command palette + a dedicated structured command console; parameterized application commands, command history, contextual suggestions; NO unrestricted OS shell (record Q43 final C). — **Reversibility:** costly — command registry is enumerated across the app; refactoring it later re-touches every screen
- **D-11:** Palette surface for Phase 7: fuzzy search, categorized commands, command history, recent actions, context-sensitive commands (record Q23 — the standard registry features only). Shortcut customization, configurable aliases, and user-defined parameterization are DEFERRED (noted below). — **Reversibility:** reversible

### Architecture & Behavior
- **D-12:** Pure presentation layer: existing modules remain authoritative; lightweight adapters where necessary; no duplicated business logic; no backend rewriting; preserve existing architectural boundaries (record Q18). — **Reversibility:** one-way — this is the app's load-bearing structural contract; undoing it mid-implementation means re-architecting every screen
- **D-13:** [informational] (phase-wide standing decision — realized and verified by executed plans 07-01..04; not per-plan trackable) Modular internal architecture with independent modules and clearly defined boundaries; no external plugin ecosystem (record Q36 final B). Future ML/data-lab/IDS-admin/reporting screens are modular placeholders, clearly marked planned/unavailable. — **Reversibility:** reversible
- **D-14:** Offline-first: all core functionality runs locally; simulation and IDS work without internet; internet only for explicitly requested external operations (record Q44). — **Reversibility:** reversible
- **D-15:** [informational] (phase-wide standing decision — realized and verified by executed plans 07-01..04; not per-plan trackable) Single-user local application: no login, no authentication, OS filesystem permissions apply (record Q47). — **Reversibility:** reversible
- **D-16:** `python -m manet` from the repository root, no mandatory flags, starts the full-screen TUI (record Q25). — **Reversibility:** reversible
- **D-17:** [informational] (phase-wide standing decision — realized and verified by executed plans 07-01..04; not per-plan trackable) Terminal compatibility target is cross-platform (Windows first — it is the dev host; Linux/macOS in code design but only Windows verified in this delivery, untested platforms reported as such) (record Q14 final C, gated by the task spec's honesty rule). — **Reversibility:** reversible
- **D-18:** Terminal-size adaptation: responsive layouts, compact mode, resizable/adjustable panels, session-level layout restoration (record Q22). Layout presets stay session-level consistent with D-09. — **Reversibility:** reversible
- **D-19:** Make the TUI the default everyday experience while existing CLI functionality, scripts, and automation are preserved unchanged (record Q51). — **Reversibility:** reversible
- **D-20:** Engineering-driven decisions where feasibility is uncertain: inspect the existing codebase, choose by repository fit, never invent backend capabilities, never expose unimplemented capabilities as operational (record Q39/Q58 spirit, binding on shell placeholder states). — **Reversibility:** reversible
- **D-21:** [informational] (phase-wide standing decision — realized and verified by executed plans 07-01..04; not per-plan trackable) Process gate from the record: implementation proceeds phase by phase with verification before proceeding (record Q58 final B — architectural approval already given via the approved roadmap; this per-phase verify gate is the remaining obligation). — **Reversibility:** reversible

### the agent's Discretion
- Concrete Textual screens/widgets composition (Header/Footer/Sidebar vs. custom layout) — any faithful structure meeting D-01/D-03/D-18.
- Theming mechanism details within Textual (CSS variables/theme constants) as long as semantics follow D-06.
- Which concrete shortcuts are "dedicated for common actions" (D-02) and their default bindings.
- Placeholder screen presentation details ("Planned — Phase N" wording, disabled styling).
- Internal module split inside `manet/` (screens\b, widgets\b, commands\b, adapters\b, runtime\b) as long as it instantiates D-12/D-13.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engineering contract & history
- `GEMINI.md` — current binding engineering contract (successor of `AGENTS.md`): import boundaries, determinism, dependency-decision rule, `python -m` entry-point rule, pathlib rule. NOTE: the 2026-10-22 `.planning/codebase/*` maps cite `AGENTS.md` — that filename no longer exists; the same rules now live in `GEMINI.md`.
- `CHANGELOG.md` — authoritative project history (v1.0.0 2026-10-28, v1.1.0 2026-11-03 AODV route-recovery work). NOT the stale `.planning/` v1.0 archives.
- `README.md` — documented CLI workflows and pinned dependency line (`python -m pip install ...`) the TUI docs must extend.

### v2.0 planning artifacts
- `.planning/REQUIREMENTS.md` — TUI-01..TUI-21, DELV-01..03 (this phase: TUI-01..05) plus deferred/out-of-scope lists.
- `.planning/ROADMAP.md` — Phase 7 goal, success criteria, dependency/numbering context.
- `.planning/research/tui/SUMMARY.md` — Textual 8.2.8 framework decision, integration points, pitfalls.
- `.planning/STATE.md` — v2.0 tracking: Phase 7 of 12, 79-test baseline must hold.

### Codebase maps (context: pre-implementation, stale where marked)
- `.planning/codebase/CONVENTIONS.md` — project code-style rules (PEP 8, stdlib-first, no bare except, docstring rules); column/label naming that adapters must read but never rename.
- `.planning/codebase/STRUCTURE.md` — layout rationale; note the actual repo evolved (root `tests/` exists, `scripts/` added) — verify against the live tree.
- `docs/ARCHITECTURE.md` — generated current architecture overview for integration context.

### Framework
- Textual 8.2.8 docs (PyPI-verified; command palette, screens, theme system) — consult Context7/official docs during research/planning.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `simulator/run_scenario.py` + scenario loader — the composition root pattern Phase 7's launcher must NOT touch, only sit alongside (`python -m manet` is a new entry point, same `python -m` invocation style).
- `scripts/` experiment drivers — show the existing CLI UX the TUI must coexist with; nothing here changes.
- `docs/ARCHITECTURE.md` — current architecture summary usable as adapter-surface reference.

### Established Patterns
- Every invoked stage runs as a module (`python -m <pkg>.<mod>`); absolute first-party imports; package `__init__.py` with explicit `__all__`; pathlib everywhere; stdlib-first; dataclasses for structured records.
- Import boundary discipline (DAG, no cycles): `manet/` will be a NEW top-level package depending on existing packages (like `ml/run_evaluation.py` may import `simulator/`); no existing package may depend on `manet/`.
- Tests live in root `tests/` (actually built this way during v1.0, superseding the maps' per-package recommendation) — new `manet` tests follow the same root-`tests/` convention (`tests/test_manet_*.py`).

### Integration Points
- New `manet/` package root with `manet/__main__.py` (+ `__init__.py`) providing `python -m manet`.
- Dependency addition goes through the repo's dependency-decision rule (record in README pinned install line + CHANGELOG entry; contract sync in same commit).
- Session history/results adapters belong to Phase 11; workload/workers belong to Phase 10 — Phase 7 defines only their mounting points (status bar, notification area) and noop adapters.

</code_context>

<specifics>
## Specific Ideas

- The user supplied a completed 58-question Requirement Discovery Decision Record (Requirement Discovery, Q1–Q58) — the approved product surface for `MANET IDS`. This CONTEXT carries its Phase-7-relevant decisions verbatim in intent; the full record text was provided in-session and its scope mapping is captured in `<decisions>` + `<deferred>`.
- Visual reference intent: "premium cybersecurity/SOC control-center" with structured panels and live-telemetry aesthetics — implemented as Textual panels/surfaces, not terminal art.

</specifics>

<deferred>
## Deferred Ideas

Ideas surfaced by the record that belong to later phases (kept so nothing is lost):

### Assigned to v2.0 phases
- Dashboard diagnostics, dependency inspection, capability states — Phase 8 (record Q21, Q26, Q53).
- Preset/custom simulation forms, review/confirm — Phase 9 (record Q4, Q11).
- Background execution, controls, bounded live telemetry — Phase 10 (record Q5, Q6, Q20, Q41, Q42, Q48).
- Experiment records, history, manifests, checksums — Phase 11 (record Q7, Q8, Q33, Q46, Q56).

### Deferred beyond v2.0's six planned phases (future milestones)
- Resource/monitoring screens (CPU/RAM/disk live graphs, thresholds) — record Q27.
- In-TUI test runner / health verification screens — record Q29.
- Reports & export center (CSV/JSON/HTML/PDF, bundles) — record Q24.
- Alerts center (acknowledge/group/export alert history) — record Q17.
- Dashboard panel customization presets — record Q52.
- Storage lifecycle management (retention, archival, storage analytics) — record Q49.
- ML management (Q9), dataset management (Q10), IDS operations center (Q54), topology visualization (Q12), live network monitoring (Q12) — the planned-advanced v2.0 "Also available" screens.
- Version/update checks via Git + changelog viewer — record Q35 (a help/about screen may include static version info in Phase 7 discretion; active update checking deferred).
- Shortcut customization, configurable aliases, user-defined parameterized bindings — the deferred third of record Q23.
- Notifications escalation, diagnostic snapshots beyond error log capture — remainder of record Q16/Q17.

### Reviewed Todos (not folded)
None — no pending todos existed.

</deferred>

---

*Phase: 7-TUI Shell & Application Frame*
*Context gathered: 2026-11-06*
