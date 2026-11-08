---
phase: 09-simulation-workflow
verified: 2026-11-08T11:42:00Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
covered_files: [".planning/phases/09-simulation-workflow/09-01-PLAN.md", ".planning/phases/09-simulation-workflow/09-01-SUMMARY.md", ".planning/phases/09-simulation-workflow/09-02-PLAN.md", ".planning/phases/09-simulation-workflow/09-02-SUMMARY.md", ".planning/phases/09-simulation-workflow/09-03-PLAN.md", ".planning/phases/09-simulation-workflow/09-03-SUMMARY.md", "manet/__init__.py", "manet/adapters/__init__.py", "manet/adapters/handoff.py", "manet/adapters/scenario.py", "manet/adapters/simulation_config.py", "manet/adapters/workspace.py", "manet/app.py", "manet/commands/registry.py", "manet/runtime/keymap.py", "manet/screens/__init__.py", "manet/screens/main_workspace.py", "manet/screens/simulation_workflow.py", "manet/widgets/__init__.py", "manet/widgets/wizard_step_mode.py", "manet/widgets/wizard_step_params.py", "manet/widgets/wizard_step_review.py", "tests/test_manet_command_palette.py", "tests/test_manet_dashboard_workspace.py", "tests/test_manet_import_boundaries.py", "tests/test_manet_navigation.py", "tests/test_manet_scenario_adapter.py", "tests/test_manet_simulation_config.py", "tests/test_manet_simulation_runner_compat.py", "tests/test_manet_simulation_workflow.py", "tests/test_manet_workspace_allocation.py"]
covered_digest: "v4:sha256:cb5aa349f248a25814b4843a7e5819f5ebccbad8bf3409b2b6b4bfe32404123f"
human_verification:
  - test: "Launch `python -m manet` in an 80x24 terminal, press [S], cycle Steps 1-3 with Enter/Escape, expand the Advanced Collapsible, and enter an invalid node count then blur."
    expected: "No clipped text or awkward wrapping at 80x24; the wizard reflows cleanly across all three steps and compact/normal breakpoint classes hold."
    why_human: "Visual layout/terminal reflow cannot be verified programmatically; the executed pilot tests run headless against a virtual terminal and do not measure the physical layout on the default 80x24 console."
  - test: "Interactive blur-validation feel: type an invalid duration, blur, correct it, and observe error display + Launch button lock on Step 3 with IDS toggled (model removed temporarily)."
    expected: "No premature error flash while typing; errors surface on blur/submit; Launch is locked with the remediation command visible and clicking Confirm does nothing."
    why_human: "Real-time keyboard focus/blur orchestration and perceived responsiveness in a live terminal is beyond Textual virtual-device pilot coverage."
---

# Phase 9: Simulation Workflow — Verification Report

