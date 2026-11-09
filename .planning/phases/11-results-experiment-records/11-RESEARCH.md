# Phase 11: Results & Experiment Records - Research

**Researched:** 2026-11-09  
**Domain:** Textual TUI results exploration, atomic experiment manifests, SHA-256 artifact verification, past run history browsing, and safe workspace management  
**Confidence:** HIGH  

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01 (Results Screen Layout & Exploration Depth):** Hybrid Split-Pane Architecture:
  - Top Pane (Fixed QoS Scorecard): Permanently displays the four primary academic MANET QoS metrics:
    - Packet Delivery Ratio (PDR, formatted as percentage e.g. `94.2%` and ratio `0.9420`);
    - Throughput (kbps / bps);
    - Average End-to-End Delay (seconds / milliseconds);
    - Routing Overhead (normalized routing packets per data packet sent);
    - Supplementary counters: `data_sent`, `data_received`, and `routing_packets`.
  - Lower Pane (Tabbed Detail Inspector via Textual `TabbedContent`):
    - **Tab 1: Artifacts & Integrity**: Displays absolute and relative generated trace paths (`trace.csv`), SHA-256 checksum, file size, row count, and live integrity verification status badge ("Verified" / "Corrupted" / "Missing").
    - **Tab 2: Security & Isolation Log**: If online IDS was active, displays the roster of flagged and isolated malicious nodes (Blackhole/Grayhole), isolation timestamps, and detection reason. If IDS was disabled or no nodes were isolated, displays an honest empty state indicator.
    - **Tab 3: Configuration & Execution**: Full experiment launch parameters (scenario name, seed, node count, duration, radio range, speed), software version, timestamps (created, started, completed), run status, and supervisor execution log excerpt.

- **D-02 (Session History & Past Run Browser):** Hybrid Two-Tier Navigation Pattern:
  - Preserves the existing compact `RecentExperimentsTable` on `MainWorkspace` (lower split panel) for glanceable recent run status.
  - Selecting a row in `RecentExperimentsTable` and pressing `[Enter]`, or pressing the global shortcut `[R]` (`BINDING_RESULTS`), opens the dedicated full-screen `HistoryScreen`.
  - `HistoryScreen` features:
    - Search and filter controls (filter by run status: `COMPLETED`, `INTERRUPTED`, `FAILED`; filter by scenario name or tag).
    - Sortable columns: Run ID, Scenario, Seed, Status, PDR, Timestamp.
    - Navigation: `[Enter]` opens the selected run in `ResultsScreen`; `[Esc]` or `[B]` returns to `MainWorkspace`.
    - Live synchronization: newly completed runs are reflected in the history browser and dashboard table without requiring application restart.

- **D-03 (Artifact Integrity & Checksum Verification):** Lazy Verification on Open:
  - At run finalization (`WorkloadSupervisor` / `ConcreteSimulationExecutor` completion stage), SHA-256 checksums are calculated for primary generated payload artifacts (`trace.csv` and `isolation_log.json` when present) and stored atomically in `manifest.json` under an `artifacts` mapping (including filename, relative path, byte size, and sha256).
  - `manifest.json` is not hashed into itself to avoid circular hash recursion.
  - When a user opens an experiment in `ResultsScreen`, the application performs on-demand lazy recalculation of artifact hashes in the background/worker to display a clear visual integrity badge:
    - `[green]VERIFIED[/]` — Hash matches manifest record exactly;
    - `[bold red]CORRUPTED / TAMPERED[/]` — File content has been modified since run finalization;
    - `[yellow]MISSING[/]` — File referenced in manifest is no longer present on disk.
  - History list scanning remains fast and responsive on Windows by deferring SHA-256 recalculation to run inspection time.

- **D-04 (Workspace Storage & Safe Cleanup Protocol):** Interactive Pruning with Preview Confirmation Modal:
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

- **D-05 (Clean Package Architecture & Adapter Boundary):** Preservation of Package Isolation Invariants:
  - `test_manet_never_imports_business_packages` remains strictly unweakened. Modules under `manet/` must never import `simulator`, `attacks`, `feature_extraction`, or `ml`.
  - Metrics computation (`simulator.metrics.compute_metrics`) is invoked by the stepping executor in `bootstrap.py` upon simulation completion and persisted in `manifest.json`.
  - The results and history screens read all metrics, configuration, and artifact metadata directly from `manifest.json` via `manet/adapters/workspace.py` without importing simulation modules.

### the agent's Discretion

