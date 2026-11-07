# Phase 07 — UI Review

**Audited:** 2026-11-07
**Baseline:** No UI-SPEC.md exists — audited against abstract 6-pillar standards plus the phase's binding decisions (07-CONTEXT.md: D-02/D-03/D-04/D-05/D-06/D-08/D-09/D-10/D-11/D-13/D-18/D-20; D-03/D-05/D-11/D-13 as recorded in plan intent) and the 07-01..04 PLAN must_haves.
**Screenshots:** Captured — 8 headless SVG states via `run_test()` + `export_screenshot()` (`.planning/ui-reviews/07-20261107-tui-captures/`; no dev server on 3000/5173/8080, so the browser port scan is N/A for this TUI app).
**Interaction captures:** off (workflow.ui_interaction_capture is false)

**Registry audit:** skipped — no `components.json` (NO_SHADCN); this is a Textual/Python TUI, not a shadcn project.

## Capture Evidence Ledger

| State | File | Verified content |
|-------|------|------------------|
| Workspace 120×40 | `01-workspace-normal-120x40.svg` | SOC theme renders: fg `#dbe4ed`, info-blue border `#3b82f6`, footer keys bold `#00b8d4`; single centered 2-line panel only |
| Workspace 60×20 | `02-workspace-compact-60x20.svg` | `-compact` engages; condensed padding/margin legible |
| Console first-use | `04-console-first-use-empty.svg` | Banner "Command Console — …", empty dark log area, input placeholder "Enter command..." |
| Console errors | `08-console-error-and-help-deadend.svg` | "Unknown command '...'. Type 'help' or check command palette." rendered in Rich-default `#f4005f`, NOT SOC `#ef4444`; echo line in Rich bright cyan `#58d1eb`, NOT `#00b8d4` |
| Help/About | `05-help-about-120x40.svg` | "MANET IDS — Version 2.0.0-dev", populated shortcut DataTable (ctrl+o/f1/ctrl+p/ctrl+q) |
| High-contrast workspace | `06-workspace-high-contrast-120x40.svg` | Theme toggle visibly works: `#ffffff`, `#00e5ff`, `#0d1520` render |
| Command palette ("theme") | `07-command-palette-query-theme.svg` | Palette themed correctly (SOC fg on hits); fuzzy query works; footer shows `^p palette` |

Threat-model discipline (no OS execution, no disk writes, honest command set) is strong throughout; this review scores the *visual and interaction* surfaces.

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 2/4 | Console tells users to "Type 'help' or check command palette" — `help` is not registered; both references are dead ends |
| 2. Visuals | 2/4 | Shell is a single 2-line panel; no structured panels / telemetry placeholders / deferred-screen placeholders (D-05/D-03/D-13); focus indicators dead on workspace |
| 3. Color | 2/4 | TCSS variable discipline verified clean, but console RichLog output colors bypass the SOC theme entirely (Rich-ANSI defaults, proven in render) |
| 4. Typography | 3/4 | Cell-grid hierarchy via bold+color consistent (3 uses); no stray styles |
| 5. Spacing | 3/4 | All cell-scale values (0/1/2), breakpoint-adaptive; one cross-screen margin inconsistency |
| 6. Experience Design | 2/4 | D-03 mounting contract never built (no status/notification surface, no noop adapters); motion-toggle has zero consumers and zero feedback |

**Overall: 14/24**

---

## Top 3 Priority Fixes

1. **BLOCKER — Console copy references a non-existent command (self-referential dead end).** Banner (`manet/screens/console.py:74`) says "Type application commands or 'help'" and the error path (`manet/screens/console.py:133`) says "Type 'help' or check command palette." — but `manet/commands/registry.py:35-57` registers only `workspace`/`theme-toggle`/`motion-toggle`. Typing `help` yields `Unknown command 'help'. Type 'help' or check command palette.` (captured in `08-…svg`) — the user follows the screen's own instruction and re-enters the error, and the palette has no help entry either. Violates D-20 ("never expose unimplemented capabilities as operational"). **Fix:** register `AppCommand(name="help", display="Open Help", help="Show the shortcut cheat sheet", parameters=(), action="action_show_help")` — `action_show_help` already exists on `ManetApp` (`manet/app.py:61`), so zero new logic; the hasattr anti-phantom test will stay green.

