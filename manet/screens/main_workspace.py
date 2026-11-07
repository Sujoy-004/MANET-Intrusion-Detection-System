"""Primary workspace shell screen for MANET IDS TUI.

Provides the foundational layout composing Header, centered content panel, and Footer.
All styling references theme variables; no hex color literals are defined directly in screens.
Implements HORIZONTAL_BREAKPOINTS for responsive layout adaptation in compact terminal windows (D-18, TUI-02).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


WORKSPACE_CONTENT = (
    "[bold $primary]MANET INTRUSION DETECTION SYSTEM[/]\n"
    "[dim]Session Control & Operational Workspace[/]\n\n"
    "[dim]───────────────────────────────────────────────[/]\n\n"
    "[bold]Topology State:[/]       [green]Online (AODV Active)[/]\n"
    "[bold]IDS Monitoring:[/]       [cyan]Ready[/]\n"
    "[bold]Active Threat Level:[/]  [green]Nominal[/]\n\n"
    "[dim]───────────────────────────────────────────────[/]\n\n"
    "[dim]Press [bold $primary]Ctrl+P[/] for Command Palette[/]\n"
    "[dim]Press [bold $primary]Ctrl+O[/] for Interactive Console[/]\n"
    "[dim]Press [bold $primary]F1[/] for Shortcuts & System Help[/]"
)


class MainWorkspace(Screen):
    """Primary workspace screen hosting the MANET IDS session shell."""

    HORIZONTAL_BREAKPOINTS = [(0, "-compact"), (80, "-normal")]

    CSS = """
    $info-blue: $secondary;
    $navigation-cyan: $primary;

    MainWorkspace {
        align: center middle;
        background: $background;
    }

    #workspace-box {
        width: 90%;
        max-width: 64;
        height: auto;
        border: solid $info-blue;
        color: $foreground;
        background: $surface;
        text-align: center;
    }

    Screen.-compact Static#workspace-box {
        padding: 0 1;
        margin: 0;
    }

    Screen.-normal Static#workspace-box {
        padding: 1 2;
        margin: 1 2;
    }

    #workspace-box:focus {
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
            WORKSPACE_CONTENT,
            id="workspace-box",
        )
        yield Footer()


__all__ = ["MainWorkspace"]
