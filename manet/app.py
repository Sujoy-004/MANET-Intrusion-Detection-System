"""Application composition root for MANET IDS TUI.

Provides the ManetApp class managing screen installation, theme registration,
keyboard navigation, and session lifecycle for the terminal user interface.
"""

from __future__ import annotations

from typing import Any

from textual.app import App
from textual.binding import Binding

from manet.commands.console_driver import ConsoleDriver
from manet.commands.palette_provider import ManetCommands
from manet.runtime.keymap import (
    BINDING_CONSOLE,
    BINDING_HELP,
    BINDING_PALETTE,
    BINDING_QUIT,
)
from manet.runtime.settings import SessionSettings
from manet.runtime.theme import AI_STUDIO_WARM, SOC, SOC_HIGH_CONTRAST
from manet.screens.console import ConsoleScreen
from manet.screens.help_about import HelpAboutScreen
from manet.screens.main_workspace import MainWorkspace
from manet.screens.simulation_workflow import SimulationWorkflowScreen


class ManetApp(App):
    """Main application frame for MANET Intrusion Detection System."""

    TITLE = "MANET IDS"
    COMMANDS = App.COMMANDS | {ManetCommands}
    SCREENS = {
        "workspace": MainWorkspace,
        "console": ConsoleScreen,
        "help": HelpAboutScreen,
        "simulation": SimulationWorkflowScreen,
    }
    BINDINGS = [
        Binding(BINDING_CONSOLE, "show_console", "Console", show=True),
        Binding(BINDING_HELP, "show_help", "Help", show=True),
        Binding(BINDING_PALETTE, "command_palette", "Palette", show=True),
        Binding(BINDING_QUIT, "quit", "Quit", show=True),
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize ManetApp, console driver, and in-memory session settings."""
        super().__init__(*args, **kwargs)
        self.console_driver = ConsoleDriver(self)
        self.settings = SessionSettings()

    def on_mount(self) -> None:
        """Register themes and mount the primary workspace screen."""
        self.register_theme(SOC)
        self.register_theme(SOC_HIGH_CONTRAST)
        self.register_theme(AI_STUDIO_WARM)
        self.theme = "manet-soc"
        self.push_screen("workspace")

    def action_show_workspace(self) -> None:
        """Switch to the primary workspace screen."""
        self.switch_screen("workspace")

    def action_show_console(self) -> None:
        """Switch to the command console screen."""
        self.switch_screen("console")

    def action_show_help(self) -> None:
        """Switch to the contextual help screen."""
        self.switch_screen("help")

    def action_simulation(self) -> None:
        """Switch to simulation workflow wizard screen."""
        self.switch_screen("simulation")

    def action_results(self) -> None:
        """Forward results shortcut to active MainWorkspace screen."""
        if isinstance(self.screen, MainWorkspace):
            self.screen.action_results()

    action_new_simulation = action_simulation
    action_show_results = action_results

    def action_toggle_high_contrast(self) -> None:
        """Toggle between standard SOC and high-contrast themes."""
        self.settings.high_contrast = not self.settings.high_contrast
        self.theme = "manet-soc-high-contrast" if self.settings.high_contrast else "manet-soc"

    def action_toggle_warm_theme(self) -> None:
        """Toggle between dark SOC theme and Google AI Studio warm-white theme."""
        if self.theme == "manet-ai-studio-warm":
            self.theme = "manet-soc"
        else:
            self.theme = "manet-ai-studio-warm"
            self.settings.high_contrast = False

    def action_set_theme(self, theme_name: str) -> None:
        """Switch active theme by name."""
        if theme_name in ("manet-soc", "manet-soc-high-contrast", "manet-ai-studio-warm"):
            self.theme = theme_name
            self.settings.high_contrast = (theme_name == "manet-soc-high-contrast")

    def action_toggle_reduced_motion(self) -> None:
        """Toggle UI motion and animation effects."""
        self.settings.reduced_motion = not self.settings.reduced_motion


__all__ = ["ManetApp"]
