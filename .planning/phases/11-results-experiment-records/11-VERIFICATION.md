---
phase: 11-results-experiment-records
verified: 2026-11-10T04:45:04Z
status: human_needed
score: 27/27 must-haves verified
overrides_applied: 0
verification_coverage_files:
  - manet/adapters/workspace.py
  - manet/widgets/qos_scorecard.py
  - manet/screens/results.py
  - manet/screens/history.py
  - manet/screens/prune_modal.py
  - manet/screens/main_workspace.py
  - manet/screens/live_run.py
  - manet/runtime/keymap.py
  - manet/commands/registry.py
  - manet/app.py
  - manet/screens/__init__.py
  - .gitignore
  - tests/test_manet_manifest_artifacts.py
  - tests/test_manet_workspace_pruning.py
  - tests/test_manet_results_screen.py
  - tests/test_manet_history_screen.py
fingerprint: v4:sha256:fee98be16a215e56df52f492a4ad621a4e5f268153249da18b6f7d73513494e6
human_verification:
  - test: "Launch the TUI in a real terminal, run a simulation to completion, and inspect the ResultsScreen"
    expected: "QoS Scorecard colors render with the intended SOC palette (green #3fb950 / yellow #d29922 / red #f85149), split-pane proportions look correct, and the three tabs are visually navigable"
    why_human: "Color rendering, layout proportion, and terminal-font behavior cannot be verified programmatically; Pilot tests assert DOM structure only"
  - test: "Real-keyboard navigation loop: MainWorkspace [R] → History → Enter → Results → Esc → [Esc] back, and LiveRunScreen [V] after completion"
    expected: "Every shortcut lands on the intended screen in a live terminal with no screen stacking or focus traps"
    why_human: "Keyboard focus order and binding suppression while typing in search inputs is runtime behavior; automated Pilot coverage approximates but does not feel out real terminal quirks"
  - test: "Start a prune ([D]) on a real run, press Enter to confirm, then separately press Esc on a second attempt"
    expected: "Confirm deletes the record with an itemized preview shown first; cancel leaves the run and table untouched"
    why_human: "Destructive-action UX and modal interaction in a live terminal is destructive and interactive; only human confirmation establishes the real gesture flow"
  - test: "With a run's trace.csv open in another Windows application (e.g., Excel), attempt [D] deletion and confirm"
    expected: "HistoryScreen remains active with table intact and shows the actionable 'files are locked by another Windows process' notification"
    why_human: "Real OS file-handle contention cannot be reproduced faithfully in unit tests (the handler is monkeypatch-tested); needs a live confirmation"
---

# Phase 11: Results & Experiment Records — Verification Report

**Phase Goal:** Completed runs produce honest, verifiable experiment records the user can browse and reopen
**Verified:** 2026-11-10T04:45:04Z (HEAD: 9fee649)
**Status:** human_needed (all automated must-haves verified; 4 UI/OS-level items routed to human)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Merge logic: ROADMAP Success Criteria are the contract; PLAN truths that restate SC wording are merged into the SC row. Every distinct truth below is one row. Sources annotated.

