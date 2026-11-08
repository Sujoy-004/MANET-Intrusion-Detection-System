# Phase 10: Background Execution & Live Feedback - Context

**Gathered:** 2026-11-08 (Audited & Reconciled with Live Repository Baseline `e27bf046707f526f7dc1cd6a4f7c247f5f86acc0`)
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 10 delivers non-blocking background execution and live telemetry for simulation runs in the `manet/` TUI application. It executes simulation workloads in a background worker without freezing the UI or dropping frames, while supporting one simulation workload and one ML workload at a time (with the simulation execution path fully implemented and verified in this delivery). It consumes the `SimulationLaunchRequest` allocated and prepared by Phase 9's review confirmation step. During execution, it provides honest live feedback—including run status, elapsed time, measurable progress, current stage, and a bounded event stream that never blocks the simulator and never retains unbounded telemetry in memory. It provides a safe cancellation and stop protocol that cooperatively halts execution, guarantees that partial trace files are preserved on disk without corruption, and records the experiment manifest status as interrupted. Pause/resume is presented as disabled because the simulation runner does not support checkpointing. Phase 10 wires the execution lifecycle to the handoff boundary for Phase 11 (Results & Experiment Records), but does NOT implement completed experiment browsing, result viewing/metrics calculation displays, or manifest checksum generation (Phase 11), nor does it implement live ML retraining workloads (deferred TUI-MLWORK) or simulator pause/resume checkpointing (deferred TUI-PAUSE).

</domain>

<decisions>
## Implementation Decisions

### Worker Concurrency Architecture
- **D-01:** In-Process Thread Worker via Textual Worker API:
  - The simulation runs in a dedicated background worker thread scheduled at the application supervisor level (never inside `LiveRunScreen`), so screen unmounting or navigation can never abort execution.
  - In Textual 8.2.8, the worker is launched via `from textual import work` or `app.run_worker(..., thread=True, exit_on_error=False)`.
  - Avoids Windows subprocess signal handling bugs, pipe buffering delays, and abrupt process termination that would discard in-memory trace buffers.
  - Worker lifecycle is managed at the application supervisor level, decoupling run execution from screen mount lifecycles.
  - Thread workers must never query or mutate Textual widgets directly; all telemetry and state updates are published via shared synchronized structures for UI-thread polling and rendering.
- **Strict Business-Import Prohibition & Clean Dependency Direction:**
  - **Hard Architectural Invariant:** `test_manet_never_imports_business_packages` remains strictly unweakened. No module under `manet/` may import `simulator`, `attacks`, `feature_extraction`, or `ml`. Dynamic imports, `importlib`, and local import bypasses are strictly forbidden.
  - **Clean Dependency Direction:** Symmetrically, no module under `simulator/` (or other business packages) may import `manet`. `get_project_root()` may only be used by the external composition root or concrete adapter, and must never be imported into `simulator/`.
  - Define an abstract execution protocol (`SimulationExecutorProtocol`) within `manet/adapters/` or `manet/runtime/` specifying the execution interface.
  - Retain the external composition-root design: create a minimal top-level composition root outside `manet/` (e.g. `bootstrap.py` or entry point) that imports both `ManetApp` and the concrete `SimulationRunner` adapter, injecting the concrete runner into `ManetApp`.
  - Verify `python -m manet` startup through this dependency-injection path, keeping application entry fully functional while maintaining strict package isolation.
- **API, Configuration Invariants & Model-Path Resolution:**
  - Retain the existing `SimulationRunner.run()` API signature and return contract (`Dict[str, float]` metrics) completely unchanged.
  - Legacy CLI execution path (`python -m simulator.run_scenario --scenario ... --seed ... --out ...`) remains completely unaffected.
  - Pass a defensive deep copy of `SimulationLaunchRequest.config` (`copy.deepcopy(launch_request.config)`) to eliminate mutable dictionary leakage across screens.
  - **Model-Path Resolution:** Resolve the configured IDS `model_path` relative to the project root when it is relative; preserve absolute paths and explicitly configured model selections. Do not hardcode or silently replace custom model paths with `best_model.joblib`.
