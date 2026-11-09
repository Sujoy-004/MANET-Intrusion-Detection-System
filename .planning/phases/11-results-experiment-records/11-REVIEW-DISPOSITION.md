---
phase: 11-results-experiment-records
reviewed: 2026-11-09T09:22:37Z
review_status: issues_found
severity:
  critical: 0
  warning: 5
  info: 9
  total: 14
open: 14
fixed: 0
skipped: 0
generated: 2026-11-09
---

# Phase 11 — Review Disposition

Ledger of what happened to each finding from `11-REVIEW.md`. Advisory — edited by hand or by `/gsd-code-review-fix 11` runs; rows with no recorded decision default to `open`.

Legend: triage decisions go in Disposition — `open` · `fixed` · `skipped` · `deferred`. Add the reason to Source when deferring by hand.

| Finding | Title | Severity | Disposition | Source |
|---------|-------|----------|-------------|--------|
| WR-01 | ResultsScreen resolves experiment IDs without workspace containment validation | warning | open | generated from 11-REVIEW.md (2026-11-09) |
| WR-02 | Primary navigation actions fail silently - no user feedback on exception | warning | open | generated from 11-REVIEW.md (2026-11-09) |
| WR-03 | stat race inside list_recent_experiments empties the entire history listing | warning | open | generated from 11-REVIEW.md (2026-11-09) |
| WR-04 | NaN PDR renders as "nan" in the history table (scorecard path is correct) | warning | open | generated from 11-REVIEW.md (2026-11-09) |
| WR-05 | Test swallows its own assertions - artifact verification result can never fail the test | warning | open | generated from 11-REVIEW.md (2026-11-09) |
| IN-01 | Phantom fallbacks defending against unproducible states | info | open | generated from 11-REVIEW.md (2026-11-09) |
| IN-02 | Dead code and unused imports in results.py | info | open | generated from 11-REVIEW.md (2026-11-09) |
| IN-03 | `_format_metric` helper exported but never called | info | open | generated from 11-REVIEW.md (2026-11-09) |
| IN-04 | keymap single-source invariant violated by duplicated inline bindings | info | open | generated from 11-REVIEW.md (2026-11-09) |
| IN-05 | Test hygiene - leftover junk expression, redundant sleeps, unused imports | info | open | generated from 11-REVIEW.md (2026-11-09) |
| IN-06 | HistoryTestApp constructs ResultsScreen with no args — reads the real developer workspace during tests | info | open | generated from 11-REVIEW.md (2026-11-09) |
| IN-07 | Deletion-preview fingerprint does not cover empty directories | info | open | generated from 11-REVIEW.md (2026-11-09) |
| IN-08 | Workspace hero-vs-table layout decided only at compose time | info | open | generated from 11-REVIEW.md (2026-11-09) |
| IN-09 | CSV row_count undercounts files lacking a trailing newline | info | open | generated from 11-REVIEW.md (2026-11-09) |
