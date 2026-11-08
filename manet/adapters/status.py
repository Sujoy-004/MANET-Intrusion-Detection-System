"""Status adapter providing decoupled active workload and engine status."""

from __future__ import annotations

from dataclasses import dataclass


from typing import Any, Optional


@dataclass(frozen=True)
class WorkloadStatus:
    """Status record representing workload execution and engine readiness."""

    workload_state: str  # e.g., "IDLE", "RUNNING", "STOPPING", "COMPLETED", "INTERRUPTED", "FAILED"
    engine_state: str    # e.g., "AODV Engine Ready (Offline)", "AODV Engine Active (SIMULATING)"
    description: str     # e.g., "No active simulation", "Simulating e1_normal_30n (seed 42)"


class StatusAdapter:
    """Provides active workload status distinguishing engine readiness from execution state."""

    def __init__(self, supervisor: Optional[Any] = None) -> None:
        self.supervisor = supervisor

    def get_status(self) -> WorkloadStatus:
        """Return the current workload and engine state."""
        if self.supervisor is not None and getattr(self.supervisor, "is_running", False):
            state_name = getattr(self.supervisor.state, "name", str(self.supervisor.state))
            stage = getattr(self.supervisor, "stage", "ACTIVE")
            req = getattr(self.supervisor, "current_request", None)
            if req:
                desc = f"Simulating {req.scenario_name} (seed {req.seed})"
            else:
                desc = "Simulation active"
            return WorkloadStatus(
                workload_state=state_name,
                engine_state=f"AODV Engine Active ({stage})",
                description=desc,
            )

        if self.supervisor is not None and getattr(self.supervisor, "state", None) is not None:
            state_name = getattr(self.supervisor.state, "name", str(self.supervisor.state))
            if state_name in ("COMPLETED", "INTERRUPTED", "FAILED"):
                req = getattr(self.supervisor, "current_request", None)
                if req:
                    desc = f"Last run: {req.experiment_id} ({state_name})"
                else:
                    desc = f"Status: {state_name}"
                return WorkloadStatus(
                    workload_state=state_name,
                    engine_state="AODV Engine Ready (Offline)",
                    description=desc,
                )

        return WorkloadStatus(
            workload_state="IDLE",
            engine_state="AODV Engine Ready (Offline)",
            description="No active simulation",
        )


__all__ = ["StatusAdapter", "WorkloadStatus"]
