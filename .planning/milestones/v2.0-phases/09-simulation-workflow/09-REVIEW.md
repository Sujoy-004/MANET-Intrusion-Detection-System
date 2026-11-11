---
phase: 09-simulation-workflow
reviewed: 2026-11-08T04:55:00Z
depth: standard
files_reviewed: 22
files_reviewed_list:
  - manet/adapters/__init__.py
  - manet/adapters/handoff.py
  - manet/adapters/scenario.py
  - manet/adapters/simulation_config.py
  - manet/adapters/workspace.py
  - manet/app.py
  - manet/commands/registry.py
  - manet/screens/__init__.py
  - manet/screens/main_workspace.py
  - manet/screens/simulation_workflow.py
  - manet/widgets/__init__.py
  - manet/widgets/wizard_step_mode.py
  - manet/widgets/wizard_step_params.py
  - manet/widgets/wizard_step_review.py
  - tests/test_manet_command_palette.py
  - tests/test_manet_dashboard_workspace.py
  - tests/test_manet_navigation.py
  - tests/test_manet_scenario_adapter.py
  - tests/test_manet_simulation_config.py
  - tests/test_manet_simulation_runner_compat.py
  - tests/test_manet_simulation_workflow.py
  - tests/test_manet_workspace_allocation.py
findings:
  critical: 2
  warning: 6
  info: 6
  total: 14
status: issues_found
---

# Phase 09: Code Review Report

**Reviewed:** 2026-11-08T04:55:00Z
**Depth:** standard
**Files Reviewed:** 22 (14 manet source, 8 test files)
**Status:** issues_found

## Summary

Reviewed the full presentation-adapter layer, wizard widgets/screen, app wiring, and test suites for Phase 09 at standard depth. All 55 tests in the 8 listed suites pass at review time. Cross-file verification (reading `manet/commands/palette_provider.py`, `manet/commands/console_driver.py`, `manet/notifications.py`, `manet/widgets/dashboard_cards.py`, `manet/runtime/keymap.py`, `simulator/run_scenario.py`) confirms the wiring between the registry/UI/runner is coherent.

**Project constraint verification:**

- **AST boundary (manet must not import `simulator`/`attacks`/`feature_extraction`/`ml`) — PASS.** Independent AST scan of all 14 in-scope `manet/` files found zero forbidden imports.
- **T-09-08 (command resolver string-actions only, no shell execution) — PASS.** `registry.resolve()` matches names and returns string-named actions; the only interpreters are `getattr(app, command.action)` in `palette_provider.py:41` and `console_driver.py:96`. `shlex` is used for tokenization only; no `os.system`/`subprocess`/`exec` primitives exist anywhere under `manet/`.
- **T-09-09 (compat test durations ≤ 10.0s) — PASS.** Compat tests use 2.0s, 5.0s, 4.0s and 3.0s.
- **Workspace root containment — PASS.** `allocate_experiment_directory` mkdirs, resolves, and re-checks `is_relative_to(root)` on every collision iteration, correctly following symlinks.
- **Custom run tag sanitization — FAIL (CR-02).** The sanitizer itself can emit a Windows-illegal trailing dot after 32-char truncation (empirically reproduced on this Windows host).

Two findings are backed by executed reproductions against the installed stack (Textual 8.2.8, Python 3.11, Windows): a `DuplicateKey` crash that bricks the whole simulation wizard, and a sanitize-then-truncate contract break in the run-tag sanitizer. One warning finding (wizard stale state on re-entry) is also empirically verified. The review did not modify any source files.

## Critical Issues

### CR-01: Duplicate `scenario_id` across scenario JSON files crashes wizard with `DuplicateKey`

