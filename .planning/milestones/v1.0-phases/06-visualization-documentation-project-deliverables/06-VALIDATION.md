---
phase: "06"
slug: "visualization-documentation-project-deliverables"
status: draft
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-28"
---

# Phase 06 - Validation Strategy

> Per-phase validation contract for feedback sampling during visualization and documentation execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 (Python 3.11.8) |
| **Config file** | none (standard repo pytest discovery) |
| **Quick run command** | `python -m pytest tests/test_plots.py -v` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_plots.py -v`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | RESP-03 | - | Headless safe plotting | unit | `python -m pytest tests/test_plots.py -v` | ❌ W0 | ⏳ pending |
| 06-01-02 | 01 | 1 | RESP-03 | - | Deterministic plot generation | integration | `python .archify/scripts/generate_all_plots.py` | ❌ W0 | ⏳ pending |
| 06-02-01 | 02 | 1 | RESP-03 | - | Validated Archify visual schemas | integration | `node "C:\Users\KIIT0001\.agents\skills\archify\bin\archify.mjs" finalize architecture .archify/diagrams/architecture_candidate.json .archify/diagrams/system_architecture.html --quality showcase --json` | ❌ W0 | ⏳ pending |
| 06-02-02 | 02 | 1 | RESP-03 | - | Academic report provenance verification | integrity | `python -c "import os; assert os.path.exists('docs/FINAL_PROJECT_REPORT.md') and os.path.getsize('docs/FINAL_PROJECT_REPORT.md') > 10000; print('REPORT VERIFIED')"` | ❌ W0 | ⏳ pending |

---

## Wave 0 Requirements

- [ ] `tests/test_plots.py` - Unit test suite verifying plotting functions produce valid 300 DPI PNG image files without GUI dependencies.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual aesthetic and layout clarity | RESP-03 | Subjective styling check | Open `.archify/PLOTS_CATALOG.md` in browser/markdown viewer and verify legible fonts, distinct markers, and clear legends. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending 2026-10-28
