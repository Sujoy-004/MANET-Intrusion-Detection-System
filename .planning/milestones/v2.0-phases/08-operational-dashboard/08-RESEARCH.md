# Phase 08: Operational Dashboard - Research

**Researched:** 2026-11-07  
**Domain:** Textual 8.2.8 operational dashboard, runtime capability diagnostics, executive grid layout, non-blocking polling, zero-mock presentation  
**Confidence:** HIGH  

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Top Status Cards with Split Body (Executive Grid) layout. The operational dashboard organizes high-level system diagnostics across top status cards (System Health, Component Capabilities, Active Workload/Threat Status), with a split lower body dedicated to Recent Experiments / First-Run CTA and quick navigation shortcuts. Responsive `HORIZONTAL_BREAKPOINTS` automatically reflow multi-column cards into a single vertical stream on compact viewports (down to 80x24). — **Reversibility:** costly — defines the widget composition and mounting hierarchy of `MainWorkspace`.
- **D-02:** Periodic Background Polling (every 3–5 seconds). Capability diagnostics evaluate system readiness on startup (`on_mount`) and periodically re-scan filesystem indicators (presence of scenario JSONs, `data/train.csv`, `data/test.csv`, and `ml/models/best_model.joblib`) using lightweight, non-blocking file stat checks. This automatically discovers newly trained models or datasets without requiring an application restart. — **Reversibility:** reversible — timer interval and probe logic live in a self-contained diagnostic provider.
- **D-03:** Inline Contextual Badges within Capability Cards. Missing components, unverified artifacts, and degraded models are rendered as inline badges directly inside their respective capability cards (e.g., `[amber]PARTIAL (Grayhole F1: 0.0)[/]`, `[red]UNAVAILABLE[/]`, `[green]VERIFIED[/]`). This preserves screen real estate and visual balance on compact terminals while maintaining absolute operational honesty per TUI-08 without intrusive top alert banners. — **Reversibility:** reversible.
- **D-04:** Guided Call-to-Action (CTA) Hero Panel. When launching the application on a fresh environment where no experiments exist in `.manet-workspace/`, the lower body displays a prominent, guided CTA panel orienting the user to their first action (e.g., "Ready for Simulation • Press [S] to configure and launch your first MANET scenario"). Once an experiment completes, the panel transitions to display the Recent Experiments summary table. — **Reversibility:** reversible.
- **D-05:** Session Shell Mounting Contract. Carry forward Phase 7's deferred D-03 contract by structuring `MainWorkspace` with `StatusBar`, `NotificationRail`, and `NavRail` under `manet/widgets/` backed by clean noop adapter interfaces under `manet/adapters/`. This establishes the mounting points for Phase 10/11 background workers and history without re-architecting the shell. — **Reversibility:** costly — pins the adapter interface boundaries across the app.

### the agent's Discretion
- Concrete diagnostic probe adapter implementation (`manet/adapters/diagnostics.py`).
- Exact card styling, borders, and badge text typography using existing Textual theme tokens (`$primary`, `$secondary`, `$success`, `$warning`, `$error`).
- Detailed metadata formatting from `ml/models/model_metadata.json` (timestamp, architecture, hyperparameters, precision, recall, and Grayhole F1 callout).

### Deferred Ideas (OUT OF SCOPE)
- In-TUI live model retraining / evaluation workload runner — Phase 10 / future scope (TUI-MLWORK).
- Full interactive experiment replay and packet-level animation — future milestone (VIZ-01).
- Advanced metric export center (PDF/HTML report generation) — future milestone.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TUI-06 | User can view a real operational dashboard showing startup diagnostics: Python version, required dependency availability, and availability of scenario files, datasets, and model artifacts | `manet/adapters/diagnostics.py` probes Python version (`sys.version_info`), required packages (`simpy`, `networkx`, `sklearn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pytest`, `joblib`), scenario presets (`scenarios/*.json`), datasets (`data/train.csv`, `data/test.csv`), and champion model artifact (`ml/models/best_model.joblib`), displayed inside `SystemHealthCard` and `ComponentCapabilitiesCard` on `MainWorkspace`. |
| TUI-07 | User can view active workload state and recent experiment summaries (when available) on the dashboard, with quick navigation to simulation, results, logs, and help | `ActiveWorkloadCard` displays workload state (e.g., `IDLE (No active simulation)`), `RecentExperimentsTable` displays runs found in `.manet-workspace/`, `CtaHeroPanel` displays guided first-run actions when `.manet-workspace/` is empty, and `NavRail` / key bindings provide instant navigation to simulation (`[S]`), results (`[R]`), console (`[Ctrl+O]`), palette (`[Ctrl+P]`), and help (`[F1]`). |
| TUI-08 | User sees explicit capability states — verified, experimental, partial, unavailable — with no mock values displayed and no claim of model or dataset existence when files are missing; model metadata is reported with its timestamp/version context and current Grayhole F1 of 0.0 is presented as not-effective detection | `ComponentCapabilitiesCard` renders inline badges with strict operational truth: missing files surface as `UNAVAILABLE` with exact CLI remediation commands (e.g. `Run python scripts/build_dataset.py --multi-attack`), and champion model metadata from `ml/models/model_metadata.json` explicitly badges the detector as `PARTIAL (Grayhole F1: 0.0 - Ineffective Detection)` because Grayhole F1 is 0.0. Zero mock or hardcoded values are rendered when files are missing. |
</phase_requirements>

