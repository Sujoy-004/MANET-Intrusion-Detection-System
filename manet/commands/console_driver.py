"""Console driver adapting application command registry for interactive console screen.

Provides in-memory history management, tokenization, parameter validation,
and safe dispatch through manet.commands.registry without any OS execution primitives.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import difflib
import shlex
from typing import Any

from manet.commands.registry import AppCommand, iter_known, resolve


@dataclass
class ConsoleResult:
    """Result of attempting to execute a command through ConsoleDriver.

    Attributes:
        success: True if the command was recognized, validated, and dispatched.
        output: Formatted human-readable status, error message, or output.
        command: Matched AppCommand if successfully resolved, else None.
    """

    success: bool
    output: str
    command: AppCommand | None = None


class ConsoleDriver:
    """In-memory driver and execution dispatcher for the command console.

    Maintains a bounded session history deque and dispatches verified application
    commands to the active application instance. Handles the 'exit' meta-command to
    dismiss the console and return to the primary workspace. Never writes history to disk
    and contains zero OS process execution primitives (D-10, T-7-01, Pitfall 5).
    """

    def __init__(self, app: Any, max_history: int = 100) -> None:
        """Initialize ConsoleDriver with target app instance and bounded history.

        Args:
            app: Application instance (ManetApp) hosting action methods.
            max_history: Maximum number of recent command lines kept in memory.
        """
        self.app = app
        self.max_history = max_history
        self.history: deque[str] = deque(maxlen=max_history)
        self._history_index: int = 0

    def execute(self, line: str) -> ConsoleResult:
        """Parse, validate, and dispatch a command line.

        Trims input, tokenizes with shlex, resolves against the application command
        registry, and invokes the matching action on the app instance. Supports the
        case-sensitive 'exit' first-token meta-command to return to the workspace.

        Args:
            line: Raw input string from the console.

        Returns:
            ConsoleResult indicating success/failure and message output.
        """
        stripped = line.strip()
        if not stripped:
            return ConsoleResult(success=True, output="", command=None)

        try:
            tokens = shlex.split(stripped)
        except ValueError:
            tokens = stripped.split()

        if not tokens:
            return ConsoleResult(success=True, output="", command=None)

        name = tokens[0]
        args = tokens[1:]

        if name == "exit":
            self.history.append(stripped)
            self._history_index = len(self.history)
            self.app.action_show_workspace()
            return ConsoleResult(
                success=True,
                output="Returned to workspace.",
                command=None,
            )

        resolved = resolve(name, args)
        if resolved is not None:
            command, params = resolved
            action_name = command.action
            action_fn = getattr(self.app, action_name, None)
            if action_fn is None:
                return ConsoleResult(
                    success=False,
                    output=f"Error: Application action '{action_name}' is not defined.",
                    command=command,
                )

            if params:
                action_fn(**params)
            else:
                action_fn()

            self.history.append(stripped)
            self._history_index = len(self.history)
            return ConsoleResult(
                success=True,
                output=f"Executed: {command.display}",
                command=command,
            )

        known = iter_known()
        matched_cmd = next((c for c in known if c.name == name), None)
        if matched_cmd is not None:
            expected = (
                f"<{', '.join(matched_cmd.parameters)}>"
                if matched_cmd.parameters
                else "no arguments"
            )
            return ConsoleResult(
                success=False,
                output=(
                    f"Parameter mismatch for '{name}'. Expected: {expected} "
                    f"(received {len(args)} arguments)."
                ),
                command=None,
            )

        close_matches = difflib.get_close_matches(name, [c.name for c in known], n=3, cutoff=0.5)
        prefix_matches = [c.name for c in known if c.name.startswith(name)]
        all_suggestions = sorted(set(close_matches + prefix_matches))

        if all_suggestions:
            suggestion_str = f" Did you mean: {', '.join(all_suggestions)}?"
        else:
            suggestion_str = ""

        return ConsoleResult(
            success=False,
            output=f"Unknown command '{name}'.{suggestion_str} Type 'help' or check command palette.",
            command=None,
        )

    def history_prev(self) -> str | None:
        """Navigate backwards to an earlier command in history.

        Returns:
            Earlier command string, or None if history is empty.
        """
        if not self.history:
            return None

        if self._history_index > 0:
            self._history_index -= 1
        return self.history[self._history_index]

    def history_next(self) -> str | None:
        """Navigate forward to a more recent command in history.

        Returns:
            More recent command string, empty string if returning to current line,
            or None if already at current uncommitted line.
        """
        if not self.history:
            return None

        if self._history_index < len(self.history) - 1:
            self._history_index += 1
            return self.history[self._history_index]
        elif self._history_index == len(self.history) - 1:
            self._history_index = len(self.history)
            return ""
        return None


__all__ = ["ConsoleDriver", "ConsoleResult"]
