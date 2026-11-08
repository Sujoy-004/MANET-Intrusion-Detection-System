# Phase 10: Background Execution & Live Feedback - Research

**Researched:** 2026-11-08  
**Domain:** Concurrent Python execution, Textual worker lifecycle, SimPy discrete-event cooperative stepping, decoupled bounded telemetry, cooperative cancellation, atomic persistence  
**Confidence:** HIGH  

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Worker Concurrency Architecture (D-01)
- **In-Process Thread Worker via Textual Worker API:**
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

#### Live Run View & Screen Navigation (D-02)
- **Dedicated Full-Screen Monitor (`LiveRunScreen`) as a Reconnectable View:**
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

#### Live Telemetry & UI Refresh Throttling (D-03)
- **Decoupled Bounded Ring-Buffer with UI Timer Drain:**
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

#### Cancellation & Interruption Protocol (D-04)
- **Context-Differentiated Stop Protocol:**
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

### the agent's Discretion
- Visual badge styling and syntax formatting in `RichLog`.
- Fine-tuning UI timer drain frequency between 10Hz and 20Hz (50–100ms) and batch chunk size for optimal responsiveness without CPU spikes.
- Progress bar and counter layout formatting in 80x24 compact mode.

### Deferred Ideas (OUT OF SCOPE)
- Experiment results viewer, metric graphs, and historical session browsing — Phase 11 (TUI-19, TUI-20, TUI-21).
- In-TUI live ML model retraining / evaluation background runner — future milestone (TUI-MLWORK).
- Simulator pause/resume with state checkpointing — future milestone (TUI-PAUSE).
- Interactive graphical packet path / network topology replay — future milestone (VIZ-01).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **TUI-15** | User can interact with the TUI without it freezing while a simulation runs in the background, with architecture supporting one simulation workload and one ML workload at a time (simulation execution implemented and verified in this delivery) | Thread-worker architecture via Textual `app.run_worker(..., thread=True, exit_on_error=False)` managed by `WorkloadSupervisor` at the app level. Decoupled telemetry ring buffer eliminates UI-thread blocking; extensible single-slot execution architecture strictly enforces 1 active simulation workload while keeping UI event loop responsive at 60 FPS. |
| **TUI-16** | User sees run status, elapsed time, measurable progress, and current stage, with bounded live event/log streaming that never blocks the simulator and never retains unbounded telemetry in memory | Honest SimPy virtual-time progress (`env.now / duration * 100%`), monotonic wall-clock timing (`time.monotonic() - start_monotonic`), authentic stages (`INITIALIZING`, `SIMULATING`, `FINALIZING`), authentic packet counters (`DATA_SENT`, `DATA_FWD`, `DATA_RECV`, `DATA_DROP`), and bounded ring buffer (`maxlen=500`) drained in batches (≤100 items per 50-100ms tick) into `RichLog(max_lines=500)`. |
| **TUI-17** | User can Ctrl+C, Esc, or shut down the application without corrupting result files; existing simulation semantics (event ordering, results) are preserved regardless of UI interaction, and UI callbacks cannot change simulation or IDS decisions | Cooperative cancellation token (`threading.Event`), two-phase atomic manifest replacement (`manifest.json.tmp` -> `os.replace`), best-effort disk flushing (`write_traces()`, isolation log) on interruption/failure, and strict separation between UI rendering and simulation execution preventing UI callbacks from altering simulation state. |
| **TUI-18** | User can stop a running simulation safely; pause/resume is presented as disabled because the runner does not support it safely; an interrupted run preserves partial traces and is marked interrupted; worker exceptions surface actionable diagnostics with no silent retries and no mislabeling of partial runs as completed | In-view dedicated `[X] Stop` button signaling cooperative cancellation, disabled Pause button with helper text `(Pause not supported by runner)`, partial trace disk persistence, atomic manifest status `INTERRUPTED`, and rigorous supervisor state machine enforcing terminal precedence: `FAILED` > `INTERRUPTED` > `COMPLETED`. |
</phase_requirements>

## Summary

Phase 10 connects the simulation wizard configured in Phase 9 (`SimulationLaunchRequest`) to real, non-blocking execution inside the MANET IDS TUI. It executes simulations in a dedicated background worker thread managed by an application-level supervisor (`WorkloadSupervisor`), ensuring that terminal UI frames are never dropped, navigation remains instantaneous, and screen transitions do not kill running simulations.

The core challenge of this phase is maintaining strict architectural boundaries while providing rich live telemetry:
1. **Architectural Purity:** `manet/` must never import `simulator`, `attacks`, `feature_extraction`, or `ml`, nor may `simulator/` import `manet` (`test_manet_never_imports_business_packages` remains strictly unweakened). This is achieved through an external composition root (`bootstrap.py`) that implements `SimulationExecutorProtocol` and injects the concrete adapter into `ManetApp`.
2. **Stepping Equivalence & Virtual-Time Completion:** SimPy discrete-event simulation runs in a cooperative stepping loop checking a `threading.Event` token. To match baseline CLI execution (`SimulationRunner.run()`) identically, the stepping loop explicitly schedules an `URGENT` `until` event at `duration`, cleanly advancing `env.now` to `duration` without processing ordinary events scheduled at that boundary. Stepping equivalence was verified empirically across preset scenarios (`e1_normal_30n.json`, `e2_blackhole_30n.json`, `e4_grayhole_50n.json` across seeds 1, 42, 99) with byte-identical trace logs and identical metric results.
3. **Decoupled Telemetry:** The simulator emits up to ~70,000 events/second. Telemetry is collected via a synchronized bounded deque (`maxlen=500`) with O(1) integer counter increments. The UI thread periodically drains bounded chunks (≤100 items per 50-100ms) into `RichLog(max_lines=500)`. Memory consumption remains strictly constant and the simulator thread is never throttled.
4. **Resilient Interruption & Atomic Persistence:** Stopping a run preserves partial traces to disk via `write_traces()` and atomically updates `manifest.json` (`manifest.json.tmp` -> `os.replace`). State precedence is strictly enforced (`FAILED` > `INTERRUPTED` > `COMPLETED`), eliminating any possibility of mislabeling aborted runs as completed.