- **Controlled Stepping API, Virtual-Time Completion & Stepping Equivalence:**
  - Driven by cooperative time stepping with cooperative cancellation checking (an explicit `threading.Event` token between steps/ticks).
  - **Virtual-Time Completion & Boundary Semantics:** Clarify that a naive `while env.peek() < duration: env.step()` loop may produce matching trace rows without advancing `env.now` to `duration` (halting at the timestamp of the last event prior to duration). Controlled stepping is required to preserve full `env.run(until=duration)` semantics: advancing virtual time cleanly to the requested duration (`env.now == duration` on normal completion) while strictly not processing ordinary events scheduled exactly at that boundary.
  - **Stepping Equivalence Scope:** Cooperative time stepping was experimentally verified against `env.run(until=duration)` for the tested scenario/seed matrix (`e1_normal_30n.json`, `e2_blackhole_30n.json`, `e4_grayhole_50n.json` across seeds 1, 42, 99), producing identical row counts and byte-identical traces. This equivalence is characterized as verified for the tested scenario/seed matrix rather than an assumed universal mathematical proof.
- **Regression Test Coverage Requirements:**
  - Test suites must maintain explicit regression coverage for:
    1. Final `env.now` advancement to target `duration` on clean completion;
    2. Exact duration boundary handling (confirming events scheduled at `time == duration` are not processed, matching baseline CLI runs);
    3. Scenarios with no further events before the target duration (sparse/quiescent queues);
    4. IDS-enabled runs (`run_with_ids`) including model loading, inference, and node isolation logging;
    5. Correct emission and capture of `NODE_STATUS` trace events (e.g. node quarantine/isolation);
    6. Deterministic trace generation (exact row-by-row matching with baseline CLI runs given identical seed);
    7. Cooperative cancellation (verifying token stops loop and preserves partial traces).
  — **Reversibility:** costly — anchors execution lifecycle, dependency injection boundaries, and worker management.

### Live Run View & Screen Navigation
- **D-02:** Dedicated Full-Screen Monitor (`LiveRunScreen`) as a Reconnectable View:
  - Upon confirming launch in Step 3 of the simulation wizard (`simulation_workflow.py`), the application transitions immediately to `LiveRunScreen`.
  - `LiveRunScreen` is a reconnectable observer of supervisor state; it never owns, spawns, or terminates the worker thread.
  - Full 80x24 terminal viewport utilization: header with scenario/seed, progress bar with elapsed wall time vs simulated duration, current execution stage, key live counters, and bounded event log.
  - Navigation: `[B]` (Background) or `[Esc]` backgrounds the run and navigates to `MainWorkspace`, where `ActiveWorkloadCard` displays live status with shortcut `[L]` to re-open the live monitor.
  - Unmounting `LiveRunScreen` does not abort or interrupt the worker; re-entering the screen reconnects widgets to active supervisor state.
- **Authentic Execution Stages:**
  - Exactly three authentic execution stages are defined:
    1. `INITIALIZING`: allocating environment, scenario loading, node placement, and RNG setup;
    2. `SIMULATING`: active SimPy discrete-event stepping loop;
    3. `FINALIZING`: flushing trace CSV, persisting IDS isolation log, updating manifest.
  - Never fabricate arbitrary percentages or fake intermediate stages.
- **Honest Progress & Monotonic Timing:**
  - Progress is strictly computed as `env.now / duration * 100%` (or 0.0 to 1.0) based on authentic SimPy virtual time.
  - Elapsed time is strictly computed using `time.monotonic() - start_monotonic` (monotonic wall-clock seconds). Never conflate simulated time with wall time, and never invent estimated time of arrival (ETA).
