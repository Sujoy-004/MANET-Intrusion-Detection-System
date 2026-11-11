# Phase 8: Operational Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-11-07
**Phase:** 08-Operational Dashboard
**Areas discussed:** Dashboard Layout & Section Hierarchy, Capability Diagnostics & Refresh Behavior, Missing Component & Warning Presentation, First-Run & Empty State Experience

---

## Dashboard Layout & Section Hierarchy

| Option | Description | Selected |
|--------|-------------|----------|
| Top Status Cards with Split Body (Executive Grid) | Immediate at-a-glance visibility across health, experiments, and actions at launch; prominent placement for honest capability states; clean responsive scaling | ✓ |
| Stacked Vertical Stream | Natural flow across all window widths without complex breakpoints; full width for detailed experiment metric tables | |
| Tabbed Operational View | Dedicated full-screen view for each section (Health, Experiments, Quick Actions); zero visual crowding | |

**User's choice:** Top Status Cards with Split Body (Executive Grid)
**Notes:** Provides instant situational awareness and preserves responsive collapse into a single vertical stream on smaller screens.

---

## Capability Diagnostics & Refresh Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Startup + Manual Refresh ('r' / 'F5' hotkey) | Zero background CPU/disk usage; gives full deterministic control; zero risk of file locking | |
| Lifecycle Events + Manual Fallback | Updates automatically when an in-app task finishes; manual 'r' fallback | |
| Periodic Background Polling (every 3-5s) | Hands-free; automatically discovers newly trained models or datasets without user interaction | ✓ |
| Startup-Only Check | Zero background overhead; static check on launch | |

**User's choice:** Periodic Background Polling (every 3-5s)
**Notes:** User preferred automatic background polling so that new datasets and models placed or trained during the session are recognized without requiring manual keypresses or app restarts.

---

## Missing Component & Warning Presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Inline Contextual Badges within Capability Cards | Uses zero extra vertical space; keeps dashboard clean, organized, and balanced; pairs warnings directly with components | ✓ |
| Prominent Top Alert Banner with Next Steps | High-visibility callout box at top of screen with exact remediation CLI commands | |
| Dedicated Diagnostics Modal ('d' hotkey) | Keeps main dashboard clean; shows deep academic audit details in a popup | |

**User's choice:** Inline Contextual Badges within Capability Cards
**Notes:** Aligns with the Top Status Cards layout; communicates missing artifacts and Grayhole F1 0.0 partial efficacy honestly without consuming excessive vertical space on standard 80x24 viewports.

---

## First-Run & Empty State Experience

| Option | Description | Selected |
|--------|-------------|----------|
| Persistent Grid with Empty-State Placeholders | Predictable fixed visual layout from day one; honest zero-data display | |
| Guided Call-to-Action (CTA) Hero Panel | Obvious visual guidance on first launch; clear prompt ("Press [S] to launch your first MANET simulation") | ✓ |
| Embedded Quick-Start Checklist Card | Checkmarks next to prerequisites (Environment, Scenarios, Model); multi-step onboarding | |

**User's choice:** Guided Call-to-Action (CTA) Hero Panel
**Notes:** User chose a guided CTA hero panel for the first-run experience to provide clear onboarding direction before the first simulation run is recorded.

---

## the agent's Discretion

- Specific diagnostic probe implementation in `manet/adapters/diagnostics.py` or similar helper module.
- Fine-grained typography and border styling referencing theme color tokens.

## Deferred Ideas

- Interactive graphical packet flow animation & live topology map (deferred to future milestone VIZ-01).
- In-TUI ML model training workflow (deferred to future milestone TUI-MLWORK).
