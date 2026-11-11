---
phase: "10"
slug: "background-execution-live-feedback"
status: complete
nyquist_compliant: true
wave_0_complete: true
created: "2026-11-08"
last_validated: "2026-11-09"
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pytest.ini` (`asyncio_mode = auto`) |
| **Quick run command** | `python -m pytest tests/test_manet_supervisor_lifecycle.py tests/test_manet_telemetry_bounded.py -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Observed runtime** | ~3.0 seconds (quick) / ~308 seconds (full suite: 239 passed) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_manet_supervisor_lifecycle.py tests/test_manet_telemetry_bounded.py -q`
- **After every plan wave:** Run `python -m pytest tests/`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | TUI-17 | T-10-01 | Stepping loop advances virtual time cleanly to duration across seeds 1, 42, 99; routes NODE_STATUS telemetry; flushes partial traces on failure | integration / regression | `python -m pytest tests/test_manet_stepping_equivalence.py -k "test_stepping_equivalence_preset_matrix"` | ✅ | ✅ green (9 passed) |
| 10-01-02 | 01 | 1 | TUI-15, TUI-18 | T-10-03 | WorkloadSupervisor manages single-workload capacity, fail-fast missing executor guard, worker spawn recovery, and atomic manifest updates | integration | `python -m pytest tests/test_manet_supervisor_lifecycle.py -k "test_single_active_workload_capacity"` | ✅ | ✅ green (11 passed) |
| 10-01-03 | 01 | 1 | TUI-16 | T-10-02 | Synchronized bounded ring-buffer drops overflow without blocking simulator; preserves authentic counters across evictions | unit / stress | `python -m pytest tests/test_manet_telemetry_bounded.py -k "test_bounded_telemetry_under_burst"` | ✅ | ✅ green (4 passed) |
| 10-02-01 | 02 | 2 | TUI-15, TUI-16 | T-10-04 | LiveRunScreen mounts telemetry ring-buffer draining, virtual progress bounded in [0.0, 100.0]%, disabled pause button, and authentic counters | async pilot | `python -m pytest tests/test_manet_live_run_screen.py -k "test_authentic_stages_and_progress"` | ✅ | ✅ green (7 passed) |
| 10-02-02 | 02 | 2 | TUI-15, TUI-16, TUI-18 | T-10-05 | Stop button halts run, preserves partial traces, and drains remaining queued events to RichLog before stopping timer | async pilot | `python -m pytest tests/test_manet_live_run_screen.py -q` | ✅ | ✅ green (7 passed) |
| 10-03-01 | 03 | 3 | TUI-15, TUI-17, TUI-18 | T-10-07 | Wizard launch transitions to LiveRunScreen; non-blocking shutdown sequence halts worker cleanly or surfaces error modal | async pilot | `python -m pytest tests/test_manet_live_run_screen.py -k "test_background_navigation_preserves_run"` | ✅ | ✅ green (7 passed) |
| 10-03-02 | 03 | 3 | TUI-15, TUI-16 | — | ActiveWorkloadCard and StatusBar render authentic supervisor states (including COMPLETED with metrics), shortcuts [L] and commands | async pilot | `python -m pytest tests/test_manet_navigation.py -k "test_live_run_shortcut or test_command_registry or test_simulation_shortcut"` | ✅ | ✅ green (24 passed) |
| 10-03-03 | 03 | 3 | DELV-01 | T-10-06 | Full regression suite and bidirectional AST import boundary assertions (zero business imports in manet, zero manet imports in business packages) | regression | `python -m pytest tests/test_manet_import_boundaries.py tests/test_manet_stepping_equivalence.py tests/test_manet_supervisor_lifecycle.py tests/test_manet_telemetry_bounded.py tests/test_manet_live_run_screen.py -q` | ✅ | ✅ green (43 passed) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_manet_stepping_equivalence.py` — stepping runner equivalence across seeds 1, 42, 99; NODE_STATUS live telemetry propagation; partial trace/isolation log survival on simulated exception (TUI-17).
- [x] `tests/test_manet_supervisor_lifecycle.py` — workload capacity, missing executor fail-fast guard, worker spawn failure recovery, terminal state precedence (FAILED > INTERRUPTED > COMPLETED), and atomic manifest transitions (TUI-15, TUI-18).
- [x] `tests/test_manet_telemetry_bounded.py` — bounded ring-buffer (maxlen=500), drop-oldest eviction, atomic counter integrity, and multi-threaded lock safety (TUI-16).
- [x] `tests/test_manet_live_run_screen.py` — Textual pilot tests for `LiveRunScreen` virtual-time progress bounding [0.0, 100.0]%, terminal event queue flushing, disabled pause button, stop cancellation, and screen reconnection (TUI-15, TUI-16, TUI-18).
- [x] Update `tests/test_manet_navigation.py` — add pilot tests for non-blocking graceful shutdown, quit modal confirmation, finalization error modal, `[L]` shortcut, and COMPLETED card rendering (TUI-15, TUI-17, TUI-18).
- [x] Update `tests/test_manet_import_boundaries.py` — assert `test_business_packages_never_import_manet()` and `test_bootstrap_is_at_project_root()` (DELV-01).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Status |
|----------|-------------|------------|-------------------|--------|
| High-speed stream visual fluidity | TUI-16 | Visual observation of RichLog rendering smoothness at 20Hz | Run 50-node simulation in TUI, observe live log feed and progress bar update without flickering or frame stuttering. | ⬜ pending manual execution |
| Global exit confirmation dialog | TUI-18 | Keyboard shortcut intercept verification under running workload | Press `Ctrl+Q` while simulation is active, verify confirmation prompt appears before interrupting run. | ⬜ pending manual execution |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** verified with automated test suites (239 tests green across 16 test modules)
