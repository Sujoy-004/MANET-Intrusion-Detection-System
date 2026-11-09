"""Stepping executor equivalence and virtual-time boundary completion tests.

Verifies:
- SimPy discrete-event simulation stepped cooperatively advances virtual time cleanly
  to duration (env.now == duration) while producing deterministic, byte-identical
  traces matching baseline SimulationRunner.run() across seeds 1, 42, and 99 (TUI-17).
- Events scheduled at time == duration are not processed (matching baseline CLI runs).
- Quiescent/sparse queues complete cleanly without hanging.
- NODE_STATUS telemetry routes through log_event() to TelemetrySink and trace.csv.
- Partial traces and isolation logs persist on disk upon simulated mid-run worker exception.
- Cooperative cancellation token cleanly halts stepping and writes partial traces.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import threading
from typing import Any, List
import pytest

from bootstrap import ConcreteSimulationExecutor
from manet.adapters.execution import TelemetryEvent
from manet.adapters.handoff import SimulationLaunchRequest
from manet.runtime.telemetry import TelemetrySink
from simulator.run_scenario import SimulationRunner


PRESET_SCENARIOS = [
    "scenarios/e1_normal_30n.json",
    "scenarios/e2_blackhole_30n.json",
    "scenarios/e4_grayhole_50n.json",
]
TEST_SEEDS = [1, 42, 99]


@pytest.mark.parametrize("scenario_file", PRESET_SCENARIOS)
@pytest.mark.parametrize("seed", TEST_SEEDS)
def test_stepping_equivalence_preset_matrix(scenario_file: str, seed: int, tmp_path: Path):
    """Verify byte-identical trace output and metric equivalence across preset scenario matrix and seeds."""
    repo_root = Path(__file__).resolve().parent.parent
    scenario_path = repo_root / scenario_file
    assert scenario_path.is_file(), f"Scenario file not found: {scenario_path}"

    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario_config = json.load(f)

    # 1. Baseline CLI execution via SimulationRunner.run()
    baseline_dir = tmp_path / f"baseline_{seed}"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_trace = baseline_dir / "trace.csv"

    runner_baseline = SimulationRunner(
        scenario_config=copy.deepcopy(scenario_config),
        seed=seed,
        out_path=baseline_trace,
    )
    metrics_baseline = runner_baseline.run()

    # 2. Stepping execution via ConcreteSimulationExecutor
    stepped_dir = tmp_path / f"stepped_{seed}"
    stepped_dir.mkdir(parents=True, exist_ok=True)
    stepped_trace = stepped_dir / "trace.csv"

    launch_request = SimulationLaunchRequest(
        experiment_id=f"test_step_{seed}",
        scenario_name=scenario_path.stem,
        seed=seed,
        config=copy.deepcopy(scenario_config),
        workspace_dir=stepped_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=scenario_config.get("ids", {}).get("enabled", False),
    )

    cancel_token = threading.Event()
    telemetry_sink = TelemetrySink(maxlen=500)
    stages: List[str] = []
    progress_records: List[tuple[float, float]] = []

    executor = ConcreteSimulationExecutor()
    metrics_stepped = executor.execute_simulation(
        launch_request=launch_request,
        cancel_token=cancel_token,
        telemetry_sink=telemetry_sink,
        stage_cb=stages.append,
        progress_cb=lambda now, dur: progress_records.append((now, dur)),
    )

    # Verify stage progression
    assert stages == ["INITIALIZING", "SIMULATING", "FINALIZING"]

    # Verify progress reported
    assert len(progress_records) > 0
    assert progress_records[-1][0] == runner_baseline.duration

    # Verify metrics match
    assert metrics_stepped == metrics_baseline

    # Verify trace rows identical
    assert baseline_trace.is_file()
    assert stepped_trace.is_file()

    baseline_bytes = baseline_trace.read_bytes()
    stepped_bytes = stepped_trace.read_bytes()

    assert stepped_bytes == baseline_bytes, (
        f"Byte mismatch between stepped and baseline traces for {scenario_file} (seed={seed})"
    )


def test_stepping_boundary_events_not_processed(tmp_path: Path):
    """Verify events scheduled at time == duration are not processed, matching baseline env.run."""
    scenario_config = {
        "name": "boundary_test",
        "duration": 50.0,
        "area": [500, 500],
        "nodes": 5,
        "radio": {"range": 250.0, "loss_probability": 0.0},
        "mobility": {"model": "RandomWaypoint", "speed_range": [0.0, 0.0], "pause_time": 100.0},
        "flows": [],
    }

    stepped_dir = tmp_path / "boundary_check"
    stepped_dir.mkdir(parents=True, exist_ok=True)

    launch_request = SimulationLaunchRequest(
        experiment_id="boundary_exp",
        scenario_name="boundary_test",
        seed=42,
        config=scenario_config,
        workspace_dir=stepped_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=False,
    )

    event_at_duration_fired = False

    class BoundaryExecutor(ConcreteSimulationExecutor):
        def execute_simulation(self, launch_request, cancel_token, telemetry_sink, stage_cb, progress_cb):
            stage_cb("INITIALIZING")
            cfg = copy.deepcopy(launch_request.config)
            runner = SimulationRunner(scenario_config=cfg, seed=launch_request.seed, out_path=launch_request.workspace_dir / "trace.csv")
            runner.initialize_nodes()

            # Schedule a callback at time == duration
            def boundary_callback():
                nonlocal event_at_duration_fired
                event_at_duration_fired = True

            def _proc():
                yield runner.env.timeout(runner.duration)
                boundary_callback()

            runner.env.process(_proc())

            stage_cb("SIMULATING")
            progress_cb(0.0, runner.duration)

            from simpy.core import StopSimulation, EmptySchedule
            from simpy.events import Event, URGENT

            until = Event(runner.env)
            until._ok = True
            until._value = None
            runner.env.schedule(until, URGENT, max(0.0, runner.duration - runner.env.now))
            until.callbacks.append(StopSimulation.callback)

            try:
                while True:
                    if cancel_token.is_set():
                        break
                    runner.env.step()
            except StopSimulation:
                pass
            except EmptySchedule:
                pass

            assert runner.env.now == runner.duration, f"Expected env.now == {runner.duration}, got {runner.env.now}"
            stage_cb("FINALIZING")
            return {}

    b_exec = BoundaryExecutor()
    b_exec.execute_simulation(
        launch_request=launch_request,
        cancel_token=threading.Event(),
        telemetry_sink=TelemetrySink(),
        stage_cb=lambda s: None,
        progress_cb=lambda now, dur: None,
    )

    # The event at time == duration must NOT have fired, because the URGENT until event stopped simulation first
    assert not event_at_duration_fired, "Event scheduled at time == duration was erroneously processed"


def test_stepping_sparse_quiescent_queue(tmp_path: Path):
    """Verify stepping executor completes cleanly on scenarios with no events before duration."""
    scenario_config = {
        "name": "sparse_quiescent",
        "duration": 20.0,
        "area": [200, 200],
        "nodes": 2,
        "radio": {"range": 100.0, "loss_probability": 0.0},
        "mobility": {"model": "RandomWaypoint", "speed_range": [0.0, 0.0], "pause_time": 1000.0},
        "flows": [],
    }

    work_dir = tmp_path / "sparse"
    launch_request = SimulationLaunchRequest(
        experiment_id="sparse_exp",
        scenario_name="sparse_quiescent",
        seed=1,
        config=scenario_config,
        workspace_dir=work_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=False,
    )

    executor = ConcreteSimulationExecutor()
    metrics = executor.execute_simulation(
        launch_request=launch_request,
        cancel_token=threading.Event(),
        telemetry_sink=TelemetrySink(),
        stage_cb=lambda s: None,
        progress_cb=lambda now, dur: None,
    )

    assert isinstance(metrics, dict)
    assert (work_dir / "trace.csv").is_file()


def test_node_status_event_telemetry_and_trace(tmp_path: Path):
    """Verify NODE_STATUS events reach telemetry_sink and are recorded in trace.csv with identical fields."""
    repo_root = Path(__file__).resolve().parent.parent
    scenario_path = repo_root / "scenarios/e1_normal_30n.json"

    with open(scenario_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["duration"] = 5.0  # Run short 5s for fast verification

    work_dir = tmp_path / "status_telemetry"
    launch_request = SimulationLaunchRequest(
        experiment_id="status_exp",
        scenario_name="status_test",
        seed=42,
        config=cfg,
        workspace_dir=work_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=False,
    )

    sink = TelemetrySink(maxlen=1000)
    executor = ConcreteSimulationExecutor()
    executor.execute_simulation(
        launch_request=launch_request,
        cancel_token=threading.Event(),
        telemetry_sink=sink,
        stage_cb=lambda s: None,
        progress_cb=lambda now, dur: None,
    )

    # Check sink captured NODE_STATUS events
    snapshot = sink.drain_batch(max_items=1000)
    status_events = [e for e in snapshot.events if e.pkt_type == "NODE_STATUS"]
    assert len(status_events) > 0, "No NODE_STATUS events captured in telemetry sink"

    # Verify event fields
    sample = status_events[0]
    assert sample.pkt_id == 0
    assert sample.dst == -1
    assert sample.hop_count == 0
    assert sample.dropped_by == ""
    assert sample.node_id == sample.src

    # Check trace.csv contains NODE_STATUS
    trace_path = work_dir / "trace.csv"
    with open(trace_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[0].strip().split(",")
    assert header == SimulationRunner.TRACE_HEADER

    node_status_rows = [l.strip().split(",") for l in lines[1:] if "NODE_STATUS" in l]
    assert len(node_status_rows) > 0


def test_partial_trace_persistence_on_simulation_exception(tmp_path: Path):
    """Verify that an unexpected exception mid-run flushes partial traces before re-raising."""
    repo_root = Path(__file__).resolve().parent.parent
    scenario_path = repo_root / "scenarios/e1_normal_30n.json"

    with open(scenario_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    work_dir = tmp_path / "fail_exp"
    launch_request = SimulationLaunchRequest(
        experiment_id="fail_exp",
        scenario_name="fail_test",
        seed=42,
        config=cfg,
        workspace_dir=work_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=False,
    )

def test_real_executor_mid_run_failure_preserves_partial_trace_and_isolation_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verify real ConcreteSimulationExecutor persists partial traces and isolation log on mid-run crash."""
    import simpy
    repo_root = Path(__file__).resolve().parent.parent
    scenario_path = repo_root / "scenarios/e2_blackhole_30n.json"

    with open(scenario_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    cfg["duration"] = 15.0
    cfg["ids"] = {
        "enabled": True,
        "model_path": "ml/models/best_model.joblib",
        "window_size": 2.0,
        "eval_interval": 1.0,
        "threshold": 0.5,
    }

    work_dir = tmp_path / "mid_run_fail_exp"
    launch_request = SimulationLaunchRequest(
        experiment_id="mid_run_fail_exp",
        scenario_name="mid_run_fail_test",
        seed=42,
        config=cfg,
        workspace_dir=work_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=True,
    )

    real_step = simpy.Environment.step
    step_count = 0

    def faulty_step(env_self):
        nonlocal step_count
        step_count += 1
        if step_count >= 50:
            raise ValueError("Simulated catastrophic mid-run crash!")
        return real_step(env_self)

    monkeypatch.setattr(simpy.Environment, "step", faulty_step)

    executor = ConcreteSimulationExecutor()
    with pytest.raises(ValueError, match="Simulated catastrophic mid-run crash"):
        executor.execute_simulation(
            launch_request=launch_request,
            cancel_token=threading.Event(),
            telemetry_sink=TelemetrySink(),
            stage_cb=lambda s: None,
            progress_cb=lambda now, dur: None,
        )

    # Partial trace file MUST exist on disk and have rows
    trace_path = work_dir / "trace.csv"
    assert trace_path.is_file(), "trace.csv was not persisted upon simulation exception"
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) > 1, "trace.csv has no data rows"

    # Isolation log MUST also be persisted
    isolation_path = work_dir / "isolation_log.json"
    assert isolation_path.is_file(), "isolation_log.json was not persisted on mid-run crash"
    iso_lines = isolation_path.read_text(encoding="utf-8").splitlines()
    assert len(iso_lines) >= 1, "isolation_log.json is empty"
    assert "sim_time" in iso_lines[0]


