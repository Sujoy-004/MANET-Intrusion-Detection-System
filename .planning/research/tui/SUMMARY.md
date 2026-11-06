# Project Research Summary — Interactive TUI (v2.0)

**Project:** Machine Learning-Based Intrusion Detection System for MANET
**Domain:** Terminal User Interface presentation layer over the existing simulator/IDS stack
**Researched:** 2026-11-06
**Confidence:** HIGH (framework choice verified against PyPI live metadata; integration points verified against repo docs/code layout)

## Framework Decision: Textual (single added dependency)

**Candidates evaluated:**

| Option | Verdict | Rationale |
|--------|---------|-----------|
| **Textual 8.2.8** (PyPI-verified current) | **SELECTED** | Pure-Python, no toolchain (respects "no C/C++ compilation" constraint); full-screen app model, keyboard-first focus management, **built-in searchable command palette** (`App.COMMANDS`), screens/widgets composition, Windows terminal support out of the box, Rich rendering underneath (Rich becomes available transitively, aligning with existing Matplotlib/Seaborn-adjacent styling). Requires Python 3.9+; project is 3.11+. One pinned dependency: `textual` (pin via README, same pattern as `simpy==4.1.2`). |
| Rich + prompt_toolkit | Declined | Two dependencies to version-pin instead of one; manual full-screen screen management, palette and widget system must be hand-built; three-way state integration (prompt_toolkit loop + Rich rendering + existing modules) duplicated for no benefit. prompt_toolkit(stdin) also complicates Windows Console API nuances. |
| urwid, curses | Declined | curses is POSIX-oriented on Windows (no native support); urwid smaller ecosystem, no command palette. |
| Web/Tk GUI | Declined | Violates "no web server / local-first terminal application" scope. |

## Stack Additions

- `textual==8.2.8` (pinned in README install line, transitive `rich` — do not depend on it directly beyond Textual's public API)
- **NO new** database, plugin system, web server, cloud dependency (spec-conformant)

## Integration Points (existing modules remain source of truth)

| TUI component | Existing source of truth (do not duplicate logic) |
|---------------|---------------------------------------------------|
| Scenario loading | `scenarios/*.json` schema read via the existing scenario loader used by `simulator/run_scenario.py` |
| Run execution | `SimulationRunner` (simulator package) called from a worker thread; TUI never mutates AODV/attack logic |
| Metrics | `simulator.metrics.compute_metrics` — authoritative for PDR/throughput/delay/routing overhead display |
| IDS enablement | Existing `--ids` path of `run_scenario`; gate on champion model artifact availability (model metadata currently reports Grayhole F1 = 0.0 → dashboard must NOT claim effective Grayhole detection) |
| CLI compatibility | `python -m simulator.run_scenario`, `scripts/build_dataset.py`, `python -m ml.train/evaluate` preserved unchanged; legacy CLI tests must keep passing |

**Data/artifacts policy:** unique experiment directories under a new dedicated `.manet-workspace/`; never overwrite `traces/`, `data/`, `models/`, or existing `results/`. Workspace ignore semantics documented in README; current `.gitignore` untouched except for any additive workspace-ignores required by conventions (documented in CHANGELOG/README).

## Feature Table Stakes (v2.0 scope per task spec)

1. App shell: `python -m manet`, dark cybersecurity palette (cyan navigation / blue info / green healthy / amber warning / red critical), visible focus, shortcut hints, resize-tolerant compact layout, reduced-motion + high-contrast where the framework supports it
2. Dashboard: real diagnostics (Python version, dependency availability, scenario/dataset/model-artifact presence), explicit verified/experimental/partial/unavailable states, no mock values
3. Simulation workflow: preset mode (real scenario JSON name + description + params), custom mode validated against actual runner parameter surface, seed selection, review/confirm screen, unique experiment dir
4. Execution: background worker (thread-based judged safe since simulation is deterministic, pure-Python and CPU-bound only when SimPy process-events; process fallback evaluated in planning), bounded streaming telemetry (bounded queue, drop-oldest, capped live rows), safe Ctrl+C/Esc handling, stop/cancel with partial-trace preservation and honest "interrupted" status; pause/resume NOT supported by the runner → presented as disabled in the UI
5. Results: real metrics via `compute_metrics`, manifest (experiment ID, config, seed, software versions, timestamps, status, paths), atomic manifest writes, SHA-256 for completed artifacts, read-only completed records, session history list

## Watch Out For (pitfalls)

- **Never block the Textual loop** — simulation must run in a worker; never call `SimulationRunner` inside a `@work`-blocking UI widget callback or freeze occurs
- **Bounded telemetry** — the SimPy event stream is high-volume; unbounded queue retention is forbidden by spec and by memory reality; use bounded queue + coalescing, cap at constant size
- **Honest capability states** — model metadata Grayhole F1 = 0.0 must be surfaced as experimental/unavailable, not as an effective detector; missing artifacts show explicitly `unavailable`
- **Do not weaken existing tests** — 79-test baseline (CHANGELOG 1.1.0) must stay green before/after; baseline must be captured before editing
- **Determinism** — seed passes through unchanged; interruption must not corrupt trace files; partial traces remain on disk and manifest marks interrupted
- **No shell execution** — command console is application-command-only; no OS shell passthrough
- **CHANGELOG.md is authoritative** (.planning/ history may lag: v1.0 GSD archive does not include the 1.1.0 AODV recovery work documented in CHANGELOG of 2026-11-03)

## Implications for Roadmap

Suggested phase spine (roadmapper free to adjust): (a) TUI shell + launcher + palette + theming; (b) dashboard diagnostics/capability detection; (c) simulation workflow (preset/custom/review); (d) background worker + bounded telemetry + cancellation; (e) experiment records + results surfaces; (f) tests + docs (README/CHANGELOG). Advanced ML/data-lab/IDS-admin/reporting screens deferred — modular placeholders.

## Sources

- PyPI JSON API: https://pypi.org/pypi/textual/json (textual 8.2.8, requires_python <4.0,>=3.9, pure wheel)
- In-repo: README.md install line and CLI examples; CHANGELOG.md [1.1.0] 2026-11-03 (79 tests, AODV recovery); `scenarios/`, `simulator/`, `ml/`, `scripts/`, `docs/` layout
