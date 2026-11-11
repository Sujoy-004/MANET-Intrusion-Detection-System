---
phase: "11"
slug: "results-experiment-records"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-11-09"
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pytest.ini` |
| **Quick run command** | `python -m pytest tests/test_manet_manifest_artifacts.py tests/test_manet_workspace_pruning.py tests/test_manet_results_screen.py tests/test_manet_history_screen.py -v` |
| **Boundary test command** | `python -m pytest tests/test_manet_import_boundaries.py -v` |
| **Wave suite command** | `python -m pytest tests/test_manet_results_screen.py tests/test_manet_history_screen.py tests/test_manet_manifest_artifacts.py tests/test_manet_workspace_pruning.py -v` |
| **Full manet suite command** | `python -m pytest (Get-ChildItem tests/test_manet_*.py) -q` |
| **Full repository regression gate** | `python -m pytest tests/ -q` |
| **Measured runtimes** | Boundary ~0.5s · Quick ~5s · Wave ~10s · Full manet ~135s (2m 15s) · Full repo ~506s (8m 26s) |

---

## Sampling Rate

- **After every task commit:** Run focused task test command (latency ~2-5 seconds).
- **After every plan wave:** Run Wave suite command and Boundary test command (latency ~10 seconds).
- **Before phase completion:** Run Full manet suite and Full repository regression gate.
- **Max feedback latency:** ~15 seconds for per-task and wave feedback.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | TUI-20 | T-11-01 | Atomic manifest writing via tmp+replace; chunked 64KB SHA-256 calculation; tag recording in manifest | unit | `python -m pytest tests/test_manet_manifest_artifacts.py -k "test_tracer_manifest_hash_and_verify" -v` | ✅ | ✅ green |
| 11-01-02 | 01 | 1 | TUI-20 | T-11-02 | Checksum tamper detection (VERIFIED, CORRUPTED, MISSING, RECORDED); CSV header exclusion & JSON count semantics; atomic write failure resilience; partial failed runs; tag round-tripping | unit | `python -m pytest tests/test_manet_manifest_artifacts.py -k "test_artifact_tamper_detection or test_csv_and_json_row_count_semantics or test_atomic_write_failure_resilience or test_failed_and_interrupted_run_partial_artifacts or test_manifest_tag_recording_and_summary_parsing or test_tag_extraction_with_underscored_scenario_name" -v` | ✅ | ✅ green |
| 11-01-03 | 01 | 1 | TUI-21 | T-11-03 | Path traversal protection, recursive enumeration, symlink rejection, cryptographic revalidation detecting same-size modifications, and Windows lock handling | unit | `python -m pytest tests/test_manet_workspace_pruning.py -k "test_delete_experiment_run_safety or test_preview_deletion_recursive_enumeration or test_stale_preview_rejection or test_same_size_file_modification_detection or test_symlinked_directory_rejection or test_internal_symlinked_directory_rejection or test_symlinked_file_rejection" -v` | ✅ | ✅ green |
| 11-02-01 | 02 | 2 | TUI-19 | T-11-04 | QosScorecard validates metric types, formats canonical packet_loss_ratio, displays N/A for NaN/inf/None, and renders partial run metrics | unit | `python -m pytest tests/test_manet_results_screen.py -k "test_qos_scorecard_valid_metrics or test_qos_scorecard_nan_inf_missing_metrics or test_qos_scorecard_packet_loss_ratio_canonical or test_qos_scorecard_partial_run_display" -v` | ✅ | ✅ green |
| 11-02-02 | 02 | 2 | TUI-19, TUI-20 | T-11-05 | ResultsScreen mounts split-pane tabs; background synchronous thread worker verifies hashes without UI freeze; stale results discarded on dismiss; distinguishes IDS-disabled from 0 isolates; latest completed run fallback | integration | `python -m pytest tests/test_manet_results_screen.py -k "test_results_screen_background_worker_thread_safety or test_results_screen_background_verification_states or test_results_screen_stale_worker_discarded_on_dismiss or test_results_screen_unmount_does_not_cancel_unrelated_workers or test_results_screen_ids_empty_states_distinction or test_results_screen_isolation_log_schema or test_results_screen_no_id_fallback_selects_latest_completed" -v` | ✅ | ✅ green |
| 11-03-01 | 03 | 3 | TUI-21 | T-11-07 | .gitignore isolates .manet-workspace/ (verified via git check-ignore); PruneConfirmationModal itemizes files and total bytes returning boolean confirmation | integration | `python -m pytest tests/test_manet_workspace_pruning.py -k "test_git_check_ignore_workspace or test_prune_confirmation_modal_preview_composition" -v` | ✅ | ✅ green |
| 11-03-02 | 03 | 3 | TUI-21 | T-11-06 | HistoryScreen browses all runs via list_recent_experiments(limit=None), supports column sorting, filters by scenario/tag/status, and owns pruning execution and error notifications | integration | `python -m pytest tests/test_manet_history_screen.py -k "test_history_screen_browses_all_runs or test_history_screen_sortable_columns or test_history_screen_scenario_tag_search or test_history_screen_pruning_workflow_success_and_cancellation or test_history_screen_pruning_error_notification" -v` | ✅ | ✅ green |
| 11-03-03 | 03 | 3 | TUI-21, D-05 | T-11-08 | Dashboard row selection/Enter opens History; [R] opens History; [V] in LiveRun opens completed Results; view:results handles missing ID safely by selecting latest completed run; AST test passes unweakened | architectural / integration | `python -m pytest tests/test_manet_import_boundaries.py -v; python -m pytest tests/test_manet_history_screen.py -k "test_dashboard_enter_opens_history or test_live_run_v_opens_actual_results or test_view_results_command_selects_latest_completed" -v` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_manet_manifest_artifacts.py` — stubs for TUI-20 (atomic manifest update, chunked SHA-256 computation, tamper detection, CSV header exclusion, atomic write failure test, partial failed runs, tag round-tripping)
- [x] `tests/test_manet_workspace_pruning.py` — stubs for TUI-21 (recursive prune preview, same-size modification detection, symlink rejection, modal confirmation, deletion safety, git check-ignore test)
- [x] `tests/test_manet_results_screen.py` — stubs for TUI-19 (QoS scorecard with NaN/inf handling, canonical packet loss ratio, background thread checksum worker states, stale worker discard, IDS empty state distinction, latest completed run fallback)
- [x] `tests/test_manet_history_screen.py` — stubs for TUI-21 (complete history table without truncation, column sorting, search/filter, row selection navigation, dashboard Enter delegation, deletion ownership & error handling)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual aesthetic of academic QoS scorecard | TUI-19 | Color contrast and layout appeal | Run TUI, open Results screen, verify scorecard visual hierarchy and responsiveness |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s for unit/wave tests
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated via post-execution Nyquist audit (2026-11-09) — all 8 task rows covered by automated tests (per-task `-k` filters matched real passing tests); 1 manual-only row remains (visual aesthetic of QoS scorecard)

## Validation Audit 2026-11-09

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
