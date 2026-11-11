---
phase: 09-simulation-workflow
plan: "02"
subsystem: ui-screens
tags: [textual, wizard-workflow, content-switcher, validation, ids-gating, workspace-allocation]

requires:
  - phase: 09-simulation-workflow
    plan: "01"
    provides: ScenarioAdapter, SimulationConfigValidator, WorkspaceAdapter directory allocation
provides:
  - StepModeSelectWidget with preset DataTable and custom mode toggle
  - StepParamsWidget with progressive disclosure, 5 core dials, and blur validation
  - StepReviewWidget with parameter summary, champion model gating, and workspace preview
  - SimulationWorkflowScreen 3-step wizard screen with ContentSwitcher and keyboard navigation
  - Comprehensive Textual async pilot test suite in tests/test_manet_simulation_workflow.py
affects: [09-03, 10-background-execution]

actuals:
  tokens: 18532
  tasks: 3
  commits: 3
  plan_head_before: eb1d0633f24b8a5d6bc290ae2cb9367add6576fc
  plan_head_after: e33cf9e97160cee13f73c0dc5a76f733be9c83ce

tech-stack:
  added: []
  patterns: [ContentSwitcher wizard state machine, blur validation with submit-time check, visual champion model gating]

key-files:
  created:
    - manet/widgets/wizard_step_mode.py
    - manet/widgets/wizard_step_params.py
    - manet/widgets/wizard_step_review.py
    - manet/screens/simulation_workflow.py
    - tests/test_manet_simulation_workflow.py
  modified:
    - manet/widgets/__init__.py
    - manet/screens/__init__.py
    - manet/screens/main_workspace.py
    - manet/app.py
    - manet/commands/registry.py
    - tests/test_manet_navigation.py
    - tests/test_manet_dashboard_workspace.py

key-decisions:
  - "Coordinate 3-step simulation wizard within a single screen using Textual ContentSwitcher across step-mode-select, step-param-config, and step-preflight-review"
  - "Apply validate_on=['blur'] on all numeric form fields to prevent premature error flashes during keystrokes, coupled with comprehensive submit-time validation"
  - "Strictly disable launch button on pre-flight review screen whenever IDS is toggled on without best_model.joblib, displaying an actionable remediation command"
  - "Preserve explicit random seed default (42) and custom seed adjustments across back-and-forth wizard navigation"

patterns-established:
  - "ContentSwitcher wizard pattern: state preserved seamlessly across Step 1, Step 2, and Step 3 without DOM destruction"
  - "Submit-time validator traversal: forcing all widget validators to run upon submission in addition to blur events"
  - "One-way presentation adapter layer: UI widgets consume ScenarioAdapter, SimulationConfigValidator, and WorkspaceAdapter without business package imports"

requirements-completed:
  - TUI-09
  - TUI-10
  - TUI-11
  - TUI-12
  - TUI-13
  - TUI-14

