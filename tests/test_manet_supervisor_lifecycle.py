"""Unit and lifecycle tests for WorkloadSupervisor state machine and atomic manifest updates.

Verifies:
- Single-simulation active capacity constraint enforcement (TUI-15).
- Missing executor fail-fast guard transitions to FAILED and marks manifest.
- Worker creation failure transitions state to FAILED without hanging in RUNNING.
- Manifest update failure transitions state cleanly to FAILED.
- Standard lifecycle: IDLE -> CONFIGURED -> RUNNING -> COMPLETED.
- Cooperative cancellation: RUNNING -> STOPPING -> INTERRUPTED.
- Terminal state race precedence: FAILED > INTERRUPTED > COMPLETED (TUI-18).
- Atomic manifest persistence via temporary file and atomic replace.
"""

from __future__ import annotations

import json
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, Optional
import pytest

from manet.adapters.execution import SimulationExecutorProtocol
from manet.adapters.handoff import SimulationLaunchRequest
from manet.adapters.workspace import record_launch_manifest, update_manifest_status
from manet.runtime.supervisor import WorkloadState, WorkloadSupervisor


class MockApp:
    """Mock Textual application frame providing run_worker."""

    def __init__(self, should_fail: bool = False, execute_inline: bool = True) -> None:
        self.should_fail = should_fail
        self.execute_inline = execute_inline
        self.spawned_threads: list[threading.Thread] = []

    def run_worker(
        self,
        worker_fn: Callable[[], None],
        name: str = "",
        group: str = "",
        thread: bool = True,
        exit_on_error: bool = False,
    ) -> Any:
        if self.should_fail:
            raise RuntimeError("Failed to allocate OS worker thread.")

        if self.execute_inline:
            t = threading.Thread(target=worker_fn, name=name)
            self.spawned_threads.append(t)
            t.start()
            t.join()
            return t
        else:
            t = threading.Thread(target=worker_fn, name=name)
            self.spawned_threads.append(t)
            t.start()
            return t


class DummyExecutor:
    """Mock simulation executor allowing controlled execution, delay, or exception injection."""

    def __init__(
        self,
        metrics: Optional[Dict[str, float]] = None,
        raise_exc: Optional[Exception] = None,
        step_delay: float = 0.0,
    ) -> None:
        self.metrics = metrics or {"pdr": 0.95, "throughput_bps": 15000.0}
        self.raise_exc = raise_exc
        self.step_delay = step_delay
        self.executed = False

    def execute_simulation(
        self,
        launch_request: SimulationLaunchRequest,
        cancel_token: threading.Event,
        telemetry_sink: Any,
        stage_cb: Callable[[str], None],
        progress_cb: Callable[[float, float], None],
    ) -> Dict[str, float]:
        self.executed = True
        stage_cb("INITIALIZING")
        time.sleep(0.01)
        stage_cb("SIMULATING")

        duration = float(launch_request.config.get("duration", 10.0))
        for step in range(5):
            if self.raise_exc is not None and (step == 2 or cancel_token.is_set()):
                raise self.raise_exc
            if cancel_token.is_set():
                break
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            progress_cb(float(step + 1) * 2.0, duration)

        stage_cb("FINALIZING")
        return self.metrics


def _create_test_request(exp_dir: Path, scenario_name: str = "test_scen", duration: float = 10.0) -> SimulationLaunchRequest:
    exp_dir.mkdir(parents=True, exist_ok=True)
    cfg = {"name": scenario_name, "duration": duration, "nodes": 10}
    record_launch_manifest(exp_dir, exp_dir.name, scenario_name, 42, cfg)
    return SimulationLaunchRequest(
        experiment_id=exp_dir.name,
        scenario_name=scenario_name,
        seed=42,
        config=cfg,
        workspace_dir=exp_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=False,
    )


def test_single_active_workload_capacity(tmp_path: Path):
    """Verify supervisor strictly permits only 1 active simulation workload at a time."""
    req1 = _create_test_request(tmp_path / "exp_1")
    req2 = _create_test_request(tmp_path / "exp_2")

    executor = DummyExecutor(step_delay=0.1)
    supervisor = WorkloadSupervisor(executor=executor)

    app = MockApp(execute_inline=False)
    supervisor.start_simulation(req1, app)
    assert supervisor.is_running

    # Attempting to start a second simulation while active must raise RuntimeError
    with pytest.raises(RuntimeError, match="already active"):
        supervisor.start_simulation(req2, app)

    # Attempting to prepare a new simulation while active must raise RuntimeError
    with pytest.raises(RuntimeError, match="already active"):
        supervisor.prepare_simulation(req2)

    # Wait for thread to finish
    for t in app.spawned_threads:
        t.join(timeout=2.0)