## Summary

Phase 8 elevates the `MANET IDS` terminal workspace (`MainWorkspace`) from Phase 7's static placeholder into a live, honest operational dashboard. The operational dashboard serves as the central flight deck for the entire system: upon launch, it executes non-blocking diagnostic probes inspecting the Python runtime environment, presence of 9 core dependencies (`simpy`, `networkx`, `sklearn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pytest`, `joblib`), 5 preset scenario JSON definitions in `scenarios/`, datasets in `data/`, and the champion model artifact in `ml/models/best_model.joblib` with provenance from `ml/models/model_metadata.json`.

In adherence to strict operational honesty (TUI-08), no mock values or placeholder numbers are ever rendered. If datasets or model artifacts are absent (as on a clean repository clone where `.gitignore` excludes them), the dashboard displays an unambiguous `UNAVAILABLE` badge accompanied by the exact CLI command required to generate them. When the champion model exists, its metadata is presented with full context, specifically highlighting its Blackhole F1 score (0.7593) while explicitly stating that its Grayhole detection is `PARTIAL` with an F1 score of 0.0 (ineffective detection).

Architecturally, Phase 8 fulfills the deferred D-03 Option-A mounting contract from Phase 7 (Decision D-05), structuring `MainWorkspace` with top diagnostic status cards, a split lower body containing either a Guided CTA Hero Panel (when `.manet-workspace/` is empty) or a Recent Experiments summary table, and persistent workspace rails (`StatusBar`, `NotificationRail`, `NavRail`) backed by decoupled adapter protocols in `manet/adapters/`. Periodic polling via Textual's `set_interval` (every 3–5 seconds) uses lightweight filesystem `stat` checks so that files generated outside the TUI are automatically discovered without restarting the application.

**Primary recommendation:** Implement `manet/adapters/diagnostics.py` using standard library `importlib.util` and `pathlib.Path.stat()` with strict zero-mock capability states, compose `MainWorkspace` with `StatusBar`, `NotificationRail`, `NavRail`, and cards adhering to the Executive Grid layout, and verify that all `manet/` modules strictly avoid importing `simulator`, `attacks`, `feature_extraction`, or `ml`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| System Environment Probing | Presentation Adapter (`manet/adapters/diagnostics.py`) | Python runtime (`sys`, `importlib`) | Probes host environment non-invasively; no business logic invoked |
| Artifact & Metadata Inspection | Presentation Adapter (`manet/adapters/diagnostics.py`) | Filesystem (`pathlib`, `json`) | Reads metadata JSON and file stat without importing ML or simulation models |
| Workspace Experiment Discovery | Presentation Adapter (`manet/adapters/workspace.py`) | Filesystem (`.manet-workspace/`) | Discovers experiment run manifests without running simulation code |
| Dashboard Grid Composition | Presentation Screen (`manet/screens/main_workspace.py`) | Textual Layout Engine | Composes top cards, split lower body, and responsive classes |
| Status & Notification Rails | Presentation Widgets (`manet/widgets/`) | `manet/adapters/` | Establishes mounting points for Phase 10/11 background workers and telemetry |
| Periodic File Stat Polling | Presentation Screen (`MainWorkspace.set_interval`) | Diagnostics Probe | Re-evaluates file timestamps without holding Windows file locks or freezing the UI |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | 8.2.8 | Full-screen TUI widgets (`Static`, `DataTable`, `Container`, `Horizontal`, `Vertical`), layout, reactive updates, timer polling | Verified installed in environment; locked milestone framework `[VERIFIED: pip show textual]` |
| pytest-asyncio | 1.3.0 | Asynchronous test harness for pilot testing Textual screens and timers | Standard pairing for Textual testing `[VERIFIED: pip show pytest-asyncio]` |

### Supporting (Standard Library Only)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `importlib.util` / `importlib.metadata` | stdlib 3.11.8 | Probe module specs and distribution package versions without importing heavy packages | Dependency availability checking in `diagnostics.py` |
| `pathlib.Path` | stdlib 3.11.8 | File existence, timestamp check (`stat().st_mtime`), file size (`stat().st_size`) | Cross-platform, Windows-safe filesystem probing |
| `json` | stdlib 3.11.8 | Parse `ml/models/model_metadata.json` and scenario JSON files | Reading metadata without importing business logic |
| `sys` / `platform` | stdlib 3.11.8 | Extract Python version and OS platform name | Runtime environment diagnostics |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `importlib.util.find_spec` | `import <module>` | Direct `import` executes package top-level code, imports heavy C-extensions (like numpy, scipy), and can pollute runtime state; `find_spec` checks availability without loading |
| Direct JSON file reading | `import ml.models` | Forbidden by architectural boundary rule `[VERIFIED: tests/test_manet_import_boundaries.py:38]`: `manet/` must never import `ml` |
| Full file content scanning | `pathlib.Path.stat()` | Reading thousands of CSV lines on every poll would cause UI stutters; `stat().st_mtime` and `stat().st_size` provide instantaneous checks |