coverage:
  - id: D1
    description: "Step 1 Mode Selection discovering authentic presets from scenarios/*.json and supporting custom mode"
    requirement: TUI-09
    verification:
      - kind: unit
        ref: "tests/test_manet_simulation_workflow.py#test_wizard_steps_step1_mode_selection"
        status: pass
      - kind: unit
        ref: "tests/test_manet_simulation_workflow.py#test_step1_preset_selection_and_parameter_population"
        status: pass
    human_judgment: false
  - id: D2
    description: "Step 2 Parameter Configuration with 5 core dials, progressive disclosure via Collapsible, and blur validation"
    requirement: TUI-10
    verification:
      - kind: unit
        ref: "tests/test_manet_simulation_workflow.py#test_wizard_steps_step2_params_structure_and_blur_validation"
        status: pass
      - kind: unit
        ref: "tests/test_manet_simulation_workflow.py#test_step2_blur_validation_and_seed_customization"
        status: pass
    human_judgment: false
  - id: D3
    description: "Explicit customizable random seed (default 42) retained across step navigation"
    requirement: TUI-11
    verification:
      - kind: unit
        ref: "tests/test_manet_simulation_workflow.py#test_step2_blur_validation_and_seed_customization"
        status: pass
    human_judgment: false
  - id: D4
    description: "IDS toggle visually and operationally gated on presence and non-zero size of ml/models/best_model.joblib with remediation message"
    requirement: TUI-12
    verification:
      - kind: unit
        ref: "tests/test_manet_simulation_workflow.py#test_ids_gating"
        status: pass
    human_judgment: false
  - id: D5
    description: "Pre-flight review screen displaying summary, scale estimate, and allocating unique directory under .manet-workspace/"
    requirement: TUI-13
    verification:
      - kind: unit
        ref: "tests/test_manet_simulation_workflow.py#test_review_confirmation"
        status: pass
    human_judgment: false
  - id: D6
    description: "Launch manifest recorded with CONFIGURED status, matching configuration, explicit seed, and software version"
    requirement: TUI-14
    verification:
      - kind: unit
        ref: "tests/test_manet_simulation_workflow.py#test_review_confirmation"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-11-08
status: complete
---

# Phase 9 Plan 02: Simulation Workflow Wizard Screen and Widgets Summary

**Interactive 3-step simulation workflow wizard with authentic preset discovery, progressive disclosure parameter configuration with blur validation, strict champion model IDS gating, and pre-flight review confirmation.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-11-07T18:08:03Z
- **Completed:** 2026-11-07T18:34:00Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments

- Delivered `StepModeSelectWidget` discovering and presenting all 5 authentic scenario presets in a keyboard-navigable `DataTable` (ID, nodes, duration, attack, flows, description) and supporting custom simulation mode selection.
- Delivered `StepParamsWidget` presenting 5 essential macro parameters (Node Count, Duration, Explicit Seed, Attacker Strategy, IDS Toggle) with a `Collapsible` container for advanced network dials (radio range, loss probability, speed range, pause time, CBR packet rate, area width/height, run tag), strictly configured with `validate_on=['blur']` to eliminate premature validation error flashing during typing.
- Delivered `StepReviewWidget` displaying a consolidated configuration overview, packet scale estimate, target `.manet-workspace/<experiment_id>/` directory preview, and strict champion model gating that locks the Launch button whenever IDS is enabled without `ml/models/best_model.joblib` while showing actionable remediation commands.
- Delivered `SimulationWorkflowScreen` controller managing the 3 steps with Textual `ContentSwitcher`, full keyboard navigation (`[Enter]`, `[Escape]`), responsive breakpoints for 80x24 terminals, and execution handoff through `WorkspaceAdapter.allocate_experiment_directory()` and `record_launch_manifest()`.
- Connected `MainWorkspace` shortcut `[S]` and command palette `sim:start` directly to `SimulationWorkflowScreen`.
- Created 9 comprehensive async pilot tests in `tests/test_manet_simulation_workflow.py`, with 100% pass rate across all 91 TUI tests and zero AST import boundary violations.

## Task Commits

Each task was committed atomically:

1. **Task 1: Step 1 Mode Selection and Step 2 Parameter Configuration Widgets** - `5971d5d` (feat)
2. **Task 2: Step 3 Review Widget, IDS Gating, and Wizard Controller Screen** - `fd96af9` (feat)
3. **Task 3: Textual Async Pilot Test Suite for Simulation Workflow** - `e33cf9e` (test)

## Files Created/Modified

