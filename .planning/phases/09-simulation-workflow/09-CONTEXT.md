# Phase 9: Simulation Workflow - Context

**Gathered:** 2026-11-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 9 delivers the simulation configuration, parameter validation, review, and workspace allocation workflows in the `manet/` TUI application. It enables the user to select and inspect authentic preset scenario files from `scenarios/*.json` (reading live schemas rather than documented examples) or configure custom simulation parameters. It enforces strict validation on node counts, duration, numeric ranges, flow endpoints, and random seeds. It strictly gates the IDS toggle on the presence of the champion model artifact (`ml/models/best_model.joblib`), disabling it with clear explanatory feedback if absent. Before launching, a dedicated review screen summarizes the full configuration and allocates a unique, collision-free experiment directory under `.manet-workspace/` with an initial launch record capturing scenario, seed, configuration, software version, and start timestamp. Phase 9 wires the workflow up to the execution handoff boundary using the existing `SimulationRunner`, scenario loader, and metric functions, compatible with the current trace schema and legacy CLI behavior. It does NOT implement background worker thread lifecycle, live event streaming, cancellation/interruption signals, or progress bars (Phase 10), nor does it implement results inspection, checksumming, or persistent session history browsing (Phase 11).

</domain>

<decisions>
## Implementation Decisions

### Screen Flow & Navigation
- **D-01:** Multi-Step Guided Wizard architecture (`SimulationWorkflowScreen` / `WizardController`) with three clear sequential steps:
  1. **Step 1: Scenario & Mode Selection**: Choose between authentic presets discovered from `scenarios/*.json` (displaying real names, descriptions, node count, duration) or creating a custom simulation.
  2. **Step 2: Parameter Configuration**: Edit core simulation variables (nodes, duration, seed, attacker strategy, IDS toggle) with progressive disclosure for advanced networking dials.
  3. **Step 3: Pre-Flight Review & Confirmation**: View a consolidated summary of all parameters, estimated scale, champion model status, collision-free workspace destination, and confirm launch.
  - **Reversibility:** costly — defines the wizard controller, step navigation messages, and widget mounting hierarchy in `manet/screens/`.

### Input Validation & Guidance
- **D-02:** Two-Tier Validation Strategy:
  - **Tier 1 (Local Field Blur Validation):** Form inputs use Textual's blur validation (`validate_on=["blur"]`) to validate basic syntax, positive integers, and range boundaries (e.g. nodes >= 2, duration > 0, integer seed) without premature error flashes during active typing.
  - **Tier 2 (Pre-Flight Review Blocker):** Structural cross-field invariants (e.g. flow source/destination within node count, distinct flow endpoints, and on-disk model artifact verification `ml/models/best_model.joblib` when IDS is enabled) are evaluated prior to review. The final "Launch" action is strictly disabled with actionable remediation notes if validation fails.
  - **Reversibility:** reversible — validation logic lives in modular schemas and adapters under `manet/adapters/`.

### Custom Parameter Depth
- **D-03:** Progressive Disclosure Layout:
  - **Primary Core Form:** Displays the 5 essential macro parameters by default (Nodes, Duration, Random Seed, Attacker Class [None, Blackhole, Grayhole], and IDS Mitigation Toggle). Fits cleanly in standard and compact terminals (80x24) without layout distortion.
  - **Collapsible Advanced Section:** An expandable container (`Collapsible`) pre-populated with standard benchmark defaults allowing override of granular knobs (Radio Range: 250.0m, Channel Loss Probability: 0.0, Mobility Speed: 1.0-20.0 m/s, Pause Time: 0.0s, CBR Packet Rate: 4.0 pkt/s, Area: 1000x1000m).
  - **Reversibility:** reversible — configuration builder maps defaults to the standard runner schema.

### Experiment Naming & Workspace Allocation
- **D-04:** Deterministic Identifier with Optional Semantic Tag:
  - **Default Unique Identifier:** Automatically generated as `exp_YYYYMMDD_HHMMSS_<scenario>_<seed>`.
  - **Optional Custom Tag:** Provides an optional "Run Tag / Label" field; when supplied, the identifier becomes `exp_YYYYMMDD_HHMMSS_<scenario>_<seed>_<sanitized_tag>`.
  - **Workspace Directory Allocation:** Generates a dedicated directory under `.manet-workspace/<experiment_id>/` without overwriting existing traces, datasets, models, or experiment records.
  - **Input Sanitization:** Automatically strips spaces, symbols, and Windows-illegal path characters (`\ / : * ? " < > |`) from user-provided tags.
  - **Reversibility:** reversible.