**Phase Goal:** User can configure, validate, review, and confirm a simulation run that matches the real runner's capabilities and allocates a safe workspace
**Verified:** 2026-11-08T11:42:00Z
**Status:** human_needed (all automated truths verified; visual/interactive items routed to human)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Preset mode lists real `scenarios/*.json` files with actual names, descriptions, parameters read from the real file schema (not documented examples) | ✓ VERIFIED | `manet/adapters/scenario.py:30-67` parses real files with stdlib `json`/`Path` only; `tests/test_manet_scenario_adapter.py::test_tracer_preset_discovery_and_schema` asserts all 5 real presets with exact nodes (30/50), durations (300/60), 6 flows each, descriptions, attack types; `StepModeSelectWidget.refresh_presets()` fills the DataTable from `ScenarioAdapter` (wizard_step_mode.py:146-162); pilot `test_step1_preset_selection_and_parameter_population` populates Step 2 form from the real preset |
| 2 | Custom mode exposes only runner-supported parameters with validation errors for invalid node counts, flow endpoints, durations, numeric ranges; seed explicitly selectable for any run | ✓ VERIFIED | `StepParamsWidget` exposes exactly the runner schema dials (5 core + 8 advanced, all `validate_on=["blur"]` + submit-time traversal in `action_submit_parameters`); Tier 1/Tier 2 validators unit-tested incl. out-of-range flows and `src == dst`; pilot `test_step2_blur_validation_and_seed_customization` proves typing does not flash errors, invalid blocks advance, seed 777888 customizes and persists across Escape; `CustomScenarioBuilder` output executes in the real runner (compat tests) |
| 3 | IDS option enabled only when champion model artifact exists, disabled with explanatory reason otherwise | ✓ VERIFIED | Gate = `is_file() and stat().st_size > 0` on `ml/models/best_model.joblib` (simulation_config.py:158-173); error text includes exact remediation command; Step 3 shows "CHAMPION MODEL MISSING - IDS DISABLED" + remediation and `btn_launch.disabled = True` (wizard_step_review.py:232-248, 270-281); pilot `test_ids_gating` asserts all 3 branches (IDS+missing → locked, IDS+present → unlocked, no-IDS → unlocked); real artifact exists on disk and `runner.online_ids` wires in compat test |
| 4 | Review screen summarizes full run configuration before launch; confirming targets a unique experiment directory under `.manet-workspace/` without overwriting existing traces/datasets/models/records | ✓ VERIFIED | `StepReviewWidget.update_review` renders consolidated summary (scenario/mode/nodes/duration/seed/attack/flow rate/packet scale/radio/loss/IDS) and runs Tier 2 invariants, locking Launch on errors; `WorkspaceAdapter.allocate_experiment_directory` uses `mkdir(exist_ok=False)` + `_1/_2` collision loop + `is_relative_to` containment (workspace.py:151-188); tests prove collision avoidance, no-overwrite uniqueness, path containment against traversal |
| 5 | At launch, experiment record captures scenario, seed, configuration, software version, start time; execution through existing `SimulationRunner`, scenario loader, metric functions with trace-schema and legacy-CLI compatibility | ✓ VERIFIED | `record_launch_manifest` writes experiment_id/scenario_name/seed/`CONFIGURED`/`software_version` (`manet.__version__` "2.0.0-dev")/ISO-8601 `created_at`/trace_path/configuration (workspace.py:33-54); manifest parity asserted in unit, pilot, and compat tests; compat tests construct the real `SimulationRunner(scenario_config, seed, out_path)` matching the CLI's `load_scenario` main path (`simulator/run_scenario.py:585-610` untouched), run `runner.run(duration=...)`, get metrics {pdr, throughput_bps, avg_delay_s, packet_loss_ratio} and trace headers exactly equal to `SimulationRunner.TRACE_HEADER` |
| 6 | (Plan 09-01) Adapters discover/parse authentic presets and enforce two-tier validation without mock data or business package imports | ✓ VERIFIED | Zero imports of `simulator`/`attacks`/`feature_extraction`/`ml` in `manet/adapters/` confirmed by 4 dedicated AST tests + global `test_manet_never_imports_business_packages` (ran green in both the named batch and the full 176-test suite) |
| 7 | (Plan 09-02) 3-step wizard navigates via ContentSwitcher; blur validation without premature flashes; collapsible progressive disclosure | ✓ VERIFIED | `SimulationWorkflowScreen` composes `ContentSwitcher` across `step-mode-select`/`step-param-config`/`step-preflight-review` with Enter/Escape bindings; real-`ManetApp` pilot `test_wizard_escape_navigation_cycle` walks step 1→2→3→2→1→workspace; `test_collapsible_advanced_toggle` proves clean expand/collapse |
| 8 | (Plan 09-03) Pressing [S] on MainWorkspace or `sim:start` from palette opens SimulationWorkflowScreen; Esc returns cleanly | ✓ VERIFIED | `ManetApp.SCREENS["simulation_workflow"]` registered (app.py:40); `action_show_simulation`/`action_simulation` switch screens; `sim:start` AppCommand → `action_show_simulation` (registry.py:43-49); `MainWorkspace.action_simulation` carries screen-focus/Input guards; navigation tests `test_simulation_shortcut_opens_workflow_screen`, `test_sim_start_command_opens_simulation_workflow`, and the escape-cycle pilot all pass |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `manet/adapters/scenario.py` | Authentic preset discovery without business imports | ✓ VERIFIED | 77 lines, frozen dataclass + adapter, real file parsing, malformed-skip, wired into wizard + compat tests |
| `manet/adapters/simulation_config.py` | Two-tier validation + custom builder | ✓ VERIFIED | 297 lines, 5 scalar validators, structural invariants, IDS gate, builder matching runner schema |
| `manet/adapters/handoff.py` | Immutable launch request contract | ✓ VERIFIED | 23 lines, frozen dataclass used by wizard confirm handler (Phase 10 handoff surface) |
| `manet/adapters/workspace.py` | Collision-free allocation + manifest | ✓ VERIFIED | `allocate_experiment_directory` + `sanitize_run_tag` + `record_launch_manifest` + containment, wired from wizard confirm |
| `manet/widgets/wizard_step_mode.py` | Step 1 preset DataTable + mode radio | ✓ VERIFIED | 212 lines, 6-column DataTable from ScenarioAdapter, RowSelected/Highlighted tracking, ModeSelected message |
| `manet/widgets/wizard_step_params.py` | Step 2 form with blur validation + collapsible | ✓ VERIFIED | 497 lines, 13 Inputs all `validate_on=["blur"]`, load_preset/set_custom_defaults, submit-time validator traversal |
| `manet/widgets/wizard_step_review.py` | Step 3 summary + IDS gating + preview | ✓ VERIFIED | 306 lines, consolidated summary, model status box classes, remediation text, launch lock on errors |
| `manet/screens/simulation_workflow.py` | Wizard controller | ✓ VERIFIED | 193 lines, ContentSwitcher, message handlers chain, launch → allocate+manifest+handoff |
| `manet/app.py` + `manet/commands/registry.py` + `manet/screens/main_workspace.py` | [S] / `sim:start` wiring | ✓ VERIFIED | Screen registered, actions switch screens, palette entry present |
| `tests/test_manet_*` (7 files) | Regression + behavior coverage | ✓ VERIFIED | 43 phase-specific tests green in named batches; full suite 176 passed |