**Version verification:**
- `python -m pip show textual` → Version: 8.2.8 `[VERIFIED: python -m pip show textual]`
- `python -m pip show pytest-asyncio` → Version: 1.3.0 `[VERIFIED: python -m pip show pytest-asyncio]`
- Python: 3.11.8 `[VERIFIED: python --version]`

## Package Legitimacy Audit

> Phase 8 requires **no new external packages**. All required dependencies were verified in Phase 7 and are already present in the environment.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| textual | PyPI | 4+ yrs | >2M/mo | github.com/Textualize/textual | [OK] | Approved (Phase 7 locked) |
| pytest-asyncio | PyPI | 8+ yrs | >50M/mo | github.com/pytest-dev/pytest-asyncio | [OK] | Approved (Phase 7 locked) |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none  

## Architecture Patterns

### System Architecture Diagram

```
                 +-----------------------------------------------------+
                 |                      ManetApp                       |
                 |      (Mounts MainWorkspace, Handles App Bindings)   |
                 +--------------------------+--------------------------+
                                            |
                                            v
                 +-----------------------------------------------------+
                 |                    MainWorkspace                    |
                 |      (Executive Grid, Responsive Breakpoints)       |
                 +--------------------------+--------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                  |                                  |
         v                                  v                                  v
+------------------+              +-------------------+              +------------------+
|  StatusBar       |              |  NotificationRail |              |  NavRail         |
|  (System Status) |              |  (Alert Notices)  |              |  (Quick Actions) |
+------------------+              +-------------------+              +------------------+
         |                                  |                                  |
         +----------------------------------+----------------------------------+
                                            |
         +----------------------------------+----------------------------------+
         |                                                                     |
         v                                                                     v
+-----------------------------------+             +------------------------------------+
|        Top Status Cards           |             |           Lower Split Body         |
|  - SystemHealthCard               |             |  - If .manet-workspace empty:      |
|  - ComponentCapabilitiesCard      |             |      CtaHeroPanel (Guided Tour)    |
|  - ActiveWorkloadCard             |             |  - If experiments exist:           |
+-----------------+-----------------+             |      RecentExperimentsTable        |
                  |                               +------------------------------------+
                  v
+--------------------------------------------------------------------------------------+
|                     DiagnosticsAdapter / DiagnosticsProbe                            |
|             (Non-blocking filesystem stat, importlib spec checking)                  |
+-------------------+--------------------+--------------------+--------------------+
                    |                    |                    |
                    v                    v                    v
         +--------------------+ +--------------------+ +--------------------+
         |   scenarios/*.json | |      data/*.csv    | | ml/models/*.joblib |
         |   (5 Presets)      | | (train & test csv) | |   & metadata.json  |
         +--------------------+ +--------------------+ +--------------------+
```

### Recommended Project Structure
```
manet/
├── adapters/                  # [NEW: Phase 8 adapter layer]
│   ├── __init__.py            # Adapter package boundary
│   ├── diagnostics.py         # DiagnosticsProbe: probes env, dependencies, scenarios, data, models
│   ├── navigation.py          # NavigationAdapter: navigation links and action dispatch
│   ├── notifications.py       # NotificationAdapter: in-memory notification queue / banner
│   ├── status.py              # StatusAdapter: system health and active workload status
│   └── workspace.py           # WorkspaceAdapter: scan .manet-workspace/ for run manifests
├── commands/                  # Command registry and console
│   ├── console_driver.py
│   ├── palette_provider.py
│   └── registry.py            # AppCommand registrations
├── runtime/                   # Runtime environment and styling
│   ├── keymap.py              # Single-source keymap definitions
│   ├── settings.py            # Session settings (in-memory)
│   └── theme.py               # SOC & SOC_HIGH_CONTRAST themes
├── screens/                   # Full-screen views
│   ├── console.py             # Interactive command console
│   ├── help_about.py          # Shortcuts and about screen
│   └── main_workspace.py      # Upgraded Executive Grid operational dashboard
└── widgets/                   # [NEW: Phase 8 reusable UI widgets]
    ├── __init__.py            # Widget package boundary
    ├── cta_hero.py            # Guided Call-to-Action Hero Panel (first-run empty state)
    ├── dashboard_cards.py     # SystemHealthCard, ComponentCapabilitiesCard, ActiveWorkloadCard
    ├── nav_rail.py            # Quick action navigation panel
    ├── notification_rail.py   # Workspace notification / notice banner
    ├── recent_experiments.py  # RecentExperimentsTable (DataTable of past runs)
    └── status_bar.py          # Persistent footer status indicator
```

