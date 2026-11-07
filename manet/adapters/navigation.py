"""Navigation adapter defining quick action navigation targets and shortcuts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavigationTarget:
    """Action shortcut target for quick workspace navigation."""

    id: str
    shortcut: str
    label: str
    description: str


QUICK_ACTIONS: tuple[NavigationTarget, ...] = (
    NavigationTarget(
        id="simulation",
        shortcut="s",
        label="Simulation (Phase 9 Notice)",
        description="Configure and launch MANET simulation scenarios",
    ),
    NavigationTarget(
        id="results",
        shortcut="r",
        label="Results (Phase 11 Notice)",
        description="Browse experiment records and evaluation reports",
    ),
    NavigationTarget(
        id="console",
        shortcut="ctrl+o",
        label="Console (Logs & Diagnostics)",
        description="Interactive session log and diagnostics console",
    ),
    NavigationTarget(
        id="palette",
        shortcut="ctrl+p",
        label="Command Palette",
        description="Global command search and action palette",
    ),
    NavigationTarget(
        id="help",
        shortcut="f1",
        label="Help & Shortcuts",
        description="Key bindings and system documentation",
    ),
)


class NavigationAdapter:
    """Provides navigation targets and quick action metadata."""

    def get_quick_actions(self) -> tuple[NavigationTarget, ...]:
        """Return all defined quick navigation actions."""
        return QUICK_ACTIONS

    def get_action_by_id(self, action_id: str) -> NavigationTarget | None:
        """Find a navigation action by its identifier."""
        for action in QUICK_ACTIONS:
            if action.id == action_id:
                return action
        return None


__all__ = ["NavigationAdapter", "NavigationTarget", "QUICK_ACTIONS"]