- Styling and visual design of the QoS Scorecard cards (using SOC cyan/blue/green/amber/red color hierarchy).
- Organization of widgets: whether to place scorecard widgets in `manet/widgets/qos_scorecard.py` or compose inside `manet/screens/results.py`.
- Format of the prune confirmation modal layout and disk size calculation formatting (KB/MB).
- Exact text matching search algorithm in `HistoryScreen` (case-insensitive substring over scenario name, run ID, and seed).

### Deferred Ideas (OUT OF SCOPE)

- Multi-experiment comparative plotting / bar charts across seeds (deferred VIZ-01).
- In-TUI ML model retraining and feature dataset generation (deferred TUI-MLWORK).
- Checkpoint-based simulation pause and resume (deferred TUI-PAUSE).

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **TUI-19** | User can view completed-run results showing actual PDR, throughput, delay, and routing overhead computed via the existing `simulator.metrics.compute_metrics`, plus sent/received packet counts and the generated trace location | `ResultsScreen` with fixed top QoS Scorecard displaying all 4 academic metrics plus packet counters; Tab 1 displays generated trace location, row count, and size; metrics read directly from `manifest.json["metrics"]` computed by `simulator.metrics.compute_metrics` [VERIFIED: simulator/metrics.py:114-123] |
| **TUI-20** | Each experiment stores a manifest (experiment ID, configuration, seed, software version, run status, timestamps, logs, trace paths, available metrics) written atomically, with SHA-256 checksums for completed artifacts | `update_manifest_status` in `manet/adapters/workspace.py` augmented to calculate and store `artifacts` (`trace.csv`, `isolation_log.json`) with SHA-256, byte sizes, and row counts atomically via `.tmp` + `os.replace` [VERIFIED: manet/adapters/workspace.py:59-99] |
| **TUI-21** | User can browse a session history list and open a past result; completed experiment metadata is read-only (reruns create new runs); workspace artifacts are ignored by Git without changing `.gitignore` semantics unintentionally; safe cleanup, if implemented, requires preview and explicit confirmation | `HistoryScreen` with search/filter DataTable; `.manet-workspace/` ignored in `.gitignore`; `PruneConfirmationModal` itemizes files and reclaimable bytes before requiring explicit confirmation; metadata is strictly read-only [VERIFIED: .gitignore:1-8] |

</phase_requirements>

---

## Executive Summary

Phase 11 delivers the results exploration and experiment record infrastructure for the MANET IDS terminal application. Up to Phase 10, background discrete-event simulations executed into timestamped directories under `.manet-workspace/` and recorded execution status into `manifest.json`. Phase 11 completes the research-grade verification cycle by:

1. **Academic QoS Results Screen (`ResultsScreen`):** Providing an authentic academic results scorecard that displays Packet Delivery Ratio (PDR), Throughput (bps/kbps), End-to-End Delay (s/ms), and Routing Overhead, alongside transmitted/received packet tallies and packet loss ratio. A lower tabbed inspector (`TabbedContent`) provides three deep inspection views: Artifacts & SHA-256 Integrity, Security & Isolation Log, and Configuration & Execution Details.
2. **Atomic Manifest Finalization with SHA-256 Artifact Checksums:** Augmenting `update_manifest_status` so that upon completion (or interruption), SHA-256 hashes, byte sizes, and line counts are calculated for generated artifacts (`trace.csv` and `isolation_log.json`) and persisted atomically into `manifest.json` via temporary files and `os.replace`.
3. **Session History Browser (`HistoryScreen`):** Offering a full-screen, searchable, and filterable table of past runs discovered under `.manet-workspace/`. Users can filter by run status (`COMPLETED`, `INTERRUPTED`, `FAILED`), search by scenario or tag, sort by columns, and press `[Enter]` to inspect any run in `ResultsScreen`.
4. **Safe Workspace Pruning Modal (`PruneConfirmationModal`):** Providing an explicit, un-dismissible modal dialog triggered by `[D]` in the history browser that itemizes files to be deleted and total disk space to be reclaimed before requiring confirmation, with Windows file lock safety.
5. **Git Isolation:** Ensuring `.manet-workspace/` is strictly ignored by Git in `.gitignore` without mutating existing pattern semantics.
6. **Strict Architectural Isolation:** Preserving `test_manet_never_imports_business_packages` and `test_command_package_never_uses_os_execution` unweakened. All presentation screens and adapters read parsed JSON and CSV files without importing `simulator`, `attacks`, `feature_extraction`, or `ml`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Metrics Computation | `simulator.metrics` (invoked by `bootstrap.py`) | None | Business logic tier computes metrics at simulation end; presentation tier never computes raw packet metrics [VERIFIED: bootstrap.py:160-161] |
| Manifest Persistence & Checksums | `manet.adapters.workspace` | `bootstrap.py` / `supervisor` | Adapter owns atomic write of `manifest.json` and artifact hashing using stdlib `hashlib` [VERIFIED: manet/adapters/workspace.py:59-99] |
| Results Screen (`ResultsScreen`) | `manet.screens.results` | `manet.widgets.qos_scorecard` | Textual screen rendering QoS scorecard and tabbed inspectors |
| History Browser (`HistoryScreen`) | `manet.screens.history` | `manet.adapters.workspace` | Screen rendering searchable/sortable DataTable of past runs |
| Prune Confirmation Dialog | `manet.screens.prune_modal` | `manet.adapters.workspace` | ModalScreen displaying itemized deletion preview and confirming filesystem removal |
| Git Isolation | `.gitignore` | None | Repository configuration ensuring `.manet-workspace/` is ignored by Git |

