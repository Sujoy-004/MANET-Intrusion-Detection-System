---
phase: "11"
slug: "results-experiment-records"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-09"
---

# Phase 11 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Experiment workspace root (.manet-workspace/) | User-owned local files vs. adapter-controlled manifest writes/deletes — deletion and verification surface | Artifact bytes, manifest JSON/CSV, artifact hashes; traversal/symlink containment required |
| Presentation layer (Textual screens/widgets) | TUI rendering vs. generated artifacts from scripts/datasets — display surface | Filesystem paths, SHA-256 digests, isolation-log CSV lines, metric values |
| Git repository | Generated experiment traces must never enter version control | .gitignore containment for .manet-workspace/ |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-11-01 | Tampering | manet/adapters/workspace.py | medium | mitigate | Atomic manifest writes via tmp file + `os.replace` across COMPLETED/INTERRUPTED/FAILED; chunked 64KB SHA-256 — automated: `tests/test_manet_manifest_artifacts.py::test_tracer_manifest_hash_and_verify` (green) | closed |
| T-11-02 | Tampering | manet/adapters/workspace.py | high | mitigate | Exact SHA-256 verification detecting alteration/missing/corruption — automated: `test_artifact_tamper_detection` etc. (green) | closed |
| T-11-03 | Elevation of Privilege | manet/adapters/workspace.py | high | mitigate | Strict symlink rejection (lstat) + path-traversal containment in delete/preview — automated: `tests/test_manet_workspace_pruning.py` symlink/traversal set (green; 3 skip = Windows symlink-creation privilege constraint on test setup, guard assertions themselves pass) | closed |
| T-11-04 | Information Disclosure | manet/widgets/qos_scorecard.py | medium | mitigate | Dynamic strings escaped via `rich.markup.escape`; honest N/A for NaN/inf/None — automated: scorecard metric tests (green) | closed |
| T-11-05 | Information Disclosure | manet/screens/results.py | medium | mitigate | Schema-accurate isolation log or honest empty state; stale-worker guards — automated: `test_results_screen_ids_empty_states_distinction`, stale-discard workers tests (green) | closed |
| T-11-06 | Denial of Service | manet/screens/history.py | medium | mitigate | In-memory filtering/sorting, bounded table population — automated: history browse/sort/sort-filter tests (green) | closed |
| T-11-07 | Tampering | manet/screens/prune_modal.py | high | mitigate | Un-dismissible modal with explicit Enter confirmation + pre-deletion cryptographic revalidation — automated: `test_prune_confirmation_modal_preview_composition` set (green) | closed |
| T-11-08 | Information Disclosure | .gitignore / tests/test_manet_import_boundaries.py | high | mitigate | `.manet-workspace/` git-ignored (test_git_check_ignore_workspace, green) + AST import-boundary tests green (4 passed) | closed |
| T-11-SC | Tampering | npm/pip/cargo installs | high | mitigate | No external packages installed in Phase 11 — verified: pyproject/requirements/lock files unchanged across baa0c2d..HEAD (empty diff); new code imports stdlib + pre-existing textual only (re-verified per plan 11-01/11-02/11-03) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (high) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|

*Accepted risks do not resurface in future audit runs.*

*If none: "No accepted risks."*

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-09 | 9 | 9 | 0 | orchestrator (GLM-5.3 Flash) — L1 grep + automated-test evidence; short-circuit per ASVS L1 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-09 — threat register authored at plan time; all dispositions `mitigate` evidenced by automated tests (Nyquist audit green) and/or absence-of-change checks; short-circuit rule applied (threats_open: 0, register_authored_at_plan_time: true, asvs_level == 1)