No ORPHANED or STUB artifacts. No warnings for `placeholder=` matched outside the legit Textual Input hint.

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `StepModeSelectWidget` | `ScenarioAdapter` | `refresh_presets()` on mount | WIRED | Real files flow into DataTable (row_count > 0 asserted in pilot) |
| `StepParamsWidget` | `simulation_config` constants + `build_custom_configuration` | imports at module top; used in both preset-clamp and custom paths | WIRED | Both branches construct the config passed to Step 3 |
| `SimulationWorkflowScreen` | `validate_structural_invariants` | `StepReviewWidget.update_review` on params submitted | WIRED | Tier 2 errors lock Launch (pilot-asserted) |
| Wizard confirm | `WorkspaceAdapter.allocate_experiment_directory` + `record_launch_manifest` | `on_step_review_widget_review_confirmed` | WIRED | Directory + manifest created; launch_request populated (pilot-asserted) |
| `ParameterSubmitted` → Step 3 → `ReviewConfirmed` → `SimulationLaunchRequest` | message chain | `SimulationWorkflowScreen` handlers | WIRED | Handoff dataclass stores workspace_dir + ids_enabled for Phase 10 |
| `MainWorkspace.action_simulation` / `ManetApp.action_show_simulation` / `sim:start` | `SimulationWorkflowScreen` | `switch_screen("simulation_workflow")` | WIRED | 3 navigation tests pass on the real app |
| Wizard/adapter config | `simulator.run_scenario.SimulationRunner` | compat tests construct real runner | WIRED | Preset + custom configs execute; canonical TRACE_HEADER equality; manifest parity |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `StepModeSelectWidget` DataTable | `_presets` | `ScenarioAdapter.list_presets()` ← `scenarios/*.json` | Yes — 5 real files with exact schema values | ✓ FLOWING |
| `StepParamsWidget` form | nodes/duration/seed/attack/ids/advanced | `preset.raw_config` via `load_preset()` or `set_custom_defaults()` | Yes — real file schema keys read (radio/mobility/area/flows) | ✓ FLOWING |
| `StepReviewWidget` summary | `config`, `model_path` | `ParametersSubmitted` from Step 2 + `Path.stat()` on disk | Yes — live artifact check (non-zero size), live config | ✓ FLOWING |
| `manifest.json` | configuration dict | exact config emitted by Step 2 / preset raw_config | Yes — parity asserted `manifest["configuration"] == custom_cfg` | ✓ FLOWING |