---

## Codebase Inventory & In-Repo Provenance

### 1. `simulator/metrics.py:17-28` & `114-123`
The canonical metrics dataclass and return dictionary:
```python
[VERIFIED: simulator/metrics.py:17-28]
@dataclass
class NetworkMetrics:
    """Summary of standard MANET QoS performance metrics."""
    pdr: float
    throughput_bps: float
    avg_delay_s: float
    packet_loss_ratio: float
    routing_overhead: float
    data_sent: int
    data_received: int
    routing_packets: int
```

```python
[VERIFIED: simulator/metrics.py:114-123]
    return {
        "pdr": m.pdr,
        "throughput_bps": m.throughput_bps,
        "avg_delay_s": m.avg_delay_s,
        "packet_loss_ratio": m.packet_loss_ratio,
        "routing_overhead": m.routing_overhead,
        "data_sent": float(m.data_sent),
        "data_received": float(m.data_received),
        "routing_packets": float(m.routing_packets),
    }
```
**Insight:** `manifest.json` already contains this exact dictionary under `"metrics"`. `ResultsScreen` can read these fields directly without importing `simulator.metrics`!

### 2. `manet/adapters/workspace.py:59-99`
Atomic manifest update mechanism:
```python
[VERIFIED: manet/adapters/workspace.py:59-99]
def update_manifest_status(
    experiment_dir: Path,
    status: str,
    metrics: dict[str, float] | None = None,
    error: str | None = None,
) -> Path:
    """Atomically update status, metrics, and timestamps in experiment manifest.json."""
    manifest_path = experiment_dir / "manifest.json"
    tmp_path = experiment_dir / "manifest.json.tmp"
...
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    os.replace(tmp_path, manifest_path)
    return manifest_path
```
**Insight:** Windows native atomic file replacement is guaranteed by `os.replace` (backed by `MoveFileExW` with `MOVEFILE_REPLACE_EXISTING`). Augmenting this function to compute and embed the `artifacts` dictionary ensures SHA-256 hashes are recorded atomically before the file is swapped into place.

### 3. `bootstrap.py:156-161` & `manet/runtime/supervisor.py:212-218`
Run finalization and manifest recording:
```python
[VERIFIED: bootstrap.py:156-161]
        runner.write_traces()
        if runner.online_ids is not None and runner.online_ids.isolation_log_path is not None:
            runner.online_ids.write_isolation_log()

        metrics = compute_metrics(runner.trace_rows, sim_duration=runner.duration)
        return metrics
```

```python
[VERIFIED: manet/runtime/supervisor.py:212-218]
                if self.current_request:
                    try:
                        update_manifest_status(
                            self.current_request.workspace_dir,
                            "COMPLETED",
                            metrics=metrics,
                        )
                        manifest_persisted = True
```
**Insight:** When `update_manifest_status` is called with `COMPLETED` (or `INTERRUPTED`), `runner.write_traces()` and `runner.online_ids.write_isolation_log()` have already flushed `trace.csv` and `isolation_log.json` to disk! Therefore, `workspace.py` can compute SHA-256 hashes of the files right at that moment.

### 4. `manet/runtime/keymap.py:10-19`
Keymap constants:
```python
[VERIFIED: manet/runtime/keymap.py:10-19]
BINDING_CONSOLE = "ctrl+o"
BINDING_HELP = "f1"
BINDING_QUIT = "ctrl+q"
BINDING_PALETTE = "ctrl+p"
BINDING_SIMULATION = "s"
BINDING_RESULTS = "r"
BINDING_LIVE_RUN = "l"
BINDING_STOP = "x"
BINDING_BACKGROUND = "b"
```
**Insight:** `BINDING_RESULTS = "r"` is already bound in `MainWorkspace`. In Phase 11, pressing `[R]` will open `HistoryScreen` instead of triggering a notification. We will also define `BINDING_VIEW_RESULTS = "v"` for transitioning from `LiveRunScreen` upon completion.

