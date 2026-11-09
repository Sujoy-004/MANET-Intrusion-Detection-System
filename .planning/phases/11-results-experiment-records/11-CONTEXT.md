# Phase 11: Results & Experiment Records - Context

**Gathered:** 2026-11-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 11 delivers completed-run results exploration and verifiable experiment records within the `manet/` TUI application. It provides:
1. A rich Results Screen displaying actual QoS metrics (PDR, throughput, delay, routing overhead) computed via `simulator.metrics.compute_metrics`, alongside sent/received packet counts and generated trace locations (TUI-19).
2. Atomic experiment manifests recording experiment ID, configuration, seed, software version, run status, timestamps, logs, trace paths, and metrics, complemented by SHA-256 checksums computed for payload artifacts (`trace.csv` and `isolation_log.json`) upon run completion (TUI-20).
3. A Session History browser enabling users to explore past experiments, sort/filter runs, inspect detailed results, and verify artifact integrity on-demand, while enforcing read-only metadata protection (reruns create new runs) (TUI-21).
4. Safe workspace storage management ensuring generated artifacts are ignored by Git without changing `.gitignore` semantics unintentionally, and an interactive run pruning capability gated by an itemized preview confirmation modal before physical disk deletion (TUI-21).

Phase 11 does NOT implement live ML model retraining (deferred TUI-MLWORK), simulator pause/resume checkpointing (deferred TUI-PAUSE), or multi-scenario comparative chart plotting (deferred VIZ-01).

</domain>

<decisions>
## Implementation Decisions

### Results Screen Layout & Exploration Depth
- **D-01:** Hybrid Split-Pane Architecture:
  - Top Pane (Fixed QoS Scorecard): Permanently displays the four primary academic MANET QoS metrics:
    - Packet Delivery Ratio (PDR, formatted as percentage and ratio);
    - Throughput (kbps / bps);
    - Average End-to-End Delay (seconds / milliseconds);
    - Routing Overhead (normalized routing packets per data packet sent);
    - Supplementary counters: `data_sent`, `data_received`, and `routing_packets`.
  - Lower Pane (Tabbed Detail Inspector via Textual `TabbedContent`):
    - **Tab 1: Artifacts & Integrity**: Displays absolute and relative generated trace paths (`trace.csv`), SHA-256 checksum, file size, row count, and live integrity verification status badge ("Verified" / "Corrupted" / "Missing").
    - **Tab 2: Security & Isolation Log**: If online IDS was active, displays the roster of flagged and isolated malicious nodes (Blackhole/Grayhole), isolation timestamps, and detection reason. If IDS was disabled or no nodes were isolated, displays an honest empty state indicator.
    - **Tab 3: Configuration & Execution**: Full experiment launch parameters (scenario name, seed, node count, duration, radio range, speed), software version, timestamps (created, started, completed), run status, and supervisor execution log excerpt.
  — **Reversibility:** costly — anchors screen structure, widget composition, and tab navigation.

### Session History & Past Run Browser
- **D-02:** Hybrid Two-Tier Navigation Pattern:
  - Preserves the existing compact `RecentExperimentsTable` on `MainWorkspace` (lower split panel) for glanceable recent run status.
  - Selecting a row in `RecentExperimentsTable` and pressing `[Enter]`, or pressing the global shortcut `[R]` (`BINDING_RESULTS`), opens the dedicated full-screen `HistoryScreen`.
  - `HistoryScreen` features:
    - Search and filter controls (filter by run status: `COMPLETED`, `INTERRUPTED`, `FAILED`; filter by scenario name or tag).
    - Sortable columns: Run ID, Scenario, Seed, Status, PDR, Timestamp.
    - Navigation: `[Enter]` opens the selected run in `ResultsScreen`; `[Esc]` or `[B]` returns to `MainWorkspace`.
    - Live synchronization: newly completed runs are reflected in the history browser and dashboard table without requiring application restart.
  — **Reversibility:** costly — defines navigation routing between `MainWorkspace`, `HistoryScreen`, and `ResultsScreen`.

### Artifact Integrity & Checksum Verification
- **D-03:** Lazy Verification on Open:
  - At run finalization (`WorkloadSupervisor` / `ConcreteSimulationExecutor` completion stage), SHA-256 checksums are calculated for primary generated payload artifacts (`trace.csv` and `isolation_log.json` when present) and stored atomically in `manifest.json` under an `artifacts` mapping (including filename, relative path, byte size, and sha256).
  - `manifest.json` is not hashed into itself to avoid circular hash recursion.
  - When a user opens an experiment in `ResultsScreen`, the application performs on-demand lazy recalculation of artifact hashes in the background/worker to display a clear visual integrity badge:
    - `[green]VERIFIED[/]` — Hash matches manifest record exactly;
    - `[bold red]CORRUPTED / TAMPERED[/]` — File content has been modified since run finalization;
    - `[yellow]MISSING[/]` — File referenced in manifest is no longer present on disk.
  - History list scanning remains fast and responsive on Windows by deferring SHA-256 recalculation to run inspection time.
  — **Reversibility:** reversible — modular hash calculation and verification functions in `manet/adapters/workspace.py`.

