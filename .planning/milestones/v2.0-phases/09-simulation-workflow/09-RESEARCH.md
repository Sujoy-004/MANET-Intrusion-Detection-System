# Phase 9: Simulation Workflow - Research
**Researched:** 2026-11-07
**Domain:** Terminal User Interface (Textual 8.2.8), MANET Simulation Configuration, Validation, Workspace Allocation
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Screen Flow & Navigation
- **D-01:** Multi-Step Guided Wizard architecture (`SimulationWorkflowScreen` / `WizardController`) with three clear sequential steps:
  1. **Step 1: Scenario & Mode Selection**: Choose between authentic presets discovered from `scenarios/*.json` (displaying real names, descriptions, node count, duration) or creating a custom simulation.
  2. **Step 2: Parameter Configuration**: Edit core simulation variables (nodes, duration, seed, attacker strategy, IDS toggle) with progressive disclosure for advanced networking dials.
  3. **Step 3: Pre-Flight Review & Confirmation**: View a consolidated summary of all parameters, estimated scale, champion model status, collision-free workspace destination, and confirm launch.
  - **Reversibility:** costly — defines the wizard controller, step navigation messages, and widget mounting hierarchy in `manet/screens/`.

#### Input Validation & Guidance
- **D-02:** Two-Tier Validation Strategy:
  - **Tier 1 (Local Field Blur Validation):** Form inputs use Textual's blur validation (`validate_on=["blur"]`) to validate basic syntax, positive integers, and range boundaries (e.g. nodes >= 2, duration > 0, integer seed) without premature error flashes during active typing.
  - **Tier 2 (Pre-Flight Review Blocker):** Structural cross-field invariants (e.g. flow source/destination within node count, distinct flow endpoints, and on-disk model artifact verification `ml/models/best_model.joblib` when IDS is enabled) are evaluated prior to review. The final "Launch" action is strictly disabled with actionable remediation notes if validation fails.
  - **Reversibility:** reversible — validation logic lives in modular schemas and adapters under `manet/adapters/`.

#### Custom Parameter Depth
- **D-03:** Progressive Disclosure Layout:
  - **Primary Core Form:** Displays the 5 essential macro parameters by default (Nodes, Duration, Random Seed, Attacker Class [None, Blackhole, Grayhole], and IDS Mitigation Toggle). Fits cleanly in standard and compact terminals (80x24) without layout distortion.
  - **Collapsible Advanced Section:** An expandable container (`Collapsible`) pre-populated with standard benchmark defaults allowing override of granular knobs (Radio Range: 250.0m, Channel Loss Probability: 0.0, Mobility Speed: 1.0-20.0 m/s, Pause Time: 0.0s, CBR Packet Rate: 4.0 pkt/s, Area: 1000x1000m).
  - **Reversibility:** reversible — configuration builder maps defaults to the standard runner schema.

#### Experiment Naming & Workspace Allocation
- **D-04:** Deterministic Identifier with Optional Semantic Tag:
  - **Default Unique Identifier:** Automatically generated as `exp_YYYYMMDD_HHMMSS_<scenario>_<seed>`.
  - **Optional Custom Tag:** Provides an optional "Run Tag / Label" field; when supplied, the identifier becomes `exp_YYYYMMDD_HHMMSS_<scenario>_<seed>_<sanitized_tag>`.
  - **Workspace Directory Allocation:** Generates a dedicated directory under `.manet-workspace/<experiment_id>/` without overwriting existing traces, datasets, models, or experiment records.
  - **Input Sanitization:** Automatically strips spaces, symbols, and Windows-illegal path characters (`\ / : * ? " < > |`) from user-provided tags.
  - **Reversibility:** reversible.

### the agent's Discretion
- Exact Textual widget composition for preset scenario lists (e.g. `OptionList` vs. `DataTable` with scenario details).
- Visual badge styling and color mapping (`$primary`, `$success`, `$warning`, `$error`) for validation messages and IDS gating notices.
- Launch execution handoff adapter interface structure connecting Phase 9 review confirmation to Phase 10's background runner.

