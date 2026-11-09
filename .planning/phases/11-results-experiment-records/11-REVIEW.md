---
phase: 11-results-experiment-records
reviewed: 2026-11-09T09:22:37Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - .gitignore
  - manet/adapters/workspace.py
  - manet/app.py
  - manet/commands/registry.py
  - manet/runtime/keymap.py
  - manet/screens/__init__.py
  - manet/screens/history.py
  - manet/screens/live_run.py
  - manet/screens/main_workspace.py
  - manet/screens/prune_modal.py
  - manet/screens/results.py
  - manet/widgets/qos_scorecard.py
  - tests/test_manet_history_screen.py
  - tests/test_manet_manifest_artifacts.py
  - tests/test_manet_results_screen.py
  - tests/test_manet_workspace_pruning.py
findings:
  critical: 0
  warning: 5
  info: 9
  total: 14
  necessity: 1
status: issues_found
---

# Phase 11: Code Review Report

**Reviewed:** 2026-11-09T09:22:37Z
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed all Phase 11 source (workspace adapter manifest/artifact/pruning layer, results/history/live-run/workspace screens, QoS scorecard, keymap/registry, `.gitignore`) plus the four accompanying test files, at standard depth with cross-file contract checks.

**What holds up under adversarial scrutiny:**
- The deletion safety chain (`preview_experiment_deletion` → fingerprint → `delete_experiment_run` revalidation) is genuinely sound: top-level and nested symlink rejection (incl. `os.walk(followlinks=False)` + explicit `islink` checks), `resolve()`-based containment against workspace root, root-self rejection, atomic fingerprint check before `rmtree`, and Windows `PermissionError` handling. All exercised by tests.
- `verify_artifact_checksums` deflects `../evil.txt` and absolute-path escape attempts in `artifacts[].relative_path` to `SECURITY_VIOLATION` status (verified by `test_unsafe_artifact_paths_boundary`).
- Manifest writes are atomic (`manifest.json.tmp` + `os.replace`), and the atomicity is test-verified failure injection.
- Cross-file contracts verified: the runner's metric key set (`simulator/metrics.py:114-122`) matches `QosScorecard` and `dashboard_cards` consumers exactly; every widget method called by `main_workspace.py` (`update_report`/`update_status`/`refresh_experiments`/`dismiss`/`probe_all`/`get_status`) and every supervisor attribute used by `live_run.py` exists; all 10 registry action names resolve to real `ManetApp` methods.
- Full phase test suite passes: 42 passed, 3 skipped (Windows symlink-privilege skips — correct behavior via `pytest.skip`).
- `.gitignore` `results/*` + `!results/plots/` re-inclusion idiom is correctly ordered for git semantics.

**Key concerns:** zero Critical findings, but five Warnings — most notably `ResultsScreen._resolve_target` resolving experiment IDs without the workspace-containment hardening every neighboring workspace API enforces, and two places where primary user actions fail silently (`except Exception: pass`) with no notification. One test has its own assertions inside a `try/except Exception` so it can never fail on the behavior it claims to verify.

## Critical Issues

None found. The deletion and checksum security paths survived adversarial probing (traversal, symlink, tamper, stale-preview, same-size-modification variants all tested and passing).

## Warnings

### WR-01: ResultsScreen resolves experiment IDs without workspace containment validation

**File:** `manet/screens/results.py:96-100` (also `:109`)
**Issue:** `_resolve_target()` builds `experiment_dir = self.workspace_adapter.workspace_root / self._requested_experiment_id` and then reads `manifest.json` (`get_experiment_manifest`), `isolation_log.json`, and `isolation_log.csv` from it — with no traversal/symlink/containment check. An ID like `".."`, `"foo/../../bar"`, or an absolute path changes which directory the screen reads. Every other workspace entry point hardens exactly this (`WorkspaceAdapter._resolve_experiment_dir`, `manet/adapters/workspace.py:452-462`, rejects `..`, symlinks, and root-escape) and `verify_artifact_checksums` guards `relative_path` escapes — so ResultsScreen is an inconsistent soft spot in an otherwise hardened boundary. Currently not user-injectable (all call sites pass manifest-derived IDs; the `view:results` registry command has zero parameters), which keeps this at Warning rather than Critical, but the class is public API and the next caller that wires user text through it (e.g. a console command gaining a parameter) inherits a disk-read primitive.
**Fix:** Route resolution through a containment-checked adapter API instead of raw path math:

