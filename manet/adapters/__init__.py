"""Adapters package providing decoupled presentation boundary protocols."""

from __future__ import annotations

from manet.adapters.diagnostics import (
    CapabilityStatus,
    DiagnosticsProbe,
    DiagnosticsReport,
)
from manet.adapters.execution import (
    SimulationExecutorProtocol,
    TelemetryEvent,
    TelemetrySinkProtocol,
)
from manet.adapters.handoff import (
    SimulationLaunchRequest,
)
from manet.adapters.navigation import (
    NavigationAdapter,
    NavigationTarget,
    QUICK_ACTIONS,
)
from manet.adapters.notifications import (
    NoticeItem,
    NotificationAdapter,
)
from manet.adapters.scenario import (
    ScenarioAdapter,
    ScenarioPreset,
)
from manet.adapters.simulation_config import (
    CustomScenarioBuilder,
    SimulationConfigValidator,
    build_custom_configuration,
    validate_duration,
    validate_loss_probability,
    validate_node_count,
    validate_radio_range,
    validate_seed,
    validate_structural_invariants,
)
from manet.adapters.status import (
    StatusAdapter,
    WorkloadStatus,
)
from manet.adapters.workspace import (
    ExperimentSummary,
    WorkspaceAdapter,
    record_launch_manifest,
    sanitize_run_tag,
)

__all__ = [
    "CapabilityStatus",
    "CustomScenarioBuilder",
    "DiagnosticsProbe",
    "DiagnosticsReport",
    "ExperimentSummary",
    "NavigationAdapter",
    "NavigationTarget",
    "NoticeItem",
    "NotificationAdapter",
    "QUICK_ACTIONS",
    "ScenarioAdapter",
    "ScenarioPreset",
    "SimulationConfigValidator",
    "SimulationExecutorProtocol",
    "SimulationLaunchRequest",
    "StatusAdapter",
    "TelemetryEvent",
    "TelemetrySinkProtocol",
    "WorkloadStatus",
    "WorkspaceAdapter",
    "build_custom_configuration",
    "record_launch_manifest",
    "sanitize_run_tag",
    "validate_duration",
    "validate_loss_probability",
    "validate_node_count",
    "validate_radio_range",
    "validate_seed",
    "validate_structural_invariants",
]
