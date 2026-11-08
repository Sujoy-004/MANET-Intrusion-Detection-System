---
phase: 09-simulation-workflow
plan: "03"
subsystem: integration-testing
tags: [textual, textual-pilot, simulation-runner, trace-schema, manifest-parity, import-boundaries, pytest]

requires:
  - phase: 09-simulation-workflow
    plan: "02"
    provides: SimulationWorkflowScreen 3-step wizard, wizard widgets, Task 1 [S]/sim:start wiring (commit d990673)
  - phase: 06-simulation-stack-v1.0
    provides: simulator.run_scenario.SimulationRunner, simulator.metrics.compute_metrics, canonical trace format
provides:
  - Verified [S] shortcut on MainWorkspace and sim:start palette command opening SimulationWorkflowScreen directly
  - End-to-end compatibility test suite tests/test_manet_simulation_runner_compat.py proving preset (ScenarioAdapter) and custom (CustomScenarioBuilder) configurations are fully consumable by SimulationRunner
  - Exact canonical SimulationRunner.TRACE_HEADER schema assertions on all generated traces
  - manifest.json launch-record parity assertions (CONFIGURED status, experiment identity, seed, exact configuration dict)
  - Confirmed-zero architectural import violations via AST boundary regression (manet/ never imports simulator, attacks, feature_extraction, ml)
affects: [10-background-execution, 11-results-experiment-records]

actuals:
  tokens: 10300
  tasks: 2
  commits: 2
  plan_head_before: eb1d0633f24b8a5d6bc290ae2cb9367add6576fc
  plan_head_after: ec6f74f78eada80ece72acb0b7436466a36e23d0

tech-stack:
  added: []  # zero new dependencies (threat T-09-SC mitigation honored)
  patterns: [canonical trace-header schema assertion, manifest launch-record parity check, short-duration compat runs, AST import-boundary regression]

key-files:
  created:
    - tests/test_manet_simulation_runner_compat.py
    - .planning/phases/09-simulation-workflow/09-03-SUMMARY.md
  modified:
    - manet/app.py
    - manet/commands/registry.py
    - manet/screens/main_workspace.py
    - tests/test_manet_navigation.py
    - tests/test_manet_command_palette.py
    - .planning/STATE.md
    - .planning/ROADMAP.md
    - .planning/REQUIREMENTS.md
    - .planning/milestone.lock

key-decisions:
  - "Verified SimulationRunner compatibility against the REAL runner API (scenario_config, seed, out_path trace CSV + run(duration=...)) rather than the plan's sketched output_dir kwarg; workspace directories come from WorkspaceAdapter.allocate_experiment_directory()"
  - "Used short compat durations (2.0s-5.0s, all under the 10.0s cap required by threat T-09-09) with a duration override on preset copies so tests finish in seconds"
  - "IDS-gating compat test mirrors wizard gating in both branches: champion model present -> runner.online_ids wired; model absent -> structural invariant rejects ids_enabled with champion-model-artifact error"
  - "Palette regression: query 'work' was ambiguous after sim:start registration; tightened to 'workspace' and added explicit 'workflow' -> 'Start Simulation Workflow' assertion"

patterns-established:
  - "Canonical trace assertion: every generated trace header must equal SimulationRunner.TRACE_HEADER exactly"
  - "Manifest parity: manifest.json 'configuration' must equal the exact configuration dict produced by the builder/adapter"
  - "Boundary regression at close of every presentation-layer plan: AST tests re-run to prove manet/ stays import-free of business packages"

requirements-completed:
  - TUI-09
  - TUI-10
  - TUI-11
  - TUI-12
  - TUI-13
  - TUI-14

