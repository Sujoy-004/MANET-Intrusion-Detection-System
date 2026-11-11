# Phase 7: TUI Shell & Application Frame — Research

**Researched:** 2026-11-06
**Domain:** Textual 8.2.8 full-screen TUI application frame (`manet/` package, `python -m manet`, Windows-first)
**Confidence:** HIGH (Textual APIs verified against the v8.2.8-tagged Context7 docs and the installed package; environment probed live)

## Summary

Phase 7 builds the first v2.0 deliverable: a presentation-layer Textual application in a new top-level `manet/` package that launches via `python -m manet`, hosts placeholder surfaces for the Phase 8–11 screens, and wires the shell-level capabilities (screen stack, command palette, command console, SOC theme, keyboard navigation, compact layout, session-only settings). Textual 8.2.8 is already installed in the environment (`pip show textual` → 8.2.8, verified this session), so the dependency task is only the *documentation* record (README pinned install line + CHANGELOG entry), not installation.

Every shell primitive D-01..D-19 require is a first-class Textual feature: the searchable command palette with fuzzy matching (Provider/Hit system, overhauled in 0.37.0-era intro of `Provider` — current API verified against v8.2.8-tagged docs), `register_theme()` + `App.theme` for the 6.x+ theme system (legacy `App.dark`/`dark:` CSS is gone), `Footer` for visible shortcut hints, `BINDINGS`/priority bindings for keyboard-first navigation, and `HORIZONTAL_BREAKPOINTS` responsive screen classes for compact mode. Headless testing runs through `App.run_test()` + `Pilot` with pytest-asyncio (pytest-asyncio 1.3.0 is installed but **not yet configured** — this is the one genuine Wave 0 gap; see Validation Architecture).

The structural contract is the same one v1.0 already follows: `manet/` is a new top-level package with `__main__.py`, applied DAG-wise on top of existing packages (which never import `manet/`), adapters are thin/noop in this phase, and the 79-test root-`tests/` baseline must stay green. The repo has an AST-based `tests/test_import_boundaries.py` — the same pattern extends to enforcing that `manet/` presentation modules never duplicate simulator/ML logic.

**Primary recommendation:** Build `ManetApp(App)` with an installed-screen architecture (`App.SCREENS` + `switch_screen`), centralize app commands in a single registry consumed by both a `textual.command.Provider` (palette) and a custom console screen (application-commands-only), encode D-06 semantics directly into one registered `Theme` (color slots + custom variables) plus a second high-contrast theme variant, drive compact mode with `HORIZONTAL_BREAKPOINTS`, and test everything through `run_test()`/`Pilot` with `asyncio_mode = auto` in a new root `pytest.ini`.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Hybrid interface — full-screen dashboard, interactive forms, live monitoring, keyboard navigation, plus command-entry capability.
- **D-02:** Keyboard + mouse interaction with a global searchable command palette; arrows navigate, Enter selects, Esc goes back, dedicated shortcuts for common actions.
- **D-03:** Hybrid information architecture: workspace-based navigation, global command palette, contextual submenus, persistent notifications, active workload indicators, global system status. **Costly — layout shell determines where every later screen's notifications/status/workload indicators mount.**
- **D-04:** App identity is exactly `MANET IDS`; no separate product branding.
- **D-05:** Premium cybersecurity/SOC control-center aesthetic: dark, high contrast, structured panels, live telemetry placeholders, professional readable typography.
- **D-06:** Color semantics fixed: cyan navigation, blue information, green healthy, amber warnings, red critical, on dark background.
- **D-07:** Performance-bounded honest animation only; effects automatically reduce on limited terminals; reduced visual effects as a session accessibility option.
- **D-08:** Accessibility: readable labels, configurable colors, high-contrast mode, reduced visual effects, alternative status indicators (not color-only), screen-reader-friendly output where Textual supports it, configurable text density, visible keyboard focus indicators, contextual help.
- **D-09:** Session-only application settings; no persistent configuration profiles.
- **D-10:** Global command palette + dedicated structured command console; parameterized application commands, command history, contextual suggestions; NO unrestricted OS shell.
- **D-11:** Palette: fuzzy search, categorized commands, command history, recent actions, context-sensitive commands. Shortcut customization/aliases/user-defined parameterization DEFERRED.
- **D-12:** Pure presentation layer: existing modules remain authoritative; lightweight adapters; no duplicated business logic. **One-way contract.**
- **D-13:** Modular internal architecture, no plugin ecosystem; future screens are clearly-marked modular placeholders.
- **D-14:** Offline-first; no internet at runtime.
- **D-15:** Single-user local application; no login/auth.
- **D-16:** `python -m manet` from repo root, no mandatory flags.
- **D-17:** Cross-platform in code design; **only Windows is verified in this delivery** — untested platforms are reported as such (honesty rule).
- **D-18:** Responsive layouts, compact mode, resizable panels, session-level layout restoration (presets stay session-level per D-09).
- **D-19:** TUI is the default everyday experience; existing CLI/scripts unchanged.
- **D-20:** Engineering-driven choices by repository fit; never expose unimplemented capabilities as operational.
- **D-21:** Phase-by-phase implementation with verification before proceeding.

### OpenCode's Discretion
- Concrete screens/widgets composition (Header/Footer/Sidebar vs custom layout) — any faithful structure meeting D-01/D-03/D-18.
- Theming mechanism details within Textual (CSS variables/theme constants) as long as semantics follow D-06.
- Which concrete shortcuts are "dedicated for common actions" and their default bindings.
- Placeholder screen presentation details ("Planned — Phase N" wording, disabled styling).
- Internal module split inside `manet/` as long as it instantiates D-12/D-13.