- **StatusAdapter & Command Integration:**
  - Wire `ActiveWorkloadCard` and `StatusBar` to real supervisor state (replacing hardcoded `IDLE` in `StatusAdapter`).
  - Add a dedicated, lightweight workload-status refresh path (e.g. 0.5s timer or state change callback) rather than waiting on MainWorkspace's 4-second diagnostics timer.
  - Add `[L]` shortcut binding on `MainWorkspace` to open the active simulation monitor.
  - Register `sim:monitor` (open live view) and `sim:stop` (stop active simulation) in `manet/commands/registry.py`.
  — **Reversibility:** costly — defines navigation contracts between `simulation_workflow.py`, `live_run.py`, and `main_workspace.py`.

### Live Telemetry & UI Refresh Throttling
- **D-03:** Decoupled Bounded Ring-Buffer with UI Timer Drain:
  - Simulator worker thread (producer) appends packet and node status events to a bounded `collections.deque(maxlen=500)` with drop-oldest semantics.
  - Non-blocking execution: simulator never awaits Textual rendering or message dispatch.
  - Full trace fidelity is written directly to disk via `write_traces()` on run finalization (or partial trace on interrupt).
- **Explicit Synchronization for Shared Telemetry:**
  - Protect the shared telemetry deque and overflow counters using explicit synchronization (e.g., `threading.Lock`).
  - Shared mutations of telemetry state (appending events, tracking dropped/overflow event counts, clearing, or multi-item draining) must be synchronized to prevent race conditions or counter skew between the background worker and the UI thread.
- **Lightweight Producer & Bounded Consumer Drain:**
  - **Lightweight Producer:** simulator worker thread appends raw event snapshots and increments counters under lock immediately (O(1)), without performing string formatting or Rich text markup generation.
  - **Bounded UI Drain:** `LiveRunScreen` runs a periodic interval timer (10Hz–20Hz / 50–100ms) that drains accumulated events in bounded batches (e.g. up to 100 events per cycle) into Textual `RichLog(max_lines=500)`. Never blocks the Textual event loop during high-event packet bursts (~70k events/sec).
- **Authentic Counters:**
  - Counters are derived strictly from real event types in traces:
    - `DATA_SENT`: authentic data transmission origins;
    - `DATA_FWD`: authentic forwarding hops/events (explicitly labeled as hops/forwarding events);
    - `DATA_RECV`: authentic data deliveries at destinations;
    - `DATA_DROP`: authentic packet drop events.
  — **Reversibility:** reversible — contained within telemetry adapters and `LiveRunScreen` widgets.

### Cancellation & Interruption Protocol
- **D-04:** Context-Differentiated Stop Protocol:
  - **In-View Explicit Stop:** Pressing dedicated `[X] Stop` inside `LiveRunScreen` immediately signals the cooperative cancellation token without a modal prompt. Execution halts, partial trace rows are written to disk, manifest is marked `interrupted`, and UI updates cleanly.
  - **Accidental Global Exit Guard:** Destructive global actions (`Ctrl+Q`, application shutdown, or quitting while a run is active) present a confirmation dialog to prevent accidental aborts, and await finalization before exiting.
  - **Pause/Resume Indication:** Pause button is visible in `LiveRunScreen` but permanently disabled with explicit label/tooltip `(Pause not supported by runner)` fulfilling TUI-18 while keeping TUI-PAUSE deferred.
- **Supervisor State Machine & Lifecycle Transitions:**
  - A single app-level supervisor (`WorkloadSupervisor` / `SimulationSupervisor`) owns the active launch request, worker reference, cancellation token, telemetry ring buffer, counters, and lifecycle state.
  - Enforces single active simulation capacity while preserving an extensible slot model (one simulation + one ML workload).
  - Explicit lifecycle states and valid transitions:
    - `CONFIGURED` → `RUNNING` → `COMPLETED`
    - `CONFIGURED` → `RUNNING` → `STOPPING` → `INTERRUPTED`
    - `RUNNING` → `FAILED`
    - `STOPPING` → `FAILED` when finalization fails.
