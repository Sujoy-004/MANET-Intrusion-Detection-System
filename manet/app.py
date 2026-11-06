"""Application composition root for MANET IDS TUI.

Provides the ManetApp class managing screen installation, theme registration,
and session lifecycle for the terminal user interface.
"""

from __future__ import annotations

from textual.app import App

from manet.runtime.theme import SOC
from manet.screens.main_workspace import MainWorkspace


class ManetApp(App):
    """Main application frame for MANET Intrusion Detection System."""

    TITLE = "MANET IDS"
    SCREENS = {
        "workspace": MainWorkspace,
    }

    def on_mount(self) -> None:
        """Register themes and mount the primary workspace screen."""
        self.register_theme(SOC)
        self.theme = "manet-soc"
        self.push_screen("workspace")

    def action_show_workspace(self) -> None:
        """Switch to the primary workspace screen."""
        self.switch_screen("workspace")



__all__ = ["ManetApp"]
