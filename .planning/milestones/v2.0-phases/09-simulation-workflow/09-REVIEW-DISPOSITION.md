---
phase: 09
review: 09-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "Duplicate `scenario_id` across scenario JSON files crashes wizard with `DuplicateKey`"
  - id: CR-02
    severity: critical
    disposition: fixed
    title: "`sanitize_run_tag` truncation re-introduces a Windows-illegal trailing dot"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "Wizard never resets state on re-entry - stale Step 3 config is re-confirmable"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "Unhandled `OSError`s during allocation/manifest write crash the whole TUI after confirm"
  - id: WR-03
    severity: warning
    disposition: fixed
    title: "No cross-field invariant for mobility speed ordering (min speed > max speed is accepted)"
  - id: WR-04
    severity: warning
    disposition: fixed
    title: "Preset mode silently mutates flows (endpoint rewrite + single-rate overwrite) without surfacing the change"
  - id: WR-05
    severity: warning
    disposition: fixed
    title: "Step 3 workspace preview ignores the injected `workspace_root` (hardcoded `.manet-workspace/`)"
  - id: WR-06
    severity: warning
    disposition: fixed
    title: "periodic-timer test cannot exercise the 4s interval it claims to verify"
  - id: IN-01
    severity: info
    disposition: fixed
    title: "Unused imports verified by pyflakes (dead code)"
  - id: IN-02
    severity: info
    disposition: fixed
    title: "Corrupt artifacts silently vanish with no signal (`except Exception: continue/pass`)"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "Private API access `self.app._installed_screens`"
  - id: IN-04
    severity: info
    disposition: fixed
    title: "Command parameter machinery is untestable dead weight today"
  - id: IN-05
    severity: info
    disposition: fixed
    title: "Previewed directory name almost never matches the actual allocated name (timestamp churn)"
  - id: IN-06
    severity: info
    disposition: fixed
    title: "CWD-anchored defaults silently degrade when the TUI is not launched from repo root"
open: 0
total: 14
unparsed: 0
recorded: 2026-11-08T06:05:00Z
---

# Phase 09: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | `manet/adapters/scenario.py`, `manet/widgets/wizard_step_mode.py`; unit `test_duplicate_scenario_id_deduplication` & pilot `test_duplicate_scenario_id_mounts_cleanly_in_wizard` |
| CR-02 | critical | fixed | `manet/adapters/workspace.py`; boundary and Windows parity tests `test_manifest_experiment_id_matches_directory_name_on_windows` |
| WR-01 | warning | fixed | `manet/screens/simulation_workflow.py`, `manet/widgets/wizard_step_review.py`; pilot `test_wizard_resets_on_reentry_preventing_stale_reconfirmation` |
| WR-02 | warning | fixed | `manet/screens/simulation_workflow.py`, `manet/widgets/wizard_step_review.py`; pilot `test_allocation_and_manifest_failure_handling` |
| WR-03 | warning | fixed | `manet/adapters/simulation_config.py`, `manet/widgets/wizard_step_params.py`; unit `test_two_tier_validation_and_model_gate` & pilot `test_mobility_speed_ordering_validation_in_wizard` |
| WR-04 | warning | fixed | `manet/widgets/wizard_step_params.py`; pilot `test_preset_flow_validation_and_rate_override` |
| WR-05 | warning | fixed | `manet/widgets/wizard_step_review.py`; pilot `test_step3_preview_respects_custom_workspace_root` |
| WR-06 | warning | fixed | `manet/screens/main_workspace.py`, `tests/test_manet_dashboard_workspace.py`; verified timer interval & callback in `test_periodic_diagnostics_refresh_timer` |
| IN-01 | info | fixed | Removed unused imports from all Phase 9 files; `python -m pyflakes manet` reports 0 issues |
| IN-02 | info | fixed | Narrowed exception handlers to `(json.JSONDecodeError, OSError, ValueError, KeyError, NoMatches)` and added diagnostic tracking |
| IN-03 | info | fixed | `manet/screens/simulation_workflow.py`; migrated to public Textual 8.2.8 API `self.app.is_screen_installed("workspace")` |
| IN-04 | info | fixed | `tests/test_manet_command_registry.py`, `tests/test_manet_console.py`; added unit tests for parameterized command resolution and dispatch |
| IN-05 | info | fixed | `manet/widgets/wizard_step_review.py`; rendered truthful directory pattern indicating timestamp and suffix are finalized at confirm |
| IN-06 | info | fixed | `manet/runtime/paths.py`, adapters/screens/widgets; centralized `get_project_root()` and added cwd-independence test `tests/test_manet_paths.py` |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