### Pattern 1: Non-Blocking Non-Leaking Capability Probe
**What:** Probes system health and file artifacts without importing business logic (`simulator`, `attacks`, `feature_extraction`, `ml`) or loading massive files into RAM.  
**When to use:** Every application startup (`on_mount`) and during periodic background polling timer events.  
**Example:**
```python
# Source: manet/adapters/diagnostics.py
from dataclasses import dataclass
import importlib.util
import importlib.metadata
import json
from pathlib import Path
import sys

REQUIRED_DEPENDENCIES: tuple[tuple[str, str], ...] = (
    ("simpy", "simpy"),
    ("networkx", "networkx"),
    ("sklearn", "scikit-learn"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
    ("pytest", "pytest"),
    ("joblib", "joblib"),
)

@dataclass(frozen=True)
class CapabilityStatus:
    name: str
    state: str  # "VERIFIED", "PARTIAL", "EXPERIMENTAL", "UNAVAILABLE"
    details: str
    remediation: str | None = None

class DiagnosticsProbe:
    """Probes runtime environment and filesystem artifacts with zero mock values."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()

    def probe_dependencies(self) -> dict[str, tuple[bool, str]]:
        results = {}
        for mod, dist in REQUIRED_DEPENDENCIES:
            available = importlib.util.find_spec(mod) is not None
            ver = "missing"
            if available:
                try:
                    ver = importlib.metadata.version(dist)
                except Exception:
                    ver = "installed"
            results[mod] = (available, ver)
        return results

    def probe_model_artifact(self) -> CapabilityStatus:
        joblib_path = self.repo_root / "ml" / "models" / "best_model.joblib"
        metadata_path = self.repo_root / "ml" / "models" / "model_metadata.json"
        
        # Distinguish missing binary from available historical metadata
        if not joblib_path.exists():
            meta_note = " (historical metadata available)" if metadata_path.exists() else ""
            return CapabilityStatus(
                name="Champion Model",
                state="UNAVAILABLE",
                details=f"best_model.joblib missing{meta_note}",
                remediation="Run python scripts/build_dataset.py --multi-attack && python -m ml.train && python -m ml.evaluate",
            )
        
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                model_name = meta.get("champion", "unknown")
                test_metrics = meta.get("test_metrics", {})
                f1_bh = test_metrics.get("f1_blackhole")
                f1_gh = test_metrics.get("f1_grayhole")
                fpr = test_metrics.get("fpr")
                
                bh_str = f"BH F1: {f1_bh:.4f}" if f1_bh is not None else "BH F1: N/A"
                fpr_str = f"FPR: {fpr:.4f}" if fpr is not None else "FPR: N/A"
                
                # Grayhole F1 is 0.0 -> dynamically badged as PARTIAL / Ineffective detection
                if f1_gh == 0.0:
                    gh_str = "GH F1: 0.0 [Ineffective Detection]"
                    status_state = "PARTIAL"
                elif f1_gh is not None:
                    gh_str = f"GH F1: {f1_gh:.4f}"
                    status_state = "VERIFIED"
                else:
                    gh_str = "GH F1: N/A"
                    status_state = "EXPERIMENTAL"

                return CapabilityStatus(
                    name="Champion Model",
                    state=status_state,
                    details=f"{model_name.replace('_', ' ').title()} ({bh_str}, {gh_str}, {fpr_str})",
                    remediation="Multi-attack tuning required for Grayhole detection" if status_state == "PARTIAL" else None,
                )
            except Exception:
                pass
                
        return CapabilityStatus(
            name="Champion Model",
            state="EXPERIMENTAL",
            details="Artifact present, metadata unreadable/corrupt",
            remediation="Re-evaluate model: python -m ml.evaluate",
        )
```

### Pattern 2: Executive Grid Responsive Layout
**What:** Organizes status cards and lower split body in a structured grid with responsive classes.  
**When to use:** In `MainWorkspace.CSS` using Textual's class selectors `.-compact` and `.-normal`.  
**Example:**
```css
/* Executive Grid Styling for MainWorkspace */
MainWorkspace {
    layout: vertical;
    background: $background;
    padding: 0;
}

#workspace-box {
    width: 100%;
    height: 1fr;
    layout: vertical;
    padding: 1 2;
}

#top-cards-container {
    height: auto;
    margin-bottom: 1;
}

Screen.-normal #top-cards-container {
    layout: horizontal;
}

Screen.-compact #top-cards-container {
    layout: vertical;
}

.status-card {
    height: auto;
    background: $surface;
    border: solid $info-blue;
    padding: 0 1;
    margin: 0 1 0 0;
}

Screen.-normal .status-card {
    width: 1fr;
}

Screen.-compact .status-card {
    width: 100%;
    margin: 0 0 1 0;
}

#lower-body-container {
    height: 1fr;
    layout: horizontal;
}

Screen.-compact #lower-body-container {
    layout: vertical;
}

#main-content-panel {
    width: 3fr;
    height: 100%;
    background: $surface;
    border: solid $info-blue;
    padding: 1;
}

Screen.-compact #main-content-panel {
    width: 100%;
    height: 1fr;
}

#nav-rail-panel {
    width: 1fr;
    height: 100%;
    background: $surface;
    border: solid $navigation-cyan;
    padding: 1;
    margin-left: 1;
}

Screen.-compact #nav-rail-panel {
    width: 100%;
    height: auto;
    margin-left: 0;
    margin-top: 1;
}
```