### the agent's Discretion
- Exact Textual widget composition for preset scenario lists (e.g. `OptionList` vs. `DataTable` with scenario details).
- Visual badge styling and color mapping (`$primary`, `$success`, `$warning`, `$error`) for validation messages and IDS gating notices.
- Launch execution handoff adapter interface structure connecting Phase 9 review confirmation to Phase 10's background runner.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engineering contract & specs
- `GEMINI.md` — binding contract: Python 3.11+, pure-Python SimPy discrete-event simulator, determinism, explicit integer seeds, zero mock values, Windows-safe paths.
- `CHANGELOG.md` — authoritative project history and version records.
- `README.md` — documented CLI workflows, scenario paths, and model training instructions.
- `.planning/REQUIREMENTS.md` — TUI-09 through TUI-14 (simulation workflow requirements).
- `.planning/ROADMAP.md` — Phase 9 goal, dependencies, and success criteria.

### Prior Phase Context
- `.planning/phases/07-tui-shell-application-frame/07-CONTEXT.md` — Phase 7 decisions (D-01..D-21): SOC theme, keyboard navigation (`[S]`, `[Esc]`, `[Enter]`), responsive layout, offline-first execution.
- `.planning/phases/08-operational-dashboard/08-CONTEXT.md` — Phase 8 decisions (D-01..D-05): real diagnostic probes, model metadata inspection (`ml/models/model_metadata.json`), capability honesty.

### Existing Simulation Code & Schemas
- `simulator/run_scenario.py` — authoritative CLI runner, `SimulationRunner`, `NodeState`, config parameters, trace header schema.
- `simulator/scenario.py` / `scenarios/*.json` — authentic scenario schemas (e.g. `e1_normal_30n.json`, `e2_blackhole_30n.json`, `e4_grayhole_50n.json`).
- `simulator/metrics.py` — metric calculation functions (`compute_metrics`).
- `ml/models/model_metadata.json` — champion model metadata and provenance.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `manet/adapters/diagnostics.py` — already probes filesystem for scenario JSON count and champion model presence; can be reused or extended for scenario metadata discovery.
- `manet/adapters/workspace.py` — existing workspace adapter for scanning `.manet-workspace/`; needs directory allocation logic.
- `scenarios/*.json` — authentic preset scenario definitions ready for direct loading.
- `simulator/run_scenario.py` — `SimulationRunner` composition root and argument parser logic showing parameter bounds and types.

### Established Patterns
- All application logic under `manet/` cleanly separated into `screens/`, `widgets/`, `adapters/`, `commands/`, `runtime/`.
- Keyboard-first interaction: Tab/Shift+Tab navigation, Enter to select/proceed, Esc to cancel/back out.
- Responsive breakpoints down to 80x24 terminal windows without horizontal clipping.
- Absolute imports throughout `manet`.

### Integration Points
- `manet/screens/main_workspace.py` — shortcut `[S]` navigates to the new `SimulationWorkflowScreen` instead of showing a placeholder notice.
- `manet/commands/registry.py` — command palette action `sim:start` launches the simulation workflow screen.
- `manet/adapters/` — add simulation scenario adapter / workflow validator to inspect presets and prepare run payloads for Phase 10.

</code_context>

<specifics>
## Specific Ideas

- The simulation workflow screen replaces the Phase 8 "Phase 9 Notice" on pressing `[S]`.
- Preset scenario list loads all `.json` files from `scenarios/`, extracting scenario name, node count, duration, attack strategy, and description from the actual file.
- IDS Toggle must be visually disabled with an explanatory tooltip or inline badge if `ml/models/best_model.joblib` is missing from disk, referencing `python scripts/build_dataset.py --multi-attack && python -m ml.train`.
- Custom configuration pre-fills safe default values (e.g. 30 nodes, 100s duration, seed 42) to minimize typing required for standard test runs.
- Review screen clearly displays the target workspace path (e.g. `.manet-workspace/exp_20261107_141500_e1_42/`) before asking for final launch confirmation.

</specifics>

<deferred>
## Deferred Ideas

- Background worker thread execution and live progress polling — Phase 10 (TUI-15, TUI-16, TUI-17, TUI-18).
- Experiment results viewer, manifest checksum generation, and session history browsing — Phase 11 (TUI-19, TUI-20, TUI-21).
- In-TUI live model retraining / evaluation workload runner — Phase 10 / future scope (TUI-MLWORK).
- Interactive packet replay and animation — future milestone (VIZ-01).

### Reviewed Todos (not folded)
None — no pending todos existed.

</deferred>

---

*Phase: 09-Simulation Workflow*
*Context gathered: 2026-11-07*
