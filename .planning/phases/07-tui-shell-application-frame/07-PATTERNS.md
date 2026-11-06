# Phase 7: TUI Shell & Application Frame - Pattern Map

**Mapped:** 2026-11-06
**Files analyzed:** 24 (19 new `manet/` + test/config files, 3 modified docs/config)
**Analogs found:** 12 / 19 have codebase analogs for *convention* (imports, docstrings, dataclasses, entry-point style, test style, boundary tests). **0 have analogs for Textual framework mechanics** — the repo contains no Textual code; framework construction must come from 07-RESEARCH.md Patterns 1–5 (Context7-verified against the v8.2.8 tag).

## Codebase Reality Check (supersedes stale maps)

Verified against the live tree this session:

- `manet/` does **not** exist (greenfield).
- Root `tests/` exists with 11 `test_*.py` files — root-level tests convention confirmed.
- **No `pytest.ini` / `pyproject.toml` / `setup.cfg` anywhere in the repo** — confirmed. Every existing test is plain sync `def test_*()` (grep for `async def|asyncio` in `tests/` returned nothing). The pytest-asyncio `asyncio_mode = auto` gap (Pitfall 1 in RESEARCH) is real.
- **No `__main__.py` exists anywhere in the repo.** The `python -m` entry-point convention lives as the `main()` + `if __name__ == "__main__": main()` tail in `simulator/run_scenario.py` (invoked as `python -m simulator.run_scenario`). `manet/__main__.py` transfers that convention into a module named `__main__`.
- `GEMINI.md` at repo root is the live contract; the same rules now live there under "Import Organization", "Module Design", "Error Handling", "Documentation Sync Rule".
- README pinned install line: line 23 (`python -m pip install simpy==4.1.2 ... pytest==9.0.2 joblib==1.5.3`) — this is the surface the `textual==8.2.8` pin must join.
- CHANGELOG format: Keep a Changelog with `## [X.Y.Z] - YYYY-MM-DD` sections and `### Added/Changed/Fixed` — new entry follows this verbatim.
- Package `__init__.py` styles differ in weight: `simulator/__init__.py` = docstring + `__version__` only; `attacks/__init__.py` = re-exports + explicit `__all__` + boundary contract docstring; `ml/__init__.py` = one-line docstring. Use `attacks/__init__.py` as the model where `manet/__init__.py` re-exports.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `manet/__init__.py` | config (package surface) | static | `attacks/__init__.py` | convention-exact |
| `manet/__main__.py` | controller (launcher) | request-response | `simulator/run_scenario.py` `main()` + `__main__` tail | convention-exact (no `__main__.py` exists in repo — new mechanism) |
| `manet/app.py` | provider (App shell) | event-driven | none (Textual) + `simulator/run_scenario.py` composition-root convention | role-partial |
| `manet/screens/main_workspace.py` | component (Screen) | event-driven | none (Textual) | no analog — framework |
| `manet/screens/console.py` | component (Screen) | event-driven | none (Textual) | no analog — framework |
| `manet/screens/help_about.py` | component (Screen) | event-driven/static | none | no analog |
| `manet/screens/placeholder.py` | component (Screen factory) | event-driven/static | none | no analog |
| `manet/widgets/status_bar.py` | component (Widget) | event-driven | none (Textual) | no analog — framework |
| `manet/widgets/notification_rail.py` | component (Widget) | event-driven | none (Textual) | no analog — framework |
| `manet/widgets/nav_rail.py` | component (Widget) | event-driven | none (Textual) | no analog — framework |
| `manet/commands/registry.py` | model (AppCommand dataclass + resolver) | transform | `simulator/aodv.py` `@dataclass` records + `simulator/run_scenario.py` `NodeState` | convention-exact |
| `manet/commands/palette_provider.py` | provider (textual.command.Provider) | request-response | none (Textual) | no analog — framework |
| `manet/commands/console_driver.py` | utility (adapter) | request-response | none (Textual) | no analog — framework |
| `manet/adapters/__init__.py` + `noop.py` | service (stub interfaces) | event-driven | none — Phase 10/11 plug-ins land here | no analog |
| `manet/runtime/settings.py` | store (reactive session state) | event-driven | none (Textual reactive); dataclass style from `simulator/metrics.py` `NetworkMetrics` | role-partial |
| `manet/runtime/theme.py` | config (Theme constants) | static | none (Textual) | no analog |
| `manet/runtime/keymap.py` | config (Binding constants) | static | none (Textual) | no analog |
| `pytest.ini` (repo root, NEW) | config (test runner) | static | none — no pytest config exists in repo | no analog |
| `tests/test_manet_app_launch.py`, `tests/test_manet_entry.py`, `tests/test_manet_navigation.py`, `tests/test_manet_compact.py`, `tests/test_manet_command_palette.py`, `tests/test_manet_command_registry.py`, `tests/test_manet_theme.py` | test (async, Pilot) | event-driven | `tests/test_aodv_recovery.py` (structure/docstrings), asyncio mechanics from RESEARCH Pattern 5 | convention-exact structure / framework-mechanics gap |
| `tests/test_manet_import_boundaries.py` | test (sync, AST) | batch | `tests/test_import_boundaries.py` | **exact** |
| `README.md` (MODIFIED) | docs | static | its own pinned-install + workflow sections | exact |
| `CHANGELOG.md` (MODIFIED) | docs | static | its own Keep-a-Changelog sections | exact |
| `GEMINI.md` (MODIFIED, same commit as dependency) | contract docs | static | its own dependency-record rule | exact |

