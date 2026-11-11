# Phase 11 — UI Review

**Audited:** 2026-11-09
**Baseline:** abstract 6-pillar standards (no UI-SPEC.md exists for this phase) + app-level semantic color contract (`manet/runtime/theme.py`, D-06) and Phase 11 CONTEXT decisions D-01–D-05
**Screenshots:** not captured (no dev server on :3000/:5173/:8080 — Textual TUI ships no HTTP surface by design; code-only audit)
**Format note:** Textual TUI audit — Tailwind-class greps adapted to TCSS blocks and Rich markup tokens.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Honest, specific copy throughout; one zero-run dead end in History and a `)+)` rendering typo on a rare badge |
| 2. Visuals | 3/4 | Strong split-pane hierarchy; sort state invisible and no layout defense at the documented 80×24 minimum |
| 3. Color | 2/4 | ~20 hardcoded hexes bypass the documented D-06 theme-variable contract and blind the screens to all three registered themes |
| 4. Typography | 4/4 | Disciplined two-treatment system ([dim] label / [bold] value) consistent across all four new files |
| 5. Spacing | 4/4 | Consistent cell-unit vocabulary (0 1 / 1 2 margins-paddings) matching the app's established idiom |
| 6. Experience Design | 3/4 | Exemplary loading/error/confirmation states; zero-run History is a blank dead-end and sorting is mouse-only |

**Overall: 19/24**

---

## Top 3 Priority Fixes

1. **Theme bypass in all four Phase 11 files (Color 2/4)** — Results/History/prune/scorecard render in a hardcoded GitHub-dark palette (`#0a0e14`, `#161b22`, `#30363d`, `#3fb950`, `#d29922`, `#f85149`, `#58a6ff`, `#39c5cf`, `#8b949e`, `#e6edf3`, `#1f6feb`) while `theme.py:13-14` documents the D-06 contract that "TCSS references theme variables ($variable) rather than hardcoded hex values", and `ManetApp` registers three switchable themes (`app.py:168-170`, commands `theme-toggle` / `theme-warm` in `registry.py:64-84`). User impact: after `theme-warm` (light theme), MainWorkspace goes near-white while Results/History stay pitch-black with hardcoded light-on-dark text — a visibly broken, mixed theme; the D-08 accessibility high-contrast theme (TUI-05) also has zero effect on these screens. Fix: swap hexes for variables — `#0a0e14`→`$background`, `#0d1117`/`#161b22`→`$surface`, `#30363d`/`#21262d` borders→`$panel`, `#8b949e`→`$foreground-muted`-style dim text, `#3fb950`→`$success`, `#d29922`→`$warning`, `#f85149`→`$error`, `#58a6ff`/`#39c5cf`/`#1f6feb`→`$primary`/`$secondary` (mirroring the existing variable usage in `main_workspace.py:50-193`, which uses zero hexes). Rich-markup badges in `qos_scorecard.py` can keep bold/color pairs via the theme slots (`$success`, `$warning`, `$error`).
2. **HistoryScreen zero-run dead end + invisible sort state (Experience 3/4, Visuals 3/4)** — `_refresh_table` (`history.py:260-290`) leaves an empty DataTable with no message, no CTA, and no exit ramp when the workspace has no runs; contrast with MainWorkspace's `CtaHeroPanel` empty state and ResultsScreen's honest redirect (`results.py:204`). Independently, `_set_sort` (`history.py:240-247`) never marks the active column, so after any header click the sort order is silent. Fix: in `_refresh_table`, toggle an empty-state `Static` ("No experiment records yet — launch a simulation to populate history.") when `table.row_count == 0`; in `_set_sort`, append `▲`/`▼` to the sorted column label (e.g. `table.columns["pdr"].label = "PDR ▲"`).
3. **No responsive defense at the app's documented 80×24 minimum (Visuals 3/4)** — MainWorkspace implements `HORIZONTAL_BREAKPOINTS` and compact reflow (`main_workspace.py:41,98-184`), but `ResultsScreen`, `QosScorecard`, and the history filter bar have none. At 80 columns, four `1fr` cards ≈19 cells each clip the label `PACKET DELIVERY RATIO` (20 chars, `qos_scorecard.py:140`), and the filter bar (search `min-width: 24` + four buttons `min-width: 10` + margins ≈ 74 cells) overflows (`history.py:68-76,111-119`). Fix: add `HORIZONTAL_BREAKPOINTS` to `ResultsScreen`/`HistoryScreen`; in compact mode stack scorecard cards 2×2 (wrap the Horizontal in a `Grid(columns=2)`), and let the four filter buttons drop to a second row or icon-labels at ≤80 cols.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)
Evidence for the strong side:
- No generic CTA strings: destructive action is explicit — `"DELETE EXPERIMENT RECORD"` title + `Button("Delete Permanently", variant="error")` (`prune_modal.py:104,117`), paired with `Button("Cancel", ...)` — a semantic cancel, not a lazy label.
- Search placeholder is concrete and enumerates matchable fields: `"Search scenario, tag, run ID, or seed..."` (`history.py:113`).
- Empty/error copy is honest and specific: `"[dim]No artifact records found.[/]"` and `"[dim]No artifacts.[/]"` (`results.py:185,318`), `"[bold yellow]No completed experiment records found in workspace.[/]"` (`results.py:204,267`; `app.py:251` — matches the 11-02-PLAN Test-10 contract string verbatim), `f"Deletion failed: {exc}"` / `f"Cannot preview deletion: {exc}"` with correct severities (`history.py:373,357`).
- All 9 `notify()` calls carry specific text × severity (information/warning/error) — no bare "Oops"/"Something went wrong" anywhere in the phase files.
- Shortcut hint bar is actionable: `"[Enter] View Results | [D] Delete | [R] Refresh | [Esc] Back"` (`history.py:122`).