### Deferred Ideas (OUT OF SCOPE)
- Background worker thread execution and live progress polling — Phase 10 (TUI-15, TUI-16, TUI-17, TUI-18).
- Experiment results viewer, manifest checksum generation, and session history browsing — Phase 11 (TUI-19, TUI-20, TUI-21).
- In-TUI live model retraining / evaluation workload runner — Phase 10 / future scope (TUI-MLWORK).
- Interactive packet replay and animation — future milestone (VIZ-01).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **TUI-09** | User can start a validated preset run by choosing a scenario JSON from `scenarios/` shown with its real name, description, and relevant parameters (actual file schema, not documented examples) | Scenario adapter scans `scenarios/*.json` via `pathlib` and `json.load()`, extracting verified schema fields (`scenario_id`, `description`, `nodes`, `duration`, `attack`, `radio`, `mobility`, `flows`). |
| **TUI-10** | User can start a custom run configuring only parameters the actual runner supports, with validation of node counts, flow endpoints, durations, seed, and numeric ranges | Progressive disclosure form with 5 macro fields + `Collapsible` for advanced knobs; two-tier validator verifies bounds and cross-field constraints matching `SimulationRunner`. |
| **TUI-11** | User can select the random seed explicitly for any run | Integer input widget with `validate_on=["blur"]`, integer range `[0, 2147483647]`, default 42, passed to runner configuration. |
| **TUI-12** | User can enable IDS only when the champion model artifact exists, and never otherwise | Invariant check on `ml/models/best_model.joblib`; if missing, `Switch.disabled = True` with explanatory remediation badge (`python scripts/build_dataset.py --multi-attack && python -m ml.train && python -m ml.evaluate`). |
| **TUI-13** | User confirms a review screen before any run launches, and each run executes into a unique experiment directory under a dedicated `.manet-workspace/` without overwriting existing traces, datasets, models, or experiment records | Step 3 Pre-Flight Review screen shows complete summary; `WorkspaceAdapter.allocate_experiment_directory` generates `exp_YYYYMMDD_HHMMSS_<scenario>_<seed>[_<tag>]` with collision detection. |
| **TUI-14** | Each experiment records scenario, seed, configuration, software version, and start time at launch, using the existing `SimulationRunner`, scenario loader, and metric functions with output compatible with the current trace schema and legacy CLI behavior | Launch manifest written to `.manet-workspace/<experiment_id>/manifest.json` containing `experiment_id`, `scenario_name`, `seed`, `configuration`, `software_version` ("2.0.0-dev"), `created_at`, `status` ("CONFIGURED"), trace path `trace.csv`. |
</phase_requirements>

---

## Summary

Phase 9 establishes the simulation configuration, parameter validation, review, and workspace allocation workflows in the `manet/` Textual application. It replaces the temporary Phase 8 "simulation pending" notification triggered by `[S]` with an interactive, keyboard-navigable multi-step wizard (`SimulationWorkflowScreen`).

The wizard guides the user through three distinct steps:
1. **Scenario & Mode Selection**: Real preset discovery from `scenarios/*.json` (verifying actual schemas without mock files) or initiating a custom scenario configuration.
2. **Parameter Configuration**: Form editing of core simulation dials (nodes, duration, integer seed, attacker class, IDS toggle) with a collapsible container for advanced parameters (radio range, loss probability, speed range, pause time, CBR packet rate, area, and attack-specific dials).
3. **Pre-Flight Review & Confirmation**: Consolidated summary of all parameters, estimated simulation scale, champion model status, collision-free workspace destination, and launch confirmation.

Architecturally, Phase 9 strictly respects the project's one-way import boundary: `manet/` modules never import business logic packages (`simulator`, `attacks`, `feature_extraction`, `ml`). All scenario inspection, configuration compilation, and workspace allocation are handled via standard library utilities (`pathlib`, `json`, `datetime`) and dedicated adapters (`manet/adapters/scenario.py`, `manet/adapters/simulation_config.py`, and extending `manet/adapters/workspace.py`). Phase 9 produces a fully compliant scenario configuration dictionary and allocates the experiment workspace, writing an initial `manifest.json`. The background worker thread execution, live event streaming, and progress tracking are deferred to Phase 10.