## Pattern Assignments

### `manet/__main__.py` (controller, request-response)

**Analog:** `simulator/run_scenario.py` — module docstring, stdlib-only header, `main()`, `__main__` guard. **No repo `__main__.py` exists; this module name is new** — Textual `ManetApp().run()` body comes from RESEARCH "Code Examples" § `python -m manet` entry point.

**Module docstring + entry-tail pattern** (`simulator/run_scenario.py` lines 1–6, 594–596, 626–627):
```python
"""CLI entry point and composition root for MANET simulations.

Handles deterministic scenario execution, SimPy environment lifecycle, ...
"""

def main(args: Optional[List[str]] = None) -> None:
    """CLI execution entrypoint."""
    ...

if __name__ == "__main__":
    main()
```
Transfer rule: same structure, minus argparse (D-16: no mandatory flags), replacing the body with `ManetApp().run()`. Per GEMINI.md error rule, catch only expected failure classes at CLI boundaries and let unexpected exceptions propagate — a `def main()` with no try/except is the convention (see `simulator/run_scenario.py:594-613`, which has zero exception handling in `main()`; validation happens in `load_scenario()` with `ValueError`/`FileNotFoundError`).

### `manet/__init__.py` (config, static)

**Analog:** `attacks/__init__.py` (whole file — re-export + `__all__` + boundary-contract docstring) for any `__init__.py` that re-exports; `simulator/__init__.py` (docstring + `__version__` only) for leaf subpackage `__init__.py` files (`manet/screens/__init__.py`, `manet/widgets/__init__.py`, etc.).
```python
# attacks/__init__.py — the re-export + explicit __all__ model
"""Attacks package for MANET adversarial simulation.

This package provides standalone attack strategies decoupled from the simulator.
No module in this package may import from `simulator/`.
"""

from __future__ import annotations

from attacks.base import AttackStrategy
from attacks.blackhole import BlackholeStrategy
from attacks.grayhole import GrayholeStrategy
from attacks.registry import create_attack_strategy

__all__ = [
    "AttackStrategy",
    "BlackholeStrategy",
    "GrayholeStrategy",
    "create_attack_strategy",
]
```
**Critical constraint (GEMINI.md "Module Design", also RESEARCH Pitfall 6):** "An `__init__.py` must not import a submodule that imports the package root — that is the classic barrel-file cycle." Because `manet/app.py` will import `manet.screens.*`, `manet/__init__.py` must either stay docstring+`__version__`-only (the `simulator/__init__.py` shape — recommended) or import only leaf submodules that never import `manet.app`. Do not re-export `ManetApp` from the package root.

