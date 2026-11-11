---
phase: 12-quality-testing-delivery
reviewed: 2026-11-11T10:50:35Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - requirements.txt
  - scripts/verify_environment.py
  - tests/conftest.py
  - tests/test_legacy_cli_compat.py
  - tests/test_manet_paths.py
findings:
  critical: 1
  warning: 4
  info: 6
  total: 11
status: issues_found
---

# Phase 12: Code Review Report

**Reviewed:** 2026-11-11T10:50:35Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the five net-new Phase 12 files: the exact-pin manifest, the on-demand
environment gate, the hermetic workspace-isolation fixture, the subprocess CLI
regression harness, and the one-line marker opt-out in the path-anchoring test.
Cross-referenced every called contract (`WorkspaceAdapter.__init__`,
`SimulationRunner.TRACE_HEADER`, `SCHEMA_COLUMNS`, `ml.train` / `ml.evaluate`
error streams, `validate_structural_invariants`, `verify_gate2_impact.py`,
`manet/__main__.py`).

Empirical checks run during this review (not just code reading):

- `python scripts/verify_environment.py` → exit 0, all 10 pins `[OK]`, 4/4
  entrypoints `[OK]`, artifacts `[PRESENT]`.
- `python -m manet --help` under captured pipes → still alive at 35 s (emits
  terminal escape sequences), confirming the `tui_alive` semantics.
- `python scripts/verify_gate2_impact.py` → exit 0 in ~5.7 s, so the 30 s
  `SUBPROC_TIMEOUT` in the CLI harness is not the binding constraint.
- `validate_structural_invariants(..., model_path=<absent>)` → returns exactly
  `"IDS enabled but champion model artifact (ml/models/best_model.joblib) does
  not exist on disk..."`, which is the string the path test asserts against.
- `pip download numpy==1.26.4 --python-version 3.13 --only-binary=:all:` →
  no matching distribution (available list starts at 2.1.0).

Overall the work is unusually well documented and the gate behaves as
advertised on this host. The material defect is that the "hermetic" suite is
not reproducible from a clean checkout: `tests/test_manet_paths.py` asserts on
a gitignored, untracked model artifact. The remaining findings are robustness
gaps in `verify_environment.py` (uncaught metadata exception, duplicated pin
table, unbounded Python check) and one flake-prone wall-clock assertion.

## Critical Issues

### CR-01: Path-anchoring test depends on a gitignored, untracked model artifact — fails on a fresh checkout

**File:** `tests/test_manet_paths.py:46-48`
**Issue:** The test asserts that `validate_structural_invariants(valid_ids_config)`
(with `ids.enabled=True`) reports no `"champion model artifact"` error. That
validator resolves the default model path to
`<repo>/ml/models/best_model.joblib` and appends the error whenever the file is
absent (confirmed empirically: the error string is returned verbatim when the
path does not exist). However:

- `.gitignore:11` ignores `ml/models/*.joblib`.
- `git ls-files ml/models/` returns only `model_metadata.json` — the joblib is
  **not tracked**.
- `scripts/verify_environment.py:10-12` explicitly documents that "a fresh
  checkout legitimately has no trained model yet."

So on any clean clone (or CI runner) the assertion at line 48 fails:

```
AssertionError: assert not any("champion model artifact" in e for e in errs)
```

This contradicts the phase's hermetic-isolation contract (`tests/conftest.py`
states test runs must never depend on real disk state) and the phase's
reproducibility claim. The `@pytest.mark.real_workspace_defaults` opt-out is
correct for the *workspace root* assertions (lines 50-61), but it also disables
isolation for this unrelated artifact dependency, which is not what the marker
was intended to expose.

**Fix:** Make the model-artifact assertion hermetic by supplying an explicit
stub artifact (or by testing the path-anchoring logic with IDS disabled and
asserting the model-path default separately):

```python
# tests/test_manet_paths.py
def test_repo_root_anchoring_outside_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ...
    # Hermetic: the champion joblib is gitignored, so a fresh checkout has none.
    # Pass an explicit non-empty stub to validate_structural_invariants.
    stub_model = tmp_path / "best_model.joblib"
    stub_model.write_bytes(b"stub")
    errs = validate_structural_invariants(valid_ids_config, model_path=stub_model)
    assert not any("champion model artifact" in e for e in errs)
```

Alternatively, split the assertion: keep `ids.enabled=False` for the anchoring
checks and add a separate test that asserts the *default* model path resolves
to `repo_root / "ml" / "models" / "best_model.joblib"` without requiring the
file to exist.

## Warnings

### WR-01: `importlib.metadata.version()` is outside the `try`, so a missing distribution aborts the whole gate