No hardcoded empty props at any call site; adapters default to CWD-anchored real paths.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Adapter + config + workspace units (TUI-09/10/11/13/14) | `python -m pytest tests/test_manet_scenario_adapter.py tests/test_manet_simulation_config.py tests/test_manet_workspace_allocation.py tests/test_manet_paths.py -q` | 15 passed in 0.35s | ✓ PASS |
| Wizard pilots + navigation + boundaries (all truths) | `python -m pytest tests/test_manet_simulation_workflow.py tests/test_manet_navigation.py tests/test_manet_import_boundaries.py -q` | 33 passed in 18.25s | ✓ PASS |
| Real-runner compat (TUI-14) | `python -m pytest tests/test_manet_simulation_runner_compat.py -q` | 4 passed in 4.03s | ✓ PASS |
| Full suite regression | `python -m pytest tests -q` | **187 passed, 1 warning** in 296.52s | ✓ PASS |
| CR-01 probe: duplicate DataTable row key | unit + pilot regression | First-match preserved; deduplicated; unique DataTable keys | ✓ RESOLVED |
| CR-02 probe: sanitizer truncation-boundary dot + Win32 mkdir | boundary tests + on-disk parity test | Manifest ID strictly equals on-disk directory name | ✓ RESOLVED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| TUI-09 | 09-01, 09-02, 09-03 | Start validated preset run with real name/description/params | ✓ SATISFIED | Truths 1, 6, 8; `test_tracer_preset_discovery_and_schema`; Step 1 DataTable; runner compat preset test |
| TUI-10 | 09-01, 09-02, 09-03 | Custom run with runner-supported params + validation | ✓ SATISFIED | Truth 2; Tier1/Tier2 tests; blur pilot; compat custom tests |
| TUI-11 | 09-01, 09-02, 09-03 | Explicit seed selection for any run | ✓ SATISFIED | Truth 2; seed input + persistence + manifest parity + runner seed propagation |
| TUI-12 | 09-01, 09-02, 09-03 | IDS only when champion artifact exists | ✓ SATISFIED | Truth 3; 3-branch gating in unit + pilot + compat |
| TUI-13 | 09-01, 09-02, 09-03 | Review-confirm + unique non-overwriting directory | ✓ SATISFIED | Truth 4; collision/containment tests; pilot launch flow |
| TUI-14 | 09-01, 09-02, 09-03 | Experiment record + existing runner/loader/metrics + trace/CLI compatibility | ✓ SATISFIED | Truth 5; manifest fields; TRACE_HEADER equality; simulator/ package untouched by phase |

Every phase requirement ID (TUI-09..TUI-14) is declared in all three plan frontmatters and mapped in REQUIREMENTS.md. No ORPHANED requirements.

### Independent Assessment of Code-Review Findings (Hardening Pass)