### 5. `tests/test_manet_import_boundaries.py:32-51` & `99-122`
Architectural boundary constraints:
```python
[VERIFIED: tests/test_manet_import_boundaries.py:38]
    forbidden_roots = ("simulator", "attacks", "feature_extraction", "ml")
```
and
```python
[VERIFIED: tests/test_manet_import_boundaries.py:105]
    forbidden_roots = ("subprocess", "shutil", "os")
```
**Insight:** Any new screens or widgets in `manet/` must never import `simulator`, `attacks`, `feature_extraction`, or `ml`. `manet/commands/` must never import `subprocess`, `shutil`, or `os`. Note that `manet/adapters/workspace.py` is permitted to use `os` and `shutil` for file system pruning and manifest replacement, but `manet/commands/` cannot.

### 6. `.gitignore:1-8`
Existing ignore patterns:
```gitignore
[VERIFIED: .gitignore:1-8]
# Generated simulation output — reproducible from a seed, never commit (guide §4)
traces/
data/

# Experiment output: keep plots, drop bulk per-run records
results/*
!results/plots/
```
**Insight:** `.manet-workspace/` is currently NOT in `.gitignore`. Adding `.manet-workspace/` to `.gitignore` satisfies TUI-21 without changing the semantics of any existing pattern.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11.8 | Native Windows CPython runtime | Baseline language runtime [VERIFIED: GEMINI.md] |
| Textual | 8.2.8 | TUI widgets, screens, reactive layout, `TabbedContent`, `DataTable`, `ModalScreen` | Standard framework locked for v2.0 milestone [VERIFIED: STATE.md:24] |
| hashlib | stdlib | SHA-256 calculation for artifact checksums | Built-in, fast, zero-dependency, standard cryptographic hash |
| json | stdlib | Manifest serialization and parsing | Built-in, atomic persistence format |
| shutil / os | stdlib | Directory pruning and atomic file replacement (`os.replace`) | Built-in filesystem primitives |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Rich (via Textual) | bundled | Text styling, badges, markup escaping (`rich.markup.escape`) | Formatting QoS metrics and integrity badges |
| csv | stdlib | Parsing `isolation_log` records safely | Inspecting isolated nodes without pandas |

### Package Legitimacy Audit
**Verdict:** OK. Phase 11 installs zero external packages. All required capabilities are fulfilled by Python 3.11 stdlib and Textual 8.2.8.

---

## Technical Approach & Architecture Patterns

### System Architecture Diagram

```mermaid
flowchart TD
    subgraph Execution Finalization
        SimRunner["SimulationRunner (bootstrap.py)"] -->|Writes traces| TraceFile["trace.csv"]
        OnlineIDS["OnlineIDS (ml/response.py)"] -->|Writes isolation log| IsoLog["isolation_log.json / .csv"]
        ComputeMetrics["compute_metrics()"] -->|Returns metrics dict| Supervisor["WorkloadSupervisor"]
        Supervisor -->|update_manifest_status()| WorkspaceAdapter["WorkspaceAdapter"]
        WorkspaceAdapter -->|Compute SHA-256| HashEngine["hashlib.sha256()"]
        HashEngine -->|Record artifacts & metrics| ManifestTmp["manifest.json.tmp"]
        ManifestTmp -->|os.replace() atomic swap| Manifest["manifest.json"]
    end

    subgraph User Exploration & Navigation
        MainWorkspace["MainWorkspace ([R] or table click)"] --> HistoryScreen["HistoryScreen"]
        LiveRun["LiveRunScreen ([V] View Results)"] --> ResultsScreen["ResultsScreen"]
        HistoryScreen -->|Enter on row| ResultsScreen
        HistoryScreen -->|[D] Prune run| PruneModal["PruneConfirmationModal"]
        PruneModal -->|Confirm Enter| DeleteOp["workspace.delete_experiment_run()"]
    end

    subgraph ResultsScreen Architecture
        ResultsScreen --> Scorecard["Top QoS Scorecard (PDR, Throughput, Delay, Overhead)"]
        ResultsScreen --> TabbedInspector["TabbedContent Lower Pane"]
        TabbedInspector --> Tab1["Tab 1: Artifacts & Integrity (SHA-256, Size, Rows, Live Badge)"]
        TabbedInspector --> Tab2["Tab 2: Security & Isolation Log (Node roster, timestamps, strikes)"]
        TabbedInspector --> Tab3["Tab 3: Configuration & Execution (Parameters, versions, logs)"]
    end
```

