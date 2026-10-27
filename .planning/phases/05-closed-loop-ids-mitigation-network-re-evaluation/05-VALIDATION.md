---
phase: "05"
slug: "closed-loop-ids-mitigation-network-re-evaluation"
status: ready
nyquist_compliant: true
wave_0_complete: false
created: "2026-10-27"
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | none — native pytest discovery |
| **Quick run command** | `python -m pytest tests/test_closed_loop.py -v` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_closed_loop.py -v`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | RESP-01 | T-05-01 | RREPs from blacklisted nodes dropped & routes invalidated | unit | `python -m pytest tests/test_closed_loop.py -k "rrep or route" -v` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 2 | RESP-01 | T-05-02 | OnlineIDS accumulates 2 strikes, isolates node, respects 30s cooldown & endpoint guard | unit / integration | `python -m pytest tests/test_closed_loop.py -k "online_ids or strike or endpoint" -v` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 1 | RESP-02 | T-05-03 | Triad runner executes Baseline vs Attack vs AODV+IDS with positive PDR recovery | integration | `python -m pytest tests/test_closed_loop.py -k "recovery" -v` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | RESP-02 | T-05-04 | Full benchmark executes across seeds, exporting metrics CSV, markdown report, and isolation events | benchmark / e2e | `python scripts/run_closed_loop_benchmark.py --smoke` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_closed_loop.py` — comprehensive test suite covering unit routing hooks, OnlineIDS state transitions, and closed-loop triad recovery

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | N/A | N/A | All phase behaviors have automated verification. |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved
