"""Quick action navigation rail widget for the operational workspace."""

from __future__ import annotations

from textual.widgets import Static

from manet.adapters.navigation import NavigationAdapter


class NavRail(Static):
    """Panel displaying workspace navigation shortcuts and quick action guidance."""

    def __init__(
        self,
        *args,
        adapter: NavigationAdapter | None = None,
        id: str | None = "nav-rail-panel",
        classes: str | None = None,
        **kwargs,
    ) -> None:
        self.adapter = adapter or NavigationAdapter()
        super().__init__("", *args, id=id, classes=classes, **kwargs)
        self.render_actions()

    def render_actions(self) -> None:
        """Format and render quick actions with honest capability labels."""
        actions = self.adapter.get_quick_actions()
        lines: list[str] = [
            "[bold $primary]Quick Navigation[/]",
            "[dim]Workspace Shortcuts & Actions[/]\n",
        ]

        for action in actions:
            shortcut_display = f"[bold $navigation-cyan]\\[{action.shortcut.upper()}][/]"
            lines.append(f"{shortcut_display} {action.label}")
            lines.append(f"  [dim]{action.description}[/]")

        self.update("\n".join(lines))


__all__ = ["NavRail"]
