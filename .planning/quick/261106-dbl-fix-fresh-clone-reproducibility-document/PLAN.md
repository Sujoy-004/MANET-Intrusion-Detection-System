---
phase: quick-261106-dbl-fix-fresh-clone-reproducibility-document
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - README.md
  - docs/GETTING-STARTED.md
  - docs/DEVELOPMENT.md
autonomous: true
requirements: [QUICK-REPRO-01]

must_haves:
  truths:
    - "A fresh-clone reader can follow the docs top-to-bottom and reach the closed-loop IDS demo without a FileNotFoundError on ml/models/best_model.joblib"
    - "The docs explain why .joblib artifacts are excluded (.gitignore `ml/models/*.joblib`) and that they are deterministically regenerable from seeds"
    - "The docs state the expected artifacts (ml/models/best_model.joblib, ml/models/model_metadata.json) and the FPR <= 1.0% acceptance gate with the verified champion values (F1 0.7593, FPR 0.0099)"
    - "The docs contain a troubleshooting entry for the missing best_model.joblib error that routes the reader to the prep sequence"
    - "Simulator-only workflows (baseline / blackhole without --ids) are documented as independent of ML model preparation"
  artifacts:
    - path: "README.md"
      provides: "First-time ML prep section + sim-vs-IDS independence note + regeneration rationale"
      contains: "build_dataset.py --multi-attack"
    - path: "docs/GETTING-STARTED.md"
      provides: "Step 0 model prep in the walkthrough + missing-model troubleshooting entry"
      contains: "best_model.joblib"
    - path: "docs/DEVELOPMENT.md"
      provides: "Corrected command ordering + regeneration workflow subsection"
      contains: "artifact regeneration"
  key_links:
    - from: "simulator/run_scenario.py (--ids)"
      to: "ml/models/best_model.joblib"
      via: "OnlineIDS joblib.load"
      pattern: "best_model\\.joblib"
    - from: "docs/GETTING-STARTED.md"
      to: "scripts/build_dataset.py"
      via: "prep command in Step 0"
      pattern: "build_dataset\\.py --multi-attack"
---

# Quick Task: Fix Fresh-Clone Reproducibility Documentation

## DOCS-ONLY + NO-COMMIT OVERRIDE (read before executing)

1. This task touches ONLY `README.md`, `docs/GETTING-STARTED.md`, `docs/DEVELOPMENT.md`. Do not modify any `.py` file, `data/`, `results/`, or `ml/models/` content.
2. **NO GIT COMMITS.** The orchestrator has decided the executor will NOT create any git commits for this task (`commit_docs: false` in `.planning/config.json`, plus orchestrator override). Do NOT run `git add` or `git commit`. The working tree currently contains pre-existing modified tracked files (`ml/models/model_metadata.json`, `results/plots/confusion_matrix_*.png`) from the user's own run — leave them untouched and unrecognized.
3. All numbers added by this docs task must be sourced from exactly three places: (a) the verified numbers provided by the task text (52,200 rows; train 34,800 seeds 42+43; test 17,400 seed 44; RF champion F1 0.7593; FPR 0.0099; IDS-protected PDR 62.93%), (b) the existing README benchmark table, (c) code constants. Do NOT invent other results. Note: docs/DEVELOPMENT.md "8,700 samples" claim (in ml/evaluate.py docstrings) refers to the *single-attack* default dataset — multi-attack test set is 17,400 rows; do not reproduce the 8,700 figure in the new content.

## Verified code facts (grounded — use verbatim)

| Fact | Source |
|---|---|
| `--ids` loads `ml/models/best_model.joblib` | `simulator/run_scenario.py` lines 83–87 (`ids_cfg.get("model_path", "ml/models/best_model.joblib")` → `ml/response.py` `OnlineIDS.__init__` default + `joblib.load`) |
| FPR gate = 0.01 (1.0%) | `ml/evaluate.py` line 45: `FPR_GATE: float = 0.01`; candidates exceeding gate are disqualified, and evaluate aborts if none pass |
| `build_dataset.py` flag | `--multi-attack` (store_true): builds unified dataset from `e3_blackhole_onset_30n.json` + `e4_grayhole_onset_30n.json`; defaults `--seeds 42,43,44`, `--out-dir data`, `--trace-dir traces` |
| Where splits go | `data/train.csv` (seeds 42, 43) and `data/test.csv` (seed 44) — defaults in `ml/train.py` / `ml/evaluate.py` |
| Where candidates persist | `python -m ml.train` → `ml/models/{random_forest,decision_tree,svm}.joblib` (5-fold Stratified CV) |
| Where champion persists | `python -m ml.evaluate` → `ml/models/best_model.joblib` + `ml/models/model_metadata.json` |
| What git tracks | `.gitignore` excludes `traces/`, `data/`, `ml/models/*.joblib`; `ml/models/model_metadata.json` stays tracked |

