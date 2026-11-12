"""Application composition root for MANET IDS TUI.

Provides the ManetApp class managing screen installation, theme registration,
keyboard navigation, and session lifecycle for the terminal user interface.
"""

from __future__ import annotations

from typing import Any, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.timer import Timer
from textual.widgets import Button, Static

from manet.adapters.workspace import WorkspaceAdapter
from manet.commands.console_driver import ConsoleDriver
from manet.commands.palette_provider import ManetCommands
from manet.runtime.keymap import (
    BINDING_CONSOLE,
    BINDING_HELP,
    BINDING_PALETTE,
    BINDING_QUIT,
)
from manet.runtime.settings import SessionSettings
from manet.runtime.supervisor import WorkloadState, WorkloadSupervisor
from manet.runtime.theme import AI_STUDIO_WARM, SOC, SOC_HIGH_CONTRAST
from manet.screens.console import ConsoleScreen
from manet.screens.help_about import HelpAboutScreen
from manet.screens.history import HistoryScreen
from manet.screens.live_run import LiveRunScreen
from manet.screens.main_workspace import MainWorkspace
from manet.screens.results import ResultsScreen
from manet.screens.simulation_workflow import SimulationWorkflowScreen


class QuitConfirmModal(ModalScreen[bool]):
    """Modal dialog prompting user to confirm exit while a simulation is active."""

    CSS = """
    QuitConfirmModal {
        align: center middle;
    }

    #quit-dialog {
        width: 60;
        height: auto;
        border: thick #f85149;
        background: #161b22;
        padding: 1 2;
    }

    #quit-buttons {
        layout: horizontal;
        align: right middle;
        margin-top: 1;
        height: 3;
    }

    #quit-buttons Button {
        margin-left: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="quit-dialog"):
            yield Static("[bold #f85149]ACTIVE SIMULATION RUNNING[/]\n")
            yield Static(
                "A simulation workload is currently active in the background.\n"
                "Exiting will halt the simulation. Partial traces will be preserved.\n\n"
                "Are you sure you want to stop the simulation and quit?"
            )
            with Horizontal(id="quit-buttons"):
                yield Button("Cancel", id="btn-cancel", variant="default")
                yield Button("Stop & Quit", id="btn-confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class ShutdownErrorModal(ModalScreen[None]):
    """Modal dialog displaying error encountered during simulation shutdown finalization."""

    CSS = """
    ShutdownErrorModal {
        align: center middle;
    }

    #error-dialog {
        width: 64;
        height: auto;
        border: thick #f85149;
        background: #161b22;
        padding: 1 2;
    }

    #error-buttons {
        layout: horizontal;
        align: right middle;
        margin-top: 1;
        height: 3;
    }

    #error-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(self, error_message: str) -> None:
        super().__init__()
        self.error_message = error_message

    def compose(self) -> ComposeResult:
        with Vertical(id="error-dialog"):
            yield Static("[bold red]SIMULATION FINALIZATION FAILED[/]\n")
            yield Static(
                f"Error during shutdown finalization:\n[red]{self.error_message}[/]\n\n"
                "You can force exit now or dismiss to inspect state."
            )
            with Horizontal(id="error-buttons"):
                yield Button("Dismiss", id="btn-dismiss", variant="default")
                yield Button("Force Exit", id="btn-force-exit", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-force-exit":
            self.app.exit(1)
        else:
            self.dismiss()


class ManetApp(App):
    """Main application frame for MANET Intrusion Detection System."""

    TITLE = "MANET IDS"
    COMMANDS = App.COMMANDS | {ManetCommands}
    SCREENS = {
        "workspace": MainWorkspace,
        "console": ConsoleScreen,
        "help": HelpAboutScreen,
        "history": HistoryScreen,
        "results": ResultsScreen,
        "simulation": SimulationWorkflowScreen,
        "simulation_workflow": SimulationWorkflowScreen,
        "live_run": LiveRunScreen,
    }
    BINDINGS = [
        Binding(BINDING_CONSOLE, "show_console", "Console", show=True),
        Binding(BINDING_HELP, "show_help", "Help", show=True),
        Binding(BINDING_PALETTE, "command_palette", "Palette", show=True),
        Binding(BINDING_QUIT, "quit", "Quit", show=True, priority=True),
        Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
    ]

    def __init__(
        self,
        *args: Any,
        executor: Optional[Any] = None,
        model_trainer: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize ManetApp, supervisor, console driver, model trainer, and in-memory session settings."""
        super().__init__(*args, **kwargs)
        self.supervisor = WorkloadSupervisor(executor=executor)
        self.model_trainer = model_trainer
        self.console_driver = ConsoleDriver(self)
        self.settings = SessionSettings()
        self._shutdown_timer: Optional[Timer] = None

    def on_mount(self) -> None:
        """Register themes and mount the primary workspace screen."""
        self.register_theme(SOC)
        self.register_theme(SOC_HIGH_CONTRAST)
        self.register_theme(AI_STUDIO_WARM)
        self.theme = "manet-soc"
        self.push_screen("workspace")

    def action_show_workspace(self) -> None:
        """Switch to the primary workspace screen."""
        self.switch_screen("workspace")

    def action_show_console(self) -> None:
        """Switch to the command console screen."""
        self.switch_screen("console")

    def action_show_help(self) -> None:
        """Switch to the contextual help screen."""
        self.switch_screen("help")

    def action_show_simulation(self) -> None:
        """Switch to simulation workflow wizard screen."""
        self.switch_screen("simulation_workflow")

    def action_show_live_run(self) -> None:
        """Switch to live simulation monitor screen."""
        self.switch_screen("live_run")

    def action_stop_simulation(self) -> None:
        """Trigger cooperative cancellation of the active simulation."""
        if hasattr(self, "supervisor") and self.supervisor.is_running:
            self.supervisor.cancel_simulation()

    def action_quit(self) -> None:
        """Safe non-blocking quit action with active simulation confirmation."""
        if hasattr(self, "supervisor") and self.supervisor.is_running:
            self.push_screen(QuitConfirmModal(), self._handle_quit_confirm)
        else:
            self.exit()

    def _handle_quit_confirm(self, confirmed: bool | None) -> None:
        """Handle quit confirmation modal result."""
        if not confirmed:
            return

        self.action_stop_simulation()
        self._shutdown_timer = self.set_interval(0.1, self._poll_shutdown)

    def _poll_shutdown(self) -> None:
        """Asynchronously monitor shutdown without blocking the Textual event loop."""
        if not self.supervisor.is_running:
            if self._shutdown_timer is not None:
                self._shutdown_timer.stop()
                self._shutdown_timer = None

            if self.supervisor.state == WorkloadState.FAILED and self.supervisor.last_error:
                self.push_screen(ShutdownErrorModal(self.supervisor.last_error))
            else:
                self.exit()

    def action_simulation(self) -> None:
        """Switch to simulation workflow wizard screen."""
        self.switch_screen("simulation_workflow")

    def action_show_history(self) -> None:
        """Open session history browser."""
        try:
            self.push_screen("history")
        except Exception:
            try:
                self.switch_screen("history")
            except Exception:
                pass

    def action_show_results(self, experiment_id: str | None = None) -> None:
        """Open results for an experiment, or latest completed run."""
        if experiment_id is None:
            try:
                recent_runs = WorkspaceAdapter().list_recent_experiments(limit=None)
            except Exception:
                recent_runs = []
            completed = next((r for r in recent_runs if r.status == "COMPLETED"), None)
            if completed is None:
                try:
                    self.notify(
                        "[bold yellow]No completed experiment records found in workspace.[/]",
                        severity="warning",
                    )
                except Exception:
                    pass
                try:
                    self.push_screen("history")
                except Exception:
                    try:
                        self.switch_screen("history")
                    except Exception:
                        pass
                return
            experiment_id = completed.experiment_id
        try:
            self.push_screen(ResultsScreen(experiment_id=experiment_id))
        except Exception:
            pass

    def action_results(self) -> None:
        """Open session history (TUI-21 / D-02)."""
        self.action_show_history()

    action_new_simulation = action_show_simulation

    def action_toggle_high_contrast(self) -> None:
        """Toggle between standard SOC and high-contrast themes."""
        self.settings.high_contrast = not self.settings.high_contrast
        self.theme = "manet-soc-high-contrast" if self.settings.high_contrast else "manet-soc"

    def action_toggle_warm_theme(self) -> None:
        """Toggle between dark SOC theme and Google AI Studio warm-white theme."""
        if self.theme == "manet-ai-studio-warm":
            self.theme = "manet-soc"
        else:
            self.theme = "manet-ai-studio-warm"
            self.settings.high_contrast = False

    def action_set_theme(self, theme_name: str) -> None:
        """Switch active theme by name."""
        if theme_name in ("manet-soc", "manet-soc-high-contrast", "manet-ai-studio-warm"):
            self.theme = theme_name
            self.settings.high_contrast = (theme_name == "manet-soc-high-contrast")

    def action_toggle_reduced_motion(self) -> None:
        """Toggle UI motion and animation effects."""
        self.settings.reduced_motion = not self.settings.reduced_motion

    def action_train_champion_model(self) -> None:
        """Trigger calculation of the champion ML model."""
        if not self.is_screen_installed("simulation"):
            try:
                self.notify("Simulation screen is not installed.", severity="error")
            except Exception:
                pass
            return
        self.switch_screen("simulation")
        try:
            wizard = self.get_screen("simulation")
            switcher = wizard.query_one("#wizard-switcher")
            switcher.current = "step-preflight-review"
            review = wizard.query_one("#step-preflight-review")
            if hasattr(review, "action_train_champion"):
                review.action_train_champion()
        except Exception as exc:
            try:
                self.notify(f"Could not trigger model calculation: {exc}", severity="error")
            except Exception:
                pass


__all__ = ["ManetApp"]
