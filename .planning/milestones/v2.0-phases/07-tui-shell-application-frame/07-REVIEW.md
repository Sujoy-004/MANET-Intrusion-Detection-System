---
phase: 07-tui-shell-application-frame
reviewed: 2026-11-07T03:28:55Z
depth: standard
files_reviewed: 25
files_reviewed_list:
  - pytest.ini
  - manet/__init__.py
  - manet/__main__.py
  - manet/app.py
  - manet/runtime/__init__.py
  - manet/runtime/theme.py
  - manet/runtime/keymap.py
  - manet/runtime/settings.py
  - manet/screens/__init__.py
  - manet/screens/main_workspace.py
  - manet/screens/console.py
  - manet/screens/help_about.py
  - manet/commands/__init__.py
  - manet/commands/registry.py
  - manet/commands/palette_provider.py
  - manet/commands/console_driver.py
  - tests/test_manet_app_launch.py
  - tests/test_manet_entry.py
  - tests/test_manet_import_boundaries.py
  - tests/test_manet_command_registry.py
  - tests/test_manet_command_palette.py
  - tests/test_manet_console.py
  - tests/test_manet_navigation.py
  - tests/test_manet_theme.py
  - tests/test_manet_compact.py
findings:
  critical: 3
  warning: 5
  info: 9
  total: 17
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-11-07T03:28:55Z
**Depth:** standard
**Files Reviewed:** 25
**Status:** issues_found

## Summary

Phase 7 delivered a clean, well-structured `manet/` Textual TUI package: the import boundaries are genuinely enforced (AST tests), there is zero OS-execution primitive in the command path, zero filesystem writes anywhere in `manet/`, no secrets, no `eval`, and the phase commit range (`3b2c527..3e20392`) touched only `manet/`, `tests/`, `pytest.ini`, and planning artifacts — no forbidden-dir writes. All 37 `tests/test_manet*` tests pass (re-verified; full-suite 116 claim consistent).

However, adversarial probing found **one new crash-class BLOCKER the phase's own UI review missed**: user-typed text is interpolated into Rich markup on a `markup=True` RichLog, and any input containing an unmatched Rich closing tag (e.g. literally typing `[/red]`) raises `MarkupError` that escapes the message handler and kills the whole application — reproduced headlessly against the committed code. Two further BLOCKERs from the domain constraints are confirmed by direct inspection: the registered `help` command the console copy tells users to type does not exist (D-20), and the D-03 "option-a" mounting decision recorded as user-approved in 07-01-SUMMARY was never built (no `manet/widgets/`, no `manet/adapters/`, zero `notify(` usage).

