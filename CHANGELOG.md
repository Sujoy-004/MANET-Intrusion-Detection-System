# Changelog

All notable changes to the Machine Learning-Based Intrusion Detection System for MANET will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Python 3.13 Fresh-Clone Bootstrap Failure:** Bumped the `numpy` pin from `1.26.4` to `2.3.3` in `requirements.txt` (mirrored in `scripts/verify_environment.py`). numpy 1.26.4 ships no CPython 3.13+ wheels, so `pip install -r requirements.txt` aborted during a Meson source build on wheel-less interpreters, leaving the entire environment untouched (`simpy`/`textual` absent, all pinned packages drifted, CLI/TUI entrypoints failing on `No module named 'simpy'`). numpy 2.3.3 provides wheels for CPython 3.11-3.14 and satisfies pandas 3.0.2's `numpy>=2.3.3` floor on Python >= 3.14.

## [2.0.0] - 2026-11-11

### Added
- **Milestone v2.0: Interactive Terminal UI (TUI) Application:**
  - **Full-Screen TUI Presentation Layer (`python -m manet`, app name `MANET IDS`):** Pure presentation framework built with Textual 8.2.8, completely decoupled from core business logic via AST import boundary gates.
  - **Executive Operational Flight Deck (`MainWorkspace`):** Status cards for system diagnostics, ML model readiness, active workload state, and quick CTA actions.
  - **Scenario Configuration Wizard (`SimulationWorkflowScreen`):** 3-step interactive wizard with preset scenario loading, parameter editing, and two-tier structural validation.
  - **Live Run Monitor (`LiveRunScreen`):** Real-time 80x24 SOC dark monitor with SimPy virtual-time progress tracking `[0.0, 100.0]%`, wall-clock elapsed timer, authentic packet counters (`SENT`, `FWD`, `RECV`, `DROP`, `OVERFLOW`), throttled 20Hz RichLog streaming, and safe cooperative cancellation `[X]`.
  - **Results & QoS Scorecard (`ResultsScreen`):** Post-run evaluation screen displaying delivery metrics (PDR, throughput, delay, routing overhead), color-coded threshold badges, raw packet trace viewers, and isolation event ledgers.
  - **Experiment Records & Workspace (`HistoryScreen`):** History browser listing past runs stored in `.manet-workspace/`, manifest inspect views with SHA-256 checksum validation, and safe workspace pruning modal (`[D]`).
  - **Diagnostics Probe (`DiagnosticsCard`):** Real-time system health card displaying Python version, dependency checks, model artifact paths, and active process metrics.
  - **Command Palette (`[Ctrl+P]`):** Searchable command launcher for jumping to any screen, toggling settings, or triggering actions.
  - **In-Process Stepping Engine (`bootstrap.py`):** In-process cooperative SimPy stepping execution via `ConcreteSimulationExecutor` with exact `until` boundary event scheduling, defensive configuration deep copies, and verified byte-identical trace parity against baseline `SimulationRunner.run()` across preset scenarios and seeds (1, 42, 99).
  - **Bounded Telemetry Sink (`manet/runtime/telemetry.py`):** Multi-threaded synchronized ring-buffer (`maxlen=500`) with drop-oldest overflow discarding, atomic counter preservation across evictions, and immutable batch draining for UI decoupling.
  - **Safe Exit & Shutdown Guard:** Integrated `QuitConfirmModal` intercepting `Ctrl+Q` during active runs, asynchronous non-blocking shutdown polling, and `ShutdownErrorModal` for finalization failure diagnostics with dismiss and force exit controls.
  - **Standardized Dependency Packaging (`requirements.txt`):** Pinned exact versions for all 10 project dependencies (`simpy==4.1.2`, `networkx==3.6.1`, `scikit-learn==1.8.0`, `pandas==3.0.2`, `numpy==1.26.4`, `matplotlib==3.10.8`, `seaborn==0.13.2`, `joblib==1.5.3`, `textual==8.2.8`, `pytest==9.0.2`).
  - **On-Demand Environment Verification (`scripts/verify_environment.py`):** Verification script checking Python >= 3.11, exact dependency pins, artifact existence, and CLI entry points (`run_scenario`, `ml.train`, `ml.evaluate`, `manet`).
  - **Hermetic Test Isolation Fixture (`tests/conftest.py`):** Autouse `tmp_path` fixture patching `WorkspaceAdapter` to prevent test runs from polluting real experiment workspaces.
  - **Subprocess CLI Compatibility Harness (`tests/test_legacy_cli_compat.py`):** Subprocess regression suite ensuring all pre-existing CLI commands maintain exact exit codes, stdout schemas, and trace parity.
  - **AST Import Boundary Enforcement (`tests/test_manet_import_boundaries.py` & `tests/test_import_boundaries.py`):** Static code boundary tests enforcing that `manet/` never imports business packages, `manet/commands/` never imports OS execution primitives, and `simulator/` never imports `attacks/`.
  - Total automated test suite expanded to **293 collected tests across 38 modules** (**290 passed, 3 expected symlink skips, 0 failures**).