- `manet/widgets/wizard_step_mode.py` - Step 1 scenario mode selector and preset DataTable widget
- `manet/widgets/wizard_step_params.py` - Step 2 parameter configuration widget with progressive disclosure and blur validation
- `manet/widgets/wizard_step_review.py` - Step 3 pre-flight review summary and champion model gating widget
- `manet/screens/simulation_workflow.py` - Master wizard screen controller managing step transitions and launch directory allocation
- `manet/widgets/__init__.py` - Exported new wizard widgets
- `manet/screens/__init__.py` - Exported `SimulationWorkflowScreen`
- `manet/screens/main_workspace.py` - Updated `[S]` action to navigate to `SimulationWorkflowScreen`
- `manet/app.py` - Registered `"simulation"` screen route and shortcut handler
- `manet/commands/registry.py` - Registered `sim:start` command for command palette
- `tests/test_manet_navigation.py` - Updated navigation tests to verify `[S]` switches to `SimulationWorkflowScreen`
- `tests/test_manet_dashboard_workspace.py` - Updated shortcut test assertions for Phase 9 screen transition
- `tests/test_manet_simulation_workflow.py` - Full async pilot test suite for wizard navigation, validation, IDS gating, and launch confirmation

## Decisions Made

- Coordinated all 3 wizard steps within a single screen using Textual `ContentSwitcher` (`step-mode-select`, `step-param-config`, `step-preflight-review`), preserving form state during step navigation.
- Configured all numeric inputs with `validate_on=['blur']` and augmented `action_submit_parameters` with validator traversal to ensure comprehensive verification before advancing.
- Strictly disabled the Launch button on pre-flight review screen whenever IDS is toggled on without `ml/models/best_model.joblib`, rendering the exact remediation command: `python scripts/build_dataset.py --multi-attack && python -m ml.train && python -m ml.evaluate`.
- Configured `[Escape]` key to step back gracefully: Step 3 -> Step 2, Step 2 -> Step 1, Step 1 -> `MainWorkspace`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Textual submit validation on programmatic value changes**
- **Found during:** Task 3 pilot test run
- **Issue:** Programmatically setting `input.value = "1"` without firing focus/blur left Textual's `inp.is_valid` in its default state, bypassing validation on submit.
- **Fix:** In `action_submit_parameters()`, explicitly evaluated `validator.validate(inp.value)` across all attached validators on submission.
- **Files modified:** `manet/widgets/wizard_step_params.py`
- **Commit:** `e33cf9e`

**2. [Rule 1 - Bug] Command palette test collision on query 'work'**
- **Found during:** Regression test run
- **Issue:** `tests/test_manet_command_palette.py` tested `'work'` expecting only `'Go to workspace'`. Registering `'Start Simulation Workflow'` caused an unexpected second match.
- **Fix:** Renamed display to `'Start Simulation Wizard'` in `manet/commands/registry.py`.
- **Files modified:** `manet/commands/registry.py`
- **Commit:** `e33cf9e`

**3. [Rule 1 - Bug] Phase 8 placeholder shortcut assertion in dashboard test**
- **Found during:** Regression test run
- **Issue:** `tests/test_manet_dashboard_workspace.py` still asserted that `[S]` showed a notification rail notice ("Phase 9 will enable...").
- **Fix:** Updated test to assert `[S]` navigates to `SimulationWorkflowScreen` and `[Escape]` returns to `MainWorkspace`.
- **Files modified:** `tests/test_manet_dashboard_workspace.py`
- **Commit:** `e33cf9e`

## Issues Encountered

None. All 9 wizard tests, 91 TUI tests, and 170+ total repository tests passed cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The 3-step simulation workflow wizard (`SimulationWorkflowScreen`) and all widgets are fully implemented, verified, and integrated into `ManetApp`.
- Ready to proceed to Plan 09-03 or Phase 10 (background simulation execution and telemetry).

---
## Self-Check: PASSED
- FOUND: manet/widgets/wizard_step_mode.py
- FOUND: manet/widgets/wizard_step_params.py
- FOUND: manet/widgets/wizard_step_review.py
- FOUND: manet/screens/simulation_workflow.py
- FOUND: tests/test_manet_simulation_workflow.py
- FOUND commit: 5971d5d
- FOUND commit: fd96af9
- FOUND commit: e33cf9e