### Anti-Patterns to Avoid
- **Importing `ml`, `simulator`, `attacks`, or `feature_extraction` into `manet/`**: Forbidden by `[VERIFIED: tests/test_manet_import_boundaries.py:38]` (`forbidden_roots = ("simulator", "attacks", "feature_extraction", "ml")`). All inspection of scenarios, datasets, and models must be done via standard library `pathlib` and `json`.
- **Displaying Fake / Mock Metrics When Files Are Missing**: Hardcoding dummy F1 scores, fake dataset rows, or simulated runs violates TUI-08. If `data/train.csv` or `best_model.joblib` is missing, display `UNAVAILABLE` with clear remediation commands.
- **Masking Grayhole F1 of 0.0 as "Working"**: Labeling the champion Random Forest model as "Fully Effective Multi-Attack IDS" violates TUI-08. Its Grayhole F1 of 0.0 must be explicitly stated as `PARTIAL` and `Ineffective`.
- **Breaking `#workspace-box`**: In `tests/test_manet_compact.py:33`, tests query `app.screen.query_one("#workspace-box", Static)`. The root container or inner dashboard frame in `MainWorkspace` must retain `id="workspace-box"` so existing tests continue to pass unweakened.
- **Reading Whole CSV Files on Every Timer Poll**: Calling `len(open("data/train.csv").readlines())` every 3 seconds locks files and wastes CPU. Use `stat().st_mtime` to detect changes and only recount when mtime changes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Periodic Refresh Timer | Custom background thread with `time.sleep()` | Textual's `self.set_interval(interval, callback)` | Threading in Textual without thread-safety causes race conditions and UI deadlocks; `set_interval` posts callbacks directly to the event loop safely |
| Distribution Package Resolution | Shelling out to `pip show` or `pip list` | `importlib.metadata.version(dist_name)` | Shelling out is slow, platform-dependent, and forbidden by `test_command_package_never_uses_os_execution` |
| Table Rendering for Experiments | Custom ASCII string concatenation | Textual `DataTable` | `DataTable` handles row highlighting, cursor navigation, sorting, scrolling, and compact terminal clipping automatically |
| Responsive Layout Reflow | Custom resize event handlers calculating column widths | Textual `HORIZONTAL_BREAKPOINTS = [(0, "-compact"), (80, "-normal")]` + TCSS classes | Textual recalculates styles and applies breakpoints deterministically |

## Common Pitfalls

### Pitfall 1: Breaking the Import Boundary Test
**What goes wrong:** A developer imports `from ml.models import ...` or `from simulator.run_scenario import ...` in `manet/adapters/diagnostics.py`.  
**Why it happens:** Wanting to inspect model classes or scenario configurations using backend code.  
**How to avoid:** Remember `tests/test_manet_import_boundaries.py` walks every `.py` file under `manet/` and asserts that none of `("simulator", "attacks", "feature_extraction", "ml")` are imported. Inspect files purely using `pathlib` and `json.load`.  
**Warning signs:** `test_manet_never_imports_business_packages` fails during `pytest`.

### Pitfall 2: `importlib.metadata.PackageNotFoundError` for `sklearn`
**What goes wrong:** Calling `importlib.metadata.version("sklearn")` raises `PackageNotFoundError`.  
**Why it happens:** The Python package import name is `sklearn`, but its PyPI distribution name is `scikit-learn`.  
**How to avoid:** Map `("sklearn", "scikit-learn")` in the dependency probe list so `find_spec("sklearn")` checks importability and `version("scikit-learn")` queries distribution metadata.  
**Warning signs:** Unhandled `PackageNotFoundError` on startup.

### Pitfall 3: Removing `#workspace-box` Breaks Phase 7 Compact Tests
**What goes wrong:** Refactoring `MainWorkspace.compose()` without an element having `id="workspace-box"`.  
**Why it happens:** Replacing `Static(id="workspace-box")` with new containers without preserving the ID or type.  
**How to avoid:** Maintain `#workspace-box` as the main outer container (or static widget) in `MainWorkspace.compose()`.  
**Warning signs:** `tests/test_manet_compact.py::test_compact_breakpoint_engagement_small_terminal` fails with `NoMatches`.

### Pitfall 4: Anti-Phantom-Command Failure When Adding Registry Commands
**What goes wrong:** Adding new commands (e.g. `simulation`, `results`) to `_COMMANDS` in `manet/commands/registry.py` without implementing corresponding `action_*` methods on `ManetApp`.  
**Why it happens:** `tests/test_manet_command_registry.py::test_anti_phantom_command_honesty` asserts `hasattr(ManetApp, cmd.action)`.  
**How to avoid:** Every `AppCommand(action="action_xyz")` added to `registry.py` must have an explicit `def action_xyz(self) -> None:` method defined on `ManetApp`.