**Primary recommendation:** Build an external composition root `bootstrap.py` implementing `SimulationExecutorProtocol`, an application-level `WorkloadSupervisor` state machine in `manet/runtime/supervisor.py`, a synchronized telemetry ring buffer in `manet/runtime/telemetry.py`, and a reconnectable `LiveRunScreen` in `manet/screens/live_run.py` utilizing Textual `ProgressBar` and `RichLog`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Simulation Discrete-Event Stepping | Simulator Worker Thread | `SimulationRunner` / SimPy | Heavy CPU computation (~70k events/sec) must run in a background OS thread to keep the Textual asyncio event loop running at 60 FPS without frame drops. |
| Workload Concurrency & Slot Management | `WorkloadSupervisor` (App Level) | `ManetApp` | Execution lifecycle outlives individual screen mounts (`LiveRunScreen`); supervisor enforces the single-active-simulation capacity invariant. |
| In-Memory Live Telemetry Buffering | Telemetry Ring Buffer (`collections.deque`) | `threading.Lock` | Bounded drop-oldest ring buffer decouples high-speed simulator emissions from UI drain rate, keeping memory strictly bounded. |
| Live Telemetry Draining & Rendering | `LiveRunScreen` UI Timer (10Hz-20Hz) | Textual `RichLog` & `ProgressBar` | UI drains bounded batches (≤100 items) and renders formatted markup on the Textual main loop without freezing. |
| Background Status & Navigation Routing | `MainWorkspace` & `ActiveWorkloadCard` | `StatusAdapter` & `StatusBar` | Allows backgrounding run (`[B]`), displaying live status in dashboard card, and reconnecting (`[L]`). |
| Dependency Injection & Composition Root | Root `bootstrap.py` | `manet/__main__.py` | Glues `manet` presentation layer to `simulator` execution engine without violating AST boundary tests. |
| Trace & Manifest Atomic Persistence | Worker Finalization Routine | `WorkspaceAdapter` (`os.replace`) | Guaranteed partial/complete trace persistence and atomic manifest status updates without disk corruption. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **Python** | 3.11.8 [VERIFIED: local runtime] | Runtime environment | Windows-native target required by `GEMINI.md`. |
| **Textual** | 8.2.8 [VERIFIED: local runtime] | TUI framework & worker runtime | Provides `app.run_worker(..., thread=True, exit_on_error=False)`, `RichLog`, and `ProgressBar`. |
| **SimPy** | 4.1.2 [VERIFIED: local runtime] | Discrete-event clock & stepping loop | Event scheduler for MANET network events. |
| **NetworkX** | 3.6.1 [VERIFIED: local runtime] | Topology & neighbor graph | Graph substrate for AODV routing and dynamic attacker selection. |
| **pytest** | 9.0.2 [VERIFIED: local runtime] | Test framework | Regression testing with `asyncio` support. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **threading (stdlib)** | Python 3.11 stdlib [VERIFIED] | Synchronization & cancellation | `threading.Event` cancellation tokens and `threading.Lock` for telemetry deque. |
| **collections (stdlib)** | Python 3.11 stdlib [VERIFIED] | Bounded queue | `collections.deque(maxlen=500)` for drop-oldest telemetry. |
| **time (stdlib)** | Python 3.11 stdlib [VERIFIED] | Monotonic timing | `time.monotonic()` for elapsed wall-clock time calculation. |
| **os (stdlib)** | Python 3.11 stdlib [VERIFIED] | Atomic file replacement | `os.replace` for atomic manifest updates on Windows. |
| **copy (stdlib)** | Python 3.11 stdlib [VERIFIED] | Defensive copying | `copy.deepcopy` to defuse shared dictionary mutation. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| In-process thread worker (`app.run_worker(..., thread=True)`) | Subprocess execution (`multiprocessing` / `subprocess.Popen`) | Rejected per D-01: Windows process spawning has high startup latency, complex IPC serialization, broken signal handling on Ctrl+C, and pipe buffer truncations that discard in-memory traces on interrupt. |
| Cooperative `env.step()` loop | Raw `env.run(until=duration)` inside worker thread | Raw `env.run` does not allow cooperative cancellation checking or live step-by-step progress telemetry without custom SimPy monkey-patching. Cooperative stepping allows clean cancellation checks every N steps. |
| Bounded ring buffer (`collections.deque(maxlen=500)`) | Unbounded `queue.Queue` | Unbounded queue causes memory leaks and UI lag when simulator generates 100,000+ packets in < 1 second. Bounded ring buffer drops oldest UI events while disk trace records 100% of packets. |

## Package Legitimacy Audit

No new external packages are introduced in Phase 10. All required dependencies are verified in the existing local environment:

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `textual` | PyPI | 4+ yrs | 2M+/mo | github.com/Textualize/textual | [OK] | Approved (pinned at 8.2.8) |
| `simpy` | PyPI | 15+ yrs | 1.5M+/mo | gitlab.com/team-simpy/simpy | [OK] | Approved (pinned at 4.1.2) |
| `networkx` | PyPI | 15+ yrs | 45M+/mo | github.com/networkx/networkx | [OK] | Approved (pinned at 3.6.1) |
| `pytest` | PyPI | 15+ yrs | 100M+/mo | github.com/pytest-dev/pytest | [OK] | Approved (pinned at 9.0.2) |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none  