Gaps (why not 4/4):
- **Zero-run HistoryScreen has no empty-state copy at all** — a blank DataTable with only the global hint bar; the user has no words telling them why the list is empty or what to do next.
- `results.py:353` renders a stray double close-paren: `f"...SECURITY VIOLATION[/] ({escape(...)})"` → literal output `(msg))` on the rare SECURITY_VIOLATION badge.
- `qos_scorecard.py:155` uses the informal abbreviation `{recv} recvd` amid otherwise professional prose ("sent" is not abbreviated) — `received` would match the register of the academic scorecard it styles.

### Pillar 2: Visuals (3/4)
Strong:
- Clear focal point on ResultsScreen: fixed top `results-top-pane` hosting `QosScorecard` (`results.py:213-220`), with the tabbed inspector below — exactly the D-01 hybrid split-pane contract.
- Metric-card hierarchy is textbook: `[dim]` uppercase label above `[bold]` value with semantic badge color (`qos_scorecard.py:140-150`), ratio shown dimmed under the percentage (`:83`).
- Integrity badges form a legible severity ladder with paired symbols: `VERIFIED ✓` bold green → `CORRUPTED / TAMPERED ✗` bold red → `MISSING ✗` yellow → `RECORDED` cyan (`results.py:336-354`), including the first-16-char sha256 prefix the CONTEXT sheet asked for (`results.py:340`).
- Prune modal is a proper danger dialog: centered 72-col `thick #f85149` border, itemized bullets with per-file KB, bold-green reclaim total (`prune_modal.py:42-46,104-117`).
- No icon-only buttons anywhere — every control is text-labeled or binding-hinted; zebra stripes on both DataTables improve row scanning.

Gaps:
- **Sort state invisible:** columns are sortable by header click (`history.py:253-258`) but the active column/order is never reflected in the header labels or styling — users cannot see which column the table is ordered by or that clicking did anything.
- **80×24 minimum unprotected** (see Priority Fix 3): four 1fr cards clip their labels at the documented minimum; filter bar overflows.
- **Configuration tab is a wall of text:** a single `Static` of 13–14 `[bold]Label:[/] value` lines including lifecycle timestamps, status, and error (`results.py:154-172`) — no grouping between launch parameters, lifecycle, and run status; a DataTable or two-section layout would give the eye anchors instead of one dense block.
- Minor: when a manifest has no `metrics` dict at all, the scorecard is omitted entirely (`results.py:214-215`) so the screen loses its header anchor for exactly the runs (no-metrics failures) that most need a structured frame; a scorecard with all-N/A cards would keep the layout stable.

### Pillar 3: Color (2/4)
Hardcoded hex counts per file (unique per file, pooled overlap): `results.py` 6, `history.py` 8, `prune_modal.py` 5, `qos_scorecard.py` 9 — roughly **20 distinct hex values across the four new files**.