**Roadmap Success Criteria (the contract)**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SC1: Results view shows actual PDR, throughput, delay, routing overhead computed via existing `simulator.metrics.compute_metrics`, plus sent/received packet counts and generated trace location (merges 11-02 truths: scorecard renders 4 metrics, split-pane layout, trace-path display) | ✓ VERIFIED | `bootstrap.py:160` calls `simulator.metrics.compute_metrics(runner.trace_rows, sim_duration=runner.duration)`; `supervisor.py:213-217` persists returned dict into manifest via `update_manifest_status(..., "COMPLETED", metrics=metrics)` (same for INTERRUPTED at 184-188); `results.py:209-215` renders `manifest["metrics"]` via `QosScorecard`; `qos_scorecard.py:130-159` maps keys `pdr/throughput_bps/avg_delay_s/routing_overhead/data_sent/data_received/routing_packets` — exactly `compute_metrics`'s output keys (`simulator/metrics.py:114-123`); Tab 1 shows Path + Relative path (`results.py:190-198`) |
| 2 | SC2: Each experiment stores a manifest (experiment ID, configuration, seed, software version, run status, timestamps, logs, trace paths, available metrics) written atomically, with SHA-256 checksums for completed artifacts (merges 11-01 truths: terminal-state hashing, atomic tmp+os.replace, canonical relative paths, tag preservation) | ✓ VERIFIED | `record_launch_manifest` (workspace.py:110-135) records experiment_id, scenario, seed, `software_version` (Line 127), `created_at`, `trace_path`, full configuration, tag; `update_manifest_status` writes `started_at` on RUNNING / `completed_at`+`artifacts` on terminal states via `manifest.json.tmp` + `os.replace` (Lines 146, 179-182) — spot-check recreated the whole flow live: status/started_at/completed_at/software_version/configuration/tag all present and sha256 hex64 recorded. Caveat: "logs" is represented by `error_details` (failure/supervisor error excerpt, workspace.py:176-177; displayed at results.py:169-171) — no general run-log field is persisted, consistent with Phase 10's bounded in-memory telemetry and Tab 3's "supervisor error/log excerpts if any"; see Info note in Anti-Patterns |
| 3 | SC3: Session history list lets user browse past experiments and open a completed result; completed experiment metadata is read-only — reruns create new runs (merges 11-03 history truths and 11-01 limit=None/tag truths) | ✓ VERIFIED | `history.py:140` loads `list_recent_experiments(limit=None)`; `workspace.py:349-406` has no truncation when `limit is None` (Line 403 guards only non-None) and is docstringed "(strictly read-only)"; Enter → `ResultsScreen` (`history.py:313-343`); reruns allocate collision-free new timestamped dirs with `_1/_2` suffix (`workspace.py:408-449`); no metadata-edit path exists anywhere in the UI; spot-check listed a run with tag round-trip (pdr 0.83) via limit=None |
| 4 | SC4: Workspace artifacts ignored by Git without unintentionally changing `.gitignore` semantics; any safe-cleanup path requires preview plus explicit confirmation (merges 11-03 .gitignore/modal truths) | ✓ VERIFIED | `.gitignore:4` `.manet-workspace/` with `traces/`, `data/`, `results/*` untouched; live `git check-ignore` confirms `.manet-workspace/.../trace.csv` and `manifest.json` ignored (`.gitignore:4`), `traces/x.csv`, `data/x.bin`, `results/x.txt` still ignored, and `results/plots/a.png` NOT ignored (exit 1) — semantics preserved; cleanup path: `preview_experiment_deletion` (workspace.py:464-508, itemized files/sizes/fingerprint) → `PruneConfirmationModal` (prune_modal.py:20, `ModalScreen[bool]`, dismiss True/False only, never deletes) → `delete_experiment_run` with fingerprint revalidation (workspace.py:510-537) |

**Plan 11-01 truths (workspace & manifest engine)**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 5 | Terminal-state finalization (COMPLETED, INTERRUPTED, FAILED) hashes payload artifacts with 64KB chunking; CSV row_count = data lines minus header; JSON record count = parsed list length (never newlines); partial runs hash what exists without failing | ✓ VERIFIED | `workspace.py:65-107` (`_compute_file_hash_and_rows`, `ARTIFACT_FILENAMES`); spot-check: csv row_count==2 for 2 data rows, json row_count==1; `tests/test_manet_manifest_artifacts.py` (`test_failed_and_interrupted_run_partial_artifacts`, `test_csv_and_json_row_count_semantics`) passing in green suite |
| 6 | Unsuccessful os.replace leaves previous manifest intact (atomic resilience) | ✓ VERIFIED | `workspace.py:179-182` writes tmp then replaces; `test_atomic_write_failure_resilience` passing |
| 7 | Lazy integrity verification reports authentic VERIFIED / CORRUPTED / MISSING / RECORDED (legacy) / ERROR / SECURITY_VIOLATION without circular manifest hashing, confined within experiment_dir | ✓ VERIFIED | `workspace.py:207-303`; manifest.json never in `ARTIFACT_FILENAMES` (Line 19); spot-check demonstrated VERIFIED→CORRUPTED→MISSING inline, `../evil.txt` → `SECURITY_VIOLATION`, legacy RECORDED + ERROR paths covered by `test_legacy_manifest_recorded_state`, `test_malformed_and_missing_manifests` |
| 8 | Deletion previews itemize recursively (relative path, size, mtime, content sha256, total bytes) and reject symlinked dirs/files; cryptographic fingerprint over `path:size:mtime_ns:content_sha256` detects same-size modification; traversal/workspace-root targets rejected; Windows PermissionError → actionable RuntimeError | ✓ VERIFIED | `workspace.py:452-537` (`_resolve_experiment_dir`, `preview_experiment_deletion`, `delete_experiment_run`); spot-check: fingerprint hex64, same-size modification rejected with RuntimeError, delete reclaims bytes and removes dir, `../../scenarios` and `.` rejected; `tests/test_manet_workspace_pruning.py::test_windows_file_lock_handling`/`test_delete_experiment_run_traversal_and_root` passing (symlink tests skipped on Windows env constraint — guards verified by code read at Lines 454, 472-481) |