## Unified prep sequence (the canonical 3 commands to document)

```powershell
python scripts/build_dataset.py --multi-attack
python -m ml.train
python -m ml.evaluate
```

Run from repository root; Windows PowerShell (`python -m pip`, `python -m pytest` style already used by/docs). Expected outcomes (cited from verified outputs): dataset 52,200 rows total (train 34,800 from seeds 42+43; test 17,400 from seed 44); train produces 3 candidate joblibs in `ml/models/`; evaluate selects an FPR-gated champion — expected Random Forest F1 0.7593, FPR 0.0099 (0.99%, under the 1.0% gate) — persisted to `ml/models/best_model.joblib` with `model_metadata.json`.

<objective>
Make the project reproducible from a fresh GitHub clone by fixing the documentation so every reader generates the excluded model artifacts before any workflow that depends on them.

Purpose: A fresh clone fails at the documented closed-loop IDS command (`--ids`) with a missing `ml/models/best_model.joblib` because `.gitignore` intentionally excludes `ml/models/*.joblib`. The docs currently omit the required first-time model preparation sequence.

Output: Updated `README.md`, `docs/GETTING-STARTED.md`, `docs/DEVELOPMENT.md` — documentation-only. No commits.
</objective>

<execution_context>
@./.opencode/get-shit-done/workflows/execute-plan.md
@./.opencode/get-shit-done/templates/summary.md

**OVERRIDE:** skip the git-commit step from the execute-plan workflow (no-commits decision above).
</execution_context>

<context>
Ground-truth interfaces (already verified — do not re-explore):

```python
# ml/evaluate.py (line 45, 131, 135)
FPR_GATE: float = 0.01
# champion selection: eligible = [r for r in rows if r["fpr"] <= FPR_GATE]
# aborts with "FPR gate failure" if no candidate passes

# ~/.opencode simulator/run_scenario.py lines 83-87
self.online_ids = OnlineIDS(..., model_path=ids_cfg.get("model_path", "ml/models/best_model.joblib"))
# ml/response.py: OnlineIDS.__init__ default model_path = "ml/models/best_model.joblib" → joblib.load

# scripts/build_dataset.py --multi-attack (store_true)
# → unified dataset from e3_blackhole_onset_30n.json + e4_grayhole_onset_30n.json
# → data/train.csv (seeds 42,43) + data/test.csv (seed 44) + manifest

# python -m ml.train  → ml/models/<candidate>.joblib per class; python -m ml.evaluate → ml/models/best_model.joblib + model_metadata.json
```

.gitignore rules already in place (do NOT change): `traces/`, `data/`, `ml/models/*.joblib` excluded; `ml/models/model_metadata.json` tracked.
</context>

<tasks>

<task type="auto">
  <name>task 1: Add first-time ML preparation + regeneration rationale + troubleshooting to README.md</name>
  <files>README.md</files>
  <action>
Edit README.md (keep all existing content unless explicitly amended):

1. **New subsection `### 0. First-Time Model Preparation (After Fresh Clone)` inserted between `## Prerequisites & Installation` and `### 1. Run Baseline Normal Simulation`** containing:
   - Explanation: trained model artifacts (`ml/models/*.joblib`, including `ml/models/best_model.joblib`) are intentionally excluded from version control via `.gitignore` (`ml/models/*.joblib`). They are deterministic products of seeded simulations and are regenerated locally with three commands — this keeps the repository small and the results reproducible. `ml/models/model_metadata.json`, `data/`, and `traces/` are likewise generated locally (metadata is tracked; datasets and traces are not).
   - The canonical 3-command sequence (PowerShell, from repository root):
     ```powershell
     python scripts/build_dataset.py --multi-attack
     python -m ml.train
     python -m ml.evaluate
     ```
   - Expected outputs (verbatim from verified run, labeled as "verified reference run"): dataset 52,200 total rows; training split 34,800 rows (seeds 42 & 43); held-out test split 17,400 rows (seed 44); champion Random Forest persisted to `ml/models/best_model.joblib` with F1 0.7593 and FPR 0.0099 (0.99%).
   - Expected artifacts list: `data/train.csv`, `data/test.csv`, `ml/models/{random_forest,decision_tree,svm}.joblib`, `ml/models/best_model.joblib`, `ml/models/model_metadata.json`.