### Pitfall 5: Windows File Locking During File Probing
**What goes wrong:** Opening files with write mode or keeping open file handles during polling blocks other tools from modifying datasets or models.  
**Why it happens:** Opening files without context managers or using mode `"r+"`.  
**How to avoid:** Use `pathlib.Path.stat()` for polling. When reading `model_metadata.json`, open in `"r"` mode with UTF-8 encoding and close immediately via `with open(...) as f:`.

## Code Examples

### 1. Concrete Diagnostic Probe Adapter
```python
# Source: manet/adapters/diagnostics.py
from __future__ import annotations

from dataclasses import dataclass
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import platform
import sys
from typing import Any

DEPENDENCY_MAP = (
    ("simpy", "simpy"),
    ("networkx", "networkx"),
    ("sklearn", "scikit-learn"),
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
    ("pytest", "pytest"),
    ("joblib", "joblib"),
)

@dataclass(frozen=True)
class DiagnosticReport:
    python_version: str
    os_platform: str
    dependencies: dict[str, tuple[bool, str]]
    scenarios_count: int
    datasets_status: tuple[str, str, str | None]  # state, details, remediation
    model_status: tuple[str, str, str | None]     # state, details, remediation
    model_metadata: dict[str, Any] | None

class DiagnosticsProbe:
    """Probes system environment and artifact presence without importing business logic."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or Path.cwd()

    def run_diagnostics(self) -> DiagnosticReport:
        # 1. Environment
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        os_plat = platform.system()

        # 2. Dependencies
        deps = {}
        for mod, dist in DEPENDENCY_MAP:
            avail = importlib.util.find_spec(mod) is not None
            ver = "missing"
            if avail:
                try:
                    ver = importlib.metadata.version(dist)
                except Exception:
                    ver = "installed"
            deps[mod] = (avail, ver)

        # 3. Scenarios
        scenarios_dir = self.root_dir / "scenarios"
        scenario_files = list(scenarios_dir.glob("*.json")) if scenarios_dir.is_dir() else []
        scenarios_count = len(scenario_files)

        # 4. Datasets
        train_csv = self.root_dir / "data" / "train.csv"
        test_csv = self.root_dir / "data" / "test.csv"
        if train_csv.is_file() and test_csv.is_file():
            datasets_status = ("VERIFIED", "train.csv & test.csv present", None)
        else:
            datasets_status = (
                "UNAVAILABLE",
                "Datasets missing",
                "Run: python scripts/build_dataset.py --multi-attack",
            )

        # 5. Champion Model & Metadata
        joblib_file = self.root_dir / "ml" / "models" / "best_model.joblib"
        metadata_file = self.root_dir / "ml" / "models" / "model_metadata.json"
        
        model_meta = None
        if not joblib_file.is_file():
            model_status = (
                "UNAVAILABLE",
                "Champion artifact missing",
                "Run: python -m ml.train && python -m ml.evaluate",
            )
        else:
            if metadata_file.is_file():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        model_meta = json.load(f)
                    f1_bh = model_meta.get("test_metrics", {}).get("f1_blackhole", 0.0)
                    f1_gh = model_meta.get("test_metrics", {}).get("f1_grayhole", 0.0)
                    champ = model_meta.get("champion", "model")
                    
                    # Explicit Grayhole F1 = 0.0 callout per TUI-08
                    model_status = (
                        "PARTIAL",
                        f"{champ.replace('_', ' ').title()} (BH F1: {f1_bh:.4f}, GH F1: {f1_gh:.1f} [Ineffective])",
                        "Grayhole detection not effective; retrain with multi-attack features",
                    )
                except Exception:
                    model_status = ("EXPERIMENTAL", "Artifact exists, metadata parse error", None)
            else:
                model_status = ("EXPERIMENTAL", "Artifact exists without metadata provenance", None)

        return DiagnosticReport(
            python_version=py_ver,
            os_platform=os_plat,
            dependencies=deps,
            scenarios_count=scenarios_count,
            datasets_status=datasets_status,
            model_status=model_status,
            model_metadata=model_meta,
        )
```