**File:** `scripts/verify_environment.py:99-105`
**Issue:** The `try/except ImportError` wraps only `importlib.import_module`.
The very next line calls `importlib.metadata.version(distribution)`, which
raises `importlib.metadata.PackageNotFoundError` (a subclass of
`ModuleNotFoundError` → `ImportError`, confirmed) when the module imports but
the distribution metadata is absent (e.g., a vendored/renamed/conda-installed
package, or an editable install whose metadata name differs from the PyPI
name). That exception escapes `check_dependencies` → `main` and terminates the
script with a traceback, skipping the artifact report, the entrypoint checks,
and the final verdict. The gate still fails closed (non-zero exit), but it no
longer honors its own contract of reporting every check and returning a clean
`1`.

**Fix:**

```python
try:
    importlib.import_module(module_name)
    installed = importlib.metadata.version(distribution)
except ImportError as err:  # PackageNotFoundError is an ImportError subclass
    print(f"  [FAIL] {distribution} could not be imported: {err}")
    all_ok = False
    continue
```

### WR-02: The pin table is hardcoded and duplicates `requirements.txt` — drift makes the gate enforce stale versions

**File:** `scripts/verify_environment.py:39-50`
**Issue:** `PINNED_DEPENDENCIES` re-states all 10 `name == version` pairs that
already live in `requirements.txt:1-10`. The docstring calls the values "exact
pinned version per requirements.txt", but nothing enforces that the two stay in
sync. When a pin is bumped in `requirements.txt` and this dict is not updated,
the gate will keep asserting the *old* version — either failing a healthy
environment or, worse, blessing a version that no longer matches the manifest
the developer was told to install. This is the exact drift the gate exists to
catch, reintroduced one level up.

**Fix:** Derive the expectations from the manifest (single source of truth) or
add a startup consistency assertion:

```python
def _load_pinned_versions() -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        dist, sep, ver = line.partition("==")
        if sep:
            pins[dist] = ver
    return pins
```

Then assert `set(PINNED_DEPENDENCIES) == set(_load_pinned_versions())` and that
each version matches, so a manifest edit without a gate edit is itself a hard
failure.

### WR-03: The Python runtime check is unbounded (`>= 3.11`) but the pins do not support Python 3.13+

**File:** `scripts/verify_environment.py:36,79-83`
**Issue:** The gate advertises "Python 3.11+ is required" and accepts any
`sys.version_info >= (3, 11)`. The pinned `numpy==1.26.4` predates CPython
3.13 and publishes no cp313 wheels (verified: `pip download --python-version
3.13 --only-binary=:all:` finds no matching distribution; the earliest
available is 2.1.0). On Python 3.13 the gate therefore prints
`[OK] Python version is >= 3.11.` and then fails later at
`import numpy` / `importlib.metadata` with a confusing dependency error, rather
than reporting an unsupported interpreter up front. The project's own
verification report states only 3.11.8 was tested.

**Fix:** Bound the check to the range the pin set actually supports (or record
the tested range explicitly):

```python
MIN_PYTHON = (3, 11)
MAX_PYTHON = (3, 12)  # numpy==1.26.4 has no cp313 wheels

...
if not (MIN_PYTHON <= sys.version_info[:2] <= MAX_PYTHON):
    print(
        f"  [FAIL] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}.."
        f"{MAX_PYTHON[0]}.{MAX_PYTHON[1]} is required "
        f"(pins are validated only in this range)."
    )
    return False
```

### WR-04: Wall-clock assertion on a subprocess is a flake vector