- **Terminal-State Race Precedence:**
  - Precedence order for terminal-state races: `FAILED` > `INTERRUPTED` > `COMPLETED`.
  - If worker execution or finalization fails at any point (even if cancellation was signaled or simulation loop reached duration), `FAILED` takes highest precedence.
  - If cancellation was signaled and finalization succeeds, terminal state is `INTERRUPTED` (takes precedence over normal completion).
  - If the simulation loop reaches duration, no cancellation occurred, and finalization succeeds, terminal state is `COMPLETED`.
- **Finalization Contract & Persistence Guarantees:**
  - Neither `INTERRUPTED` nor `COMPLETED` may ever be reported or recorded until required finalization succeeds (flushing partial or complete traces to disk via `write_traces()` and writing any configured IDS isolation log).
  - If finalization raises an unhandled error, the state transitions to `FAILED`.
  - **Best-Effort Persistence on Failure:** When execution fails (`RUNNING` → `FAILED` or `STOPPING` → `FAILED`), the supervisor must perform best-effort flushing of in-memory trace buffers (`write_traces()`) and IDS isolation log before recording `FAILED` with diagnostics in `manifest.json`.
  - **Atomic Manifest Updates:** State updates to `manifest.json` are written via temporary file write (`manifest.json.tmp`) and atomic replacement (`os.replace`).
  - Stop logic is idempotent and safely handles race conditions: stop-before-start, stop-during-run, stop-at-completion, duplicate stop, and worker error.
  — **Reversibility:** costly — governs execution state machine, file writing protocols, and manifest guarantees.

### the agent's Discretion
- Visual badge styling and syntax formatting in `RichLog`.
- Fine-tuning UI timer drain frequency between 10Hz and 20Hz (50–100ms) and batch chunk size for optimal responsiveness without CPU spikes.
- Progress bar and counter layout formatting in 80x24 compact mode.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engineering Contract & Architecture
- `GEMINI.md` — local architectural contract: Python 3.11+, pure-Python SimPy discrete-event simulator, determinism with explicit integer seeds, zero mock values, Windows-safe paths. *(Note: local file present in repository root; not tracked on remote GitHub).*
- `CHANGELOG.md` — authoritative project history and version records.
- `README.md` — documented CLI workflows, scenario paths, and runner expectations.
- `.planning/REQUIREMENTS.md` — TUI-15 through TUI-18 (background execution, live telemetry, non-corruption, interruption/stop).
- `.planning/ROADMAP.md` — Phase 10 goal, dependencies, and success criteria.

### Prior Phase Context & UI Contracts
- `.planning/phases/07-tui-shell-application-frame/07-CONTEXT.md` — Phase 7 decisions (D-01..D-21): SOC theme, keyboard navigation (`[S]`, `[Esc]`, `[Enter]`), responsive layout down to 80x24, offline-first execution.
- `.planning/phases/08-operational-dashboard/08-CONTEXT.md` — Phase 8 decisions (D-01..D-05): active workload card, honest diagnostics, capability detection.
- `.planning/phases/09-simulation-workflow/09-CONTEXT.md` — Phase 9 decisions (D-01..D-04): `SimulationLaunchRequest` handoff, `.manet-workspace/<experiment_id>` directory with initial launch manifest, 3-step wizard.

