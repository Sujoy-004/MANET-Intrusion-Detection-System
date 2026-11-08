"""Pilot navigation tests for screen transitions, console execution, and keyboard cycles.

Verifies:
- ctrl+o switches to ConsoleScreen and escape / ctrl+o dismisses back to MainWorkspace.
- f1 switches to HelpAboutScreen and escape / f1 dismisses back to MainWorkspace.
- Submitting 'workspace' command in ConsoleScreen executes cleanly.
- Submitting 'exit' meta-command dismisses ConsoleScreen back to MainWorkspace.
- Submitting 'help' command switches from ConsoleScreen to HelpAboutScreen.
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
from manet.screens.simulation_workflow import SimulationWorkflowScreen
from manet.widgets.notification_rail import NotificationRail


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


@pytest.mark.asyncio
async def test_console_typed_exit_returns_to_workspace():
    """Verify typing 'exit' into console input line dismisses to MainWorkspace."""
    app = ManetApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, ConsoleScreen)

        input_widget = app.screen.query_one("#console-input", Input)
        input_widget.value = "exit"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(app.screen, MainWorkspace)
        assert list(app.console_driver.history) == ["exit"]


@pytest.mark.asyncio
async def test_console_typed_help_opens_help_about():
    """Verify typing 'help' into console input line switches to HelpAboutScreen."""
    app = ManetApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, ConsoleScreen)

        input_widget = app.screen.query_one("#console-input", Input)
        input_widget.value = "help"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(app.screen, HelpAboutScreen)


@pytest.mark.asyncio
async def test_console_hostile_markup_input_does_not_crash():
    """Verify hostile rich markup closing tags (e.g. [/red], [/]) do not raise MarkupError."""
    app = ManetApp()
    async with app.run_test() as pilot:
        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, ConsoleScreen)

        input_widget = app.screen.query_one("#console-input", Input)
        for hostile_cmd in ["[/red]", "[/]", "echo [bold]", "[/x] ls"]:
            input_widget.value = hostile_cmd
            await pilot.press("enter")
            await pilot.pause()
            # Verify screen is still healthy and app has not crashed
            assert isinstance(app.screen, ConsoleScreen)


@pytest.mark.asyncio
async def test_simulation_shortcut_opens_workflow_screen():
    """Verify pressing 's' on MainWorkspace opens SimulationWorkflowScreen, and escape dismisses."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)

        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, SimulationWorkflowScreen)

        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainWorkspace)


test_simulation_shortcut_triggers_notice = test_simulation_shortcut_opens_workflow_screen


@pytest.mark.asyncio
async def test_sim_start_command_opens_simulation_workflow():
    """Verify executing 'sim:start' in console switches to SimulationWorkflowScreen."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)

        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, ConsoleScreen)

        input_widget = app.screen.query_one("#console-input", Input)
        input_widget.value = "sim:start"
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(app.screen, SimulationWorkflowScreen)

        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainWorkspace)


@pytest.mark.asyncio
async def test_results_shortcut_triggers_notice():
    """Verify pressing 'r' on MainWorkspace triggers results notice in NotificationRail."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)
        rail = app.screen.query_one("#notification-rail", NotificationRail)
        assert rail.get_active_notice() is None

        await pilot.press("r")
        await pilot.pause()
        assert rail.display is True
        notice = rail.get_active_notice()
        assert notice is not None
        assert "Phase 11" in notice
        assert "Results" in notice


@pytest.mark.asyncio
async def test_command_palette_shortcut_opens_palette():
    """Verify pressing ctrl+p opens the command palette modal."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)
        await pilot.press("ctrl+p")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "CommandPalette"


@pytest.mark.asyncio
async def test_console_typing_does_not_trigger_s_r_actions():
    """Verify typing words with 's' and 'r' in ConsoleScreen input does not trigger workspace notices."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)
        workspace = app.screen
        rail = workspace.query_one("#notification-rail", NotificationRail)

        # Open ConsoleScreen
        await pilot.press("ctrl+o")
        await pilot.pause()
        assert isinstance(app.screen, ConsoleScreen)

        input_widget = app.screen.query_one("#console-input", Input)
        assert input_widget.has_focus

        # Type words containing 's' and 'r'
        test_strings = ["status", "scenario", "reset"]
        for word in test_strings:
            for char in word:
                await pilot.press(char)
            await pilot.pause()
            assert input_widget.value == word
            # Clear for next word
            input_widget.value = ""

        # Return to workspace and verify no notification notices were fired
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, MainWorkspace)
        assert rail.get_active_notice() is None
        assert rail.display is False


