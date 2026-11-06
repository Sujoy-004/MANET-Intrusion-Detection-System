---
phase: 07-tui-shell-application-frame
plan: "02"
subsystem: tui
tags: [textual, tui, commands, command-palette, registry, ast-boundaries, security]
requires: ["07-01"]
provides:
  - single-source application command registry at manet/commands/registry.py (AppCommand, iter_known, resolve)
  - Textual Provider command palette provider at manet/commands/palette_provider.py (ManetCommands)
  - honest workspace navigation action on ManetApp (action_show_workspace)
  - palette integration on ManetApp via COMMANDS = App.COMMANDS | {ManetCommands}
  - AST boundary test suite in tests/test_manet_import_boundaries.py (presentation isolation + OS execution prevention)
  - registry unit test suite in tests/test_manet_command_registry.py
  - palette provider integration test suite in tests/test_manet_command_palette.py
affects:
  - manet/app.py
  - tests/
tech-stack:
  added: []
  patterns:
    - Single-source application command registry with string-reference actions (never subprocess/callables)
    - Textual 8.2.8 Provider pattern (discover, search, matcher, Hit, DiscoveryHit)
    - AST static boundary enforcement preventing forbidden imports
    - Anti-phantom-command honesty verification loop (hasattr(ManetApp, command.action))
key-files:
  created:
    - manet/commands/__init__.py
    - manet/commands/registry.py
    - manet/commands/palette_provider.py
    - tests/test_manet_import_boundaries.py
    - tests/test_manet_command_registry.py
    - tests/test_manet_command_palette.py
  modified:
    - manet/app.py
decisions:
  - "Enforced string-reference actions in AppCommand (action: str) resolved exclusively via getattr(app, action)() to forbid arbitrary process execution or callable injection (T-7-01, T-7-03)"
  - "Constructed AST boundary test suite cloning _get_imported_modules verbatim to mechanically verify manet/ never imports simulator/attacks/feature_extraction/ml and manet/commands/ never imports subprocess/shutil/os"
  - "Enforced anti-phantom honesty check requiring every registered AppCommand action to map directly to an existing method on ManetApp (D-20, T-7-02)"
  - "Delegated palette search empty-query behavior to discover() yielding identical discovery hits in deterministic insertion order"
status: complete
actuals:
  tokens: 2850
  tasks: 3
  commits: 3
---

# Phase 07 Plan 02: Command Registry & Palette Summary

**One-liner:** Single-source application command registry, AST import-boundary enforcement against business and OS execution primitives, and fuzzy Textual command palette provider with honest workspace action wiring.

## Overview

Plan 07-02 delivered the command architecture foundation for the MANET IDS TUI. It established a single source of truth for application commands, protected the codebase with mechanical AST boundary tests, and wired a fuzzy-search command palette provider to `ManetApp`.

Key deliverables achieved:
1. **Application Command Registry (`manet/commands/`)**:
   - `manet/commands/__init__.py`: Package-level guardrail docstring explicitly defining the security boundary (application commands only; zero imports of `subprocess`, `shutil`, or `os`).
   - `manet/commands/registry.py`: Defines the immutable `@dataclass(frozen=True) AppCommand` with exact fields `name`, `display`, `help`, `parameters`, and `action`. `iter_known()` returns registered commands in deterministic insertion order. `resolve(name, args)` enforces exact name matching and exact parameter arity checking without prefix expansion or shell escape paths.
   - Initial honest command: `workspace` (`action_show_workspace` switching to `"workspace"` screen).
2. **AST Architectural Boundary Tests (`tests/test_manet_import_boundaries.py`)**:
   - Cloned `_get_imported_modules` verbatim from `tests/test_import_boundaries.py`.
   - `test_manet_never_imports_business_packages`: Verifies that no module under `manet/` imports `simulator`, `attacks`, `feature_extraction`, or `ml` (D-12, TUI-02).
   - `test_command_package_never_uses_os_execution`: Mechanically proves that no module under `manet/commands/` imports `subprocess`, `shutil`, or `os` (D-10, T-7-01, Pitfall 5).