**Primary recommendation:** Implement a 3-step wizard screen using Textual's `ContentSwitcher` (`step-mode-select`, `step-param-config`, `step-preflight-review`), powered by a dedicated `ScenarioAdapter` and `SimulationConfigValidator`, wired to the `[S]` shortcut on `MainWorkspace` and `sim:start` in the command registry.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Authentic Scenario Discovery | `manet/adapters/scenario.py` | Filesystem (`scenarios/*.json`) | Reads and validates raw JSON schema without importing `simulator` |
| Local Field Validation | `manet/widgets/` (Textual Inputs) | `textual.validation` | Provides immediate blur-triggered syntax and range validation |
| Cross-Field Invariant Checking | `manet/adapters/simulation_config.py` | `manet/screens/simulation_workflow.py` | Enforces flow endpoint bounds and model existence before review |
| Wizard Navigation & State | `manet/screens/simulation_workflow.py` | `textual.widgets.ContentSwitcher` | Coordinates step transitions, back/next actions, and shortcut bindings |
| Workspace Allocation & Manifest | `manet/adapters/workspace.py` | Filesystem (`.manet-workspace/`) | Creates collision-free directory and writes initial `manifest.json` |
| Execution Handoff Interface | `manet/adapters/handoff.py` | Phase 10 Worker Interface | Hands off validated `SimulationLaunchRequest` without importing `simulator` |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `textual` | 8.2.8 | Full-screen terminal UI framework, widgets, validation, layout | Verified installed; provides `ContentSwitcher`, `Collapsible`, `Select`, `Switch`, `Input`, `DataTable` |
| `pathlib` | stdlib | Filesystem traversal and path manipulation | Native Windows-safe path handling, required for repo paths with spaces |
| `json` | stdlib | Scenario reading, configuration dumping, manifest writing | Standard data format across `scenarios/*.json` and `manifest.json` |
| `dataclasses` | stdlib | Strongly-typed internal records (`ScenarioMetadata`, `LaunchPayload`) | High readability, immutable (`frozen=True`), zero external dependency |
| `datetime` | stdlib | UTC timestamp generation for experiment IDs and manifests | ISO-8601 formatting for deterministic audit trails |
| `re` | stdlib | Input sanitization for user run tags | Strips illegal filesystem characters and whitespace |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `rich` | (textual bundle) | Terminal markup, styling, text escaping | Rendering color badges and escaped table cells |
| `pytest` | 9.0.2 | Test suite runner | Automated unit and integration testing |
| `pytest-asyncio` | 1.3.0 | Async test runner | Headless pilot testing of Textual screens |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ContentSwitcher` | Separate Screen push/pop per step | Screen push/pop breaks wizard state continuity; `ContentSwitcher` preserves controller state across Back/Next |
| `validate_on=["blur"]` | `validate_on=["changed"]` | "changed" flashes red errors while the user is actively typing a multi-digit number |
| Standard Library JSON | Pydantic models | Pydantic is an unnecessary dependency for internal configuration dictionaries; stdlib `dataclasses` + `json` preserves the minimal-dependency mandate |

---

## Package Legitimacy Audit

> All required packages are already installed and locked in the environment. No new external dependencies are required or permitted for Phase 9.

| Package | Registry | Installed Version | Status | Verdict | Disposition |
|---------|----------|-------------------|--------|---------|-------------|
| `textual` | PyPI | 8.2.8 | Verified present | [OK] | Approved |
| `pytest` | PyPI | 9.0.2 | Verified present | [OK] | Approved |
| `pytest-asyncio` | PyPI | 1.3.0 | Verified present | [OK] | Approved |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
User Action: Press [S] or 'sim:start'
                 │
                 ▼
    ┌──────────────────────────┐
    │ SimulationWorkflowScreen │ ◄── WizardController State
    └────────────┬─────────────┘
                 │
       ┌─────────┴───────────────────────┐
       ▼                                 ▼
┌─────────────────────────┐   ┌──────────────────────────┐
│ Mode A: Preset Scenario │   │ Mode B: Custom Scenario  │
│ - Scan scenarios/*.json │   │ - Pre-populated defaults │
│ - Display schema fields │   │ - Form Inputs (Nodes,    │
│ - Select preset         │   │   Duration, Seed, Class) │
└────────────┬────────────┘   └──────────┬───────────────┘
             │                           │
             └─────────────┬─────────────┘
                           ▼
              ┌──────────────────────────┐
              │ Step 2: Parameter Config │
              │ - Core Form (5 dials)    │
              │ - Collapsible Advanced   │
              │ - IDS Gated on Model     │
              │ - Tier 1 Blur Validation │
              └────────────┬─────────────┘
                           │ [Enter] / Next
                           ▼
              ┌──────────────────────────┐
              │ Tier 2 Validator         │
              │ - Endpoints in [0, N-1]  │
              │ - src != dst             │
              │ - best_model.joblib check│
              └────────────┬─────────────┘
                           │ Passed
                           ▼
              ┌──────────────────────────┐
              │ Step 3: Pre-Flight Review│
              │ - Consolidated Summary   │
              │ - Scale Estimation       │
              │ - Unique Workspace Path  │
              └────────────┬─────────────┘
                           │ [Enter] / Launch
                           ▼
              ┌──────────────────────────┐
              │ Workspace Allocation     │
              │ - exp_YYYYMMDD_...       │
              │ - Write manifest.json    │
              │ - Handoff to Phase 10    │
              └──────────────────────────┘
```

