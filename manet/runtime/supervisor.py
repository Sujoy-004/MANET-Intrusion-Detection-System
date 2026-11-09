"""Application-level workload supervisor managing simulation background execution.

Enforces:
- Single-simulation capacity invariant while keeping UI event loop responsive (TUI-15).
- Fail-fast missing executor validation.
- Worker creation and manifest write error safety (never hung in RUNNING/STOPPING).
- Cooperative cancellation lifecycle and terminal state precedence:
  FAILED > INTERRUPTED > COMPLETED (TUI-18).
"""

from __future__ import annotations

from enum import Enum
import threading
import time
from typing import Any, Dict, Optional

from manet.adapters.execution import SimulationExecutorProtocol
from manet.adapters.handoff import SimulationLaunchRequest
from manet.adapters.workspace import update_manifest_status
from manet.runtime.telemetry import TelemetrySink


class WorkloadState(str, Enum):
    """Lifecycle states for background simulation workloads."""

    IDLE = "IDLE"
    CONFIGURED = "CONFIGURED"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"
    FAILED = "FAILED"


class WorkloadSupervisor:
    """Manages background simulation worker execution, lifecycle state, and telemetry buffering."""

    def __init__(self, executor: Optional[SimulationExecutorProtocol] = None) -> None:
        self.executor = executor
        self.state: WorkloadState = WorkloadState.IDLE
        self.current_request: Optional[SimulationLaunchRequest] = None
        self.cancel_token = threading.Event()
        self.telemetry = TelemetrySink()
        self.worker_handle: Any = None
        self.start_monotonic: float = 0.0
        self.last_error: Optional[str] = None
        self.stage: str = "IDLE"
        self.metrics: Optional[Dict[str, float]] = None
        self._lock = threading.RLock()

    @property
    def is_running(self) -> bool:
        """Return True if a workload is currently running or in the process of stopping."""
        with self._lock:
            return self.state in (WorkloadState.RUNNING, WorkloadState.STOPPING)

    def prepare_simulation(self, request: SimulationLaunchRequest) -> None:
        """Prepare supervisor for a new validated launch request."""
        with self._lock:
            if self.state in (WorkloadState.RUNNING, WorkloadState.STOPPING):
                raise RuntimeError("A simulation workload is already active.")
            self.current_request = request
            self.state = WorkloadState.CONFIGURED
            self.stage = "CONFIGURED"

    def start_simulation(self, request: SimulationLaunchRequest, app: Any) -> None:
        """Start a simulation workload in a background worker thread."""
        with self._lock:
            if self.state in (WorkloadState.RUNNING, WorkloadState.STOPPING):
                raise RuntimeError("A simulation workload is already active.")

            # Fail-fast missing executor guard
            if self.executor is None:
                self.state = WorkloadState.FAILED
                self.stage = "FAILED"
                self.last_error = "No simulation executor configured."
                try:
                    update_manifest_status(request.workspace_dir, "FAILED", error="No simulation executor configured.")
                except Exception:
                    pass
                raise RuntimeError("No simulation executor configured.")

            self.current_request = request
            self.cancel_token.clear()
            duration = float(request.config.get("duration", 300.0))
            self.telemetry.reset(duration=duration)
            self.state = WorkloadState.RUNNING
            self.stage = "INITIALIZING"
            self.start_monotonic = time.monotonic()
            self.last_error = None
            self.metrics = None

            # Atomically update manifest to RUNNING
            try:
                update_manifest_status(request.workspace_dir, "RUNNING")
            except Exception as exc:
                self.state = WorkloadState.FAILED
                self.stage = "FAILED"
                self.last_error = f"Manifest update failed: {exc}"
                raise RuntimeError(f"Failed to update manifest status to RUNNING: {exc}") from exc

        # Worker creation safety (dispatched outside supervisor lock to allow synchronous start)
        try:
            worker_handle = app.run_worker(
                self._worker_entrypoint,
                name=f"sim-{request.experiment_id}",
                group="simulation",
                thread=True,
                exit_on_error=False,
            )
            with self._lock:
                self.worker_handle = worker_handle
        except Exception as exc:
            with self._lock:
                self.state = WorkloadState.FAILED
                self.stage = "FAILED"
                self.last_error = f"Worker creation failed: {exc}"
            try:
                update_manifest_status(request.workspace_dir, "FAILED", error=str(exc))
            except Exception:
                pass
            raise RuntimeError(f"Failed to start simulation worker: {exc}") from exc

    def cancel_simulation(self) -> bool:
        """Signal cooperative cancellation to the active simulation workload."""
        with self._lock:
            if self.state == WorkloadState.RUNNING:
                self.state = WorkloadState.STOPPING
                self.cancel_token.set()
                if self.current_request:
                    try:
                        update_manifest_status(self.current_request.workspace_dir, "STOPPING")
                    except Exception:
                        pass
                return True
            return False

    def _set_stage(self, stage: str) -> None:
        """Internal callback updating active execution stage."""
        with self._lock:
            self.stage = stage

    def _worker_entrypoint(self) -> None:
        """Worker thread entrypoint executing discrete-event simulation."""
        error_exc: Optional[Exception] = None
        metrics: Optional[Dict[str, float]] = None

        try:
            assert self.executor is not None
            assert self.current_request is not None
            metrics = self.executor.execute_simulation(
                launch_request=self.current_request,
                cancel_token=self.cancel_token,
                telemetry_sink=self.telemetry,
                stage_cb=self._set_stage,
                progress_cb=self.telemetry.update_progress,
            )
        except Exception as exc:
            error_exc = exc

        with self._lock:
            # Enforce terminal state precedence: FAILED > INTERRUPTED > COMPLETED
            # Terminal states are only published after execution and required manifest updates succeed.
            if error_exc is not None:
                self.state = WorkloadState.FAILED
                self.stage = "FAILED"
                self.last_error = str(error_exc)
                if self.current_request:
                    try:
                        update_manifest_status(
                            self.current_request.workspace_dir,
                            "FAILED",
                            error=str(error_exc),
                        )
                    except Exception as m_err:
                        self.last_error = (
                            f"{error_exc}; secondary manifest update failure: {m_err}"
                        )
            elif self.cancel_token.is_set():
                manifest_persisted = False
                if self.current_request:
                    try:
                        update_manifest_status(
                            self.current_request.workspace_dir,
                            "INTERRUPTED",
                            metrics=metrics,
                        )
                        manifest_persisted = True
                    except Exception as m_err:
                        self.state = WorkloadState.FAILED
                        self.stage = "FAILED"
                        self.last_error = f"Failed to persist INTERRUPTED manifest: {m_err}"
                        try:
                            update_manifest_status(
                                self.current_request.workspace_dir,
                                "FAILED",
                                error=f"Interrupted run manifest persistence failed: {m_err}",
                            )
                        except Exception:
                            pass
                else:
                    manifest_persisted = True

                if manifest_persisted:
                    self.state = WorkloadState.INTERRUPTED
                    self.stage = "INTERRUPTED"
                    self.metrics = metrics
            else:
                manifest_persisted = False
                if self.current_request:
                    try:
                        update_manifest_status(
                            self.current_request.workspace_dir,
                            "COMPLETED",
                            metrics=metrics,
                        )
                        manifest_persisted = True
                    except Exception as m_err:
                        self.state = WorkloadState.FAILED
                        self.stage = "FAILED"
                        self.last_error = f"Failed to persist COMPLETED manifest: {m_err}"
                        try:
                            update_manifest_status(
                                self.current_request.workspace_dir,
                                "FAILED",
                                error=f"Completed run manifest persistence failed: {m_err}",
                            )
                        except Exception:
                            pass
                else:
                    manifest_persisted = True

                if manifest_persisted:
                    self.state = WorkloadState.COMPLETED
                    self.stage = "COMPLETED"
                    self.metrics = metrics


__all__ = [
    "WorkloadState",
    "WorkloadSupervisor",
]