def test_missing_executor_fail_fast(tmp_path: Path):
    """Verify starting simulation with executor=None fails fast and marks manifest FAILED."""
    req = _create_test_request(tmp_path / "missing_exec")
    supervisor = WorkloadSupervisor(executor=None)
    app = MockApp()

    with pytest.raises(RuntimeError, match="No simulation executor configured"):
        supervisor.start_simulation(req, app)

    assert supervisor.state == WorkloadState.FAILED
    assert supervisor.stage == "FAILED"
    assert "No simulation executor" in (supervisor.last_error or "")

    # Manifest must reflect FAILED status
    manifest = json.loads((req.workspace_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "FAILED"
    assert "No simulation executor" in manifest.get("error_details", "")


def test_worker_creation_failure(tmp_path: Path):
    """Verify that worker spawn error transitions state to FAILED without hanging in RUNNING."""
    req = _create_test_request(tmp_path / "worker_fail")
    executor = DummyExecutor()
    supervisor = WorkloadSupervisor(executor=executor)
    app = MockApp(should_fail=True)

    with pytest.raises(RuntimeError, match="Failed to start simulation worker"):
        supervisor.start_simulation(req, app)

    assert supervisor.state == WorkloadState.FAILED
    assert supervisor.stage == "FAILED"
    assert not supervisor.is_running

    manifest = json.loads((req.workspace_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "FAILED"


def test_manifest_update_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Verify that manifest write failure transitions supervisor cleanly to FAILED."""
    req = _create_test_request(tmp_path / "manifest_fail")
    executor = DummyExecutor()
    supervisor = WorkloadSupervisor(executor=executor)
    app = MockApp()

    # Force update_manifest_status to raise
    def mock_update(*args, **kwargs):
        raise OSError("Disk quota exceeded or filesystem read-only")

    monkeypatch.setattr("manet.runtime.supervisor.update_manifest_status", mock_update)

    with pytest.raises(RuntimeError, match="Failed to update manifest status to RUNNING"):
        supervisor.start_simulation(req, app)

    assert supervisor.state == WorkloadState.FAILED
    assert supervisor.stage == "FAILED"
    assert not supervisor.is_running


def test_state_transitions_completed(tmp_path: Path):
    """Verify standard lifecycle IDLE -> CONFIGURED -> RUNNING -> COMPLETED."""
    req = _create_test_request(tmp_path / "normal_run")
    executor = DummyExecutor(metrics={"pdr": 0.98, "throughput_bps": 24000.0})
    supervisor = WorkloadSupervisor(executor=executor)

    assert supervisor.state == WorkloadState.IDLE
    supervisor.prepare_simulation(req)
    assert supervisor.state == WorkloadState.CONFIGURED
    assert supervisor.stage == "CONFIGURED"

    app = MockApp(execute_inline=True)
    supervisor.start_simulation(req, app)

    assert supervisor.state == WorkloadState.COMPLETED
    assert supervisor.stage == "COMPLETED"
    assert not supervisor.is_running
    assert supervisor.metrics == {"pdr": 0.98, "throughput_bps": 24000.0}

    manifest = json.loads((req.workspace_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "COMPLETED"
    assert manifest["metrics"]["pdr"] == 0.98
    assert "completed_at" in manifest


def test_cancellation_interrupted(tmp_path: Path):
    """Verify cancellation transition RUNNING -> STOPPING -> INTERRUPTED."""
    req = _create_test_request(tmp_path / "cancel_run")
    executor = DummyExecutor(step_delay=0.05)
    supervisor = WorkloadSupervisor(executor=executor)

    app = MockApp(execute_inline=False)
    supervisor.start_simulation(req, app)

    assert supervisor.state == WorkloadState.RUNNING

    # Call cancel
    cancelled = supervisor.cancel_simulation()
    assert cancelled is True
    assert supervisor.state == WorkloadState.STOPPING
    assert supervisor.cancel_token.is_set()

    # Second cancel is idempotent
    assert supervisor.cancel_simulation() is False

    for t in app.spawned_threads:
        t.join(timeout=2.0)

    assert supervisor.state == WorkloadState.INTERRUPTED
    assert supervisor.stage == "INTERRUPTED"
    assert not supervisor.is_running

    manifest = json.loads((req.workspace_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "INTERRUPTED"
    assert "completed_at" in manifest


def test_terminal_precedence_failed_over_interrupted(tmp_path: Path):
    """Verify terminal precedence: FAILED takes priority over cancellation INTERRUPTED."""
    req = _create_test_request(tmp_path / "precedence_run")
    executor = DummyExecutor(raise_exc=ValueError("Crash during interrupted run"), step_delay=0.05)
    supervisor = WorkloadSupervisor(executor=executor)

    app = MockApp(execute_inline=False)
    supervisor.start_simulation(req, app)

    # Cancel while running
    supervisor.cancel_simulation()
    assert supervisor.cancel_token.is_set()

    for t in app.spawned_threads:
        t.join(timeout=2.0)

    # Even though cancel was signaled, executor exception makes terminal state FAILED
    assert supervisor.state == WorkloadState.FAILED
    assert supervisor.stage == "FAILED"
    assert "Crash during interrupted run" in (supervisor.last_error or "")

    manifest = json.loads((req.workspace_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "FAILED"
    assert "Crash during interrupted run" in manifest.get("error_details", "")


def test_completed_manifest_write_failure_transitions_to_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verify failure to persist COMPLETED manifest transitions state to FAILED and records error."""
    req = _create_test_request(tmp_path / "completed_manifest_fail")
    executor = DummyExecutor(metrics={"pdr": 0.95, "throughput_bps": 15000.0})
    supervisor = WorkloadSupervisor(executor=executor)

    real_update = update_manifest_status

    def mock_update(workspace_dir, status, **kwargs):
        if status == "COMPLETED":
            raise OSError("Disk full while saving completed manifest")
        return real_update(workspace_dir, status, **kwargs)

    monkeypatch.setattr("manet.runtime.supervisor.update_manifest_status", mock_update)

    app = MockApp(execute_inline=True)
    supervisor.start_simulation(req, app)

    assert supervisor.state == WorkloadState.FAILED
    assert supervisor.stage == "FAILED"
    assert "Failed to persist COMPLETED manifest" in (supervisor.last_error or "")
    assert "Disk full while saving completed manifest" in (supervisor.last_error or "")

    # Manifest should have best-effort FAILED status
    manifest = json.loads((req.workspace_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "FAILED"


def test_interrupted_manifest_write_failure_transitions_to_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verify failure to persist INTERRUPTED manifest transitions state to FAILED and records error."""
    req = _create_test_request(tmp_path / "interrupted_manifest_fail")
    executor = DummyExecutor(step_delay=0.05)
    supervisor = WorkloadSupervisor(executor=executor)

    real_update = update_manifest_status

    def mock_update(workspace_dir, status, **kwargs):
        if status == "INTERRUPTED":
            raise OSError("I/O error saving interrupted manifest")
        return real_update(workspace_dir, status, **kwargs)

    monkeypatch.setattr("manet.runtime.supervisor.update_manifest_status", mock_update)

    app = MockApp(execute_inline=False)
    supervisor.start_simulation(req, app)
    supervisor.cancel_simulation()

    for t in app.spawned_threads:
        t.join(timeout=2.0)

    assert supervisor.state == WorkloadState.FAILED
    assert supervisor.stage == "FAILED"
    assert "Failed to persist INTERRUPTED manifest" in (supervisor.last_error or "")
    assert "I/O error saving interrupted manifest" in (supervisor.last_error or "")

    manifest = json.loads((req.workspace_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "FAILED"


def test_secondary_manifest_failure_preserves_original_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Verify worker execution error with secondary manifest failure retains original cause."""
    req = _create_test_request(tmp_path / "secondary_fail_run")
    executor = DummyExecutor(raise_exc=RuntimeError("Primary executor explosion"))
    supervisor = WorkloadSupervisor(executor=executor)

    real_update = update_manifest_status

    def mock_update(workspace_dir, status, **kwargs):
        if status == "FAILED":
            raise OSError("Secondary disk write failure")
        return real_update(workspace_dir, status, **kwargs)

    monkeypatch.setattr("manet.runtime.supervisor.update_manifest_status", mock_update)

    app = MockApp(execute_inline=True)
    supervisor.start_simulation(req, app)

    assert supervisor.state == WorkloadState.FAILED
    assert supervisor.stage == "FAILED"
    assert "Primary executor explosion" in (supervisor.last_error or "")
    assert "secondary manifest update failure: Secondary disk write failure" in (
        supervisor.last_error or ""
    )


def test_atomic_manifest_updates(tmp_path: Path):
    """Verify update_manifest_status preserves existing attributes, writes atomically, and updates fields."""
    exp_dir = tmp_path / "atomic_manifest"
    exp_dir.mkdir(parents=True, exist_ok=True)
    cfg = {"name": "atomic_test", "nodes": 20}
    record_launch_manifest(exp_dir, "exp_atomic", "atomic_test", 99, cfg)

    # Step 1: Update to RUNNING
    m1_path = update_manifest_status(exp_dir, "RUNNING")
    assert m1_path.is_file()
    assert not (exp_dir / "manifest.json.tmp").exists()
    m1 = json.loads(m1_path.read_text(encoding="utf-8"))
    assert m1["status"] == "RUNNING"
    assert m1["configuration"] == cfg
    assert "updated_at" in m1
    assert "completed_at" not in m1

    # Step 2: Update to COMPLETED with metrics
    m2_path = update_manifest_status(exp_dir, "COMPLETED", metrics={"pdr": 0.88, "delay": 0.05})
    assert not (exp_dir / "manifest.json.tmp").exists()
    m2 = json.loads(m2_path.read_text(encoding="utf-8"))
    assert m2["status"] == "COMPLETED"
    assert m2["pdr"] == 0.88
    assert m2["metrics"] == {"pdr": 0.88, "delay": 0.05}
    assert "completed_at" in m2