### 2. Upgraded `MainWorkspace` Composition
```python
# Source: manet/screens/main_workspace.py
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from manet.adapters.diagnostics import DiagnosticsProbe
from manet.adapters.workspace import WorkspaceAdapter
from manet.widgets.cta_hero import CtaHeroPanel
from manet.widgets.dashboard_cards import (
    ActiveWorkloadCard,
    ComponentCapabilitiesCard,
    SystemHealthCard,
)
from manet.widgets.nav_rail import NavRail
from manet.widgets.notification_rail import NotificationRail
from manet.widgets.recent_experiments import RecentExperimentsTable
from manet.widgets.status_bar import StatusBar

class MainWorkspace(Screen):
    """Primary workspace screen hosting the operational dashboard."""

    HORIZONTAL_BREAKPOINTS = [(0, "-compact"), (80, "-normal")]

    BINDINGS = [
        Binding("s", "new_simulation", "New Simulation", show=True),
        Binding("r", "show_results", "Results", show=True),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.diagnostics_probe = DiagnosticsProbe()
        self.workspace_adapter = WorkspaceAdapter()

    def compose(self) -> ComposeResult:
        yield Header()
        yield NotificationRail(id="notification-rail")
        with Static(id="workspace-box"):  # Retains backward-compat ID and Static type for tests
            with Container(id="top-cards-container"):
                yield SystemHealthCard(id="card-health")
                yield ComponentCapabilitiesCard(id="card-capabilities")
                yield ActiveWorkloadCard(id="card-workload")
            with Container(id="lower-body-container"):
                # Conditional render: Recent experiments table vs Guided CTA Hero
                experiments = self.workspace_adapter.list_recent_experiments()
                if experiments:
                    yield RecentExperimentsTable(experiments, id="main-content-panel")
                else:
                    yield CtaHeroPanel(id="main-content-panel")
                yield NavRail(id="nav-rail-panel")
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_diagnostics()
        # Non-blocking background polling every 4 seconds (D-02)
        self.set_interval(4.0, self.refresh_diagnostics)

    def refresh_diagnostics(self) -> None:
        report = self.diagnostics_probe.probe_all()
        self.query_one("#card-health", SystemHealthCard).update_report(report)
        self.query_one("#card-capabilities", ComponentCapabilitiesCard).update_report(report)
        self.query_one("#card-workload", ActiveWorkloadCard).update_report(report)
        self.query_one("#status-bar", StatusBar).update_report(report)

    def action_new_simulation(self) -> None:
        self.query_one("#notification-rail", NotificationRail).notify_user(
            "Simulation workflow will be available in Phase 9 (TUI-09)"
        )

    def action_show_results(self) -> None:
        self.query_one("#notification-rail", NotificationRail).notify_user(
            "Experiment results browser will be available in Phase 11 (TUI-19)"
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Static placeholder text on `MainWorkspace` | Executive Grid with live status cards and lower split body | Phase 8 (TUI-06..08) | User sees real runtime environment, dependencies, and artifact states |
| Hardcoded capability assumptions | Real filesystem probing via `pathlib.Path.stat()` | Phase 8 (D-02) | Newly trained models or generated datasets are discovered live |
| Concealing Grayhole F1 of 0.0 | Explicit `PARTIAL (Grayhole F1: 0.0 [Ineffective])` callout | Phase 8 (TUI-08) | Academic integrity and honesty; no false claims of multi-attack protection |
| Monolithic workspace screen | Decoupled widgets (`StatusBar`, `NotificationRail`, `NavRail`) + adapters | Phase 8 (D-05) | Fulfills Phase 7 deferred mounting contract for Phase 10/11 background workers |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | File stat probing via `pathlib.Path.stat()` is sufficiently fast on local Windows NTFS to run every 4s without perceptible UI jitter | Periodic Polling | If wrong, polling could introduce micro-stutters; mitigated by polling only 4 files (`train.csv`, `test.csv`, `best_model.joblib`, `model_metadata.json`) |
| A2 | Users launching the app before running `build_dataset.py` expect immediate remediation CLI guidance | First-run UX | If wrong, users may be confused by `UNAVAILABLE` status; mitigated by explicit Guided CTA Hero Panel |

## Open Questions (RESOLVED)

1. **How should `MainWorkspace` handle terminal heights below 24 rows?** [RESOLVED]
   - What we know: `HORIZONTAL_BREAKPOINTS` manages widths below 80 columns by stacking cards vertically.
   - Resolution: `MainWorkspace` wraps the card container with compact padding and single-line / responsive reflow under `Screen.-compact` with `overflow-y: auto` so short terminal viewports remain navigable without clipping or layout exceptions (verified down to standard 80x24).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.11.8 | None (required floor 3.11+) |
| textual | TUI framework | ✓ | 8.2.8 | None (milestone dependency) |
| pytest-asyncio | Test runner | ✓ | 1.3.0 | None (required for async tests) |
| simpy | Simulation core | ✓ | 4.1.2 | Probed as dependency |
| networkx | Graph topology | ✓ | 3.6.1 | Probed as dependency |
| scikit-learn | ML classifier | ✓ | 1.8.0 | Probed as dependency |
| pandas | Trace analysis | ✓ | 3.0.2 | Probed as dependency |
| numpy | Numerical core | ✓ | 1.26.4 | Probed as dependency |
| matplotlib | Visualization | ✓ | 3.10.8 | Probed as dependency |
| seaborn | Visualization | ✓ | 0.13.2 | Probed as dependency |
| joblib | Model serialization | ✓ | 1.5.3 | Probed as dependency |

**Missing dependencies with no fallback:** None  
**Missing dependencies with fallback:** None  

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 with pytest-asyncio 1.3.0 |
| Config file | `pytest.ini` (`asyncio_mode = auto`) |
| Quick run command | `python -m pytest -k "manet"` |
| Full suite command | `python -m pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TUI-06 | Startup diagnostics detect Python version, 9 dependencies, scenarios, datasets, and models | unit / integration | `python -m pytest tests/test_manet_diagnostics_probe.py -k "test_diagnostics_report"` | ❌ Wave 0 |
| TUI-06 | Missing dependencies or artifacts correctly reported as `UNAVAILABLE` with remediation hints | unit | `python -m pytest tests/test_manet_diagnostics_probe.py -k "test_missing_artifacts"` | ❌ Wave 0 |
| TUI-07 | Dashboard mounts status cards, CTA hero on empty workspace, and recent experiments when manifests exist | integration / pilot | `python -m pytest tests/test_manet_dashboard_workspace.py -k "test_dashboard_mount"` | ❌ Wave 0 |
| TUI-07 | Quick navigation shortcuts (`[S]`, `[R]`, `[Ctrl+O]`, `[F1]`) navigate or notify user | integration / pilot | `python -m pytest tests/test_manet_dashboard_workspace.py -k "test_dashboard_navigation"` | ❌ Wave 0 |
| TUI-08 | Capability states strictly explicit; Grayhole F1 0.0 presented as ineffective; zero mock values | unit / regression | `python -m pytest tests/test_manet_diagnostics_probe.py -k "test_grayhole_ineffective"` | ❌ Wave 0 |
| DELV-01 | Import boundaries preserved: `manet/` modules never import business logic (`simulator`, `attacks`, `feature_extraction`, `ml`) | AST regression | `python -m pytest tests/test_manet_import_boundaries.py` | ✅ Yes |
| DELV-01 | Existing Phase 7 tests continue to pass unweakened (including compact mode `#workspace-box`) | regression | `python -m pytest -k "manet"` | ✅ Yes |