```python
# In WorkspaceAdapter — make the hardened resolver public:
def resolve_experiment_dir(self, experiment_id: str) -> Path:
    return self._resolve_experiment_dir(experiment_id)  # existing checks

# In ResultsScreen._resolve_target:
if self._requested_experiment_id:
    try:
        self.experiment_dir = self.workspace_adapter.resolve_experiment_dir(
            self._requested_experiment_id
        )
    except (ValueError, FileNotFoundError):
        self._resolve_failed_no_completed = True
        return False
    ...
```

### WR-02: Primary navigation actions fail silently — no user feedback on exception

**File:** `manet/app.py:265-268` (`action_show_results`) and `manet/app.py:230-238` (`action_show_history`)
**Issue:** The final `try: self.push_screen(ResultsScreen(...)) / except Exception: pass` in `action_show_results` swallows every failure of the screen's *primary purpose* — constructor-time disk I/O (`_resolve_target`), widget construction — with no notification and no fallback navigation. Same pattern in `action_show_history`, where both `push_screen` and the `switch_screen` fallback are individually swallowed; if both fail the user presses a key/palette command and nothing observable happens. Elsewhere in this file failures are at least surfaced via `self.notify` (e.g. `app.py:250-253`), so this is inconsistent even within the same action.
**Fix:** Surface the failure via the already-guarded notify helper:

```python
try:
    self.push_screen(ResultsScreen(experiment_id=experiment_id))
except Exception as exc:
    try:
        self.notify(f"Could not open results: {escape(str(exc))}", severity="error")
    except Exception:
        pass
```

(And in `action_show_history`, notify on the final fallback failure rather than bare `pass`.)

### WR-03: stat race inside list_recent_experiments empties the entire history listing

**File:** `manet/adapters/workspace.py:355-362`
**Issue:** The mtime sort key lambda calls `p.stat()` per entry, and the whole `sorted(...)` sits inside one `try/except (OSError, ValueError): return []`. If *any* workspace entry (e.g. one the user just deleted from another session, or a transient top-level file removed concurrently) vanishes between `iterdir()` and its `stat()`, the single `OSError` aborts the sort and the function returns `[]` — the History refresh then renders an empty table until the next poll/press, misrepresenting the workspace ("record gone" when it is not). The per-entry manifest reads below are already individually exception-guarded (`continue` on failure), so the all-or-nothing stat is the outlier.
**Fix:** Degrade per entry instead of per listing:

```python
def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0

entries = sorted([d for d in self.workspace_root.iterdir()], key=_mtime, reverse=True)
```

### WR-04: NaN PDR renders as "nan" in the history table (scorecard path is correct)

**File:** `manet/screens/history.py:280`
**Issue:** `pdr_str = f"{r.pdr:.4f}"` does not validate the value. `update_manifest_status` serializes metrics with `json.dump` (default `allow_nan=True`), so a manifest with `"pdr": NaN` — genuinely producible when a scenario has zero data-sent packets — parses back to `float('nan')` in `_summary_from_manifest` (`workspace.py:345`), and the history cell shows literal `nan`. The sibling consumer `QosScorecard` explicitly defends this (`qos_scorecard.py:14-15`, `test_qos_scorecard_nan_inf_missing_metrics` proves the team considers NaN a real input), so History is inconsistent with the established contract for the same data.
**Fix:** Reuse the same validity rule:

```python
def _pdr_str(pdr: float | None) -> str:
    if pdr is None or not math.isfinite(pdr):
        return "N/A"
    return f"{pdr:.4f}"
```

or import/expose `_is_valid_number` from `qos_scorecard` rather than duplicating it.

### WR-05: Test swallows its own assertions — artifact verification result can never fail the test

**File:** `tests/test_manet_results_screen.py:210-222` (`test_results_screen_background_worker_thread_safety`)
**Issue:** Both content assertions are inside `try:` with a bare `except Exception: pass`. `AssertionError` subclasses `Exception`, so if the verification never lands (e.g. worker regression causes the `#artifacts-content` static to keep showing "VERIFYING CHECKSUMS"), the assert raises, is swallowed, and the test passes — it verifies worker *source text* only and can no longer fail on runtime behavior, which is precisely the flake this test exists to catch.
**Fix:** Catch only the widget-lookup failure, not assertion failure:

