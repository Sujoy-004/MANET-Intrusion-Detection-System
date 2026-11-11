---
status: complete
phase: 09-simulation-workflow
source: [09-VERIFICATION.md]
started: 2026-11-08T11:55:00Z
updated: 2026-11-08T05:04:05.388Z
---

## Current Test

[testing complete]

## Tests

### 1. Compact Terminal 80x24 Reflow

expected: Launch `python -m manet` in an 80x24 terminal, press [S], cycle through wizard Steps 1-3 with Enter/Escape, expand the Advanced Collapsible, enter an invalid node count and blur. No clipped text or awkward wrapping anywhere; breakpoint classes shift smoothly; focus lands correctly per step.
result: [passed]
notes: Full Step 1-3 walkthrough plus confirm-and-allocate succeeded (run exp_20261108_045743 allocated, notice rendered, health checks green). Scenario-row "click does nothing" verified in code as by-design silent selection (wizard_step_mode.py DataTable handlers); advanced collapsible, invalid-node blur validation, and compact 80x24 layout all confirmed by user.

### 2. Live Blur-Validation and IDS-Lock Feel

expected: Temporarily move `ml/models/best_model.joblib` away, toggle IDS with a valid config, and observe Step 3 lock state and remediation command; restore the artifact and repeat. Errors appear only on blur/submit (never during typing); Launch locks with "CHAMPION MODEL MISSING - IDS DISABLED" + remediation; clicking Confirm does nothing while locked.
result: [passed]
notes: User confirmed blur/submit-only validation, IDS lock banner with remediation command, and inert Confirm while locked.

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
