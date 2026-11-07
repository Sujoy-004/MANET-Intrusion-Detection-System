"""Widgets package for MANET IDS TUI."""

from __future__ import annotations

from manet.widgets.cta_hero import CTA_HERO_CONTENT, CtaHeroPanel
from manet.widgets.dashboard_cards import (
    ActiveWorkloadCard,
    ComponentCapabilitiesCard,
    SystemHealthCard,
)
from manet.widgets.nav_rail import NavRail
from manet.widgets.notification_rail import NotificationRail
from manet.widgets.recent_experiments import RecentExperimentsTable
from manet.widgets.status_bar import StatusBar
from manet.widgets.wizard_step_mode import StepModeSelectWidget
from manet.widgets.wizard_step_params import StepParamsWidget

__all__ = [
    "CTA_HERO_CONTENT",
    "ActiveWorkloadCard",
    "ComponentCapabilitiesCard",
    "CtaHeroPanel",
    "NavRail",
    "NotificationRail",
    "RecentExperimentsTable",
    "StatusBar",
    "StepModeSelectWidget",
    "StepParamsWidget",
    "SystemHealthCard",
]