coverage:
  - id: D1
    description: "[S] shortcut and sim:start command open SimulationWorkflowScreen from MainWorkspace; Esc returns to MainWorkspace"
    requirement: TUI-09
    verification:
      - kind: unit
        ref: "tests/test_manet_navigation.py#test_simulation_shortcut_opens_workflow_screen"
        status: pass
      - kind: unit
        ref: "tests/test_manet_navigation.py#test_sim_start_command_opens_simulation_workflow"
        status: pass
      - kind: other
        ref: "static check: ManetApp.SCREENS['simulation_workflow'] registered, MainWorkspace.action_simulation switches screen, AppCommand sim:start action=action_show_simulation (programmatic True x4)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Preset scenario configurations discovered by ScenarioAdapter execute cleanly in SimulationRunner with non-empty canonical-schema trace"
    requirement: TUI-14
    verification:
      - kind: integration
        ref: "tests/test_manet_simulation_runner_compat.py#test_preset_scenarios_compatibility_with_simulation_runner"
        status: pass
    human_judgment: false
  - id: D3
    description: "Custom configurations from CustomScenarioBuilder (nodes, duration, seed, attacker type, advanced dials) execute in SimulationRunner; trace matches canonical header; manifest.json launch record matches CONFIGURED configuration"
    requirement: TUI-14
    verification:
      - kind: integration
        ref: "tests/test_manet_simulation_runner_compat.py#test_custom_scenario_builder_compatibility_with_simulation_runner"
        status: pass
      - kind: integration
        ref: "tests/test_manet_simulation_runner_compat.py#test_custom_grayhole_scenario_compatibility_with_simulation_runner"
        status: pass
    human_judgment: false
  - id: D4
    description: "IDS gating parity in compat tests: structured invariant rejects ids_enabled without champion model artifact; OnlineIDS wired when artifact exists"
    requirement: TUI-12
    verification:
      - kind: integration
        ref: "tests/test_manet_simulation_runner_compat.py#test_custom_scenario_with_ids_enabled_compatibility"
        status: pass
    human_judgment: false
  - id: D5
    description: "AST import boundaries intact: manet/ never imports simulator, attacks, feature_extraction, ml; commands never import OS execution primitives"
    verification:
      - kind: unit
        ref: "tests/test_manet_import_boundaries.py#test_manet_never_imports_business_packages"
        status: pass
      - kind: unit
        ref: "tests/test_manet_import_boundaries.py#test_command_package_never_uses_os_execution"
        status: pass
    human_judgment: false
  - id: D6
    description: "Full project test suite regression passes cleanly with all Phase 9 tests included"
    verification:
      - kind: other
        ref: "command invocation: python -m pytest tests -q -> 176 passed, 1 warning in 167.38s"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-11-08
status: complete
---

# Phase 9 Plan 03: SimulationRunner Compatibility and Boundary Regression Summary

**End-to-end compatibility proof that wizard-generated scenario configurations (preset and custom) execute through the real `SimulationRunner` with canonical trace schema and manifest parity — plus verified `[S]`/`sim:start` wizard wiring and zero import-boundary violations; full suite 176 passed.**

## Performance

- **Duration:** 10 min (resumed session — Task 1 had been committed by the interrupted prior session as `d990673`; this session re-verified Task 1 acceptance criteria on disk, then finalized and committed Task 2)
- **Started:** 2026-11-08T03:48:32Z
- **Completed:** 2026-11-08T03:59:00Z
- **Tasks:** 2
- **Files modified:** 11 (5 production/test files + 6 planning/tracking files)

## Accomplishments

