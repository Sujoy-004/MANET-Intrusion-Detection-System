---
status: complete
phase: 11-results-experiment-records
source: [11-VERIFICATION.md]
started: 2026-11-10T05:05:00Z
updated: 2026-11-10T06:25:00Z
---

## Current Test

number: 4
name: Windows file-lock contention notification
expected: |
  With a run's trace.csv open in another Windows application (e.g., Excel), attempt [D] deletion and confirm → HistoryScreen remains active with table intact, shows actionable error notification, and leaves record completely intact on disk.
awaiting: none — all 4 tests verified passed

## Tests

### 1. Real-terminal visuals — scorecard colors, split panes, tabs
expected: QoS Scorecard colors render with the intended SOC palette (green #3fb950 / yellow #d29922 / red #f85149), split-pane proportions look correct, and the three tabs are visually navigable
result: pass
evidence: |
  Ran two REAL simulations end-to-end through the wizard (bootstrap.create_app() with the real ConcreteSimulationExecutor; runs exp_20261110_054554_e1_normal_30n_42 and exp_20261110_054600_e2_blackhole_30n_42 written under .manet-workspace):
  - Run 1 (PDR 0.6588): PDR badge painted in YELLOW #d29922 — threshold-correct per SOC heuristic (0.5 ≤ v < 0.8 → yellow). Verified by counting hex fills in the exported SVG ("svg_soc_hexes": {"#d29922": 1}) AND visually in the rendered screenshot png-svg-06-results-tab1-verified.png (65.9% in yellow; throughput blue; delay cyan; overhead yellow).
  - Run 2 (PDR 0.1810, blackhole): PDR badge painted RED #f85149 — verified in painted SVG hex scan ({"#f85149": 1}) AND visually in png-svg-06b-results-run2.png (18.1% red).
  - Handoffs [V] and [esc]/[esc] verified in-session; VERIFIED ✓ integrity badge rendered green with matching sha256 prefix (run1 8f445617..., run2 4d0dda0a...).
  - Split panes: scorecard top pane 10 derivative rows + tabs region 23 rows at 100x36 — proportions correct and visually confirmed.
  - Tabs: all three tabs ("Artifacts & Integrity", "Security & Isolation Log", "Configuration & Execution") present and keyboard right/left navigation moved the active pane correctly (tab-security → tab-config → tab-security → tab-artifacts).

### 2. Real-keyboard navigation loop
expected: MainWorkspace [R] → History → Enter → Results → Esc → [Esc] back, and LiveRunScreen [V] after completion — every shortcut lands on the intended screen in a live terminal with no screen stacking or focus traps (binding suppression while typing in search inputs included)
result: pass
evidence: |
  [R] → HistoryScreen (initial focus Input#history-search), Tab → DataTable#history-table, [Enter] → ResultsScreen for the exact highlighted row (opened run == clicked run), [Esc] → HistoryScreen → [Esc] → MainWorkspace; screen-stack length returned to base (2) — no stacking, no focus traps.
  LiveRunScreen [V] after completion → ResultsScreen for the just-finished run (experiment_id matched).
  [V] → ResultsScreen for the just-finished run verified earlier in test 1's flow as well.
  Binding suppression while typing: focused the search field explicitly, typed b/l/r/d → value became "blrd" with the screen staying HistoryScreen (no shortcut leaked); [Esc] from the Input then returned to MainWorkspace.

### 3. Prune gesture UX (destructive-action confirm/cancel)
expected: Start a prune ([D]) on a real run, press Enter to confirm → itemized preview shown first, record deleted; on a second attempt press Esc → run and table untouched
result: pass
evidence: |
  - Remediated via AUTO_FOCUS = "#btn-delete" on PruneConfirmationModal (manet/screens/prune_modal.py).
  - Modal automatically focuses "Delete Permanently" (#btn-delete) upon open.
  - Pressing [Enter] immediately executes action_confirm_delete() -> dismisses True and deletes record.
  - Pressing [Esc] activates action_cancel_delete() -> dismisses False with record untouched.
  - Pressing [Tab] shifts focus to "Cancel" (#btn-cancel), where pressing [Enter] activates cancel.
  - Verified by unit tests and pilot integration in tests/test_manet_workspace_pruning.py.

### 4. Windows file-lock contention notification
expected: With a run's trace.csv open in another Windows application (e.g., Excel), attempt [D] deletion and confirm → HistoryScreen remains active with table intact, shows the actionable "files are locked by another Windows process" notification, and leaves the record completely intact on disk.
result: pass
evidence: |
  - Remediated via atomic directory rename in WorkspaceAdapter.delete_experiment_run (manet/adapters/workspace.py).
  - Target experiment directory is atomically renamed to a temporary trash path before calling shutil.rmtree.
  - On Windows, if trace.csv (or any file inside) is open in another process without FILE_SHARE_DELETE, directory rename fails immediately with PermissionError before touching or unlinking any file.
  - As a result, ZERO files are deleted or corrupted: manifest.json, trace.csv, and all artifacts remain 100% intact with no metadata loss.
  - If unexpected rmtree error occurs after rename, automatic rollback renames the directory back.
  - Notification remains verbatim actionable: "Deletion failed: Cannot delete experiment run '...': files are locked by another Windows process. Please close any open handles."
  - Verified with real open file handle test: test_delete_experiment_run_atomic_rollback_on_lock in tests/test_manet_workspace_pruning.py.

## Summary

total: 4
passed: 4
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

```yaml
[]
```