**File:** `tests/test_legacy_cli_compat.py:104`
**Issue:** `assert elapsed < 15.0` measures the full subprocess wall time
(Python startup + imports + 2.0 s simulation). The warm measurement is ~2.5 s,
but on a loaded CI host, cold interpreter starts, antivirus scanning, and CPU
contention can push a 2.5 s process past 15 s. The assertion adds no protection
the 30 s `subprocess.run(timeout=...)` does not already provide — it can only
produce false failures. The module docstring itself acknowledges the tension
("Generous wall-clock bound ... real hang protection is the subprocess timeout
above"), but a non-deterministic assertion in a regression harness is still a
reliability defect.

**Fix:** Delete the wall-clock assertion and rely on the timeout, or derive a
generous bound from it:

```python
# The 30 s subprocess timeout is the hang guard; a wall-clock assertion here
# only adds flake risk on loaded hosts.
assert proc.returncode == 0, proc.stderr
```

## Info

### IN-01: Brittle hard-coded preset count

**File:** `tests/test_manet_paths.py:37`
**Issue:** `assert len(presets) == 5` couples the path-anchoring test to the
current number of files in `scenarios/`. Adding, removing, or renaming a
scenario preset breaks this test for an unrelated reason, producing a noisy
failure that points at path anchoring rather than at the scenario inventory.
**Fix:** Assert the directory is anchored and non-empty (`assert presets`), or
compare against `len(list((repo_root / "scenarios").glob("*.json")))` if the
exact count is genuinely part of the contract.

### IN-02: Module docstring overstates hermeticity

**File:** `tests/test_legacy_cli_compat.py:4-6`
**Issue:** The docstring claims "Nothing here reads or writes the real
`.manet-workspace/` or any repo file". The harness does read repo files:
`micro_scenario` loads `scenarios/e1_normal_30n.json` (line 56) and
`test_verify_gate2_impact_script` runs a benchmark that loads
`scenarios/e1_normal_30n.json` and `scenarios/e2_blackhole_30n.json`. The
reads are read-only and intentional, but the claim is inaccurate and could
mislead a future author into thinking no repo state is touched.
**Fix:** Reword to "Nothing here reads or writes the real `.manet-workspace/`;
scenario presets under `scenarios/` are read-only inputs."

### IN-03: Gate 2 test docstring misdescribes the workload

**File:** `tests/test_legacy_cli_compat.py:270-276`
**Issue:** The docstring says the script "executes its internal micro scenarios
read-only and writes nothing". `scripts/verify_gate2_impact.py` has no
`--help`/micro mode: `run_benchmark()` defaults to `duration=300.0` over seeds
42/43/44, i.e. six full 300-second paired simulations (measured ~5.7 s wall on
this host). The description understates the work and the coupling to simulator
behaviour.
**Fix:** Reword to "runs the real multi-seed benchmark (300 s paired
baseline/attack simulations, seeds 42/43/44, ~6 s warm) read-only".

### IN-04: Magic-string dispatch and double glob in the artifact report

**File:** `scripts/verify_environment.py:126-128`
**Issue:** The scenarios entry is detected with
`if relative.endswith("scenarios")`, and `path.glob("*.json")` is evaluated
twice (once for `any(...)`, once for `len(list(...))`). The string test is
implicit coupling to the literal path `"scenarios"`, and the second glob
re-walks the directory.
**Fix:** Make the artifact kind explicit, e.g. change `OPTIONAL_ARTIFACTS` to
carry a `kind` field (`"dir_glob"` vs `"file"`), and compute the file list once:

```python
matches = sorted(path.glob("*.json")) if path.is_dir() else []
present = bool(matches)
detail = f"{len(matches)} files" if present else "none"
```

### IN-05: `pytest` is pinned in the runtime manifest; no `requires-python` metadata

**File:** `requirements.txt:10`
**Issue:** `pytest==9.0.2` is a test-only tool but is pinned alongside runtime
dependencies in the single manifest. That is defensible for reproducibility
(the gate re-asserts it), but it means a runtime-only install (`pip install
-r requirements.txt` on a deployment host) pulls a test framework. There is no
`pyproject.toml`/`setup.py` in the repo, so `requires-python` metadata cannot
be expressed anywhere — which is also why WR-03's upper bound has no natural
home.
**Fix:** If the manifest is meant to describe runtime deps, split test tools
into `requirements-dev.txt`; otherwise add a comment in `requirements.txt`
stating that the manifest is the full reproducible environment (runtime + test)
and that the supported Python range is 3.11–3.12.

### IN-06: Hermetic isolation does not cover the direct `.manet-workspace` fallback in `StepReviewWidget`

**File:** `tests/conftest.py:57-60` (with `manet/widgets/wizard_step_review.py:137`)
**Issue:** The autouse fixture patches `WorkspaceAdapter.__init__` only.
`StepReviewWidget.__init__` independently computes
`workspace_root or (get_project_root() / ".manet-workspace")`. In the real
workflow this is harmless because `SimulationWorkflowScreen` passes
`workspace_root=self.workspace_adapter.workspace_root`
(`manet/screens/simulation_workflow.py:110`), and the widget's `workspace_root`
is currently display-only (lines 260/265). But the fixture's stated guarantee —
"test runs must never touch the real `.manet-workspace/`" — is therefore not
complete: any future write through a standalone-constructed `StepReviewWidget`
would hit the real workspace, and the fixture would not prevent it.
**Fix:** Either patch `manet.runtime.paths.get_project_root` during isolation
(strongest, but affects all adapters), or have `StepReviewWidget` resolve its
default through `WorkspaceAdapter()` so the single patch covers it.

---

_Reviewed: 2026-11-11T10:50:35Z_
_Reviewer: OpenCode (gsd-code-reviewer)_
_Depth: standard_
