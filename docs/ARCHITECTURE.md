<!-- generated-by: gsd-doc-writer -->
# Architecture Overview

This document provides a comprehensive technical overview of the software architecture, design principles, component interactions, and data flow of the Machine Learning-Based Intrusion Detection and Response System for MANET.

## High-Level Overview

The system is designed as a modular, pure-Python architecture replacing heavyweight C++ network simulators (such as NS-3) with a lightweight, deterministic discrete-event engine based on SimPy and NetworkX, paired with Scikit-learn machine learning classifiers and a Textual 8.2.8 Interactive Terminal UI.

The system operates across three primary tiers:

1. **Discrete-Event Simulation & Attack Injection Tier (`simulator/`, `attacks/`):**
   Executes RFC 3561 Ad hoc On-Demand Distance Vector (AODV) routing over 2D Random Waypoint mobility and unit-disk radio propagation. Decoupled attack strategies (Blackhole and Grayhole) are dynamically injected at runtime at the composition root without contaminating core protocol code.

2. **Feature Engineering & Machine Learning Tier (`feature_extraction/`, `ml/`):**
   Transforms discrete packet event traces into non-leaking sliding-window tabular features. Partitions datasets strictly by seed/scenario (zero random-row leakage), tunes cost-sensitive classifiers under a locked False Positive Rate gate ($\text{FPR} \le 1.0\%$), and executes closed-loop mitigation via `OnlineIDS` with two-strike confirmation and route invalidation.

3. **Interactive Terminal UI Presentation Tier (`manet/`, `bootstrap.py`):**
   A full-screen, keyboard-first operational flight deck (`python -m manet`, app name `MANET IDS`) built with Textual 8.2.8. Features real-time simulation progress monitoring, scenario configuration wizards, post-run QoS scorecards, manifest inspect views, and safe workspace pruning.

---

## System Component Diagram

```mermaid
graph TD
    subgraph Presentation_Layer [TUI Presentation Layer - manet/ (Textual 8.2.8)]
        MainWorkspace[screens/main_workspace.py - Flight Deck]
        Wizard[screens/simulation_workflow.py - 3-Step Wizard]
        LiveRun[screens/live_run.py - SOC Monitor]
        Results[screens/results.py - QoS Scorecard]
        History[screens/history.py - Manifest Ledger]
        Adapters[adapters/ - Workspace, Diagnostics, Scenario]
        MainWorkspace --> Adapters
        Wizard --> Adapters
        LiveRun --> Adapters
        Results --> Adapters
        History --> Adapters
    end

    subgraph Composition_Bridge [Composition Root - Repo Root]
        Bootstrap[bootstrap.py - ConcreteSimulationExecutor]
        Adapters -. Bridge Protocol .-> Bootstrap
    end

    subgraph Discrete_Event_Simulator [Simulator Core - SimPy & NetworkX]
        Mobility[mobility.py - Random Waypoint] --> Topology[radio.py - Euclidean Radio Graph]
        Traffic[traffic.py - CBR/UDP Application Flows] --> AODV[aodv.py - RFC 3561 AODV Protocol]
        Topology --> AODV
        Bootstrap --> AODV
    end

    subgraph Adversarial_Injection [Attacks Module - Decoupled]
        StrategyRegistry[registry.py - Factory Registry] --> BH[blackhole.py - BlackholeStrategy]
        StrategyRegistry --> GH[grayhole.py - GrayholeStrategy]
        BH -. Hook Injected .-> AODV
        GH -. Hook Injected .-> AODV
    end

    subgraph Telemetry_And_Features [Telemetry & Feature Pipeline]
        AODV --> TraceLogger[run_scenario.py - 10-Column Trace Logger]
        TraceLogger --> RawTraces[(traces/*.csv or .manet-workspace/)]
        RawTraces --> FeatureExtractor[extract_features.py - Sliding Extractor]
        FeatureExtractor --> Dataset[(data/train.csv & data/test.csv)]
    end

    subgraph Machine_Learning [ML Engine - Scikit-learn]
        Dataset --> MLTrainer[train.py - 5-Fold Stratified CV Tuning]
        MLTrainer --> ChampionModel[(ml/models/best_model.joblib)]
        ChampionModel --> Evaluator[evaluate.py - Security Metric Evaluator]
    end

    subgraph Closed_Loop_Mitigation [Closed-Loop Response Engine]
        ChampionModel --> OnlineIDS[response.py - OnlineIDS Controller]
        AODV -. Packet Events .-> OnlineIDS
        OnlineIDS -. Two-Strike Confirmed Isolation .-> AODV
    end
```

