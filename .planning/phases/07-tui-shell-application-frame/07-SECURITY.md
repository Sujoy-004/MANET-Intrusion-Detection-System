---
phase: "7"
slug: "tui-shell-application-frame"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-11-07"
---

# Phase 7 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Terminal → `manet/` TUI process | Keystrokes enter the Textual app (input widgets, keyboard bindings, command palette) | user command text, key events — untrusted input |
| Dispatch boundary: manet/commands → ManetApp | `ConsoleDriver` and the palette provider resolve user input through `manet/commands/registry.py` to an app-action string; a single getattr-on-app performs the single dispatch | parsed command tokens → action object |
| `manet/` → business-logic packages | One-way import contract (D-12): `manet/` never imports `simulator/`, `feature_extraction/`, `ml/`, `attacks/`; presentation is read-only over the existing stack | none (data flows are wired in later phases, not Phase 7) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-7-01 | Elevation of Privilege | `manet/` package scope | medium | mitigate | AST boundary test `tests/test_manet_import_boundaries.py`: no `subprocess`/`shutil`/`os` imports anywhere in `manet/`; no business-package imports; entry point runs the Textual app only (grep audit: zero matched imports — the sole textual match is the rule stated in a docstring) | closed |
| T-7-02 | Tampering (user trust) | `ManetApp` bindings/commands surface | medium | mitigate | Anti-phantom-command honesty loop in `tests/test_manet_command_registry.py`: `hasattr(ManetApp, command.action)` true for every registry entry (D-20); no binding/action declared for a capability that does not exist | closed |
| T-7-03 | Tampering (registry escape) | `manet/commands/palette_provider.py`, `console_driver.py` | medium | mitigate | Provider sources every Hit from `iter_known()` only (tests assert hit-source set == registry display set exactly); console dispatches strictly via `registry.resolve()` after `shlex` tokenize — no shell invocation, no arbitrary callable evaluation | closed |
| T-7-04 | Repudiation / DoS / Information Disclosure | `manet/commands/console_driver.py` history buffer, `manet/runtime/settings.py` | low | mitigate | History is an in-memory `deque(maxlen=100)` with zero disk persistence; `SessionSettings` is a strictly in-memory dataclass; AST zero-disk-write tests in `tests/test_manet_theme.py`/`tests/test_manet_compact.py` prevent accidental file I/O | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

**Cross-plan register note (#4683).** The four threat IDs are shared references to one phase-level threat register — each PLAN's threat table scopes TO-ID mitigations to its own components; the IDs resolve identically across all four plans. Renumbering plan-level registers to unique IDs remains recommended before any future phase-level re-audit that re-scans plan frontmatter independently.

**Scope-clarification note (T-7-04).** `manet/screens/console.py:118` contains an `except Exception: return` early-return guard (`query_one` for an unmounted input widget during teardown). The zero-handler rule is scoped by its authoring plans to plan-07-01 files and to the bounded history / in-memory-state mitigation surfaces, both verified above; the command-execution error path surfaces failures visibly to the RichLog (no swallowing). Recorded as an advisory for `/gsd-review` triage, not an open threat.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|

*No accepted risks.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-07 | 4 | 4 | 0 | the agent (gsd-secure-phase, ASVS L1 grep-depth) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-07