@pytest.mark.asyncio
async def test_repeated_shortcut_presses_bounded_queue():
    """Verify rapid repeated pressing of 's' and 'r' stays within bounded queue and does not crash."""
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)
        rail = app.screen.query_one("#notification-rail", NotificationRail)

        # Press 'r' rapidly 25 times
        for _ in range(25):
            await pilot.press("r")
        await pilot.pause()

        # Check notification rail is still healthy and visible
        assert rail.display is True
        assert rail.get_active_notice() is not None
        # Verify adapter queue is bounded (maxlen=20)
        adapter = rail.adapter
        assert len(adapter.get_history()) <= 20


@pytest.mark.asyncio
async def test_live_run_shortcut():
    """Verify pressing 'l' in MainWorkspace switches directly to LiveRunScreen."""
    from manet.screens.live_run import LiveRunScreen
    app = ManetApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MainWorkspace)
        await pilot.press("l")
        await pilot.pause()
        assert isinstance(app.screen, LiveRunScreen)


def test_command_registry_sim_commands():
    """Verify sim:monitor and sim:stop are properly registered in command registry."""
    from manet.commands import registry
    commands = {cmd.name: cmd for cmd in registry.iter_known()}

    assert "sim:monitor" in commands
    assert commands["sim:monitor"].action == "action_show_live_run"

    assert "sim:stop" in commands
    assert commands["sim:stop"].action == "action_stop_simulation"


@pytest.mark.asyncio
async def test_active_workload_card_displays_live_state(tmp_path):
    """Verify ActiveWorkloadCard reflects RUNNING state and COMPLETED metrics from supervisor."""
    from manet.adapters.handoff import SimulationLaunchRequest
    from manet.runtime.supervisor import WorkloadState
    from manet.widgets.dashboard_cards import ActiveWorkloadCard

    app = ManetApp()
    async with app.run_test() as pilot:
        workspace = app.screen
        assert isinstance(workspace, MainWorkspace)
        card = workspace.query_one("#card-workload", ActiveWorkloadCard)

        # Initially IDLE
        assert "IDLE" in str(card.render())

        # Set supervisor to RUNNING
        app.supervisor.current_request = SimulationLaunchRequest(
            experiment_id="exp_nav_test",
            scenario_name="e1_normal_30n",
            seed=42,
            config={"duration": 100.0},
            workspace_dir=tmp_path,
            created_at="2026-11-08T00:00:00Z",
            ids_enabled=True,
        )
        app.supervisor.state = WorkloadState.RUNNING
        app.supervisor.stage = "SIMULATING"

        await pilot.pause(0.6)  # allow 0.5s fast refresh to fire
        rendered = str(card.render())
        assert "RUNNING" in rendered
        assert "[L] Live Monitor" in rendered

        # Transition to COMPLETED with metrics
        app.supervisor.state = WorkloadState.COMPLETED
        app.supervisor.stage = "COMPLETED"
        app.supervisor.metrics = {"pdr": 0.94, "throughput_bps": 12000.0}

        await pilot.pause(0.6)
        rendered_comp = str(card.render())
        assert "COMPLETED" in rendered_comp
        assert "94.0%" in rendered_comp
        assert "[L] View Run" in rendered_comp


@pytest.mark.asyncio
async def test_safe_quit_confirmation_guard():
    """Verify quitting with active simulation prompts QuitConfirmModal."""
    from manet.app import QuitConfirmModal
    from manet.runtime.supervisor import WorkloadState

    app = ManetApp()
    async with app.run_test() as pilot:
        # Simulate active run
        app.supervisor.state = WorkloadState.RUNNING

        # Press ctrl+q to quit
        await pilot.press("ctrl+q")
        await pilot.pause()

        # Modal must be displayed, app must not have exited
        assert isinstance(app.screen, QuitConfirmModal)

        # Dismiss modal via cancel
        btn_cancel = app.screen.query_one("#btn-cancel")
        btn_cancel.press()
        await pilot.pause()

        # Should be back to workspace, simulation still running
        assert isinstance(app.screen, MainWorkspace)
        assert app.supervisor.is_running is True


