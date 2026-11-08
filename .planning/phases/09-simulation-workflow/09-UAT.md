---
status: testing
phase: 09-simulation-workflow
source: [09-VERIFICATION.md]
started: 2026-11-08T11:55:00Z
updated: 2026-11-08T11:55:00Z
---

## Current Test

number: 1
name: Compact Terminal 80x24 Reflow
expected: |
  Launch `python -m manet` in an 80x24 terminal, press [S], cycle through wizard
  Steps 1-3 with Enter/Escape, expand the Advanced Collapsible, and enter an
  invalid node count then blur. No clipped text or awkward wrapping anywhere;
  breakpoint classes shift smoothly; focus lands correctly per step.
awaiting: user response

## Tests

### 1. Compact Terminal 80x24 Reflow

expected: Launch `python -m manet` in an 80x24 terminal, press [S], cycle through wizard Steps 1-3 with Enter/Escape, expand the Advanced Collapsible, enter an invalid node count and blur. No clipped text or awkward wrapping anywhere; breakpoint classes shift smoothly; focus lands correctly per step.
result: [pending]

### 2. Live Blur-Validation and IDS-Lock Feel

expected: Temporarily move `ml/models/best_model.joblib` away, toggle IDS with a valid config, and observe Step 3 lock state and remediation command; restore the artifact and repeat. Errors appear only on blur/submit (never during typing); Launch locks with "CHAMPION MODEL MISSING - IDS DISABLED" + remediation; clicking Confirm does nothing while locked.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