### Fixed
- **Phase 10 Audit Findings & Execution Hardening:**
  - **Terminal State Contract (`WorkloadSupervisor`):** Published `COMPLETED` and `INTERRUPTED` states only after trace, isolation log, and manifest updates succeed on disk; manifest write failures transition supervisor state and stage truthfully to `FAILED` with actionable `last_error` diagnostics.
  - **Initialization & Stepping Error Protection (`ConcreteSimulationExecutor`):** Expanded protected execution region to encompass node and traffic initialization after runner construction, ensuring partial `trace.csv` and configured IDS isolation logs persist on disk upon simulated failure without test subclasses.
  - **Truthful Dashboard IDS Protection & Metrics Preview (`ActiveWorkloadCard`):** Derived IDS protection dynamically from `supervisor.current_request.ids_enabled` across all states; added E2E delay (`avg_delay_s`) alongside PDR and throughput in completed run preview.
  - **Status Bar Terminal Experiment ID (`StatusBar`):** Rendered the last run's experiment ID and terminal state (`COMPLETED`, `INTERRUPTED`, `FAILED`) using authentic `WorkloadStatus` data.
  - **Launch Lifecycle Parity (`SimulationWorkflowScreen`):** Wired `prepare_simulation()` prior to `start_simulation()`, enforcing the documented `IDLE -> CONFIGURED -> RUNNING` contract and preventing deceptive screen transitions on launch failure.
  - **Fail-Fast Bootstrap Guard (`manet/__main__.py`):** Replaced hidden stderr-only warning with explicit stderr error and exit code 1 if `bootstrap.py` fails to load.
- **Phase 9 Simulation Workflow Hardening:**
  - **CR-01 (Duplicate Scenario IDs):** Enforced deterministic first-match deduplication in `ScenarioAdapter.list_presets()` with diagnostic warning logging; defused `DuplicateKey` crashes in `StepModeSelectWidget` DataTable with unique row keys.
  - **CR-02 (Run Tag Sanitization Boundary):** Updated `sanitize_run_tag()` to strip leading/trailing dots and underscores both before and after 32-character truncation, eliminating Windows on-disk folder name and manifest `experiment_id` divergence.
  - **WR-01 (Wizard Re-Entry State):** Configured `SimulationWorkflowScreen` to automatically reset to Step 1 on workflow completion and screen re-entry.
  - **WR-02 (Workspace Allocation Resilience):** Wrapped experiment directory allocation and manifest generation in specific `(OSError, ValueError)` handlers with safe best-effort cleanup of incomplete newly allocated directories.
  - **WR-03 (Mobility Speed Ordering Invariant):** Enforced `min_speed < max_speed` in Tier 2 structural invariant validator and Step 2 submit validation.
  - **WR-04 (Preset Flow Mutation Transparency):** Removed silent coercion of preset flow endpoints to 0 or `nodes - 1`, blocking advance with explicit identification of offending flows when node count is reduced below preset requirements.
  - **WR-05 (Workspace Destination Preview):** Updated Step 3 workspace preview to honor injected `workspace_root`.
  - **WR-06 (Diagnostics Periodic Refresh Test):** Replaced vacuous pause in `test_periodic_diagnostics_refresh_timer` with deterministic assertion of the 4.0s timer interval.
  - **IN-01..IN-06 (Hygiene, API & Portability):** Removed all unused imports across `manet/`; narrowed broad `except Exception` blocks; replaced private `_installed_screens` with public API; added direct tests for parameterized commands; centralized repository root in `manet/runtime/paths.py`.

## [1.1.0] - 2026-11-03

