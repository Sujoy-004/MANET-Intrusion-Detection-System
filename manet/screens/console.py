"""Command console screen for interactive application command execution.

Provides a full-screen non-modal command console hosting an output log buffer,
interactive input line, in-memory history traversal, and safe dispatch through
the application console driver.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog, Static

from manet.runtime.keymap import BINDING_CONSOLE

if TYPE_CHECKING:
    from manet.commands.console_driver import ConsoleDriver


class ConsoleScreen(Screen):
    """Full-screen interactive command console."""

    BINDINGS = [
        Binding("escape", "dismiss_console", "Close"),
        Binding(BINDING_CONSOLE, "dismiss_console", "Close"),
    ]

    CSS = """
    $info-blue: $secondary;
    $navigation-cyan: $primary;

    ConsoleScreen {
        layout: vertical;
        background: $background;
    }

    .console-header {
        dock: top;
        padding: 1 2;
        background: $panel;
        color: $navigation-cyan;
        text-style: bold;
    }

    #console-log {
        height: 1fr;
        background: $surface;
        border: solid $panel;
        padding: 0 1;
        color: $foreground;
    }

    #console-input {
        dock: bottom;
        margin: 1 0 0 0;
        border: tall $navigation-cyan;
        background: $surface;
        color: $foreground;
    }

    #console-input:focus {
        border: tall $navigation-cyan;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the console screen layout."""
        yield Header()
        yield Static(
            "Command Console — Type application commands or 'help'",
            classes="console-header",
        )
        yield RichLog(id="console-log", highlight=True, markup=True)
        yield Input(placeholder="Enter command...", id="console-input")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the command input widget on mount."""
        input_widget = self.query_one("#console-input", Input)
        input_widget.focus()

    def action_dismiss_console(self) -> None:
        """Return to the primary workspace screen."""
        self.app.switch_screen("workspace")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission from the input field."""
        command_line = event.value
        event.input.value = ""

        if not command_line.strip():
            return

        log = self.query_one("#console-log", RichLog)
        log.write(f"> [bold cyan]{command_line}[/]")

        driver: ConsoleDriver | None = getattr(self.app, "console_driver", None)
        if driver is None:
            log.write("[red]Error: Console driver is not available on application.[/]")
            return

        result = driver.execute(command_line)
        if result.success:
            if result.output:
                log.write(f"[green]{result.output}[/]")
        else:
            log.write(f"[red]{result.output}[/]")

    def on_key(self, event: events.Key) -> None:
        """Intercept Up/Down arrow keys in input for history navigation."""
        if event.key in ("up", "down"):
            input_widget = self.query_one("#console-input", Input)
            if input_widget.has_focus:
                driver: ConsoleDriver | None = getattr(self.app, "console_driver", None)
                if driver is None:
                    return

                if event.key == "up":
                    nav_val = driver.history_prev()
                else:
                    nav_val = driver.history_next()

                if nav_val is not None:
                    input_widget.value = nav_val
                    input_widget.cursor_position = len(nav_val)
                    event.stop()
                    event.prevent_default()


__all__ = ["ConsoleScreen"]
