---
phase: "10"
slug: "background-execution-live-feedback"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-08"
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
| **Full suite command** | `python -m pytest tests/` |
| **Estimated runtime** | ~15 seconds (quick) / ~35 seconds (full) |

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
| 10-01-01 | 01 | 1 | TUI-17 | T-10-01 | Discrete-event stepping loop advances virtual time deterministically to duration | integration | `python -m pytest tests/test_manet_stepping_equivalence.py -k "test_stepping_equivalence_preset_matrix"` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | TUI-16 | T-10-02 | Synchronized bounded ring-buffer drops overflow without blocking simulator | unit / stress | `python -m pytest tests/test_manet_telemetry_bounded.py -k "test_bounded_telemetry_under_burst"` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 1 | TUI-15, TUI-18 | T-10-03 | WorkloadSupervisor manages single-workload capacity, stop token, and atomic manifest updates | integration | `python -m pytest tests/test_manet_supervisor_lifecycle.py -k "test_single_active_workload_capacity"` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 2 | TUI-15, TUI-16 | T-10-04 | LiveRunScreen mounts telemetry ring-buffer draining, progress bars, and stage labels | async pilot | `python -m pytest tests/test_manet_live_run_screen.py -k "test_authentic_stages_and_progress"` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 2 | TUI-18 | T-10-05 | Stop button invokes supervisor cancel, preserves partial traces, and marks INTERRUPTED | async pilot | `python -m pytest tests/test_manet_supervisor_lifecycle.py -k "test_cancellation_preserves_partial_traces"` | ❌ W0 | ⬜ pending |
| 10-03-01 | 03 | 3 | TUI-15..18 | — | Wiring SimulationWorkflow launch to LiveRunScreen and global navigation | async pilot | `python -m pytest tests/test_manet_live_run_screen.py -k "test_background_navigation_preserves_run"` | ❌ W0 | ⬜ pending |
| 10-03-02 | 03 | 3 | DELV-01 | — | Full regression suite and import boundary assertions (no simulator in manet) | regression | `python -m pytest tests/test_manet_import_boundaries.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_manet_stepping_equivalence.py` — stepping runner equivalence and deterministic trace reproducibility (TUI-17)
- [ ] `tests/test_manet_telemetry_bounded.py` — bounded ring-buffer dropped-counter and thread-safe draining (TUI-16)
- [ ] `tests/test_manet_supervisor_lifecycle.py` — workload capacity, atomic manifest transitions, and cancellation (TUI-15, TUI-18)
- [ ] `tests/test_manet_live_run_screen.py` — Textual pilot tests for `LiveRunScreen` telemetry feed and stop confirmation (TUI-15, TUI-16, TUI-18)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| High-speed stream visual fluidity | TUI-16 | Visual observation of RichLog rendering smoothness at 10Hz | Run 50-node simulation in TUI, observe live log feed and progress bar update without flickering or frame stuttering. |
| Global exit confirmation dialog | TUI-18 | Keyboard shortcut intercept verification under running workload | Press `Ctrl+Q` while simulation is active, verify confirmation prompt appears before interrupting run. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
