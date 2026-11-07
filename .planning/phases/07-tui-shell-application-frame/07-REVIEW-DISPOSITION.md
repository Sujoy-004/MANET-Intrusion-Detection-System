---
phase: 07
review: 07-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "User-triggerable application crash — raw user text interpolated into Rich markup on `markup=True` RichLog"
    details: "Fixed in manet/screens/console.py by emitting unparsed Text objects directly into RichLog, preventing MarkupError on unmatched closing tags. Regression-tested via test_console_hostile_markup_input_does_not_crash."
  - id: CR-02
    severity: critical
    disposition: deferred
    title: "D-03 \"option-a\" reversibility decision recorded as user-approved but the mounting contract was never built"
    details: "Deferred to Phase 8: Mounting contract for StatusBar, NotificationRail, NavRail and adapter interfaces in manet/widgets/ and manet/adapters/ carried into Phase 8 operational dashboard."
  - id: CR-03
    severity: critical
    disposition: fixed
    title: "D-20 honesty violation — console help copy advertises a nonexistent `help` command (self-referential dead end)"
    details: "Fixed in Plan 07-05: registered 'help' command in manet/commands/registry.py dispatching action_show_help, backed by test_console_executes_help_command."
  - id: WR-01
    severity: warning
    disposition: deferred
    title: "`motion-toggle` is an advertised capability with zero consumers (unobservable toggle)"
    details: "Deferred to Phase 10: live telemetry and progress animation consumers will observe motion settings."
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "`except Exception: return` silently swallows — violates the zero-exception-swallowing rule"
    details: "Fixed in Plan 07-05: removed silent exception swallow in ConsoleScreen.on_key, enforcing T-7-04 visible traceback invariant."
  - id: WR-03
    severity: warning
    disposition: deferred
    title: "Workspace focus CSS is dead and the default screen has no focusable content (D-08 gap)"
    details: "Deferred to Phase 8: interactive dashboard cards and widgets mounted on MainWorkspace will receive keyboard focus."
  - id: WR-04
    severity: warning
    disposition: skipped
    title: "Palette provider docstring records a recency handoff that its own completed plan never delivered"
    details: "Skipped: docstring-only drift with zero runtime effect."
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
open: 9
deferred: 3
fixed: 3
skipped: 1
total: 17
recorded: 2026-11-07T11:18:00.000Z
---

# Phase 07: Code Review Disposition

| Finding | Severity | Disposition | Details |
|---------|----------|-------------|---------|
| CR-01 | critical | fixed | Raw user text bypasses markup via rich.text.Text; regression tested |
| CR-02 | critical | deferred | Carried into Phase 8 mounting contract (StatusBar/NotificationRail/NavRail) |
| CR-03 | critical | fixed | Addressed in Plan 07-05 (registered 'help' AppCommand in registry.py) |
| WR-01 | warning | deferred | Deferred to Phase 10 live telemetry animation consumers |
| WR-02 | warning | fixed | Addressed in Plan 07-05 (silent exception swallow removed from on_key) |
| WR-03 | warning | deferred | Deferred to Phase 8 (interactive dashboard widgets on MainWorkspace) |
| WR-04 | warning | skipped | Informational docstring drift without runtime impact |
| WR-05 | warning | open | Console output colors |
| IN-01 | info | open | Hardcoded version literal in help_about.py |
| IN-02 | info | open | CSS variable shadowing |
| IN-03 | info | open | Dead session settings |
| IN-04 | info | open | Redundant type union in registry |
| IN-05 | info | open | Runtime __init__ re-exports |
| IN-06 | info | open | Import guard test style |
| IN-07 | info | open | Asyncio test marker consistency |
| IN-08 | info | open | Input clear timing |
| IN-09 | info | open | Console footer shortcut copy |


Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
