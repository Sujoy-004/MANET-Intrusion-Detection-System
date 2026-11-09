"""Screen definitions for MANET IDS TUI application."""

from __future__ import annotations

from manet.screens.console import ConsoleScreen
from manet.screens.help_about import HelpAboutScreen
from manet.screens.history import HistoryScreen
from manet.screens.live_run import LiveRunScreen
from manet.screens.main_workspace import MainWorkspace
from manet.screens.prune_modal import PruneConfirmationModal
from manet.screens.results import ResultsScreen
from manet.screens.simulation_workflow import SimulationWorkflowScreen

__all__ = [
    "ConsoleScreen",
    "HelpAboutScreen",
    "HistoryScreen",
    "LiveRunScreen",
    "MainWorkspace",
    "PruneConfirmationModal",
    "ResultsScreen",
    "SimulationWorkflowScreen",
]
