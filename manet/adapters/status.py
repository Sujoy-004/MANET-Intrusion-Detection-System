"""Status adapter providing decoupled active workload and engine status."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkloadStatus:
    """Status record representing workload execution and engine readiness."""

    workload_state: str  # e.g., "IDLE", "RUNNING", "COMPLETED"
    engine_state: str    # e.g., "AODV Engine Ready (Offline)"
    description: str     # e.g., "No active simulation"


class StatusAdapter:
    """Provides active workload status distinguishing engine readiness from execution state."""

    def __init__(self) -> None:
        pass

    def get_status(self) -> WorkloadStatus:
        """Return the current workload and engine state."""
        return WorkloadStatus(
            workload_state="IDLE",
            engine_state="AODV Engine Ready (Offline)",
            description="No active simulation",
        )


__all__ = ["StatusAdapter", "WorkloadStatus"]
