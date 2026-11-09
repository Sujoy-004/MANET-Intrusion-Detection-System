---
phase: "11"
slug: "results-experiment-records"
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| **Quick run command** | `python -m pytest tests/test_manet_results_screen.py tests/test_manet_history_screen.py tests/test_manet_manifest_artifacts.py tests/test_manet_workspace_pruning.py -v` |
| **Full suite command** | `python -m pytest tests/test_manet_*.py` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_manet_results_screen.py tests/test_manet_history_screen.py tests/test_manet_manifest_artifacts.py tests/test_manet_workspace_pruning.py tests/test_manet_import_boundaries.py`
- **After every plan wave:** Run `python -m pytest tests/test_manet_*.py`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | TUI-20 | T-11-01 | Atomic manifest writing via tmp+replace; chunked SHA-256 calculation | unit | `python -m pytest tests/test_manet_manifest_artifacts.py -v` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | TUI-20 | T-11-02 | Checksum tamper detection identifies VERIFIED, CORRUPTED, MISSING states | unit | `python -m pytest tests/test_manet_manifest_artifacts.py -k "test_artifact_tamper_detection" -v` | ❌ W0 | ⬜ pending |
| 11-01-03 | 01 | 1 | TUI-21 | T-11-03 | Path traversal protection and Windows handle release on run deletion | unit | `python -m pytest tests/test_manet_workspace_pruning.py -k "test_delete_experiment_run_safety" -v` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 2 | TUI-19 | T-11-04 | ResultsScreen renders QoS scorecard with authentic PDR, throughput, delay, overhead | integration | `python -m pytest tests/test_manet_results_screen.py -k "test_results_screen_scorecard" -v` | ❌ W0 | ⬜ pending |
| 11-02-02 | 02 | 2 | TUI-19 | T-11-05 | ResultsScreen renders detail tabs and honest empty state for disabled IDS | integration | `python -m pytest tests/test_manet_results_screen.py -k "test_results_screen_tabs_and_empty_state" -v` | ❌ W0 | ⬜ pending |
| 11-03-01 | 03 | 3 | TUI-21 | T-11-06 | HistoryScreen lists runs, supports search/status filtering, navigates on Enter | integration | `python -m pytest tests/test_manet_history_screen.py -v` | ❌ W0 | ⬜ pending |
| 11-03-02 | 03 | 3 | TUI-21 | T-11-07 | PruneConfirmationModal itemizes files and bytes before explicit Enter deletion | integration | `python -m pytest tests/test_manet_workspace_pruning.py -k "test_prune_confirmation_modal" -v` | ❌ W0 | ⬜ pending |
| 11-03-03 | 03 | 3 | TUI-21, D-05 | T-11-08 | .gitignore ignores .manet-workspace; zero business imports verified in new modules | architectural | `python -m pytest tests/test_manet_workspace_pruning.py -k "test_git_ignores_workspace" tests/test_manet_import_boundaries.py -v` | ❌ W0 / ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_manet_manifest_artifacts.py` — stubs for TUI-20 (atomic manifest update, SHA-256 computation, tamper detection)
- [ ] `tests/test_manet_workspace_pruning.py` — stubs for TUI-21 (prune preview, modal confirmation, deletion safety, gitignore check)
- [ ] `tests/test_manet_results_screen.py` — stubs for TUI-19 (QoS scorecard, tabs, empty states, missing metrics)
- [ ] `tests/test_manet_history_screen.py` — stubs for TUI-21 (history table, search, filter, row selection navigation)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual aesthetic of academic QoS scorecard | TUI-19 | Color contrast and layout appeal | Run TUI, open Results screen, verify scorecard visual hierarchy |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