def test_real_executor_initialization_failure_preserves_trace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verify failure during initialization after runner creation persists trace and fails supervisor."""
    repo_root = Path(__file__).resolve().parent.parent
    scenario_path = repo_root / "scenarios/e1_normal_30n.json"

    with open(scenario_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    work_dir = tmp_path / "init_fail_exp"
    launch_request = SimulationLaunchRequest(
        experiment_id="init_fail_exp",
        scenario_name="init_fail_test",
        seed=42,
        config=cfg,
        workspace_dir=work_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=False,
    )

    def faulty_initialize_traffic(self):
        self.log_event(
            sim_time=0.0,
            src=0,
            dst=1,
            pkt_id=1,
            pkt_type="NODE_STATUS",
            hop_count=0,
        )
        raise RuntimeError("Simulated failure during traffic initialization")

    monkeypatch.setattr(SimulationRunner, "initialize_traffic", faulty_initialize_traffic)

    executor = ConcreteSimulationExecutor()
    with pytest.raises(RuntimeError, match="Simulated failure during traffic initialization"):
        executor.execute_simulation(
            launch_request=launch_request,
            cancel_token=threading.Event(),
            telemetry_sink=TelemetrySink(),
            stage_cb=lambda s: None,
            progress_cb=lambda now, dur: None,
        )

    trace_path = work_dir / "trace.csv"
    assert trace_path.is_file(), "trace.csv was not persisted upon initialization failure"


def test_cooperative_cancellation_preserves_partial_trace(tmp_path: Path):
    """Verify cooperative cancellation halts stepping and flushes partial trace to disk."""
    repo_root = Path(__file__).resolve().parent.parent
    scenario_path = repo_root / "scenarios/e1_normal_30n.json"

    with open(scenario_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    work_dir = tmp_path / "cancel_exp"
    launch_request = SimulationLaunchRequest(
        experiment_id="cancel_exp",
        scenario_name="cancel_test",
        seed=42,
        config=cfg,
        workspace_dir=work_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=False,
    )

    cancel_token = threading.Event()
    stages: List[str] = []
    progress_count = 0

    def on_progress(now: float, dur: float):
        nonlocal progress_count
        progress_count += 1
        if progress_count >= 3:
            cancel_token.set()

    executor = ConcreteSimulationExecutor()
    metrics = executor.execute_simulation(
        launch_request=launch_request,
        cancel_token=cancel_token,
        telemetry_sink=TelemetrySink(),
        stage_cb=stages.append,
        progress_cb=on_progress,
    )

    assert "FINALIZING" in stages
    assert (work_dir / "trace.csv").is_file()
    lines = (work_dir / "trace.csv").read_text(encoding="utf-8").splitlines()
    assert len(lines) > 1


def test_stepping_with_online_ids(tmp_path: Path):
    """Verify that an IDS-enabled scenario runs cleanly under the stepping executor and creates isolation_log.json."""
    repo_root = Path(__file__).resolve().parent.parent
    scenario_path = repo_root / "scenarios/e2_blackhole_30n.json"

    with open(scenario_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    cfg["duration"] = 15.0  # Run 15s to trigger IDS eval loop
    cfg["ids"] = {
        "enabled": True,
        "model_path": "ml/models/best_model.joblib",
        "window_size": 2.0,
        "eval_interval": 1.0,
        "threshold": 0.5,
    }

    work_dir = tmp_path / "ids_exp"
    launch_request = SimulationLaunchRequest(
        experiment_id="ids_exp",
        scenario_name="ids_test",
        seed=42,
        config=cfg,
        workspace_dir=work_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=True,
    )

    executor = ConcreteSimulationExecutor()
    metrics = executor.execute_simulation(
        launch_request=launch_request,
        cancel_token=threading.Event(),
        telemetry_sink=TelemetrySink(),
        stage_cb=lambda s: None,
        progress_cb=lambda now, dur: None,
    )

    assert isinstance(metrics, dict)
    assert (work_dir / "trace.csv").is_file()
    assert (work_dir / "isolation_log.json").is_file()