```python
try:
    w = screen.query_one("#artifacts-content", Static)
except NoMatches:
    pytest.fail("#artifacts-content not mounted")
txt = str(w.render())
assert "VERIFYING CHECKSUMS" not in txt
assert ("VERIFIED" in txt or "RECORDED" in txt or "CORRUPTED" in txt or "MISSING" in txt)
```

## Info

### IN-01: Phantom fallbacks defending against unproducible states

**File:** `manet/adapters/workspace.py:489`, `manet/adapters/workspace.py:210-212`, `manet/screens/prune_modal.py:88`
**Category:** necessity
**Subtype:** phantom requirement / impossible-state guard (Info — judgment plus one provable from the stack)
**Issue:** Three defensive variants have no possible trigger in this runtime: (1) `getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9))` — `os.stat_result` has exposed `st_mtime_ns` since Python 3.3, and this codebase requires ≥3.9 (`Path.is_relative_to` at `workspace.py:258/438`), so the fallback branch is unreachable; (2) `del workspace_root` in `verify_artifact_checksums` (`workspace.py:212`) — the parameter is accepted solely to be discarded; the two call sites pass one argument; (3) `preview.get("path", preview.get("directory_path", ""))` (`prune_modal.py:88`) — the only producer (`preview_experiment_deletion`, `workspace.py:503`) always emits `"path"`; no code path ever produces `"directory_path"`.
**Fix:** Use `st.st_mtime_ns` directly; drop the `workspace_root` parameter (or wire it meaningfully if symmetry matters — proofs say it doesn't); drop the `directory_path` fallback and read `"path"` directly.

### IN-02: Dead code and unused imports in results.py

**File:** `manet/screens/results.py:14`, `manet/screens/results.py:22`, `manet/screens/results.py:297`
**Issue:** `Vertical` is imported from `textual.containers` but never used (`Container` is the only container composed). `ISOLATION_SCHEMA_FIELDS` (line 22) is defined and never referenced. Line 297 `except (RuntimeError, Exception)` — `RuntimeError` is a subclass of `Exception`, so the tuple is redundant.
**Fix:** Remove the unused import and constant; write `except Exception`.

### IN-03: `_format_metric` helper exported but never called

**File:** `manet/widgets/qos_scorecard.py:18-25`, `manet/widgets/qos_scorecard.py:162`
**Issue:** `_format_metric` is defined, exported in `__all__`, and never invoked anywhere in the module (each `_fmt_*` method does its own validation) nor by any other reviewed file. Dead generality with a misleading public export.
**Fix:** Delete the function and remove it from `__all__`; or refactor the `_fmt_*` methods to delegate to it if a second consumer ever materializes.

### IN-04: keymap single-source invariant violated by duplicated inline bindings

**File:** `manet/runtime/keymap.py:3-4` vs `manet/screens/history.py:45-51`, `manet/screens/results.py:28-31`, `manet/screens/live_run.py:52`
**Issue:** `keymap.py`'s docstring declares the invariant "keybinding strings … defined in a single location and never duplicated inline across screens." Then: `"b"`/Back is bound inline in both `history.py:47` and `results.py:30`; `history.py:48` hardcodes literal `"r"` for Refresh while `keymap.BINDING_RESULTS = "r"` is consumed by `main_workspace.py` for a different action on the same key; `"escape"` is hardcoded in three screens. No bug today, but the stated contract is already broken in the phase that added these screens.
**Fix:** Promote the repeated literals to keymap constants (e.g. `BINDING_BACK = "b"`, `BINDING_HISTORY_REFRESH = "r"`) and bind screens from the keymap, matching how `live_run.py` already correctly imports `BINDING_STOP`/`BINDING_BACKGROUND`.

### IN-05: Test hygiene — leftover junk expression, redundant sleeps, unused imports

**File:** `tests/test_manet_workspace_pruning.py:89`; `tests/test_manet_history_screen.py:12`, `:453-455`, `:482-484`; `tests/test_manet_results_screen.py:7`, `:15`, `:17` (and `:355-359`); `tests/test_manet_workspace_pruning.py:5`
**Issue:** (1) `adapter.delete_experiment_run("exp_stale2" if False else "exp_same", ...)` — a leftover debugging conditional; should just be `"exp_same"`. (2) Back-to-back duplicated `tmod.sleep(0.02); os.utime(...)` calls in two tests (history test `:454-455` shipped twice; results test `:356-359` same pattern) — one utime suffices. (3) Dead scaffolding `orig_adapter = app_mod.WorkspaceAdapter if hasattr(...) else None` (history test `:482-484`) is assigned, never used. (4) Unused imports: `Static` (history test), `math`, `TabbedContent`, `ExperimentSummary` (results test), `json` (pruning test).
**Fix:** Delete the leftover conditional-else, the duplicate sleep/utime lines, the orphan assignment, and the unused imports.

### IN-06: HistoryTestApp constructs ResultsScreen with no args → reads the real developer workspace during tests

**File:** `tests/test_manet_history_screen.py:69`
**Issue:** `HistoryTestApp.on_mount` runs `install_screen(ResultsScreen(), "results")`. A no-arg `ResultsScreen` executes `_resolve_target()` at construction, which calls `list_recent_experiments(limit=None)` on the *default* adapter — i.e. the real `.manet-workspace/` under the project root on the machine running the tests. Read-only, so impact is limited to non-hermetic behavior (runs found on a real workspace can change results-screen construction cost/state; CI determinism depends on the workspace being absent), but tests should not touch the developer's actual data directory.
**Fix:** Construct the dummy with a tmp-scoped adapter where isolation matters, e.g. patch `manet.screens.results.WorkspaceAdapter` in the fixture, or build the installed screen as `ResultsScreen(workspace_adapter=WorkspaceAdapter(workspace_root=tmp_path / "ws"))`.

### IN-07: Deletion-preview fingerprint does not cover empty directories

**File:** `manet/adapters/workspace.py:466-508`
**Issue:** `preview_experiment_deletion` records only files (name/size/mtime/hash) in the fingerprint; `os.walk`'s `dirnames` are checked for symlinks but never recorded. An empty subdirectory created under the experiment dir between preview and confirm changes the final `preview_experiment_deletion` output (it lists it... actually it does not — only files are recorded) and bypasses the stale-preview `RuntimeError`. The blind spot is bounded: the deleted directory is still entirely inside the already-confirmed experiment directory, and no file content can change undetected. Practical harm ≈ zero; noted because the mechanism is marketed as complete "cryptographic revalidation."
**Fix:** If coverage matters, fold `sorted(relative dir paths)` into `fp_material`, or document that the fingerprint guarantees file-content equality only.

### IN-08: Workspace hero-vs-table layout decided only at compose time

**File:** `manet/screens/main_workspace.py:219-227` (with `refresh_workspace` `:279-286`)
**Issue:** `compose()` picks `RecentExperimentsTable` or `CtaHeroPanel` based on a snapshot taken at compose time. Fans of the empty↔non-empty transition are not handled: after deleting the last run (Phase 11's own pruning feature!) and returning to the workspace, `refresh_workspace` only refreshes the already-mounted table — the user sees an empty DataTable where the design contract (`CtaHeroPanel` empty state) says they should see the hero panel; the inverse (hero → runs appear) stays hero until remount.
**Fix:** In `refresh_workspace`, swap widgets when the state flips: if empty and a table is mounted, remove it and mount `CtaHeroPanel`; conversely mount the table when runs exist.

### IN-09: CSV row_count undercounts files lacking a trailing newline

**File:** `manet/adapters/workspace.py:74-77`
**Issue:** `_compute_file_hash_and_rows` counts `\n` bytes and computes `row_count = total_lines - 1` for CSVs. For a CSV whose last data row is not newline-terminated (`"h1,h2\na,b"` — 1 `\n`), the result is `0` rows despite one data row. Also, quoted CSV fields containing embedded newlines inflate the count. Manufactured traces in this repo appear newline-terminated, so impact is metadata quality in `manifest.json`/Results display only.
**Fix:** For row counts use the `csv` module (count `len(list(csv.reader)) - 1`) or treat the last partial line: `row_count = total_lines - 1 + (1 if size_bytes > 0 and last byte != b"\n" else 0)`.

---

**No Critical findings.** The submission is broadly solid — the phase's core security surface (deletion safety, checksum verification, traversal rejection) is the strongest part of the change, and every cross-file contract I traced (metrics keys, widget methods, supervisor attributes, registry actions) holds.

_Reviewed: 2026-11-09T09:22:37Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