2. **Edit `### 3. Run Closed-Loop IDS Mitigation`** by prepending one sentence: the `--ids` flag loads `ml/models/best_model.joblib` (see §0) and fails with a missing-file error if that artifact does not exist yet. Do not change the existing command or result claims (PDR 62.93% etc. stay).
3. **New `### 4. FPR Acceptance Gate` (or bullet under §0) after the prep content**: state the locked gate `FPR <= 1.0%` enforced by `ml/evaluate.py` (`FPR_GATE = 0.01`): any candidate classifier exceeding 1.0% FPR is disqualified from champion selection, and evaluation aborts if no candidate passes. Cite the verified champion: Random Forest, F1 0.7593, FPR 0.0099 (0.99%) — under the gate.
4. **Amend `## Quick Start` intro (or insert one line after it)** noting Steps 1–2 (baseline and blackhole without `--ids`) require only the simulator dependencies and are independent of the ML pipeline; only Steps 3 (`--ids`) and the ML/evaluation workflows need the prep sequence from §0.
5. **Append a numbered troubleshooting entry to a new short `## Troubleshooting` section at the end (before `## License`)**:
   - Title: `### Missing ml/models/best_model.joblib` — Symptom: running any `--ids` command (or `python -m ml.evaluate`, `python scripts/run_closed_loop_benchmark.py`) fails with a file-not-found / invalid-load error on `ml/models/best_model.joblib`. Cause: model artifacts are excluded from the repository (`.gitignore` rule `ml/models/*.joblib`) and must be regenerated locally. Fix: run the §0 sequence `python scripts/build_dataset.py --multi-attack`, then `python -m ml.train`, then `python -m ml.evaluate` from the repository root.
  </action>
  <verify>
    <automated>python -c "import io; s = io.open('README.md', encoding='utf-8').read(); checks = {'prep section': ('build_dataset.py --multi-attack' in s and '0. First-Time Model Preparation' in s), 'IDS loads model': 'best_model.joblib' in s, 'gitignore reason': 'ml/models/*.joblib' in s, 'FPR gate': 'FPR' in s and '1.0%' in s, 'troubleshooting entry': 'Missing ml/models/best_model.joblib' in s, 'no python changes': True}; missing = [k for k, v in checks.items() if not v]; assert not missing, missing; print('README.md OK')"</automated>
  </verify>
  <done>README.md contains the prep section with the exact 3 commands, verification numbers (52,200 / 34,800 / 17,400 / F1 0.7593 / FPR 0.0099), the 0.01-gate explanation citing `ml/evaluate.py`, the sim-vs-IDS independence note, and the missing-model troubleshooting entry; existing quick-start commands and benchmark numbers unchanged.</done>
</task>

<task type="auto">
  <name>task 2: Add Step 0 + missing-model troubleshooting to docs/GETTING-STARTED.md</name>
  <files>docs/GETTING-STARTED.md</files>
  <action>
Edit docs/GETTING-STARTED.md (keep all existing content unless explicitly amended):

1. **Insert a new section `## Step 0: Generate the Trained IDS Model (First Time Only)` between `## Installation` and `## First Run: Running Your First Simulation`** containing:
   - Explanation identical in substance to README §0: `.gitignore` excludes `ml/models/*.joblib` because the binaries are deterministically regenerable from seeds — the IDS model is a build-time artifact, not a source asset. Present the canonical 3-command sequence (PowerShell block) and expected outputs: 52,200 total rows (train 34,800 / seeds 42+43; test 17,400 / seed 44); `python -m ml.train` writes candidate pipelines to `ml/models/`; `python -m ml.evaluate` selects the champion under the FPR <= 1.0% gate (verified reference: Random Forest F1 0.7593, FPR 0.0099) and writes `ml/models/best_model.joblib` + `ml/models/model_metadata.json`.
   - State expected wall-clock: the reference run of the full chain fits in a standard terminal session; readers should confirm `ml/models/best_model.joblib` exists afterward (`Test-Path ml/models/best_model.joblib` in PowerShell returns `True`).