2. **BLOCKER — D-03 mounting contract is not built: shell has no persistent status/notification surface.** 07-01's reversibility gate "Confirmed option-a … noop adapter mounting contract" and 07-CONTEXT.md `<code_context>` "Phase 7 defines only their mounting points (status bar, notification area) and noop adapters" — yet `manet/` has **no** `widgets/`, **no** `adapters/`, zero `notify(` calls, no StatusBar/NotificationRail/NavRail (grep-proven). `MainWorkspace.compose` is Header + one `Static` + Footer. Consequences visible today: `motion-toggle` flips a bool consumed by nothing (`manet/app.py:72` — grep confirms no reader) while the palette advertises "Toggle Reduced Motion" (unobservable capability, D-08 status-indicator gap), theme toggles produce no status feedback, and Phase 8–11 screens must re-invent their mounts inside the "costly" shell D-03 explicitly pins. **Fix:** minimum honest increment for this phase: `manet/widgets/status_bar.py` (mock-free, placeholder "no active workload" wording) + a notification area widget mounted on `MainWorkspace` + one `manet/adapters/` noop interface per CONTEXT's mounting contract; route `action_toggle_reduced_motion`/`theme-toggle` completion through it (or `app.notify()` as interim), and give `reduced_motion` at least one real consumer (e.g. gate Textual's animation sensitivity).

3. **WARNING (top-3-worthy) — Console log colors bypass the theme system.** `manet/screens/console.py:99/109/111` use Rich markup `[bold cyan]`/`[green]`/`[red]`; the render proves output colors resolve to Rich's default ANSI skin — errors `#f4005f` vs SOC `critical-red #ef4444`, bright cyan `#58d1eb` vs `navigation-cyan #00b8d4` (`08-…svg` style block). D-06 color semantics are not honored on the app's primary output surface, and high-contrast toggling never re-tints console output. **Fix:** resolve from the active theme at write time: `vals = self.app.app.theme.variables; f"[#{vals['navigation-cyan']}]…"`, `f"[#{vals['critical-red']}]…"` — Rich accepts arbitrary hex in markup, so errors follow both themes.

---

## Detailed Findings

### Pillar 1: Copywriting (2/4)
- **BLOCKER:** `'help'` dead-end copy — see Top Fix 1. Two surfaces (`console.py:74`, `console.py:133`) instruct the user to use a capability that does not exist; the rendered capture `08-…svg` shows the error containing the same broken instruction.
- **WARNING:** Console echo interpolates raw user text into Rich markup unescaped — `log.write(f"> [bold cyan]{command_line}[/]")` (`console.py:99`); input like `foo [red]bar[/]` lets typed text alter log styling (display injection). Fix: `rich.markup.escape(command_line)` (or pass markup=False per write).
- No console empty/first-use orientation: `04-…svg` shows a completely empty dark log area; a boot line listing available commands would orient the user (empty-state copy absent).
- Good: rejection copy is structured and suggests alternates (`rm` → "Unknown command 'rm'.", `console_driver.py:122-133`); parameter mismatch copy names expected vs received (`console_driver.py:113-120`); help screen identity string matches D-04 exactly ("MANET IDS — Version 2.0.0-dev").
- Minor: `SHORTCUT_HINTS` says "Command palette" but the framework footer renders "palette" — wording mismatch across hint surfaces.
- Minor: console footer shows two identical "Close" entries (escape + ctrl+o both labeled "Close", `console.py:27-30`).

### Pillar 2: Visuals (2/4)
- **WARNING:** Workspace fails D-05/D-03/D-13's shell promise: one bordered 2-line `Static` ("MANET IDS\nSession shell workspace") with no structured panels, no live-telemetry placeholders, no placeholder surfaces marking deferred Phase 8–11 capabilities ("Planned — Phase N", D-20-permitted wording). Capture `01-…svg` confirms; the full viewport is a single box in an empty screen.
- **WARNING:** Focus indicators are dead where they matter: workspace `*:focus` (`main_workspace.py:52-54`) targets a screen whose only content (`Static`) is not focusable — Tab does nothing and no focus ring can ever render (D-08 "visible keyboard focus indicators" unmet on the default screen). `#workspace-box:focus` (`main_workspace.py:48-50`) is unreachable dead code.
- **WARNING:** Console input focus is invisible: `#console-input:focus` is stylistically identical to the unfocused rule (`console.py:57-67`, both `border: tall $navigation-cyan`) — the highest-traffic control gives no focus feedback.
- Good: SOC banner (bold cyan on `$panel`), bordered help panel with focused double-cyan DataTable (`help_about.py:71-73` + mounts focus on `on_mount`), footer key hints with `footer-key-foreground` cyan styling verified in the render (`r4 #00b8d4 bold`).
- Minor: workspace title and body are same weight/size — hierarchy rests on the border color only.

### Pillar 3: Color (2/4)
- Verified clean where the discipline applies: zero hex literals in screens; TCSS uses `$navigation-cyan`/`$info-blue`; SOC theme semantic slots render as declared (`01-…svg` style block: `#dbe4ed`/`#3b82f6`/`#00b8d4` bold); hi-contrast swap re-tints confirmed (`06-…svg`: `#ffffff`/`#00e5ff`/`#0d1520`).
- **WARNING:** Console RichLog bypasses all of it (see Top Fix 3) — output colors are Rich-ANSI defaults (`#f4005f`, `#98e024`, `#58d1eb`) in renders and code (`console.py:99/109/111`).
- **Minor:** Redundant variable shadowing: `manet/screens/main_workspace.py:21-22`, `console.py:33-34`, `help_about.py:27-28` re-declare `$info-blue: $secondary;` `$navigation-cyan: $primary;` although `theme.py:35-40` already defines those theme variables for both themes. Harmless while values coincide, but if a future theme decouples nav-cyan from primary, screens silently revert to primary (single-source drift by design). Delete the alias blocks.
- Note: framework's built-in palette entries (e.g. "Theme") render in framework-owned description colors — correctly outside this audit's scope.

### Pillar 4: Typography (3/4)
- All text is monospace cell-grid (TUI constraint); weight usage is restrained and consistent: `text-style: bold` exactly 3 times (console banner `console.py:46`, help title `help_about.py:47`, table header `help_about.py:60`), plus framework footer bold keys.
- No stray modifiers (no italic/reverse misuse).
- Deduct one point because textual hierarchy is carried almost entirely by color (see Pillar 2) — titles don't use available cell-scale devices (e.g., `#workspace-box` title vs body identical rendering).

### Pillar 5: Spacing (3/4)
- All spacing values are canonical cell-scale integers: workspace normal `padding: 1 2; margin: 1 2` / compact `padding: 0 1; margin: 0` (`main_workspace.py:38-46`); console banner `1 2`, log `0 1`, input `margin: 1 0 0 0` (`console.py:41-63`); help container `padding: 1 2`, title `margin-bottom: 1` (`help_about.py:35-49`). No arbitrary values anywhere (grep-verified `\[.*px\]`-style: n/a in TCSS).
- Breakpoint adaptation verified in render (`02-…svg` legible at 60×20 with margin collapse) and by 3 compact tests.
- **Minor:** Cross-screen margin inconsistency: workspace panel floats with `margin: 1 2`, help container sits flush (`margin` unset). Pick one philosophy (docked inset vs flush) across info surfaces.

### Pillar 6: Experience Design (2/4)
- **BLOCKER:** D-03 mounting contract unimplemented (see Top Fix 2) — 07-01 SUMMARY records "Confirmed option-a … noop adapter mounting contract" as a decision, but no widget holds that contract. This is the phase-load-bearing "costly" decision recorded as approved while absent.
- **WARNING:** `motion-toggle` is an unobservable capability (D-20 inversion): palette displays "Toggle Reduced Motion" and the driver reports "Executed: Toggle Reduced Motion", but `settings.reduced_motion` has zero consumers (grep-proven: only `settings.py` and the `app.py:72` flip). The status feedback surface that would make the toggle honest (D-08 alternative status indicators) is precisely what wasn't built.
- **WARNING:** D-11 palette features are partial: only fuzzy search + discovery landed; no command categories, no recent/history surfacing (console history never reaches the palette), no context-sensitive commands. `palette_provider.py:7-12` documents the plan-03 handoff for recency that never landed.
- Minor: `SessionSettings.compact_density` is declared with alias but consumed by nothing (D-18 is handled by breakpoints instead) — dormant placeholder field; document or wire it.
- Minor: `console.py:118` swallows via `except Exception` — the phase norm (T-7-04, zero exception swallowing) allows the documented shlex `except ValueError` fallback (`console_driver.py:71`) but this second one is a silent catch; replace with a membership check on the widget tree.
- Good — flows are genuinely solid where implemented: console→workspace→history cycles, Esc routes, palette open/close, Up/Down history all test-verified (37 TUI tests) and confirmed in captures; rejection/empty paths return structured results; no fake data anywhere (D-20 upheld technically); nothing disables/destroys so confirmation flows are correctly absent.

---

## Files Audited
- `manet/app.py`, `manet/__main__.py`, `manet/__init__.py` (docstring-only shape)
- `manet/runtime/theme.py`, `manet/runtime/keymap.py`, `manet/runtime/settings.py`
- `manet/commands/registry.py`, `manet/commands/console_driver.py`, `manet/commands/palette_provider.py`
- `manet/screens/main_workspace.py`, `manet/screens/console.py`, `manet/screens/help_about.py`
- `manet/commands/__init__.py` (boundary docstring)
- Captures: `.planning/ui-reviews/07-20261107-tui-captures/01…08*.svg` (8 states, gitignored)
- Cross-checked against 07-01..04 SUMMARY/PLAN and 07-CONTEXT.md decisions
