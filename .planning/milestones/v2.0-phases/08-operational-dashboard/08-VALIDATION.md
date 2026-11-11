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
| 08-01-01 | 08-01 | 1 | TUI-06, TUI-08 | T-08-01 / — | Test stubs created and tracer card mounts without runtime failures | unit / pilot | `python -m pytest tests/test_manet_dashboard_workspace.py -k "test_tracer_diagnostic_card_mount" -q` | ❌ W0 | ⬜ pending |
| 08-01-02 | 08-01 | 1 | TUI-06, TUI-08 | T-08-02, T-08-03 | Zero-mock probe: `scikit-learn` distribution mapping, scenario JSON validation, dynamic metrics without 0.0 defaults, missing binary vs metadata, dataset remediation | unit | `python -m pytest tests/test_manet_diagnostics_probe.py -q` | ❌ W0 | ⬜ pending |
| 08-01-03 | 08-01 | 1 | TUI-07, DELV-01 | T-08-SC | Decoupled adapter interfaces, read-only workspace discovery, bounded notification queue (`maxlen=20`), AST import boundaries | unit / AST | `python -m pytest tests/test_manet_adapters.py tests/test_manet_import_boundaries.py -q` | ❌ W0 | ⬜ pending |
| 08-02-01 | 08-02 | 2 | TUI-06, TUI-08 | T-08-05 | Top status cards: SystemHealth, ComponentCapabilities with inline badges, ActiveWorkload distinguishing engine ready offline vs idle | pilot | `python -m pytest tests/test_manet_dashboard_workspace.py -k "test_cards_render or test_rails_render" -q` | ❌ W0 | ⬜ pending |
| 08-02-02 | 08-02 | 2 | TUI-07 | T-08-05 | Lower split-body: CtaHeroPanel communicates pending Phase 9 workflow without false launch claims, RecentExperimentsTable read-only | pilot | `python -m pytest tests/test_manet_dashboard_workspace.py -k "test_cta_hero or test_recent_experiments" -q` | ❌ W0 | ⬜ pending |
| 08-02-03 | 08-02 | 2 | TUI-06, TUI-07 | T-08-04 | Executive Grid layout responsive reflow down to 80x24 and non-blocking periodic background refresh | pilot / regression | `python -m pytest tests/test_manet_dashboard_workspace.py tests/test_manet_compact.py -q` | ❌ W0 | ⬜ pending |
| 08-03-01 | 08-03 | 3 | TUI-07 | T-08-06, T-08-07 | Dashboard quick action keys ([S], [R], [O], [P], [F1]), console typing isolation (S/R do not fire in input), repeated shortcut bounded queue safety | pilot / unit | `python -m pytest tests/test_manet_navigation.py -k "test_simulation_shortcut or test_results_shortcut or test_console or test_repeated_shortcut" -q` | ❌ W0 | ⬜ pending |
| 08-03-02 | 08-03 | 3 | DELV-01 | T-08-SC | Full test suite passes unweakened (baseline 122 + all new tests green) and AST import boundary checks | full suite | `python -m pytest` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_manet_diagnostics_probe.py` — unit tests for `DiagnosticsProbe` covering dependencies, scikit-learn distribution mapping, valid vs malformed scenario JSON presets, dataset stats, missing binary vs metadata, dynamic metrics, and Grayhole F1 0.0 badge
- [ ] `tests/test_manet_adapters.py` — unit tests for `StatusAdapter` (engine ready vs idle), `NotificationAdapter` (bounded in-memory queue), `NavigationAdapter`, and read-only `WorkspaceAdapter`
- [ ] `tests/test_manet_dashboard_workspace.py` — headless pilot tests for `MainWorkspace` composing executive grid, mounting rails, CtaHeroPanel pending workflow text, RecentExperimentsTable read-only population, and periodic background refresh

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
- [ ] `nyquist_compliant: true` set in frontmatter (updated upon Wave 0 completion in execute-phase)

**Approval:** pending 2026-11-07