## Architecture Patterns

### System Architecture Diagram

```mermaid
flowchart TD
    subgraph UI_Thread ["UI Thread (Textual Asyncio Event Loop)"]
        SW["SimulationWorkflowScreen\n(Step 3 Review Confirmed)"] -->|"Allocate & handoff\nSimulationLaunchRequest"| WS["WorkloadSupervisor\n(Application Level)"]
        WS -->|"Mount & Switch Screen"| LRS["LiveRunScreen\n(Reconnectable View)"]
        WS -->|"Update status"| AWC["ActiveWorkloadCard\n& StatusBar"]
        
        LRS -->|"Periodic Timer\n(10Hz-20Hz / 50ms)"| Drain["Bounded UI Drain\n(drain ≤100 events under lock)"]
        Drain -->|"Format Rich markup"| RL["RichLog (max_lines=500)\n& ProgressBar"]
        
        LRS -.->|"User presses [B] / [Esc]"| MW["MainWorkspace\n(Background View)"]
        MW -.->|"User presses [L]"| LRS
        LRS -->|"User presses [X] Stop"| CancelAction["Signal cancel_token.set()"]
    end

    subgraph Composition_Root ["Composition Root (bootstrap.py)"]
        WS -->|"Start Simulation"| CR["ConcreteSimulationExecutor\n(implements SimulationExecutorProtocol)"]
    end

    subgraph Worker_Thread ["Dedicated Background Worker Thread"]
        CR -->|"Launch via\napp.run_worker(thread=True)"| WorkerProc["Worker Stepping Loop"]
        WorkerProc -->|"Instantiate & Initialize"| SR["SimulationRunner\n(pure Python)"]
        WorkerProc -->|"Cooperative stepping\nuntil == duration"| StepLoop{"env.step()\nToken set?"}
        
        StepLoop -->|"Yes (Cancelled)"| BreakLoop["Break Loop"]
        StepLoop -->|"No (Continue)"| EventLog["runner.log_event()"]
        
        EventLog -->|"Append to disk rows"| DiskBuf["runner.trace_rows"]
        EventLog -->|"Synchronized enqueue (O(1))\n& update counters"| TB["Shared Telemetry Deque\n(collections.deque maxlen=500)\n+ threading.Lock"]
        
        StepLoop -->|"Completed or Broken"| Finalize["Finalization Routine"]
        Finalize -->|"Flush all rows to disk"| CSVFile["trace.csv (Disk)"]
        Finalize -->|"Write isolation log (if IDS)"| IsoLog["isolation_log.json (Disk)"]
        Finalize -->|"Atomic replace\nmanifest.json.tmp -> manifest.json"| Manifest["manifest.json\n(COMPLETED / INTERRUPTED / FAILED)"]
    end

    TB -.->|"Drained under lock"| Drain
```

### Recommended Project Structure

```text
[repo-root]/
├── bootstrap.py                              # External composition root: implements ConcreteSimulationExecutor & injects into ManetApp
├── manet/
│   ├── __main__.py                           # App entry point (imports bootstrap.create_app if present, else ManetApp)
│   ├── app.py                                # ManetApp with supervisor wiring and global quit confirmation
│   ├── adapters/
│   │   ├── execution.py                      # SimulationExecutorProtocol, TelemetrySinkProtocol, TelemetryEvent dataclass
│   │   ├── handoff.py                        # SimulationLaunchRequest [VERIFIED: manet/adapters/handoff.py:10-21]
│   │   ├── workspace.py                      # WorkspaceAdapter + update_manifest_status atomic helper
│   │   └── status.py                         # StatusAdapter wired to WorkloadSupervisor
│   ├── runtime/
│   │   ├── supervisor.py                     # WorkloadSupervisor: state machine, slot management, worker handle
│   │   ├── telemetry.py                      # Synchronized bounded telemetry deque and authentic counters
│   │   └── keymap.py                         # Key constants: BINDING_LIVE_RUN, BINDING_STOP, etc.
│   ├── screens/
│   │   ├── live_run.py                       # LiveRunScreen: reconnectable monitor, progress bar, counters, RichLog
│   │   ├── simulation_workflow.py            # Guided wizard Step 3 wired to app.supervisor
│   │   └── main_workspace.py                 # ActiveWorkloadCard refresh, [L] binding to LiveRunScreen
│   ├── widgets/
│   │   ├── dashboard_cards.py                # ActiveWorkloadCard reflecting real supervisor state
│   │   └── status_bar.py                     # StatusBar reflecting active engine simulation state
│   └── commands/
│       └── registry.py                       # AppCommand entries: 'sim:monitor', 'sim:stop'
├── simulator/
│   └── run_scenario.py                       # SimulationRunner (unchanged API; cooperative stepping hook)
└── tests/
    ├── test_manet_live_run_screen.py         # Headless tests for LiveRunScreen mounting and navigation
    ├── test_manet_supervisor_lifecycle.py    # State machine, slot capacity, cancellation, failure precedence
    ├── test_manet_telemetry_bounded.py       # Deque bounding, overflow tracking, lock synchronization
    └── test_manet_stepping_equivalence.py    # Byte-identical trace equivalence and boundary completion
```

