"""Headless launch verification tests for MANET IDS TUI application.

Verifies:
- Application mounts headlessly via run_test() with exact title "MANET IDS"
- Active theme registers and applies "manet-soc" with SOC color variables
- Primary screen initializes as a MainWorkspace instance
- Footer widget is present on the mounted workspace screen
- Single-source keymap definitions exist in manet.runtime.keymap
"""

from __future__ import annotations

import pytest

from manet.app import ManetApp
from manet.runtime.keymap import (
    BINDING_CONSOLE,
    BINDING_HELP,
    BINDING_PALETTE,
    BINDING_QUIT,
    SHORTCUT_HINTS,
)
from manet.screens.main_workspace import MainWorkspace


async def test_manet_app_headless_launch():
    """Verify ManetApp mounts headlessly with title, theme, and workspace screen."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert app.TITLE == "MANET IDS", f"Expected TITLE 'MANET IDS', got {app.TITLE}"
        assert app.theme == "manet-soc", f"Expected theme 'manet-soc', got {app.theme}"
        assert isinstance(
            app.screen, MainWorkspace
        ), f"Expected screen to be MainWorkspace, got {type(app.screen)}"
        footers = list(app.screen.query("Footer"))
        assert len(footers) >= 1, "Expected at least one Footer widget mounted on workspace screen"


def test_keymap_constants_defined():
    """Verify single-source keymap constants and shortcut hints are defined."""
    assert BINDING_CONSOLE == "ctrl+o"
    assert BINDING_HELP == "f1"
    assert BINDING_QUIT == "ctrl+q"
    assert BINDING_PALETTE == "ctrl+p"

    assert BINDING_CONSOLE in SHORTCUT_HINTS
    assert BINDING_HELP in SHORTCUT_HINTS
    assert BINDING_PALETTE in SHORTCUT_HINTS
    assert BINDING_QUIT in SHORTCUT_HINTS

    assert SHORTCUT_HINTS[BINDING_CONSOLE] == "Open command console"
    assert SHORTCUT_HINTS[BINDING_HELP] == "Help and about"
    assert SHORTCUT_HINTS[BINDING_PALETTE] == "Command palette"
    assert SHORTCUT_HINTS[BINDING_QUIT] == "Quit"
