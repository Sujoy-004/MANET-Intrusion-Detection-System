# Phase 11: Results & Experiment Records - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-09
**Phase:** 11-results-experiment-records
**Areas discussed:** Results Screen Layout & Exploration Depth, Session History & Past Run Browser, Artifact Integrity & Checksum Verification, Workspace Storage & Safe Cleanup Protocol

---

## Results Screen Layout & Exploration Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid Split-Pane | Fixed QoS Scorecard at top (PDR, throughput, delay, overhead) + Tabbed lower pane (Trace/Checksums, Isolation Log, Packet stats) | ✓ |
| Full Tabbed Detail Inspector | Entire screen partitioned into tabs (Overview QoS, Artifacts & Checksums, Security & Isolation Log) | |
| Unified Scrollable Card Grid | Single vertically-scrolling page with stacked metric and artifact cards | |

**User's choice:** Hybrid Split-Pane
**Notes:** Retains immediate academic QoS visibility on top while providing uncluttered inspection of artifacts, SHA-256 hashes, and isolation details in tabs below.

---

## Session History & Past Run Browser

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid Two-Tier Navigation | Keep compact RecentExperimentsTable on dashboard; [R] or Enter on a row opens full-screen History/Results screen with sorting, search/filtering, and detail inspection | ✓ |
| Dedicated Full-Screen History Screen Only | Remove dashboard table; [R] navigates to full history browser, [Esc] returns to dashboard | |
| In-Workspace Modal Expansion | Keep everything on MainWorkspace; selecting a row opens a floating modal popup dialog with the metrics | |

**User's choice:** Hybrid Two-Tier Navigation
**Notes:** Leaves dashboard layout clean and glanceable while unlocking full viewport filtering and sorting on a dedicated history screen via existing `[r]` binding.

---

## Artifact Integrity & Checksum Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Lazy Verification on Open | Record SHA-256 for trace.csv and isolation_log.json in manifest on run completion; verify checksums and show integrity badge when run is opened in Results screen | ✓ |
| Record-Only Passive Display | Record SHA-256 checksums in manifest at completion and display hashes in Results screen, but do not re-hash to verify on load | |
| Eager Batch Verification | Re-hash and verify all trace files in workspace during history list scanning so table shows verification badge upfront | |

**User's choice:** Lazy Verification on Open
**Notes:** Keeps history scanning instantaneous on Windows by avoiding heavy disk rehashing upfront, while providing verifiable tamper detection upon opening individual runs.

---

## Workspace Storage & Safe Cleanup Protocol

| Option | Description | Selected |
|--------|-------------|----------|
| Interactive Pruning with Preview Confirmation Modal | Provide [D] Delete Run in history with itemized preview dialog (directory path, file count, total bytes) requiring explicit confirmation before disk deletion | ✓ |
| Strictly Append-Only Storage | No in-app deletion; all experiment records and traces are permanently preserved on disk to guarantee an inviolable audit trail | |
| Soft-Delete / Hide Toggle | In-app action hides/archives runs from the active history table without physically removing files from disk | |

**User's choice:** Interactive Pruning with Preview Confirmation Modal
**Notes:** Satisfies TUI-21 safe cleanup requirements while protecting against accidental deletion via an explicit confirmation dialog detailing directory paths, files, and byte sizes.

---

## the agent's Discretion

None — all 4 gray areas were explicitly explored, compared, and decided with structured user choices.

## Deferred Ideas

- Multi-experiment comparative plotting / bar charts across seeds (deferred VIZ-01).
- In-TUI ML model retraining and feature dataset generation (deferred TUI-MLWORK).
- Checkpoint-based simulation pause and resume (deferred TUI-PAUSE).
