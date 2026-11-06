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
from manet.runtime.keymap import BINDING_CONSOLE, BINDING_HELP, BINDING_QUIT
from manet.runtime.theme import SOC
from manet.screens.console import ConsoleScreen
from manet.screens.help_about import HelpAboutScreen
from manet.screens.main_workspace import MainWorkspace


class ManetApp(App):
    """Main application frame for MANET Intrusion Detection System."""

    TITLE = "MANET IDS"
    COMMANDS = App.COMMANDS | {ManetCommands}
    SCREENS = {
        "workspace": MainWorkspace,
        "console": ConsoleScreen,
        "help": HelpAboutScreen,
    }
    BINDINGS = [
        Binding(BINDING_CONSOLE, "show_console", "Console", show=True),
        Binding(BINDING_HELP, "show_help", "Help", show=True),
        Binding(BINDING_QUIT, "quit", "Quit", show=True),
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize ManetApp and in-memory console driver."""
        super().__init__(*args, **kwargs)
        self.console_driver = ConsoleDriver(self)

    def on_mount(self) -> None:
        """Register themes and mount the primary workspace screen."""
        self.register_theme(SOC)
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


__all__ = ["ManetApp"]