**Plan 11-02 truths (results screen & scorecard — beyond merged SC1)**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 9 | Missing/None/NaN/inf/non-numeric metrics render dim N/A; canonical `packet_loss_ratio` used with PDR-derivation only as fallback; PDR color thresholds (≥80% green, 50–79.9% yellow, <50% red) documented as presentation heuristics | ✓ VERIFIED | `qos_scorecard.py:14-15` (`math.isnan`/`isinf` checks), `:119-127` (`_loss_text` canonical-first fallback), `:70-83` (`_fmt_pdr` colors, Line 74 comment "Visual presentation heuristic"); tests `test_qos_scorecard_*` passing |
| 10 | Background verification runs in a synchronous `@work(thread=True)` worker, delivers UI updates via `call_from_thread`, guards stale results with `is_mounted`, and cancels only screen-scoped workers on unmount (never `cancel_all`) — always dynamic, never static badges | ✓ VERIFIED | `results.py:283-304` (decorated synchronous def, `get_current_worker`, `worker.is_cancelled`, `call_from_thread`), `:356-373` (`if not self.is_mounted: return`), `:375-380` (`self.workers.cancel_node(self)`); tests `test_results_screen_background_worker_thread_safety`, `test_results_screen_stale_worker_discarded_on_dismiss`, `test_results_screen_unmount_does_not_cancel_unrelated_workers` passing |
| 11 | Partial/interrupted runs display available metrics with an informative banner, never fabricating zeros or claiming unavailability | ✓ VERIFIED | `results.py:214-220` (banner when INTERRUPTED/FAILED or non-COMPLETED with metrics); `test_results_screen_...::test_qos_scorecard_partial_run_display` passing |
| 12 | Security tab distinguishes IDS-disabled runs from IDS-enabled-with-zero-isolates and parses the real isolation schema (sim_time, node_id, predicted_type, action, prob_malicious, reason) | ✓ VERIFIED | `results.py:22` (`ISOLATION_SCHEMA_FIELDS` exactly the six fields), `:126-147` (CSV DictReader / JSON load), `:234-263` (disabled → dim notice; active-zero → distinct green notice; events → DataTable with escape) |
| 13 | Tab 3 displays authentic `created_at`, `started_at`, `completed_at` (and `updated_at`) without substituting updated_at for started_at | ✓ VERIFIED | `results.py:164-167`; `test_results_screen_timestamp_display` passing |
| 14 | No-ID open resolves latest COMPLETED run (ignoring newer FAILED/INTERRUPTED) or redirects to HistoryScreen with honest notification | ✓ VERIFIED | `results.py:102-110` (next COMPLETED from `list_recent_experiments(limit=None)`), `:203-206` honest Static, `:266-278` notify + `switch_screen("history")`; tests `test_results_screen_no_id_fallback_selects_latest_completed`, `test_results_screen_no_completed_runs_redirects_to_history` passing |
| 15 | All dynamic strings/paths/params/node IDs/log excerpts escaped via `rich.markup.escape` | ✓ VERIFIED | `import escape` + used at results.py:155-171, 183-198, 247-262, 316-333 etc; qos_scorecard.py:25, 81-83; history.py:276-281; prune_modal.py:87-100 |