### `manet/commands/registry.py` (model, transform)

**Analog:** `simulator/aodv.py` lines 15–62 — the repo's pure dataclass-record style (`@dataclass`, one-class-one-concern, docstring per class, default fields via `field(default_factory=...)`); `simulator/run_scenario.py` lines 35–42 (`NodeState`) shows the dataclass + composition-root pairing.
```python
# simulator/aodv.py lines 15-62
@dataclass
class RouteEntry:
    """Entry in an AODV node's routing table."""
    dest: int
    next_hop: int
    hop_count: int
    dest_seq: int
    lifetime: float
    is_valid: bool = True
    precursors: Set[int] = field(default_factory=set)

@dataclass
class DiscoveryState:
    """State of an ongoing route discovery for a destination."""
    dest: int
    retries: int = 0
    timeout: float = 2.0
    timer_token: int = 0
    last_attempt_time: float = 0.0
```
Note: line 43 in `aodv.py` shows `@dataclass` followed by class — copy spacing style exactly. The registry's `AppCommand` follows RESEARCH's contract (action is a *string reference* to an app action method — never subprocess). The `SessionSettings` dataclass in `manet/runtime/settings.py` copies the same dataclass style (`simulator/metrics.py` lines 17–26 `NetworkMetrics` is the cleanest single-block example).

### `manet/app.py` (provider, event-driven) — composition root

**Analog (convention only):** `simulator/run_scenario.py` lines 45–105 — `SimulationRunner.__init__` shows the repo's composition-root shape: wire dependencies by constructor, keep a single root that owns assembly, accept configuration explicitly. `manet/app.py` is the `manet/` package's composition root (registers themes, installs screens, mounts the registry) — apply that responsibility placement, not the SimPy mechanics.
```python
# simulator/run_scenario.py lines 45-57 — composition-root shape
class SimulationRunner:
    """Orchestrates deterministic simulation execution."""

    TRACE_HEADER = [...]          # module-level constants as class attrs
    HOP_DELAY = 0.002

    def __init__(self, scenario_config: Dict[str, Any], seed: int, out_path: Optional[Path] = None):
        self.scenario = scenario_config
        self.seed = seed
        ...
        self.rng = random.Random(seed)
```
Class-attribute constants (`TRACE_HEADER`) are the convention for the equivalent `manet.runtime.keymap.BINDINGS`-style declarations. Framework mechanics (SCREENS, BINDINGS, `register_theme` in `on_mount`, `COMMANDS = App.COMMANDS | {ManetCommands}`) come from RESEARCH Patterns 1–3.

### `tests/test_manet_import_boundaries.py` (test, sync AST batch)

**Analog:** `tests/test_import_boundaries.py` — **exact match, copy wholesale**. The file is 75 lines; copy `_get_imported_modules()` verbatim and clone the three test functions to the new boundaries:
```python
# tests/test_import_boundaries.py lines 1-20 and 23-44 — THE model
"""AST architectural boundary tests enforcing simulator never imports attacks."""

import ast
from pathlib import Path


def _get_imported_modules(file_path: Path) -> list[str]:
    """Extract all imported top-level module names from a Python source file using AST."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.append(node.module)
    return imported


def test_core_simulator_never_imports_attacks():
    """Enforce AGENTS.md rule: simulator core modules must NEVER import from attacks."""
    repo_root = Path(__file__).resolve().parent.parent
    simulator_dir = repo_root / "simulator"
    ...
    attack_imports = [imp for imp in imported if imp == "attacks" or imp.startswith("attacks.")]
    assert (
        len(attack_imports) == 0
    ), f"Architectural violation: {mod_name} imports attacks directly: {attack_imports}"
```
New boundaries to enforce with this pattern (TUI-02, TUI-04, Pitfall 5):
1. `manet/` modules never import `simulator` / `feature_extraction` / `ml` / `attacks` (equivalent of `test_core_simulator_never_imports_attacks`).
2. `manet/commands/**` never imports `subprocess` / `os.system` / `os.popen`-style execution primitives (equivalent assertion style: `imp == "subprocess" or imp.startswith("subprocess.")`, plus a token check for `os.system`/`os.popen` usage in `ast.Call` nodes or the import-name list).
3. Mirror `test_only_run_scenario_acts_as_composition_root` (lines 47–61) with a whitelist if any `manet/` module legitimately needs the reverse-direction exception — Phase 7 should need none.