2. **Edit `### Step 3: Run with Closed-Loop Online IDS Active`**: prepend one sentence — "This step requires the model generated in Step 0 (`ml/models/best_model.joblib`); the `--ids` runtime loads it on startup." Keep the existing command and output block untouched (62.93% PDR, strike messages, etc. remain verbatim).
3. **Insert a new numbered troubleshooting entry into `## Common Setup Issues & Troubleshooting` as item 4**: Symptom — `--ids` (or `python -m ml.evaluate` / `scripts/run_closed_loop_benchmark.py`) fails with a missing-file/al invalid-load error for `ml/models/best_model.joblib`. Cause — model binaries are excluded from the repo (`ml/models/*.joblib` in `.gitignore`) and regenerate locally. Fix — execute the Step 0 sequence from the repository root.
4. **Amend the `## Next Steps` bullet list** to mention that a fresh clone complete-prep starts at Step 0 before continuing elsewhere (one added bullet linking back to Step 0). Keep existing bullets.
  </action>
  <verify>
    <automated>python -c "import io; s = io.open('docs/GETTING-STARTED.md', encoding='utf-8').read(); checks = {'step0': 'Step 0: Generate the Trained IDS Model' in s, 'canonical cmds': ('build_dataset.py --multi-attack' in s and 'python -m ml.train' in s and 'python -m ml.evaluate' in s), 'numbers': ('52,200' in s and '34,800' in s and '17,400' in s and '0.7593' in s and '0.0099' in s), 'gitignore reason': 'ml/models/*.joblib' in s, 'trouble item 4': ('4.' in s and 'best_model.joblib' in s), 'powershell': 'Test-Path' in s}; missing = [k for k, v in checks.items() if not v]; assert not missing, missing; print('GETTING-STARTED.md OK')"</automated>
  </verify>
  <done>GETTING-STARTED.md contains a Step 0 prep section with the 3 canonical commands and verified numbers, an explicit dependency sentence on the IDS step, troubleshooting item 4 for the missing model error, and PowerShell existence check; all pre-existing walkthrough outputs preserved verbatim.</done>
</task>

<task type="auto">
  <name>task 3: Correct command ordering + regeneration workflow in docs/DEVELOPMENT.md</name>
  <files>docs/DEVELOPMENT.md</files>
  <action>
Edit docs/DEVELOPMENT.md (keep all existing content unless explicitly amended):

