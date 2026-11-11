"""Subprocess regression harness for legacy CLI entrypoints (D-01, Phase 12).

Every legacy command line is executed OUT-OF-PROCESS via ``sys.executable``
with ``cwd`` pinned to the project root and all outputs isolated under
pytest's tmp directories. Nothing here reads or writes the real
``.manet-workspace/`` or any repo file, so disk state can never cause flakes.

Contracts asserted per D-01:
- exit codes (0 for valid invocations, non-zero for invalid ones),
- canonical stdout banners,
- canonical trace schema columns (``SimulationRunner.TRACE_HEADER``),
- explicit subprocess timeouts (micro-fixtures keep every test fast).

The wall-clock sanity bound is deliberately generous (15s for the ~2.5s
micro simulation) to avoid CI flakes from cold starts and imports.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from feature_extraction.extract_features import SCHEMA_COLUMNS
from simulator.run_scenario import SimulationRunner

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Explicit timeout budget (seconds): micro simulation runs in ~2.5s warm;
# 30s absorbs cold interpreter/import starts without ever hanging (T-12-02).
SUBPROC_TIMEOUT = 30

# Deviation note (documented in 12-01-SUMMARY.md): the full three-model
# ml.train CLI is inherently slower than the T-12-02 <30s figure (RF grid
# with n_jobs=-1 worker-pool overhead is CLI-inherent and ml/ must not be
# modified). Measured ~9s with the staircase fixture; 90s absorbs cold
# starts while still guaranteeing termination.
TRAIN_TIMEOUT = 90


@pytest.fixture(scope="module")
def micro_scenario(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """2.0s scenario derived from scenarios/e1_normal_30n.json (micro-fixture).

    The source preset is read-only; the retimed copy is written to tmp. Two
    flows are kept active inside the 2.0s window so the trace has packets.
    """
    src = json.loads((PROJECT_ROOT / "scenarios" / "e1_normal_30n.json").read_text())
    src["scenario_id"] = "micro_compat"
    src["description"] = "Micro 2.0s compat-test scenario derived from e1_normal_30n"
    src["duration"] = 2.0
    flows = src["flows"][:2]
    for i, flow in enumerate(flows):
        flow["flow_id"] = i
        flow["start_time"] = 0.1 + 0.5 * i
        flow["duration"] = 1.5 - 0.5 * i
        flow["rate_pps"] = 10.0
    src["flows"] = flows
    path = tmp_path_factory.mktemp("scenario") / "micro_scenario.json"
    path.write_text(json.dumps(src, indent=2))
    return path


def test_run_scenario_success(micro_scenario: Path, tmp_path: Path) -> None:
    """python -m simulator.run_scenario: exit 0, banners, canonical trace schema."""
    trace = tmp_path / "trace.csv"
    t0 = time.perf_counter()
    proc = subprocess.run(
        [
            sys.executable, "-m", "simulator.run_scenario",
            "--scenario", str(micro_scenario),
            "--seed", "42",
            "--out", str(trace),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=SUBPROC_TIMEOUT,
    )
    elapsed = time.perf_counter() - t0

    assert proc.returncode == 0, proc.stderr
    assert "=== Simulation Results ===" in proc.stdout
    assert "Packet Delivery Ratio (PDR):" in proc.stdout

    assert trace.is_file(), f"trace CSV missing: {trace}"
    with trace.open(newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        data_rows = list(reader)
    assert header == list(SimulationRunner.TRACE_HEADER)
    assert len(data_rows) > 0

    # Generous wall-clock bound (~2.5s warm); real hang protection is the
    # subprocess timeout above.
    assert elapsed < 15.0


def test_run_scenario_missing_required_flags(tmp_path: Path) -> None:
    """python -m simulator.run_scenario without flags: non-zero exit + usage on stderr."""
    proc = subprocess.run(
        [sys.executable, "-m", "simulator.run_scenario"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=SUBPROC_TIMEOUT,
    )
    assert proc.returncode != 0
    assert "usage:" in proc.stderr


# ---------------------------------------------------------------------------
# Synthetic staircase dataset (micro-fixture for the ML CLI chain)
# ---------------------------------------------------------------------------
# Labels alternate over 20 equal intervals of packet_forward_ratio: Normal
# for even k, Blackhole for k%4==1, Grayhole for k%4==3. The other nine
# schema features are constant zero (StandardScaler maps them to 0 with
# scale_=1.0), collapsing the effective feature space to one dimension.
#
# Why this shape: the RBF SVM grid (gamma in {'scale', 0.01}) yields kernel
# radii of ~3 and ~10 in scaled space versus the ~0.17-period alternation,
# so the SVM cannot resolve it (FPR >> 1% -> ineligible), while trees
# separate the intervals perfectly. The ml.evaluate champion is therefore
# deterministically a tree and the SVM-only refit_with_probability path
# (hardcoded to data/train.csv) stays inert -- the historical >5min hang.
#
# Jitter uses a fixed 3-decimal grid (x011/x033/x055/x077/x099) identical
# for train and test, so decision-tree thresholds (midpoints x022/x044/
# x066/x088 and the x105 boundary) never collide with a data value and
# generalize exactly to test rows.

N_INTERVALS = 20
INTERVAL_WIDTH = 0.1
JITTERS = (0.011, 0.033, 0.055, 0.077, 0.099)
METRICS_CSV_HEADER = [
    "model", "accuracy", "precision", "recall", "f1_blackhole", "fpr",
    "tn", "fp", "fn", "tp",
]


def _label_for_interval(k: int) -> str:
    if k % 2 == 0:
        return "Normal"
    return "Blackhole" if k % 4 == 1 else "Grayhole"


def _staircase_frame() -> pd.DataFrame:
    """100 rows: 20 intervals x 5 fixed jitters, fully deterministic."""
    ks: list[int] = []
    js: list[float] = []
    for j in JITTERS:
        for k in range(N_INTERVALS):
            ks.append(k)
            js.append(j)
    n = len(ks)
    u = np.asarray(ks, dtype=float) * INTERVAL_WIDTH + np.asarray(js)
    data = {
        "packet_forward_ratio": u,
        "packet_drop_ratio": np.zeros(n),
        "avg_delay": np.zeros(n),
        "route_request_rate": np.zeros(n),
        "route_reply_rate": np.zeros(n),
        "throughput": np.zeros(n),
        "hop_count": np.zeros(n),
        "neighbor_count": np.zeros(n),
        "mobility_speed": np.zeros(n),
        "label": [_label_for_interval(int(k)) for k in ks],
    }
    return pd.DataFrame(data)[SCHEMA_COLUMNS]


@pytest.fixture(scope="module")
def trained_models(tmp_path_factory: pytest.TempPathFactory) -> SimpleNamespace:
    """Train all three legacy models ONCE via subprocess (module-scoped).

    ml.evaluate requires every candidate joblib to exist, so the chain
    trains random_forest, decision_tree and svm in a single subprocess and
    shares the result across the train/evaluate tests.
    """
    base = tmp_path_factory.mktemp("ml_chain")
    train_csv = base / "train_stair.csv"
    test_csv = base / "test_stair.csv"
    frame = _staircase_frame()
    frame.to_csv(train_csv, index=False)
    frame.to_csv(test_csv, index=False)  # train==test by design (deterministic)
    models_dir = base / "models"

    proc = subprocess.run(
        [
            sys.executable, "-m", "ml.train",
            "--models", "random_forest,decision_tree,svm",
            "--train-csv", str(train_csv),
            "--models-dir", str(models_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=TRAIN_TIMEOUT,
    )
    assert proc.returncode == 0, proc.stderr
    return SimpleNamespace(
        base=base, train_csv=train_csv, test_csv=test_csv,
        models_dir=models_dir, proc=proc,
    )


def test_ml_train_success(trained_models: SimpleNamespace) -> None:
    """python -m ml.train: exit 0, training banner, three model artifacts."""
    assert "MODEL TRAINING" in trained_models.proc.stdout
    assert "ALL REQUESTED CANDIDATE MODELS TRAINED & PERSISTED" in trained_models.proc.stdout
    for name in ("random_forest", "decision_tree", "svm"):
        assert (trained_models.models_dir / f"{name}.joblib").is_file()


def test_ml_evaluate_success(
    trained_models: SimpleNamespace, tmp_path: Path
) -> None:
    """python -m ml.evaluate: exit 0, report banner, full artifact set, non-SVM champion."""
    results_dir = tmp_path / "results"
    proc = subprocess.run(
        [
            sys.executable, "-m", "ml.evaluate",
            "--models-dir", str(trained_models.models_dir),
            "--test-csv", str(trained_models.test_csv),
            "--results-dir", str(results_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=SUBPROC_TIMEOUT,
    )
    assert proc.returncode == 0, proc.stderr
    assert "EVALUATION & ARTIFACT EXPORT COMPLETE" in proc.stdout
    assert "Champion selected:" in proc.stdout

    # Champion persistence (models dir)
    assert (trained_models.models_dir / "best_model.joblib").is_file()
    assert (trained_models.models_dir / "model_metadata.json").is_file()

    # Metrics and report artifacts (results dir)
    assert (results_dir / "metrics.csv").is_file()
    assert (results_dir / "feature_importance.csv").is_file()
    assert (results_dir / "evaluation_report.md").is_file()
    plots = results_dir / "plots"
    assert plots.is_dir() and any(plots.glob("*.png"))

    with (results_dir / "metrics.csv").open(newline="") as fh:
        header = next(csv.reader(fh))
    assert header == METRICS_CSV_HEADER

    # T-12-02 regression guard: the staircase fixture keeps the champion a
    # tree, so the SVM-only refit_with_probability path (hardcoded
    # data/train.csv) must stay inert and the run must never hang.
    metadata = json.loads(
        (trained_models.models_dir / "model_metadata.json").read_text()
    )
    assert metadata["champion"] in ("random_forest", "decision_tree")
    assert metadata["selection"]["fpr_gate_satisfied"] is True


def test_verify_gate2_impact_script() -> None:
    """scripts/verify_gate2_impact.py: real benchmark run, exit 0, GATE 2 PASSED.

    The script has no argparse parser, so there is no --help contract; the
    plan's alternative ("micro-duration scenario execution") is covered by
    running the benchmark itself, which executes its internal micro
    scenarios read-only and writes nothing.
    """
    proc = subprocess.run(
        [sys.executable, "scripts/verify_gate2_impact.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=SUBPROC_TIMEOUT,
    )
    assert proc.returncode == 0, proc.stderr
    assert "GATE 2 PASSED" in proc.stdout


def test_build_dataset_help() -> None:
    """scripts/build_dataset.py --help: exit 0 and usage description."""
    proc = subprocess.run(
        [sys.executable, "scripts/build_dataset.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=SUBPROC_TIMEOUT,
    )
    assert proc.returncode == 0
    assert "usage:" in proc.stdout


def test_ml_train_nonexistent_dataset(tmp_path: Path) -> None:
    """python -m ml.train with a non-existent dataset path exits non-zero."""
    proc = subprocess.run(
        [
            sys.executable, "-m", "ml.train",
            "--models", "decision_tree",
            "--train-csv", str(tmp_path / "does_not_exist.csv"),
            "--models-dir", str(tmp_path / "models"),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=SUBPROC_TIMEOUT,
    )
    assert proc.returncode != 0
    assert "Model training failed" in proc.stderr


def test_ml_evaluate_invalid_models_dir(
    trained_models: SimpleNamespace, tmp_path: Path
) -> None:
    """python -m ml.evaluate with an invalid models dir exits non-zero."""
    proc = subprocess.run(
        [
            sys.executable, "-m", "ml.evaluate",
            "--models-dir", str(tmp_path / "no_such_models"),
            "--test-csv", str(trained_models.test_csv),
            "--results-dir", str(tmp_path / "results"),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=SUBPROC_TIMEOUT,
    )
    assert proc.returncode != 0
    assert "Evaluation failed" in proc.stderr