- Re-verified Task 1 wiring on disk after resume: `ManetApp.SCREENS["simulation_workflow"]` registered, `MainWorkspace.action_simulation` switches screen (with screen-focus/Input guards), `AppCommand("sim:start", ...)` present with `action="action_show_simulation"` — all programmatically confirmed.
- Navigation suite fully green (16 tests): pressing `[S]` opens `SimulationWorkflowScreen`, `Esc` returns to `MainWorkspace`, and `sim:start` from the console opens the wizard and Esc returns.
- Created 4 end-to-end compatibility tests in `tests/test_manet_simulation_runner_compat.py`: preset scenarios from `ScenarioAdapter` and custom scenarios from `CustomScenarioBuilder` (Blackhole with advanced dials, Grayhole with drop probability, IDS-enabled branching) all execute through the real `simulator.run_scenario.SimulationRunner` without schema divergence.
- All generated traces assert the exact canonical `SimulationRunner.TRACE_HEADER` (`time,src,dst,pkt_id,type,hop_count,dropped_by,node_id,speed,neighbor_count`) with non-empty rows.
- `manifest.json` launch-record parity verified: experiment_id, scenario_name, seed, `CONFIGURED` status, and the exact configuration dict recorded by `record_launch_manifest`.
- AST import boundary regression green (2 tests) — `manet/` still never imports `simulator`, `attacks`, `feature_extraction`, or `ml`; `manet/commands/` still never imports OS execution primitives.
- Full project test suite regression: **176 passed, 0 failed** (79 baseline + 97 manet) — up from the 148-test v2.0 baseline with all Phase 9 tests included.

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire Main Workspace Shortcut [S] and Command Palette Action** - `d990673` (feat, committed by interrupted prior session; acceptance criteria re-verified on disk this session)
2. **Task 2: End-to-End SimulationRunner Compatibility and Boundary Regression** - `ec6f74f` (test)

_Plan metadata was committed together with this SUMMARY (`docs(09-03)`)._

## Files Created/Modified

- `tests/test_manet_simulation_runner_compat.py` - NEW: 4 end-to-end compatibility tests (preset + custom + grayhole + IDS-gating parity) with canonical TRACE_HEADER and manifest-parity assertions
- `manet/app.py` - Registers `"simulation_workflow": SimulationWorkflowScreen` and `action_show_simulation` (Task 1)
- `manet/commands/registry.py` - `sim:start` AppCommand (`display="Start Simulation Workflow"`, `action="action_show_simulation"`, `parameters=()`) (Task 1)
- `manet/screens/main_workspace.py` - `action_simulation` switches to `"simulation_workflow"` instead of the Phase 8 placeholder notice; keeps screen-focus and Input guards; `action_new_simulation = action_simulation` (Task 1)
- `tests/test_manet_navigation.py` - `test_simulation_shortcut_opens_workflow_screen`, back-compat alias `test_simulation_shortcut_triggers_notice`, and `test_sim_start_command_opens_simulation_workflow` (Task 1)
- `tests/test_manet_command_palette.py` - Palette search assertions adjusted: `'work'` -> `'workspace'` exact hit plus new `'workflow'` -> `'Start Simulation Workflow'` hit (Task 2)

## Decisions Made

- Verified `SimulationRunner` against its real constructor contract (`scenario_config`, `seed`, `out_path` for the trace CSV) and `run(duration=...)`; the wizard-relevant workspace directory is allocated by `WorkspaceAdapter.allocate_experiment_directory()` and the manifest by `record_launch_manifest()` — mirroring the actual Phase 9 handoff rather than a sketched-but-nonexistent `output_dir` kwarg.
- Kept compat durations at 2.0s-5.0s with `date`-style tamper-free preset copies, honoring threat T-09-09 (short simulated runs, <= 10.0s).
- Mirrored the wizard's IDS gating in the compat suite both ways: structural invariant rejects `ids_enabled` without `ml/models/best_model.joblib`, and `runner.online_ids` is wired when the artifact is present.
- Marked TUI-09..TUI-14 satisfied in REQUIREMENTS.md after this plan (all three declaring plans 09-01, 09-02, 09-03 now have summaries — shared-ID gate satisfied).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] SimulationRunner API alignment (plan sketched non-existent `output_dir` kwarg)**
- **Found during:** Task 2 (compat test drafted by interrupted session; finalized and verified in this session)
- **Issue:** Plan action sketched `SimulationRunner(scenario_dict, seed=42, output_dir=tmp_workspace)`; the actual `simulator/run_scenario.py` API is `SimulationRunner(scenario_config, seed, out_path: Optional[Path])` with `run(duration=None)` — there is no `output_dir` parameter.
- **Fix:** Compat tests construct `SimulationRunner(scenario_config=..., seed=..., out_path=...)` with trace paths inside `tmp_path` (or the allocated experiment directory), call `runner.run(duration=...)`, and allocate the workspace directory + manifest via `WorkspaceAdapter`/`record_launch_manifest`, faithfully reproducing the wizard handoff.
- **Files modified:** tests/test_manet_simulation_runner_compat.py
- **Verification:** All 4 compat tests pass against the real runner (preset, custom Blackhole, custom Grayhole, IDS-gating branches).
- **Committed in:** ec6f74f