---

## Architectural Separation of Concerns & AST Boundary Enforcement

The codebase strictly enforces clean layer separation via static AST (`ast.parse`/`ast.walk`) test suites (`tests/test_manet_import_boundaries.py` and `tests/test_import_boundaries.py`):

1. **One-Way Presentation Boundary (D-12, TUI-02):**
   - The `manet/` package is a pure presentation layer. It **NEVER** imports from business logic packages (`simulator`, `attacks`, `feature_extraction`, `ml`).
   - Business packages never import `manet/`.
   - The composition root `bootstrap.py` exists only at the repository root and serves as the sole bridge wiring `manet` to the underlying simulator and ML pipeline.
2. **Command Package Safety (D-10, T-7-01):**
   - `manet/commands/` never imports OS execution primitives (`subprocess`, `shutil`, `os`). All operational commands are routed through internal application handlers.
3. **Decoupled Attack Strategies:**
   - `simulator/` core modules never import from `attacks/`.
   - `simulator/run_scenario.py` and `bootstrap.py` act as the only sanctioned composition roots where adversarial strategies are injected via dynamic duck-typed hooks (`recv_rreq_hook`, `forward_data_hook`).
   - `attacks/` never imports from `simulator/`.

---

## Presentation Layer Architecture (`manet/`)

The presentation layer is structured into 6 focused subpackages:

1. **`manet/adapters/` (10 modules):**
   Provides one-way data models and interfaces between Textual widgets and the underlying file system or simulation runner. Includes `diagnostics.py`, `execution.py`, `handoff.py`, `navigation.py`, `notifications.py`, `scenario.py`, `simulation_config.py`, `status.py`, and `workspace.py`.
2. **`manet/screens/` (9 modules):**
   Textual screen containers designed for an 80×24 minimum geometry:
   - `main_workspace.py`: Operational flight deck with Executive Grid cards.
   - `simulation_workflow.py`: 3-step configuration and pre-flight validation wizard.
   - `live_run.py`: Real-time SOC monitor with virtual-time progress tracking and live packet counters.
   - `results.py`: Post-simulation QoS scorecard and trace inspector.
   - `history.py`: Experiment history browser with manifest validation.
   - `prune_modal.py`: Confirmation modal for safe workspace pruning.
   - `console.py`: In-app telemetry log viewer.
   - `help_about.py`: Keyboard shortcuts and system documentation viewer.
3. **`manet/widgets/` (9 modules):**
   Reusable UI components: executive status cards, QoS scorecard, navigation rails, recent experiments table, notification toast rails, and wizard step panes.
4. **`manet/runtime/` (6 modules):**
   Runtime facilities: `telemetry.py` (bounded thread-safe ring-buffer), `supervisor.py` (background thread worker coordinator), `settings.py` (in-memory session display toggles), `theme.py` (SOC dark palette and high-contrast modes), `paths.py` (centralized path resolution), and `keymap.py` (global keybindings).
5. **`manet/commands/` (4 modules):**
   Command palette registry, search filtering, and action dispatchers.
6. **`manet/app.py` & `manet/__main__.py`:**
   Application initialization, keymap registration, screen stack management, and CLI launcher.

---

## Execution Mechanisms: CLI vs In-Process Stepping

The system supports two distinct execution modes:

### 1. Batch Subprocess Runner (`SimulationRunner`)
- Executed via `python -m simulator.run_scenario --scenario <json> --seed <int> --out <dir>`.
- Runs the SimPy event loop (`env.run(until=duration)`) to completion in a dedicated process.
- Outputs complete CSV traces and emits stdout metric summaries.

### 2. Cooperative In-Process Stepping Engine (`ConcreteSimulationExecutor`)
- Implemented in `bootstrap.py` for background TUI execution without GUI thread freezing.
- Executes SimPy stepping using micro-intervals (`env.run(until=next_step)`), feeding intermediate progress and packet events into the synchronized ring buffer.
- **Byte-Identical Trace Parity:** Formally proven in `tests/test_manet_stepping_equivalence.py` to yield byte-for-byte identical packet event traces and exact metric parity with the batch runner across preset scenarios and seeds (1, 42, 99).