### Other `tests/test_manet_*.py` (test, async Pilot)

**Analog (structure only):** `tests/test_aodv_recovery.py` lines 1–55 — docstring style, `from __future__ import annotations`, ordered stdlib → third-party → first-party imports, keyword-arg construction, docstring-per-test, assert-with-message. Note this repo file uses `List`/`Tuple` typing; per GEMINI.md either style passes but stay consistent per file.
```python
# tests/test_aodv_recovery.py lines 1-12, 14-28
"""Regression and integration tests for AODV route-discovery recovery lifecycle.

Verifies:
- Per-destination route discovery state and SimPy timeout scheduling
- Bounded retransmission attempts and exponential backoff
...
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, List, Optional, Set, Tuple

import pytest
import simpy

from ml.response import OnlineIDS
from simulator.aodv import AODVNode, DiscoveryState, RREP, RREQ, RouteEntry
from simulator.metrics import compute_metrics
from simulator.run_scenario import NodeState, SimulationRunner
from simulator.traffic import DataPacket


def test_duplicate_concurrent_discovery_prevention():
    """Verify initiate_route_discovery rejects concurrent discovery for same destination."""
    ...
    assert node.initiate_route_discovery(dest=5) is True
    assert 5 in node.pending_rreqs
```
Deltas for the new async tests (RESEARCH Pattern 5 is the only source — no async test exists in the repo): `pytest.mark.asyncio` (or `asyncio_mode = auto` via new `pytest.ini`), `async with app.run_test(size=(80, 24)) as pilot:`, `await pilot.press(...)`. Manual sync-only conventions (no real TTY spawns — Pitfall 8) stay.

### `pytest.ini` (root, NEW)

**No analog exists** (verified: zero pytest config files in repo; zero async tests). Sole source: RESEARCH "Validation Architecture"/Wave 0 — `asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function`. Wave-0 task ordering per Pitfall 9: run `python -m pytest tests/ -q` → 79 passed, add pytest.ini, re-run → still 79 passed, only then add the first TUI test. Quick run of the new subset: `python -m pytest tests/test_manet_*.py -q`. Always invoke via `python -m pytest`, never bare `pytest` (GEMINI.md invocation rule).

### `README.md` (MODIFIED — dependency record convention)

**Source: its own live sections.** Add the pinned pin to line 23's existing command (README line 23):
```bash
python -m pip install simpy==4.1.2 networkx==3.6.1 scikit-learn==1.8.0 pandas==3.0.2 numpy==1.26.4 matplotlib==3.10.8 seaborn==0.13.2 pytest==9.0.2 joblib==1.5.3
```
→ append `textual==8.2.8 pytest-asyncio==1.3.0`. The README is the repo's only recorded install surface (no requirements.txt / pyproject.toml exists — verified). Extend Quick Start with a `python -m manet` workflow section in the same numbered-workflow style as "### 1. Run Baseline Normal Simulation" (README lines 48–56), and record the final shortcut set (D-02 discretion) as a table matching README's existing heading style.

### `CHANGELOG.md` (MODIFIED)