### Recommended Project Structure
```
manet/
├── adapters/
│   ├── diagnostics.py          # Existing diagnostics probe
│   ├── handoff.py              # NEW: Launch execution handoff protocol & request dataclass
│   ├── scenario.py             # NEW: Authentic scenario discovery & metadata parsing
│   ├── simulation_config.py    # NEW: Parameter builder & two-tier validation engine
│   └── workspace.py            # EXTENDED: Directory allocation & initial manifest writing
├── commands/
│   └── registry.py             # EXTENDED: Add 'sim:start' command
├── runtime/
│   └── keymap.py               # EXTENDED: Update BINDING_SIMULATION hint
├── screens/
│   ├── main_workspace.py       # EXTENDED: [S] navigates to SimulationWorkflowScreen
│   └── simulation_workflow.py  # NEW: 3-step wizard screen with ContentSwitcher
└── widgets/
    ├── wizard_step_mode.py     # NEW: Step 1 widget (preset list / custom selector)
    ├── wizard_step_params.py   # NEW: Step 2 widget (core form + collapsible advanced)
    └── wizard_step_review.py   # NEW: Step 3 widget (pre-flight review summary)
```

### Pattern 1: Wizard State Machine with ContentSwitcher
**What:** Manage the 3-step configuration workflow inside a single Screen using Textual's `ContentSwitcher`.  
**When to use:** Multi-step forms where state must persist seamlessly when stepping back and forth.  
**Example:**
```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import ContentSwitcher, Footer, Header

class SimulationWorkflowScreen(Screen):
    BINDINGS = [
        ("escape", "cancel_or_back", "Back / Cancel"),
        ("enter", "next_or_launch", "Next / Confirm"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with ContentSwitcher(initial="step-mode-select", id="wizard-switcher"):
            yield StepModeSelectWidget(id="step-mode-select")
            yield StepParamsWidget(id="step-param-config")
            yield StepReviewWidget(id="step-preflight-review")
        yield Footer()

    def action_cancel_or_back(self) -> None:
        switcher = self.query_one("#wizard-switcher", ContentSwitcher)
        if switcher.current == "step-mode-select":
            self.app.switch_screen("workspace")
        elif switcher.current == "step-param-config":
            switcher.current = "step-mode-select"
        elif switcher.current == "step-preflight-review":
            switcher.current = "step-param-config"
```