What works:
- Within-phase 60/30/10 distribution is disciplined: dark backgrounds dominate (~60%), muted `#8b949e`/`#e6edf3` text and borders ~30%, and accent color is reserved for ~6 semantic badge types + one `active` filter state (`#1f6feb`, `history.py:78`) — accents are meaningful, not decorative, and destructive red appears only in the prune path and the stop button.
- PDR thresholds follow the plan's documented heuristics exactly (`>=0.8` green, `>=0.5` amber, else red — `qos_scorecard.py:74-83`) and honest `N/A` avoids fabricating badge color for unknown values.

Why 2/4 — systemic violations:
- **Documented contract breach:** `theme.py:13-14` states the app's D-06 design intent: "Semantic colors are defined both in standard framework slots and custom variables to ensure TCSS references theme variables ($variable) rather than hardcoded hex values." The sibling dashboard (`main_workspace.py:50-193`) honors it with `$background`/`$surface`/`$panel`/`$primary` and **zero** hex literals; Phase 11 instead imports an entire GitHub-dark palette with values that don't match the theme slots it sits beside (SOC success `#34d399` vs badge `#3fb950`; SOC warning `#fbbf24` vs `#d29922`; SOC error `#f87171` vs `#f85149`; SOC background `#0a0f18` vs `#0a0e14`).
- **All three registered themes are bypassed:** `ManetApp.register_theme(SOC / SOC_HIGH_CONTRAST / AI_STUDIO_WARM)` + `theme = "manet-soc"` (`app.py:168-172`), with user-facing toggle commands `theme-toggle` and `theme-warm` (`registry.py:64-84`, `app.py:276-287`). The Phase 11 screens set their own `background:`/`color:` on the Screen root (`results.py:34-48`, `history.py:54-58`, `prune_modal.py:43-46`), so on the light `AI_STUDIO_WARM` theme the dashboard flips near-white while these screens remain dark with dark-theme text — a mixed-rendering defect a real user triggers from the command palette. High-contrast mode (accessibility path D-08/TUI-05) also has no effect on the new screens.
- Note for fix planning: the plans (11-02-PLAN Task 1 concept boxes) themselves specified the GitHub hexes, so plan-fidelity was met — but the plans contradicted the app-level contract, and the audit is scored against the contract, not the typo carried forward.
- Minor: rich-markup `[dim]`/`[bold green]` tokens in composition strings cannot be themed by TCSS variables anywhere; the fix must convert badge colors to widget-level classes or theme-slot references for the correction to hold.

### Pillar 4: Typography (4/4)
- TUI monospace regime, so the audit maps to style treatments: `[bold]` ×37 and `[dim]` ×19 across the four phase files, plus two TCSS `text-style: bold` rules (`qos_scorecard.py:50-52`, `history.py:80`) — two emphasis levels total, well inside the ≤2-weight budget.
- The label/value language is systematic, not accidental: card labels always `[dim]` uppercase (`qos_scorecard.py:140-149`), values always `[bold]` + semantic color; subcounters label-value pairs follow the same pattern (`:154-157`).
- Header/title hierarchy is consistent: one all-caps danger title for the modal (`prune_modal.py:104`), sentence-case tab and card labels elsewhere; no fake-heading inflation in the static config block (labels `[bold]`, values plain — `results.py:155-167`).
- Only nit (non-scoring): `VERIFYING CHECKSUMS...` is `[bold cyan]` (`results.py:197`) while the settled `RECORDED` state is plain `[cyan]` (`:349`) — a weight asymmetry on the same badge element, defensible as a in-progress/emphasis distinction.

### Pillar 5: Spacing (4/4)
- A single spacing vocabulary in cell units across all four files plus app modals: screen gutters `padding: 0 1` (`results.py:42,47`, `qos_scorecard.py:36`, `history.py:65`), section separation `margin-bottom: 1` / `margin-top: 1` (`qos_scorecard.py:37,55`, `prune_modal.py:51-67`), modal interior `padding: 1 2` (`prune_modal.py:44`, same as the pre-existing app modals `app.py:52,101`), button gutters `margin: 0 1` / `margin-left: 1` with `min-width` in cells (`prune_modal.py:75-78`, `history.py:73-76`, `live_run.py:133-136`).
- Fractional/auto heights (`1fr` content + `height: auto` chrome + fixed dock strips `height: 1`) keep vertical rhythm identical to the dashboard's pattern; no arbitrary pixel/rem-style values and no mixed-unit confusion (TUI cell sizing is idiomatic here, unlike Tailwind arbitrary brackets).
- Structural nit (non-scoring): scorecard card gutters are effectively 2 cells interior vs 1 cell at the outer edge (`padding: 0 1` on the container + `margin: 0 1 0 0` per card — `qos_scorecard.py:36,48`); halving one side would make breathing room symmetric.