### Deferred Ideas (OUT OF SCOPE)
- Dashboard diagnostics & capability states — Phase 8. Simulation workflow screens — Phase 9. Background execution/workload/telemetry — Phase 10. Experiment records/history — Phase 11. Test/docs gate — Phase 12.
- Deferred beyond v2.0: resource monitors, in-TUI test runner, reports/export center, alerts center, panel presets, storage lifecycle, ML/dataset/IDS-admin screens, topology & live network monitoring, update checking (a static version string in a help/about surface is Phase 7 discretion), shortcut customization/aliases, notification escalation.
- Out of scope globally: persistent settings files, databases/plugins/web servers, unrestricted OS shell, mock data presented as live output, edits to scenario fixtures, git commits/pushes during the implementation run, unbounded telemetry retention.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TUI-01 | `python -m manet` launches full-screen `MANET IDS` app, no flags, offline | `manet/__main__.py` calling `ManetApp().run()`; Textual `run()` is local/offline (no network teardown needed); app title via App/SUB_TITLE‑free `TITLE = "MANET IDS"` |
| TUI-02 | All TUI code in `manet/` with screens/widgets/commands/adapters/runtime separation; no duplicated logic | Recommended structure below; extend the `test_import_boundaries.py` AST pattern into `tests/test_manet_*.py` |
| TUI-03 | Keyboard-first navigation, visible focus, shortcut hints, resize adaptation incl. compact mode | Textual focus system + `Footer` binding display + `HORIZONTAL_BREAKPOINTS` screen classes + TCSS responsive widths; `run_test(size=…)` for resize tests |
| TUI-04 | Global searchable command palette + structured app-command console, no OS shell | Built-in palette framework (`Provider`/`Hit`/`matcher` fuzz) + custom console `Screen` fed by the same command registry; the registry itself never calls `subprocess`/`os.system`/`os.popen` |
| TUI-05 | Dark SOC palette (cyan/blue/green/amber/red semantics), reduced-motion + high-contrast where supported, session-only | One `Theme` registration with color slots + `variables`; second high-contrast theme registered; animation gating via `animate(level=…)` and `TEXTUAL_ANIMATIONS`; switching = assigning `self.theme` at runtime (no persistence — satisfies D-09) |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| App lifetime / screen stack (`python -m manet`) | Frontend (TUI process, `manet/app.py`) | — | Pure presentation; entry point owns nothing but the App object |
| Keyboard navigation / bindings | Frontend (`App`/`Screen` `BINDINGS`) | — | Textual handles binding dispatch; project only declares keymap |
| Command palette | Frontend (`textual.command.Provider`) | `manet/commands/` registry | Framework owns search UI + fuzzy scoring; project owns the command list |
| Command console (app-commands-only) | Frontend (custom `Screen`) | `manet/commands/registry.py` | No `execute`-like primitives; must exist entirely above the OS shell boundary |
| Theme / palette semantics (D-06) | Frontend (`textual.theme.Theme`) | — | Framework variable system; project only supplies colors |
| Compact mode / resize | Frontend (TCSS + `HORIZONTAL_BREAKPOINTS`) | — | Framework recalculates layout on resize; project declares breakpoints |
| Session settings (reduced motion, high contrast) | Frontend (`manet/runtime/settings.py`) | Theme system | In-memory app/reactive state only — never written to disk (D-09) |
| Status bar / notification mounting points | Frontend (`manet/widgets/`) | noop adapter objects | Phase 10/11 plug in later through the mounting contract D-03 established here |
| Adapters (session history, workbook/dashboard data) | Frontend (`manet/adapters/`) | Existing packages (Phase 9–11) | Phase 7 ships interfaces + noop impls; no simulator/ML logic duplicated |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| textual | **8.2.8** | The entire TUI: App/Screen/Widget model, command palette, theme system, focus & bindings, footer, notifications | Single pinned dependency (framework decision locked in `.planning/research/tui/SUMMARY.md`); pure Python, no toolchain; installed in the environment **[VERIFIED: pip show textual]** |
| pytest-asyncio | 1.3.0 | Makes `async def` tests (needed for `run_test()`) work under the repo's pytest 9.0.2 | Officially recommended pairing in Textual's testing guide **[VERIFIED: installed; CITED: textual.textualize.io/guide/testing]** |

### Supporting (already present, no new pins needed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.2 | Test runner for the 79-test baseline + new TUI tests | Every task commit |
| typing/importlib/stdlib | 3.11.8 | Module split, `__main__.py` mechanics, version strings for help/about | Throughout `manet/` |

