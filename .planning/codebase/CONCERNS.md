# Codebase Concerns

**Analysis Date:** 2026-10-22

> **Scope of this audit.** The repository is at a **pre-implementation / spec-only** state. The entire tracked content is `AGENTS.md` (177 lines), `MANET_IDS_BTech_Execution_Guide.md` (391 lines) and `.gitignore` (22 lines). Git is initialised on branch `main` with **one commit** (`2246d39 Add project spec and agent instructions`) and **no remote**. There is no source code, no manifest, no CI, and no test suite.
>
> **Therefore no concern below claims a bug in code that was never written.** Every item is one of three things: a defect in a file that exists today, a risk the *specified* architecture or process will create, or a thing the spec requires that does not exist yet.

## Classification legend

| Tag | Meaning |
|-----|---------|
| **[CURRENT]** | A problem that exists in the repository right now, in a committed file or in the repo's git state. |
| **[RISK]** | A risk the specified architecture or process will create if implemented as written. Grounded in a doc citation. |
| **[GAP]** | Something `AGENTS.md` or `MANET_IDS_BTech_Execution_Guide.md` requires that does not exist yet. |
| **[FRAGILE]** | An area that works but has a low margin for error — safe only with a specific discipline. |

## Severity scale

| Severity | Meaning |
|----------|---------|
| **Critical** | If it happens, the project's headline claims (accuracy, IDS benefit, "reproducible") become false or unverifiable. The failure is silent and self-congratulating — it looks like success. |
| **High** | Blocks a guide gate, a Day-N deliverable, or a viva question, and costs rework measured in days. |
| **Medium** | Degrades quality or reproducibility; recoverable, but it will show up in the report or the defence. |
| **Low** | Hygiene. Cheap to fix, annoying if left. |

## Severity ranking (read this first)

