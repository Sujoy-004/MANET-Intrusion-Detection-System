# Quick Task: Refine Phase 8 Plans Before Execution

**Slug:** refine-phase-08-plans  
**Date:** 2026-11-07  
**Status:** complete  

## Objective
Apply final refinement to Phase 8 planning documents (`08-01-PLAN.md`, `08-02-PLAN.md`, `08-03-PLAN.md`, `08-VALIDATION.md`, `08-RESEARCH.md`, `08-CONTEXT.md`), correcting all 10 identified issues and verifying cross-document consistency while preserving decisions D-01 through D-05 and the 3-plan/3-wave architecture.

## Tasks
- [x] Task 1: Update CTA Hero Panel to not claim pressing S launches/configures simulation (workflow pending in Phase 9).
- [x] Task 2: Update ActiveWorkloadCard to distinguish routing engine availability (AODV Engine Ready Offline) from active execution state (IDLE), never claiming AODV is actively running when idle.
- [x] Task 3: Map import name `sklearn` to distribution name `scikit-learn` in `importlib.metadata.version` lookup to prevent `PackageNotFoundError`.
- [x] Task 4: Extract model metrics dynamically from `model_metadata.json` schema without hardcoding or 0.0 defaults; distinguish missing binary from available metadata; update model remediation to include dataset generation.
- [x] Task 5: Standardize `DiagnosticsProbe` and `WorkspaceAdapter` method names across plans, research, and implementation examples.
- [x] Task 6: Reconcile navigation: `ctrl+o` = Console (logs & diagnostics), `ctrl+p` = Palette, `s` = Simulation notice, `r` = Results notice, `f1` = Help; ensure `s` and `r` do not interfere with typing in the console input.
- [x] Task 7: Keep workspace discovery strictly read-only; do not invent run records or premature Phase 11 manifest logic.
- [x] Task 8: Bound `NotificationAdapter` in-memory queue (`maxlen=20`) and add repeated-shortcut tests.
- [x] Task 9: Make scenario discovery distinguish valid JSON presets from malformed files.
- [x] Task 10: Reconcile `08-VALIDATION.md` per-task map, automated commands, Wave 0 stubs, and Nyquist sign-off.