### Do NOT add
- `rich` as a direct dependency (arrives transitively with Textual; only Textual's public API may be used — D-12 spirit and the framework decision forbid depending on it directly).
- Any settings/config persistence library (YAML/TOML writers) — D-09 forbids persistent profiles.
- `textual-dev` — devtools are a development convenience, not needed to build Phase 7 and would add another surfaced dependency.

**Dependency record obligation (GEMINI.md rule):** the dependency-decision already made (research/tui/SUMMARY.md) still must be *recorded*: add the pinned install line (`python -m pip install textual==8.2.8`) to README + a CHANGELOG entry in the same commit that lands the first `manet/` code. **[VERIFIED: no requirements.txt / pyproject.toml exists in the repo; README is the recorded install surface]**

**Version verification:** `python -m pip show textual` → 8.2.8 (matches locked decision; no install step needed). `python -m pip show pytest-asyncio` → 1.3.0.

## Architecture Patterns

### System Architecture Diagram

```text
python -m manet  (repo root, no flags, offline)
        │
        ▼
manet/__main__.py ──► ManetApp (textual.app.App)  ── TITLE = "MANET IDS"
        │
        ├─ on_mount: register_theme(soc_theme, soc_high_contrast) → self.theme = "manet-soc"
        │
        ├─ Screen stack (App.SCREENS installed, switch_screen for top-level nav)
        │        │
        │        ├─ main_workspace (Screen)          ← shell frame for Phases 8–11 content
        │        ├─ placeholder screens (DataFrame? no —} Static panels, "Planned — Phase N")
        │        ├─ help/about (Screen, optional)
        │        └─ command_console (Screen or ModalScreen)
        │
        ├─ Global command surface
        │        ├─ Command palette  ◄── ctrl+p, textual.command.Provider (built-in UI + fuzzy)
        │        ├─ Command console  ◄── dedicated key, custom Screen + Input + history
        │        └─ manet/commands/registry.py  ←─ SINGLE source of truth for app commands
        │                    (resolve(name, args) → app action; NO subprocess/os.system anywhere)
        │
        ├─ Session settings (manet/runtime/settings.py)
        │        ├─ reduced_motion  (reactive → gates animate(level=…)/animation usage)
        │        └─ high_contrast   (reactive → self.theme swap, session-only)
        │
        ├─ Mounting points for later phases (D-03)
        │        ├─ Status bar widget (global status, workload indicator slots) ← noop adapters
        │        └─ Notification rail (persistent notification list) ← App.notify()/Toast for transient
        │
        └─ Footer (visible shortcut hints) + focus ring styling (visible keyboard focus)
                │
                ▼
        Terminal (Windows Terminal first; resize events → breakpoint classes recalc)
```

Primary flow: `python -m manet` → `ManetApp.run()` → main workspace screen → user hits arrows/Enter/Esc or ctrl+p → palette/console receives commands from the registry → registry resolves to actions on app/screens. Nothing leaves the process; nothing reads or writes disk in Phase 7 beyond Python importing the package.

### Recommended Project Structure

```text
manet/
├── __init__.py            # package surface + __all__ (no logic — CONVENTIONS.md rule)
├── __main__.py            # python -m manet entry: def main(): ManetApp().run()
├── app.py                 # ManetApp(App): SCREENS, BINDINGS, theme registration, on_mount, title
├── screens/
│   ├── __init__.py
│   ├── main_workspace.py  # primary shell screen (nav + content area + status rail slots)
│   ├── console.py         # structured command console screen (Input + history list)
│   ├── help_about.py      # contextual help / version (static, discretion D-04/Q35)
│   └── placeholder.py     # reusable "Planned — Phase N" placeholder screen factory
├── widgets/
│   ├── __init__.py
│   ├── status_bar.py      # global system status + workload indicator slots (D-03)
│   ├── notification_rail.py  # persistent notification list (App.notify() toasts for transient)
│   └── nav_rail.py        # cyan navigation column (discretion; any faithful structure)
├── commands/
│   ├── __init__.py
│   ├── registry.py        # AppCommand dataclass + resolve(); app-commands-only contract
│   ├── palette_provider.py  # textual.command.Provider subclass over the registry
│   └── console_driver.py  # adapts registry to the console screen (history, suggestions)
├── adapters/
│   ├── __init__.py
│   └── noop.py            # session/worker/dashboard data stubs: interfaces only, noop impls
├── runtime/
│   ├── __init__.py
│   ├── settings.py        # SessionSettings dataclass: reduced_motion, high_contrast, density
│   ├── theme.py           # Theme definitions (manet-soc + manet-soc-high-contrast)
│   └── keymap.py          # BINDINGS constants + human-readable shortcut hint strings
```


### Pattern 1: The 8.x `Provider`-based command palette
**What:** Subclass `textual.command.Provider`, implement `discover()` (quick suggestion hits for an empty input) and/or `search(query)` (fuzzy-scored hits) using `self.matcher(query)`; register on the App with `COMMANDS = App.COMMANDS | {ManetProvider}`. Each `Hit(score, display, callback, help=…)` carries the callback that runs on selection.
**When to use:** For every globally reachable command (D-02/D-11). The built-in palette UI (ctrl+p, fuzzy search, categorized *via provider grouping*) is framework-owned — never hand-build the palette window.
**Example**
```python
from textual.command import DiscoveryHit, Hit, Hits, Provider

class ManetCommands(Provider):
    """Command palette provider over the MANET IDS app command registry."""

    async def discover(self) -> Hits:
        for command in self.app.commands_registry.iter_known():
            yield DiscoveryHit(command.display, command.make_callback(self.app), help=command.help)

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)          # built-in fuzzy matcher
        for command in self.app.commands_registry.iter_known():
            score = matcher.match(command.display)
            if score > 0:
                yield Hit(score, matcher.highlight(command.display),
                          command.make_callback(self.app), help=command.help)

class ManetApp(App):
    COMMANDS = App.COMMANDS | {ManetCommands}
```
Source: CITED: github.com/textualize/textual/blob/v8.2.8/docs/guide/command_palette.md (verified via Context7, v8.2.8 tag)

**Command history / recent actions:** the framework shows previously-run commands by scoring/matching again — history is your registry's job only if you want *ordering*; the simplest faithful D-11 implementation keeps a deque of executed command names in the registry and surfaces them first in `discover()`.

### Pattern 2: Theme registration with the 6.x+ theme system
**What:** Build `Theme(name=…, primary=…, …)` objects, call `register_theme(theme)` in `on_mount`, then set `self.theme = "manet-soc"`. Registered themes automatically appear in the theme switcher — meaning **session-only theme change is built-in** (no persistence: nothing writes anywhere, satisfies D-09 exactly).
**When to use:** For D-06 color semantics and the D-08 high-contrast variant.
**Example**
```python
from textual.theme import Theme

SOC = Theme(
    name="manet-soc",
    dark=True,
    background="#0a0f14",      # deep dark SOC background
    surface="#101820",
    panel="#152230",
    foreground="#dbe4ed",
    primary="#00b8d4",         # cyan → navigation emphasis (D-06)
    secondary="#3b82f6",       # blue  → informational surfaces (D-06)
    accent="#22c55e",          # healthy/green accent slot
    success="#22c55e",         # green healthy
    warning="#f59e0b",         # amber warnings
    error="#ef4444",           # red critical
    variables={
        "navigation-cyan": "#00b8d4",      # custom variables usable as $navigation-cyan in TCSS
        "info-blue": "#3b82f6",
        "healthy-green": "#22c55e",
        "warning-amber": "#f59e0b",
        "critical-red": "#ef4444",
        "footer-key-foreground": "#00b8d4",
    },
)
SOC_HIGH_CONTRAST = Theme(name="manet-soc-high-contrast", dark=True, …)  # brighter variants

class ManetApp(App):
    def on_mount(self) -> None:
        self.register_theme(SOC)
        self.register_theme(SOC_HIGH_CONTRAST)
        self.theme = "manet-soc"
```
Source: CITED: github.com/textualize/textual/blob/v8.2.8/docs/guide/design.md (verified via Context7).

### Pattern 3: Keyboard-first shell + visible hints
**What:** App-level `BINDINGS` apply on every screen; priority bindings survive focused-widget key capture. `Footer()` renders active bindings with human-readable keys — that *is* the visible shortcut hint requirement (TUI-03). Focus rings are styled with `:focus` pseudo-classes in TCSS.
**Example**
```python
from textual.binding import Binding

```python
# Structural sketch only — the final dedicated keymap is D-02 discretion.
# Encode one consistent keymap in manet/runtime/keymap.py; never duplicate Binding tuples inline.
BINDINGS = [
    Binding("ctrl+c", "quit", "Quit", show=False, priority=True),  # framework default; keep hidden in footer
    Binding("ctrl+o", "command_console", "Console", priority=True),  # dedicated console key (discretion)
    ("f1", "help_about", "Help"),                                   # contextual help
]
# App-level BINDINGS apply on every screen; mandatory keys already provided by the framework:
#   ctrl+q → quit (priority, App default), ctrl+p → command palette (COMMAND_PALETTE_BINDING).
```
```
Source: CITED: docs/guide/input.md + docs/guide/command_palette.md (verified via Context7). *(The snippet above is structural; the final keymap is the implementer's D-02 discretion — encode one consistent keymap in `manet/runtime/keymap.py` and import it everywhere, never duplicate `Binding` tuples inline.)*

### Pattern 4: Responsive compact mode with `HORIZONTAL_BREAKPOINTS`
**What:** `App.HORIZONTAL_BREAKPOINTS = [(0, "-normal"), (80, "-wide"), (120, "-very-wide")]` (or per-Screen). TCSS then targets the breakpoint classes: `Screen.-normal { NavRail { display: none; } }` etc. Combined with percentage/`fr` width units, layouts survive resize without imperative size math.
**When to use:** For the D-18 compact mode — small windows collapse the nav rail and switch the status bar to condensed labels via screen classes.
**Example**
```python
class MainWorkspace(Screen):
    HORIZONTAL_BREAKPOINTS = [(0, "-compact"), (89, "-full")]
```
```css
MainWorkspace.-compact #nav-rail { display: none; }
MainWorkspace.-compact #status-bar { layout: vertical; height: auto; }
```
Source: CITED: textual.textualize.io/api/app (HORIZONTAL_BREAKPOINTS, verified via Context7) + docs/guide/styles.md (percentage/vw units).

### Pattern 5: Headless testing with `run_test()` + `Pilot`
**What:** `async with app.run_test(size=(80, 24)) as pilot:` replaces `run()`; `pilot.press("down")`, `pilot.click("#id")`; the app is fully mounted, isolated from the real terminal.
**When to use:** For every TUI-01..TUI-05 automated test.
**Example**
```python
import pytest
from manet.app import ManetApp

@pytest.mark.asyncio
async def test_app_launches_and_focuses_nav():
    app = ManetApp()
    async with app.run_test() as pilot:
        assert app.TITLE == "MANET IDS"
        await pilot.press("down")
        ...
```
Source: CITED: textual.textualize.io/guide/testing (verified via Context7).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fuzzy command search | custom scoring/typo tolerance | `Provider.matcher(query)` (`textual.fuzzy.Matcher`) | Framework-tuned scoring (1 = exact, 0 = miss) + `highlight()` markup — CITED: v8.2.8 command_palette.md |
| Palette window/UX (key handling, ordering, provider grouping) | custom modal listing widget | Built-in command palette (`ctrl+p`) driven by `COMMANDS` | Hand-built version loses free accessibility behavior and every future provider hook |
| Color theming | per-widget hex constants scattered in code | `Theme` object + TCSS `$variables` | One object re-skins the app; high-contrast = second registration; switching is one assignment |
| Compact/responsive layouts | manual width math on `on_resize` | `HORIZONTAL_BREAKPOINTS` + TCSS classes + `%`/`fr`/`vw` units | Framework recalculates on resize and applies classes automatically |
| Shortcut hint display | self-drawn help strip | `Footer()` + `Binding(..., display_key/help)` | Footer already inspects *active* bindings per focus context |
| Transient notifications | custom counters/timers | `app.notify(message, title=…, severity=…)` / Toast | Severity classes (`-information`, `-warning`, `-error`) map 1:1 to blue/amber/red semantics |
| Animation gating | condor-like heuristics for "limited terminals" | `animate(..., level=…)` with `AnimationLevel` (`none`/`basic`/`full`) + `TEXTUAL_ANIMATIONS` env var | The framework already degrades animation on slow terminals; CITED: textual.textualize.io/api/types (AnimationLevel) |
| Key detection quirks | raw kbget/termios work | Textual input driver | Cross-platform input already abstracted; Windows driver included |

**Key insight:** almost every "hard" shell requirement in D-01..D-19 (fuzzy palette, theming, focus visibility, resize classes, notifications, animation degradation) is a framework feature, not application code. The app's own code is: the command *registry*, the screens' *composition*, the theme *constants*, and the adapter *interfaces*. Anything else is reimplementing Textual.

## Common Pitfalls

### Pitfall 1: pytest-asyncio strict mode silently skips async tests
**What goes wrong:** `run_test()`-based tests are `async def`. pytest without an asyncio plugin config prints "async def functions are not natively supported" and counts them as **skipped/passed-wrong**, not failed — TUI coverage can quietly vanish.
**Why it happens:** pytest-asyncio ≥ 0.22 defaults to *strict* mode → every async test needs `@pytest.mark.asyncio`, and there is currently **no pytest.ini/setup.cfg/pyproject in the repo** (verified: `Test-Path pytest.ini` → False).
**How to avoid:** Add a root `pytest.ini` with `asyncio_mode = auto` and `asyncio_default_fixture_loop_scope = function` in the Wave 0 task, or mark every test explicitly. Verify the new tests *run* (not skip) by counting collected items.
**Warning signs:** `pytest` output shows "async def functions are not natively supported" or the collected count doesn't include the new async tests.

### Pitfall 2: The theme must be registered before it is referenced
**What goes wrong:** Setting `self.theme = "manet-soc"` when no such theme is registered raises (invalid theme) or silently falls back — UI looks broken with no test failure if only the default is asserted.
**Why it happens:** `register_theme` runs in `on_mount` per the docs; code that sets the theme in `__init__` before registration fails.
**How to avoid:** Register both themes in `on_mount` *first*, then assign `self.theme`. Assert `app.theme == "manet-soc"` in a launch test.
**Warning signs:** ValueError "no theme … registered" or default-looking colors.

### Pitfall 3: App-level bindings vs ModalScreen suppression
**What goes wrong:** A modal console screen blocks App bindings — the global palette key (ctrl+p) stops working *while the console is open*, which may be desired for modal UX, but Esc-to-navigate-everywhere (D-02) then must be handled on the modal screen itself, or the user gets stuck.
**How to avoid:** Give every custom screen its own minimal BINDINGS (at minimum the console key and Esc↦pop/switch) even when most bindings live at App level. Use plain `Screen` (not `ModalScreen`) for the console if global shortcuts must keep firing while it's open — discretion, but a decision must be made and tested.
**Warning signs:** "Esc does nothing on screen X" in manual testing; palette unreachable from a specific screen.

### Pitfall 4: Duplicate/hidden quit bindings — ctrl+c vs ctrl+q
**What goes wrong:** The App base class already defines `ctrl+c` quit and `ctrl+q` quit as priority bindings; adding your own ctrl+c binding shows a duplicate in the footer or shadows the framework default (test suite also relies on ctrl+q being present).
**How to avoid:** Keep framework defaults; add only the bindings YOU introduce, with `show=False` on anything not user-facing. Check `App.BINDINGS` before declaring overlapping keys.
**Warning signs:** Footer shows two "Quit" entries; a key binding defined on a screen never fires because a priority App binding ate it.

### Pitfall 5: Command registry accidentally grows an execution primitive
**What goes wrong:** The natural temptation is `subprocess`/`os.system`/`os.popen` in the console for convenience (e.g., "run tests"). That directly violates D-10 and the spec's Out-of-Scope (no unrestricted OS shell) — plus the AST import-boundary test pattern from `tests/test_import_boundaries.py` should be able to prove it never happens.
**How to avoid:** The registry's `resolve()` returns references to app action methods only. Add an AST test in `tests/test_manet_command_registry.py` that fails if `manet/commands/**` ever imports `subprocess`/`shutil`/`os.popen`-style execution. **Never** widen the exception.
**Warning signs:** code review diff adding any `subprocess` import under `manet/`; manual console test echoing one-off shell-like strings.

### Pitfall 6: `manet/__init__.py` barrel-file cycle
**What goes wrong:** Following the repo's "export public surface with `__all__`" rule naively — e.g., `manet/__init__.py` importing `manet.app` while `manet/app.py` imports `manet.screens.*` which imports `manet.app` — creates a circular import at `python -m manet` time and breaks at startup.
**How to avoid:** Per CONVENTIONS.md, `__init__.py` re-exports but **must not import a submodule that imports the package root**. Keep `manet/__init__.py` exports minimal (app-level names only if safe) or module-marker-free; put the real API in submodules. The `__main__.py` does the imports.
**Warning signs:** `ImportError: cannot import name … from partially initialized module` during the very first launch test.

### Pitfall 7: Theme semantics mapped to base colors lose the five-color contract
**What goes wrong:** Mapping cyan/blue → `primary`/`secondary` works, but amber/red map to `warning`/`error` *only if no other widget misuse occurs* — e.g., a nav rail styled with `$error` by accident passes tests but breaks D-06 semantics.
**How to avoid:** Define the five semantic colors *both* as base color slots (for framework-native widgets where severity colors apply automatically) **and** as dedicated custom `variables` (`$navigation-cyan`, `$info-blue`, `$healthy-green`, `$warning-amber`, `$critical-red`); project TCSS references the custom variables, framework widgets ride severity slots. And satisfy D-08's "not color-only": every status surface also carries a textual label/badge icon.
**Warning signs:** any widget rule in project TCSS hard-codes a hex literal instead of a `$semantic` variable, or pulls a severity color for the wrong axis (e.g., a nav rail styled with `$critical-red`).

### Pitfall 8: Testing the launcher by spawning a real TTY
**What goes wrong:** A subprocess test of `python -m manet` hangs forever (a real TUI needs a TTY; under pytest there is none) or flakes on Windows console behavior.
**How to avoid:** Test the *App object* via `run_test()` (covers composition, theme, title, keymap). Keep at most one pure-*import* test of `manet.__main__` (`from manet.__main__ import main` + checking `main` callable) — running the executable path headlessly is exactly what `run_test()` was built for. `python -m manet`-executable-equivalence is verified manually in the phase verification step, not in the suite.
**Warning signs:** a test job stuck at 100% CPU with no output.

### Pitfall 9: Forgetting the 79-test baseline isn't free
**What goes wrong:** Adding any `pytest.ini` or new test module can interact with the existing suite: pytest-asyncio config changes plugin behavior suite-wide, a new `tests/test_manet_*.py` might import `manet` before `__init__.py` is safe, and the phase gate forbids *weakened* tests.
**How to avoid:** Wave 0 task: capture the baseline (`python -m pytest tests/ -q` → 79 passed, recorded), add `pytest.ini`, re-run to confirm still 79 passed+collected, and only then add the first `manet` test.
**Warning signs:** collected test count changes without cause; `asyncio_mode = auto` errors under pytest 9.

## Code Examples

### `python -m manet` entry point (TUI-01)
```python
# manet/__main__.py — Source: repo CLI convention (python -m) + textual docs (App.run)
"""MANET IDS entry point: launches the full-screen Textual application."""
from manet.app import ManetApp

def main() -> None:
    """Launch the MANET IDS terminal application."""
    ManetApp().run()

if __name__ == "__main__":
    main()
```
No flags needed beyond the object itself. The `run()` call owns the event loop; nothing else runs after it except a potential exception path (let unexpected exceptions propagate per CONVENTIONS.md error-handling rule).

### Command registry contract (single source of truth, TUI-04)
```python
# manet/commands/registry.py
from dataclasses import dataclass

@dataclass
class AppCommand:
    """A single application command callable from the palette or console.

    Fields: name (internal id), display (human title), help (one-liner),
    parameters (tuple of parameter names it accepts), action (app method name).

    NOTE: action is a *string reference* to an existing app action — the
    registry never constructs a process; there is no shell boundary here.
    """
    name: str; display: str; help: str; parameters: tuple[str, ...]; action: str

def iter_known() -> list[AppCommand]: ...
def resolve(name: str, args: list[str]) -> tuple[AppCommand, dict[str, str]] | None: ...
```
The console screen consumes `iter_known()` for suggestions and `resolve()` for execution; the palette provider consumes the same iterables. One registry = D-10's "single surface" and the cheapest Phase-8+ extension axis.

### Session-only settings pattern (TUI-05, D-09)
```python
class ManetApp(App):
    reduced_motion: reactive[bool] = reactive(False)

    def watch_reduced_motion(self, enabled: bool) -> None:
        """Gate all non-essential animation when the accessibility option is on."""
        if enabled:
            self.screen.call_after_refresh(self._stop_decorative_animations)
```
Two verified mechanisms combine here: (1) all animation call sites pass `level="basic"` to `animate(...)` — "basic" is the lowest level that still moves, and each animation can specify a minimum level ("full" by default) at which it is considered safe to play; (2) the `TEXTUAL_ANIMATIONS` environment variable globally clamps the framework's effective level to `none`/`basic`/`full` (`AnimationLevel` Literal, CITED: textual.textualize.io/api/types). The reduced-motion toggle is therefore: keep a session reactive on the App, have decorative call sites request `level="full"` (inert when the user disables anim), and have *progress/metric* animations request `level="basic"` (still allowed, per D-07's "honest animation"). **Do not invent a second animation-setting path.** Session-only is automatic: reactives live on the App object and die with it; nothing is written to disk.

### Resize/compact verification test (TUI-03)
```python
@pytest.mark.asyncio
async def test_compact_mode_collapses_nav_rail():
    app = ManetApp()
    async with app.run_test(size=(60, 20)) as pilot:   # below the compact breakpoint
        assert app.screen.has_class("-compact")
```
`run_test(size=…)` forces an exact terminal size — the framework recomputes breakpoint classes exactly as a real resize; re-open with `size=(120, 40)` to assert `-full` (verified parameter: `size: tuple[int,int] | None` in the run_test signature).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `App.dark: bool` + `dark:` CSS prefix, light/dark flip | `App.theme: str` + `Theme` objects + `$variable` TCSS | 0.86 (theme system) / 2024-2025 line | All theming goes through named registrations; legacy attribute gone in v8 — do not write `App.dark` |
| Command palette `Command` “legacy class” per-command subclasses | `Provider` with `discover`/`search`/`matcher` and `COMMANDS = App.COMMANDS | {Provider}` | 0.77-0.80 era + fortified at 8.x | The 8.2.8 API followed here is class-list-based providers; ignore pre-0.77 `binding="ctrl+backslash"` docs (default palette key moved to ctrl+p) |
| Sixteen-size engine tweaks/manual `on_resize` math | Screen-class breakpoints from `HORIZONTAL_BREAKPOINTS` | ~0.80 | Responsive layouts are declarative; avoid `on_resize` imperative sizing |
| `snap_compare` snapshot testing needing `pytest-textual-snapshot` plugin | Pilot-based `run_test()` testing requires only pytest-asyncio | current | Phase 7 requires no snapshot plugin; if visual regression emerges later a separate dependency decision applies |
| `tests/` per package (`OWN_PACKAGE/tests/`) | root-level `tests/` with root `tests/test_*.py` | v1.0 actual layout (supersedes maps) | New tests: `tests/test_manet_*.py` per CONTEXT.md; do NOT create `manet/tests/` |

**Deprecated/outdated:** `App.dark` attribute (no such attribute on v8.2.8 App — theming is `self.theme`), pre-0.77 ctrl+backslash palette key, `Selector...`-era command docs, per-package tests layout, direct `rich` API usage.

## Runtime State Inventory

Not a rename/refactor/migration phase — this is a greenfield application package. No runtime state carries old identifiers (verified: `manet/` doesn't exist in the repo root listing; only `simulator/`, `attacks/`, `feature_extraction/`, `ml/`, `scripts/`, `docs/`, `results/`, `traces/`, `data/`, `scenarios/`, `tests/`). Nothing to migrate; the only "state" is the dependency-record line in README/CHANGELOG (a documentation edit, listed in the obligations above).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Textual works out of the box on Windows Terminal; legacy `conhost` support degrades (the honesty rule (D-17) makes this an explicitly *reported* limitation, not an implementation problem) | Pitfalls / state-of-the-art | Documentation only — plan reports it, no code change needed |
| A2 | App title can be set with `TITLE`/`SUB_TITLE` class attributes and shows in `Header()` | Architecture diagram / TUI-01 | Cosmetic only; trivial to fix during implementation |
| A3 | Registered themes are automatically available to the built-in theme switcher (giving "session-only theme changing" for free) | Pattern 2 / TUI-05 | Minor — fallback is two tiny palette actions toggling `self.theme` |
| A4 | Custom variable names in `Theme.variables` (e.g. `"navigation-cyan"`) are addressable as `$navigation-cyan` in TCSS | Pattern 2 | Styling-only workaround (use explicit hex in project TCSS, still driven from `runtime/theme.py` constants) |
| A5 | `pilot.press("ctrl+o")`-style composite key strings work for our chosen console key in run_test | Validation Architecture | Test-only; choose a simple key or use pilot.click as fallback |
| A6 | pytest-asyncio 1.3.0 accepts `asyncio_default_fixture_loop_scope` config key (post-0.25 key) | Validation Architecture | Config-only; if unknown key, remove and rely on `asyncio_mode = auto` alone |

## Open Questions (RESOLVED)

1. **Which screen hosts the console — plain `Screen` pushed full-screen, or `ModalScreen` overlay?**
   - What's known: both patterns verified; ModalScreen blocks App bindings (Pitfall 3).
   - What's unclear: whether the console should be reachable *from anywhere including inside the console* (stacked) or always a modal.
   - Recommendation: plain `Screen` switched at top level, carrying its own Esc-back binding; simplest D-02 conformance. Decided during planning (discretion).
   - RESOLVED: plain `Screen` at top level — implemented as `ConsoleScreen(Screen)` in `manet/screens/console.py`, proven in-suite (Pilot open/Esc navigation tests).

2. **Should notification persistence (D-03) be a widget (persistent notification rail listing dismissible entries) or App.notify()+history widget?**
   - What's known: `notify()`/Toast is transient only; a persistent list is custom but trivial (a `Static`/`ListView` fed by a deque).
   - What's unclear: nothing — this is *the* discretionary split.
   - Recommendation: ship `App.notify()` for fresh toasts + a small persistent rail widget mirroring the deque (history survives dismiss); keep the widget thin so Phase 10/11 workers can `post_message` into it.
   - RESOLVED: `App.notify()` toasts shipped in Phase 7; the persistent notification rail (D-03, with the full shell-rails mounting contract) is deferred to Phase 8 per the 07-VERIFICATION.md Deferred Items table.

3. **Exact dedicated-key set (D-02 discretion).**
   - Recommendation: ctrl+p (palette, framework default), ctrl+o (console), F1 (help), arrows/Enter/Esc (navigation), ctrl+q (quit, priority, framework default). Record final choice in `manet/runtime/keymap.py` and README's shortcut table.
   - RESOLVED: final keymap locked in `manet/runtime/keymap.py` — `BINDING_PALETTE = "ctrl+p"`, `BINDING_CONSOLE = "ctrl+o"`, `BINDING_HELP = "f1"`, `BINDING_QUIT = "ctrl+q"`, arrows/Enter/Esc navigation (verified in-tree; framework defaults preserved).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | everything | ✓ | 3.11.8 | — |
| textual | TUI framework | ✓ | 8.2.8 | — (already installed; doc-record only) |
| pytest | test runner | ✓ | 9.0.2 | — |
| pytest-asyncio | async `run_test()` tests | ✓ | 1.3.0 | — (needs pytest.ini config — Pitfall 1) |
| AppTextual-usable TTY (Windows Terminal) | manual verification of the real launch | ✓ (dev host) | Windows 11 host | `run_test()` headless covers automated coverage; manual launch verification step in the plan |
| Internet | none | ✗ (not needed) | — | Phase is intentionally offline (D-14) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 (both installed) |
| Config file | **none today — Wave 0 gap**: add root `pytest.ini` (`asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function`) |
| Quick run command | `python -m pytest tests/ -q` |
| Full suite command | `python -m pytest tests/ -q` (full suite IS the gate; 79 baseline + new) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TUI-01 | App launches headless, title `MANET IDS`, default screen mounted, theme set | unit (async) | `python -m pytest tests/test_manet_app_launch.py -x` | ❌ Wave 0 |
| TUI-01 | `manet/__main__.main` exists/callable; package importable with no side effects | unit (sync) | `python -m pytest tests/test_manet_entry.py -x` | ❌ Wave 0 |
| TUI-02 | `manet/` modules never import `simulator`/`ml`/`feature_extraction` business logic; `manet/commands/` never imports `subprocess`/`os.system`/`shutil` | unit (AST, sync — extends `test_import_boundaries.py` pattern) | `python -m pytest tests/test_manet_import_boundaries.py -x` | ❌ Wave 0 |
| TUI-03 | Arrow navigation moves focus; Enter activates; Esc returns; Footer present; focus styles defined | unit (async, Pilot.press) | `python -m pytest tests/test_manet_navigation.py -x` | ❌ Wave 0 |
| TUI-03 | Compact breakpoint classes applied at small size (e.g., 60×20 `-compact`), full at large | unit (async, run_test(size=…)) | `python -m pytest tests/test_manet_compact.py -x` | ❌ Wave 0 |
| TUI-04 | Palette provider yields known commands via discover() and fuzzy matches via search(); every Hit callback maps to a registry command | unit (async) | `python -m pytest tests/test_manet_command_palette.py -x` | ❌ Wave 0 |
| TUI-04 | Console resolve() accepts/returns known app commands only; unknown input yields suggestion, never execution; history grows | unit (mix) | `python -m pytest tests/test_manet_command_registry.py -x` | ❌ Wave 0 |
| TUI-05 | `manet-soc` + `manet-soc-high-contrast` registered; `app.theme == "manet-soc"` at launch; high-contrast toggle switches theme; nothing persists (no file writes — import-blocked test on `os`/`Path` writes in settings module) | unit (async + AST) | `python -m pytest tests/test_manet_theme.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** quick run — `python -m pytest tests/test_manet_*.py -q` (fast, TUI-only subset) to catch regressions immediately, plus the full suite at plan boundaries.
- **Per wave/merge:** full `python -m pytest tests/ -q` — 79 baseline + new, all green.
- **Phase gate:** full suite green + one documented *manual* launch of `python -m manet` on the Windows host (TUI real-terminal behavior, including at least one resize) before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] Root `pytest.ini` — `asyncio_mode = auto`, `asyncio_default_fixture_loop_scope = function` (Pitfall 1; verify the 79 existing tests still collect/pass unchanged)
- [ ] `tests/test_manet_app_launch.py` — covers TUI-01
- [ ] `tests/test_manet_entry.py` — covers TUI-01
- [ ] `tests/test_manet_import_boundaries.py` — covers TUI-02 (non-exec of `manet/commands/**` is part of TUI-04)
- [ ] `tests/test_manet_navigation.py`, `tests/test_manet_compact.py` — covers TUI-03
- [ ] `tests/test_manet_command_palette.py`, `tests/test_manet_command_registry.py` — covers TUI-04
- [ ] `tests/test_manet_theme.py` — covers TUI-05
- [ ] No framework install needed — textual/pytest/pytest-asyncio all present

## Security Domain

### Applicable ASVS Categories (security_enforcement enabled, ASVS Level 1)

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Local single-user app; no login (D-15) |
| V3 Session Management | no | No sessions — app process is the session (D-15) |
| **V4 Access Control** | **yes (code hierarchy only)** | Filesystem permissions only; the TUI cannot escalate privileges — enforced structurally by "no backend logic duplicated" (D-12) and the adapter noop contract |
| **V5 Input/Output Validation** | **yes** | Command console parses app-commands through a strict registry (known names + validated parameters → actions); unknown tokens reject with a suggestion, never execute; AST test enforces "no `subprocess`/`os.system` in `manet/commands/`" (Pitfall 5) |
| V6 Cryptography | no | No secrets, no crypto in this phase (SHA-256 manifests are Phase 11; use stdlib `hashlib` then) |
| V7/V8/V12+ | no | No logging of secrets (none exist), no CDN/hosting, no uploads; ASVS Level 1 with no user/session/auth surfaces beyond the terminal process |

### Known Threat Patterns for Textual + local app
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Command console becomes an OS shell (D-10 violation) | Elevation of Privilege | Registry references app actions only; AST boundary test; no negotiation/danger commands |
| Stale/phantom commands shown as operational when backend is absent (D-20 violation) | Tampering with user trust | Placeholder screens carry explicit "Planned — Phase N" states; console has commands only for implemented features; capability states come from Phase 8, not simulated here |
| Palette callback escapes: parent classes yield actions unrelated to the registry | Tampering | Palette provider yields from `manet/commands/registry.py` only; no `partial(self.app.execute, ...)`-style generic executors |
| Permissive error swallowing hides real failures | Repudiation | CONVENTIONS.md error rule applies: no bare `except:`/`except-Exception:pass` in `manet/`; unexpected exceptions propagate (local dev app, so a visible traceback is correct) |

## Project Constraints (from GEMINI.md — binding for the planner)

- **Language/python floor:** Python 3.11+ only; pathlib everywhere (repo root contains spaces — always quote paths in shell).
- **Invocation:** always `python -m pip …` / `python -m pytest …` / `python -m manet …` (never bare `pip`).
- **Entry points:** run as modules, never file paths; `manet/__main__.py` is the pattern peer of `simulator/run_scenario.py`.
- **Import boundaries:** absolute first-party imports; package `__init__.py` with explicit `__all__` and **no barrel-file cycles (`__init__` must not import a submodule that imports the package root)`**; DAG — existing packages never import `manet/`.
- **No new runtime dependency without a recorded decision** — README pinned install line + CHANGELOG entry + GEMINI.md sync in the same commit (this still needs its documentation task even though research/tui/SUMMARY.md made the technical decision).
- **Determinism/tolerance:** prepare for `manet` never touching RNG; don't add state or randomness at the shell layer.
- **Stdlib-first:** dataclasses for structured records (e.g. `AppCommand`, `SessionSettings`); stdlib `json` (not yaml); `logging` (no loguru).
- **Error handling:** no bare except; catch expected failure classes at CLI boundaries only; unexpected exceptions propagate; `KeyboardInterrupt` semantics from the CLI convention don't apply inside Textual's loop, but ctrl+q/ctrl+c quit bindings must terminate cleanly.
- **Docs:** NO formatting tool; PEP 8, ≤100 cols; docstring rules (module purpose + invariant; dataclass field units/meaning).
- **Git:** no remote, `main` branch; **no commits/pushes during the implementation run** (documentation/plan commits are fine — the repo's GSD workflow commits planning docs).
- **Tests:** root `tests/`, `test_<module>.py` naming; 79-test baseline must stay green and unweakened.
- **CHANGELOG.md is authoritative project history** — not `.planning/` v1.0 archives.

## Sources

### Primary (HIGH confidence)
- Context7 `/textualize/textual/v8.2.8` (version-tagged!) — command_provider.md (Provider/discover/search/Hit/DiscoveryHit/matcher), design.md (Theme + register_theme + self.theme + $variables), input.md (BINDINGS, priority, show=False), screens.md (stack, push/switch/pop, ModalScreen), app.md (HORIZONTAL_BREAKPOINTS, run_test signature, screen API), widgets/toast.md (notify, severity classes), blog release0.37.0 (COMMANDS registration).
- Context7 `/websites/textual_textualize_io` — guide/testing (run_test, pytest-asyncio pairing, asyncio_mode=auto), types.md (AnimationLevel literal), command_palette.md (ENABLE_COMMAND_PALETTE, COMMAND_PALETTE_BINDING, get_system_commands overlay for extra system commands), api/app (switch_screen/push_screen signatures).
- Live environment probes (this session): `python -m pip show textual` → 8.2.8; `pytest-asyncio` → 1.3.0; `python --version` → 3.11.8; `Test-Path pytest.ini` → False; repo root listing (no `manet/`, `tests/` at root with 11 erkend files); `tests/test_import_boundaries.py` (AST pattern, read directly).

### Secondary (MEDIUM confidence)
- Official docs pages cited via Context7 with literal URLs (github.com/textualize/textual/blob/v8.2.8/docs/...) — matches verified v8.2.8 tag exactly.

### Tertiary (LOW confidence)
- None — all claims are Context7-verified or live-environment-verified; a small number of judgment calls (concrete color hex values, keymap choices) are explicitly discretion, not knowledge claims.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — framework pinned and already installed; pytest-asyncio presence verified.
- Architecture patterns: HIGH — every pattern cited from the v8.2.8-tagged Context7 docs; minor judgment calls (color hexes, keymap) are discretion, not invention.
- Pitfalls: HIGH — every pitfall is either framework-documented behavior (theme registration timing, ModalScreen binding suppression, AnimationLevel) or repo-specific verified facts (missing pytest.ini, AST boundary test exists, 79-test baseline).
- Validation architecture: MEDIUM-HIGH — framework verified; assumed items A5/A6 flagged in the log.

**Research date:** 2026-11-06
**Valid until:** ~2026-12-06 (Textual is stable at 8.2.8; framework pinned by locked decision — revisit only if a v9 lands mid-delivery)