**Plan 11-03 truths (history, pruning UX & wiring — beyond merged SC3/SC4)**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 16 | PruneConfirmationModal is confirmation-only returning True/False; HistoryScreen owns deletion execution + exception handling and revalidates the fingerprint before physical deletion; failure leaves HistoryScreen active with table intact + actionable error notification; a cancelled modal never invokes deletion | ✓ VERIFIED | `history.py:345-386` (`action_prune_selected` pushes modal with preview; `_handle_prune_result` early-returns on `not confirmed`, calls `delete_experiment_run(run_id, expected_preview=preview)`, catches `(RuntimeError, OSError, ValueError)` → notify, refresh only on success); modal never touches disk (prune_modal.py docstring + no deletion calls); tests `test_history_screen_pruning_workflow_success_and_cancellation`, `test_history_screen_pruning_error_notification` passing |
| 17 | Columns (Run ID, Scenario, Seed, Status, PDR, Date) sort ascending/descending via header click; search matches scenario/tag/run ID/seed in real time; status filter buttons ALL/COMPLETED/INTERRUPTED/FAILED | ✓ VERIFIED | `history.py:216-258` (`_sort_key` incl. PDR None-last, `on_data_table_header_selected`, `action_sort_by`), `:196-214` (`_filtered_runs` haystack over id/scenario/tag/seed), `:161-189` (filter buttons with active-class toggle); tests passing |
| 18 | MainWorkspace row selection (Enter on RecentExperimentsTable) and [R] open HistoryScreen; [R] inside History refreshes from disk | ✓ VERIFIED | `main_workspace.py:293-301` (RowSelected → push "history"), `:311-321` (`action_results` → history), `history.py:145-150, 48` (`action_refresh_runs` + binding); tests `test_dashboard_enter_opens_history` passing; regression `test_manet_navigation.py::test_results_shortcut_opens_history` passing (49c4081-aligned contract) |
| 19 | Newly finalized runs auto-synchronize with MainWorkspace and HistoryScreen on completion/screen resume | ✓ VERIFIED | `main_workspace.py:288-291` (`on_screen_resume` → refresh_workspace) + `:277` refresh after report update; `history.py:388-390` (`on_screen_resume` → refresh_runs) |
| 20 | LiveRunScreen terminal COMPLETED state enables [V] shortcut + View Results button opening ResultsScreen for the actual completed run | ✓ VERIFIED | `live_run.py:54` (Binding BINDING_VIEW_RESULTS), `:320-330` (button mounted only when `sup.state == WorkloadState.COMPLETED`), `:355-365, 377-378` (`action_view_results` reads `sup.current_request.experiment_id` — the actual run); test `test_live_run_v_opens_actual_results` passing |
| 21 | Commands `view:results` and `view:history` registered; `view:results` without ID safely resolves latest COMPLETED or redirects to history with honest notification; `view:history` opens history from anywhere | ✓ VERIFIED | `registry.py:92-105`; `app.py:230-268` (`action_show_history`; `action_show_results` with latest-COMPLETED + honest notify + history redirect); `app.py:141-146` SCREENS mounts `"history": HistoryScreen`, `"results": ResultsScreen`; tests `test_view_results_command_selects_latest_completed`, `test_view_results_command_no_completed_runs_redirects_to_history` passing |
| 22 | `.gitignore` behavior validated via actual `git check-ignore` subprocess in automated tests | ✓ VERIFIED | `tests/test_manet_workspace_pruning.py::test_git_check_ignore_workspace:171` (passing in green suite); independently re-executed live `git check-ignore -v` this session — matches (SC4) |
| 23 | `test_manet_never_imports_business_packages` passes unweakened with zero forbidden business imports (D-05) | ✓ VERIFIED | `tests/test_manet_import_boundaries.py:32-58` AST-walks `manet/**/*.py` all files incl. pool new screen/widget modules (rglob, no allowlist holes); passed 4/4 in this verification's suite run; grep confirms results/history/prune_modal/main_workspace/live_run/app contain no `simulator|attacks|feature_extraction|ml` imports; metrics enter via `bootstrap.py` composition root only |