### Pattern 1: External Composition Root & Dependency Injection
**What:** Preserves clean package isolation. `manet/` cannot import `simulator/` (enforced by `test_manet_never_imports_business_packages`), and `simulator/` cannot import `manet/`. An external module `bootstrap.py` at the repo root defines the concrete executor and injects it into `ManetApp(executor=...)`.  
**When to use:** Application entry (`python -m manet` or `python bootstrap.py`) and testing.  
**Example:**
```python
# In manet/adapters/execution.py
from typing import Protocol, Any, Callable
import threading
from manet.adapters.handoff import SimulationLaunchRequest

class SimulationExecutorProtocol(Protocol):
    def execute_simulation(
        self,
        launch_request: SimulationLaunchRequest,
        cancel_token: threading.Event,
        telemetry_sink: Any,
        stage_cb: Callable[[str], None],
        progress_cb: Callable[[float, float], None],
    ) -> dict[str, float]:
        ...

# In bootstrap.py (repo root)
from manet.app import ManetApp
from simulator.run_scenario import SimulationRunner

class ConcreteSimulationExecutor:
    def execute_simulation(self, launch_request, cancel_token, telemetry_sink, stage_cb, progress_cb):
        # Wraps SimulationRunner stepping loop and feeds telemetry_sink
        ...

def create_app(**kwargs) -> ManetApp:
    executor = ConcreteSimulationExecutor()
    return ManetApp(executor=executor, **kwargs)
```

### Pattern 2: Application-Level Workload Supervisor & State Machine
**What:** `WorkloadSupervisor` owns the execution lifecycle, active worker reference, cancellation token, and lifecycle state. Enforces a single active simulation capacity limit while allowing screens to be mounted, unmounted, and switched without affecting the background worker.  
**State Transitions & Precedence:**
- `CONFIGURED` → `RUNNING` → `COMPLETED`
- `CONFIGURED` → `RUNNING` → `STOPPING` → `INTERRUPTED`
- `RUNNING` → `FAILED`
- `STOPPING` → `FAILED`
- **Precedence Order:** `FAILED` > `INTERRUPTED` > `COMPLETED`.

### Pattern 3: Decoupled Bounded Ring-Buffer with UI Batch Drain
**What:** Simulator thread emits events at up to ~70k events/sec. Emitting directly to UI widgets would crash or freeze the event loop. The producer acquires a `threading.Lock`, appends raw data to a `collections.deque(maxlen=500)`, increments authentic counters, and tracks overflow. The UI thread periodically drains up to 100 items per tick, formatting markup outside the lock.  
**When to use:** All live simulation monitoring.

### Pattern 4: SimPy Cooperative Stepping & Virtual-Time Boundary Completion
**What:** To provide responsive cancellation and live telemetry without altering SimPy's deterministic event ordering, the simulation executes via `env.step()` in a cooperative loop. To cleanly advance virtual time to `duration` without executing ordinary events at that boundary:
```python
# Source: verified against simpy.Environment.run source in simpy/core.py:126-170
from simpy.core import StopSimulation, EmptySchedule
from simpy.events import Event, URGENT

until = Event(runner.env)
until._ok = True
until._value = None
runner.env.schedule(until, URGENT, duration - runner.env.now)
until.callbacks.append(StopSimulation.callback)

try:
    while True:
        if cancel_token.is_set():
            break
        runner.env.step()
except StopSimulation:
    pass
except EmptySchedule:
    pass
```
*Empirical verification: produces byte-identical traces to `env.run(until=duration)` across the preset test matrix.*

### Pattern 5: Two-Phase Atomic Manifest Update & Best-Effort Flush
**What:** Ensures simulation result manifests are never corrupted on disk during unexpected cancellation or power interruption. State updates write to `manifest.json.tmp` and replace via `os.replace`.

### Anti-Patterns to Avoid
- **Widget Mutation from Background Thread:** Never call `widget.update()` or `rich_log.write()` from inside the worker thread. Textual widgets are not thread-safe and will cause silent coroutine corruption or deadlocks.
- **Unbounded In-Memory Telemetry Queue:** Never use unbounded `queue.Queue` or infinite lists for live streaming; a 300s run generates 100k+ events and will exhaust heap memory or freeze Textual rendering.
- **Subprocess Spawning for In-Repo Simulator:** Never spawn `subprocess.Popen(["python", "-m", "simulator.run_scenario", ...])` — Windows signal handling cannot gracefully interrupt subprocesses without dropping buffered trace rows.
- **Dynamic Imports to Bypass Package Isolation:** Never use `importlib.import_module("simulator")` inside `manet/` to defeat `test_manet_never_imports_business_packages`. Use composition root dependency injection.
- **Fabricated Progress or ETA:** Never fabricate fake percentage increments or estimated time of arrival (ETA). SimPy virtual time is non-linear; progress is strictly `env.now / duration * 100%`, and elapsed time is monotonic wall-clock seconds.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Thread worker management | Custom `threading.Thread` lifecycle & asyncio bridges | Textual `app.run_worker(..., thread=True, exit_on_error=False)` [VERIFIED: textual.worker.Worker] | Textual manages thread cleanup, error propagation, and application shutdown integration safely. |
| Ring-buffer storage | Custom circular array or list slicing | `collections.deque(maxlen=500)` [VERIFIED: Python stdlib] | Fast O(1) appends with automatic atomic drop-oldest eviction in C. |
| Atomic file writes | Custom file locks or open/truncate writes | `os.replace(temp_path, final_path)` [VERIFIED: Python stdlib] | Guarantees atomic file metadata and content swap on Windows NTFS. |
| Progress display | Custom ASCII progress bars | Textual `ProgressBar(show_eta=False)` [VERIFIED: textual.widgets.ProgressBar] | Smooth terminal rendering with SOC theme palette integration. |
| Streamed log buffer | Custom scrollable text static widgets | Textual `RichLog(max_lines=500, markup=True)` [VERIFIED: textual.widgets.RichLog] | Built-in line capping, auto-scroll, and Rich markup rendering. |

## Common Pitfalls