**Source: its own format.** New entry above `## [1.1.0] - 2026-11-03`, matching:
```markdown
## [1.1.0] - 2026-11-03

### Added
- **AODV Route Discovery Recovery Lifecycle:** ... (CHANGELOG.md lines 8-19)
```
Keep-a-Changelog + SemVer headers, bold feature names followed by colon, bullet sub-details. The changelog is the authoritative project history (v1.0.0 2026-10-28, v1.1.0 2026-11-03); note the test-count	update convention (line 30: "Total automated test count updated from 69 to 79 across 11 test modules") — mirror that when the suite grows.

---

## No Analog Found

Files whose framework mechanics have **no codebase analog** — the planner must source construction directly from 07-RESEARCH.md Patterns 1–5 (fully quoted APIs; Context7-verified against v8.2.8):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `manet/app.py` (framework parts) | provider | event-driven | First Textual `App` in the repo; composition-root *responsibility* transfers from `simulator/run_scenario.py`, App mechanics from RESEARCH Patterns 1–3 |
| all `manet/screens/*.py`, `manet/widgets/*.py` | component | event-driven | First screens/widgets; RESEARCH Patterns 3–4 (BINDINGS, Footer, HORIZONTAL_BREAKPOINTS) |
| `manet/commands/palette_provider.py` | provider | request-response | RESEARCH Pattern 1 (Provider/discover/search/Hit/DiscoveryHit/matcher) |
| `manet/commands/console_driver.py`, `manet/screens/console.py` | utility/component | request-response | RESEARCH open-question 1 + command-registry contract |
| `manet/runtime/settings.py` (reactive part) | store | event-driven | RESEARCH "Session-only settings pattern" (reactive + watcher) — dataclass *field style* copies `NetworkMetrics` |
| `manet/runtime/theme.py` | config | static | RESEARCH Pattern 2 (Theme + variables, both `manet-soc` and high-contrast) |
| `manet/runtime/keymap.py` | config | static | RESEARCH Pattern 3 sketch — one central keymap, never inline duplicate Binding tuples |
| `manet/adapters/noop.py` | service stub | event-driven | Greenfield mounting contract (D-03); interfaces only |
| `manet/screens/placeholder.py` | component factory | static | D-20 "Planned — Phase N" honest states; no prior art |
| `pytest.ini` | config | static | No pytest config in repo; RESEARCH Wave 0 |

