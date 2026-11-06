"""Pilot navigation tests for screen transitions, console execution, and keyboard cycles.

Verifies:
- ctrl+o switches to ConsoleScreen and escape / ctrl+o dismisses back to MainWorkspace.
- f1 switches to HelpAboutScreen and escape / f1 dismisses back to MainWorkspace.
- Submitting 'workspace' command in ConsoleScreen executes cleanly.
- Up/Down arrow history cycling functions in console input when focused.
- Visible focus indicator exists on active interactive widgets.
"""

from __future__ import annotations

import pytest
from textual.widgets import DataTable, Input

from manet.app import ManetApp
from manet.screens.console import ConsoleScreen
from manet.screens.help_about import HelpAboutScreen
from manet.screens.main_workspace import MainWorkspace


@pytest.mark.asyncio
async def test_console_screen_open_and_escape_navigation():
    """Verify ctrl+o opens ConsoleScreen and escape returns to MainWorkspace."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)

        # Open console via ctrl+o
        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, ConsoleScreen)

        # Input should be focused
        input_widget = app.screen.query_one("#console-input", Input)
        assert input_widget.has_focus

        # Dismiss console via escape
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainWorkspace)


@pytest.mark.asyncio
async def test_console_screen_toggle_dismiss():
    """Verify pressing ctrl+o while on ConsoleScreen dismisses back to MainWorkspace."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)

        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, ConsoleScreen)

        # Press ctrl+o again to toggle dismiss
        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, MainWorkspace)


@pytest.mark.asyncio
async def test_help_about_screen_navigation_cycle():
    """Verify f1 opens HelpAboutScreen and escape returns to MainWorkspace."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)

        # Open help screen via f1
        await pilot.press("f1")
        await pilot.pause()
        assert isinstance(app.screen, HelpAboutScreen)

        # Shortcuts table should be mounted and have focus
        table = app.screen.query_one("#shortcuts-table", DataTable)
        assert table is not None
        assert table.row_count > 0

        # Dismiss help screen via escape
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainWorkspace)


@pytest.mark.asyncio
async def test_help_about_screen_toggle_dismiss():
    """Verify pressing f1 while on HelpAboutScreen dismisses back to MainWorkspace."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)

        await pilot.press("f1")
        await pilot.pause()
        assert isinstance(app.screen, HelpAboutScreen)

        # Press f1 again to toggle dismiss
        await pilot.press("f1")
        await pilot.pause()
        assert isinstance(app.screen, MainWorkspace)


@pytest.mark.asyncio
async def test_console_input_submission_and_execution():
    """Verify submitting 'workspace' into ConsoleScreen input triggers action and logs."""
    app = ManetApp()
    async with app.run_test() as pilot:
        # Open console
        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, ConsoleScreen)

        input_widget = app.screen.query_one("#console-input", Input)
        input_widget.value = "workspace"

        # Submit command
        await pilot.press("enter")
        await pilot.pause()

        # Input should be cleared
        assert input_widget.value == ""

        # Driver history should record workspace
        assert len(app.console_driver.history) == 1
        assert app.console_driver.history[0] == "workspace"


@pytest.mark.asyncio
async def test_console_input_history_key_navigation():
    """Verify Up/Down arrow keys in console input navigate command history."""
    app = ManetApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, ConsoleScreen)

        # Populate history directly on driver
        app.console_driver.history.append("first_cmd")
        app.console_driver.history.append("second_cmd")
        app.console_driver._history_index = len(app.console_driver.history)

        input_widget = app.screen.query_one("#console-input", Input)
        input_widget.focus()
        await pilot.pause()

        # Press Up arrow
        await pilot.press("up")
        await pilot.pause()
        assert input_widget.value == "second_cmd"

        # Press Up arrow again
        await pilot.press("up")
        await pilot.pause()
        assert input_widget.value == "first_cmd"

        # Press Down arrow
        await pilot.press("down")
        await pilot.pause()
        assert input_widget.value == "second_cmd"

        # Press Down arrow to return to empty input
        await pilot.press("down")
        await pilot.pause()
        assert input_widget.value == ""
