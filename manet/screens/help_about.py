"""Help and about screen displaying application metadata and shortcut cheat sheet.

Provides a structured informational overview of application identity, version,
and global keyboard shortcuts defined across the application frame.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from manet.runtime.keymap import BINDING_HELP, SHORTCUT_HINTS


class HelpAboutScreen(Screen):
    """Contextual help and application identity screen."""

    BINDINGS = [
        Binding("escape", "dismiss_help", "Close"),
        Binding(BINDING_HELP, "dismiss_help", "Close"),
    ]

    CSS = """
    $info-blue: $secondary;
    $navigation-cyan: $primary;

    HelpAboutScreen {
        align: center middle;
        background: $background;
    }

    .help-container {
        width: 70;
        height: auto;
        max-height: 80%;
        border: solid $info-blue;
        background: $surface;
        padding: 1 2;
    }

    .help-title {
        text-align: center;
        color: $navigation-cyan;
        text-style: bold;
        margin-bottom: 1;
    }

    .help-subtitle {
        text-align: center;
        color: $foreground;
        margin-bottom: 1;
    }

    .table-header {
        text-align: center;
        color: $info-blue;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }

    #shortcuts-table {
        height: auto;
        max-height: 12;
        background: $surface;
    }

    #shortcuts-table:focus {
        border: double $navigation-cyan;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the help and about screen layout."""
        yield Header()
        with Vertical(classes="help-container"):
            yield Static("MANET IDS — Version 2.0.0-dev", classes="help-title")
            yield Static(
                "Software-based Intrusion Detection & Response System for MANETs",
                classes="help-subtitle",
            )
            yield Static("Keyboard Shortcut Cheat Sheet", classes="table-header")
            yield DataTable(id="shortcuts-table")
        yield Footer()

    def on_mount(self) -> None:
        """Populate the keyboard shortcut table on mount."""
        table = self.query_one("#shortcuts-table", DataTable)
        table.add_columns("Shortcut", "Action / Description")
        for key, desc in SHORTCUT_HINTS.items():
            table.add_row(key, desc)
        table.focus()

    def action_dismiss_help(self) -> None:
        """Return to the primary workspace screen."""
        self.app.switch_screen("workspace")


__all__ = ["HelpAboutScreen"]