### Pattern 1: QoS Scorecard Component
**What:** Top pane permanently visible on `ResultsScreen` displaying the 4 academic MANET QoS metrics in prominent stat cards, color-coded according to network health thresholds.
**Thresholds & Formatting:**
- **Packet Delivery Ratio (PDR):**
  - Formatted as percentage (`{pdr * 100:.2f}%`) and raw ratio (`{pdr:.4f}`).
  - Color badge: Green (`>= 80%`), Yellow (`50% - 79.9%`), Red (`< 50%`).
- **Throughput:**
  - Formatted with adaptive units: if `>= 1,000,000 bps` -> `{mbps:.2f} Mbps`; if `>= 1,000 bps` -> `{kbps:.2f} kbps`; else `{bps:.1f} bps`.
- **End-to-End Delay:**
  - Formatted as `{delay * 1000:.1f} ms` (or `{delay:.4f} s` if `>= 1.0s`).
- **Routing Overhead:**
  - Formatted as `{overhead:.4f} pkts/data`.
- **Packet Tallies:**
  - Sent / Received: `{data_sent:.0f} sent / {data_received:.0f} recv (loss: {loss * 100:.1f}%)`.
  - Routing: `{routing_packets:.0f} routing packets`.

### Pattern 2: Artifact Checksum Calculation & Lazy Verification
**What:** At completion, SHA-256 is computed using 64KB chunking to avoid loading whole files into memory:
```python
def compute_experiment_artifacts(experiment_dir: Path) -> dict[str, dict[str, Any]]:
    artifacts: dict[str, dict[str, Any]] = {}
    for filename in ("trace.csv", "isolation_log.json", "isolation_log.csv"):
        file_path = experiment_dir / filename
        if file_path.is_file():
            hasher = hashlib.sha256()
            size_bytes = 0
            row_count = 0
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
                    size_bytes += len(chunk)
                    row_count += chunk.count(b"\n")
            artifacts[filename] = {
                "filename": filename,
                "relative_path": filename,
                "absolute_path": str(file_path.resolve()),
                "size_bytes": size_bytes,
                "sha256": hasher.hexdigest(),
                "row_count": row_count,
            }
    return artifacts
```
**Lazy Verification on Open:**
When `ResultsScreen` is opened, it compares the current hash of the file on disk against the hash recorded in `manifest.json["artifacts"]`:
- If file missing -> `[yellow]MISSING[/]`
- If hash matches -> `[green]VERIFIED ✓ (sha256: {hash[:16]}...)[/]`
- If hash mismatch -> `[bold red]CORRUPTED / TAMPERED ✗[/]`
- If legacy manifest has no recorded hash -> `[cyan]RECORDED (sha256: {hash[:16]}...)[/]`

### Pattern 3: HistoryScreen with Real-Time Filtering and Sorting
**What:** Full-screen DataTable listing past runs discovered in `.manet-workspace/`.
- **Search bar:** `Input` widget filtering rows in real-time as the user types (matches `scenario_name`, `experiment_id`, or `seed`).
- **Status filter:** Buttons/tabs for `[All]`, `[Completed]`, `[Interrupted]`, `[Failed]`.
- **Keyboard interaction:**
  - `[Up]` / `[Down]`: Move cursor across runs.
  - `[Enter]`: Open selected run in `ResultsScreen`.
  - `[D]`: Open `PruneConfirmationModal` for selected run.
  - `[R]`: Refresh experiment list.
  - `[Esc]` or `[B]`: Return to `MainWorkspace`.

### Pattern 4: Safe Workspace Pruning Modal (`PruneConfirmationModal`)
**What:** ModalScreen showing an itemized list of files and disk space to be freed before deletion.
**Safety Rules:**
1. Target path validation: must resolve inside `workspace_root` and not equal `workspace_root` (anti-traversal guard).
2. Explicit confirmation required: `[Enter]` confirms, `[Esc]` cancels.
3. Windows lock safety: wraps `shutil.rmtree` in try-except block handling `PermissionError` (Windows file lock) and surfaces human-readable error if a process holds the file open.
4. Refresh parent on success: updates `HistoryScreen` and `MainWorkspace` recent experiments table.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tabbed Navigation | Custom key switchers / hidden containers | Textual `TabbedContent` + `TabPane` | Built-in keyboard navigation, mouse click support, clean CSS styling |
| Data Tables & Sorting | Formatted text lists | Textual `DataTable` | Built-in cursor management, selection events (`RowSelected`), scrolling, and row keys |
| Modal Dialogs | Manually placed overlays with z-index | Textual `ModalScreen` | Locks focus, captures dismiss result cleanly (`self.dismiss(result)`), supports dark scrim background |
| Checksums | Custom hash logic | Python stdlib `hashlib.sha256` | Battle-tested, C-accelerated in stdlib, standard SHA-256 output |
| Atomic File Writes | Direct file overwrites | Temporary file + `os.replace` | Prevents corrupted manifests on sudden termination or power loss; atomic on Windows |

