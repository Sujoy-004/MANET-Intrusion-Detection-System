"""Single-source keymap definitions for MANET IDS TUI application.

Protects the invariant that keybinding strings and human shortcut labels are defined
in a single location and never duplicated inline across screens or widgets.
Framework defaults (ctrl+q for quit, ctrl+p for command palette) are preserved.
"""

from __future__ import annotations

BINDING_CONSOLE = "ctrl+o"
BINDING_HELP = "f1"
BINDING_QUIT = "ctrl+q"
BINDING_PALETTE = "ctrl+p"
BINDING_SIMULATION = "s"
BINDING_RESULTS = "r"
BINDING_LIVE_RUN = "l"
BINDING_STOP = "x"
BINDING_BACKGROUND = "b"

SHORTCUT_HINTS: dict[str, str] = {
    BINDING_CONSOLE: "Open command console",
    BINDING_HELP: "Help and about",
    BINDING_PALETTE: "Command palette",
    BINDING_QUIT: "Quit",
    BINDING_SIMULATION: "Simulation workflow wizard",
    BINDING_RESULTS: "Results notice (Phase 11 pending)",
    BINDING_LIVE_RUN: "View active simulation monitor",
    BINDING_STOP: "Stop active simulation",
    BINDING_BACKGROUND: "Background simulation run",
}

__all__ = [
    "BINDING_CONSOLE",
    "BINDING_HELP",
    "BINDING_PALETTE",
    "BINDING_QUIT",
    "BINDING_SIMULATION",
    "BINDING_RESULTS",
    "BINDING_LIVE_RUN",
    "BINDING_STOP",
    "BINDING_BACKGROUND",
    "SHORTCUT_HINTS",
]