---

## Telemetry & Workspace Manifest Pipeline

### 1. Bounded Thread-Safe Telemetry Sink (`TelemetrySink`)
- Synchronized ring buffer (`collections.deque(maxlen=500)`) with drop-oldest eviction.
- Tracks cumulative packet counters (`DATA_SENT`, `DATA_FWD`, `DATA_RECV`, `DATA_DROP`, `OVERFLOW`) across dropped frames.
- Drains immutable batch snapshots for 20Hz UI rendering without lock contention.

### 2. Atomic Workspace Manifests (`WorkspaceAdapter`)
- Every simulation executed via the TUI generates a unique experiment directory in `.manet-workspace/<experiment_id>/`.
- Directory contents:
  - `scenario.json`: Snapshot of the configuration used.
  - `trace.csv`: Full 10-column packet event log.
  - `manifest.json`: Atomic metadata record containing:
    - Experiment metadata (`experiment_id`, `run_tag`, timestamps, run type).
    - Status (`RUNNING`, `COMPLETED`, `INTERRUPTED`, `FAILED`).
    - Computed QoS scorecard (PDR, throughput, delay, routing overhead).
    - SHA-256 checksums of all generated artifacts for tamper detection.
    - IDS isolation logs (if enabled).

---

## Data Flow & Event Lifecycles

### 1. Packet Event Logging
All node packet events (`SEND`, `RECV`, `FWD`, `DROP`, `DATA_DROP`, `RREQ_DROP`) and periodic node state rows (`NODE_STATUS`) are appended to a CSV trace with a 10-column canonical schema:
`time, src, dst, pkt_id, type, hop_count, dropped_by, node_id, speed, neighbor_count`

### 2. Sliding-Window Feature Extraction
1. `feature_extraction/extract_features.py` divides the simulation duration into overlapping sliding windows $[t - W, t]$ with step size $S$ (default: $W = 10.0\text{ s}, S = 2.0\text{ s}$).
2. Backward aggregation computes 9 non-leaking behavioral features:
   - `packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`, `neighbor_count`, `mobility_speed`.
3. Anti-Leakage Protocol: Feature matrix $X$ contains zero identity tags, coordinate positions, or oracle flags. Changing ground-truth attack labels leaves $X$ 100% numerically invariant.

### 3. Closed-Loop Online Mitigation
1. Packet events stream to `OnlineIDS`.
2. Every $\Delta t = 5.0\text{ s}$, `OnlineIDS.step()` infers node behaviors through the champion classifier.
3. **2-Strike Confirmation:** Malicious classification must persist for 2 consecutive windows before isolation triggers.
4. **Route Invalidation:** Quarantined nodes are silenced from RREPs/RREQs, and all routing entries routing through the attacker are expunged.
5. **Quarantine Decay:** Quarantined nodes remain isolated for 30.0s before probationary reintegration.

---

## Key Abstractions

| Class / Component | Module Path | Responsibility |
|---|---|---|
| `ManetApp` | [manet/app.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/manet/app.py) | Full-screen Textual application shell, screen routing, and keybindings. |
| `ConcreteSimulationExecutor` | [bootstrap.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/bootstrap.py) | Composition root bridging TUI to simulator; in-process SimPy stepping engine. |
| `WorkloadSupervisor` | [manet/runtime/supervisor.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/manet/runtime/supervisor.py) | Background worker thread coordinator, lifecycle state transitions. |
| `TelemetrySink` | [manet/runtime/telemetry.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/manet/runtime/telemetry.py) | Synchronized bounded ring-buffer for high-throughput UI decoupling. |
| `WorkspaceAdapter` | [manet/adapters/workspace.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/manet/adapters/workspace.py) | Experiment workspace directory management, atomic manifests, SHA-256 checks. |
| `SimulationRunner` | [simulator/run_scenario.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/simulator/run_scenario.py) | Scenario orchestrator, SimPy environment lifecycle, strategy injector, and trace recorder. |
| `AodvNode` | [simulator/aodv.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/simulator/aodv.py) | RFC 3561 AODV protocol implementation with sequence numbers, routing table expiry, and blacklist hook. |
| `OnlineIDS` | [ml/response.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/ml/response.py) | Real-time sliding window controller with 2-strike confirmation and quarantine route invalidation. |
