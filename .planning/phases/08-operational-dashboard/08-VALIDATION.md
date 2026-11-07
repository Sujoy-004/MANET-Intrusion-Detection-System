---
phase: "08"
slug: "operational-dashboard"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-07"
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 with pytest-asyncio 1.3.0 |
| **Config file** | `pytest.ini` (`asyncio_mode = auto`) |
| **Quick run command** | `python -m pytest -k "manet"` |
| **Full suite command** | `python -m pytest` |
| **Estimated runtime** | ~10 seconds quick, ~137 seconds full suite |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest -k "manet"`
- **After every plan wave:** Run `python -m pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 0 | TUI-06, TUI-08 | T-08-01 / — | Test stubs created without runtime failures | unit / test stub | `python -m pytest tests/test_manet_diagnostics_probe.py tests/test_manet_adapters.py -q` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | TUI-06, TUI-08 | T-08-03 | Inspects presence/stat without full memory loads or lock retention | unit | `python -m pytest tests/test_manet_diagnostics_probe.py -k "test_diagnostics_report"` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 1 | TUI-08 | T-08-04 | Grayhole F1 0.0 reported as ineffective; missing artifacts report exact remediation | unit | `python -m pytest tests/test_manet_diagnostics_probe.py -k "test_missing_artifacts or test_grayhole_ineffective"` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 1 | TUI-07 | T-08-02 | Decoupled adapter interfaces under `manet/adapters/` with zero business logic imports | unit / AST | `python -m pytest tests/test_manet_adapters.py tests/test_manet_import_boundaries.py` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 2 | TUI-06, TUI-07 | T-08-04 | Executive Grid cards render honest capability states, escaping markup strings | pilot | `python -m pytest tests/test_manet_dashboard_workspace.py -k "test_dashboard_mount"` | ❌ W0 | ⬜ pending |
| 08-02-03 | 02 | 2 | TUI-07 | T-08-02 | Lower body shows CTA Hero Panel on empty workspace and Recent Experiments when runs exist | pilot | `python -m pytest tests/test_manet_dashboard_workspace.py -k "test_dashboard_empty_and_populated"` | ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 3 | TUI-07, DELV-01 | T-08-01 | Quick action keys `[S]`, `[R]`, `[O]`, `[P]`, `[F1]` navigate/notify and compact mode retains `#workspace-box` | pilot / regression | `python -m pytest tests/test_manet_dashboard_workspace.py tests/test_manet_compact.py -q` | ❌ W0 | ⬜ pending |
| 08-03-02 | 03 | 3 | DELV-01 | T-08-01 | Full test suite passes unweakened (baseline 122 + all new tests green) | full suite | `python -m pytest` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_manet_diagnostics_probe.py` — unit tests for `DiagnosticsProbe` covering present, missing, and partial artifact states
- [ ] `tests/test_manet_adapters.py` — unit tests for `StatusAdapter`, `NotificationAdapter`, `NavigationAdapter`, and `WorkspaceAdapter`
- [ ] `tests/test_manet_dashboard_workspace.py` — headless pilot tests for `MainWorkspace` composing executive grid, mounting rails, and responding to shortcuts

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual balance and reflow down to 80x24 | TUI-07 | Subjective readability and visual hierarchy verification across different physical terminal window resizes | Launch `python -m manet` in an 80x24 terminal and verify cards reflow cleanly into a vertical stream without clipping or visual corruption |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending 2026-11-07