**Boundaries these greenfield files inherit from repo convention (apply everywhere):**
- Absolute first-party imports (`from simulator.aodv import ...` style → `from manet.commands.registry import AppCommand`), never relative hops across packages.
- `from __future__ import annotations` at top of every module (repo-wide, all analogs).
- Module docstring stating purpose + invariant it protects (e.g., `attacks/__init__.py`'s "No module in this package may import from `simulator/`.", `test_import_boundaries.py`'s "AST architectural boundary tests enforcing...").
- Stdlib-first; stdlib `dataclasses` for `AppCommand`/`SessionSettings`; no new deps beyond the recorded textual/pytest-asyncio pair.
- PEP 8, ≤100 cols, 4-space indent.
- Error handling: no bare except; no nested catch-all; unexpected exceptions propagate (Textual's loop replaces KeyboardInterrupt semantics, but ctrl+q/ctrl+c bindings must quit cleanly).

## Shared Patterns

### Module Header (all new files)
**Source:** every analog (`simulator/run_scenario.py:8`, `simulator/metrics.py:7`, `tests/test_aodv_recovery.py:14`, `tests/test_import_boundaries.py`)
```python
"""<one-paragraph purpose + the invariant it protects>."""

from __future__ import annotations

# stdlib imports, then third-party (textual), then first-party (manet.*), absolute paths
```

### Dataclass Records for Structured State
**Source:** `simulator/aodv.py:15-62`, `simulator/metrics.py:17-26`
**Apply to:** `manet/commands/registry.py` (`AppCommand`), `manet/runtime/settings.py` (`SessionSettings`)
```python
@dataclass
class AppCommand:            # every field documented: meaning + (where unit-bearing) unit + source
    """A single application command callable from the palette or console."""
    ...
```
Docstring rule from GEMINI.md: class docstrings state what each field means; registry fields are config-sourced, not observed.

### AST Boundary Enforcement
**Source:** `tests/test_import_boundaries.py:7-75`
**Apply to:** `tests/test_manet_import_boundaries.py` — clone `_get_imported_modules` verbatim; new assertions: (a) no `simulator|feature_extraction|ml|attacks` imports anywhere under `manet/` (D-12 one-way contract); (b) no `subprocess`-family imports under `manet/commands/` (D-10/Pitfall 5).

### Entry-Point Discipline
**Source:** `simulator/run_scenario.py:594-627` (`def main()` + `if __name__ == "__main__": main()`), README line 53/63/75 (`python -m <pkg>.<mod>`)
**Apply to:** `manet/__main__.py`. Never run as a file path; `python -m manet` from repo root, no mandatory flags (D-16). Existing CLI entry points untouched (D-19).

### Package Surface Contract
**Source:** `attacks/__init__.py` (re-exports + `__all__` + boundary docstring), `simulator/__init__.py` (docstring + `__version__` only)
**Apply to:** every `manet/**/__init__.py`. Subpackage `__init__.py` files should mimic `simulator/__init__.py`'s minimal shape (docstring only) unless they have a leaf re-export that provably never imports the package root (barrel-cycle rule, GEMINI.md Module Design / RESEARCH Pitfall 6).

### Dependency-Record Documentation
**Source:** `README.md:22-24` (pinned install line), `CHANGELOG.md:8-19` (Keep-a-Changelog entry), GEMINI.md "Documentation Sync Rule"
**Apply to:** the same commit that lands the first `manet/` code must add `textual==8.2.8 pytest-asyncio==1.3.0` to README line 23, a v2.0.0-dev or Unreleased CHANGELOG entry, and the GEMINI.md sync line.

### Test Conventions
**Source:** `tests/test_aodv_recovery.py` (structure), `tests/test_import_boundaries.py` (boundary tests), CHANGELOG.md:19/30 (test-count provenance in history)
**Apply to:** all `tests/test_manet_*.py` — root-`tests/` location only (never `manet/tests/`), `test_<area>.py` naming, docstring-per-module listing behaviors verified, docstring-per-test one-liner, assert with meaningful failure context. **Every async test must actually run** (Pitfall 1: pytest-asyncio strict mode silently skips; verify collected count grows; `asyncio_mode = auto` in the new `pytest.ini`). 79-test baseline must stay green and unweakened at every wave boundary.

### Windows/Path Safety
**Source:** GEMINI.md platform rules; repo root contains spaces
**Apply to:** all shell commands in plan actions (`python -m pytest tests/ -q` run from repo root — quote any path passed to the shell). Python code uses `pathlib.Path` only (pattern present in `run_scenario.py:14,20,587`; `test_import_boundaries.py:4,25`).

## Metadata

**Analog search scope:** repo root packages (`simulator/`, `ml/`, `attacks/`, `feature_extraction/`, `scripts/`), root `tests/`, `README.md`, `CHANGELOG.md`, `GEMINI.md`
**Files read:** 11 (GEMINI.md, 07-CONTEXT.md, 07-RESEARCH.md, simulator/run_scenario.py, simulator/__init__.py, ml/__init__.py, attacks/__init__.py, feature_extraction/__init__.py, simulator/aodv.py [first 70], simulator/metrics.py [first 60], tests/test_import_boundaries.py, tests/test_aodv_recovery.py [first 55], README.md [first 80], CHANGELOG.md [first 40])
**Grep scans:** `@dataclass` (12 hits across 6 files), `async def|asyncio` in tests (0 hits — confirms pytest-asyncio gap), glob `**/__main__.py` (0 hits)
**Pattern extraction date:** 2026-11-06