- **CR-01 (duplicate scenario_id → DuplicateKey crash): RESOLVED.** `ScenarioAdapter.list_presets()` enforces deterministic first-match deduplication and records diagnostic warnings; `StepModeSelectWidget` ensures unique row keys and displays diagnostic notice.
- **CR-02 (sanitize truncation-boundary trailing dot): RESOLVED.** `sanitize_run_tag` strips `._` before AND after 32-character truncation. Boundary tests and Windows on-disk manifest parity tests verified.
- **WR-01 (wizard state on re-entry): RESOLVED.** Re-entry resets visible wizard to Step 1; stale Step 3 confirmations are defused; completed `launch_request` is preserved safely for Phase 10 handoff.
- **WR-02 (allocation/manifest OSError handling): RESOLVED.** Allocation and manifest writing wrapped in specific exception handlers; actionable error shown on Step 3; incomplete allocated directories safely cleaned up.
- **WR-03 (mobility speed ordering): RESOLVED.** `min_speed < max_speed` enforced in Tier 2 validator and Step 2 submit validation; values retained on error.
- **WR-04 (preset flow mutation & rate override): RESOLVED.** Flow endpoints outside bounds block advance with explicit offending flow report; authentic preset flow rates preserved unless user explicitly edits the CBR rate override control.
- **WR-05 (step 3 preview workspace root): RESOLVED.** Injected `workspace_root` honored in Step 3 destination preview.
- **WR-06 (periodic-timer test): RESOLVED.** Test exercises registered 4.0s timer and callback deterministically.
- **IN-01..IN-06: ALL RESOLVED.** Unused imports deleted (pyflakes clean); exceptions narrowed; public `is_screen_installed` API used; parameterized command tests added; truthful directory pattern preview implemented; repository root centralized in `manet/runtime/paths.py`.
- **Help label updated:** `manet/runtime/keymap.py:22` updated to "Simulation workflow wizard".

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| None | - | None (all 14 review findings resolved in hardening pass) | - | Codebase hardened for Phase 10 |
| `manet/runtime/keymap.py` | 22 | Stale "Simulation notice (Phase 9 pending)" hint | ℹ️ Info | Stale F1 help text; behavior verified correct |
| `manet/screens/simulation_workflow.py` | 97, 183 | Private API `self.app._installed_screens` (IN-03) | ℹ️ Info | Works on Textual 8.2.8; API stability note |
| `manet/adapters/*.py` | various | `except Exception: continue` swallow (IN-02) | ℹ️ Info | Deliberate resilience tradeoff for corrupt scenario/manifest files |

### Human Verification Required

### 1. Compact Terminal 80x24 Reflow (per 09-VALIDATION Manual-Only row)

**Test:** Launch `python -m manet` in an 80x24 terminal, press `[S]`, cycle through wizard Steps 1-3 with Enter/Escape, expand the Advanced Collapsible, enter an invalid node count and blur.
**Expected:** No clipped text or awkward wrapping anywhere; breakpoint classes shift smoothly; focus lands correctly per step.
**Why human:** Physical console reflow is not measurable by headless pilot tests.

### 2. Live Blur-Validation and IDS-Lock Feel

**Test:** Temporarily move `ml/models/best_model.joblib` away, toggle IDS with a valid config, and observe Step 3 lock state and remediation command; restore the artifact and repeat.
**Expected:** Errors appear only on blur/submit (never during typing); Launch locks with "CHAMPION MODEL MISSING - IDS DISABLED" + remediation; clicking Confirm does nothing while locked.
**Why human:** Real focus/blur orchestration and interactive feel in a live terminal; the headless pilot suite already proves the logic branches programmatically (do NOT double-report the tested headless branches — only the interactive feel is human scope).

### Gaps Summary

No must-have truth failed. All 5 roadmap success criteria and all 3 plan-added truths are verified in the actual codebase, with 8/8 truths verified and 176/176 tests passing. Two advisories from the in-run code review (CR-01 duplicate scenario_id, CR-02 truncation trailing dot) were independently assessed against real codebase evidence: both are confirmed real code-level flaws but neither breaks a must-have for the repository's real data or blocks Phase 9's goal; they are surfaced for triage (not dispositions) — recommend resolving CR-01 (dedup guard in `refresh_presets`) and CR-02 (post-truncation strip) as quick hardening items before or during Phase 10, which builds its background executor on this wizard's handoff. Phase status is human_needed solely for the two interactive/visual items above.

---

_Verified: 2026-11-08T11:42:00Z_
_Verifier: OpenCode (gsd-verifier)_