**2. [Rule 1 - Bug/Regression] Command palette search collision for query 'work'**
- **Found during:** Task 2 (regression scope; adjustment drafted by interrupted session, verified in this session)
- **Issue:** `tests/test_manet_command_palette.py` asserted exactly 1 fuzzy hit for query `'work'`; after Task 1 registered the `sim:start` display `'Start Simulation Workflow'`, the query `'work'` matched both `'Go to workspace'` and the simulation entry, breaking the assertion.
- **Fix:** Tightened the existing fuzzy-scoring assertion's query to `'workspace'` (still exactly 1 hit: 'Go to workspace') and added a positive assertion that `'workflow'` returns exactly 1 hit, `'Start Simulation Workflow'`.
- **Files modified:** tests/test_manet_command_palette.py
- **Verification:** `python -m pytest tests/test_manet_command_palette.py -q` -> 6 passed.
- **Committed in:** ec6f74f (note: this file was not in the plan's `files_modified` frontmatter — impact is one additional touched test file)

---

**Total deviations:** 2 auto-fixed (1 blocking API alignment, 1 regression collision).
**Impact on plan:** Both fixes were necessary to satisfy the plan's must-have that preset/custom configurations are consumable by `SimulationRunner` without divergence while keeping the suite green. No scope creep.

## Issues Encountered

None. The interrupted-session resume reconciled cleanly: Task 1 acceptance criteria held on disk with its commit `d990673` intact, and the drafted Task 2 test file required no structural changes to pass against the real runner APIs.

## Threat Register Verification

- **T-09-08 (Elevation of Privilege, mitigated):** `manet/commands/registry.py` still resolves only string action method names on `ManetApp`; `sim:start` -> `action_show_simulation` (no callables, no shell) — verified programmatically and by the untouched security boundary tests (`test_command_package_never_uses_os_execution` passes).
- **T-09-09 (Denial of Service, mitigated):** all compat simulations run 2.0s-5.0s, comfortably under the 10.0s cap; full suite completes in under 3 minutes.
- **T-09-SC (Tampering, mitigated):** zero new dependencies added for this plan (`tech-stack.added: []`).

No new threat surface introduced (compat tests exercise the existing `SimulationRunner` surface only; no new endpoints, auth paths, file-access patterns, or schema changes beyond the plan's declared trace/manifest checks).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 9 Simulation Workflow is complete (3/3 plans: 09-01 adapters, 09-02 wizard, 09-03 wiring + compatibility proof); REQUIREMENTS.md now marks TUI-09..TUI-14 satisfied.
- The wizard handoff surface is proven compatible with `SimulationRunner` — Phase 10 (background execution & live feedback, TUI-15..18) can implement its worker directly on `SimulationLaunchRequest` + `SimulationRunner` with the dashed-in trace/manifest contract already regression-tested.
- No blockers. Suggested next: `/gsd-verify-work 09`, then `/gsd-plan-phase 10`.

---
## Self-Check: PASSED
- FOUND: tests/test_manet_simulation_runner_compat.py
- FOUND: tests/test_manet_command_palette.py
- FOUND: manet/app.py
- FOUND: manet/commands/registry.py
- FOUND: manet/screens/main_workspace.py
- FOUND: manet/screens/simulation_workflow.py
- FOUND: tests/test_manet_navigation.py
- FOUND: .planning/phases/09-simulation-workflow/09-03-SUMMARY.md
- FOUND commit: d990673
- FOUND commit: ec6f74f
- FOUND: verification `python -m pytest tests -q` -> 176 passed (79 baseline + 97 manet)