3. **Command Palette Integration (`manet/commands/palette_provider.py` & `manet/app.py`)**:
   - `ManetCommands(Provider)`: Implements Textual 8.2.8 `discover()` and `search()`.
   - `discover()` yields `DiscoveryHit` items sourced strictly from `iter_known()`.
   - `search(query)` uses `self.matcher(query)` for fuzzy scoring and filtering (`score > 0`), delegating empty queries to `discover()`.
   - Action dispatching uses a single private factory `_make_callback()` that resolves `getattr(self.app, command.action)()`, preventing arbitrary command execution.
   - `ManetApp` registers `COMMANDS = App.COMMANDS | {ManetCommands}` and implements `action_show_workspace()`.
4. **Test Verification**:
   - `tests/test_manet_command_registry.py`: 5 tests verifying resolution, rejection, arity validation, determinism, and the `hasattr(ManetApp, command.action)` anti-phantom check.
   - `tests/test_manet_import_boundaries.py`: 2 tests verifying AST package boundaries.
   - `tests/test_manet_command_palette.py`: 6 tests verifying registration, discovery ordering, empty search equivalence, fuzzy match scoring, registry-fidelity without hit escape, and `ctrl+p` / `escape` palette modal lifecycle.
   - Entire test suite: 96 passed (79 baseline + 4 from plan 01 + 13 from plan 02).

## Threat Mitigations (STRIDE Register)

| Threat ID | Category | Component | Disposition | Mitigation Summary |
|-----------|----------|-----------|-------------|--------------------|
| T-7-01 | Elevation of Privilege | `manet/commands/registry.py`, `palette_provider.py` | mitigate | `resolve()` returns `(AppCommand, params)` tuples only; action is a string reference. AST boundary test mechanically guarantees no module in `manet/commands/` imports `subprocess`, `shutil`, or `os`. |
| T-7-02 | Tampering (user trust) | Command registry initial set | mitigate | Registry only includes commands backed by existing app actions (`action_show_workspace`). Anti-phantom test loop validates `hasattr(ManetApp, command.action)` for every registered command. |
| T-7-03 | Tampering | `manet/commands/palette_provider.py` | mitigate | `discover()` and `search()` source exclusively from `iter_known()`. Hit set strictly equals registry display set. Dispatch occurs via private `_make_callback` using `getattr(self.app, action)()`. |
| T-7-04 | Repudiation | Registry and provider error paths | mitigate | Rejection paths return `None` or empty hit sets without swallowing unexpected exceptions; no bare `except` blocks anywhere. |

## Commits

- `2fb85fd`: `feat(phase-7): implement application command registry with honest workspace action`
- `47f7f29`: `test(phase-7): enforce AST import boundaries for presentation layer and command package`
- `226d13b`: `feat(phase-7): wire command palette provider to application registry`

## Verification Results

- `python -m pytest tests/test_manet_command_registry.py -x` -> 5 passed in 1.13s
- `python -m pytest tests/test_manet_import_boundaries.py -x` -> 2 passed in 0.04s
- `python -m pytest tests/test_manet_command_palette.py -x` -> 6 passed in 0.88s
- `python -m pytest tests/test_manet_*.py -q` (all Phase 7 tests) -> 17 passed in 0.83s
- `python -m pytest tests/ -q` (full project test suite) -> 96 passed, 1 warning in 132.52s

## Deviations from Plan

None - plan executed exactly as specified.

## Self-Check: PASSED

- FOUND: manet/commands/__init__.py
- FOUND: manet/commands/registry.py
- FOUND: manet/commands/palette_provider.py
- FOUND: manet/app.py
- FOUND: tests/test_manet_import_boundaries.py
- FOUND: tests/test_manet_command_registry.py
- FOUND: tests/test_manet_command_palette.py
- FOUND commit: 2fb85fd
- FOUND commit: 47f7f29
- FOUND commit: 226d13b
