---
status: complete
date: "2026-11-07"
slug: refine-phase-08-plans
---

# Quick Task Summary: Refine Phase 8 Plans Before Execution

All 10 requested corrections have been applied across Phase 8 planning documents, validated against schema and structure rules, and re-verified by `gsd-plan-checker` with all checks passing (0 blockers, 0 warnings).

## Key Changes
1. **CTA Honest Workflow Messaging:** `CtaHeroPanel` in `08-02-PLAN.md` and `08-CONTEXT.md` updated to explicitly communicate that the simulation workflow is pending in Phase 9 and not yet available.
2. **ActiveWorkloadCard Engine Status:** `ActiveWorkloadCard` distinguishes engine readiness (`AODV Engine Ready (Offline)`) from active execution state (`IDLE (No active simulation)`), removing any claim that AODV is actively running when idle.
3. **Scikit-Learn Distribution Name Mapping:** `DiagnosticsProbe.probe_dependencies()` explicitly maps `sklearn` import name to `scikit-learn` distribution name when calling `importlib.metadata.version()` to prevent `PackageNotFoundError`.
4. **Dynamic Model Metrics Extraction & Complete Remediation:** Metrics are dynamically parsed from `model_metadata.json` without hardcoding or defaulting to 0.0. Missing model binary is explicitly distinguished from available metadata, and remediation includes dataset generation when required (`Run python scripts/build_dataset.py --multi-attack && python -m ml.train && python -m ml.evaluate`).
5. **Standardized Method Signatures:** Standardized across plans, research, and examples:
   - `DiagnosticsProbe`: `probe_python_version()`, `probe_dependencies()`, `probe_scenarios()`, `probe_datasets()`, `probe_model_artifact()`, `probe_all()`.
   - `WorkspaceAdapter`: `list_recent_experiments(limit: int = 5)`, `has_experiments()`.
6. **Navigation & Console Typing Isolation:** Navigation shortcuts standardized (`[S] Simulation notice`, `[R] Results notice`, `[Ctrl+O] Console (Logs & Diagnostics)`, `[Ctrl+P] Palette`, `[F1] Help`). Bindings for `s` and `r` are scoped to `MainWorkspace` and will not trigger when typing inside `#console-input`. Logs requirement reconciled via the active Console without advertising an unimplemented dedicated logs screen.
7. **Read-Only Workspace Discovery:** `WorkspaceAdapter` strictly performs read-only discovery of `.manet-workspace/`, returning `[]` on missing/empty directories without inventing run records or prematurely implementing Phase 11 manifest logic.
8. **Bounded In-Memory Notification Queue:** `NotificationAdapter` uses `collections.deque(maxlen=20)` to guard against memory leaks under rapid repeated shortcut presses, accompanied by automated repeated-press unit tests.
9. **Validated Scenario Presets:** `DiagnosticsProbe.probe_scenarios()` inspects and parses each JSON file, distinguishing valid presets from malformed files and reporting malformed files in details.
10. **Reconciled Validation Strategy:** `08-VALIDATION.md` Per-Task Verification Map, automated commands, Wave 0 test stubs, and Nyquist criteria match the planned tasks across all 3 plans.

## Verification
- `verify-command-paths`: 0 blockers, 0 warnings.
- `verify-failure-directions`: 0 blockers, 0 warnings.
- `check.decision-coverage-plan`: 5/5 decisions covered (D-01 through D-05).
- `gap-analysis-plan-post`: 8/8 items covered (TUI-06, TUI-07, TUI-08, D-01..D-05).
- `gsd-plan-checker`: ## VERIFICATION PASSED.
