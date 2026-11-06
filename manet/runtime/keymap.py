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

SHORTCUT_HINTS: dict[str, str] = {
    BINDING_CONSOLE: "Open command console",
    BINDING_HELP: "Help and about",
    BINDING_PALETTE: "Command palette",
    BINDING_QUIT: "Quit",
}

__all__ = [
    "BINDING_CONSOLE",
    "BINDING_HELP",
    "BINDING_PALETTE",
    "BINDING_QUIT",
    "SHORTCUT_HINTS",
]