### Pillar 6: Experience Design (3/4)
Strong — the state matrix is far above typical TUI discipline:
- **Loading state**: every artifact badge initializes to `[bold cyan]VERIFYING CHECKSUMS...[/]` (`results.py:197`) and is replaced by a thread worker using `@work(thread=True)` + `call_from_thread` with `is_mounted` and cancel guards (`results.py:283-304,356-358`) — no static integrity badges, no UI freeze on hashing.
- **Error states**: verification failure → dedicated badge path (`results.py:366-373`); disk-read exception → `VERIFICATION ERROR` badge without crash (`results.py:299-304`); deletion failures surface as titled error notifications while leaving the screen and table intact (`history.py:371-377`); open-results failure notifies (`history.py:318-322`). All destructive and preview errors are caught at the screen boundary, exactly per D-04.
- **Confirmation for destructive action**: `PruneConfirmationModal` is presentation-only, itemizes files+KB+bytes, returns `bool`, and HistoryScreen revalidates the cryptographic `expected_preview` fingerprint before `rmtree` (`history.py:345-377`; `prune_modal.py:1-6,119-131`) — exemplary.
- **Honest empty states where they exist**: IDS-disabled vs IDS-enabled-with-zero-events are distinguished verbatim per plan (`results.py:237-249`); no-ID results flow redirects to history with a warning (`results.py:265-279`).
- **Sync**: `on_screen_resume` refreshes both History (`history.py:388-390`) and dashboard (`main_workspace.py:288-291`), satisfying D-02 live synchronization.

Gaps:
- **Zero-run History dead end** (Priority Fix 2): `_refresh_table` handles 0 rows by writing nothing (`history.py:275-285`); contrast the deliberate `CtaHeroPanel` empty state on the dashboard and ResultsScreen's redirect.
- **Keyboard users can't sort**: sorting exists only via mouse `DataTable.HeaderSelected` (`history.py:253-258`); `action_sort_by` (`history.py:249-251`) is bound to nothing anywhere, so there is no keyboard path to a core D-02 capability.
- **Event-loop blocking risk**: `ResultsScreen.__init__` synchronously calls `list_recent_experiments(limit=None)` (full workspace enumeration + manifest parse, `results.py:103,110`), and `app.action_show_results` repeats the scan before pushing (`app.py:244`) — on a large workspace this stalls the UI thread, contrary to the plan's own T-11-06 DoS mitigation intent; the heavy hashing was correctly deferred to a worker but manifest enumeration was not.
- Minor: `Enter` inside the search `Input` does nothing (no `Input.Submitted` handler) — a user who types a filter instinctively presses Enter and gets no jump to the first match; shortcuts [R]/[D] typed while the input is focused are swallowed as text, which is correct behavior but leaves the hint bar partly inert in that context.

**Registry Safety:** skipped — no `components.json` (project is Python/Textual, not shadcn-based) and no UI-SPEC.md registry table. Registry audit: 0 third-party blocks checked, no flags.

---

## Files Audited

- `manet/widgets/qos_scorecard.py` (created, 11-02)
- `manet/screens/results.py` (created, 11-02)
- `manet/screens/history.py` (created, 11-03)
- `manet/screens/prune_modal.py` (created, 11-03)
- `manet/screens/main_workspace.py` (modified, 11-03 — navigation wiring)
- `manet/screens/live_run.py` (modified, 11-03 — [V] View Results)
- `manet/runtime/keymap.py` (modified, 11-03 — BINDING_VIEW_RESULTS)
- `manet/commands/registry.py` (modified, 11-03 — view:history, view:results)
- `manet/app.py` (modified, 11-03 — SCREENS mounting, action_show_results fallback)
- `manet/runtime/theme.py` (read for color-contract baseline; not modified in phase)

Supporting context: `.planning/phases/11-results-experiment-records/11-CONTEXT.md`, 11-01/02/03-PLAN.md, 11-01/02/03-SUMMARY.md (screenshots not applicable — terminal UI).