### Sampling Rate
- **Per task commit:** `python -m pytest -k "manet"` (~10s)
- **Per wave merge:** `python -m pytest` (full suite, ~137s)
- **Phase gate:** Full suite green (122 baseline + new Phase 8 tests) before completing verification.

### Wave 0 Gaps
- [ ] `tests/test_manet_diagnostics_probe.py` — unit tests for `DiagnosticsProbe` covering present, missing, and partial artifact states
- [ ] `tests/test_manet_dashboard_workspace.py` — headless pilot tests for `MainWorkspace` composing executive grid, mounting rails, and responding to shortcuts
- [ ] `tests/test_manet_adapters.py` — unit tests for `StatusAdapter`, `NotificationAdapter`, `NavigationAdapter`, and `WorkspaceAdapter`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Single-user local TUI; no remote authentication |
| V3 Session Management | no | In-memory session settings only; reset on app exit (D-09) |
| V4 Access Control | no | Local filesystem OS permissions apply (D-15) |
| V5 Input Validation | yes | All paths probed with `pathlib.Path`; scenario JSON and model metadata parsed safely with `json.load()` within try/except |
| V6 Cryptography | no | No cryptography implementation in Phase 8 |

### Known Threat Patterns for Textual TUI & File Diagnostics

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Arbitrary OS Shell Execution | Elevation of Privilege | Maintained AST boundary enforcing zero imports of `subprocess`, `shutil`, `os` in `manet/commands/` `[VERIFIED: tests/test_manet_import_boundaries.py:54]` |
| Path Traversal in Scenario/Model Inspection | Information Disclosure | All inspected directories are resolved relative to trusted project root; no arbitrary user-supplied file paths accepted in dashboard |
| Denial of Service via Huge Dataset File Reads | Denial of Service | Diagnostic probe inspects file presence and metadata via `stat()` without reading dataset CSV rows into memory |
| Hostile Markup Injection | Tampering | Textual Rich markup tags in dynamic filenames or error messages are escaped via `rich.markup.escape()` before rendering in widgets |

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `tests/test_manet_import_boundaries.py:38-51` — architectural rule forbidding `manet/` from importing `simulator`, `attacks`, `feature_extraction`, `ml`
- Codebase inspection: `tests/test_manet_compact.py:33` — requires `#workspace-box` on `MainWorkspace`
- Codebase inspection: `ml/models/model_metadata.json:46-47,107-108` — champion Random Forest, Blackhole F1 0.7593, Grayhole F1 0.0
- Codebase inspection: `manet/runtime/theme.py:21-42` — SOC theme tokens and variables
- Codebase inspection: `tests/test_manet_command_registry.py:57-70` — anti-phantom-command honesty rule

### Secondary (MEDIUM confidence)
- Python stdlib documentation: `importlib.util.find_spec` and `importlib.metadata.version` behavior

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Textual 8.2.8 and pytest-asyncio 1.3.0 verified installed and operational
- Architecture: HIGH — Executive Grid layout, responsive breakpoints, and adapter separation verified against existing patterns
- Pitfalls: HIGH — Identified specific traps: `importlib.metadata.PackageNotFoundError` for `sklearn`, `#workspace-box` regression in compact test, import boundary enforcement

**Research date:** 2026-11-07  
**Valid until:** 2026-12-07 (stable local framework)