**File:** `manet/widgets/wizard_step_mode.py:154-162` (crash site) / `manet/adapters/scenario.py:30-67` (root cause)
**Issue:** `refresh_presets()` builds DataTable rows keyed by `key=preset.scenario_id`. `ScenarioAdapter.list_presets()` scans every `scenarios/*.json` and trusts the file-declared `scenario_id`; two files declaring the same id produce two presets with an identical key. `table.add_row(..., key=...)` then raises `textual.widgets.DataTable.DuplicateKey` inside `on_mount()` — the exception kills the widget mount and takes down the entire app. Reproduced: two temp JSON files both with `"scenario_id": "dup_id"` → `DuplicateKey: The row key <RowKey(value='dup_id')> already exists.` during `on_mount` (line 136 → 154). The scenarios directory is user-extensible by design (the adapter's entire purpose is scanning arbitrary JSONs), so this is a user-reachable full-app crash, not a theoretical path. Note the adapter's own `get_preset()` implements first-match-wins semantics, i.e., it already assumes ids are unique.
**Fix:** De-duplicate in the adapter (consistent with `get_preset`), keeping the first occurrence per scenario_id — and/or key rows by filename instead:

```python
# manet/adapters/scenario.py — inside list_presets(), after building `preset`:
if any(p.scenario_id == preset.scenario_id for p in presets):
    continue  # or keep first-match semantics identical to get_preset()
presets.append(preset)

# manet/widgets/wizard_step_mode.py — defuse the crash regardless:
path_key = getattr(preset, "raw_config", {}).get("_source_name", preset.scenario_id)
table.add_row(..., key=preset.scenario_id)  # dedupe adapter is the primary fix; optional assert here
```

Also add a regression test: two JSON files sharing `scenario_id` must yield 1 preset (adapter) and must not raise on widget mount (pilot test).

### CR-02: `sanitize_run_tag` truncation re-introduces a Windows-illegal trailing dot

**File:** `manet/adapters/workspace.py:15-30` (line 30: `return cleaned[:32]`)
**Issue:** The primary security purpose of this function is producing Windows-legal directory components (T-09 threat mitigation). Strip of `._` happens *before* truncation, so a tag that truncates to a string ending with `.` (or an interior dot at the boundary) violates the function's own contract. Emberically verified on this Windows host:

- `sanitize_run_tag("a"*31 + ".b")` → `"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa."` (32 chars, trailing dot — Windows-illegal)
- Allocating `exp_20261107_120000_x_1_<that_tag>` via `mkdir()` succeeded, but the on-disk directory is created as `...aaa` (Win32 silently strips trailing dots), while the returned `candidate_id` and the `manifest.json` `experiment_id`/`trace_path` record the dotted name.

Consequence: the recorded experiment ID does not match the physical directory name for any tooling that reads the filesystem (`WorkspaceAdapter.list_recent_experiments` reads `entry.name`, which is dotless, while manifests carry the dotted ID) — an ID/name divergence seeded precisely where the phase promises path-safety. `clean_scenario` in `allocate_experiment_directory` (line 163) is not affected (it has no truncation), so the tag path is the sole hole.
**Fix:** Re-strip after truncation:

```python
return cleaned[:32].rstrip("._")
```

Add regression cases: `sanitize_run_tag("a"*31 + ".b")` must not end with `.` or `_`.

## Warnings

### WR-01: Wizard never resets state on re-entry — stale Step 3 config is re-confirmable

**File:** `manet/screens/simulation_workflow.py:149-190` (confirm handler)
**Issue:** `SCREENS` installs `SimulationWorkflowScreen` as a cached named screen, so `switch_screen("simulation_workflow")` always returns the same instance. After the user confirms a run, the handler switches to the workspace screen but leaves `switcher.current == "step-preflight-review"` and does not clear `launch_request`. Empirically verified: after completing a run, pressing `s` re-opens the wizard **on Step 3 with the previous run's config, Confirm button enabled, and stale `launch_request`** — a single Enter immediately allocates a duplicate experiment directory for the old run (real `.manet-workspace/<new timestamp>_<old scenario>_42` created during the verification). Same applies after Escape→re-enter if the user had walked to Step 3.
**Fix:** Reset the wizard when re-entered or after a successful confirm:

```python
# simplest: at the end of on_step_review_widget_review_confirmed (after storing launch_request)
switcher = self.query_one("#wizard-switcher", ContentSwitcher)
switcher.current = "step-mode-select"
self.launch_request = None  # hand off a copy if Phase 10 needs it

# alternatively, reset on resume:
def on_screen_resume(self) -> None:
    self.query_one("#wizard-switcher", ContentSwitcher).current = "step-mode-select"
```

Add a pilot regression test: confirm a run → `s` → assert switcher is `step-mode-select`.

### WR-02: Unhandled `OSError`s during allocation/manifest write crash the whole TUI after confirm

**File:** `manet/screens/simulation_workflow.py:152-165`
**Issue:** `on_step_review_widget_review_confirmed` calls `allocate_experiment_directory()` and `record_launch_manifest()` with no error handling. `mkdir` on a read-only/unwritable workspace root, `PermissionError`, `OSError.ENAMETOOLONG` (long `scenario_id` from a user JSON — no length cap on `clean_scenario` in `workspace.py:163-164`), or a failed manifest write all propagate out of the message handler as a fatal app crash — after the user typed a full configuration, which is then lost. Directory allocation also happens at "Confirm & Allocate" time, so the failure window is exactly the one where the user expects the operation to succeed.
**Fix:** Wrap the allocation block; on failure, notify through the rail and stay on Step 3:

```python
try:
    exp_id, exp_dir = self.workspace_adapter.allocate_experiment_directory(...)
    self.workspace_adapter.record_launch_manifest(...)
except OSError as exc:
    self.app.call_from_thread  # not needed; use:
    self.query_one("#step-preflight-review", StepReviewWidget).show_error(f"Allocation failed: {escape(str(exc))}")
    return
```

(Add a `show_error` API to `StepReviewWidget` reusing its `#review-errors-display` Static.)

### WR-03: No cross-field invariant for mobility speed ordering (min speed > max speed is accepted)

**File:** `manet/widgets/wizard_step_params.py:231-248` (independent bounds) / `manet/adapters/simulation_config.py:97-175` (Tier-2 validator has no ordering check)
**Issue:** Min Speed (0.0–100.0) and Max Speed (0.1–100.0) are each validated in isolation. A user can submit `speed_range=[80.0, 10.0]`. `SimulationRunner.initialize_nodes` passes the tuple to `RandomWaypoint`, which runs `speed = self.rng.uniform(self.vmin, self.vmax)` (`simulator/mobility.py:65`) — Python's `uniform` tolerates `vmin > vmax` (samples the inverted interval), so the run does not crash but silently simulates a semantically-wrong mobility model that still "passes" the pre-flight review with zero invariant errors. Same gap applies to the builder (`build_custom_configuration` copies `speed_range` unchecked) and to the structural invariant validator.
**Fix:** Add the invariant to Tier-2 and surface it in Step 3's blocked-launch errors:

```python
speed = config.get("mobility", {}).get("speed_range", None)
if isinstance(speed, (list, tuple)) and len(speed) == 2:
    try:
        lo, hi = float(speed[0]), float(speed[1])
        if lo >= hi:
            errors.append(f"Mobility speed_range minimum ({lo}) must be less than maximum ({hi})")
    except (TypeError, ValueError):
        errors.append("Mobility speed_range must contain two numbers")
```

### WR-04: Preset mode silently mutates flows (endpoint rewrite + single-rate overwrite) without surfacing the change

**File:** `manet/widgets/wizard_step_params.py:448-455`
**Issue:** In preset mode the form deep-copies the preset, then: (a) any flow endpoint `>= nodes` is silently rewritten (`src → 0`, `dst → nodes-1`), which can produce `src == dst` flows — e.g. preset flow `(src=0, dst=25)` re-run with nodes reduced to 10 → `(0, 0)`? no: `(src≥nodes → 0)` collides with a surviving `dst=0` — yielding a Step 3 "source cannot equal destination" launch block whose cause (UI mutation) the user never sees; (b) *every* flow's `rate_pps` is overwritten with the single advanced-tuning value, discarding per-flow rates (currently benign: all shipped presets use uniform 4.0 pps, verified, but the operation silently destroys future non-uniform presets). Step 3's summary displays the mutated topology as authentic. This conflicts with the project's honesty/mutation-disclosure posture.
**Fix:** Don't silently mutate — validate and report:

```python
bad = [f for f in config.get("flows", []) if isinstance(f, dict)
       and (f.get("src", 0) >= nodes or f.get("dst", 0) >= nodes)]
if bad:
    error_display.update(
        f"[bold $error]Preset flows use nodes outside range:[/] reduce-able endpoints {[(f['src'], f['dst']) for f in bad]}. "
        "Increase node count or edit the preset JSON.")
    return
```

### WR-05: Step 3 workspace preview ignores the injected `workspace_root` (hardcoded `.manet-workspace/`)

**File:** `manet/widgets/wizard_step_review.py:131, 137, 255-261`
**Issue:** The constructor accepts and stores `self.workspace_root` (`workspace_root=...` passed from the screen), but `update_review()` builds the preview as `preview_path = f".manet-workspace/{preview_id}/"` — the stored parameter is dead. Whenever a custom root is injected (tests do; any future embedding will), the user-facing "Target Workspace Destination" names a directory that is not where allocation will happen. The parameter+dead-store also hides the bug from static analyzers.
**Fix:**

```python
preview_path = f"{self.workspace_root.as_posix().rstrip('/')}/{preview_id}/"
```

(Optionally show only the parent-relative leaf when the root equals the default.)

### WR-06 (test reliability): periodic-timer test cannot exercise the 4s interval it claims to verify

**File:** `tests/test_manet_dashboard_workspace.py:337-350`
**Issue:** `test_periodic_diagnostics_refresh_timer` advances the pilot by only 0.2s (`pilot.pause(0.2)`) while the interval under test is `set_interval(4.0, ...)` — the timer can never fire within the test, so the "periodic timer triggers safely" claim is unverifiable; the closing `assert screen.is_mounted` is trivially true and the assert set would pass even if the timer were broken or crashed on first fire. This is a false-coverage pattern (test green but does not test the named behavior), which misleads future maintainers.
**Fix:** Actually advance past the interval, or drive the callback directly and drop the mismatched claim:

```python
await pilot.pause(4.5)          # inside run_test the interval fires late during shutdown — guard with press("ctrl+q")
# or, deterministic alternative: capture the interval callback
self._interval_cb = callback  # in MainWorkspace: self.set_interval(4.0, self.refresh_diagnostics)
```

Simplest robust pattern: `screen.set_interval` call site stays; test calls `screen.refresh_diagnostics()` twice and also asserts no exception via `pilot.pause(4.0)` with `show=False` binding — at minimum, update the docstring to match what is verified.

## Info

### IN-01: Unused imports verified by pyflakes (dead code)

**File:** `manet/screens/simulation_workflow.py:11` (`Container`), `manet/widgets/wizard_step_mode.py:9` (`Label`), `manet/widgets/wizard_step_params.py:10` (`Vertical`), `manet/widgets/wizard_step_review.py:12` (`Horizontal`, `Vertical`)
**Issue:** All five imports are unused in their modules; they double the surface for future import-cycle churn and fail any future lint gate.
**Fix:** Delete the imports.

### IN-02: Corrupt artifacts silently vanish with no signal (`except Exception: continue/pass`)

**File:** `manet/adapters/scenario.py:64`, `manet/adapters/workspace.py:91, 115-116, 143-144`, `manet/screens/main_workspace.py:238-264`
**Issue:** A malformed scenario JSON or corrupt manifest silently disappears from preset/workload lists, and diagnostics refresh swallows all exceptions, with no log line or user-facing notice. For a presentation layer whose contract is honest status display, silent data loss contradicts the project's own honesty tests (e.g., honest notices in `NotificationRail`). `except Exception` also hides genuine programming errors (e.g., a typo in a query_one would compile-time-invisible).
**Fix:** Log at minimum: `self.log("Skipped malformed scenario file", json_path)` (Textual log), and prefer `except (OSError, ValueError, json.JSONDecodeError)` over bare `Exception` where the failure mode is known.

### IN-03: Private API access `self.app._installed_screens`

**File:** `manet/screens/simulation_workflow.py:97, 183`
**Issue:** Both call sites check `if "workspace" in self.app._installed_screens` — reading a private Textual attribute (a `dict` in 8.x, a `set` in prior versions). Public equivalent exists: `App.is_screen_installed(screen)` (app.py:2731 in the installed 8.2.8).
**Fix:** `if self.app.is_screen_installed("workspace"):`

### IN-04: Command parameter machinery is untestable dead weight today

**File:** `manet/commands/registry.py:31, 90-110`, `manet/commands/console_driver.py:104-107`
**Issue:** Every registered command has `parameters=()`, so `resolve()`'s positional-matching branch (`dict(zip(cmd.parameters, args))`), the driver's `action_fn(**params)` call, and the arg-count error path are all unreachable in practice — no test can exercise them without inventing a fake command. The docstring justifies forward-compat, but the machinery is currently unverified code in a security-tagged resolver.
**Fix:** Either add one parameterized registry command (e.g., `theme-set` with `action_set_theme(theme_name)`, already implemented in `app.py:104-108` and never wired!) with its test, or trim the branch until a parameterized command exists. Note `action_set_theme` receiving a string parameter makes the trim/decide concrete.

### IN-05: Previewed directory name almost never matches the actual allocated name (timestamp churn)

**File:** `manet/widgets/wizard_step_review.py:255-258` vs `manet/adapters/workspace.py:162` / `manet/screens/simulation_workflow.py:152`
**Issue:** `update_review()` stamps the preview with `datetime.now()` at Step 3 render time; the real allocation re-stamps at confirm time. Unless the user confirms within the same second, the "Target Directory" preview shows a name that will not exist — a small honesty gap in an explicitly user-facing pre-flight artifact.
**Fix:** Render the preview without a full timestamp (e.g., `exp_<UTC date>_<scene>_<seed>[_tag]` with a "timestamp fixed at allocation" note), or cache the preview timestamp for actual allocation.

### IN-06: CWD-anchored defaults silently degrade when the TUI is not launched from repo root

**File:** `manet/adapters/scenario.py:28`, `manet/adapters/simulation_config.py:161`, `manet/widgets/wizard_step_review.py:136-137`, `manet/screens/simulation_workflow.py:74`
**Issue:** Scenario discovery (`Path.cwd() / "scenarios"`), model gating, and workspace root all default to CWD. Launching the app from any other directory yields an empty preset table (looks like "no scenarios exist") and "CHAMPION MODEL MISSING" — presented as project-state claims rather than launch-context errors.
**Fix:** Anchor defaults to the project root: `PROJECT_ROOT = Path(__file__).resolve().parents[2]` next to `manet/__init__.py` and reuse it in the three default sites (keep constructor injection for tests).

---

## Verification evidence (commands executed during review)

| Check | Result |
|---|---|
| `python -m pytest` on the 8 listed test files | 55 passed, 0 failed |
| AST scan of 14 in-scope `manet/` files for forbidden imports | 0 forbidden imports |
| pyflakes on the 14 in-scope `manet/` files + 8 test files | 5 unused manet imports (IN-01), 9 test-file cleanliness notes (omitted from findings per test-file policy, none affect reliability except WR-06) |
| Reproduction: duplicate `scenario_id` in two temp JSON files → `app.run_test()` | `DuplicateKey` raised from `wizard_step_mode.py:154` during `on_mount` (CR-01) |
| Reproduction: `sanitize_run_tag("a"*31 + ".b")`, then `mkdir` of the resulting name on Windows | 32-char tag ends `.`; on-disk entry name silently stripped (CR-02) |
| Reproduction: run wizard 1→2→3→confirm, then re-open via `s` | `switcher.current == "step-preflight-review"` and stale `launch_request` on re-entry (WR-01) |
| T-09-08 grep across `manet/` | no `os.system`/`subprocess`/`exec`/`eval`; registry actions are string names only |
| Scenario JSON rate audit | all shipped presets use uniform 4.0 pps (bounds the impact of WR-04 to future non-uniform presets) |

All review-time reproductions of workspace side effects (`.manet-workspace/exp_20261108_041605_e1_normal_30n_42` created by the WR-01 probe) were removed before this report was written; the working tree contains no modifications.

---

_Reviewed: 2026-11-08T04:55:00Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
