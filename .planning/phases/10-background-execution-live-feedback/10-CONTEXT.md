# Phase 10: Background Execution & Live Feedback - Context

**Gathered:** 2026-11-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 10 delivers non-blocking background execution and live telemetry for simulation runs in the `manet/` TUI application. It executes simulation workloads in a background worker without freezing the UI or dropping frames, while supporting one simulation workload and one ML workload at a time (with the simulation execution path fully implemented and verified in this delivery). It consumes the `SimulationLaunchRequest` allocated and prepared by Phase 9's review confirmation step. During execution, it provides honest live feedback—including run status, elapsed time, measurable progress, current stage, and a bounded event stream that never blocks the simulator and never retains unbounded telemetry in memory. It provides a safe cancellation and stop protocol that cooperatively halts execution, guarantees that partial trace files are preserved on disk without corruption, and records the experiment manifest status as interrupted. Pause/resume is presented as disabled because the simulation runner does not support checkpointing. Phase 10 wires the execution lifecycle to the handoff boundary for Phase 11 (Results & Experiment Records), but does NOT implement completed experiment browsing, result viewing/metrics calculation displays, or manifest checksum generation (Phase 11), nor does it implement live ML retraining workloads (deferred TUI-MLWORK).

</domain>

<decisions>
## Implementation Decisions

### Worker Concurrency Architecture
- **D-01:** In-Process Thread Worker (`@work(thread=True)`) anchored at the application/runner level:
  - The simulation runs in a dedicated background worker thread driving `SimulationRunner` via cooperative time stepping intervals.
  - Avoids Windows subprocess signal handling bugs, pipe buffering delays, and abrupt process termination that would discard in-memory trace buffers.
  - Direct in-memory event passing to telemetry buffers without IPC serialization overhead.
  - Ensures clean exception propagation to UI diagnostics with no silent retries.
  - Worker lifecycle is managed at the application level so switching screens does not inadvertently cancel active runs.
  — **Reversibility:** costly — anchors the execution lifecycle and worker management across `manet/runtime/`, `manet/adapters/`, and `manet/app.py`.

### Live Run View & Screen Navigation
- **D-02:** Dedicated Full-Screen Monitor (`LiveRunScreen`) with Background Navigation:
  - Upon confirming launch in Step 3 of the simulation wizard, the app transitions immediately to `LiveRunScreen`.
  - Utilizes the full 80x24 terminal viewport for clear visual hierarchy: header with scenario/seed, progress bar with elapsed wall time vs simulated duration, current execution stage, key live counters (packets sent/forwarded/dropped), and bounded event log.
  - Pressing `[B]` (Background) or `[Esc]` backgrounds the run and navigates to `MainWorkspace`, where `ActiveWorkloadCard` displays live status with shortcut `[L]` to re-open the live monitor.
  - Unmounting the screen does not terminate the background worker; when re-entering `LiveRunScreen`, widgets reconnect to the active runner telemetry stream.
  — **Reversibility:** costly — defines screen navigation contracts between `simulation_workflow.py`, `live_run.py`, and `main_workspace.py`.

### Live Telemetry & UI Refresh Throttling
- **D-03:** Decoupled Bounded Ring-Buffer with UI Timer Drain (`deque(maxlen=500)` + 10–20Hz flush):
  - The simulator worker thread appends packet/routing events to a thread-safe in-memory ring buffer (`collections.deque(maxlen=500)`) with O(1) drop-oldest semantics.
  - Simulator execution is completely non-blocking and never waits for Textual widget rendering or message handling.
  - `LiveRunScreen` runs a periodic interval timer (10Hz–20Hz / 50–100ms) that drains accumulated events from the deque and writes them to a Textual `RichLog(max_lines=500)`.
  - Full trace fidelity remains preserved on disk via the existing continuous CSV trace writer, ensuring visual sampling/throttling does not alter scientific results.
  — **Reversibility:** reversible — contained within telemetry adapters and `LiveRunScreen` widgets.

### Cancellation & Interruption Protocol
- **D-04:** Context-Differentiated Protocol:
  - **In-View Explicit Stop:** Pressing the dedicated `[X] Stop` button/shortcut inside `LiveRunScreen` immediately signals a cooperative cancellation token. The simulation loop halts at the next check, flushes accumulated in-memory trace buffers to disk, finalizes the experiment directory, and updates the launch manifest to status `interrupted`.
  - **Accidental Global Exit Guard:** Destructive global actions (`Ctrl+C`, application shutdown, or quitting while a simulation is running) present an explicit confirmation dialog warning that a run is active.
  - **Pause/Resume Indication:** A Pause button is visible in `LiveRunScreen` but permanently disabled with explicit helper text explaining that the runner does not support checkpointing (TUI-PAUSE deferred).
  - **Failure Handling:** Worker exceptions surface actionable diagnostics directly in the UI without silent retries and without mislabeling partial runs as completed.
  — **Reversibility:** costly — impacts application exit handlers, cancellation tokens in runner loops, and manifest writing logic.