### Pattern 2: Two-Tier Parameter Validation
**What:** Field-level syntax/bounds checking on blur, combined with whole-form semantic invariant checking before advancing to review.  
**When to use:** Complex network configurations where individual fields can be valid numbers, but relations between fields (e.g. flow endpoints vs. total node count) require structural validation.  
**Example:**
```python
from textual.validation import Integer, Number
from textual.widgets import Input

# Tier 1: Local blur validation
node_input = Input(
    value="30",
    validators=[Integer(minimum=2, maximum=100)],
    validate_on=["blur"],
    id="input-nodes",
)

# Tier 2: Structural cross-field validation
def validate_configuration(config: dict, model_path: Path) -> list[str]:
    errors = []
    num_nodes = config.get("nodes", 0)
    for flow in config.get("flows", []):
        src, dst = flow.get("src"), flow.get("dst")
        if src >= num_nodes or dst >= num_nodes:
            errors.append(f"Flow {src}->{dst} references node >= total nodes ({num_nodes})")
        if src == dst:
            errors.append(f"Flow source {src} cannot equal destination {dst}")
    if config.get("ids", {}).get("enabled", False) and not model_path.is_file():
        errors.append(f"IDS enabled but model artifact {model_path} does not exist on disk")
    return errors
```

### Pattern 3: Collision-Free Workspace Directory Allocation
**What:** Generating a guaranteed-unique directory under `.manet-workspace/` incorporating timestamp, scenario name, seed, and optional sanitized tag.  
**When to use:** Preparing an experiment execution destination before launch.  
**Example:**
```python
import datetime
import re
from pathlib import Path

def sanitize_tag(tag: str) -> str:
    # Strip spaces, symbols, and Windows-illegal characters \ / : * ? " < > |
    sanitized = re.sub(r'[\s\\/:*?"<>|]+', '_', tag.strip())
    return sanitized.strip('_')[:32]

def allocate_experiment_directory(
    workspace_root: Path,
    scenario_name: str,
    seed: int,
    tag: str | None = None
) -> tuple[str, Path]:
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_id = f"exp_{now_str}_{scenario_name}_{seed}"
    if tag:
        clean_tag = sanitize_tag(tag)
        if clean_tag:
            base_id = f"{base_id}_{clean_tag}"
    
    exp_dir = workspace_root / base_id
    counter = 1
    while exp_dir.exists():
        exp_dir = workspace_root / f"{base_id}_{counter}"
        counter += 1
    
    exp_dir.mkdir(parents=True, exist_ok=False)
    return exp_dir.name, exp_dir
```

### Anti-Patterns to Avoid
- **Importing `simulator` or `ml` inside `manet/`**: Strictly forbidden by `[VERIFIED: tests/test_manet_import_boundaries.py:38]`. All scenario discovery must use `json.load()` and `pathlib`.
- **Fashing errors while typing (`validate_on=["changed"]`)**: Prematurely marks partially-typed numbers (e.g. typing "10" starts with "1", which is invalid if min=2) as errors. Always use `validate_on=["blur"]`.
- **Overwriting existing runs**: Never use hardcoded paths or overwrite existing directories. Use collision-checked allocation under `.manet-workspace/`.
- **Allowing IDS toggle without model artifact**: Violates TUI-12. Toggle must be disabled with remediation instructions if `ml/models/best_model.joblib` is missing.
- **Mock scenario data**: Never hardcode scenario descriptions or names. Read directly from `scenarios/*.json`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form step switching | Custom widget hide/show DOM mutations | `textual.widgets.ContentSwitcher` | Manages display state and layout reactivity cleanly without DOM churn |
| Advanced parameter toggle | Custom expand/collapse containers | `textual.widgets.Collapsible` | Standard keyboard focus, title rendering, and expanded/collapsed symbols |
| Numeric validation | Custom regex or `try/except int()` on every keystroke | `textual.validation.Integer` / `Number` | Clean integration with Textual's validation protocol and blur event triggers |
| Option selection | Custom button grids for presets | `textual.widgets.OptionList` or `DataTable` | Built-in row cursor, arrow key navigation, and select events |
| Safe path sanitization | String replace chains | `re.sub(r'[\s\\/:*?"<>|]+', '_', tag)` | Prevents directory traversal and Windows-illegal character crashes |

**Key insight:** Textual 8.2.8 includes built-in form controls (`Input`, `Select`, `Switch`, `Collapsible`, `ContentSwitcher`). Hand-rolling custom container toggles or input validators introduces focus-trapping bugs and keyboard navigation regressions.

---

## Runtime State Inventory