### Existing Simulation Code & Schemas
- `scenarios/*.json` — authentic preset scenario definitions (e.g. `e1_normal_30n.json`, `e2_blackhole_30n.json`, `e4_grayhole_50n.json`). *(Note: `simulator/scenario.py` does not exist; scenario loading is implemented via `load_scenario` in `simulator/run_scenario.py`).*
- `simulator/run_scenario.py` — `SimulationRunner`, CLI entry point, `load_scenario`, discrete-event loop, trace writing.
- `simulator/metrics.py` — metric calculation functions (`compute_metrics`).
- `manet/adapters/handoff.py` — authoritative `SimulationLaunchRequest` dataclass.
- `manet/adapters/workspace.py` — workspace directory allocation and launch manifest recording.
- `manet/adapters/status.py` — workload status dataclass.
- `tests/test_manet_import_boundaries.py` — AST boundary test enforcing `manet/` package isolation from business logic packages.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `manet/adapters/handoff.py` — `SimulationLaunchRequest` dataclass containing experiment ID, scenario name, seed, config, workspace dir, and IDS flag ready for runner invocation.
- `manet/widgets/dashboard_cards.py` — `ActiveWorkloadCard` already rendered in `MainWorkspace`, ready to display live simulation status and provide `[L]` shortcut to open monitor.
- `manet/widgets/status_bar.py` — status bar capable of displaying active background running state.
- `manet/adapters/workspace.py` — records initial launch manifest; can be extended to atomically update status to `RUNNING`, `STOPPING`, `INTERRUPTED`, `FAILED`, or `COMPLETED`.
- `simulator/run_scenario.py` — `SimulationRunner` composition root and simulation stepping.

### Established Patterns
- All application code strictly within `manet/` separated into `screens/`, `widgets/`, `adapters/`, `commands/`, `runtime/`.
- Textual worker pattern via `from textual import work` or `app.run_worker(..., thread=True, exit_on_error=False)`.
- Keyboard-first interaction: `[B]` to background, `[L]` to view live run, `[X]` to stop, `[Esc]` for back/cancel.
- Clean breakpoints handling 80x24 terminal window dimensions.

### Integration Points
- Top-level bootstrap: Minimal integration composition root outside `manet/` instantiating concrete `SimulationRunner` adapter and passing it to `ManetApp(runner=...)`.
- `manet/screens/simulation_workflow.py`: Wizard Step 3 confirmation initiates supervisor run and transitions to `LiveRunScreen`.
- `manet/screens/live_run.py`: new screen managing the live monitoring UI, progress bar, counters, and bounded event log.
- `manet/app.py`: application-level supervisor holding active simulation thread, cancellation token, and telemetry deque across screen transitions.
- `manet/commands/registry.py`: command palette entries `sim:monitor` / `sim:stop`.

</code_context>

<specifics>
## Specific Ideas

- Launch confirmation immediately mounts/pushes `LiveRunScreen` so the user gets instant visual confirmation that execution started.
- `LiveRunScreen` header displays: Experiment ID, Scenario Name, Seed, IDS Status badge, and elapsed wall-clock time (`time.monotonic() - start_monotonic`).
- Progress bar visually advances based on simulated time (`env.now / duration * 100%`) alongside authentic counters (`DATA_SENT`, `DATA_FWD`, `DATA_RECV`, `DATA_DROP`).
- Event log syntax highlighting formats packets clearly (e.g. DATA packets in blue, RREQ/RREP in cyan, packet drops in red, malicious interceptions in amber).
- Pause button is rendered visually disabled with tooltip/helper text `(Pause not supported by runner)`.
- Stop button `[X]` halts the run cleanly and updates the manifest on disk to `interrupted` while preserving generated partial traces.

</specifics>

<deferred>
## Deferred Ideas

- Experiment results viewer, metric graphs, and historical session browsing — Phase 11 (TUI-19, TUI-20, TUI-21).
- In-TUI live ML model retraining / evaluation background runner — future milestone (TUI-MLWORK).
- Simulator pause/resume with state checkpointing — future milestone (TUI-PAUSE).
- Interactive graphical packet path / network topology replay — future milestone (VIZ-01).

### Reviewed Todos (not folded)
None — no pending todos existed.

</deferred>

---

*Phase: 10-Background Execution & Live Feedback*
*Context gathered: 2026-11-08 (Audited baseline: e27bf046707f526f7dc1cd6a4f7c247f5f86acc0)*