---

## Common Pitfalls & Edge Cases

### Pitfall 1: Package Isolation Invariant Violation (Business Imports)
**What goes wrong:** A developer imports `from simulator.metrics import compute_metrics` or `from ml.response import OnlineIDS` inside `manet/screens/results.py` or `manet/adapters/workspace.py`.
**Why it happens:** Convenience — trying to recompute metrics or parse logs using classes from business logic.
**How to avoid:** Hard invariant `test_manet_never_imports_business_packages` forbids this. `ResultsScreen` and `WorkspaceAdapter` MUST only read the serialized numbers in `manifest.json` and parse CSV/JSON logs with stdlib `csv` / `json`.
**Warning signs:** CI breaks on `test_manet_never_imports_business_packages`.

### Pitfall 2: Windows File Locking (`PermissionError: [WinError 32]`)
**What goes wrong:** When trying to delete an experiment directory via `shutil.rmtree` or recalculate hashes, Windows throws `PermissionError` because a file handle was left open.
**Why it happens:** Failing to use `with open(...)` or lingering file streams in background tasks.
**How to avoid:** Always use context managers (`with open(...) as f:`) when reading traces, manifests, or logs. In `delete_experiment_run`, catch `PermissionError` and surface an actionable error message ("File is currently open by another process on Windows").

### Pitfall 3: Massive Trace Files Blocking UI Event Loop
**What goes wrong:** Calling `hashlib.sha256(f.read())` or `pd.read_csv(trace_path)` on a 100,000-line trace file locks the Textual event loop, causing UI freezing.
**Why it happens:** Reading multi-megabyte traces synchronously into memory.
**How to avoid:** Chunk reading in 64KB blocks (`f.read(65536)`). Count rows during chunk reading via byte count `chunk.count(b"\n")`. Perform on-demand verification efficiently.

### Pitfall 4: Missing or Interrupted Runs
**What goes wrong:** Opening an experiment that failed or was interrupted mid-run causes `KeyError` or `TypeError` because `metrics` is `None` or `pdr` is missing.
**Why it happens:** Assuming all manifests look like successful completed runs.
**How to avoid:** Check `manifest["status"]`. If metrics are `None`, render an honest banner: `"Simulation Interrupted / Partial Run — No final QoS metrics available"` and show available traces and error details instead of crashing.

### Pitfall 5: Path Traversal Vulnerability in Pruning
**What goes wrong:** A crafted run ID (e.g. `../../scenarios`) could cause `delete_experiment_run` to delete files outside `.manet-workspace/`.
**Why it happens:** Directly concatenating `workspace_root / experiment_id` without path resolution verification.
**How to avoid:** Validate `resolved = (workspace_root / experiment_id).resolve()`; assert `resolved.is_relative_to(workspace_root.resolve())` and `resolved != workspace_root.resolve()`.

---

## Code Examples