### Pitfall 1: SimPy Virtual Time Halting Early
**What goes wrong:** A naive stepping loop `while runner.env.peek() < duration: runner.env.step()` produces matching trace rows but halts at the timestamp of the last event before `duration` (e.g. `env.now == 299.82` instead of `300.0`).  
**Why it happens:** Discrete event simulators only advance `env.now` when an event executes. If no event is scheduled at `duration`, virtual time never reaches `duration`.  
**How to avoid:** Explicitly schedule an `URGENT` `until` event at `duration` with `until.callbacks.append(StopSimulation.callback)`, exactly matching `simpy.Environment.run`.  
**Warning signs:** Progress bar stops at 99% on clean completion; metrics calculation divides by partial duration.

### Pitfall 2: High-Frequency Simulator Flooding Textual Event Loop
**What goes wrong:** A fast simulation produces 70,000 events/second. If the simulator thread posts a message to Textual for every event, the asyncio message queue floods, UI freezes completely, and memory spikes by hundreds of megabytes.  
**Why it happens:** Textual message passing has per-message asyncio overhead that cannot sustain 70k msg/sec.  
**How to avoid:** Producer pushes raw events to a bounded `deque(maxlen=500)` under lock and increments integer counters. UI thread polls and drains up to 100 events per 50ms interval.  
**Warning signs:** Application stops responding to keyboard input (`[B]`, `[X]`, `Ctrl+Q`) during simulation run.

### Pitfall 3: Race Condition on Terminal State Precedence
**What goes wrong:** User presses `[X] Stop` just as the simulation reaches `duration`. The worker logs `COMPLETED` instead of `INTERRUPTED`, or finalization fails and logs `COMPLETED` despite corrupt trace output.  
**Why it happens:** Independent completion checks evaluate without strict precedence ordering.  
**How to avoid:** Enforce strict precedence: `FAILED` > `INTERRUPTED` > `COMPLETED`. If an exception occurs, always record `FAILED`. If `cancel_token.is_set()`, always record `INTERRUPTED`. Only record `COMPLETED` if finalization succeeded and no cancellation was requested.  
**Warning signs:** Manifest reports `COMPLETED` for aborted runs or runs with missing trace files.

### Pitfall 4: Mutating Shared Scenario Config Across Screens
**What goes wrong:** Launching a simulation alters dictionary keys (e.g. inserting default IDS parameters or modifying flow endpoints) in the original `SimulationLaunchRequest.config`, affecting subsequent wizard runs.  
**Why it happens:** Python dictionaries are passed by reference across widgets and threads.  
**How to avoid:** Perform `copy.deepcopy(launch_request.config)` in the supervisor before passing to `SimulationRunner`.  
**Warning signs:** Wizard step 2 shows modified parameters after running a scenario.

### Pitfall 5: Broken Packaging Boundaries via Simulator Imports
**What goes wrong:** `tests/test_manet_import_boundaries.py` fails with `Architectural violation (D-12/TUI-02)` because a developer imported `SimulationRunner` inside `manet/runtime/supervisor.py`.  
**Why it happens:** Convenience of direct import rather than dependency injection.  
**How to avoid:** `manet/` must only import abstract protocols (`SimulationExecutorProtocol`). The concrete runner is imported exclusively in `bootstrap.py` (outside `manet/`) and passed to `ManetApp` during construction.  
**Warning signs:** `pytest tests/test_manet_import_boundaries.py` fails with forbidden import error.

## Code Examples

### 1. Concrete Simulation Stepping Executor (in `bootstrap.py`)
```python
# [VERIFIED: tested on e1_normal_30n, e2_blackhole_30n, e4_grayhole_50n seeds 1, 42, 99]
from __future__ import annotations
import copy
from pathlib import Path
import threading
from typing import Any, Callable

import simpy
from simpy.core import EmptySchedule, StopSimulation
from simpy.events import Event, URGENT

from manet.adapters.execution import SimulationExecutorProtocol, TelemetryEvent
from manet.adapters.handoff import SimulationLaunchRequest
from manet.runtime.paths import get_project_root
from simulator.metrics import compute_metrics
from simulator.run_scenario import SimulationRunner

class ConcreteSimulationExecutor:
    """Executes SimulationRunner with cooperative stepping and telemetry hooks."""

    def execute_simulation(
        self,
        launch_request: SimulationLaunchRequest,
        cancel_token: threading.Event,
        telemetry_sink: Any,
        stage_cb: Callable[[str], None],
        progress_cb: Callable[[float, float], None],
    ) -> dict[str, float]:
        stage_cb("INITIALIZING")
        
        # Defensive deepcopy of config
        cfg = copy.deepcopy(launch_request.config)
        
        # Resolve IDS model path relative to project root if relative
        if "ids" in cfg and isinstance(cfg["ids"], dict) and cfg["ids"].get("enabled", False):
            m_path = cfg["ids"].get("model_path")
            if m_path:
                p = Path(m_path)
                if not p.is_absolute():
                    cfg["ids"]["model_path"] = str((get_project_root() / p).resolve())
            iso_path = launch_request.workspace_dir / "isolation_log.json"
            cfg["ids"]["isolation_log_path"] = str(iso_path)

        trace_path = launch_request.workspace_dir / "trace.csv"
        runner = SimulationRunner(
            scenario_config=cfg,
            seed=launch_request.seed,
            out_path=trace_path,
        )
        
        # Attach telemetry callback to runner.log_event
        original_log_event = runner.log_event
        def hooked_log_event(sim_time, src, dst, pkt_id, pkt_type, hop_count, dropped_by=None, node_id=None, speed=None, neighbor_count=None):
            original_log_event(sim_time, src, dst, pkt_id, pkt_type, hop_count, dropped_by, node_id, speed, neighbor_count)
            acting_node = node_id if node_id is not None else src
            telemetry_sink.record_event(
                TelemetryEvent(
                    sim_time=sim_time,
                    src=src,
                    dst=dst,
                    pkt_id=pkt_id,
                    pkt_type=pkt_type,
                    hop_count=hop_count,
                    dropped_by=str(dropped_by) if dropped_by is not None else "",
                    node_id=acting_node,
                    speed=f"{speed:.4f}" if speed is not None else "",
                    neighbor_count=str(neighbor_count) if neighbor_count is not None else "",
                )
            )
        runner.log_event = hooked_log_event

        runner.initialize_nodes()
        runner.initialize_traffic()

        duration = runner.duration
        progress_cb(0.0, duration)
        stage_cb("SIMULATING")

        # Schedule URGENT until event for clean boundary completion
        until = Event(runner.env)
        until._ok = True
        until._value = None
        runner.env.schedule(until, URGENT, duration - runner.env.now)
        until.callbacks.append(StopSimulation.callback)

        step_counter = 0
        try:
            while True:
                if cancel_token.is_set():
                    break
                runner.env.step()
                step_counter += 1
                if step_counter % 200 == 0:
                    progress_cb(runner.env.now, duration)
        except StopSimulation:
            pass
        except EmptySchedule:
            pass

        progress_cb(runner.env.now, duration)
        stage_cb("FINALIZING")

        # Write traces (partial on cancel, full on completion)
        runner.write_traces()
        if runner.online_ids is not None and runner.online_ids.isolation_log_path is not None:
            runner.online_ids.write_isolation_log()

        metrics = compute_metrics(runner.trace_rows, sim_duration=duration)
        return metrics
```

