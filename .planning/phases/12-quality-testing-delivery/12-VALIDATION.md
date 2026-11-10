---
phase: "12"
slug: "quality-testing-delivery"
status: draft
nyquist_compliant: true
wave_0_complete: false
created: "2026-11-10"
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pytest.ini` (`asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function`) |
| **Quick run command** | `python -m pytest tests/test_legacy_cli_compat.py tests/test_manet_import_boundaries.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~5 seconds quick / ~400 seconds full suite |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_legacy_cli_compat.py tests/test_manet_import_boundaries.py -q`
- **After every plan wave:** Run `python -m pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green (285+ collected, zero failures, 3 expected symlink skips on Windows)
- **Max feedback latency:** 5 seconds (quick) / 450 seconds (full suite)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | DELV-01 | T-12-01 | Tests execute in hermetic tmp_path without mutating workspace | unit | `python -m pytest tests/test_manet_dashboard_workspace.py -q` | ❌ W0 | ⬜ pending |
| 12-01-02 | 01 | 1 | DELV-01 | T-12-02 | Legacy simulator & ML CLI commands execute with exit code 0 and valid schema | integration | `python -m pytest tests/test_legacy_cli_compat.py -q` | ❌ W0 | ⬜ pending |
| 12-02-01 | 02 | 2 | DELV-01 | T-12-03 | Pinned dependencies installed and verified without drift | operational | `python scripts/verify_environment.py` | ❌ W0 | ⬜ pending |
| 12-02-02 | 02 | 2 | DELV-01 | T-12-04 | AST boundaries assert presentation layer never imports business logic | static | `python -m pytest tests/test_manet_import_boundaries.py tests/test_import_boundaries.py -q` | ✅ | ⬜ pending |
| 12-02-03 | 02 | 2 | DELV-03 | — | Complete unweakened test suite passes on host | audit | `python -m pytest -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — autouse fixture isolating `.manet-workspace` for all tests
- [ ] `tests/test_legacy_cli_compat.py` — subprocess regression suite for `simulator.run_scenario`, `ml.train`, `ml.evaluate`, `scripts/*`
- [ ] `requirements.txt` — root pinned package manifest
- [ ] `scripts/verify_environment.py` — standalone environment verification script

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | — | — | All phase behaviors have automated verification. |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s quick
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-11-10
