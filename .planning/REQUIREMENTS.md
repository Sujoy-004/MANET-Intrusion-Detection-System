# Requirements: Milestone v2.0 — Interactive TUI Application

Locale note: REQ-IDs follow the v1.0 convention ([CATEGORY]-[NN]). New category prefix `TUI` plus continuation categories `DELV` (delivery/documentation). Numbering starts at 01 for v2.0 categories.

## v2 Requirements

### TUI Shell & Launcher

- [ ] **TUI-01**: User can launch the full-screen `MANET IDS` terminal application from the repository root via `python -m manet` with no required flags, usable offline (local-first)
- [ ] **TUI-02**: TUI code lives entirely in a new `manet/` package with clean separation of screens, widgets, commands, adapters, and runtime — no simulation, routing, feature-extraction, or IDS logic duplicated
- [ ] **TUI-03**: User can navigate every screen keyboard-first (arrows, Enter, Esc) with visible keyboard focus and visible shortcut hints, and the layout adapts to terminal resizing including a compact mode for small windows
- [ ] **TUI-04**: User can open a global searchable command palette and a structured application-command console; the console exposes application commands only and performs no operating-system shell execution
- [ ] **TUI-05**: User experiences the dark cybersecurity palette (cyan navigation, blue information, green healthy, amber warning, red critical) with reduced-motion and high-contrast options where the framework supports them; preferences are session-only (no persistent profiles)

### Dashboard

- [ ] **TUI-06**: User can view a real operational dashboard showing startup diagnostics: Python version, required dependency availability, and availability of scenario files, datasets, and model artifacts
- [ ] **TUI-07**: User can view active workload state and recent experiment summaries (when available) on the dashboard, with quick navigation to simulation, results, logs, and help
- [ ] **TUI-08**: User sees explicit capability states — verified, experimental, partial, unavailable — with no mock values displayed and no claim of model or dataset existence when files are missing; model metadata is reported with its timestamp/version context and current Grayhole F1 of 0.0 is presented as not-effective detection

### Simulation Workflow

- [ ] **TUI-09**: User can start a validated preset run by choosing a scenario JSON from `scenarios/` shown with its real name, description, and relevant parameters (actual file schema, not documented examples)
- [ ] **TUI-10**: User can start a custom run configuring only parameters the actual runner supports, with validation of node counts, flow endpoints, durations, seed, and numeric ranges
- [ ] **TUI-11**: User can select the random seed explicitly for any run
- [ ] **TUI-12**: User can enable IDS only when the champion model artifact exists, and never otherwise
- [ ] **TUI-13**: User confirms a review screen before any run launches, and each run executes into a unique experiment directory under a dedicated `.manet-workspace/` without overwriting existing traces, datasets, models, or experiment records
- [ ] **TUI-14**: Each experiment records scenario, seed, configuration, software version, and start time at launch, using the existing `SimulationRunner`, scenario loader, and metric functions with output compatible with the current trace schema and legacy CLI behavior

### Execution & Live Feedback

- [ ] **TUI-15**: User can interact with the TUI without it freezing while a simulation runs in the background, with architecture supporting one simulation workload and one ML workload at a time (simulation execution implemented and verified in this delivery)
- [ ] **TUI-16**: User sees run status, elapsed time, measurable progress, and current stage, with bounded live event/log streaming that never blocks the simulator and never retains unbounded telemetry in memory
- [ ] **TUI-17**: User can Ctrl+C, Esc, or shut down the application without corrupting result files; existing simulation semantics (event ordering, results) are preserved regardless of UI interaction, and UI callbacks cannot change simulation or IDS decisions
- [ ] **TUI-18**: User can stop a running simulation safely; pause/resume is presented as disabled because the runner does not support it safely; an interrupted run preserves partial traces and is marked interrupted; worker exceptions surface actionable diagnostics with no silent retries and no mislabeling of partial runs as completed

### Results & Experiment Records

