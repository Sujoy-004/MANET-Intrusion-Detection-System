"""Command palette provider exposing registry commands to Textual's palette.

The provider is the palette tail; it exposes ONLY registry commands — the stated
invariant: no provider-local command list, no hardcoded display string, no generic
executor callback (T-7-03).

Command history / recent actions (D-11): the provider itself keeps NO state (no
module-level mutable state — determinism contract). Recency is delegated to the
console driver's history deque in plan 03, which will surface recent commands at
the TOP of discover() when it lands. This plan's discover() yields insertion
order only; recent-order arrives with plan 03's history without a second history
mechanism being invented.
"""

from __future__ import annotations

from typing import Any, Callable

from textual.command import DiscoveryHit, Hit, Hits, Provider

from manet.commands.registry import AppCommand, iter_known


class ManetCommands(Provider):
    """Command palette provider over the single-source MANET IDS command registry."""

    def _make_callback(self, command: AppCommand) -> Callable[[], Any]:
        """Construct a callback dispatching through the command's action on the app instance.

        The only sanctioned interpreter of the action string is getattr-on-app dispatch,
        ensuring all executions route through existing application action methods.

        Args:
            command: The registered AppCommand to dispatch.

        Returns:
            Callable invoking the action method on the app.
        """

        def callback() -> Any:
            action_method = getattr(self.app, command.action)
            return action_method()

        return callback

    async def discover(self) -> Hits:
        """Yield discovery hits for all registry commands in deterministic insertion order.

        Yields:
            DiscoveryHit instances for each known command in iter_known().
        """
        for command in iter_known():
            yield DiscoveryHit(
                command.display,
                self._make_callback(command),
                help=command.help,
            )

    async def search(self, query: str) -> Hits:
        """Search registered commands using Textual fuzzy matching against display titles.

        Args:
            query: The user search input string.

        Yields:
            Hit instances scored > 0 with highlighted match display.
        """
        if not query:
            async for hit in self.discover():
                yield hit
            return

        matcher = self.matcher(query)
        for command in iter_known():
            score = matcher.match(command.display)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(command.display),
                    self._make_callback(command),
                    help=command.help,
                )


__all__ = ["ManetCommands"]
