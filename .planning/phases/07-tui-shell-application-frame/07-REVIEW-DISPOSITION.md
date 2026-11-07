---
phase: 07
review: 07-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "User-triggerable application crash — raw user text interpolated into Rich markup on `markup=True` RichLog"
  - id: CR-02
    severity: critical
    disposition: open
    title: "D-03 \"option-a\" reversibility decision recorded as user-approved but the mounting contract was never built"
  - id: CR-03
    severity: critical
    disposition: open
    title: "D-20 honesty violation — console help copy advertises a nonexistent `help` command (self-referential dead end)"
  - id: WR-01
    severity: warning
    disposition: open
    title: "`motion-toggle` is an advertised capability with zero consumers (unobservable toggle)"
  - id: WR-02
    severity: warning
    disposition: open
    title: "`except Exception: return` silently swallows — violates the zero-exception-swallowing rule"
  - id: WR-03
    severity: warning
    disposition: open
    title: "Workspace focus CSS is dead and the default screen has no focusable content (D-08 gap)"
  - id: WR-04
    severity: warning
    disposition: open
    title: "Palette provider docstring records a recency handoff that its own completed plan never delivered"
  - id: WR-05
    severity: warning
    disposition: open
    title: "Console output colors bypass the SOC theme entirely (D-06 violation on the primary output surface)"
  - id: IN-01
    severity: info
    disposition: open
    title: "Version string duplicated as a hardcoded literal in the help screen"
  - id: IN-02
    severity: info
    disposition: open
    title: "Redundant CSS variable shadowing re-declared in three screens"
  - id: IN-03
    severity: info
    disposition: open
    title: "Dead session settings — `compact_density` and its `compact_mode` alias have zero consumers"
  - id: IN-04
    severity: info
    disposition: open
    title: "Registry API shape — redundant type union; latent kwargs contract unverified"
  - id: IN-05
    severity: info
    disposition: open
    title: "`manet/runtime/__init__.py` does not re-export the package's public surface"
  - id: IN-06
    severity: info
    disposition: open
    title: "Substring-based import guard is brittle and weaker than the AST gate it duplicates"
  - id: IN-07
    severity: info
    disposition: open
    title: "Inconsistent asyncio test markers (auto mode makes them redundant, style should be uniform)"
  - id: IN-08
    severity: info
    disposition: open
    title: "Input cleared before execution; on handler exceptions the typed command is already gone"
  - id: IN-09
    severity: info
    disposition: open
    title: "Shortcut copy drift — console footer shows two identical \"Close\" entries; help-table labels vs footer labels differ"
open: 17
total: 17
recorded: 2026-11-07T03:32:35.213Z
---

# Phase 07: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| CR-02 | critical | open | - |
| CR-03 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| WR-04 | warning | open | - |
| WR-05 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |
| IN-07 | info | open | - |
| IN-08 | info | open | - |
| IN-09 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
