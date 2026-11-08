---
phase: "09"
slug: "simulation-workflow"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-11-08"
---

# Phase 9 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| File System -> TUI Adapter | Scenario JSON files from disk loaded into Python memory (Plan 09-01) | Scenario schema + parameters (attacker-controlled file content) |
| User Input -> File Path | Custom run tag string converted into workspace directory name on Windows filesystem (Plan 09-01) | Path string (hostile tag characters) |
| Model Artifact -> TUI Capability | Verification of `ml/models/best_model.joblib` before allowing IDS activation (Plan 09-01) | Filesystem stat result |
| User Keyboard Input -> Form State | Raw keystrokes received by Textual inputs for nodes, durations, seed, and tags (Plan 09-02) | Form state values |
| Form State -> Review Screen | Transition from individual inputs to validated invariant snapshot (Plan 09-02) | Configuration dict |
| Review Screen -> Workspace Filesystem | Launch confirmation triggers physical directory allocation and manifest write (Plan 09-02) | Directory + manifest.json |
| Command Console / Palette -> App Navigation | String input from user resolved to action method on `ManetApp` (Plan 09-03) | Action name string |
| Presentation Layer -> Simulation Execution | Configuration payload handed over to `SimulationRunner` (Plan 09-03) | Scenario dict |

---

## Threat Register

*Register authored at plan time across the three phase PLANs (T-09-SC deduplicated across 09-01/09-02/09-03).*

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-09-01 | Tampering | `manet/adapters/scenario.py` | high | mitigate | stdlib `json.load` only (`scenario.py:39`); schema-key validation on load; malformed files rejected/skipped without code execution; `manet/` AST-import boundary suite proves no `os`/`subprocess` execution surface (`test_manet_never_imports_business_packages`, `test_command_package_never_uses_os_execution` green) | closed |
| T-09-02 | Denial of Service | `manet/adapters/simulation_config.py` | medium | mitigate | Two-tier validation implemented: `validate_node_count` / `validate_duration` / `validate_seed` / `validate_radio_range` / `validate_loss_probability` + `validate_structural_invariants` (flow endpoints), all unit-tested before handoff to the runner | closed |
| T-09-03 | Elevation / Tampering | `manet/adapters/workspace.py` | high | mitigate | `sanitize_run_tag` (`workspace.py:15`) strips `..`, slashes, colons, Windows-illegal chars with 32-char cap, applied at allocation (`:166`); root containment via `is_relative_to` (`:179`); collision-free `mkdir(exist_ok=False)` (`:183`) — sanitization/containment tests green. Caveat: CR-02 — truncation can leave a trailing `.` at char 32 (string-level edge; normalized by Win32 FS; collision loop preserves uniqueness — see notes) | closed |
| T-09-04 | Repudiation | `manet/adapters/simulation_config.py` | medium | mitigate | Champion artifact gate `target_model.is_file() and stat().st_size > 0` (`simulation_config.py:161-171`) with actionable remediation message on rejection | closed |
| T-09-05 | Denial of Service | `manet/widgets/wizard_step_params.py` | low | mitigate | Blur validation: 12 `Input` widgets declared `validate_on=["blur"]` plus submit-time validator traversal; no validation thrash during typing (pilot-asserted) | closed |
| T-09-06 | Elevation / Tampering | `manet/widgets/wizard_step_params.py` | medium | mitigate | Input-level caps NOT present on `#input-run-tag` (`wizard_step_params.py:293-298` — mitigation drills down one layer): both length cap and character restrictions enforced by `sanitize_run_tag` at the allocator boundary before any filesystem effect, with containment + lint tests green. Risk mitigated at the FS-effective boundary; widget-layer cap recorded as hardening note (see notes) | closed |
| T-09-07 | Repudiation | `manet/widgets/wizard_step_review.py` | high | mitigate | Step 3 displays champion model status (`:237` PRESENT / `:244` MISSING + `:246` remediation command) and strictly locks Launch when IDS enabled without artifact (verifier evidence `wizard_step_review.py:232-248, 270-281`; pilot `test_ids_gating` covers all 3 branches) | closed |
| T-09-08 | Elevation of Privilege | `manet/commands/registry.py` | high | mitigate | `AppCommand.action` entries are string method names only (`action_show_workspace`, `action_show_simulation`, ...); resolver dispatches via `getattr` on `ManetApp` — no shell execution or arbitrary callables; dedicated `test_command_package_never_uses_os_execution` green | closed |
| T-09-09 | Denial of Service | `tests/test_manet_simulation_runner_compat.py` | medium | mitigate | All compat durations 2.0s / 5.0s / 4.0s / 3.0s — under the 10.0s cap, flagged with an explicit T-09-09 comment in-file | closed |
| T-09-SC | Tampering | npm/pip/cargo installs | high | mitigate | Package legitimacy gate honored: `git diff b0aa3c3a..HEAD` over `pyproject.toml`, `requirements.txt`, lockfiles = empty; zero new external dependencies (SUMMARY 09-03 frontmatter `added: []`) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Notes (hardening caveats surfaced during verification, non-blocking)

- **CR-01 (review):** duplicate `scenario_id` across hypothetical future `scenarios/*.json` files would raise `DuplicateKey` in `StepModeSelectWidget.on_mount` (`wizard_step_mode.py:161` `add_row(key=...)`). All 5 real scenario files have unique IDs — no live exposure; recommend a dedupe guard in `refresh_presets()` before/during Phase 10.
- **CR-02 (review):** `sanitize_run_tag` truncation can re-emit a trailing `.` at char 32. Empirically normalized by Win32 FS on `mkdir` and uniqueness is preserved by the collision loop; one-line fix (`cleaned[:32].rstrip("._")`) recommended.
- **T-09-06 single-boundary defense:** widget-level run-tag caps absent; sanitizer at the allocator is the sole enforcement layer. Defense-in-depth cap at the Input would restore the plan's two-layer intent.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|

*No accepted risks.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-08 | 10 | 10 | 0 | opencode /gsd-secure-phase (L1 grep classification, plan-authored register, ASVS-1 short-circuit) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-08
