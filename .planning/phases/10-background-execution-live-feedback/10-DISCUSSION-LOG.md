# Phase 10: Background Execution & Live Feedback - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-08
**Phase:** 10-Background Execution & Live Feedback
**Areas discussed:** Worker Concurrency Architecture, Live Run View & Screen Navigation, Live Telemetry & UI Refresh Throttling, Cancellation & Interruption Protocol

---

## Worker Concurrency Architecture

| Option | Description | Selected |
|--------|-------------|----------|
| In-Process Thread Worker (`@work(thread=True)`) | Native Textual worker lifecycle, direct in-memory telemetry without IPC serialization, guaranteed partial trace flushing on cancel | ✓ |
| Asynchronous Subprocess Runner | Complete process isolation with stdout streaming; risks trace loss on Windows termination and requires string parsing | |
| Multiprocessing Worker | Separate Python process using IPC queues; high Windows `spawn` latency and pipe deadlock risks | |

**User's choice:** `In-Process Thread Worker (@work(thread=True))`
**Notes:** Chosen for guaranteed partial trace persistence on cancel, absence of Windows subprocess termination issues, zero IPC serialization overhead, and clean integration with Textual's event loop.

---

## Live Run View & Screen Navigation

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated Full-Screen Monitor (`LiveRunScreen`) | Full 80x24 terminal viewport for telemetry and bounded logs, with clean `[B]` (Background) and `[L]` (Live view) navigation | ✓ |
| Embedded Workload Card in MainWorkspace | Constrains log viewer to 3–4 lines on 80x24 terminals, creates layout overflow risks, and causes high repaint churn | |
| Modal Overlay Dialog (`LiveRunModal`) | Pop-up dialog over dashboard; pinches telemetry tables and causes visual clipping on compact terminals | |

**User's choice:** `Dedicated Full-Screen Monitor (LiveRunScreen) with Background Navigation ([B]/[L])`
**Notes:** Full screen real estate prevents clipping in 80x24 terminals and allows rich, uncrowded live feedback while still supporting backgrounding to the main dashboard.

---

## Live Telemetry & UI Refresh Throttling

| Option | Description | Selected |
|--------|-------------|----------|
| Decoupled Bounded Ring-Buffer with UI Timer Drain | Simulator appends O(1) to `deque(maxlen=500)`, UI flushes at 10–20Hz to `RichLog(max_lines=500)` without blocking runner | ✓ |
| Worker-Throttled Batch Message Push | Rate-limited `post_message` from worker thread; adds timing checks to hot packet loop and risks asyncio message queue buildup | |
| High-Level Stage Progress Only | Progress bar and stage steps without live event stream; discards packet-level visibility | |

**User's choice:** `Decoupled Bounded Ring-Buffer with UI Timer Drain — collections.deque(maxlen=500) + 10-20Hz flush to RichLog`
**Notes:** Eliminates any risk of simulator blocking or UI event-loop backlog during high-frequency SimPy packet bursts (~70k events/sec), while full traces continue streaming directly to disk.

---

## Cancellation & Interruption Protocol

| Option | Description | Selected |
|--------|-------------|----------|
| Context-Differentiated Protocol | Immediate stop on explicit `[X] Stop` action in live view; confirmation modal on global app quit / destructive exit | ✓ |
| Instant Single-Key Stop | Always halt immediately on shortcut without confirmation prompt; vulnerable to accidental keypresses | |
| Modal Confirmation Dialog Everywhere | Always prompt confirmation modal; simulation continues advancing events while modal is open since runner cannot pause | |
| Two-Stage In-Place Confirmation | Press once to prime, press again within 3s to confirm; non-standard desktop interaction | |

**User's choice:** `Context-Differentiated Protocol — Immediate stop on explicit [X] Stop action; confirmation warning on global app quit / destructive exit`
**Notes:** Provides zero-latency response for deliberate in-screen stop commands while protecting active runs from accidental `Esc` or app quit keystrokes. Partial traces are cleanly flushed and manifest is marked `interrupted`.

---

## the agent's Discretion

- Visual styling, coloring, and layout proportions of progress bars, stage badges, and telemetry stream inside `LiveRunScreen`.
- Event log syntax highlighting formatting.
- Fine-tuning UI timer flush rate between 10Hz and 20Hz (50–100ms).

## Deferred Ideas

- Experiment results viewer, metric calculation inspection, and history browsing — Phase 11.
- In-TUI live ML model retraining worker — future milestone (TUI-MLWORK).
- Simulator pause/resume with state checkpointing — future milestone (TUI-PAUSE).
- Graphical packet path / network topology replay — future milestone (VIZ-01).
