"""Screen definitions for MANET IDS TUI application."""

from __future__ import annotations

from manet.screens.console import ConsoleScreen
from manet.screens.help_about import HelpAboutScreen
from manet.screens.main_workspace import MainWorkspace
from manet.screens.simulation_workflow import SimulationWorkflowScreen

__all__ = [
    "ConsoleScreen",
    "HelpAboutScreen",
    "MainWorkspace",
    "SimulationWorkflowScreen",
]