> Phase 9 generates new runtime experiment directories under `.manet-workspace/`.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `.manet-workspace/<experiment_id>/` | Allocated cleanly with `mkdir(parents=True, exist_ok=False)` |
| Live service config | None | Purely local offline terminal application |
| OS-registered state | None | No daemon or scheduled tasks |
| Secrets/env vars | None | Zero credentials required |
| Build artifacts | `.manet-workspace/` ignored by Git | Verified in `.gitignore:2` (`.manet-workspace/` is local-only) |

---

## Common Pitfalls

### Pitfall 1: Breaking the Architectural Import Boundary
**What goes wrong:** A developer imports `from simulator.run_scenario import SimulationRunner` or `from ml.response import OnlineIDS` into `manet/adapters/scenario.py` or `manet/screens/simulation_workflow.py`.  
**Why it happens:** Convenient access to default values or runner classes.  
**How to avoid:** `tests/test_manet_import_boundaries.py` strictly fails if `manet/` imports `simulator`, `attacks`, `feature_extraction`, or `ml`. Keep `manet/` purely presentation and data-contract driven.  
**Warning signs:** AST test failure in `test_manet_never_imports_business_packages()`.

### Pitfall 2: Premature Validation Errors on Keystroke
**What goes wrong:** Red error highlights flash immediately when a user clears a field or starts typing a number.  
**Why it happens:** Using default `validate_on=["changed", "submitted"]` on `Input` widgets.  
**How to avoid:** Explicitly pass `validate_on=["blur"]` to all validated `Input` widgets (D-02).  
**Warning signs:** Form fields flashing red during normal typing.

### Pitfall 3: Broken Existing Navigation Tests
**What goes wrong:** `tests/test_manet_navigation.py` contains `test_simulation_shortcut_triggers_notice` which expects pressing `[S]` to show a "Phase 9 pending" notice on the notification rail.  
**Why it happens:** The test was written to verify Phase 8 placeholder behavior.  
**How to avoid:** Update `test_manet_navigation.py` to assert that pressing `[S]` opens `SimulationWorkflowScreen`, and pressing `[Esc]` returns to `MainWorkspace`.  
**Warning signs:** Test failure in `test_simulation_shortcut_triggers_notice`.

### Pitfall 4: Window Clipping in 80x24 Terminals
**What goes wrong:** Displaying all 15 simulation knobs simultaneously overflows standard 80x24 terminal heights, clipping action buttons.  
**Why it happens:** Not using progressive disclosure.  
**How to avoid:** D-03 mandates 5 primary core parameters by default, with granular dials housed in a `Collapsible(title="Advanced Network Parameters", collapsed=True)` container.  
**Warning signs:** Bottom action buttons pushed off-screen or scrollbar appearing on standard terminals.

### Pitfall 5: Windows Path Traversal and Illegal Characters in Run Tags
**What goes wrong:** User types a custom tag like `test/run*1` or `../bad`, crashing directory creation on Windows or escaping the workspace root.  
**Why it happens:** Blindly appending user input to filesystem paths.  
**How to avoid:** Strip all non-alphanumeric/underscore characters using regex and enforce a maximum tag length of 32 characters.  
**Warning signs:** `OSError: [WinError 123] The filename, directory name, or volume label syntax is incorrect`.

---

## Code Examples

### Scenario Metadata Loading (Adapter)
```python
# [VERIFIED: scenarios/e1_normal_30n.json:1-10]
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class ScenarioPreset:
    scenario_id: str
    description: str
    nodes: int
    duration: float
    attack_type: str
    raw_config: dict[str, Any]

class ScenarioAdapter:
    def __init__(self, scenarios_dir: Path | None = None) -> None:
        self.scenarios_dir = scenarios_dir or (Path.cwd() / "scenarios")

    def list_presets(self) -> list[ScenarioPreset]:
        if not self.scenarios_dir.is_dir():
            return []
        presets = []
        for json_path in sorted(self.scenarios_dir.glob("*.json")):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                presets.append(
                    ScenarioPreset(
                        scenario_id=data.get("scenario_id", json_path.stem),
                        description=data.get("description", "No description"),
                        nodes=int(data.get("nodes", 30)),
                        duration=float(data.get("duration", 300.0)),
                        attack_type=data.get("attack", {}).get("type", "None"),
                        raw_config=data,
                    )
                )
            except Exception:
                continue
        return presets
```

