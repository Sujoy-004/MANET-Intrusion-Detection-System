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

import pytest

from simulator.run_scenario import SimulationRunner

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Explicit timeout budget (seconds): micro simulation runs in ~2.5s warm;
# 30s absorbs cold interpreter/import starts without ever hanging (T-12-02).
SUBPROC_TIMEOUT = 30


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