### 1. `ResultsScreen` Top QoS Scorecard Layout
```python
# In manet/widgets/qos_scorecard.py or manet/screens/results.py
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static
from rich.markup import escape

class QosScorecard(Container):
    """QoS Scorecard rendering the four primary MANET metrics with SOC color badges."""
    
    def __init__(self, metrics: dict[str, float] | None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metrics = metrics or {}

    def compose(self) -> ComposeResult:
        pdr = self.metrics.get("pdr")
        thru = self.metrics.get("throughput_bps", 0.0)
        delay = self.metrics.get("avg_delay_s", 0.0)
        overhead = self.metrics.get("routing_overhead", 0.0)
        sent = self.metrics.get("data_sent", 0.0)
        recv = self.metrics.get("data_received", 0.0)
        routing = self.metrics.get("routing_packets", 0.0)

        # PDR badge
        if pdr is not None:
            pdr_color = "#3fb950" if pdr >= 0.8 else ("#d29922" if pdr >= 0.5 else "#f85149")
            pdr_str = f"[bold {pdr_color}]{pdr * 100:.1f}%[/] [dim]({pdr:.4f})[/]"
        else:
            pdr_str = "[dim]N/A[/]"

        # Throughput formatting
        if thru >= 1_000_000:
            thru_str = f"[bold #58a6ff]{thru / 1_000_000:.2f} Mbps[/]"
        elif thru >= 1_000:
            thru_str = f"[bold #58a6ff]{thru / 1_000:.2f} kbps[/]"
        else:
            thru_str = f"[bold #58a6ff]{thru:.0f} bps[/]"

        # Delay formatting
        delay_ms = delay * 1000.0
        delay_str = f"[bold #39c5cf]{delay_ms:.1f} ms[/]" if delay < 1.0 else f"[bold #39c5cf]{delay:.3f} s[/]"

        # Overhead formatting
        overhead_str = f"[bold #d29922]{overhead:.4f}[/] [dim]pkts/data[/]"

        with Horizontal(id="scorecard-cards"):
            with Vertical(classes="scorecard-card"):
                yield Static("[dim]PACKET DELIVERY RATIO[/]")
                yield Static(pdr_str, classes="metric-val")
            with Vertical(classes="scorecard-card"):
                yield Static("[dim]NETWORK THROUGHPUT[/]")
                yield Static(thru_str, classes="metric-val")
            with Vertical(classes="scorecard-card"):
                yield Static("[dim]END-TO-END DELAY[/]")
                yield Static(delay_str, classes="metric-val")
            with Vertical(classes="scorecard-card"):
                yield Static("[dim]ROUTING OVERHEAD[/]")
                yield Static(overhead_str, classes="metric-val")

        with Horizontal(id="scorecard-subcounters"):
            loss_pct = (1.0 - pdr) * 100 if pdr is not None else 0.0
            yield Static(
                f"[dim]Data Traffic:[/] [bold]{sent:.0f}[/] sent | [bold]{recv:.0f}[/] recvd (loss: {loss_pct:.1f}%) | "
                f"[dim]Routing:[/] [bold]{routing:.0f}[/] packets",
                id="subcounters-text",
            )
```