**Score: 27/27 truths verified**

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `manet/adapters/workspace.py` | Manifest/hash/verify/prune engine | ✓ VERIFIED | 555 lines, substantive; all class methods wired via staticmethod exports + module funcs |
| `manet/widgets/qos_scorecard.py` | Academic QoS widget | ✓ VERIFIED | Substantive; consumed by ResultsScreen compose (results.py:215) |
| `manet/screens/results.py` | Split-pane results inspector | ✓ VERIFIED | 383 lines, worker + 3 tabs; pushed by history/live-run/app |
| `manet/screens/history.py` | Session history browser | ✓ VERIFIED | 393 lines; pushed by main_workspace/app; owns prune workflow |
| `manet/screens/prune_modal.py` | Boolean confirmation modal | ✓ VERIFIED | Presentation-only `ModalScreen[bool]`; consumed by history.py:20 |
| `manet/screens/__init__.py` | Exports | ✓ VERIFIED | Exports ResultsScreen, HistoryScreen, PruneConfirmationModal (Lines 7,10-11,17,20-21) |
| `manet/screens/main_workspace.py` | Dashboard nav updates | ✓ VERIFIED | Row/[R]→history, resume refresh |
| `manet/screens/live_run.py` | [V] View Results | ✓ VERIFIED | Binding + button on COMPLETED + action_view_results |
| `manet/runtime/keymap.py` | Shortcut keys/hints | ✓ VERIFIED | `BINDING_VIEW_RESULTS="v"` (Line 19), hint "Session history and past experiments" (Line 27) |
| `manet/commands/registry.py` | Palette commands | ✓ VERIFIED | `view:history` (93), `view:results` (100) |
| `manet/app.py` | App wiring | ✓ VERIFIED | SCREENS + action_show_history/action_show_results/action_results |
| `.gitignore` | Workspace isolation | ✓ VERIFIED | Line 4; semantics preserved (git check-ignore verified) |
| `tests/test_manet_manifest_artifacts.py` | TUI-20 coverage | ✓ VERIFIED | 10 tests, all passing |
| `tests/test_manet_workspace_pruning.py` | TUI-21 backend coverage | ✓ VERIFIED | 11 tests: 8 passed, 3 symlink skip (env), incl. git check-ignore + modal tests |
| `tests/test_manet_results_screen.py` | TUI-19 coverage | ✓ VERIFIED | 13 tests, all passing |
| `tests/test_manet_history_screen.py` | TUI-21 history/navigation coverage | ✓ VERIFIED | 11 tests, all passing |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `simulate` run completion (`bootstrap.py`) | `simulator.metrics.compute_metrics` | Direct import in composition root | WIRED | bootstrap.py:160 returns real metrics dict |
| ConcreteSimulationExecutor | manifest.json | `supervisor.py` → `update_manifest_status(metrics=...)` on COMPLETED/INTERRUPTED/FAILED | WIRED | supervisor.py:152-237 |
| ResultsScreen | QosScorecard | compose top pane with manifest metrics | WIRED | results.py:213-215 |
| ResultsScreen | WorkspaceAdapter.verify_artifact_checksums | `@work(thread=True)` worker → `call_from_thread(_apply_verification_results)` | WIRED | results.py:283-304, 356-364 |
| ResultsScreen | isolation_log.json/csv | stdlib csv/json parse, schema keys enforced | WIRED | results.py:126-147, 251-262 |
| HistoryScreen | WorkspaceAdapter list/preview/delete | `list_recent_experiments(limit=None)`, `preview_experiment_deletion`, `delete_experiment_run(expected_preview=...)` | WIRED | history.py:140, 354-386 |
| PruneConfirmationModal | HistoryScreen | `push_screen(modal, callback=...)` boolean contract | WIRED | history.py:361-364 |
| MainWorkspace row/[R] | HistoryScreen | RowSelected handler + `action_results` push "history" | WIRED | main_workspace.py:293-301, 311-321 |
| HistoryScreen Enter | ResultsScreen | RowSelected → `push_screen(ResultsScreen(experiment_id=...))` | WIRED | history.py:313-343 |
| LiveRunScreen [V] | ResultsScreen (actual run) | `sup.current_request.experiment_id` | WIRED | live_run.py:355-365 |
| Registry `view:history`/`view:results` | app actions | action="action_show_history"/"action_show_results" | WIRED | registry.py:92-105; app.py:230-268 |
| keymap `BINDING_VIEW_RESULTS` | LiveRunScreen binding | imported & bound | WIRED | keymap.py:19 → live_run.py:29,54 |
| .gitignore | git untracked-state | `check-ignore` semantic preservation | WIRED | verified live + in-suite test |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| QosScorecard | `metrics` | manifest.json["metrics"] ← supervisor ← `compute_metrics(runner.trace_rows)` on real trace rows | Yes — real simulator output | ✓ FLOWING |
| ResultsScreen integrity badges | `_artifact_results` | `verify_artifact_checksums()` recomputes live from file bytes on disk | Yes | ✓ FLOWING |
| ResultsScreen security table | rows | isolation_log.json/csv read at open time | Yes (empty state honest when none) | ✓ FLOWING |
| HistoryScreen table | `_all_runs` | WorkspaceAdapter reading manifest.json files from disk | Yes | ✓ FLOWING |
| PruneConfirmationModal | preview | `preview_experiment_deletion` enumerating real files/sizes | Yes | ✓ FLOWING |
| No-ID fallback | completed run | `list_recent_experiments(limit=None)` — redirects honestly when none exist (no fabricated results) | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase test suites + AST boundaries | `python -m pytest -q tests/test_manet_import_boundaries.py tests/test_manet_results_screen.py tests/test_manet_history_screen.py tests/test_manet_manifest_artifacts.py tests/test_manet_workspace_pruning.py` | 46 passed, 3 skipped (Windows symlink privs) in 19.2s | ✓ PASS |
| Prior-phase regression (contract-aligned) | `python -m pytest -q tests/test_manet_navigation.py tests/test_manet_dashboard_workspace.py` | 32 passed in 22.9s | ✓ PASS |
| Manifest engine end-to-end drive (22 assertions): COMPLETED manifest fields (status/started_at/completed_at/software_version/configuration/tag), sha256 hex64 + canonical relative_path, CSV header-excluded rows, JSON list-length rows, no tmp residue, VERIFIED→CORRUPTED→MISSING, `../` → SECURITY_VIOLATION, limit=None browsing with tag round-trip (pdr 0.83), fingerprint preview, same-size-modification stale rejection, deleted dir reclaim, traversal (`../../scenarios`) and workspace-root (`.`) rejection | temp-dir python driver against real `manet.adapters.workspace` | ALL PASS | ✓ PASS |
| Git isolation semantics | `git check-ignore -v .manet-workspace/.../trace.csv manifest.json traces/x.csv data/x.bin results/x.txt results/plots/a.png` | workspace paths ignored via `.gitignore:4`; traces/, data/, results/* still ignored; results/plots NOT ignored | ✓ PASS |
| Live-run UI / real-terminal visuals | — | — | ? HUMAN (Step 8) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| TUI-19 | 11-02 (also SC1) | View completed-run results: actual PDR/throughput/delay/overhead + packet counts + trace location | ✓ SATISFIED | SC1 + Truths 9–12; QosScorecard + ResultsScreen |
| TUI-20 | 11-01, 11-02 | Manifest (ID, config, seed, software version, status, timestamps, logs, trace paths, metrics) atomic + SHA-256 | ✓ SATISFIED | SC2 + Truths 5–7; spot-check proves fields & atomicity |
| TUI-21 | 11-01, 11-03 | History browse + open past result; read-only metadata; reruns create new runs; gitignore; cleanup needs preview + confirmation | ✓ SATISFIED | SC3 + SC4 + Truths 8, 16–22 |
| D-05 | 11-02, 11-03 (context decision — orchestrator-listed; NOT a REQUIREMENTS.md ID, no traceability row exists) | Preserve package isolation invariants: AST test unweakened; metrics via bootstrap.py composition root; screens read manifest only | ✓ SATISFIED | Truth 23; AST test covers whole `manet/**/*.py` and passes unweakened |

Orphaned requirements check: REQUIREMENTS.md maps exactly TUI-19, TUI-20, TUI-21 to Phase 11 (Lines 88-90); all three are claimed by plan frontmatter (11-01: TUI-20/21; 11-02: TUI-19/20; 11-03: TUI-21). **No orphaned requirements.** Note: REQUIREMENTS.md still shows TUI-19/20/21 as `[ ]` *Pending* in checkbox/traceability — updating those checkboxes is the orchestrator's post-verification bookkeeping (as done for Phases 7–10), not part of this code verification.

### Task Commit Verification

| Summary claim | Status |
| ------------- | ------ |
| 11-01: b49dcbb, 4bea3df, f433ab4, a564c93 | ✓ all exist (`git cat-file -t` → commit) |
| 11-02: 5cc03b0, d642773 | ✓ exist |
| 11-03: 8ac47c1, 7a8d02a, 91aa237 | ✓ exist |
| Post-plan fix: 49c4081 merged via 9fee649 | Inspected: touches only `tests/test_manet_navigation.py` + `tests/test_manet_dashboard_workspace.py`; replaces the Phase-10 "results notice" stub expectation with the real D-02 contract (r → HistoryScreen) with *strengthened* behavioral assertions and an Esc-return check — contract alignment, not weakening |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | TODO/FIXME/HACK/not-implemented scan over all manet sources, plus generic scan across phase files | ℹ️ Info | Only matches are Textual `Input(placeholder=...)` UI hints (history.py:113) — not stubs |
| manet/adapters/workspace.py | 176-177 | SC2 "logs" manifest field is represented by `error_details` (supervisor error/log excerpt) only; no general run-log is persisted for COMPLETED runs | ℹ️ Info | Consistent with Phase 10 bounded in-memory telemetry and Tab 3's "supervisor error/log excerpts if any" scoping; results screen renders the excerpt when present. Recorded as honest observation, not a must-have failure |

### Human Verification Required

### 1. Real-terminal visual inspection of ResultsScreen & QoS Scorecard
**Test:** Launch the TUI in a live terminal, complete a simulation, and open results (via [V] or view:results).
**Expected:** SOC color badges render as designed (#3fb950/#d29922/#f85149), split-pane proportions hold, tabs are navigable and badges transition VERIFYING → VERIFIED.
**Why human:** Color/typographic rendering and terminal font fallbacks are not observable in Pilot DOM tests.

### 2. Live keyboard navigation loop
**Test:** Walk: MainWorkspace [R] → History; Enter → Results; Esc back; from LiveRunScreen after completion press [V]; type in the history search box and confirm shortcut suppression while typing.
**Expected:** Every shortcut lands on the intended screen, no screen stacking, no shortcut leakage while the search Input is focused.
**Why human:** Focus-order and real keyboard-event behavior in actual terminals can diverge from Pilot-simulated presses.

### 3. Prune confirmation UX in a live terminal
**Test:** [D] a real completed run, review the itemized preview, press Enter to confirm; repeat on another run and press Esc instead.
**Expected:** Confirm deletes with "Experiment Deleted" notification and refreshed table; cancel leaves everything untouched.
**Why human:** Destructive-action confirmation is interactive and needs a real gesture flow; the plumbing is proven but the gesture is not.

### 4. Windows file-lock contention
**Test:** Open a run's trace.csv in Excel (or another Windows handle holder), then [D]-delete that run and confirm.
**Expected:** HistoryScreen stays active, table intact, and the actionable "files are locked by another Windows process" error notification appears.
**Why human:** Real OS handle contention cannot be reproduced faithfully by monkeypatched unit tests.

### Gaps Summary

No gaps. All 27 merged must-have truths are verified in the codebase at HEAD 9fee649; all 16 artifacts exist, are substantive, and are wired; all 13 key links are connected; the data path runs from the real `simulator.metrics.compute_metrics` in the composition root through the supervisor into manifest.json and out through the results/history/pruning UI; all 46 phase tests and the aligned prior-phase regression pass; all 9 recorded task commits exist. The 3 skipped tests are Windows-environment symlink-privilege skips whose guards were verified by direct code read, and the underlying behavior is exercised by the environment-independent traversal/root rejection checks which passed live.

Status is **human_needed** solely because 4 items (visual rendering, live keyboard flow, destructive gesture UX, real-OS lock contention) are only satisfiable by a human in a running terminal — the automated contract is fully met.

---

_Verified: 2026-11-10T04:45:04Z_
_Verifier: OpenCode (gsd-verifier)_