### Added
- **AODV Route Discovery Recovery Lifecycle:** Per-destination route discovery state machine (`DiscoveryState`) in `simulator/aodv.py` supporting:
  - Initial wait timeout (`DEFAULT_RREQ_TIMEOUT = 2.0s`).
  - Bounded retries (`DEFAULT_RREQ_RETRIES = 2`, representing 3 total discovery attempts).
  - Exponential backoff multiplier (`DEFAULT_BACKOFF_MULT = 2.0`, scaling timeouts: 2s -> 4s -> 8s; no separate `MAX_RREQ_TIMEOUT` constant).
  - Discovery cooldown period (`DEFAULT_DISCOVERY_COOLDOWN = 2.0s`) after retry exhaustion to suppress RREQ broadcast storms.
- **Timer-Generation Token Protection:** Generation token tracking (`timer_token`) for SimPy discovery timeout callbacks, ensuring stale or late RREP callbacks do not interfere with subsequent route discovery cycles.
- **Bounded Packet Buffering & TTL:** Enforced per-destination queue limit (`DEFAULT_MAX_BUFFER_PER_DEST = 100` packets) and packet Time-To-Live expiration (`DEFAULT_MAX_BUFFER_TIME = 20.0s`) to prevent unbounded memory growth during persistent topological partitions.
- **Quarantine Local Egress Guard:** Explicit self-blacklisting check in `handle_rreq()` preventing quarantined nodes from locally constructing or transmitting RREPs.
- **Dedicated Recovery Test Suite:** 10 new unit and integration tests in `tests/test_aodv_recovery.py` covering timeout backoff, cooldown, partition recovery, queue limits, late RREPs, quarantine egress guards, and storm elimination (bringing test suite total to 79 passed tests).

### Changed
- **AODV Buffer Flushing Semantics:** Buffered packets are released only when a valid, non-blacklisted route is confirmed installed; rejected blacklisted RREPs no longer clear legitimate pending discovery state.
- **Documentation & Benchmark Provenance:** Updated `README.md`, `docs/ARCHITECTURE.md`, `docs/CONFIGURATION.md`, `docs/GETTING-STARTED.md`, `docs/TESTING.md`, `docs/DEVELOPMENT.md`, `docs/FINAL_PROJECT_REPORT.md`, and `results/closed_loop_report.md` to reflect:
  - Verified 300-second Seed-42 reference benchmark:
    - Baseline Normal: PDR 65.88% (4,098 / 6,220), throughput 55.95 kbps, delay 134.74 ms across 4,098 delivered packets, overhead 0.0950.
    - Blackhole Attack: PDR 18.10% (1,126 / 6,220), throughput 15.37 kbps, delay 138.66 ms across 1,126 delivered packets, overhead 0.1055.
    - Blackhole + IDS: PDR 62.93% (3,914 / 6,220), throughput 53.44 kbps, delay 102.29 ms across 3,914 delivered packets, overhead 0.1302.
    - Net Restoration: 95.51% baseline delivery restored (3,914 / 4,098 packets), +44.82 percentage points absolute PDR improvement over attack.
    - Delay Interpretation: Clarified that delay is computed exclusively over successfully delivered packets; removed unsupported causal latency claims.
  - Total automated test count updated from 69 to 79 across 11 test modules.

### Fixed
- **Permanent Route Discovery Stalls:** Resolved issue where flows experiencing initial unreplied RREQs during temporary topological partitions permanently retained stale pending state without retrying.
- **Blacklisted RREP Storm Loop:** Eliminated scenario runner loop where rejected blacklisted RREPs repeatedly cleared pending discovery state and flushed unrouted buffers, previously generating over 16,000 rogue control packets.
- **Quarantined Node RREP Generation:** Silenced quarantined nodes from generating and transmitting local RREPs when receiving RREQs destined to themselves.

## [1.0.0] - 2026-10-28

### Added
- Pure-Python discrete-event MANET simulator (SimPy 4.1.2 + NetworkX 3.6.1) implementing RFC 3561 AODV routing and Random Waypoint mobility.
- Decoupled adversarial strategies: Blackhole (sequence spoofing and unconditional drop) and Grayhole (probabilistic/selective drop).
- Non-leaking 10-column sliding-window feature extractor.
- Cost-sensitive Scikit-learn classification pipeline (Random Forest champion, FPR <= 1.0% operational gate).
- Closed-loop `OnlineIDS` controller with 2-strike confirmation and dynamic route invalidation (`invalidate_routes_through`).
- Initial automated test suite and publication-grade visualization suite.
