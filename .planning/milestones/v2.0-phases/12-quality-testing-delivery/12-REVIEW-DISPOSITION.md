---
phase: 12
review: 12-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "Path-anchoring test depends on a gitignored, untracked model artifact — fails on a fresh checkout"
  - id: WR-01
    severity: warning
    disposition: open
    title: "`importlib.metadata.version()` is outside the `try`, so a missing distribution aborts the whole gate"
  - id: WR-02
    severity: warning
    disposition: open
    title: "The pin table is hardcoded and duplicates `requirements.txt` — drift makes the gate enforce stale versions"
  - id: WR-03
    severity: warning
    disposition: open
    title: "The Python runtime check is unbounded (`>= 3.11`) but the pins do not support Python 3.13+"
  - id: WR-04
    severity: warning
    disposition: open
    title: "Wall-clock assertion on a subprocess is a flake vector"
  - id: IN-01
    severity: info
    disposition: open
    title: "Brittle hard-coded preset count"
  - id: IN-02
    severity: info
    disposition: open
    title: "Module docstring overstates hermeticity"
  - id: IN-03
    severity: info
    disposition: open
    title: "Gate 2 test docstring misdescribes the workload"
  - id: IN-04
    severity: info
    disposition: open
    title: "Magic-string dispatch and double glob in the artifact report"
  - id: IN-05
    severity: info
    disposition: open
    title: "`pytest` is pinned in the runtime manifest; no `requires-python` metadata"
  - id: IN-06
    severity: info
    disposition: open
    title: "Hermetic isolation does not cover the direct `.manet-workspace` fallback in `StepReviewWidget`"
open: 11
total: 11
recorded: 2026-11-11T05:39:14.899Z
---

# Phase 12: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
