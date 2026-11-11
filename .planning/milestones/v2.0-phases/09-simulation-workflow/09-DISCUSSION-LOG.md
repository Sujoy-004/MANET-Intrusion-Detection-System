# Phase 09: Simulation Workflow - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-07
**Phase:** 09-Simulation Workflow
**Areas discussed:** Screen Flow & Navigation, Input Validation & Guidance, Custom Parameter Depth, Experiment Naming & Workspace Structure

---

## Screen Flow & Navigation

| Option | Description | Selected |
|--------|-------------|----------|
| Multi-Step Guided Wizard | Step 1 Mode/Scenario Selection -> Step 2 Parameter Configuration -> Step 3 Review & Confirm. Clean navigation on compact 80x24 terminals with sequential validation gating. | ✓ |
| Tabbed Panel Interface | Tabs for Preset, Custom, and Review. Non-linear switching without resetting inputs. | |
| Split-Pane with Live Reactive Summary | Side-by-side config panel on the left and live updating review on the right. | |

**User's choice:** Multi-Step Guided Wizard (Scenario Selection -> Parameter Setup -> Final Review & Confirm)
**Notes:** Selected for clean, distraction-free workflow fitting standard and compact terminals without vertical scroll pressure.

---

## Input Validation & Guidance

| Option | Description | Selected |
|--------|-------------|----------|
| Two-Tier Inline Blur Validation with Review Pre-Flight Blocker | Field validation on blur/unfocus for scalar constraints; structural cross-field invariants and IDS champion model presence verified on Review screen prior to launch. | ✓ |
| Real-Time Keystroke Inline Validation | Immediate error flags and disabled Proceed button on every keystroke. | |
| On-Submit Validation Summary Modal | Consolidated error dialog upon clicking Proceed. | |

**User's choice:** Two-Tier Inline Blur Validation with Review Pre-Flight Blocker
**Notes:** Avoids premature error flicker while typing multi-digit numbers, while providing firm pre-flight safety before run launch.

---

## Custom Parameter Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Progressive Disclosure (Core Primary + Collapsible Advanced Knobs) | Clean 5-control core (Nodes, Duration, Seed, Attacker Class, IDS) with collapsible advanced knobs (Radio Range, Loss Probability, Mobility Speed, Pause Time, CBR Rate, Area). | ✓ |
| Focused Essential Controls Only | Strictly the 5 macro parameters; advanced parameters stay at baseline defaults. | |
| Full Granular Unified Form | All 11+ simulation parameters displayed on the form simultaneously. | |

**User's choice:** Progressive Disclosure (Clean 5-control core with collapsible Advanced Network Knobs)
**Notes:** Balances quick standard runs with academic flexibility for testing difficult wireless channel conditions.

---

## Experiment Naming & Workspace Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Optional Human Tag with Deterministic Default | Automatic unique ID (`exp_YYYYMMDD_HHMMSS_<scenario>_<seed>`) by default, with an optional sanitized tag field (`..._<tag>`). | ✓ |
| Fully Automated Timestamped Identifiers | Strictly automated unique IDs with zero user prompt. | |
| Scenario-Prefixed Hierarchical Folders | Nested folders grouped by scenario name with incrementing numbers (`run_001`). | |

**User's choice:** Optional Human Tag with Deterministic Default
**Notes:** Guarantees collision-free execution while allowing researchers to label specific experiment runs for easy identification in the dashboard history table.

---

## the agent's Discretion

- Exact Textual widget selection for preset scenario list (`OptionList` vs `DataTable`).
- Visual styling for validation badges and warning indicators.
- Structure of the simulation configuration adapter and validation helpers.

## Deferred Ideas

- Background worker thread execution, live telemetry streaming, and safe cancellation — Phase 10 (TUI-15..TUI-18).
- Results inspection, SHA-256 checksums, and session history browsing — Phase 11 (TUI-19..TUI-21).
- In-TUI live model retraining / evaluation workload runner — Phase 10 / future scope (TUI-MLWORK).
- Interactive packet replay and animation — future milestone (VIZ-01).