1. **Amend the `## Development Commands` table**:
   - Change the `python scripts/build_dataset.py` row's Purpose to clearly mark it as the FIRST step for obtaining `data/train.csv` / `data/test.csv`, e.g. "Generate seed-partitioned train/test CSVs into `data/` — run FIRST before `ml.train`; add `--multi-attack` for the canonical Blackhole+Grayhole dataset."
   - Order rows so `build_dataset.py` appears immediately above `python -m ml.train`, and annotate `python -m ml.train` / `python -m ml.evaluate` rows to note their outputs (`ml/models/<name>.joblib` candidates; `ml/models/best_model.joblib` + `model_metadata.json`) and the `ml.evaluate` FPR gate behavior.
   - Annotate the `--ids` row: requires `ml/models/best_model.joblib` (regenerated via the table's dataset+train+evaluate rows).
2. **Insert a new section `## Model Artifact Regeneration` after `## Development Commands`** explaining: why artifacts are excluded (`.gitignore` key `ml/models/*.joblib`; determinism from seeds per Engineering Contract 2 means regeneration is lossless and equivalent), the required 3-command sequence with expected artifacts, the FPR <= 1.0% gate (`FPR_GATE = 0.01` in `ml/evaluate.py` — candidates above gate are disqualified; evaluate aborts if none pass) with the verified reference champion (Random Forest F1 0.7593, FPR 0.0099), and a caution list: never commit generated `data/`, `traces/`, `results/` bulk records, or `ml/models/*.joblib` (already enforced by `.gitignore`); keep `ml/models/model_metadata.json` diffs small and committed when intentional.
3. **Cross-link**: add one sentence under Code Style/Conventions or at the end of the new section: "Fresh-clone readers should use the Step-0 walkthrough in docs/GETTING-STARTED.md or README.md Quick Start before attempting any `--ids` or ML workflow."
4. **Leave the `## Engineering Contracts & Non-Negotiables` section untouched** — no edits to contracts 1–6; they already encode the gate.
  </action>
  <verify>
    <automated>python -c "import io; s = io.open('docs/DEVELOPMENT.md', encoding='utf-8').read(); checks = {'regen section': 'Model Artifact Regeneration' in s, 'canonical cmds': ('build_dataset.py --multi-attack' in s and 'python -m ml.train' in s and 'python -m ml.evaluate' in s), 'gate': 'FPR_GATE' in s and '0.01' in s, 'verified champion': ('0.7593' in s and '0.0099' in s), 'no-commit caution': 'never commit' in s.lower(), 'ids dep': '--ids' in s and 'best_model.joblib' in s}; missing = [k for k, v in checks.items() if not v]; assert not missing, missing; print('DEVELOPMENT.md OK')"</automated>
  </verify>
  <done>DEVELOPMENT.md commands table states the required build_dataset → ml.train → ml.evaluate ordering with per-command outputs, a regeneration section documents exclusions, gate (`FPR_GATE = 0.01` in `ml/evaluate.py`), and verified champion; contracts untouched.</done>
</task>

</tasks>

<verification>
Global end-of-task checks (run all from repository root):

```powershell
# 1. Documentation-only: no Python/infra files touched by this task
python -m pytest tests/test_docs_assets.py -q  # if present; otherwise skip

# 2. Each doc contains the canonical sequence + verified numbers + gate + troubleshooting
python -c "import io; rs = {'README.md': ['build_dataset.py --multi-attack', '52,200', '34,800', '17,400', '0.7593', '0.0099', 'Missing ml/models/best_model.joblib'], 'docs/GETTING-STARTED.md': ['build_dataset.py --multi-attack', '52,200', '34,800', '17,400', 'best_model.joblib', 'Test-Path'], 'docs/DEVELOPMENT.md': ['build_dataset.py --multi-attack', 'FPR_GATE', 'Model Artifact Regeneration', '0.7593', '0.0099', 'ml/models/best_model.joblib']}; ok = all(all(t in io.open(f, encoding='utf-8').read() for t in ts) for f, ts in rs.items()); assert ok, {f: [t for t in ts if t not in io.open(f, encoding='utf-8').read()] for f, ts in rs.items()}; print('ALL DOCS OK')"

# 3. Controlled rendering: docs still reference the real acceptance gate value from code (0.01)
grep -c "FPR" ml/evaluate.py  # confirm gate symbol exists (source of truth), docs cite 1.0% consistently
```

Manual spot-check (orchestrator/user): open README.md §0, GETTING-STARTED Step 0, DEVELOPMENT regeneration section — confirm `python -m ml.evaluate` is written exactly (not `python ml.evaluate`), and that no new benchmark numbers were invented (only 52,200 / 34,800 / 17,400 / F1 0.7593 / FPR 0.0099 / PDR already in README / gate 1.0%).
</verification>

<success_criteria>
- All 3 docs updated with prep sequence (build_dataset.py --multi-attack → python -m ml.train → python -m ml.evaluate), verify automated blocks pass
- IDS workflows depend explicitly on best_model.joblib with remediation instructions pointing to the prep sequence
- FPR gate documented as `FPR <= 1.0%` citing `ml/evaluate.py` (`FPR_GATE = 0.01`) — no invented values beyond the verified outputs
- Simulator-only workflow independence stated in README Quick Start and GETTING-STARTED
- Zero Python source changes; zero git commits; pre-existing modified tracked files (`ml/models/model_metadata.json`, `results/plots/*`) untouched
</success_criteria>

<output>
After completion, create `.planning/quick/261106-dbl-fix-fresh-clone-reproducibility-document/261106-dbl-SUMMARY.md`
</output>
</plan>