### Workspace Storage & Safe Cleanup Protocol
- **D-04:** Interactive Pruning with Preview Confirmation Modal:
  - Read-Only Invariant: Past experiment metadata and manifests are strictly read-only; re-running an experiment always allocates a distinct, new timestamped directory (`exp_YYYYMMDD_HHMMSS_<scenario>_<seed>`).
  - Git Isolation: Experiment directories under `.manet-workspace/` remain strictly ignored by Git via existing `.gitignore` patterns without modifying gitignore semantics.
  - Safe Pruning Workflow:
    - In `HistoryScreen`, users can trigger cleanup with shortcut `[D]` (Delete Run).
    - An explicit, un-dismissible modal dialog (`PruneConfirmationModal`) appears displaying:
      - Target run ID and directory path;
      - Itemized list of files to be removed (`trace.csv`, `manifest.json`, `isolation_log.json`);
      - Total disk space to be reclaimed (formatted in KB / MB).
    - Requires explicit keyboard confirmation (`[Enter]` Confirm / `[Esc]` Cancel) before physical filesystem deletion.
    - Robust Windows file handle safety: verifies all handles are released before deleting directory; graceful error handling if Windows locks a file.
  — **Reversibility:** costly — introduces modal screen and filesystem deletion operations.

### Clean Package Architecture & Adapter Boundary
- **D-05:** Preservation of Package Isolation Invariants:
  - `test_manet_never_imports_business_packages` remains strictly unweakened. Modules under `manet/` must never import `simulator`, `attacks`, `feature_extraction`, or `ml`.
  - Metrics computation (`simulator.metrics.compute_metrics`) is invoked by the stepping executor in `bootstrap.py` upon simulation completion and persisted in `manifest.json`.
  - The results and history screens read all metrics, configuration, and artifact metadata directly from `manifest.json` via `manet/adapters/workspace.py` without importing simulation modules.
  — **Reversibility:** one-way — core architectural invariant established in v2.0 roadmap and enforced by CI test suites.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/ROADMAP.md` § Phase 11 — [Phase 11 goals, success criteria, and requirement mappings]
- `.planning/REQUIREMENTS.md` § TUI-19, TUI-20, TUI-21 — [Executable requirements for metrics, manifests, and history]

### Existing Code & Architecture
- `simulator/metrics.py` — [Canonical `compute_metrics` and `NetworkMetrics` implementation]
- `manet/adapters/workspace.py` — [Workspace inspection, `ExperimentSummary`, manifest reading, directory allocation]
- `manet/runtime/supervisor.py` — [Execution lifecycle, terminal workload states, and manifest update points]
- `manet/screens/main_workspace.py` — [Dashboard layout, `RecentExperimentsTable`, and `action_results` placeholder]
- `manet/widgets/recent_experiments.py` — [Existing DataTable widget for recent runs]
- `bootstrap.py` — [Top-level composition root connecting simulation stepping and metrics computation to `ManetApp`]
- `tests/test_tui_architecture.py` — [Architectural tests verifying package isolation]

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `manet.adapters.workspace.WorkspaceAdapter`: Already provides `list_recent_experiments()`, `allocate_experiment_directory()`, `record_launch_manifest()`, and `update_manifest_status()`. Can be extended to read full manifest details, compute/verify SHA-256 checksums, and safely delete runs.
- `manet.widgets.recent_experiments.RecentExperimentsTable`: Reusable DataTable component already mounted on `MainWorkspace` displaying past runs.
- `manet.runtime.keymap`: Contains `BINDING_RESULTS = "r"`, currently mapped to a placeholder notification on `MainWorkspace`.
- `simulator.metrics.compute_metrics`: Computes standard dictionary containing `pdr`, `throughput_bps`, `avg_delay_s`, `packet_loss_ratio`, `routing_overhead`, `data_sent`, `data_received`, `routing_packets`.

### Established Patterns
- Reactive screens in `manet/screens/` with dedicated `.tcss` styling and keyboard shortcut bindings (`Binding("escape", "app.pop_screen", "Back")`).
- Atomic manifest writing via `tmp_path` + `os.replace` to prevent corrupted state on interruption or power loss.
- Sanitized strings via `rich.markup.escape()` to prevent markup injection in dynamic text widgets.

### Integration Points
- `manet/screens/main_workspace.py`: Replace `action_results()` notification with push to `HistoryScreen` or `ResultsScreen`.
- `manet/screens/live_run.py`: When a simulation run reaches `COMPLETED`, provide a direct button/shortcut `[V] View Results` transitioning directly to `ResultsScreen` for the finished experiment.
- `manet/commands/registry.py`: Register commands `view:results` and `view:history` in the command palette.

</code_context>

<specifics>
## Specific Ideas

- The Results Screen layout should look like an authentic academic network evaluation report: a prominent QoS Scorecard grid at the top showing PDR%, Throughput, Delay, and Routing Overhead with color-coded status badges, and tabbed deep inspectors below for trace file verification, isolation logs, and full configuration parameters.
- Checksum verification should visibly display a `VERIFIED` green badge with the first 16 characters of the SHA-256 hash when valid, giving immediate confidence in data integrity.

</specifics>

<deferred>
## Deferred Ideas

- Multi-experiment comparative plotting / bar charts across seeds (deferred VIZ-01).
- In-TUI ML model retraining and feature dataset generation (deferred TUI-MLWORK).
- Checkpoint-based simulation pause and resume (deferred TUI-PAUSE).

</deferred>

---

*Phase: 11-Results & Experiment Records*
*Context gathered: 2026-11-09*