- [ ] **TUI-19**: User can view completed-run results showing actual PDR, throughput, delay, and routing overhead computed via the existing `simulator.metrics.compute_metrics`, plus sent/received packet counts and the generated trace location
- [ ] **TUI-20**: Each experiment stores a manifest (experiment ID, configuration, seed, software version, run status, timestamps, logs, trace paths, available metrics) written atomically, with SHA-256 checksums for completed artifacts
- [ ] **TUI-21**: User can browse a session history list and open a past result; completed experiment metadata is read-only (reruns create new runs); workspace artifacts are ignored by Git without changing `.gitignore` semantics unintentionally; safe cleanup, if implemented, requires preview and explicit confirmation

### Quality & Delivery

- [ ] **DELV-01**: User enjoys unchanged behavior: existing CLI entry points still work, existing tests pass unweakened, and the full suite plus new feature tests (launcher/command parsing, capability detection incl. missing artifacts, scenario discovery/validation, worker success/failure/cancel/partial, manifest atomicity/checksums/history, CLI compatibility, import boundaries, bounded telemetry under load) pass on the current host
- [ ] **DELV-02**: User can follow updated README documentation for the launch command, TUI dependency installation, limitations, supported terminals, and keyboard shortcuts, and CHANGELOG.md records the feature; documentation matches executable behavior with no untested cross-platform claims
- [ ] **DELV-03**: User gets an honest completion report: changed files, architecture and framework rationale, commands run with exact test results, and clearly listed known limitations and deferred features

## Future Requirements (deferred)

- **TUI-ADV**: Advanced research/administration screens — ML training workflow, data lab, advanced IDS monitoring, reporting (modular placeholders only in v2.0)
- **TUI-MLWORK**: One-ML-workload execution path (runner integration for training/evaluation inside the TUI)
- **TUI-PAUSE**: Run pause/resume if the simulator ever gains safe checkpointing
- Project-level future features remain: ATK-04 (RREQ Flooding/DoS), VIZ-01 (web replay dashboard), XAI-01 (SHAP explainability)

## Out of Scope

- Persistent settings profiles or preference files — session-only per task spec
- Any database, plugin system, web server, or cloud dependency — local-first terminal application only
- Unrestricted OS shell execution from the command console — application commands only
- Mock/demo data presented as live project output — dashboard and results must reflect real project state
- Edits to scenario JSON fixtures purely for TUI convenience
- Git commits/pushes during the implementation run — no remote state changes
- Unbounded live telemetry retention in memory

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TUI-01 | Phase 7 — TUI Shell & Application Frame | Pending |
| TUI-02 | Phase 7 — TUI Shell & Application Frame | Pending |
| TUI-03 | Phase 7 — TUI Shell & Application Frame | Pending |
| TUI-04 | Phase 7 — TUI Shell & Application Frame | Pending |
| TUI-05 | Phase 7 — TUI Shell & Application Frame | Pending |
| TUI-06 | Phase 8 — Operational Dashboard | Pending |
| TUI-07 | Phase 8 — Operational Dashboard | Pending |
| TUI-08 | Phase 8 — Operational Dashboard | Pending |
| TUI-09 | Phase 9 — Simulation Workflow | Pending |
| TUI-10 | Phase 9 — Simulation Workflow | Pending |
| TUI-11 | Phase 9 — Simulation Workflow | Pending |
| TUI-12 | Phase 9 — Simulation Workflow | Pending |
| TUI-13 | Phase 9 — Simulation Workflow | Pending |
| TUI-14 | Phase 9 — Simulation Workflow | Pending |
| TUI-15 | Phase 10 — Background Execution & Live Feedback | Pending |
| TUI-16 | Phase 10 — Background Execution & Live Feedback | Pending |
| TUI-17 | Phase 10 — Background Execution & Live Feedback | Pending |
| TUI-18 | Phase 10 — Background Execution & Live Feedback | Pending |
| TUI-19 | Phase 11 — Results & Experiment Records | Pending |
| TUI-20 | Phase 11 — Results & Experiment Records | Pending |
| TUI-21 | Phase 11 — Results & Experiment Records | Pending |
| DELV-01 | Phase 12 — Quality, Testing & Delivery | Pending |
| DELV-02 | Phase 12 — Quality, Testing & Delivery | Pending |
| DELV-03 | Phase 12 — Quality, Testing & Delivery | Pending |

Deferred (not on this roadmap): TUI-ADV, TUI-MLWORK, TUI-PAUSE (plus project-level ATK-04, VIZ-01, XAI-01).
