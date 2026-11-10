---
status: testing
phase: 11-results-experiment-records
source: [11-VERIFICATION.md]
started: 2026-11-10T05:05:00Z
updated: 2026-11-10T05:05:00Z
---

## Current Test

number: 1
name: Real-terminal visuals — Results screen QoS scorecard, split panes, tabs
expected: |
  Launch the TUI in a real terminal, run a simulation to completion, and inspect the ResultsScreen:
  QoS Scorecard colors render with the intended SOC palette (green #3fb950 / yellow #d29922 / red #f85149),
  split-pane proportions look correct, and the three tabs are visually navigable.
awaiting: user response

## Tests

### 1. Real-terminal visuals — scorecard colors, split panes, tabs
expected: QoS Scorecard colors render with the intended SOC palette (green #3fb950 / yellow #d29922 / red #f85149), split-pane proportions look correct, and the three tabs are visually navigable
result: [pending]

### 2. Real-keyboard navigation loop
expected: MainWorkspace [R] → History → Enter → Results → Esc → [Esc] back, and LiveRunScreen [V] after completion — every shortcut lands on the intended screen in a live terminal with no screen stacking or focus traps (binding suppression while typing in search inputs included)
result: [pending]

### 3. Prune gesture UX (destructive-action confirm/cancel)
expected: Start a prune ([D]) on a real run, press Enter to confirm → itemized preview shown first, record deleted; on a second attempt press Esc → run and table untouched
result: [pending]

### 4. Windows file-lock contention notification
expected: With a run's trace.csv open in another Windows application (e.g., Excel), attempt [D] deletion and confirm → HistoryScreen remains active with table intact and shows the actionable "files are locked by another Windows process" notification
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps

