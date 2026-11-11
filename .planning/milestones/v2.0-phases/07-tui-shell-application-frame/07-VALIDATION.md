---
phase: "7"
slug: "tui-shell-application-frame"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-11-06"
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 + Textual 8.2.8 `run_test()` (all installed) |
| **Config file** | none today — Wave 0 adds root `pytest.ini` (`asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function`) |
| **Quick run command** | `python -m pytest tests/test_manet_*.py -q` |
| **Full suite command** | `python -m pytest tests/ -q` (79 baseline + new, all green) |
| **Estimated runtime** | ~30–60 seconds (headless Textual tests are fast) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_manet_*.py -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green + one documented manual launch of `python -m manet` on the Windows host (real-terminal behavior incl. at least one resize)
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| W0-pytest.ini | 01 | 0 | TUI-01 (enabler) | — | N/A | collect | `python -m pytest tests/ -q` (79 baseline unchanged) | ✅ | ✅ green |
| launch | 01 | 1 | TUI-01 | T-7-02 (honest capability) | Title `MANET IDS`, default screen mounted, theme set, no network | unit (async) | `python -m pytest tests/test_manet_app_launch.py -x` | ✅ | ✅ green |
| entry | 01 | 1 | TUI-01 | — | `manet/__main__.main` callable; package import has no side effects | unit (sync) | `python -m pytest tests/test_manet_entry.py -x` | ✅ | ✅ green |
| boundaries | 01 | 1 | TUI-02 | T-7-01/T-7-03 | `manet/` never imports business logic; no `subprocess`/`os.system`/`shutil` in `manet/commands/` | unit (AST, sync) | `python -m pytest tests/test_manet_import_boundaries.py -x` | ✅ | ✅ green |
| navigation | 01 | 1 | TUI-02 | — | Arrow focus / Enter activate / Esc return / Footer visible / focus styles | unit (async, Pilot) | `python -m pytest tests/test_manet_navigation.py -x` | ✅ | ✅ green |
| compact | 01 | 1 | TUI-02 | — | Compact breakpoint classes at small size, full at large | unit (async, run_test(size)) | `python -m pytest tests/test_manet_compact.py -x` | ✅ | ✅ green |
| palette | 01 | 1 | TUI-03 | T-7-03 | Provider yields registry commands only; fuzzy match works | unit (async) | `python -m pytest tests/test_manet_command_palette.py -x` | ✅ | ✅ green |
| registry | 01 | 1 | TUI-03 | T-7-01 | Console resolve() accepts known app commands only; unknown → suggestion, never execution | unit (mix) | `python -m pytest tests/test_manet_command_registry.py -x` | ✅ | ✅ green |
| theme | 01 | 1 | TUI-04 | T-7-04 | `manet-soc` defaults; high-contrast toggle; nothing persists (no file writes) | unit (async + AST) | `python -m pytest tests/test_manet_theme.py -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Root `pytest.ini` — `asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function` (verify the 79 existing tests still collect/pass unchanged after adding)
- [x] `tests/test_manet_app_launch.py` — covers TUI-01
- [x] `tests/test_manet_entry.py` — covers TUI-01
- [x] `tests/test_manet_import_boundaries.py` — covers TUI-02 (extends existing `tests/test_import_boundaries.py` AST pattern)
- [x] `tests/test_manet_navigation.py` + `tests/test_manet_compact.py` — covers TUI-02
- [x] `tests/test_manet_command_palette.py` + `tests/test_manet_command_registry.py` — covers TUI-03
- [x] `tests/test_manet_theme.py` — covers TUI-04
- [x] No framework install needed — textual 8.2.8 / pytest / pytest-asyncio all present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full-screen launch on a real terminal (`python -m manet`) | TUI-01 | pytest never spawns a real TTY (research Pitfall 6); Textual's alt-screen behavior is only meaningful in a live terminal | Launch from repo root on Windows Terminal; confirm full-screen frame, title, footer, shortcut hints |
| Layout remains usable after terminal resizing (incl. compact mode at small size) | TUI-02 | Live resize events are not reproducible via `run_test(size=)` alone — real resize gestures/winsize changes needed | Resize the terminal window from large to ~60×20 and back; confirm layout re-renders and compact classes engage |
| Visible keyboard focus + shortcut hints legibility, sober animation feel | TUI-02/TUI-04 | Visual quality judgments (SOC aesthetic, animation smoothness) are perception, not assertions | Walk all screens with keyboard only; confirm focus is always visible; confirm no decorative motion |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

## Validation Audit 2026-11-07

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