### Initial Launch Manifest Recording (Adapter)
```python
# [VERIFIED: simulator/run_scenario.py:48-51]
import datetime
import json
from pathlib import Path
from typing import Any
import manet

def record_launch_manifest(
    experiment_dir: Path,
    experiment_id: str,
    scenario_name: str,
    seed: int,
    config: dict[str, Any],
) -> Path:
    manifest_path = experiment_dir / "manifest.json"
    manifest_data = {
        "experiment_id": experiment_id,
        "scenario_name": scenario_name,
        "seed": seed,
        "status": "CONFIGURED",
        "software_version": manet.__version__,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "trace_path": str(experiment_dir / "trace.csv"),
        "configuration": config,
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    return manifest_path
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CLI-only scenario invocation (`python -m simulator.run_scenario --scenario ...`) | Interactive TUI Wizard with pre-flight parameter review | Milestone v2.0 | Eliminates manual JSON editing and flag memorization for demonstration |
| Unchecked user parameters | Two-tier validation (blur syntax + structural cross-field invariants) | Milestone v2.0 | Prevents runtime simulation crashes mid-run due to out-of-range node IDs |
| Traces written directly to `traces/` or `out.csv` | Isolated, collision-free workspace per run (`.manet-workspace/<experiment_id>/`) | Milestone v2.0 | Guarantees non-destructive runs, preserving past traces and manifests |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `scenarios/*.json` all adhere to top-level keys `['scenario_id', 'description', 'nodes', 'area', 'duration', 'mobility', 'radio', 'traffic', 'flows', 'attack']` | Phase Requirements | Low — verified via in-repo glob inspection across all 5 JSON files. |
| A2 | Flow endpoints in custom runs default to source 0 and destination `nodes - 1` | Architecture Patterns | Low — valid default satisfying `0 <= src < nodes` and `src != dst`. |

---

## Open Questions

1. **How should flow endpoints be specified in the custom form?**
   - What we know: Scenario files use a list of flow dictionaries with `src`, `dst`, `rate_pps`, `start_time`, `duration`.
   - Recommendation: For custom runs, provide configurable macro settings: Flow Source (`0`), Flow Destination (`nodes // 2` or `1`), and CBR Packet Rate (`4.0 pkt/s`). This covers standard academic test flows without cluttering the screen with multi-table flow editors. Advanced users can always select preset JSONs.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.11.8 | — (Hard requirement >= 3.11) |
| Textual | TUI Framework | ✓ | 8.2.8 | — |
| pytest | Test Runner | ✓ | 9.0.2 | — |
| pytest-asyncio | Async Pilot Tests | ✓ | 1.3.0 | — |
| `scenarios/*.json` | Preset Discovery | ✓ | 5 authentic files | — |
| `ml/models/best_model.joblib` | Champion Model Artifact | ✓ (or probe-checked) | Present or absent | IDS toggle disabled with remediation message if missing |

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `pytest` 9.0.2 + `pytest-asyncio` 1.3.0 |
| Config file | `pytest.ini` |
| Quick run command | `python -m pytest -k "simulation_workflow or scenario or workspace"` |
| Full suite command | `python -m pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| **TUI-09** | Load authentic preset scenarios from `scenarios/*.json` and display metadata | unit / async pilot | `python -m pytest tests/test_manet_scenario_adapter.py -k "test_preset_discovery"` | ❌ Wave 0 Gap |
| **TUI-10** | Custom configuration parameter validation (numeric bounds, flow endpoints, ranges) | unit | `python -m pytest tests/test_manet_simulation_config.py -k "test_custom_validation"` | ❌ Wave 0 Gap |
| **TUI-11** | Explicit seed selection and propagation into configuration | unit / async pilot | `python -m pytest tests/test_manet_simulation_config.py -k "test_seed_propagation"` | ❌ Wave 0 Gap |
| **TUI-12** | IDS toggle disabled when champion model is absent, enabled when present | unit / async pilot | `python -m pytest tests/test_manet_simulation_workflow.py -k "test_ids_gating"` | ❌ Wave 0 Gap |
| **TUI-13** | Pre-flight review screen confirmation and collision-free workspace allocation | unit / integration | `python -m pytest tests/test_manet_workspace_allocation.py -k "test_allocation"` | ❌ Wave 0 Gap |
| **TUI-14** | Launch manifest records scenario, seed, version, created_at, and is compatible with `SimulationRunner` | integration | `python -m pytest tests/test_manet_simulation_runner_compat.py -k "test_runner_compatibility"` | ❌ Wave 0 Gap |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_manet_*.py -k "simulation or scenario or workspace"` (< 15 seconds)
- **Per wave merge:** `python -m pytest tests/test_manet_*.py` (< 30 seconds)
- **Phase gate:** Full suite green (`python -m pytest`, 148+ tests passing) before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_manet_scenario_adapter.py` — unit tests for authentic preset discovery and metadata extraction (TUI-09).
- [ ] `tests/test_manet_simulation_config.py` — unit tests for two-tier validation, field limits, and flow endpoint invariant checks (TUI-10, TUI-11).
- [ ] `tests/test_manet_workspace_allocation.py` — unit tests for deterministic naming, collision avoidance, and manifest generation (TUI-13, TUI-14).
- [ ] `tests/test_manet_simulation_workflow.py` — Textual pilot tests for wizard navigation, IDS gating, and pre-flight confirmation (TUI-09..TUI-14).
- [ ] Update `tests/test_manet_navigation.py` — adapt `test_simulation_shortcut_triggers_notice` to assert `SimulationWorkflowScreen` navigation instead of placeholder notice.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | Yes | Two-tier validation: `Integer` / `Number` field blur validators, plus structural cross-field invariant checks. |
| V5.1 Sanitization | Yes | Run tag sanitization with `re.sub(r'[\s\\/:*?"<>|]+', '_', tag)` to prevent directory traversal and Windows-illegal filenames. |
| V4 Access Control | Yes | Workspace writes restricted strictly to `.manet-workspace/` directory tree; no path escaping. |

### Known Threat Patterns for Terminal Form & File Systems

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Directory Traversal via Run Tag | Tampering / Elevation | Strip `..`, slashes, colons, and illegal characters from run tag; resolve path strictly within `.manet-workspace/`. |
| Out-of-Bounds Flow Endpoints | Denial of Service / Crash | Validator ensures `0 <= src < nodes` and `0 <= dst < nodes` and `src != dst` before configuration confirmation. |
| Mock or Fabricated Model Claims | Repudiation / Integrity | Check actual existence of `ml/models/best_model.joblib` via `stat()` / `is_file()` before permitting IDS activation. |

---

## Sources

### Primary (HIGH confidence)
- `[VERIFIED: scenarios/e1_normal_30n.json:1-76]` — authentic preset scenario schema and parameters.
- `[VERIFIED: simulator/run_scenario.py:45-99, 560-625]` — `SimulationRunner` parameter acceptance, trace header, and CLI options.
- `[VERIFIED: tests/test_manet_import_boundaries.py:32-60]` — AST boundary rule: `forbidden_roots = ("simulator", "attacks", "feature_extraction", "ml")` in `manet/`.
- `[VERIFIED: manet/adapters/diagnostics.py:172-237]` — champion model artifact inspection logic on `ml/models/best_model.joblib`.
- `[VERIFIED: manet/adapters/workspace.py:22-103]` — existing workspace adapter reading `.manet-workspace/` manifests.
- `[VERIFIED: manet/runtime/keymap.py:10-25]` — global shortcut keymap definitions (`BINDING_SIMULATION = "s"`).

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Textual 8.2.8 installed and verified with comprehensive test coverage.
- Architecture: HIGH — Guided wizard with `ContentSwitcher` fits Textual patterns and respects import boundaries.
- Pitfalls: HIGH — Clear awareness of AST import boundaries, Windows path quirks, and blur validation.

**Research date:** 2026-11-07  
**Valid until:** 2026-12-07 (stable local framework)