| ID | Sev | Class | Concern | Primary paths |
|----|-----|-------|---------|---------------|
| [C-01](#c-01-random-row-split-is-the-single-biggest-way-to-fake-this-project) | Critical | [RISK] | Random row split inflates every score | `ml/` (future) |
| [C-02](#c-02-leakage-features-make-detection-trivial-and-the-result-worthless) | Critical | [RISK] | Leakage features | `feature_extraction/` (future) |
| [C-03](#c-03-attack-that-does-not-change-measurable-behaviour-makes-everything-downstream-worthless) | Critical | [RISK] | Attack with no measurable effect | `attacks/`, `simulator/` |
| [C-04](#c-04-no-test-harness-the-baseline-can-drift-silently) | Critical | [GAP] | No test harness | repo root, `tests/` |
| [C-05](#c-05-no-baseline-aodv-comparison-the-ids-benefit-is-unmeasurable) | Critical | [RISK] | No baseline-AODV comparison | `results/`, `ml/` |
| [C-06](#c-06-per-run-records-are-gitignored-so-rule-8-cannot-be-satisfied-inside-the-repo) | Critical | [CURRENT] | Per-run records ignored → numbers untraceable | `.gitignore:6-7` |
| [C-07](#c-07-non-determinism-makes-the-whole-experiment-matrix-unreproducible) | High | [RISK] | Missing seed / set iteration order | `simulator/` |
| [C-08](#c-08-label-integrity-and-the-undefined-observation-window) | High | [RISK] | Labels + undefined window/row granularity | `feature_extraction/` |
| [C-09](#c-09-accuracy-only-reporting-on-structurally-imbalanced-data) | High | [RISK] | Accuracy-only reporting, structural imbalance | `ml/` |
| [C-10](#c-10-no-git-remote-no-backup-no-collaboration-no-ci) | High | [CURRENT] | No remote | repo root |
| [C-11](#c-11-two-sources-of-truth-with-a-manual-sync-rule-and-a-live-disagreement) | High | [CURRENT] | Doc drift | `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md` |
| [C-12](#c-12-no-manifest-and-no-lockfile-results-can-drift-between-machines) | High | [GAP] | No `requirements.txt` / lockfile | repo root |
| [C-13](#c-13-a-directly-readable-attack-flag-makes-detection-trivial) | High | [RISK] | Trivially detectable attack | `simulator/aodv.py`, `attacks/` |
| [C-14](#c-14-the-entire-target-layout-is-missing) | High | [GAP] | No `simulator/`, `attacks/`, `ml/`, `docs/`, `README.md` | repo root |
| [C-15](#c-15-the-acceptance-criterion-chain-does-not-exist) | High | [GAP] | Acceptance chain unimplemented | repo root |
| [C-16](#c-16-scope-explosion-the-guide-names-six-ways-to-fail) | High | [RISK] | Scope creep | `AGENTS.md:155-157` |
| [C-17](#c-17-overclaiming-what-the-model-detects) | Medium | [RISK] | Overclaiming | `README.md`, report |
| [C-18](#c-18-the-data-ignore-rule-cancels-the-keep-samples-policy) | Medium | [CURRENT] | `data/` ignore vs "keep samples" | `.gitignore:3` |
| [C-19](#c-19-the-feature-schema-mixes-observed-traffic-features-with-scenario-constants) | Medium | [RISK] | Schema mixes provenance classes | guide schema |
| [C-20](#c-20-the-threshold-and-the-response-loop-can-cascade-into-network-collapse) | Medium | [RISK] | Threshold + cascade | `ml/`, `simulator/` |
| [C-21](#c-21-copying-old-tutorial-snippets-breaks-silently) | Medium | [RISK] | Version traps | `AGENTS.md:98-105` |
| [C-22](#c-22-per-packet-python-overhead-is-the-performance-cliff) | Medium | [RISK] | Python overhead | `simulator/` |
| [C-23](#c-23-platform-lock-no-external-simulator-to-cross-check-fidelity-against) | Medium | [RISK] | Windows-only, no NS-3 | `AGENTS.md:27` |
| [C-24](#c-24-the-response-mechanism-changes-the-distribution-the-detector-was-trained-on) | Medium | [RISK] | Covariate shift | `ml/`, `simulator/` |
| [C-25](#c-25-gitignore-claims-reproducible-from-a-seed-which-is-not-true) | Medium | [CURRENT] | False reproducibility claim | `.gitignore:1` |
| [C-26](#c-26-no-readme-no-experiment-log-no-scope-freeze-no-saved-model) | Medium | [GAP] | Missing artefacts | `docs/`, `ml/`, `README.md` |
| [C-27](#c-27-the-rules-live-only-in-prose-nothing-in-the-repo-enforces-them) | Medium | [FRAGILE] | Rules unenforced | `AGENTS.md` |
| [C-28](#c-28-a-committed-joblib-model-is-version-fragile-and-an-arbitrary-code-execution-surface) | Medium | [RISK] | Model artefact handling | `ml/` |
| [C-29](#c-29-knowledge-concentration-in-a-four-person-team-on-a-21-day-plan) | Medium | [RISK] | Bus factor | repo root |
| [C-30](#c-30-the-row-granularity-ambiguity-decides-whether-the-ids-can-name-a-node) | Medium | [GAP] | Row unit undefined — the IDS cannot name a node without it | guide:104 |
| [C-31](#c-31-gitignore-does-not-cover-planning-artifacts-logs-or-model-binaries) | Low | [CURRENT] | Ignore-rule coverage | `.gitignore` |
| [C-32](#c-32-svc-does-not-scale-to-the-generated-dataset-size) | Medium | [RISK] | `SVC` does not scale to the dataset | `ml/` |
| [C-33](#c-33-no-ci-no-scenario-registry-no-version-tag-convention) | Low | [GAP] | No automation, no scenario index | repo root |

---

## Tech Debt

### [C-11] Two sources of truth with a manual sync rule and a live disagreement

- **Class:** [CURRENT] · **Severity:** High
- **Issue:** The project runs on two overlapping documents that must be edited in lockstep, enforced by prose only. `AGENTS.md:14-16` states the precedence rule — "`AGENTS.md` wins on engineering rules and the guide wins on project specification. **Keep both files in sync** — change one, change the other in the same commit. Never leave them disagreeing." `AGENTS.md:36-37` repeats it for architecture changes. The sync check is a human/agent reading two files; nothing enforces it.
  The disagreement is **already present**:
  - `MANET_IDS_BTech_Execution_Guide.md:153` (setup checklist) says "Install Git and create a private/public repository", and `MANET_IDS_BTech_Execution_Guide.md:278` (Day 1) makes "Create Git repository" a deliverable.
  - `AGENTS.md:6-7` says "Git is initialised on `main` with **no remote configured** — everything stays local until a remote is deliberately added."
  These are not reconcilable by a reader who does not already know the answer. Git is initialised (so Day 1's literal deliverable is arguably met) but the guide still tells a newcomer to create a repository.
  - `MANET_IDS_BTech_Execution_Guide.md:160-173` lists `README.md` in the repository structure; `AGENTS.md:113-124` (the "Target repo layout") omits `README.md` entirely.
  - `AGENTS.md:5` claims "This repo currently contains **only** `MANET_IDS_BTech_Execution_Guide.md` and this file" — already inaccurate, since `.gitignore` is a third tracked file and `.planning/` now exists.
- **Files:** `AGENTS.md:5`, `AGENTS.md:6-7`, `AGENTS.md:14-16`, `AGENTS.md:36-37`, `AGENTS.md:113-124`, `MANET_IDS_BTech_Execution_Guide.md:153`, `MANET_IDS_BTech_Execution_Guide.md:160-173`, `MANET_IDS_BTech_Execution_Guide.md:278`
- **Impact:** A future executor reads one document and acts on it. If the guide's NS-3/Ubuntu-era text resurfaces (the guide itself warns the original brief "reads like a mentor-supplied handbook", `AGENTS.md:32-33`), an agent can spend a day trying to install `ns-3-dev` on a machine with no `gcc`, no `cmake` and no WSL. The guide's own "Final note" (`MANET_IDS_BTech_Execution_Guide.md:391`) is the stated goal — "clean experimental design, reproducible simulation, realistic attack behavior, leakage-free evaluation" — and none of that is enforceable while the rules live in prose that drifts.
- **Fix approach:** Pick one direction and make it non-ambiguous, then record it in both files in the same commit.
  1. Mark the superseded lines **in place** with a short `> Superseded — see AGENTS.md:<line>` blockquote. Specifically: `MANET_IDS_BTech_Execution_Guide.md:153` and `:278` (git/remote), and add `README.md` to the `AGENTS.md:113-124` tree.
  2. Correct `AGENTS.md:5` to enumerate the actual tracked files.
  3. Add a `docs/decisions.md` with a dated decision log. Every architectural change appends one row: date, decision, doc(s) changed, commit SHA. This gives the sync rule an anchor and satisfies the "notes, deviations" purpose of the `docs/` directory (`AGENTS.md:123`).
  4. When an architecture change lands, the commit message must contain the literal token `docs-sync` so it is greppable in `git log --grep`.

### [C-12] No manifest and no lockfile: results can drift between machines

- **Class:** [GAP] · **Severity:** High
- **Issue:** There is no `requirements.txt`, no `pyproject.toml`, no lockfile of any kind. The only record of the dependency versions is a prose paragraph in `AGENTS.md:93-95`. The guide's Day 2 deliverable explicitly requires recording versions (`MANET_IDS_BTech_Execution_Guide.md:279`: "Set up the Python environment, install dependencies, **record versions**"), and `MANET_IDS_BTech_Execution_Guide.md:152` lists the install command with no manifest to install from.
- **Files:** `AGENTS.md:93-95`, `AGENTS.md:107`, `MANET_IDS_BTech_Execution_Guide.md:152`, `MANET_IDS_BTech_Execution_Guide.md:279`
- **Impact:** Two students on the same project can install different versions and produce different numbers from the same scenario and seed. The "reproducible" claim then becomes unreproducible for reasons nobody can diagnose, and rule 8 (`AGENTS.md:151`) — every number traces to a saved run — quietly fails because the environment that produced it is unrecorded. The gap is aggravated by the version traps in [C-21]: an unpinned `pandas>=2` would float to pandas 4.x and change `groupby`/null semantics under the experiment.
- **Fix approach:** Create `requirements.txt` at the repo root, before the first simulation run, with **exact `==` pins** matching the verified environment (checked 2026-10-22): `simpy==4.1.2`, `networkx==3.6.1`, `scikit-learn==1.8.0`, `pandas==3.0.2`, `numpy==1.26.4`, `scipy==1.17.1`, `matplotlib==3.10.8`, `seaborn==0.13.2`. Add `pytest==9.0.2` when the suite lands ([C-04]). Record the interpreter (`3.11.8`) and the pip invocation convention (`python -m pip install -r requirements.txt`, per `AGENTS.md:107`) in a short `docs/environment.md`. Do not add a lockfile generator; plain `==` pins are sufficient and match the "smallest change that solves the problem" rule.

### [C-14] The entire target layout is missing

- **Class:** [GAP] · **Severity:** High
- **Issue:** Not one directory or file from the prescribed layout exists. `AGENTS.md:113-124` and `MANET_IDS_BTech_Execution_Guide.md:160-173` both specify `simulator/`, `attacks/`, `scenarios/`, `traces/`, `data/`, `feature_extraction/`, `ml/`, `results/`, `dashboard/`, `docs/`, `README.md`. None is present.
- **Files:** `AGENTS.md:113-124`, `MANET_IDS_BTech_Execution_Guide.md:160-173`
- **Impact:** Every downstream concern in this document ([C-01], [C-02], [C-03], [C-05], [C-13], [C-22]) is currently *latent* rather than *active*. That is the good news. The risk is that the scaffold gets created ad-hoc under time pressure (Day 2, `MANET_IDS_BTech_Execution_Guide.md:279`) without the import boundary or the package boundaries being thought about, which converts latent risks into active ones.
- **Fix approach:** Create the scaffold as an explicit, reviewable commit before any logic lands. Minimum Day-2 scaffold: `simulator/` (with `__init__.py`, `mobility.py`, `radio.py`, `aodv.py`, `traffic.py`, `metrics.py`, `run_scenario.py` per `AGENTS.md:56-65`), `attacks/` (top-level, `__init__.py`), `scenarios/`, `feature_extraction/`, `ml/`, `docs/`, `results/plots/` (empty dir + `.gitkeep`, since `results/*` is ignored — see [C-06]), `tests/`. Add `README.md` at the root. Do **not** create `dashboard/` until the acceptance chain works (`AGENTS.md:166-167`).

### [C-16] Scope explosion: the guide names six ways to fail

- **Class:** [RISK] · **Severity:** High
- **Issue:** `AGENTS.md:155-157` and `MANET_IDS_BTech_Execution_Guide.md:59` prohibit starting with "six attacks, deep learning, federated learning, blockchain and a mobile application simultaneously". `MANET_IDS_BTech_Execution_Guide.md:68-75` lists six stretch features (XGBoost/ensemble, online learning, SHAP, extra attack classes, web dashboard, cross-scenario validation). The 21-day plan (`MANET_IDS_BTech_Execution_Guide.md:276-298`) has a dashboard on Day 19 and a full report on Day 20 — after the core chain was supposed to work on Day 18.
- **Files:** `AGENTS.md:155-159`, `MANET_IDS_BTech_Execution_Guide.md:55`, `MANET_IDS_BTech_Execution_Guide.md:59`, `MANET_IDS_BTech_Execution_Guide.md:68-75`, `MANET_IDS_BTech_Execution_Guide.md:276-298`
- **Impact:** The failure mode is not "too much code" — it is **"the baseline is never frozen, so there is nothing to compare against"**. Rule 7 (`AGENTS.md:150`) requires an IDS-off AODV baseline; a project that has spent Days 11-16 tuning a fifth classifier has no stable baseline, no frozen data version, and no time to regenerate. The report then contains impressive tables that trace to nothing ([C-06]).
- **Fix approach:** Adopt the mentor checkpoint rule literally (`AGENTS.md:158-159`, `MANET_IDS_BTech_Execution_Guide.md:387`): at the end of each week, tag a frozen working version (`git tag -a week1 -m "Week 1: simulator + baseline metrics"`) and record the tag in `docs/experiment_log.md`. Attack order is fixed: **Blackhole first, then Grayhole, then flooding/DoS only if the first two are stable** (`AGENTS.md:156-157`). Any stretch feature that blocks a gate gets deleted, not deferred — the rule is "remove the advanced feature and preserve the reproducible baseline" (`MANET_IDS_BTech_Execution_Guide.md:387`).

### [C-29] Knowledge concentration in a four-person team on a 21-day plan

- **Class:** [RISK] · **Severity:** Medium
- **Issue:** `MANET_IDS_BTech_Execution_Guide.md:309` states plainly: "Every member should understand the complete pipeline. **Do not create a situation where only one student can run the project.**" The role split at `MANET_IDS_BTech_Execution_Guide.md:302-307` divides the system into four vertical slices (Network / Data-ML / IDS / UI-Docs), and the plan assumes 3-4 people working consistently (`MANET_IDS_BTech_Execution_Guide.md:274`).
- **Files:** `MANET_IDS_BTech_Execution_Guide.md:274`, `MANET_IDS_BTech_Execution_Guide.md:302-309`
- **Impact:** The pipeline is strictly sequential (simulator → traces → features → dataset → ML → response → re-evaluation). If member 1 owns the simulator and is unavailable, members 2-4 cannot regenerate data, and every saved number becomes unfalsifiable. The guide's own failure point "Unverified numbers" (`MANET_IDS_BTech_Execution_Guide.md:320`) is what this produces. The "Do Not Overbuild" risk in [C-16] and this risk compound: scope pressure plus a single owner means the fallback is "cut features" rather than "cut weeks".
- **Fix approach:** Make the run entry points scriptable and identical for everyone: one command regenerates any dataset and one command re-evaluates any model. Require that the Day-1 scope document (`MANET_IDS_BTech_Execution_Guide.md:278`) name, per member, which *upstream* artifact they consume and which *downstream* artifact they must hand over in a format the next member can consume without a meeting. A `docs/README-runbook.md` that a non-author can follow top to bottom is the deliverable that discharges this concern.

---

## Known Bugs

> There is no source code, so there are no runtime bugs. The items below are **defects in the files that exist today** — verified by inspection and, where noted, by executing the tool against the actual repo.

### [C-06] Per-run records are gitignored, so rule 8 cannot be satisfied inside the repo

- **Class:** [CURRENT] · **Severity:** Critical
- **Issue:** `.gitignore:5-7` reads:
  ```gitignore
  # Experiment output: keep plots, drop bulk per-run records
  results/*
  !results/plots/
  ```
  The `results/*` pattern ignores every direct child of `results/`, and the only un-ignore is `results/plots/`. The per-run records — the artefact that makes a number traceable — therefore fall inside the ignore. **Verified empirically** in a scratch repo with this exact `.gitignore`:
  ```
  === STAGED ===            === IGNORED ===
  A  results/plots/pdr.png  !! data/
  A  ml/model.joblib        !! results/keepme.txt
  A  docs/log.md            !! results/runs/
  A  scenarios/e1.json      !! traces/
  ```
  `results/runs/` and any top-level file under `results/` are untracked and unbacked. This directly contradicts `AGENTS.md:151` (rule 8: "Every number in the report/README must trace to a saved experiment run + its config"), `AGENTS.md:129-130` ("Every result must be traceable back to a saved run") and `MANET_IDS_BTech_Execution_Guide.md:320` ("Every number in the report should trace back to a saved experiment").
- **Files:** `.gitignore:5-7`, `AGENTS.md:126-130`, `AGENTS.md:151`, `MANET_IDS_BTech_Execution_Guide.md:320`
- **Impact:** The project's headline integrity claim is unbacked by version control. If a run's record lives only in `results/`, it exists on one laptop, in one directory, until someone deletes it or reformats. On Day 21 ("Re-run key experiments, verify every reported number", `MANET_IDS_BTech_Execution_Guide.md:298`) there is no way to prove a number came from the run that produced it. The guide's failure point "**Unverified numbers**" is guaranteed to fire.
- **Fix approach:** Un-ignore the small, high-value subset of `results/` and make it the traceability backbone. Change `.gitignore:5-7` to:
  ```gitignore
  # Experiment output: keep plots and per-run records, drop bulk artefacts
  results/*
  !results/plots/
  !results/runs/
  !results/runs/**
  ```
  Then define exactly what a run record contains (see [C-25]) and commit one per experiment. Everything else under `results/` (raw metric dumps, large CSVs) stays ignored. A `results/plots/` directory needs a `.gitkeep` because the directory itself is currently created only by the ignore negation — a fresh clone has no `results/` at all.

### [C-18] The `data/` ignore rule cancels the "keep samples" policy

- **Class:** [CURRENT] · **Severity:** Medium
- **Issue:** `AGENTS.md:118` specifies `data/` as "built datasets (gitignored, keep samples)" and `AGENTS.md:129` says to "Commit code, scenario configs, **small sample data**, plots, and docs"; `MANET_IDS_BTech_Execution_Guide.md:175` says the same ("Keep code, configuration, small sample data and documentation under version control"). But `.gitignore:3` is a bare `data/`, which ignores the directory wholesale, and there is no negation for a samples subdirectory. **Verified:** `git check-ignore -v --no-index data/samples/sample.csv` → `.gitignore:3:data/ data/samples/sample.csv`. The file is ignored; it can only be added with `git add -f`, which is exactly the kind of friction that leads to "we'll just paste the CSV into the report".
- **Files:** `.gitignore:3`, `AGENTS.md:118`, `AGENTS.md:129`, `MANET_IDS_BTech_Execution_Guide.md:175`, `MANET_IDS_BTech_Execution_Guide.md:328`
- **Impact:** The deliverable "Clean datasets or dataset-generation scripts" (`MANET_IDS_BTech_Execution_Guide.md:328`) is only half-satisfiable. A reviewer who clones the repo cannot see a single row of the dataset the report is about, and the schema (guide:104-117) has to be taken on trust. This also removes the cheapest defence against [C-02]: a reviewer cannot eyeball a committed sample for leakage columns.
- **Fix approach:** Amend `.gitignore:3` to:
  ```gitignore
  data/
  !data/samples/
  !data/samples/**
  ```
  Commit a **small, fixed, hand-checked sample** at `data/samples/` — e.g. `feature_table_sample.csv` with ~50 rows covering all four label values, plus a `data/samples/README.md` documenting the schema, the window length and the provenance of each column. This sample doubles as the regression fixture for [C-04] and the leak-audit artefact for [C-02].

### [C-25] `.gitignore` claims "reproducible from a seed", which is not true

- **Class:** [CURRENT] · **Severity:** Medium
- **Issue:** `.gitignore:1` states: "Generated simulation output — reproducible from a seed, never commit (guide §4)". A seed is **not** sufficient to reproduce a run. Reproduction requires at minimum: the seed, the scenario JSON (node count, area, mobility model and speed, traffic flows, rate, payload size, attack type, attacker node id), the simulator code version, the Python and library versions, and the platform. `AGENTS.md:72-74` states the real requirement — "every run is driven by an explicit integer seed. Same seed ⇒ identical traces" — which is a statement about *re-running in the same code*, not about *regenerating later*.
- **Files:** `.gitignore:1`, `AGENTS.md:72-74`, `AGENTS.md:84-85`, `AGENTS.md:129-130`
- **Impact:** The comment encodes a false belief into the one file every contributor reads. A teammate who ignores `traces/` on the reasonable grounds that "it's reproducible from a seed" may delete the only copy of a run. It also masks the real requirement: the *scenario file* is the true unit of reproducibility, and it must be committed (`AGENTS.md:129`).
- **Fix approach:** Correct the comment to "Generated simulation output — regenerate with `simulator/run_scenario.py --scenario <json> --seed <int>`; the scenario JSON and the code version are the reproducibility unit" and make the run record carry the full tuple (see [C-25] fix below / [C-26]): `git SHA`, scenario path + scenario hash, seed, library versions, timestamp, metrics. The manifest then *proves* reproducibility rather than asserting it.

### [C-31] `.gitignore` does not cover planning artifacts, logs, or model binaries

- **Class:** [CURRENT] · **Severity:** Low
- **Issue:** The ignore file covers `traces/`, `data/`, `results/*` (except `results/plots/`), Python caches, `.venv/`, `venv/`, `.pytest_cache/`, `.ipynb_checkpoints/`, and OS/editor noise (`.gitignore:1-22`). It does **not** cover: `.planning/` (verified — `.planning/codebase/STACK.md` is not ignored), `*.log`, `ml/*.joblib` / `ml/*.pkl` (verified — `ml/model.joblib` is staged by `git add -A`), `*.html` report exports, or `*.png` outside `results/plots/`.
- **Files:** `.gitignore:9-22`
- **Impact:** Two effects. (a) `.planning/` and any `*.log` will be committed whether intended or not, bloating history with regenerable noise. (b) A model binary is committed **by default** with no decision having been made — see [C-28] for why that is a problem, and note that a future multi-megabyte `results/plots/` PNG is likewise unbounded.
- **Fix approach:** Add an explicit, commented block:
  ```gitignore
  # Planning/tooling scratch — not part of the project record
  *.log
  # Model artefacts are committed deliberately (see docs/decisions.md) — see C-28
  ```
  Decide the `.planning/` policy explicitly (commit it — it is the project record — but keep any future run-cache subdirectory ignored). Add a size check before committing figures: any single file over ~5 MB should be regenerated at a lower DPI rather than committed.

---

## Security Considerations

> This project holds **no secrets, no credentials, no user data, and no network services** (verified: no `.env`, no key material, no server code). The security surface is therefore not "an attacker can read my API key" — it is the **experimental security of the evaluation**: whether the reported detection performance is real, and whether the claims in the report survive an examiner's probing. That is the dominant risk class in this project, and it is what [C-01], [C-02], [C-08], [C-09], [C-13] and [C-17] cover.

### [C-02] Leakage features make detection trivial and the result worthless

- **Class:** [RISK] · **Severity:** Critical
- **Issue:** `AGENTS.md:145-146` (rule 5): "**No leakage features.** Do not add a feature that directly reveals attacker identity or the attack label (e.g. a `is_attacker` column, or any field derived from the attack config rather than from observed traffic)." `MANET_IDS_BTech_Execution_Guide.md:315` repeats it, and it is a named viva question: "How did you avoid data leakage?" (`MANET_IDS_BTech_Execution_Guide.md:370`). The spec's own feature table (`MANET_IDS_BTech_Execution_Guide.md:104-117`) mixes a `label` column into the same table as the features — an easy place for a label or a config-derived column to slide into the design matrix by accident.
- **Files:** `AGENTS.md:84-87`, `AGENTS.md:145-146`, `MANET_IDS_BTech_Execution_Guide.md:104-117`, `MANET_IDS_BTech_Execution_Guide.md:315`, `MANET_IDS_BTech_Execution_Guide.md:370`
- **Impact:** A leaky model reaches 0.99 accuracy and tells the examiner nothing. The failure is silent and self-flattering: every chart looks great, and the defence question "How did you avoid data leakage?" has no answer. The specific leaks available in this design are: (i) an `is_attacker` / `attacker_id` column written next to the label; (ii) a `dropped_by` field from the trace (`AGENTS.md:81-82` lists `dropped_by` as a trace column) being read into a feature — that column *is* the ground truth; (iii) a per-run count of drops that the attacker itself produced, rather than a ratio; (iv) the `label` column itself entering `X`.
- **Fix approach:** Make the leak structurally impossible rather than a matter of care:
  1. `feature_extraction/` must expose a **single, explicit feature allow-list** — a module-level constant listing the exact column names that may enter `X`, derived from the spec's schema minus `label`. Everything else is dropped by default, so a new column requires an explicit act.
  2. The label is joined **from the scenario config** onto a separately-constructed feature frame, never carried through the trace parser. The trace parser (`feature_extraction/`) must not be able to see the attack config at all — the dependency direction is `scenario.json → labels`, `traces → features`, and the two meet only at the join.
  3. `dropped_by` is a *trace* column and must never be a *feature*; it is a diagnostic for the attack-validation report (`MANET_IDS_BTech_Execution_Guide.md:203-204`), not a detector input. Ban it in the allow-list.
  4. Add a **leak audit** to the test suite ([C-04]): assert that the design matrix column set equals the allow-list, and assert that no feature column has near-perfect mutual information with the label (e.g. a single feature whose AUC is > 0.95 in isolation is a leak smell, not a success).
  5. State the provenance of every column in `docs/` — a table with columns `feature | source | observed-traffic? | can it reveal the attacker?` — and reuse it verbatim in the report's methodology chapter.

### [C-13] A directly-readable attack flag makes detection trivial

- **Class:** [RISK] · **Severity:** High
- **Issue:** `AGENTS.md:86-87` states the invariant: "Keep the attack's effect in the **network behavior** (drops, PDR), not in a flag the metrics can read directly. Otherwise detection becomes trivial and the result is worthless." This is the *inverse* of [C-02] and is easy to violate accidentally when the simulator is refactored: a node attribute like `is_attacker` on the AODV node object (`AGENTS.md:61-63` describes attacks as "node behavior flags on the AODV node") is exactly the kind of field a feature extractor can reach for.
- **Files:** `AGENTS.md:61-63`, `AGENTS.md:86-87`, `MANET_IDS_BTech_Execution_Guide.md:96-100`
- **Impact:** If `is_attacker` is readable anywhere a feature can reach, the detector "achieves" perfect accuracy and the whole project has no value — the examiner's question "How does a blackhole attack affect AODV?" (`MANET_IDS_BTech_Execution_Guide.md:367`) exposes that the model learned nothing about AODV.
- **Fix approach:** Keep the attack state physically separate from the node's observable state. Concretely: the attacker node's behaviour is implemented as a **behaviour object** injected into the AODV node (`AGENTS.md:61-63`, `AGENTS.md:67-69`), and the AODV node holds no `is_attacker` attribute. The only channel by which an attack influences the network is the protocol action it takes (a lying RREP, a silent drop) — which is precisely what produces drops and PDR loss. Add a test asserting that the string `is_attacker` (and any attacker-identity field) does not appear in the feature frame's columns, the trace CSV header, or the dataset CSV header.

### [C-17] Overclaiming: what the model detects

- **Class:** [RISK] · **Severity:** Medium
- **Issue:** `AGENTS.md:160-161` (rule 11): "Do not claim the model 'detects all MANET attacks.' State exactly which attacks, traffic conditions, mobility models, and simulator settings were evaluated." `MANET_IDS_BTech_Execution_Guide.md:79` states the same academic rule, and `MANET_IDS_BTech_Execution_Guide.md:384-385` (the "Final note") makes "realistic attack behavior, leakage-free evaluation" a requirement of the strongest version of the project.
- **Files:** `AGENTS.md:160-161`, `MANET_IDS_BTech_Execution_Guide.md:79`, `MANET_IDS_BTech_Execution_Guide.md:261`, `MANET_IDS_BTech_Execution_Guide.md:384-385`
- **Impact:** The most likely viva failure and the easiest to prevent. With only Blackhole and Grayhole, on one mobility model (Random Waypoint, `AGENTS.md:56`), on one simulator, the defensible claim is narrow — and the narrow claim is the credible one. Overclaiming on a narrow result is treated as unsound work; under-claiming on a narrow but rigorous result is treated as an honest engineer.
- **Fix approach:** Write the scope sentence **before** the report and put it in the README, the report's introduction, and the presentation's first slide, verbatim. It must enumerate: attack classes (Blackhole, Grayhole), traffic conditions (node counts, flow rates, payload sizes), mobility model and speeds, area size, simulation duration, and the fact that the simulator is the in-repo pure-Python model rather than NS-3 (see [C-23]). Keep a `docs/scope.md` as the single source for that sentence.

### [C-28] A committed `.joblib` model is version-fragile and an arbitrary-code-execution surface

- **Class:** [RISK] · **Severity:** Medium
- **Issue:** `.gitignore` does not ignore `ml/*.joblib`, and `git add -A` **stages it** (verified). The guide requires saving "the final model and preprocessing pipeline" (`MANET_IDS_BTech_Execution_Guide.md:127`) and lists "Trained ML model and preprocessing pipeline" as a deliverable (`MANET_IDS_BTech_Execution_Guide.md:329`). Two problems follow.
  1. **Version fragility.** A `joblib`/`pickle` artefact is tied to the exact scikit-learn and Python versions that produced it. With scikit-learn at 1.8.0 (`AGENTS.md:95`) — newer than most pins in the wild — a model saved today can fail to load on a machine with a different scikit-learn, and it cannot be re-created without the exact data, which is gitignored. This is [C-12] and [C-06] biting at once.
  2. **Trust boundary.** `joblib.load` (and `pickle.load` underneath it) executes arbitrary code in the loading process. A `.joblib` fetched from a remote — e.g. a GitHub release asset, a colleague's drive, or a "model download" link added during the optional-dashboard phase — is remote code execution, not data.
- **Files:** `.gitignore:9-16` (no model rule), `MANET_IDS_BTech_Execution_Guide.md:127`, `MANET_IDS_BTech_Execution_Guide.md:329`
- **Impact:** A committed model that cannot be loaded in the defence environment, or a model file that is opaque to a reviewer, weakens the reproducibility claim at the exact moment it is being tested. The deserialization risk is low-probability today (no remote, no dashboard) but becomes live the moment a remote is added ([C-10]) or the dashboard ships.
- **Fix approach:**
  1. Commit the **model, the pipeline and the training script** together, and record the exact library versions used to train it inside the artefact's metadata (e.g. a sidecar `ml/model_card.json` with `sklearn_version`, `python_version`, `train_date`, `train_scenario_set`, `metrics`). A model without a card is not a deliverable.
  2. Make the artefact **regenerable**: the training entry point takes the scenario list + seed set and rebuilds the model in one command. That is what makes the gitignored `data/` acceptable ([C-18]).
  3. Never `joblib.load` a file from outside the repo tree. If a dashboard ever fetches a model, fetch it into a local cache directory and treat it as untrusted — or skip the feature; the model is small and can be loaded from the repo path.
  4. Decide explicitly in `docs/decisions.md` whether the binary is committed. If committed, record the scikit-learn version alongside it; if not, commit only the card and the training script.

### [C-14b] Forward-looking attack-surface guidance (no current vulnerability)

- **Class:** [RISK] · **Severity:** Low (forward-looking)
- **Issue:** There is no security vulnerability to fix today because there is no code. The following are the attack surfaces a future phase will create, listed so they are designed out rather than audited in later.
  - **Optional dashboard** (`dashboard/`, `AGENTS.md:122`): bind to `127.0.0.1` only, never `0.0.0.0`. No user accounts — there are no users. If it displays a file path from a request parameter, resolve it under a fixed root and reject anything escaping it. No `eval`, no `subprocess` on request data. The dashboard is optional and last; if its threat model is not understood, do not build it.
  - **Model loading**: as above — `joblib.load` is deserialization-as-code-execution.
  - **Scenario JSON** is an input file and will eventually accept user-supplied values: it should be parsed with `json.load` into typed dataclasses with validation (`AGENTS.md:52` names `dataclasses` for exactly this), not passed to `eval`/`pickle`.
  - **Traces and datasets** are ignored precisely so that large generated artefacts are never pushed — that is a deliberate hygiene measure, keep it (`AGENTS.md:128`).
- **Files:** `AGENTS.md:118-123`, `MANET_IDS_BTech_Execution_Guide.md:147`, `MANET_IDS_BTech_Execution_Guide.md:332`
- **Impact:** A student demo on a lab machine with the dashboard on `0.0.0.0` is an open service on the campus network. Low severity in context, but it is the only realistic exposure this project will ever have.
- **Fix approach:** Add the rules to `AGENTS.md` as a short "Security" section at the same time the dashboard is scoped (not now), so the constraint is written before the code, per the project's own "write the constraint, then the code" discipline.

---

## Performance Bottlenecks

### [C-22] Per-packet Python overhead is the performance cliff

- **Class:** [RISK] · **Severity:** Medium
- **Issue:** `AGENTS.md:75-80` records the measured baseline: "50 nodes / 8 flows / 10 pps / 300 s simulated run with a blackhole attacker → **0.83 s wall**, ~70k events/sec. A 30–60 s run takes well under a second, so the full experiment matrix is minutes of compute. **If a run *is* slow, per-packet Python overhead is the culprit** — profile before increasing node count." The guide's own working configuration is much smaller (`MANET_IDS_BTech_Execution_Guide.md:181-186`: 20-30 nodes, 30-60 s runs), so the spec's measured headroom is roughly an order of magnitude above the working point.
- **Files:** `AGENTS.md:75-80`, `MANET_IDS_BTech_Execution_Guide.md:181-186`, `MANET_IDS_BTech_Execution_Guide.md:186`
- **Impact:** The realistic failure is not "the matrix takes too long". It is **"a run is slow, so someone increases the node count or rewrites the hot loop in a way that breaks determinism"** — which converts a performance nuisance into a correctness regression ([C-07]). The spec's instruction to profile first is precisely the guard against that. A second, subtler impact: a per-packet loop that is O(nodes) per event (e.g. re-scanning all nodes to find neighbours instead of maintaining a neighbour set via NetworkX) turns a 0.83 s run into minutes and makes the *whole* experiment matrix the bottleneck, which is exactly the pressure that leads to cutting the generalisation experiment (E8) — the one that proves the model is not overfit.
- **Fix approach:**
  1. Accept `simulator/radio.py` maintaining neighbour sets incrementally (`AGENTS.md:57`: "radio.py — transmission range / link availability; drives `neighbor_count`") rather than recomputing a graph per event.
  2. When a run is slow, profile (`python -m cProfile -o run.prof simulator/run_scenario.py --scenario ... --seed ...`) **before** changing anything. Do not reach for Cython/Numba — they are out of scope under "Python only" (`AGENTS.md:25`) and would break the Windows-native, no-compiler constraint (`AGENTS.md:27`).
  3. Keep the wall-clock budget in the acceptance script: the full E1-E8 matrix should complete in minutes. If it takes hours, that is a bug, not a capacity limit.
  4. Watch the **trace volume** dimension of the cost, not just CPU: at ~58k events for the 300 s benchmark run and roughly 60 bytes per CSV row, one run is ~3.5 MB of trace CSV. The full matrix at 50+ runs is ~150-200 MB — which is fine on disk but is exactly the quantity `traces/` is ignored to keep out of git (`AGENTS.md:128`). See [C-06] for where the *small* records go instead.

### [C-32] `SVC` does not scale to the generated dataset size

- **Class:** [RISK] · **Severity:** Medium
- **Issue:** The specified classifier list is "Decision Tree → Random Forest → SVM or XGBoost" (`MANET_IDS_BTech_Execution_Guide.md:214-217`, Step 5 of the guide). The dataset size is set by the simulation: one row per (node, window). At 50 nodes and a 1 s window over a 300 s run that is ~15,000 rows *per run*; across a multi-seed, multi-configuration dataset (E1-E8, `MANET_IDS_BTech_Execution_Guide.md:244-253`) it is realistically 10^5-10^6 rows. `sklearn.svm.SVC` with the default RBF kernel has training cost that grows super-linearly in the number of rows; it will be the one classifier in the comparison that appears to "not work" for reasons that have nothing to do with the security question.
- **Files:** `MANET_IDS_BTech_Execution_Guide.md:214-218`, `MANET_IDS_BTech_Execution_Guide.md:244-253`
- **Impact:** Two downstream harms. (a) A day is lost to a scalability surprise during the Day-12 model comparison (`MANET_IDS_BTech_Execution_Guide.md:289`). (b) Worse: an unfinished SVM in the comparison table can be misread as "SVM performs poorly", which is a false claim in the report.
- **Fix approach:** Keep the specified model ladder but bound the SVM: use `sklearn.svm.SVC` on a stratified subsample, or `sklearn.svm.LinearSVC` / `sklearn.linear_model.SGDClassifier` on the full set. Whichever is used, state the subsample size in the report and report the metric on the **same test split** as the other classifiers (`MANET_IDS_BTech_Execution_Guide.md:217`: "Use the same train/test protocol for fair comparison"). If a classifier cannot be evaluated at all, say so in the table rather than omitting it.

---

## Fragile Areas

### [C-04] No test harness: the baseline can drift silently

- **Class:** [GAP] · **Severity:** Critical
- **Issue:** There is no `pytest` dependency, no `tests/` directory, and no test of any kind. `.gitignore:15` ignores `.pytest_cache/`, which implies pytest is the expected runner, and pytest 9.0.2 is installed in the environment — but nothing in the repo uses it. The project's entire thesis is **measurement integrity**: it asserts that a measurement of a simulated network is trustworthy. There is currently no mechanism that could detect a change in the simulator that silently moves the baseline.
- **Files:** `.gitignore:15`, `AGENTS.md:136` (gate 1), `AGENTS.md:171-177` (known failure points), `MANET_IDS_BTech_Execution_Guide.md:182`
- **Impact:** This is the highest-leverage gap in the repository, because it silently invalidates every other guarantee. Concretely:
  - A refactor of `simulator/aodv.py` that changes the RREP hop-count computation shifts the baseline PDR. Every downstream dataset, every trained model and every reported number is now measuring a different network. Nothing detects this. The guide's setup checklist requires validating the simulator against expected AODV behaviour — "PDR falls with distance and load, hop count grows with distance, routing overhead is non-zero" (`MANET_IDS_BTech_Execution_Guide.md:154-156`) — but that validation is currently a one-time manual action with no re-run mechanism.
  - `AGENTS.md:175-176` names "Results change between identical runs" as a known failure point. Without a determinism test, that failure is discovered by an examiner, not by the team.
  - The 21-day plan has no test task at all. The regression suite has to be *added* to the plan, not discovered at Day 21.
- **Fix approach:** Create `tests/` at the repo root (or inside each owning package) and make it a Day-2 deliverable alongside the simulator core, not a Day-20 task. Minimum suite, in priority order:
  1. **`test_determinism.py`** — run the same scenario and seed twice and assert the trace files are byte-identical; run two *different* seeds and assert they differ. This is the single highest-value test in the project ([C-07]).
  2. **`test_baseline_invariants.py`** — assert the qualitative relationships the guide names (`MANET_IDS_BTech_Execution_Guide.md:154-156`): PDR decreases with transmission range loss, hop count increases with source-destination distance, routing overhead is non-zero, and PDR for the clean scenario falls inside a sane band (e.g. 0.5-1.0 at 20-30 nodes). These are regression locks, not tuning targets.
  3. **`test_attack_effect.py`** — assert the blackhole scenario's PDR is measurably below the clean scenario's, and that the difference exceeds a stated threshold ([C-03]). This is the automated form of gate 2 (`AGENTS.md:137`).
  4. **`test_no_leakage.py`** — assert the feature design matrix columns equal the allow-list, that no column name matches a forbidden pattern (`is_attacker`, `attacker`, `label`, `dropped_by`), and that no single feature is trivially separating ([C-02]).
  5. **`test_split_integrity.py`** — assert the train/test split is grouped by run id and that no run id appears in both sides ([C-01]).
  6. **`test_window_features.py`** — assert feature-window aggregation matches a hand-computed expectation on a tiny synthetic trace.
  Add `pytest==9.0.2` to `requirements.txt` ([C-12]) and a `python -m pytest -q` invocation to the runbook.

### [C-07] Non-determinism makes the whole experiment matrix unreproducible

- **Class:** [RISK] · **Severity:** High
- **Issue:** `AGENTS.md:72-74`: "**Determinism:** every run is driven by an explicit integer seed. Same seed ⇒ identical traces." `AGENTS.md:175-176` names the failure explicitly: "Results change between identical runs → missing explicit seed / **non-deterministic iteration order over sets**." Two specific traps exist in this stack:
  - **SimPy 4.1.2 has no seeding API.** Verified on the installed version: `simpy.Environment.__init__` accepts only `initial_time`; `env.random` does not exist; `simpy.seed` does not exist. The SimPy 3.x API is gone. Determinism must come from an explicit `random.Random(seed)` threaded into every stochastic component.
  - **Set iteration order.** `networkx` graph adjacency sets and Python `set` iteration order depend on hash randomisation; on CPython 3.11, `PYTHONHASHSEED` is not fixed by default, so the same seed can produce a different neighbour-visit order between two runs. Any loop over a set of neighbours is a nondeterminism source.
- **Files:** `AGENTS.md:72-74`, `AGENTS.md:49-50`, `AGENTS.md:175-176`, `AGENTS.md:65`
- **Impact:** Determinism is the precondition for every other guarantee in the project. Without it, (a) the "multiple seeds" dimension of the experiment matrix is not a controlled variable, (b) the IDS-off vs IDS-on comparison ([C-05]) cannot be attributed to the IDS, (c) the generality test (E8) cannot be separated from noise, and (d) rule 8's traceability collapses. It also breaks the mentor checkpoint rule: you cannot freeze a working version if re-running it produces different numbers.
- **Fix approach:**
  1. `simulator/run_scenario.py` creates exactly one `rng = random.Random(seed)` and passes it explicitly into mobility, radio, traffic and attack components. Never use the `random` module's global functions (`random.random()`, `random.shuffle()`) inside the simulator — they are not seeded by `--seed`.
  2. Never iterate a `set` where order matters. Use `sorted(neighbours)` (or `sorted(neighbours, key=...)` for a stable tie-break) at every traversal point. A mechanical check: `grep -rn "for .* in .*set(" simulator/` and `grep -rn "for .* in .*\.neighbors" simulator/` should return only sorted iterations.
  3. Seed from the CLI only (`--seed <int>`, `AGENTS.md:65`) and record it in the run record. If a scenario JSON also carries a seed, the CLI value must win, and the effective seed must be written into the run record so there is no ambiguity about which one ran.
  4. Add the `test_determinism.py` byte-identity test from [C-04] and run it in every session. Treat a determinism failure as a build break, not a flaky test.

### [C-03] Attack that does not change measurable behaviour makes everything downstream worthless

- **Class:** [RISK] · **Severity:** Critical
- **Issue:** The attack must demonstrably change measurable network behaviour *before* any detector is trained. `AGENTS.md:137` (gate 2): "No detector until the attack demonstrably changes measurable network behavior." `MANET_IDS_BTech_Execution_Guide.md:203`: "You must be able to demonstrate that the attack changes measurable network behavior before attempting detection." `MANET_IDS_BTech_Execution_Guide.md:318` names it a failure point: "Unclear attack implementation: Demonstrate the attack independently before training the detector."
  The specification leaves the attack almost entirely undefined, which is where the risk lives. The whole blackhole is one sentence — "Select a malicious node. Make it advertise attractive routes while failing to forward data as expected" (`MANET_IDS_BTech_Execution_Guide.md:199-201`) — and `AGENTS.md:61-63` compresses both attacks to "a lying reply (blackhole) and probabilistic drop (grayhole)". Undefined: *what makes a reply attractive* (a fresh sequence number? a low hop count? a shorter route?), *what "failing to forward" means* (silent drop? forward-then-discard? decrement TTL then discard?), and *how long the lie persists* (until the next RREQ? until route expiry? permanently?). Every one of those is a chance to implement an attack that is either **invisible** (no measurable effect) or **trivially visible** (a flag the metrics can read — see [C-13]).
- **Files:** `AGENTS.md:61-63`, `AGENTS.md:86-87`, `AGENTS.md:137`, `AGENTS.md:173-174`, `MANET_IDS_BTech_Execution_Guide.md:96-100`, `MANET_IDS_BTech_Execution_Guide.md:199-201`, `MANET_IDS_BTech_Execution_Guide.md:203`, `MANET_IDS_BTech_Execution_Guide.md:228`, `MANET_IDS_BTech_Execution_Guide.md:251`, `MANET_IDS_BTech_Execution_Guide.md:318`
- **Diagnostic symptom:** `AGENTS.md:173-174` — "Attack has no measurable effect → the attack implementation is wrong; validate the attack *before* training anything (gate 2)." The concrete test: run the clean and attacked scenarios at the **same seed** and compare. If the attack's PDR delta is not clearly larger than the seed-to-seed variance of the clean baseline, the attack is not working. The opposite symptom is equally diagnostic: if the attacked PDR collapses to near zero, the attack may be over-aggressive (dropping *every* packet through the attacker) rather than a realistic blackhole, and the resulting dataset is unrealistically separable.
- **Impact:** Total and non-recoverable downstream. The dataset, the features, the model, the response, the report and the defence all presuppose a real attack. If the attack is invisible, the "detector" learns noise and the response cannot improve anything; the project then reports "PDR improved 0.0% with the IDS on" and **cannot tell a broken attack from a broken detector**. Worse, an invisible attack produces a *negative* result that looks like a legitimate scientific finding, and it is not discoverable until the Day-21 validation. Gate 2 exists precisely to catch this on Day 6-7 for the cost of one day.
- **Fix approach:** Define the attack numerically *before* writing it, then validate it standalone.
  1. **Write the behaviour down first.** Put the attack's parameters in the scenario JSON — attack type, attacker node id, the fake-RREP fields (sequence number, hop count, lifetime), the data-packet disposition (drop / forward-then-discard), the grayhole drop probability and pattern (periodic vs probabilistic), and the activation window. E6 varies the drop rate (`MANET_IDS_BTech_Execution_Guide.md:251`), so the rate must be a **parameter**, not a constant in code.
  2. **Define the expected effect as a number, in the scenario file.** For example: `expected_pdr_drop_ratio_min: 0.2` — the attacked PDR must be at least 20% below the clean PDR at the same seed. Make it a contract the test asserts, not a comment.
  3. **Validate in isolation on Day 6-7** (`MANET_IDS_BTech_Execution_Guide.md:283-284`), before any ML: run clean vs attacked at identical seed, produce the PDR / throughput / delay / loss / overhead comparison, and save it as the "attack validation report" under `docs/`. This is the gate-2 artefact.
  4. **Automate the check.** `tests/test_attack_effect.py` asserts the margin, so a later refactor of `simulator/aodv.py` cannot silently remove the attack's effect.
  5. **Confirm the effect is behavioural, not nominal.** The attack must change drops and PDR and nothing else a feature can read directly ([C-13]).
  6. **If the effect is too weak, fix the attack — not the features.** A missing signal cannot be manufactured by adding columns; a dataset built on a broken attack is the worst artefact in this project, because it looks like data.
  7. Check both directions: too weak (no effect) and too strong (near-total blackhole, unrealistically separable). A realistic blackhole is one that attracts *some* traffic and drops it, producing a degraded-but-not-dead network.

### [C-08] Label integrity and the undefined observation window

- **Class:** [RISK] · **Severity:** High
- **Issue:** `AGENTS.md:84-85`: "**Labels come from the scenario config** (which node is the attacker, which attack), **never from the trace.** This is what keeps the dataset ground truth honest." `MANET_IDS_BTech_Execution_Guide.md:210` says the same ("Label observations using the known simulation ground truth") and `MANET_IDS_BTech_Execution_Guide.md:368` makes it a viva question ("How did you generate the ground-truth labels?"). Two parameters are left undefined in the spec and both materially change the dataset:
  - **The observation window length.** `MANET_IDS_BTech_Execution_Guide.md:209` says "Extract features in **fixed time windows**" but no duration is given anywhere in either document. The window length sets the number of rows, the class balance, and how much context the model has.
  - **The label space.** `MANET_IDS_BTech_Execution_Guide.md:117` lists `label` as "Normal / Blackhole / Grayhole / other", but Step 7 (`MANET_IDS_BTech_Execution_Guide.md:230-231`) contemplates a blackhole-only binary model *and* a multi-class model. Which label space a given dataset has must be explicit.
- **Files:** `AGENTS.md:84-85`, `MANET_IDS_BTech_Execution_Guide.md:104-117`, `MANET_IDS_BTech_Execution_Guide.md:209-210`, `MANET_IDS_BTech_Execution_Guide.md:230-231`, `MANET_IDS_BTech_Execution_Guide.md:368`
- **Impact:** If labels are ever derived from the trace — say, "this node dropped more than X" — the dataset is circular: the model learns the labelling function, and the reported performance is a measurement of the labelling heuristic, not of attack detection. The `label` column's presence in the same table as the features (`MANET_IDS_BTech_Execution_Guide.md:104-117`) makes the mistake easy. The undefined window length means two team members can build "the same" dataset with completely different row counts and class ratios, and the Day-12 model comparison becomes an accidental comparison of two different datasets rather than of three classifiers.
- **Fix approach:**
  1. **Labels are an input.** The scenario config is the single source of ground truth. In code, the label is attached by joining the scenario's `(attacker_node_id, attack_type)` onto the feature frame *by node id and time window*, and only for windows in which the attacker was active. Never compute a label from a trace column.
  2. **Fix the window length now, in the scenario schema, and record the decision.** A defensible starting point is 1 s windows for 30-60 s runs (`MANET_IDS_BTech_Execution_Guide.md:186`): it gives enough windows per run for a usable dataset while keeping each window's counts meaningful. Put `window_seconds` in the scenario JSON so it is a recorded experimental variable, and state the chosen value in the report.
  3. **State the label space explicitly** per dataset in its header or its companion record: `label ∈ {normal, blackhole}` for the binary dataset, `∈ {normal, blackhole, grayhole}` for the multi-class one. Do not leave "other" as a live value in a reported dataset.
  4. Document the label rule in `docs/` with the exact text that will answer the viva question.

### [C-20] The threshold and the response loop can cascade into network collapse

- **Class:** [RISK] · **Severity:** Medium
- **Issue:** Module E (`MANET_IDS_BTech_Execution_Guide.md:130-133`) specifies: "Generate an alert when confidence exceeds a predefined threshold. Assign the node a malicious/low-trust state. Prevent or discourage routing through that node." Two failure modes are not addressed anywhere:
  - **Threshold selection.** "Predefined" must mean *chosen without touching the test set*. A threshold picked by maximising F1 on the test split is a form of leakage, and a threshold picked at 0.5 on an imbalanced dataset will flag many innocent nodes.
  - **Cascade.** Every isolated node removes routes, which changes the load and the topology of what remains, which changes the features, which can cause the model to flag further nodes — a positive feedback loop. Isolating enough honest nodes in a 20-30 node network can collapse PDR far below the attacked baseline, making the "IDS improves the network" result *worse* than doing nothing.
- **Files:** `MANET_IDS_BTech_Execution_Guide.md:130-133`, `AGENTS.md:150` (rule 7), `MANET_IDS_BTech_Execution_Guide.md:234-238` (Step 8), `MANET_IDS_BTech_Execution_Guide.md:259`
- **Impact:** The IDS response is the project's payoff (`AGENTS.md:165-166`: "identify malicious node → trigger response → show measurable improvement"). A cascade failure turns the payoff into the opposite of the claim, and the guide's minimum metrics include "IDS processing time and additional routing/communication overhead" (`MANET_IDS_BTech_Execution_Guide.md:259`) — i.e. the report is expected to quantify the cost of the response, which is exactly where a cascade shows up.
- **Fix approach:**
  1. Choose the threshold on a **validation split carved out of the training groups only**, then freeze it as a constant in the model card ([C-28]) before any response experiment runs. Report the full precision/recall/F1/FPR at that operating point, and include a small threshold-sweep table so the choice is visible rather than asserted.
  2. Cap the response: isolate at most **one node per detection episode** (the attacker's node id is known in the simulation, so this is easy) and require the confidence to exceed the threshold for **k consecutive windows** before isolating. Both caps bound the blast radius and are cheap to implement in the routing hook.
  3. Report the response's cost honestly: the number of nodes isolated, the number of false isolations, the PDR/throughput/delay/loss/overhead for **both** IDS-off and IDS-on ([C-05]), and the extra routing overhead the response itself introduces.
  4. If the isolated-node count ever exceeds the number of malicious nodes in the scenario, the run is invalid — fail loudly rather than reporting the number.

### [C-24] The response mechanism changes the distribution the detector was trained on

- **Class:** [RISK] · **Severity:** Medium
- **Issue:** The acceptance chain evaluates the IDS *inside the network it is defending* (`MANET_IDS_BTech_Execution_Guide.md:134`: "Re-run the same scenario and quantify whether network performance improves"). But isolation changes the network's traffic pattern: fewer hops, different route selection, different delays, different drop counts. The features of the surviving nodes therefore shift away from the distribution the model was trained on. The isolated attacker also stops attacking, so its own features change.
- **Files:** `MANET_IDS_BTech_Execution_Guide.md:130-133`, `MANET_IDS_BTech_Execution_Guide.md:234-238`, `AGENTS.md:163-166`
- **Impact:** Detection quality measured *after* the response is live is not comparable to detection quality measured on the static dataset, and the two are easily conflated in the report. A detector whose accuracy degrades the moment it is deployed is a real finding, but reporting only the static number hides it.
- **Fix approach:** Keep the two measurements separate and label them: (a) **offline detection quality** on the held-out groups (the confusion matrix and metric set from [C-01]/[C-09]), and (b) **online behaviour** during the IDS-on run (alert rate, false isolations, PDR/throughput recovery). Use the **same frozen model artefact** for both, and do not retrain between them. State in the report that the online figures are measured under a shifted distribution. If the shift is material, that is a documented limitation, not a bug to hide.

### [C-27] The rules live only in prose; nothing in the repo enforces them

- **Class:** [FRAGILE] · **Severity:** Medium
- **Issue:** `AGENTS.md` and `MANET_IDS_BTech_Execution_Guide.md` are the *only* records of the binding rules, and they are read by convention. There is no linter, no pre-commit hook, no CI, no test that asserts a rule, and no checklist file that a reviewer can tick. The rules that matter most — the three gates (`AGENTS.md:134-138`), the five evaluation-integrity rules (`AGENTS.md:142-151`), and the scope discipline (`AGENTS.md:155-161`) — are exactly the ones that are violated by accident, because violating them never raises an error.
- **Files:** `AGENTS.md:132-167`, `MANET_IDS_BTech_Execution_Guide.md:311-320`
- **Impact:** The rules survive only as long as the person who remembers them. Every future contributor — and every future agent — rediscovers the same failure modes from scratch. The document says it plainly: these are "the rules agents break by default" (`AGENTS.md:132`).
- **Fix approach:** Convert the checkable rules into executable checks, in this order of value per unit of effort:
  1. `tests/test_no_leakage.py` and `tests/test_split_integrity.py` make rules 4 and 5 mechanical ([C-02], [C-01]).
  2. A `docs/checklist.md` mapping each rule (1-11) to the artefact that satisfies it, with a file path per rule, is a one-page document and makes the gate reviewable before the defence.
  3. `tests/test_determinism.py` makes the determinism rule mechanical ([C-07]).
  4. Only then consider a pre-commit hook or CI — and per `AGENTS.md:7` / `MANET_IDS_BTech_Execution_Guide.md:145`, that requires a remote first ([C-10]).

### [C-19] The feature schema mixes observed-traffic features with scenario constants

- **Class:** [RISK] · **Severity:** Medium
- **Issue:** The spec's feature table (`MANET_IDS_BTech_Execution_Guide.md:104-117`) mixes two provenance classes without distinguishing them:
  - **Observed-traffic features** — `packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`. These are computed from the trace and are what a detector should use.
  - **Scenario-level constants** — `mobility_speed` (a simulation parameter, identical for every row of a scenario) and `neighbor_count` (a topology quantity fixed by node count and radio range). These are configuration/topology values, not observations of traffic.
- **Files:** `MANET_IDS_BTech_Execution_Guide.md:104-117`, `AGENTS.md:56-57`, `AGENTS.md:145-146`, `MANET_IDS_BTech_Execution_Guide.md:222-224`
- **Impact:** Two distinct harms. (a) **Group fingerprinting:** a scenario-level constant is identical across all rows of a run, so under a random row split ([C-01]) it effectively identifies the run and lets the model memorise "scenario X ⇒ label Y" — a leakage path that opens up precisely because of the split choice. (b) **Generalisation damage:** the guide requires testing on unseen node counts and mobility conditions (`MANET_IDS_BTech_Execution_Guide.md:222-224`, E4/E8 at `MANET_IDS_BTech_Execution_Guide.md:249,253`). `neighbor_count` and `mobility_speed` shift with node count and speed, so a model that leans on them will degrade on the unseen configuration for a reason that has nothing to do with the security question — and the report will attribute the degradation to "generalisation difficulty" rather than to a bad feature choice.
- **Fix approach:** Declare a provenance tag for every column in the feature schema and treat the two classes differently. For each candidate feature, record `source` (trace-derived / config-derived) and `varies_within_run` (yes/no). Then: keep config-derived constants out of the design matrix by default; if `mobility_speed` is retained for a stated reason, state it and report the model's performance **with and without** it so its contribution is visible. A defensible default: the detector uses only trace-derived, node-local, within-run-varying features; `mobility_speed` and `neighbor_count` are retained in the dataset as **group metadata** (used for grouping and stratification) rather than as model inputs. The provenance table is the same artefact that discharges [C-02].

### [C-21] Copying old tutorial snippets breaks silently

- **Class:** [RISK] · **Severity:** Medium
- **Issue:** `AGENTS.md:98-105` names the traps; they are verified live on the installed versions as of 2026-10-22:
  - **pandas 3.0.2, not 2.x.** `pd.DataFrame.applymap` is **removed** (verified: `hasattr(pd.DataFrame, "applymap") == False`); use `DataFrame.map` / `Series.map` (verified present). Copy-on-Write is always on, so in-place mutation followed by a read through another view silently does not propagate. String columns default to the `str` dtype, not `object`, so `dtype="object"` filters and `isinstance` checks written for pandas 2 will not match.
  - **numpy 1.26.4, not 2.x.** numpy 2 migration notes do not apply (`AGENTS.md:103`).
  - **scikit-learn 1.8.0, newer than most tutorial pins** (`AGENTS.md:105`). `OneHotEncoder(sparse=...)` became `sparse_output=...` in 1.2; several 1.x idioms are deprecated. The APIs this project needs (`DecisionTreeClassifier`, `RandomForestClassifier`, `SVC`, `GroupShuffleSplit`, `StratifiedGroupKFold`, `Pipeline`, `StandardScaler`, `classification_report`, `confusion_matrix`) are present and stable in 1.8.0.
- **Files:** `AGENTS.md:98-105`, `AGENTS.md:93-95`, `AGENTS.md:107`
- **Impact:** Every code snippet in a tutorial, a notebook or an LLM-generated answer that assumes pandas 2 / sklearn 1.0 is a latent defect. The pandas Copy-on-Write case is the dangerous one: it does not raise, it produces a **wrong number** — which, in this project, means a wrong *result*. The `applymap` removal at least fails loudly. The other two are silent.
- **Fix approach:** Never paste a snippet without checking it against the installed version. When a snippet fails, check the version before debugging your own logic. Two cheap mechanical guards: (a) add `pandas==3.0.2` and `scikit-learn==1.8.0` to `requirements.txt` so a wrong environment is impossible to create silently ([C-12]); (b) when a DataFrame operation is used, prefer the modern forms on the first attempt — `df.map(...)`, `df = df.assign(...)` — rather than porting a 2.x idiom and then debugging it.

---

## Scaling Limits

### Simulator scale

- **Class:** [FRAGILE] · **Severity:** Medium
- **Current capacity:** Measured and recorded in `AGENTS.md:75-80`: 50 nodes / 8 flows / 10 pps / 300 s simulated with a blackhole attacker completes in **0.83 s wall** at ~70k events/sec. The guide's working configuration (`MANET_IDS_BTech_Execution_Guide.md:181-186`: 20-30 nodes, 30-60 s) sits well inside that. The E1-E8 matrix (`MANET_IDS_BTech_Execution_Guide.md:244-253`) is therefore "minutes of compute" by design.
- **Limit:** There is no capacity limit to hit — the stated limit is a *bug indicator*. `AGENTS.md:78-80` is explicit: "If a run *is* slow, per-packet Python overhead is the culprit — profile before increasing node count." A matrix that takes hours has a bug.
- **Scaling path:** (1) profile before optimising or scaling (`cProfile`, per [C-22]); (2) maintain neighbour sets incrementally rather than recomputing graphs per event (`simulator/radio.py`, `AGENTS.md:57`); (3) keep the trace write out of the hot path where possible — buffer rows and flush per window, since trace I/O is a real per-packet cost; (4) never "solve" slowness with a compiled language — "Python only" (`AGENTS.md:25`) and no compiler toolchain (`AGENTS.md:27`) are hard constraints.
- **Files:** `AGENTS.md:75-80`, `AGENTS.md:25`, `AGENTS.md:27`, `MANET_IDS_BTech_Execution_Guide.md:181-186`

### Disk scale of the generated artefacts

- **Class:** [FRAGILE] · **Severity:** Low
- **Current capacity:** ~58k trace events for the 300 s benchmark run; at roughly 60 bytes per CSV row that is ~3.5 MB per run. A 50-run matrix produces ~150-200 MB of trace CSV plus a much smaller feature dataset. The feature dataset is 10^5-10^6 rows × ~10 columns — comfortably within pandas and sklearn's range (except `SVC`, see [C-30]).
- **Limit:** Disk, not CPU, and only for the ignored artefacts. The real constraint is the *archival* burden: `traces/` and `data/` are ignored (`AGENTS.md:117-118`), so the bulk of the experimental evidence lives outside version control.
- **Scaling path:** Archive to external storage on a documented schedule, and keep the small, committable per-run records in git ([C-06]) so the trace archive is a convenience, not a dependency of traceability. Keep the `results/plots/` output small — regenerate figures rather than committing high-DPI originals.
- **Files:** `AGENTS.md:117-118`, `AGENTS.md:126-130`, `.gitignore:1-7`

---

## Dependencies at Risk

### [C-12] (cross-listed) No manifest and no lockfile

*(Cross-listed from Tech Debt; the dependency-specific risk is stated here.)*

- **Class:** [GAP] · **Severity:** High
- **Risk:** The dependency set is mandated in prose and installed but unrecorded. `simpy 4.1.2` and `networkx 3.6.1` are the simulator's foundation (`AGENTS.md:49-51`); `scikit-learn 1.8.0`, `pandas 3.0.2`, `numpy 1.26.4` are the ML substrate (`AGENTS.md:95`). A future `pip install` resolving different versions changes results with no diff in the code and no error.
- **Impact:** Silent result drift across machines and across time; the "reproducible" claim becomes unreproducible for reasons outside the experiment. Concretely: a future `pandas 4.x` changes `groupby`/null semantics; a different `scikit-learn` changes estimator defaults and can invalidate a saved `.joblib` ([C-28]).
- **Migration plan:** Not a migration — a record. Create `requirements.txt` with exact `==` pins matching the verified environment ([C-12] fix above). Add `pytest==9.0.2` when the suite lands. Do not add a lockfile generator; the "smallest change that solves the problem" rule applies and plain pins are sufficient for a single-machine, single-team project.
- **Files:** `AGENTS.md:93-95`, `AGENTS.md:107`, `MANET_IDS_BTech_Execution_Guide.md:152`, `MANET_IDS_BTech_Execution_Guide.md:279`

### [C-23] Platform lock: no external simulator to cross-check fidelity against

- **Class:** [RISK] · **Severity:** Medium
- **Risk:** The project is deliberately Windows-native with no WSL, no Linux VM, no Docker, no C++ toolchain, and NS-3 is dropped (`AGENTS.md:26-27`, `AGENTS.md:30-31`). The in-repo simulator is therefore a **model** of AODV, not an implementation of RFC 3561 — and there is no NS-3 to differentially test it against. `AGENTS.md:41-45` documents that no installable Windows-native Python AODV simulator exists, so the choice is forced, not merely preferred.
- **Impact:** The simulator's fidelity becomes a **known limitation of the in-repo model** rather than a validated property, and there is no automated way to check it. This is not a bug; it is a claim that must be made honestly in the report's limitations chapter. A grader who knows AODV will ask how closely the model matches the RFC, and "we compared against expected behaviour" (`MANET_IDS_BTech_Execution_Guide.md:154-156`) is the answer available. "We validated it against NS-3" is not available and must not be claimed.
- **Migration plan:** Not a migration. Substitute internal validation:
  1. Implement the guide's named qualitative checks as automated invariants ([C-04] item 2): PDR falls with distance and load, hop count grows with distance, routing overhead is non-zero.
  2. **Document the deviations explicitly** in `docs/` — the honest list of what the model does *not* do: e.g. no MAC-layer CSMA/CA contention, no PHY-layer loss model beyond a range threshold, no packet-size-dependent transmission time, no RERR-triggered route repair subtleties, no sequence-number wraparound, no radio range asymmetry, no per-node energy model. Every deviation listed is a deviation a reviewer can check against the code.
  3. State in the report's limitations chapter that the simulator is an in-repo pure-Python model validated against expected AODV behaviour, **not** against NS-3, and that the results characterise *this* simulator ([C-17]).
- **Files:** `AGENTS.md:26-27`, `AGENTS.md:30-31`, `AGENTS.md:41-45`, `MANET_IDS_BTech_Execution_Guide.md:10-12`, `MANET_IDS_BTech_Execution_Guide.md:154-156`, `MANET_IDS_BTech_Execution_Guide.md:360`

---

## Missing Critical Features

### [C-15] The acceptance-criterion chain does not exist

- **Class:** [GAP] · **Severity:** High
- **Issue:** The project's definition of success is a single reproducible chain (`AGENTS.md:163-166`, restated at `MANET_IDS_BTech_Execution_Guide.md:379`):
  > `launch simulation → generate normal/attack traffic → extract features → run trained IDS → identify malicious node → trigger response → show measurable improvement vs. baseline AODV`
  None of the seven links exists. This is the correct state for a pre-implementation repo — but it is the thing the whole plan is aimed at, so it should drive the sequencing rather than emerge at the end.
- **Files:** `AGENTS.md:163-167`, `MANET_IDS_BTech_Execution_Guide.md:379`, `MANET_IDS_BTech_Execution_Guide.md:381-383`
- **Impact:** Risk is a plan that satisfies each phase locally and never closes the loop. The classic failure: the ML phase produces a good classifier on a dataset, and the response phase cannot wire the prediction into AODV routing, so the "measurable improvement" link is never demonstrated. `MANET_IDS_BTech_Execution_Guide.md:133` is the hard part: "Re-run **the same scenario** and quantify whether network performance improves" — that requires the IDS to act *inside* the routing loop, not in a post-processing script.
- **Fix approach:** Build the chain **vertically and end-to-end, thin, as early as possible** — a placeholder classifier (a constant, a random guess, a trivial threshold) is enough to close the loop on Day 2-3. Then each later phase improves one link without changing the interfaces. Concretely, define the chain's contract up front:
  - `simulator/run_scenario.py --scenario <json> --seed <int> --out <dir>` is the single entry point (`AGENTS.md:65`) and must accept an optional `--model <path>` that, when present, enables the IDS. Same command, same seed, with and without `--model` ⇒ the IDS-off and IDS-on runs of `MANET_IDS_BTech_Execution_Guide.md:238`.
  - The IDS hook is a callable the routing code consults: `should_route_via(node_id) -> bool` or a node-trust table. Its implementation lives in `ml/`; the simulator calls it through an injected object, and the simulator never imports `ml/` (the same injection discipline as `AGENTS.md:67-69`).
  - Build the dashboard **only after** this chain runs end to end (`AGENTS.md:166-167`).

### [C-01] Random row split is the single biggest way to fake this project

- **Class:** [RISK] · **Severity:** Critical
- **Issue:** `AGENTS.md:142-143` (rule 4): "**Never split by random rows.** Rows from one simulation run are correlated; a random row split inflates scores. Hold out by **scenario / seed / configuration**." `MANET_IDS_BTech_Execution_Guide.md:122` says the same from the other side ("Split data by scenario, not randomly by rows alone"), and `MANET_IDS_BTech_Execution_Guide.md:314` names it the second most common failure point. The mechanism is that consecutive windows of one run are near-duplicates: the model effectively memorises the run and is then tested on the run it memorised.
- **Files:** `AGENTS.md:142-143`, `AGENTS.md:171`, `MANET_IDS_BTech_Execution_Guide.md:122`, `MANET_IDS_BTech_Execution_Guide.md:314`, `MANET_IDS_BTech_Execution_Guide.md:217`
- **Diagnostic symptom:** The `AGENTS.md:171` entry is explicit — "Model looks great on test data → suspect random row split (rule 4) or leakage (rule 5)." Concretely: a held-out score that is implausibly high (F1 > 0.95) on a problem the guide describes as "a harder detection problem" (`MANET_IDS_BTech_Execution_Guide.md:55` for grayhole) is a split bug until proven otherwise. A second tell: **the row-split and the group-split give materially different numbers** — if the group-split F1 is 0.55 and the row-split F1 is 0.98, the row-split number is meaningless.
- **Impact:** Every headline metric in the report and the defence is wrong, and the number cannot be recovered — it has to be re-run. It also invalidates the generalisation claim (E8, `MANET_IDS_BTech_Execution_Guide.md:253`) and the multi-class model decision (Step 7, `MANET_IDS_BTech_Execution_Guide.md:230-231`), because both are about generalisation across runs, not within a run.
- **Fix approach:**
  1. Carry a `run_id` column in the dataset — a deterministic composite of `scenario_name + seed` — and use it as the grouping key. `sklearn.model_selection.GroupShuffleSplit` and `StratifiedGroupKFold` are present in the installed scikit-learn 1.8.0 and are the right tools (`AGENTS.md:142-143`).
  2. Hold out **entire runs**: every row of a held-out run is in test, every row of a training run is in train. For generalisation, hold out entire *configurations* (a node count or a speed) as well as entire seeds.
  3. **Make the split a property of the dataset, not of the training script.** Persist the split assignment (`run_id` → `split`) in `data/` so every reported number is computed on the same partition and can be re-verified without re-running the split. This is what makes rule 8 auditable.
  4. Use the same split for all classifiers (`MANET_IDS_BTech_Execution_Guide.md:217`) and report it in the methodology chapter.
  5. Add `tests/test_split_integrity.py` asserting no `run_id` appears on both sides ([C-04]).
  6. Do not use `train_test_split` on raw rows anywhere in `ml/`. Grep for it in review; it is a rule violation, not a style preference.

### [C-05] No baseline-AODV comparison: the IDS benefit is unmeasurable

- **Class:** [RISK] · **Severity:** Critical
- **Issue:** `AGENTS.md:150-151` (rule 7): "**Always compare against plain AODV without IDS.** Report PDR, throughput, end-to-end delay, packet loss, routing overhead for both." `MANET_IDS_BTech_Execution_Guide.md:319` lists "No baseline" as a failure point, `MANET_IDS_BTech_Execution_Guide.md:51` makes the comparison an MVP item, and `MANET_IDS_BTech_Execution_Guide.md:237-238` makes it a Step 8 deliverable. The project has **three** distinct baselines it must produce, and the docs name them in different places: the clean AODV baseline (E1), the attacked AODV baseline (E2, IDS off), and the attacked AODV with the IDS on (E7).
- **Files:** `AGENTS.md:150-151`, `MANET_IDS_BTech_Execution_Guide.md:51`, `MANET_IDS_BTech_Execution_Guide.md:194`, `MANET_IDS_BTech_Execution_Guide.md:237-238`, `MANET_IDS_BTech_Execution_Guide.md:244-253`, `MANET_IDS_BTech_Execution_Guide.md:258-259`, `MANET_IDS_BTech_Execution_Guide.md:177`
- **Diagnostic symptom:** `AGENTS.md:177` — "'ML improves the network' but no baseline table → rule 7 violated; the claim is unverifiable."
- **Impact:** Without a baseline table, the project's central claim ("the IDS improves the network") has no referent, and `MANET_IDS_BTech_Execution_Guide.md:383` (the recommended demonstration) cannot be staged. A three-column table is the whole deliverable: **clean AODV | attacked AODV (IDS off) | attacked AODV + IDS**, each with PDR, throughput, end-to-end delay, packet loss and routing overhead, all from the *same* scenario and seed.
- **Fix approach:**
  1. The baseline runs are produced by the same `simulator/run_scenario.py` with the same scenario JSON and seed, with the attack enabled and the IDS disabled. Make the scenario schema express all three modes explicitly (`attack: {type, node_id, enabled}` and `ids: {enabled, model, threshold}`) so the three runs differ **only** in those fields — no hand-edited copies of a config.
  2. Emit all five metrics per run into the per-run record ([C-06], [C-25]) so the comparison table is assembled mechanically from records, never typed by hand.
  3. Add the IDS-off/IDS-on delta to the report as an explicit table, including the response's own cost (extra routing overhead, IDS processing time — `MANET_IDS_BTech_Execution_Guide.md:259`). A positive delta with a stated cost is the honest, defensible result.
  4. If the IDS-on run does **not** beat the attacked baseline, report that. It is a finding, it is honest, and it is far better than an unverifiable claim — and the report structure has a place for it (`MANET_IDS_BTech_Execution_Guide.md:360`).

### [C-09] Accuracy-only reporting on structurally imbalanced data

- **Class:** [RISK] · **Severity:** High
- **Issue:** `AGENTS.md:147-149` (rule 6): "**Never report accuracy alone.** Always report precision, recall, F1, false-positive rate, and a confusion matrix. Imbalanced security data can look perfect while missing most attacks." `MANET_IDS_BTech_Execution_Guide.md:261` repeats it, `MANET_IDS_BTech_Execution_Guide.md:257` lists the required metric set, and `MANET_IDS_BTech_Execution_Guide.md:369` makes "Why are accuracy and F1-score both required?" a viva question. The imbalance here is **structural, not incidental**: with 20-50 nodes (`MANET_IDS_BTech_Execution_Guide.md:181`, `MANET_IDS_BTech_Execution_Guide.md:246`) and 1-2 attackers, roughly **2-10%** of node-window rows are malicious, and the imbalance worsens as the observation window gets longer or the node count goes up. A trivial classifier that labels every window "normal" scores 90-98% accuracy and detects nothing.
- **Files:** `AGENTS.md:147-149`, `AGENTS.md:172`, `MANET_IDS_BTech_Execution_Guide.md:255-261`, `MANET_IDS_BTech_Execution_Guide.md:287`, `MANET_IDS_BTech_Execution_Guide.md:369`
- **Diagnostic symptom:** `AGENTS.md:172` — "Accuracy high but recall terrible → class imbalance; report the full metric set (rule 6)." The tell is a recall for the malicious class near zero while accuracy is high; the second tell is a confusion matrix whose malicious column is empty.
- **Impact:** An accuracy-only result is the classic way this project fails its own defence, and it is *worse* than no result because it looks successful. It also misleads the response stage: a detector with near-zero recall triggers no alerts, so the IDS-on run equals the attacked baseline and "no improvement" is reported for the wrong reason.
- **Fix approach:**
  1. Every evaluation prints **precision, recall, F1, false-positive rate, and the confusion matrix** for the malicious class, plus macro-averaged precision/recall/F1. Report the trivial "all-normal" baseline's accuracy next to the model's, so the imbalance is visible rather than implied.
  2. Report **per-class** recall for the malicious class explicitly — that is the number that says whether the IDS works.
  3. Handle the imbalance at Day 10 as the guide says (`MANET_IDS_BTech_Execution_Guide.md:287` — "Handle missing values, duplicates, class imbalance and preprocessing") with `class_weight="balanced"` (or `balanced_subsample` for Random Forest) rather than by resampling the dataset: resampling breaks the group structure that [C-01] depends on.
  4. Choose the detection threshold and the operating point on the validation split and report the full metric set **at that point** ([C-20]).
  5. Make the metric set a single function in `ml/` so no report, plot or notebook can accidentally print accuracy alone.

### [C-10] No git remote: no backup, no collaboration, no CI

- **Class:** [CURRENT] · **Severity:** High
- **Issue:** The repository is on `main` with **no remote** — `git remote -v` returns empty, and `git config --list --local` shows only `core.*` entries. `AGENTS.md:6-7` states this deliberately: "everything stays local until a remote is deliberately added." The guide, however, assumes a hosted repository throughout: `MANET_IDS_BTech_Execution_Guide.md:145` lists "Git + GitHub" as the version-control component, `MANET_IDS_BTech_Execution_Guide.md:153` says "Install Git and create a private/public repository", and `MANET_IDS_BTech_Execution_Guide.md:278` makes "Create Git repository" the Day-1 deliverable. The two documents therefore disagree about Day 1 (see [C-11]).
- **Files:** `AGENTS.md:6-7`, `AGENTS.md:126`, `MANET_IDS_BTech_Execution_Guide.md:145`, `MANET_IDS_BTech_Execution_Guide.md:153`, `MANET_IDS_BTech_Execution_Guide.md:278`
- **Impact:** The working tree exists in exactly one place on exactly one disk. A single hardware failure, an accidental `git clean -fd`, a ransomware event, or a reformat loses everything — and because `traces/`, `data/` and `results/` are all gitignored ([C-06], [C-18]), the *evidence* of every experiment is gone even if the code survives. There is also no second machine to run the "does it reproduce elsewhere?" check, and no CI to run the tests that [C-04] will add. In a 21-day, 3-4-person project, one lost laptop is a total loss.
- **Fix approach:** Close the Day-1 deliverable by making the decision explicit rather than implicit:
  1. Create a remote (GitHub private, or equivalent) and `git push -u origin main` **before Day 1 of the plan closes** — the guide's own Day-1 deliverable already calls for it. The team size (3-4 people, `MANET_IDS_BTech_Execution_Guide.md:274`) makes a private remote the right choice; it also keeps the simulator's code out of the public eye until the report is submitted.
  2. Record the decision in `docs/decisions.md` and update `AGENTS.md:6-7` and `MANET_IDS_BTech_Execution_Guide.md:153`/`:278` **in the same commit** ([C-11]).
  3. Push at the end of every working session, and tag the weekly frozen versions ([C-16]).
  4. Once a remote exists, a minimal CI is cheap and directly discharges [C-27]: install from `requirements.txt` and run `python -m pytest -q`. Nothing more.

### [C-26] No README, no experiment log, no scope freeze, no saved model

- **Class:** [GAP] · **Severity:** Medium
- **Issue:** The guide's deliverable list (`MANET_IDS_BTech_Execution_Guide.md:322-334`) names several artefacts that do not exist:
  - **`README.md`** — listed in the repository structure (`MANET_IDS_BTech_Execution_Guide.md:172`) and required by rule 8's phrasing ("Every number in the report/**README** must trace to a saved experiment run", `AGENTS.md:151`). It is also the first thing a grader opens.
  - **`docs/` with notes, deviations and an experiment log** (`AGENTS.md:123`; `MANET_IDS_BTech_Execution_Guide.md:171`) — the place where the deviations from [C-23] and the decisions in [C-11] belong, and the place where the weekly checkpoint history ([C-16]) is recorded.
  - **A one-page scope freeze, team responsibilities, and repository** — the explicit Day-1 deliverable (`MANET_IDS_BTech_Execution_Guide.md:278`). None exists.
  - **A trained model and preprocessing pipeline** (`MANET_IDS_BTech_Execution_Guide.md:127`, `:329`) — cannot exist before Phase 2 (`MANET_IDS_BTech_Execution_Guide.md:63`), but its *contract* (what is saved, in what format, with what card) should be decided now ([C-28]).
- **Files:** `AGENTS.md:123`, `AGENTS.md:151`, `MANET_IDS_BTech_Execution_Guide.md:127`, `MANET_IDS_BTech_Execution_Guide.md:172`, `MANET_IDS_BTech_Execution_Guide.md:278`, `MANET_IDS_BTech_Execution_Guide.md:322-334`
- **Impact:** The deliverables list in `MANET_IDS_BTech_Execution_Guide.md:322-334` is what the guide says the project *is*. Right now it is 0% satisfied, and four of the ten items are documents that take minutes each and remove ambiguity later (scope freeze, decisions log, experiment log, README). They are cheap now and expensive at Day 20.
- **Fix approach:** Create, in this order:
  1. `docs/scope.md` — the one-page scope freeze: title, attack set, routing protocol, simulator, models, deliverables, team responsibilities, and the exact scope sentence required by [C-17]. This is the Day-1 deliverable, and it is what the mentor will check first.
  2. `docs/decisions.md` — the dated decision log (also the anchor for the sync rule in [C-11]).
  3. `docs/experiment_log.md` — one row per run: date, scenario, seed, git SHA, metrics, run-record path, notes. This is the human-readable face of the per-run manifest ([C-06]).
  4. `README.md` — the project overview, the exact run commands, the scope sentence, the environment setup from `requirements.txt`, and a table of reported results with a link to each run record.
  5. `docs/environment.md` — interpreter, library versions, platform, and the `python -m pip` convention (`AGENTS.md:107`).

### [C-30] The row-granularity ambiguity decides whether the IDS can name a node

- **Class:** [GAP] · **Severity:** Medium
- **Issue:** `MANET_IDS_BTech_Execution_Guide.md:104` defines the unit of the dataset in the same breath as two incompatible options: "Convert raw traces into **one row per observation window or node**." Every downstream decision depends on which one is meant, and the specification never resolves it. The competing constraints are:
  - The IDS must **identify a malicious node** (`AGENTS.md:166`: "identify malicious node"), and the response mechanism "assigns the node a malicious/low-trust state" (`MANET_IDS_BTech_Execution_Guide.md:131`). That requires the classification unit to be **the node**.
  - A per-window-per-network row (one row per window, aggregating the whole network) has **no node identity to label** — its label would be "this window contained an attack somewhere", which is a different task from "this node is the attacker" and cannot drive a per-node response.
  - The features themselves are per-node quantities (`packet_forward_ratio` for a node, `neighbor_count` of a node, `hop_count` observed by a node — `MANET_IDS_BTech_Execution_Guide.md:106-116`), so a network-level row would have to aggregate them, changing their meaning.
- **Files:** `MANET_IDS_BTech_Execution_Guide.md:104-117`, `MANET_IDS_BTech_Execution_Guide.md:130-133`, `AGENTS.md:163-166`
- **Impact:** If two members build the dataset with different row granularities, the Day-12 classifier comparison compares two different datasets rather than three classifiers, and the "model" is answering a different question than the report claims. If a network-level granularity is chosen, the response stage has nothing to act on and the acceptance chain cannot close ([C-15]). The label space also differs between the two choices: a network-level label is binary per window; a node-level label is one-of-{normal, blackhole, grayhole} per (node, window).
- **Fix approach:** Decide explicitly, record it in the scenario schema and the feature-provenance table, and state it in the report's methodology chapter:
  1. **One row per (node, observation window).** The node is the classification unit; the label is that node's status in that window. This is the only granularity consistent with "identify malicious node" and with a per-node response.
  2. Put `window_seconds` and `row_granularity` in the scenario JSON so the unit is a recorded experimental variable rather than an implicit convention.
  3. State the derived class balance explicitly: with N nodes and 1 attacker, the malicious fraction of rows is ~1/N (≈2-5% at 20-50 nodes), which is what makes [C-09] a structural problem and not an incidental one.
  4. Cover this with `tests/test_window_features.py` and a dataset-level assertion that the row count equals `nodes × windows × active_attackers` for a given scenario.

### [C-33] No CI, no scenario registry, no version-tag convention

- **Class:** [GAP] · **Severity:** Low
- **Issue:** Three small automation/registration gaps, all cheap to close and all currently absent:
  - **No CI.** No `.github/workflows/`, no pipeline of any kind. `.gitignore` has no CI artefacts to ignore, and there is no remote for CI to run against ([C-10]). The guide lists "Git + GitHub" (`MANET_IDS_BTech_Execution_Guide.md:145`) and the whole project is a reproducibility argument, but nothing mechanically verifies the code even imports, let alone that the tests pass.
  - **No scenario registry.** `AGENTS.md:116` says `scenarios/` holds "one JSON config per experiment/scenario", and the experiment matrix `MANET_IDS_BTech_Execution_Guide.md:244-253` (E1-E8) enumerates the required configurations — but there is no index, manifest or naming convention connecting an experiment ID (E1, E4, E8) to a scenario file. The Day-18 deliverable is "Run the complete experiment matrix with controlled seeds and configurations" (`MANET_IDS_BTech_Execution_Guide.md:295`); running the matrix means the mapping from experiment to config must be explicit and complete.
  - **No version-tag convention.** The mentor checkpoint rule requires a frozen working version at the end of each week (`AGENTS.md:158-159`, `MANET_IDS_BTech_Execution_Guide.md:387`), but no tag naming scheme is defined, so "week 3" is a matter of memory.
- **Files:** `AGENTS.md:116`, `AGENTS.md:158-159`, `MANET_IDS_BTech_Execution_Guide.md:145`, `MANET_IDS_BTech_Execution_Guide.md:244-253`, `MANET_IDS_BTech_Execution_Guide.md:295`, `MANET_IDS_BTech_Execution_Guide.md:387`
- **Impact:** Low individually, but they compound the traceability problem. Without a scenario index, the "experiment matrix" is a mental list, and a matrix that is 90% covered is indistinguishable from one that is complete until someone reconstructs it by hand. Without a tag convention, the weekly freeze is not demonstrable to a mentor. Without CI, the tests from [C-04] are run by hand and skipped when the day is busy — which is exactly when they matter.
- **Fix approach:**
  1. `scenarios/index.json` — a registry mapping each experiment ID (E1-E8) to its scenario files, seeds and expected output locations. One command reads it and runs the matrix. This is what makes Day 18 mechanical rather than manual.
  2. Tag convention: `git tag -a week1 -m "Week 1: simulator + baseline metrics"`, `week2`, `week3`, `week4` — plus a `release` tag at the end. Record the tag in `docs/experiment_log.md` so the weekly freeze is auditable.
  3. Once a remote exists ([C-10]), add a minimal CI: install `requirements.txt`, run `python -m pytest -q`, and (optionally) a short smoke run of `simulator/run_scenario.py` on a 5-node scenario to prove the toolchain works on a clean machine. Nothing heavier. Keep CI non-blocking on the main branch; it informs, it does not gate, unless the team explicitly chooses that later.
  4. Record the naming convention for scenario files in `docs/` so two people produce the same file name for the same experiment (e.g. `E2_blackhole_pos<NN>_seed<NNN>.json`).

---

## Test Coverage Gaps

### [C-04a] Everything is untested — the gap is total, and it is the project's highest-leverage one

- **Class:** [GAP] · **Severity:** Critical
- **What's not tested:** There is no test suite, no `pytest` dependency, no test directory, no CI, and no assertion of any kind. Every property the project claims is currently unverified by machine: determinism, simulator fidelity, attack effectiveness, absence of leakage, split integrity, metric completeness, and traceability.
- **Files:** repo root (no `tests/`), `.gitignore:15` (implies pytest), `AGENTS.md:136-138` (gates), `AGENTS.md:142-151` (rules 4-8), `AGENTS.md:169-177` (known failure points)
- **Risk:** Every concern in this document is silent by nature: a leakage column, a random row split, a nondeterministic iteration order, a drifting baseline, an untraceable number — none of them raises an error. A test suite is the only thing that converts them from silent to loud. Without it, the project's central claim is that the measurements are trustworthy, and the project contains **zero** evidence for that claim.
- **Priority:** **High** — highest priority of anything in this document after the first simulator run exists. The suite must be built alongside the simulator, not after the ML phase.
- **Minimum viable suite** (in build order; each maps to a rule):
  | Test file | Asserts | Rule |
  |---|---|---|
  | `tests/test_determinism.py` | Same scenario + seed ⇒ byte-identical trace; different seed ⇒ different trace | `AGENTS.md:72-74` |
  | `tests/test_baseline_invariants.py` | PDR falls with loss/distance, hop count grows with distance, routing overhead > 0, clean PDR in a sane band | `MANET_IDS_BTech_Execution_Guide.md:154-156` |
  | `tests/test_attack_effect.py` | Blackhole PDR is measurably below clean PDR by a stated margin; grayhole likewise | `AGENTS.md:137` (gate 2) |
  | `tests/test_no_leakage.py` | Design-matrix columns == allow-list; no forbidden column names; no trivially separating feature | `AGENTS.md:145-146` |
  | `tests/test_split_integrity.py` | No `run_id` on both sides of the split | `AGENTS.md:142-143` |
  | `tests/test_metrics_complete.py` | Every evaluation output contains precision, recall, F1, FPR and a confusion matrix | `AGENTS.md:147-149` |
  | `tests/test_window_features.py` | Window aggregation matches a hand-computed expectation on a tiny synthetic trace | `MANET_IDS_BTech_Execution_Guide.md:209` |
  | `tests/test_import_boundary.py` | `simulator/` never imports `attacks/`, `ml/` or any web framework | `AGENTS.md:67-69` |

### [C-04b] No test covers the guide's own acceptance chain

- **Class:** [GAP] · **Severity:** High
- **What's not tested:** The acceptance chain (`AGENTS.md:163-166`, `MANET_IDS_BTech_Execution_Guide.md:379`) has no automated existence check. The most important regression in the whole project is the *chain* itself: the same scenario and seed, run with and without the IDS, must produce the two baseline rows that [C-05] depends on. If the injection point in the routing loop breaks — e.g. a refactor of `simulator/aodv.py` changes the route-selection call site and the hook is silently never called — the IDS-on run would silently equal the IDS-off run, and the project would report "no measurable improvement" from a plumbing bug.
- **Files:** `AGENTS.md:163-166`, `AGENTS.md:150`, `MANET_IDS_BTech_Execution_Guide.md:133`, `MANET_IDS_BTech_Execution_Guide.md:237-238`
- **Risk:** A silently-ignored IDS hook is the exact failure that produces a false negative on the project's headline claim, and it is invisible in the metrics — the numbers look like a legitimate result.
- **Priority:** **High.**
- **Fix approach:** Add `tests/test_acceptance_chain.py`: run the same scenario and seed twice — once with the IDS enabled and once without — and assert (a) the two runs differ in at least one metric, and (b) with a deliberately-broken hook the two runs are identical, i.e. the test can actually fail. Assert also that the *clean* and *attacked* runs differ, which is the same assertion for [C-03]. This is the test that keeps the demonstration honest.

---

## Verified NOT a problem

Checked explicitly so that a future contributor does not re-investigate these or file them as bugs.

| Check | Result |
|---|---|
| Does `!results/plots/` actually un-ignore the plots directory? | **Yes.** Verified in a scratch repo with this exact `.gitignore`: `results/plots/pdr.png` is staged by `git add -A`. The `results/*` + `!results/plots/` pair works as intended. |
| Will `git commit` fail because no identity is configured? | **No.** `user.name` and `user.email` are set in the *global* config (`Sujoy`, `iamsujoy004@gmail.com`). Only the *local* config is empty. |
| Is `DataFrame.applymap` really gone on pandas 3.0.2? | **Yes.** `hasattr(pd.DataFrame, "applymap") == False`; `DataFrame.map` and `Series.map` are present. `AGENTS.md:100-102` is accurate. |
| Does SimPy 4.1.2 still expose a seeding API? | **No.** `simpy.Environment.__init__` accepts only `initial_time`; `env.random` does not exist; `simpy.seed` does not exist. `AGENTS.md:72-74`'s "explicit integer seed" must therefore be implemented with `random.Random(seed)`, not with SimPy. |
| Are the installed versions exactly the ones `AGENTS.md:93-95` claims? | **Yes.** Verified: simpy 4.1.2, networkx 3.6.1, scikit-learn 1.8.0, pandas 3.0.2, numpy 1.26.4, scipy 1.17.1, matplotlib 3.10.8, seaborn 0.13.2, pytest 9.0.2, joblib 1.5.3, jupyterlab 4.5.6, Python 3.11.8, pip 26.1.2. |
| Are the ML APIs the spec needs present in scikit-learn 1.8.0? | **Yes.** `DecisionTreeClassifier`, `RandomForestClassifier`, `SVC`, `GroupShuffleSplit`, `StratifiedGroupKFold`, `Pipeline`, `StandardScaler`, `classification_report`, `confusion_matrix`, `precision_score`, `recall_score`, `f1_score` all import cleanly. |
| Does the repo contain secrets, credentials, or a `.env`? | **No.** No `.env`, no key material, no credential file of any kind exists. There is nothing to leak, and no secret management is needed. |
| Does the `traces/` + `data/` ignore rule keep the large generated artefacts out of git? | **Yes** — that is its purpose (`AGENTS.md:128`). The problem is the *opposite* direction: the small per-run records are also excluded ([C-06], [C-18]). |
| Is the repo path safe for scripted use? | **Yes, with care.** The root path contains spaces; use `pathlib.Path` and quote paths in shell commands. Git on Windows handles it. |

---

## Prioritised remediation order

Ordered for the guide's 21-day plan (`MANET_IDS_BTech_Execution_Guide.md:276-298`) and the mentor checkpoint rule (`AGENTS.md:158-159`). Items 1-6 are all Day-1-to-Day-2 work and take minutes each; they pay down the risks that make later rework catastrophic.

| Order | Action | Closes | When |
|---|---|---|---|
| 1 | Create the remote, push `main`, record the decision | [C-10], part of [C-11] | Day 1 |
| 2 | Write `docs/scope.md` (one-page scope freeze + team responsibilities + the exact scope sentence) | [C-17], [C-26], [C-29] | Day 1 |
| 3 | Create `requirements.txt` with exact `==` pins | [C-12], [C-21] | Day 2 |
| 4 | Create the scaffold: `simulator/`, `attacks/`, `scenarios/`, `feature_extraction/`, `ml/`, `docs/`, `tests/`, `results/plots/.gitkeep`, `README.md` | [C-14] | Day 2 |
| 5 | Fix `.gitignore`: un-ignore `results/runs/**` and `data/samples/**`; correct the "reproducible from a seed" comment | [C-06], [C-18], [C-25], [C-31] | Day 2 |
| 6 | Write `docs/decisions.md` and `docs/experiment_log.md`; mark the superseded lines in the guide | [C-11], [C-26] | Day 2 |
| 7 | Build the acceptance chain vertically with a placeholder classifier; define the `--model` flag and the routing hook | [C-15], [C-20] | Day 2-3 |
| 8 | Write `tests/test_determinism.py` and `tests/test_baseline_invariants.py`; run them on every change | [C-04], [C-07] | Day 3-5 |
| 9 | Implement the blackhole attack and `tests/test_attack_effect.py` — validate the attack **before** any ML | [C-03], [C-13] | Day 6-7 |
| 10 | Implement the feature allow-list and `tests/test_no_leakage.py`; write the feature-provenance table | [C-02], [C-19] | Day 8-9 |
| 11 | Build the grouped split, persist it in `data/`, add `tests/test_split_integrity.py` | [C-01], [C-08], [C-30] | Day 10-11 |
| 12 | Build the single evaluation function that always prints the full metric set; add `tests/test_metrics_complete.py` | [C-09] | Day 11-12 |
| 13 | Freeze week-1, week-2 tags; commit the `data/samples/` sample dataset | [C-16], [C-18] | weekly |
| 14 | Implement the response hook with a frozen threshold, an isolation cap and a k-consecutive-window rule | [C-20], [C-24] | Day 17 |
| 15 | Run the full E1-E8 matrix; assemble the three-column baseline table from run records | [C-05] | Day 18 |
| 16 | Write the deviations list and the limitations chapter honestly | [C-23], [C-17] | Day 20 |
| 17 | Re-run key experiments and verify every reported number against the run records | [C-06], [C-25] | Day 21 |

**Do not start, at any point:** dashboard (`AGENTS.md:166-167`), deep learning / federated learning / blockchain / mobile app (`AGENTS.md:155`), a third and fourth attack before Blackhole and Grayhole are stable (`AGENTS.md:156-157`), SHAP / XGBoost / online learning as a starting point (`MANET_IDS_BTech_Execution_Guide.md:68-75`), a database, a web framework inside `simulator/`, or a CI pipeline before a remote exists.

---

*Concerns audit: 2026-10-22 — derived from `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md`, `.gitignore`, direct inspection of the repository and git state, verification of the installed Python 3.11.8 environment, and an empirical test of the `.gitignore` rules in a scratch repository. No packages were installed and no network or package-manager write commands were run.*