### 2. Workload Supervisor & State Machine (in `manet/runtime/supervisor.py`)
```python
# [VERIFIED: Python enum & threading semantics]
from enum import Enum, auto
import os
import threading
import time
from typing import Any, Callable
from manet.adapters.execution import SimulationExecutorProtocol
from manet.adapters.handoff import SimulationLaunchRequest
from manet.adapters.workspace import update_manifest_status
from manet.runtime.telemetry import TelemetrySink

class WorkloadState(Enum):
    IDLE = auto()
    CONFIGURED = auto()
    RUNNING = auto()
    STOPPING = auto()
    COMPLETED = auto()
    INTERRUPTED = auto()
    FAILED = auto()

class WorkloadSupervisor:
    """Application-level supervisor governing simulation execution and telemetry."""

    def __init__(self, executor: SimulationExecutorProtocol | None = None) -> None:
        self.executor = executor
        self.state = WorkloadState.IDLE
        self.current_request: SimulationLaunchRequest | None = None
        self.cancel_token = threading.Event()
        self.telemetry = TelemetrySink()
        self.worker_handle: Any = None
        self.start_monotonic: float = 0.0
        self.last_error: str | None = None
        self.stage: str = "IDLE"
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self.state in (WorkloadState.RUNNING, WorkloadState.STOPPING)

    def start_simulation(self, request: SimulationLaunchRequest, app: Any) -> None:
        with self._lock:
            if self.is_running:
                raise RuntimeError("A simulation workload is already active.")
            self.current_request = request
            self.cancel_token.clear()
            self.telemetry.reset(request.config.get("duration", 300.0))
            self.state = WorkloadState.RUNNING
            self.stage = "INITIALIZING"
            self.start_monotonic = time.monotonic()
            self.last_error = None
            
            # Atomically update manifest to RUNNING
            update_manifest_status(request.workspace_dir, "RUNNING")

        # Schedule worker at app level
        self.worker_handle = app.run_worker(
            self._worker_entrypoint,
            name=f"sim-{request.experiment_id}",
            group="simulation",
            thread=True,
            exit_on_error=False,
        )

    def cancel_simulation(self) -> bool:
        with self._lock:
            if self.state == WorkloadState.RUNNING:
                self.state = WorkloadState.STOPPING
                self.cancel_token.set()
                if self.current_request:
                    update_manifest_status(self.current_request.workspace_dir, "STOPPING")
                return True
            return False

    def _worker_entrypoint(self) -> None:
        assert self.current_request is not None
        req = self.current_request
        error_exc: Exception | None = None
        metrics: dict[str, float] = {}

        try:
            if self.executor is not None:
                metrics = self.executor.execute_simulation(
                    launch_request=req,
                    cancel_token=self.cancel_token,
                    telemetry_sink=self.telemetry,
                    stage_cb=lambda s: setattr(self, "stage", s),
                    progress_cb=self.telemetry.update_progress,
                )
        except Exception as exc:
            error_exc = exc

        # Terminal state precedence: FAILED > INTERRUPTED > COMPLETED
        with self._lock:
            if error_exc is not None:
                self.state = WorkloadState.FAILED
                self.last_error = str(error_exc)
                self.stage = "FAILED"
                update_manifest_status(req.workspace_dir, "FAILED", error=str(error_exc))
            elif self.cancel_token.is_set():
                self.state = WorkloadState.INTERRUPTED
                self.stage = "INTERRUPTED"
                update_manifest_status(req.workspace_dir, "INTERRUPTED", metrics=metrics)
            else:
                self.state = WorkloadState.COMPLETED
                self.stage = "COMPLETED"
                update_manifest_status(req.workspace_dir, "COMPLETED", metrics=metrics)
```

