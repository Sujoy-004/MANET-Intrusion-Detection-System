---
phase: 09
review: 09-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "Duplicate `scenario_id` across scenario JSON files crashes wizard with `DuplicateKey`"
  - id: CR-02
    severity: critical
    disposition: open
    title: "`sanitize_run_tag` truncation re-introduces a Windows-illegal trailing dot"
  - id: WR-01
    severity: warning
    disposition: open
    title: "Wizard never resets state on re-entry - stale Step 3 config is re-confirmable"
  - id: WR-02
    severity: warning
    disposition: open
    title: "Unhandled `OSError`s during allocation/manifest write crash the whole TUI after confirm"
  - id: WR-03
    severity: warning
    disposition: open
    title: "No cross-field invariant for mobility speed ordering (min speed > max speed is accepted)"
  - id: WR-04
    severity: warning
    disposition: open
    title: "Preset mode silently mutates flows (endpoint rewrite + single-rate overwrite) without surfacing the change"
  - id: WR-05
    severity: warning
    disposition: open
    title: "Step 3 workspace preview ignores the injected `workspace_root` (hardcoded `.manet-workspace/`)"
  - id: IN-01
    severity: info
    disposition: open
    title: "Unused imports verified by pyflakes (dead code)"
  - id: IN-02
    severity: info
    disposition: open
    title: "Corrupt artifacts silently vanish with no signal (`except Exception: continue/pass`)"
  - id: IN-03
    severity: info
    disposition: open
    title: "Private API access `self.app._installed_screens`"
  - id: IN-04
    severity: info
    disposition: open
    title: "Command parameter machinery is untestable dead weight today"
  - id: IN-05
    severity: info
    disposition: open
    title: "Previewed directory name almost never matches the actual allocated name (timestamp churn)"
  - id: IN-06
    severity: info
    disposition: open
    title: "CWD-anchored defaults silently degrade when the TUI is not launched from repo root"
open: 13
total: 13
unparsed: 1
recorded: 2026-11-08T05:10:00Z
---

# Phase 09: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| CR-02 | critical | open | - |
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

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