### the agent's Discretion
- Exact Textual widget composition and styling for `LiveRunScreen` (e.g. progress bar styling, stage badges, and layout proportions in 80x24 compact mode).
- Event log syntax highlighting (coloring packet types: DATA in blue, RREQ/RREP in cyan, drops in red, attack actions in amber).
- UI timer drain frequency tuning between 10Hz and 20Hz for optimal responsiveness without CPU spikes.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engineering Contract & Architecture
- `GEMINI.md` — binding contract: Python 3.11+, pure-Python SimPy discrete-event simulator, determinism with explicit integer seeds, zero mock values, Windows-safe paths.
- `CHANGELOG.md` — authoritative project history and version records.
- `README.md` — documented CLI workflows, scenario paths, and runner expectations.
- `.planning/REQUIREMENTS.md` — TUI-15 through TUI-18 (background execution, live telemetry, non-corruption, interruption/stop).
- `.planning/ROADMAP.md` — Phase 10 goal, dependencies, and success criteria.

### Prior Phase Context & UI Contracts
- `.planning/phases/07-tui-shell-application-frame/07-CONTEXT.md` — Phase 7 decisions (D-01..D-21): SOC theme, keyboard navigation (`[S]`, `[Esc]`, `[Enter]`), responsive layout down to 80x24, offline-first execution.
- `.planning/phases/08-operational-dashboard/08-CONTEXT.md` — Phase 8 decisions (D-01..D-05): active workload card, honest diagnostics, capability detection.
- `.planning/phases/09-simulation-workflow/09-CONTEXT.md` — Phase 9 decisions (D-01..D-04): `SimulationLaunchRequest` handoff, `.manet-workspace/<experiment_id>` directory with initial launch manifest, 3-step wizard.

### Existing Simulation Code & Schemas
- `manet/adapters/handoff.py` — authoritative `SimulationLaunchRequest` dataclass.
- `simulator/run_scenario.py` — `SimulationRunner`, CLI entry point, discrete-event loop, trace writing.
- `simulator/scenario.py` — authentic scenario schemas and parameters.
- `simulator/metrics.py` — metric calculation functions (`compute_metrics`).
- `manet/adapters/workspace.py` — workspace directory allocation and manifest management.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `manet/adapters/handoff.py` — `SimulationLaunchRequest` dataclass containing experiment ID, scenario name, seed, config, workspace dir, and IDS flag ready for runner invocation.
- `manet/widgets/dashboard_cards.py` — `ActiveWorkloadCard` already rendered in `MainWorkspace`, ready to display live simulation status and provide `[L]` shortcut to open monitor.
- `manet/widgets/status_bar.py` — status bar capable of displaying active background running state.
- `manet/adapters/workspace.py` — records initial launch manifest; can be extended to update status to `interrupted`, `failed`, or `completed`.
- `simulator/run_scenario.py` — `SimulationRunner` composition root and simulation stepping.

### Established Patterns
- All application code strictly within `manet/` separated into `screens/`, `widgets/`, `adapters/`, `commands/`, `runtime/`.
- Textual `@work(thread=True)` worker lifecycle for non-blocking operations.
- Keyboard-first interaction: `[B]` to background, `[L]` to view live run, `[X]` to stop, `[Esc]` for back/cancel.
- Clean breakpoints handling 80x24 terminal window dimensions.

### Integration Points
- `manet/screens/simulation_workflow.py` (`on_step_review_widget_review_confirmed`): currently creates `SimulationLaunchRequest` and transitions to workspace; in Phase 10, hands off to the background runner and transitions to `LiveRunScreen`.
- `manet/screens/live_run.py`: new screen managing the live monitoring UI, progress bar, counters, and bounded event log.
- `manet/app.py`: application-level worker supervisor holding the active simulation thread and cancellation token across screen transitions.
- `manet/commands/registry.py`: command palette entries `sim:monitor` / `sim:stop`.

</code_context>

<specifics>
## Specific Ideas

- Launch confirmation immediately mounts/pushes `LiveRunScreen` so the user gets instant visual confirmation that execution started.
- `LiveRunScreen` header displays: Experiment ID, Scenario Name, Seed, IDS Status badge, and elapsed wall-clock time.
- Progress bar visually advances based on simulated time (`env.now / duration * 100%`) alongside an indicator of simulation throughput / events processed.
- Event log syntax highlighting formats packets clearly (e.g. DATA packets in blue, RREQ/RREP in cyan, packet drops in red, malicious interceptions in amber).
- Pause button is rendered visually disabled with tooltip/helper text `(Pause/resume not supported by runner)`.
- Stop button `[X]` halts the run cleanly and updates the manifest on disk to `interrupted` while preserving generated traces.

</specifics>

<deferred>
## Deferred Ideas

- Experiment results viewer, metric graphs, and historical session browsing — Phase 11 (TUI-19, TUI-20, TUI-21).
- In-TUI live ML model retraining / evaluation background runner — future milestone (TUI-MLWORK).
- Simulator pause/resume with state checkpointing — future milestone (TUI-PAUSE).
- Interactive graphical packet path / topology replay — future milestone (VIZ-01).

### Reviewed Todos (not folded)
None — no pending todos existed.

</deferred>

---

*Phase: 10-Background Execution & Live Feedback*
*Context gathered: 2026-11-08*