### 3. Synchronized Bounded Telemetry Sink (in `manet/runtime/telemetry.py`)
```python
# [VERIFIED: collections.deque thread safety & locking]
from collections import deque
from dataclasses import dataclass
import threading
from typing import List

@dataclass(frozen=True)
class TelemetryEvent:
    sim_time: float
    src: int
    dst: int
    pkt_id: int
    pkt_type: str
    hop_count: int
    dropped_by: str
    node_id: int
    speed: str
    neighbor_count: str

@dataclass
class TelemetrySnapshot:
    sim_now: float
    duration: float
    data_sent: int
    data_fwd: int
    data_recv: int
    data_drop: int
    overflow_count: int
    events: List[TelemetryEvent]

class TelemetrySink:
    """Thread-safe bounded ring buffer with atomic counter aggregation."""

    def __init__(self, maxlen: int = 500) -> None:
        self._lock = threading.Lock()
        self._events: deque[TelemetryEvent] = deque(maxlen=maxlen)
        self.maxlen = maxlen
        self.duration = 300.0
        self.sim_now = 0.0
        self.data_sent = 0
        self.data_fwd = 0
        self.data_recv = 0
        self.data_drop = 0
        self.overflow_count = 0

    def reset(self, duration: float) -> None:
        with self._lock:
            self._events.clear()
            self.duration = duration
            self.sim_now = 0.0
            self.data_sent = 0
            self.data_fwd = 0
            self.data_recv = 0
            self.data_drop = 0
            self.overflow_count = 0

    def update_progress(self, sim_now: float, duration: float) -> None:
        with self._lock:
            self.sim_now = sim_now
            self.duration = duration

    def record_event(self, event: TelemetryEvent) -> None:
        with self._lock:
            # Authentic counters
            if event.pkt_type == "DATA_SENT":
                self.data_sent += 1
            elif event.pkt_type == "DATA_FWD":
                self.data_fwd += 1
            elif event.pkt_type == "DATA_RECV":
                self.data_recv += 1
            elif event.pkt_type == "DATA_DROP":
                self.data_drop += 1

            if len(self._events) >= self.maxlen:
                self.overflow_count += 1
            self._events.append(event)
            self.sim_now = event.sim_time

    def drain_batch(self, max_items: int = 100) -> TelemetrySnapshot:
        with self._lock:
            drained = []
            drain_len = min(len(self._events), max_items)
            for _ in range(drain_len):
                drained.append(self._events.popleft())
            return TelemetrySnapshot(
                sim_now=self.sim_now,
                duration=self.duration,
                data_sent=self.data_sent,
                data_fwd=self.data_fwd,
                data_recv=self.data_recv,
                data_drop=self.data_drop,
                overflow_count=self.overflow_count,
                events=drained,
            )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Blocking synchronous run `metrics = runner.run()` | Textual background worker thread `app.run_worker(..., thread=True)` | Textual 0.40+ (stable in 8.2.8) | UI never freezes; frame rate remains 60 FPS; user can background, navigate, or stop run. |
| Subprocess execution with IPC pipes | In-process thread worker + shared synchronized structures | Phase 10 architectural decision | Prevents Windows subprocess signal issues, eliminates serialization overhead, and guarantees trace buffers are not lost on exit. |
| Direct widget writes from worker thread | Synchronized ring buffer + UI periodic drain timer | Textual async architecture pattern | Thread safety guaranteed; zero widget corruption or async event loop deadlock. |
| Naive `while peek() < duration: step()` | Explicit `URGENT` `until` event scheduled at `duration` | Phase 10 stepping equivalence research | Clean boundary completion where `env.now == duration` exactly matches `env.run(until=duration)`. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Textual `RichLog` with batch drain of ≤100 items per 50ms maintains smooth 60 FPS rendering under Windows terminal | Architecture Patterns | Low. Batch size or interval can be adjusted between 50ms and 100ms via agent's discretion if CPU usage spikes on constrained hardware. |
| A2 | Dedicated worker thread avoids Windows file-locking contention with trace writing | Standard Stack | Low. Traces are written to a unique experiment directory under `.manet-workspace/<experiment_id>/` accessed exclusively by the single worker thread. |

*Note: All core simulation stepping equivalence and boundary advancement findings were empirically verified in this session and are tagged [VERIFIED].*

## Open Questions (RESOLVED)

1. **Optimal Periodic Drain Interval for 80x24 Terminals** — RESOLVED:
   - Resolution: Default to 50ms (20Hz) with maximum 100 items per drain batch; fallback to 100ms if reduced motion is enabled.
   - What we know: 50ms (20Hz) provides fluid animation; 100ms (10Hz) conserves CPU.
   - Recommendation: Implemented in `10-02-PLAN.md` with 50ms periodic timer draining up to 100 items into `RichLog(max_lines=500)`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.11.8 | — |
| Textual | TUI & Worker Engine | ✓ | 8.2.8 | — |
| SimPy | Discrete-Event Simulator | ✓ | 4.1.2 | — |
| NetworkX | Topology Graph | ✓ | 3.6.1 | — |
| scikit-learn | ML IDS Classifier | ✓ | 1.8.0 | — |
| pytest | Test Runner | ✓ | 9.0.2 | — |

**Missing dependencies with no fallback:** None  
**Missing dependencies with fallback:** None  

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pytest.ini` (`asyncio_mode = auto`) |
| Quick run command | `python -m pytest tests/test_manet_supervisor_lifecycle.py -x` |
| Full suite command | `python -m pytest tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| **TUI-15** | Non-blocking background worker execution with single-simulation capacity enforcement | Integration | `python -m pytest tests/test_manet_supervisor_lifecycle.py -k "test_single_active_workload_capacity"` | ❌ Wave 0 |
| **TUI-15** | UI responsiveness during simulation execution (screen unmounting/backgrounding) | Headless UI | `python -m pytest tests/test_manet_live_run_screen.py -k "test_background_navigation_preserves_run"` | ❌ Wave 0 |
| **TUI-16** | Honest virtual-time progress, monotonic elapsed timing, and authentic stages | Unit / UI | `python -m pytest tests/test_manet_live_run_screen.py -k "test_authentic_stages_and_progress"` | ❌ Wave 0 |
| **TUI-16** | Bounded telemetry buffer drops oldest events under burst load without blocking simulator | Stress / Unit | `python -m pytest tests/test_manet_telemetry_bounded.py -k "test_bounded_telemetry_under_burst"` | ❌ Wave 0 |
| **TUI-17** | Clean boundary advancement (`env.now == duration`) and stepping equivalence | Integration | `python -m pytest tests/test_manet_stepping_equivalence.py -k "test_stepping_equivalence_preset_matrix"` | ❌ Wave 0 |
| **TUI-17** | Deterministic trace row reproduction between CLI runner and stepped runner | Regression | `python -m pytest tests/test_manet_stepping_equivalence.py -k "test_deterministic_trace_generation"` | ❌ Wave 0 |
| **TUI-18** | Stop protocol halts execution, writes partial traces, and atomically marks manifest INTERRUPTED | Integration | `python -m pytest tests/test_manet_supervisor_lifecycle.py -k "test_cancellation_preserves_partial_traces"` | ❌ Wave 0 |
| **TUI-18** | Terminal state race precedence: FAILED > INTERRUPTED > COMPLETED | Unit | `python -m pytest tests/test_manet_supervisor_lifecycle.py -k "test_terminal_state_precedence"` | ❌ Wave 0 |
| **TUI-18** | Pause button is rendered visually disabled with explicit helper tooltip | Headless UI | `python -m pytest tests/test_manet_live_run_screen.py -k "test_pause_button_disabled"` | ❌ Wave 0 |
| **TUI-02** | Package boundary isolation: `manet/` never imports business packages, and business packages never import `manet/` | AST Invariant | `python -m pytest tests/test_manet_import_boundaries.py` | ✅ (extend for simulator) |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_manet_supervisor_lifecycle.py tests/test_manet_stepping_equivalence.py -x`
- **Per wave merge:** `python -m pytest tests/` (full 187+ test suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_manet_supervisor_lifecycle.py` — covers TUI-15, TUI-18 (state transitions, capacity, cancellation, failure precedence)
- [ ] `tests/test_manet_stepping_equivalence.py` — covers TUI-16, TUI-17 (stepping equivalence against baseline `SimulationRunner.run()`, boundary duration advancement, quiescent queues, IDS inference)
- [ ] `tests/test_manet_telemetry_bounded.py` — covers TUI-16 (bounded deque maxlen=500, overflow tracking, lock synchronization, authentic counters under burst)
- [ ] `tests/test_manet_live_run_screen.py` — covers TUI-15, TUI-16, TUI-18 (headless UI testing of LiveRunScreen, reconnectability, keyboard shortcuts `[B]`, `[X]`, disabled pause button)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | Yes | Defensive `copy.deepcopy(launch_request.config)` prevents cross-screen mutable state tampering; strict path resolution for `model_path` prevents directory traversal. |
| V8 Data Protection | Yes | Atomic manifest persistence via `manifest.json.tmp` + `os.replace` prevents corruption on abrupt shutdown. |
| V11 Business Logic | Yes | Single-active-workload capacity constraint prevents thread race conditions and uncontrolled CPU resource exhaustion. |
| V14 Configuration | Yes | Strict AST boundary tests prevent insecure OS subprocess execution in command handlers or UI presentation layers. |

### Known Threat Patterns for Python Concurrent TUI Applications

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Telemetry Buffer Heap Exhaustion (DoS) | Denial of Service | Bounded ring buffer `collections.deque(maxlen=500)` with drop-oldest eviction ensures constant memory footprint regardless of simulation event volume. |
| Asynchronous Cross-Thread Race Condition | Tampering / Information Disclosure | Synchronization via `threading.Lock` protects telemetry dequeue and counter reads; immutable `SimulationLaunchRequest` dataclass. |
| Partial Trace File Corruption | Tampering | Flushes in-memory trace rows to disk (`write_traces()`) during finalization, accompanied by atomic `os.replace` of manifest status. |
| Accidental Shutdown During Active Simulation | Repudiation / Denial of Service | Intercept global quit (`Ctrl+Q`), prompt for confirmation, and await thread finalization before exiting. |

## Sources

### Primary (HIGH confidence)
- `simulator/run_scenario.py:48-99,560-572` — `SimulationRunner` implementation, trace header, discrete-event loop, and IDS response integration.
- `simpy/core.py:126-170` — SimPy `Environment.run` implementation of `URGENT` until event scheduling and `StopSimulation` callback.
- `manet/adapters/handoff.py:10-21` — `SimulationLaunchRequest` dataclass.
- `manet/adapters/workspace.py:34-56` — Launch manifest recording and workspace directory allocation.
- `manet/adapters/status.py:8-30` — `WorkloadStatus` dataclass and `StatusAdapter`.
- `tests/test_manet_import_boundaries.py:32-52` — AST architectural boundary test enforcing package isolation.
- `manet/screens/simulation_workflow.py:172-240` — Wizard Step 3 confirmation handoff point.

### Secondary (MEDIUM confidence)
- Textual 8.2.8 documentation & source inspection (`textual.worker.Worker`, `textual.widgets.RichLog`, `textual.widgets.ProgressBar`).
- Python standard library documentation (`collections.deque`, `threading.Event`, `threading.Lock`, `os.replace`).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified in local CPython 3.11.8 environment.
- Architecture: HIGH — tested and verified stepping equivalence, bounded telemetry, and AST package isolation.
- Pitfalls: HIGH — empirically identified and verified SimPy boundary completion behavior and terminal race conditions.

**Research date:** 2026-11-08  
**Valid until:** 2026-12-08 (stable local architecture)
