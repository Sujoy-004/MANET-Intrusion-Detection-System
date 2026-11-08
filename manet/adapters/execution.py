"""Execution adapter protocols and telemetry event schemas.

Defines the abstract execution protocol and telemetry event contract allowing the
TUI presentation layer to govern background simulation runs without importing
business logic packages (simulator, attacks, feature_extraction, ml).
"""

from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Any, Callable, Dict, Protocol

from manet.adapters.handoff import SimulationLaunchRequest


@dataclass(frozen=True)
class TelemetryEvent:
    """Frozen snapshot of a raw network simulation or node telemetry event."""

    sim_time: float
    src: int
    dst: int
    pkt_id: int
    pkt_type: str
    hop_count: int
    dropped_by: str
    node_id: int
    speed: str
    neighbor_count: str


class TelemetrySinkProtocol(Protocol):
    """Protocol for live telemetry event sinks."""

    def record_event(self, event: TelemetryEvent) -> None:
        """Record an individual telemetry event under lock."""
        ...

    def update_progress(self, sim_now: float, duration: float) -> None:
        """Update simulation progress coordinates."""
        ...


class SimulationExecutorProtocol(Protocol):
    """Protocol defining the simulation execution contract for background workers."""

    def execute_simulation(
        self,
        launch_request: SimulationLaunchRequest,
        cancel_token: threading.Event,
        telemetry_sink: Any,
        stage_cb: Callable[[str], None],
        progress_cb: Callable[[float, float], None],
    ) -> Dict[str, float]:
        """Execute simulation discrete-event stepping loop and return computed metrics."""
        ...


__all__ = [
    "SimulationExecutorProtocol",
    "TelemetryEvent",
    "TelemetrySinkProtocol",
]
