---
phase: 09-simulation-workflow
plan: "01"
subsystem: ui-adapters
tags: [textual, manet-adapters, scenario-discovery, validation, workspace-allocation]

requires:
  - phase: 08-operational-dashboard
    provides: Diagnostics probes and operational dashboard foundations
provides:
  - ScenarioAdapter discovering authentic presets from scenarios/*.json without business package imports
  - SimulationConfigValidator enforcing two-tier parameter checks and champion model gating
  - CustomScenarioBuilder generating valid simulation schemas for custom runs
  - WorkspaceAdapter.allocate_experiment_directory allocating collision-free experiment directories with sanitized tags
  - record_launch_manifest generating initial manifest.json
affects: [09-02, 09-03, 10-background-execution]

actuals:
  tokens: 10936
  tasks: 3
  commits: 3
  plan_head_before: b0aa3c3a2c38f9ac7a4cf07230ab606aab9e2281
  plan_head_after: fbf74f6405b3524a3af46a3939b45b719296437f

tech-stack:
  added: []
  patterns: [two-tier parameter validation, collision-free directory allocation, AST boundary enforcement]

key-files:
  created:
    - manet/adapters/scenario.py
    - manet/adapters/simulation_config.py
    - manet/adapters/handoff.py
    - tests/test_manet_scenario_adapter.py
    - tests/test_manet_simulation_config.py
    - tests/test_manet_workspace_allocation.py
  modified:
    - manet/adapters/workspace.py
    - manet/adapters/__init__.py

key-decisions:
  - "Discover authentic scenarios directly from scenarios/*.json with stdlib json without importing simulator/attacks/ml packages"
  - "Enforce two-tier parameter validation: scalar bounds check on blur, structural invariant check before review"
  - "Strictly gate IDS enablement on physical presence and non-zero size of ml/models/best_model.joblib"
  - "Sanitize custom run tags with regex stripping path traversal dots and Windows-illegal characters while enforcing workspace root containment"

patterns-established:
  - "Two-tier validation: field blur validation for scalar ranges coupled with whole-form structural invariant checking"
  - "Atomic collision-avoidance loop for experiment directory allocation under .manet-workspace/"
  - "One-way presentation adapter layer strictly isolated from simulator and ML business packages"

requirements-completed:
  - TUI-09
  - TUI-10
  - TUI-11
  - TUI-12
  - TUI-13
  - TUI-14

coverage:
  - id: D1
    description: "ScenarioAdapter authentic preset discovery from scenarios/*.json without business imports"
    requirement: TUI-09
    verification:
      - kind: unit
        ref: "tests/test_manet_scenario_adapter.py#test_tracer_preset_discovery_and_schema"
        status: pass
    human_judgment: false
  - id: D2
    description: "Two-tier parameter validator checking scalar bounds and cross-field structural invariants"
    requirement: TUI-10
    verification:
      - kind: unit
        ref: "tests/test_manet_simulation_config.py#test_two_tier_validation_and_model_gate"
        status: pass
    human_judgment: false
  - id: D3
    description: "Explicit seed selection and configuration propagation in custom scenario builder"
    requirement: TUI-11
    verification:
      - kind: unit
        ref: "tests/test_manet_simulation_config.py#test_build_custom_configuration"
        status: pass
    human_judgment: false
  - id: D4
    description: "IDS enablement strictly gated on physical presence and non-zero size of ml/models/best_model.joblib"
    requirement: TUI-12
    verification:
      - kind: unit
        ref: "tests/test_manet_simulation_config.py#test_two_tier_validation_and_model_gate"
        status: pass
    human_judgment: false
  - id: D5
    description: "Collision-free experiment directory allocation under .manet-workspace/ with tag sanitization"
    requirement: TUI-13
    verification:
      - kind: unit
        ref: "tests/test_manet_workspace_allocation.py#test_workspace_allocation_and_manifest"
        status: pass
    human_judgment: false
  - id: D6
    description: "Initial launch manifest recording scenario, seed, software version, and start timestamp"
    requirement: TUI-14
    verification:
      - kind: unit
        ref: "tests/test_manet_workspace_allocation.py#test_workspace_allocation_and_manifest"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-11-07
status: complete
---

# Phase 9 Plan 01: Simulation Workflow Adapter Foundation Summary

**Decoupled scenario discovery adapter, two-tier parameter validator with champion model gating, and collision-free workspace directory allocator with launch manifest recording.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-11-07T15:48:04Z
- **Completed:** 2026-11-07T16:03:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Delivered `ScenarioAdapter` and `ScenarioPreset` discovering all 5 authentic in-repo scenarios (`e1_normal_30n`, `e2_blackhole_30n`, `e3_blackhole_onset_30n`, `e4_grayhole_50n`, `e4_grayhole_onset_30n`) using pure stdlib `json` and `pathlib` without importing any business logic packages.
- Implemented `SimulationConfigValidator` providing Tier 1 scalar validators (`validate_node_count`, `validate_duration`, `validate_seed`, `validate_radio_range`, `validate_loss_probability`) and Tier 2 structural invariant validation (`validate_structural_invariants`), enforcing valid flow endpoints and strictly gating IDS enablement on the physical presence of `ml/models/best_model.joblib` with actionable remediation guidance.
- Implemented `CustomScenarioBuilder` and `SimulationLaunchRequest` preparing complete simulation payloads compatible with `SimulationRunner`.
- Extended `WorkspaceAdapter` with `allocate_experiment_directory`, collision avoidance loop, tag sanitization via `sanitize_run_tag`, and initial launch manifest creation via `record_launch_manifest`.
- Created comprehensive test suites across `tests/test_manet_scenario_adapter.py`, `tests/test_manet_simulation_config.py`, and `tests/test_manet_workspace_allocation.py`, with 161 total tests passing project-wide and zero AST architectural import violations.

## Task Commits

Each task was committed atomically:

1. **Task 1: Foundational Scenario Adapter Tracer Slice** - `4ffe878` (feat)
2. **Task 2: Two-Tier Parameter Validator and Configuration Builder** - `a50cbb3` (feat)
3. **Task 3: Collision-Free Workspace Directory Allocation and Launch Manifest** - `fbf74f6` (feat)

## Files Created/Modified

- `manet/adapters/scenario.py` - Authentic preset scenario discovery and schema parsing into frozen `ScenarioPreset` records
- `manet/adapters/simulation_config.py` - Two-tier parameter validation and custom scenario dictionary builder
- `manet/adapters/handoff.py` - Immutable `SimulationLaunchRequest` dataclass for Phase 10 execution handoff
- `manet/adapters/workspace.py` - Extended with `allocate_experiment_directory`, `sanitize_run_tag`, and `record_launch_manifest`
- `manet/adapters/__init__.py` - Exported new adapters and validators
- `tests/test_manet_scenario_adapter.py` - Unit tests for scenario discovery, schema validation, malformed file handling, and boundary checks
- `tests/test_manet_simulation_config.py` - Unit tests for scalar bounds, cross-field flow invariants, and champion model gate
- `tests/test_manet_workspace_allocation.py` - Unit tests for collision avoidance, tag sanitization, directory containment, and manifest structure

## Decisions Made

- Discovered authentic scenarios directly from `scenarios/*.json` with stdlib `json` without importing `simulator`, `attacks`, `feature_extraction`, or `ml`.
- Implemented two-tier validation separating local field blur checks from whole-form structural cross-field invariants.
- Enforced strict gate on IDS activation requiring physical existence and non-zero size of `ml/models/best_model.joblib`.
- Built safe regex-based run tag sanitizer stripping traversal patterns (`..`), spaces, and Windows-illegal filename characters (`\ / : * ? " < > |`), while validating directory containment under `.manet-workspace/`.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. All 12 adapter tests and 161 total repository tests passed cleanly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The adapter foundation is fully tested and ready for Plan 09-02 (Textual 3-step wizard screen implementation: Mode Select, Param Config, Pre-Flight Review).
- Ready to proceed to 09-02.

---
## Self-Check: PASSED
- FOUND: manet/adapters/scenario.py
- FOUND: manet/adapters/simulation_config.py
- FOUND: manet/adapters/handoff.py
- FOUND: manet/adapters/workspace.py
- FOUND: tests/test_manet_scenario_adapter.py
- FOUND: tests/test_manet_simulation_config.py
- FOUND: tests/test_manet_workspace_allocation.py
- FOUND commit: 4ffe878
- FOUND commit: a50cbb3
- FOUND commit: fbf74f6