### 2. `PruneConfirmationModal` Implementation
```python
# In manet/screens/prune_modal.py
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from rich.markup import escape

class PruneConfirmationModal(ModalScreen[bool]):
    """Modal confirmation dialog for permanently deleting an experiment directory."""
    
    BINDINGS = [
        Binding("escape", "dismiss(False)", "Cancel"),
        Binding("enter", "confirm_delete", "Delete"),
    ]

    def __init__(self, preview: dict[str, Any], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.preview = preview

    def compose(self) -> ComposeResult:
        exp_id = escape(self.preview.get("experiment_id", "Unknown"))
        total_kb = self.preview.get("total_bytes", 0) / 1024.0
        files = self.preview.get("files", [])

        with Vertical(id="prune-dialog"):
            yield Static("[bold #f85149]DELETE EXPERIMENT RECORD[/]\n")
            yield Static(
                f"Are you sure you want to permanently delete run [bold cyan]{exp_id}[/]?\n"
                f"Target path: [dim]{escape(self.preview.get('path', ''))}[/]\n\n"
                f"[bold]Files to be removed:[/]"
            )
            file_lines = []
            for f in files:
                f_size_kb = f.get("size_bytes", 0) / 1024.0
                file_lines.append(f"  • [yellow]{escape(f['name'])}[/] ({f_size_kb:.1f} KB)")
            yield Static("\n".join(file_lines) or "  (No files found)")
            yield Static(f"\nTotal space to reclaim: [bold green]{total_kb:.1f} KB[/]\n")
            with Horizontal(id="prune-buttons"):
                yield Button("Cancel", id="btn-cancel", variant="default")
                yield Button("Delete Permanently", id="btn-delete", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-delete":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm_delete(self) -> None:
        self.dismiss(True)
```

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | `pytest.ini` [VERIFIED: in-repo] |
| Quick run command | `python -m pytest tests/test_manet_results_screen.py tests/test_manet_history_screen.py tests/test_manet_manifest_artifacts.py tests/test_manet_workspace_pruning.py -v` |
| Full suite command | `python -m pytest tests/test_manet_*.py` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| **TUI-19** | ResultsScreen renders actual PDR, throughput, delay, routing overhead from manifest; displays sent/recvd counts and trace paths | Integration / Textual Pilot | `python -m pytest tests/test_manet_results_screen.py -v` | ❌ Wave 0 Gap |
| **TUI-19** | ResultsScreen displays honest empty state when IDS disabled or no isolated nodes | Unit / Integration | `python -m pytest tests/test_manet_results_screen.py::test_results_screen_ids_empty_state -v` | ❌ Wave 0 Gap |
| **TUI-20** | `update_manifest_status` calculates SHA-256 for trace.csv and isolation_log and records atomically | Unit | `python -m pytest tests/test_manet_manifest_artifacts.py -v` | ❌ Wave 0 Gap |
| **TUI-20** | Lazy checksum verification detects VERIFIED, CORRUPTED, and MISSING states | Unit | `python -m pytest tests/test_manet_manifest_artifacts.py::test_artifact_tamper_detection -v` | ❌ Wave 0 Gap |
| **TUI-21** | HistoryScreen lists runs, supports search/filter by status and text, opens Results on Enter | Integration / Textual Pilot | `python -m pytest tests/test_manet_history_screen.py -v` | ❌ Wave 0 Gap |
| **TUI-21** | `PruneConfirmationModal` itemizes files and total bytes; confirms before `delete_experiment_run` removes directory | Integration / Textual Pilot | `python -m pytest tests/test_manet_workspace_pruning.py -v` | ❌ Wave 0 Gap |
| **TUI-21** | `.gitignore` ignores `.manet-workspace/` without changing existing rule semantics | Unit | `python -m pytest tests/test_manet_workspace_pruning.py::test_git_ignores_workspace -v` | ❌ Wave 0 Gap |
| **D-05** | AST test verifies zero business package imports in new screens, widgets, or adapters | Architectural AST | `python -m pytest tests/test_manet_import_boundaries.py -v` | ✅ Present |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_manet_results_*.py tests/test_manet_history_*.py tests/test_manet_manifest_*.py tests/test_manet_import_boundaries.py`
- **Per wave merge:** `python -m pytest tests/test_manet_*.py`
- **Phase gate:** Full suite green (all 239+ baseline & manet tests) before completion.

### Wave 0 Gaps
- [ ] `tests/test_manet_results_screen.py` — covers TUI-19 (QoS scorecard, tabs, empty states, missing metrics)
- [ ] `tests/test_manet_manifest_artifacts.py` — covers TUI-20 (atomic manifest update, SHA-256 computation, tamper detection)
- [ ] `tests/test_manet_history_screen.py` — covers TUI-21 (history table, search, filter, row selection navigation)
- [ ] `tests/test_manet_workspace_pruning.py` — covers TUI-21 (prune preview, modal confirmation, deletion safety, gitignore check)

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Reading small trace files for hash calculation (< 5MB) takes < 20ms and does not require async threading | Artifact Integrity | Low: if larger traces are used, hash computation can be moved into a Textual background worker |
| A2 | `.gitignore` can have `.manet-workspace/` appended without affecting existing git rules | Workspace Storage | None: tested and verified; `.manet-workspace/` was previously unignored |

---

## Open Questions

1. **How should `ResultsScreen` handle runs from before Phase 11 that lack the `artifacts` field in `manifest.json`?**
   - *Recommendation:* If `artifacts` is absent from `manifest.json`, `verify_artifact_checksums` can calculate current SHA-256 of existing files and display badge `RECORDED (Current: {sha256[:16]}...)` without claiming it was verified against a historical checksum.
2. **Should `LiveRunScreen` transition automatically to `ResultsScreen` on run completion?**
   - *Recommendation:* No. Keep the user in control: display terminal summary in the log and enable a prominent `[V] View Results` button and `[V]` shortcut so the user chooses when to leave the monitor.

---

## Sources

### Primary (HIGH confidence)
- `simulator/metrics.py:17-28, 114-123` — `NetworkMetrics` dataclass and dictionary return format
- `manet/adapters/workspace.py:59-99, 102-112` — Atomic manifest update, `ExperimentSummary`, and directory allocation
- `manet/runtime/supervisor.py:212-218` — Supervisor execution lifecycle and terminal state handling
- `bootstrap.py:156-161` — Stepping executor finalization and metrics invocation
- `tests/test_manet_import_boundaries.py:32-51, 99-122` — AST boundary tests
- `.gitignore:1-8` — Current repository ignore rules
- `.planning/phases/11-results-experiment-records/11-CONTEXT.md` — User decisions D-01 through D-05

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Python 3.11 stdlib + Textual 8.2.8, zero new dependencies
- Architecture: HIGH — Follows established v2.0 screen/adapter patterns and AST package isolation
- Pitfalls: HIGH — Windows file locking, large file streaming, and atomic persistence specifically addressed

**Research date:** 2026-11-09  
**Valid until:** End of milestone v2.0
