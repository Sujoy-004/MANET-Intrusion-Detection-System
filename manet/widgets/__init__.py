"""Widgets package for MANET IDS TUI."""

from __future__ import annotations

from manet.widgets.dashboard_cards import (
    ActiveWorkloadCard,
    ComponentCapabilitiesCard,
    SystemHealthCard,
)
from manet.widgets.nav_rail import NavRail
from manet.widgets.notification_rail import NotificationRail
from manet.widgets.status_bar import StatusBar

__all__ = [
    "ActiveWorkloadCard",
    "ComponentCapabilitiesCard",
    "NavRail",
    "NotificationRail",
    "StatusBar",
    "SystemHealthCard",
]