Security posture is otherwise sound: console `name` tokens never reach `getattr` (only registry `action` strings do), shaded-parameter dispatch is unreachable with the current parameterless registry, and history/navigation are in-memory only (D-09 verified via the phase's own AST tests, plus manual grep).

## Critical Issues

### CR-01: User-triggerable application crash — raw user text interpolated into Rich markup on `markup=True` RichLog

**File:** `manet/screens/console.py:99` (echo path); also `manet/screens/console.py:111` + `manet/commands/console_driver.py:133` (error path)

**Issue:** `ConsoleScreen.compose` creates `RichLog(id="console-log", highlight=True, markup=True)` and `on_input_submitted` writes `log.write(f"> [bold cyan]{command_line}[/]")` with `command_line` being raw user input. Rich parses the user text as markup: any input containing an **unmatched closing tag** (e.g. `[/red]`, `[/]`) raises `rich.errors.MarkupError`, which escapes the `Input.Submitted` handler and terminates the app. Proven by headless pilot probe against the committed code: submitting `[/red]` produced the traceback `MarkupError: closing tag '[/red]' at position 13 doesn't match any open tag` originating at `console.py:99` → `RichLog.write:215` → `_make_renderable:162` → `Text.from_markup` — the app died (in a real terminal the user gets Textual's crash screen and a dead session).

The error path has the same vector: `console_driver.py:133` interpolates the user's first token into `f"Unknown command '{name}'..."`, and `console.py:111` writes that output with markup as `[red]{result.output}[/]` — so input `[/x] ls` crashes through `result.output` instead of the echo. (Valid markup such as `[red]bar` also restyles the log's later text — the display-injection the UI audit flagged, authorable by the user in both paths.)

**Fix:**
```python
# manet/screens/console.py — write user-derived text as Text objects (never parsed for markup),
# and resolve colors from theme variables (also addresses D-06, see WK-05).
from rich.text import Text

def on_input_submitted(self, event: Input.Submitted) -> None:
    ...
    log.write(Text("> ", style="bold #00b8d4") + Text(command_line))  # unstyled user text
    ...
    if result.success:
        if result.output:
            log.write(Text(result.output, style=self._theme_var("healthy-green")))
    else:
        log.write(Text(result.output, style=self._theme_var("critical-red")))
```
Additionally escape the user-derived `name` at the source where driver copy is built (`rich.markup.escape(name)` in `console_driver.py:133`) so driver output is markup-safe if ever written with `markup=True` elsewhere. Add a regression test submitting an input containing `[/red]` and asserting the app survives.

### CR-02: D-03 "option-a" reversibility decision recorded as user-approved but the mounting contract was never built

**File:** `manet/app.py:46-51`, `manet/screens/main_workspace.py:57-64` (absence: no `manet/widgets/`, no `manet/adapters/`)

**Issue:** `07-01-SUMMARY.md:62` records the reversibility gate resolution as *"Confirmed `option-a` (installed screens on `ManetApp`, plain `Screen` console, noop adapter contract) per user approval"*, and `07-01-PLAN.md:132` specifies: *"session shell mounts StatusBar + NotificationRail + NavRail as `manet/widgets/` components on MainWorkspace, with noop adapter interfaces in `manet/adapters/` that Phase 10/11 plug through (D-03 mounting contract)"*; its success criteria (`07-01-PLAN.md:228`) state *"screens/runtime present; commands/widgets/adapters arrive in plans 02-04"*. Plans 02–04 are complete and committed (see `3b2c527..3e20392`), yet grep/glob-verified: no `manet/widgets/`, no `manet/adapters/`, zero `notify(` calls, zero StatusBar/NotificationRail/NavRail anywhere in `manet/`. `MainWorkspace.compose` is Header + one `Static` + Footer. The code contradicts what the plan and summary record as approved; every Phase 8–11 screen will now have to re-invent mounts inside the shell whose mounting points D-03 explicitly pins as the costly one-way decision. Compound consequences visible in this phase's own code: `motion-toggle` flips a bool consumed by nothing (WK-01) and theme toggles produce no feedback.

**Fix:** Build the minimum honest increment of the recorded contract in this phase: `manet/widgets/status_bar.py` (mock-free placeholder wording, e.g. "no active workload"), a notification area widget mounted on `MainWorkspace`, and one noop adapter interface per `manet/adapters/` per the CONTEXT record; route theme-toggle / reduced-motion completion feedback through `app.notify()` or the new widget as an interim so the D-03 surface and D-08 feedback both exist. If the contract is deliberately deferred instead, the recorded decision documents (07-01-SUMMARY) must be corrected — plan artifacts must not claim a built contract that does not exist.

### CR-03: D-20 honesty violation — console help copy advertises a nonexistent `help` command (self-referential dead end)

**File:** `manet/screens/console.py:74`, `manet/commands/console_driver.py:133`

**Issue:** The console banner says "Type application commands or 'help'" (`console.py:74`) and the unknown-command error says "Type 'help' or check command palette." (`console_driver.py:133`), but `manet/commands/registry.py:35-57` registers only `workspace`, `theme-toggle`, `motion-toggle` — there is no `help` command in the console dispatch chain (the help screen exists only behind the f1 key binding). Following the screen's own instruction yields `Unknown command 'help'. Type 'help' or check command palette.` — an infinite error loop. `tests/test_manet_console.py:53` enshrines the broken copy with `assert "Type 'help' or check command palette." in res.output`. Direct D-20 violation ("UI copy must never advertise a capability that does not exist"); also carried to every user via the error surface.

**Fix:** Register the command — the action method already exists:
```python
# manet/commands/registry.py
AppCommand(
    name="help",
    display="Open Help",
    help="Show the shortcut cheat sheet",
    parameters=(),
    action="action_show_help",   # ManetApp.action_show_help (manet/app.py:61)
),
```
The anti-phantom test (`tests/test_manet_command_registry.py:57`) stays green. Then update `test_manet_console.py` to execute `help` successfully instead of asserting the dead-end string.

## Warnings

### WR-01: `motion-toggle` is an advertised capability with zero consumers (unobservable toggle)

**File:** `manet/app.py:70-72`, `manet/commands/registry.py:50-56`

**Issue:** The palette displays "Toggle Reduced Motion" and the console reports `Executed: Toggle Reduced Motion`, but `settings.reduced_motion` is never read anywhere (`grep`-verified across `manet/`: only `settings.py` declaration and the `app.py:72` flip). No motion is ever reduced — D-20/D-08 violation at the code level: the honest feedback surface (status/notification, i.e. the unbuilt D-03 contract) is exactly what would make this command truthful.

**Fix:** Either give `reduced_motion` a real consumer in this phase (e.g. gate Textual's animation sensitivity: `self.app.animate = not self.settings.reduced_motion` style wiring) or remove the command from the registry until one exists. Do not keep an executing-but-unobservable command.

### WR-02: `except Exception: return` silently swallows — violates the zero-exception-swallowing rule

**File:** `manet/screens/console.py:113-119`

**Issue:** The Up/Down history handler wraps `self.query_one("#console-input", Input)` in `try/except Exception: return`. Triage of its justification: none stands. When a key event reaches this handler and `has_focus` would be true, the input is mounted; the only realistic failure is a lookup typo or a genuinely absent widget — cases where silently returning makes dead arrow keys and hides the defect from every test (no test asserts the failure path). This is the exact anti-pattern the project error rule forbids ("Fail fast and loudly. Never catch-and-ignore"); the phase accepted only the documented `except ValueError` shlex fallback in `console_driver.py:71`.

**Fix:**
```python
def on_key(self, event: events.Key) -> None:
    if event.key not in ("up", "down"):
        return
    if not self.is_mounted:
        return  # screen is being removed — nothing to navigate
    input_widget = self.query_one("#console-input", Input)
    ...
```
`query_one` then raises loudly on any real regression instead of being eaten.

### WR-03: Workspace focus CSS is dead and the default screen has no focusable content (D-08 gap)

**File:** `manet/screens/main_workspace.py:48-54`, `manet/screens/main_workspace.py:57-64`

**Issue:** `#workspace-box:focus { border: double $navigation-cyan; }` is unreachable — `Static` is not focusable by default, so that rule can never render (dead code). The `*:focus` rule targets a screen whose only composed widget is a non-focusable `Static`, so Tab does nothing and no focus indicator can ever appear on the application's default screen — the "visible keyboard focus indicators" requirement (D-08) is unmet exactly where users first land.

**Fix:** Either restore the focus ring design by making the workspace panel a genuinely interactive/focusable surface (e.g. `focusable=True` Static with `can_focus` tracked, or compose real Phase-8 placeholder panels that are focusable — which CR-02's shell fix would provide), or delete both unreachable rules so the stylesheet doesn't lie about behavior it cannot have.

### WR-04: Palette provider docstring records a recency handoff that its own completed plan never delivered

**File:** `manet/commands/palette_provider.py:7-12`

**Issue:** The docstring states recency "is delegated to the console driver's history deque in plan 03, which will surface recent commands at the TOP of discover() when it lands," while plan 03 is already committed within this very phase — and `discover()` yields insertion order only; console history never reaches the palette. The documentation inside the shipping code promises behavior that the completed phase did not build and nothing tracks the gap. Also a partial D-11 delivery (no categories/recent/history in palette).

**Fix:** Implement the documented handoff in `discover()` (merge `console_driver.history` for recency-priority ordering, e.g. resolve recent command displays from history and yield them first), or rewrite the docstring to state the deliberate omission and a tracking reference.

### WR-05: Console output colors bypass the SOC theme entirely (D-06 violation on the primary output surface)

**File:** `manet/screens/console.py:99` (`[bold cyan]`), `manet/screens/console.py:109` (`[green]`), `manet/screens/console.py:111` (`[red]`)

**Issue:** Rich name-literal markup resolves against Rich's default ANSI skin, not the application theme: UI-review render capture (`08-console-error-and-help-deadend.svg`) proves errors render `#f4005f` instead of SOC `critical-red #ef4444`, and echoes render bright cyan `#58d1eb` instead of `navigation-cyan #00b8d4`. High-contrast toggling never re-tints console output. Every other surface in the phase honors `$variable`-only discipline; the console is the main output surface and does not.

**Fix:** Resolve at write time from the active theme's variables, e.g. bind `vals = self.app.theme_variables` (Textual exposes the active theme's dict) and emit `[#{vals['critical-red']}]...` / `[#{vals['navigation-cyan']}]...`; combine with the CR-01 fix (write `Text` objects carrying these styles so user text can never be parsed as markup).

## Info

### IN-01: Version string duplicated as a hardcoded literal in the help screen

**File:** `manet/screens/help_about.py:80` vs `manet/__init__.py:10`

**Issue:** `"MANET IDS — Version 2.0.0-dev"` duplicates the package `__version__ = "2.0.0-dev"`. A future version bump silently leaves the Help screen stale.
**Fix:** `from manet import __version__` and compose `f"MANET IDS — Version {__version__}"`.

### IN-02: Redundant CSS variable shadowing re-declared in three screens

**File:** `manet/screens/main_workspace.py:21-22`, `manet/screens/console.py:33-34`, `manet/screens/help_about.py:27-28`

**Issue:** `$info-blue: $secondary; $navigation-cyan: $primary;` re-declares what `manet/runtime/theme.py:34-41` already provides as theme variables for both themes. Harmless while values coincide; if a future theme decouples nav-cyan from primary, screens silently revert to primary (docs-drift-by-design).
**Fix:** Delete the alias blocks and reference the theme variables directly.

### IN-03: Dead session settings — `compact_density` and its `compact_mode` alias have zero consumers

**File:** `manet/runtime/settings.py:29-38`

**Issue:** `compact_density` plus the `compact_mode` property alias are declared but never read or written anywhere (D-18 was implemented via breakpoints instead). Dormant placeholder fields inflate the settings' advertised surface.
**Fix:** Remove the field and alias, or add a docstring note naming why it is retained (e.g. planned consumer) — a settings field that claims to be governable but does nothing is D-20-adjacent.

### IN-04: Registry API shape — redundant type union; latent kwargs contract unverified

**File:** `manet/commands/registry.py:69`, `manet/commands/console_driver.py:92-95`

**Issue:** `args: Sequence[str] | list[str]` — `list[str]` is redundant (already a `Sequence`). And `action_fn(**params)` dispatches registry-declared parameter names as kwargs of string values; with the current parameterless registry the branch is dead, but the first future parameterful command must ensure its `action_*` method accepts those exact string kwargs — nothing tests that contract, and a mismatch becomes a runtime `TypeError` inside the console submit handler.
**Fix:** Drop `| list[str]`. When a parameterful command is added, extend the anti-phantom test to assert `inspect.signature(getattr(ManetApp, cmd.action))` accepts each declared parameter name.

### IN-05: `manet/runtime/__init__.py` does not re-export the package's public surface

**File:** `manet/runtime/__init__.py:1-3`

**Issue:** Project convention requires each package's `__init__.py` to re-export its public API with an explicit `__all__`; `runtime/` ships only a docstring while `screens/` and `commands/` comply. Divergent barrier style invites drift.
**Fix:** Re-export `SOC, SOC_HIGH_CONTRAST` (theme), keymap constants, and `SessionSettings` with `__all__` — mirroring `manet/commands/__init__.py`'s shape.

### IN-06: Substring-based import guard is brittle and weaker than the AST gate it duplicates

**File:** `tests/test_manet_console.py:129-135`

**Issue:** `assert "os." not in source` / `assert "import os" not in source` string checks: `from os import system` contains neither marker and would evade this test; a comment mentioning "os." would false-fail. The AST boundary test (`tests/test_manet_import_boundaries.py:54-77`) already covers this correctly and strictly.
**Fix:** Delete the substring test (or reduce it to delegating to the AST analysis helper) to keep one enforcement mechanism, not two of unequal strength.

### IN-07: Inconsistent asyncio test markers (auto mode makes them redundant, style should be uniform)

**File:** `tests/test_manet_app_launch.py:26` (no marker) vs `tests/test_manet_navigation.py:22` et al. (`@pytest.mark.asyncio`)

**Issue:** `pytest.ini:2` sets `asyncio_mode = auto`, so explicit `@pytest.mark.asyncio` markers are redundant; some async tests carry them and others don't — harmless but inconsistent, and the markers invite confusion if auto mode is ever disabled.
**Fix:** Pick one policy (prefer: drop the redundant markers everywhere, relying on the documented auto mode).

### IN-08: Input cleared before execution; on handler exceptions the typed command is already gone

**File:** `manet/screens/console.py:90-93`

**Issue:** `on_input_submitted` nulls `event.input.value` before `driver.execute(...)` runs; if any handler exception occurs (e.g. the CR-01 markup crash), the user's line is lost and no echo was even written. Also `event.input.value = ""` instead of the API `event.input.clear()`.
**Fix:** Execute first, clear after success (echo happens immediately anyway), and use `event.input.clear()`.

### IN-09: Shortcut copy drift — console footer shows two identical "Close" entries; help-table labels vs footer labels differ

**File:** `manet/screens/console.py:27-30`, `manet/runtime/keymap.py:15-20`, `manet/app.py:35-36`

**Issue:** The console binds both `escape` and `ctrl+o` with the same visible label "Close", producing a redundant footer row; meanwhile `SHORTCUT_HINTS` (shown on the help screen) says "Open command console"/"Help and about" while the workspace footer shows "Console"/"Help" — three surfaces, two vocabularies for the same keys.
**Fix:** Differentiate the console bindings' labels (e.g. escape → "Close", ctrl+o → "Back") and align `SHORTCUT_HINTS` wording with the framework footer labels.

---

_Positive verification notes (no findings):_ command input tokens never reach `getattr` (only registry `action` strings); OS-shell commands rejected and tested (`tests/test_manet_console.py:44-57`); history and settings are strictly in-memory (D-09/D-10 verified via AST tests and manual grep); zero disk I/O, zero `eval`/`subprocess`/`os` imports in `manet/`; no secrets; phase commit range wrote nothing to `traces/`, `data/`, `models/`, or `results/`; navigation, palette lifecycle, breakpoints, and theme toggle are all covered by passing tests (37/37 re-verified) with render evidence from the UI audit.

_Reviewed: 2026-11-07T03:28:55Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
