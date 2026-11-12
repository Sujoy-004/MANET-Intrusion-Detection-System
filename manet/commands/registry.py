"""Single source of truth for MANET IDS application commands.

The registry is the single source of truth for MANET IDS application commands (D-10);
invariant — resolve() returns references to app action methods only; the registry has
no execution primitive, no network, no RNG (determinism contract). Later plans append
commands via the same AppCommand shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class AppCommand:
    """A single application command callable from the palette or console.

    Attributes:
        name: Internal unique identifier for the command (e.g. 'workspace').
        display: Human-readable title shown in palette suggestions and console output.
        help: Concise one-line explanation of what the command does.
        parameters: Sequence of parameter names accepted positionally.
        action: Name of an existing ManetApp action method (string reference only,
            never a callable or executable process).
    """

    name: str
    display: str
    help: str
    parameters: tuple[str, ...]
    action: str


_COMMANDS: tuple[AppCommand, ...] = (
    AppCommand(
        name="workspace",
        display="Go to workspace",
        help="Switch to the main workspace screen",
        parameters=(),
        action="action_show_workspace",
    ),
    AppCommand(
        name="sim:start",
        display="Start Simulation Workflow",
        help="Open the guided simulation wizard to configure preset or custom runs",
        parameters=(),
        action="action_show_simulation",
    ),
    AppCommand(
        name="sim:monitor",
        display="Monitor Simulation",
        help="Open the live simulation monitor screen",
        parameters=(),
        action="action_show_live_run",
    ),
    AppCommand(
        name="sim:stop",
        display="Stop Simulation",
        help="Safely stop the active simulation workload",
        parameters=(),
        action="action_stop_simulation",
    ),
    AppCommand(
        name="theme-toggle",
        display="Toggle High Contrast",
        help="Toggle between standard SOC and high-contrast themes",
        parameters=(),
        action="action_toggle_high_contrast",
    ),
    AppCommand(
        name="theme-warm",
        display="Toggle Google AI Studio Warm Theme",
        help="Toggle between dark SOC and warm-white Google AI Studio theme",
        parameters=(),
        action="action_toggle_warm_theme",
    ),
    AppCommand(
        name="motion-toggle",
        display="Toggle Reduced Motion",
        help="Toggle UI motion and animation effects",
        parameters=(),
        action="action_toggle_reduced_motion",
    ),
    AppCommand(
        name="help",
        display="Help",
        help="Open the help/about screen with app identity and keyboard shortcuts",
        parameters=(),
        action="action_show_help",
    ),
    AppCommand(
        name="view:history",
        display="Browse Session History",
        help="Open session history table to browse past runs",
        parameters=(),
        action="action_show_history",
    ),
    AppCommand(
        name="view:results",
        display="View Experiment Results",
        help="Inspect QoS metrics and artifact integrity for an experiment",
        parameters=(),
        action="action_show_results",
    ),
    AppCommand(
        name="ml:train",
        display="Calculate Champion Model",
        help="Train candidate ML models, evaluate against FPR gate, and persist champion model",
        parameters=(),
        action="action_train_champion_model",
    ),
)


def iter_known() -> tuple[AppCommand, ...]:
    """Return all known application commands in deterministic insertion order.

    Returns:
        Tuple of registered AppCommand instances in insertion order.
    """
    return _COMMANDS


def resolve(name: str, args: Sequence[str] | list[str]) -> tuple[AppCommand, dict[str, str]] | None:
    """Resolve a command name and positional argument list against known commands.

    Exact name matching is enforced without prefix expansion or fuzzy guessing.
    Positional arguments must match the command's parameter count exactly.

    Args:
        name: Command identifier string to match.
        args: Positional parameter strings provided by caller.

    Returns:
        Tuple of (matched_command, parsed_parameters_dict), or None if the command
        name is unknown or the argument count does not match command parameters.
    """
    for cmd in _COMMANDS:
        if cmd.name == name:
            if len(args) != len(cmd.parameters):
                return None
            params_dict = dict(zip(cmd.parameters, args))
            return cmd, params_dict
    return None


__all__ = ["AppCommand", "iter_known", "resolve"]
