"""Primary workspace shell screen for MANET IDS TUI.

Provides the foundational layout composing Header, centered content panel, and Footer.
All styling references theme variables; no hex color literals are defined directly in screens.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


class MainWorkspace(Screen):
    """Primary workspace screen hosting the MANET IDS session shell."""

    CSS = """
    $info-blue: $secondary;
    $navigation-cyan: $primary;

    MainWorkspace {
        align: center middle;
    }

    #workspace-content {
        width: 60;
        height: auto;
        border: solid $info-blue;
        color: $foreground;
        background: $surface;
        padding: 1 2;
        text-align: center;
    }

    #workspace-content:focus {
        border: double $navigation-cyan;
    }

    *:focus {
        border: solid $navigation-cyan;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the primary shell layout."""
        yield Header()
        yield Static(
            "MANET IDS\nSession shell workspace",
            id="workspace-content",
        )
        yield Footer()


__all__ = ["MainWorkspace"]
