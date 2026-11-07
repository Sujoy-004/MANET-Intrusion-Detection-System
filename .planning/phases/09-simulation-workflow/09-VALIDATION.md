---
phase: "09"
slug: "simulation-workflow"
status: ready
nyquist_compliant: true
wave_0_complete: false
created: "2026-11-07"
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pytest.ini` |
| **Quick run command** | `python -m pytest tests/test_manet_*.py -k "simulation or scenario or workspace"` |
| **Full suite command** | `python -m pytest` |
| **Estimated runtime** | ~15 seconds (quick) / ~30 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_manet_*.py -k "simulation or scenario or workspace"`
- **After every plan wave:** Run `python -m pytest`
- **Before `/gsd-verify-work`:** Full suite must be green (148+ tests passing)
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | TUI-09 | T-09-01 | Authentic scenario files loaded without code execution; schema validated | unit | `python -m pytest tests/test_manet_scenario_adapter.py -k "test_tracer_preset_discovery_and_schema"` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | TUI-10, TUI-11 | T-09-02 | Scalar bounds, distinct flow endpoints, and integer seed validated on blur | unit | `python -m pytest tests/test_manet_simulation_config.py -k "test_two_tier_validation_and_model_gate"` | ❌ W0 | ⬜ pending |
| 09-01-03 | 01 | 1 | TUI-13, TUI-14 | T-09-03 | User tag sanitized, path stays within `.manet-workspace/`, collision-free | unit | `python -m pytest tests/test_manet_workspace_allocation.py -k "test_workspace_allocation_and_manifest"` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 2 | TUI-09, TUI-10, TUI-11 | — | Wizard Step 1 & Step 2 UI render and update config state | async pilot | `python -m pytest tests/test_manet_simulation_workflow.py -k "test_wizard_steps"` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 2 | TUI-12 | T-09-04 | IDS toggle strictly disabled with guidance when champion model missing | async pilot | `python -m pytest tests/test_manet_simulation_workflow.py -k "test_ids_gating"` | ❌ W0 | ⬜ pending |
| 09-02-03 | 02 | 2 | TUI-13, TUI-14 | T-09-03 | Review step displays summary and confirmed launch generates initial manifest | async pilot | `python -m pytest tests/test_manet_simulation_workflow.py -k "test_review_confirmation"` | ❌ W0 | ⬜ pending |
| 09-03-01 | 03 | 3 | TUI-09..14 | — | Wire `[S]` shortcut and command palette to `SimulationWorkflowScreen` | async pilot | `python -m pytest tests/test_manet_navigation.py -k "test_simulation_shortcut"` | ✅ | ⬜ pending |
| 09-03-02 | 03 | 3 | DELV-01 | — | Full regression test suite and AST architectural import boundary verification | regression | `python -m pytest tests/test_manet_simulation_runner_compat.py tests/test_manet_import_boundaries.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_manet_scenario_adapter.py` — unit tests for authentic preset discovery and metadata extraction (TUI-09).
- [ ] `tests/test_manet_simulation_config.py` — unit tests for two-tier validation, field limits, and flow endpoint invariant checks (TUI-10, TUI-11).
- [ ] `tests/test_manet_workspace_allocation.py` — unit tests for deterministic naming, collision avoidance, and manifest generation (TUI-13, TUI-14).
- [ ] `tests/test_manet_simulation_workflow.py` — Textual pilot tests for wizard navigation, IDS gating, and pre-flight confirmation (TUI-09..TUI-14).
- [ ] Update `tests/test_manet_navigation.py` — adapt `test_simulation_shortcut_triggers_notice` to assert `SimulationWorkflowScreen` navigation instead of placeholder notice.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Compact terminal 80x24 reflow | TUI-03, TUI-09 | Visual check on small physical console window | Launch `python -m manet` in an 80x24 terminal, press `[S]`, cycle through wizard steps, verify no clipped text or awkward wrapping. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** verified 2026-11-07
