"""Adapters package providing decoupled presentation boundary protocols."""

from __future__ import annotations

from manet.adapters.diagnostics import (
    CapabilityStatus,
    DiagnosticsProbe,
    DiagnosticsReport,
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
from manet.adapters.status import (
    StatusAdapter,
    WorkloadStatus,
)
from manet.adapters.workspace import (
    ExperimentSummary,
    WorkspaceAdapter,
)

__all__ = [
    "CapabilityStatus",
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
    "StatusAdapter",
    "WorkloadStatus",
    "WorkspaceAdapter",
]
