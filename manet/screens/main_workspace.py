"""Primary workspace screen hosting the Executive Grid operational dashboard.

Composes the live Executive Grid layout:
- Top Status Cards: SystemHealthCard, ComponentCapabilitiesCard, ActiveWorkloadCard
- Lower Split Body: CtaHeroPanel (empty state) or RecentExperimentsTable (past runs) + NavRail
- Persistent Rails: StatusBar and NotificationRail fulfilling D-05 mounting contract
- Periodic Background Polling: Re-probes diagnostics every 4 seconds without blocking (D-02)
- Responsive Reflow: HORIZONTAL_BREAKPOINTS for adaptive layout down to 80x24 (D-01)
"""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Input, Static

from manet.adapters.diagnostics import DiagnosticsProbe
from manet.adapters.status import StatusAdapter
from manet.adapters.workspace import WorkspaceAdapter
from manet.runtime.keymap import BINDING_LIVE_RUN, BINDING_RESULTS, BINDING_SIMULATION
from manet.widgets.cta_hero import CtaHeroPanel
from manet.widgets.dashboard_cards import (
    ActiveWorkloadCard,
    ComponentCapabilitiesCard,
    SystemHealthCard,
)
from manet.widgets.nav_rail import NavRail
from manet.widgets.notification_rail import NotificationRail
from manet.widgets.recent_experiments import RecentExperimentsTable
from manet.widgets.status_bar import StatusBar


class MainWorkspace(Screen):
    """Primary workspace screen hosting the Executive Grid operational dashboard."""

    HORIZONTAL_BREAKPOINTS = [(0, "-compact"), (80, "-normal")]

    BINDINGS = [
        Binding(BINDING_SIMULATION, "simulation", "Simulation", show=True),
        Binding(BINDING_LIVE_RUN, "show_live_run", "Live Monitor", show=True),
        Binding(BINDING_RESULTS, "results", "Results", show=True),
        Binding("escape", "dismiss_notification", "Dismiss", show=False),
    ]

    CSS = """
    $info-blue: $secondary;
    $navigation-cyan: $primary;

    MainWorkspace {
        layout: vertical;
        background: $background;
        padding: 0;
    }

    #notification-rail {
        dock: top;
        height: auto;
        background: $surface;
        color: $warning;
        padding: 0 1;
        display: none;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $foreground;
        padding: 0 1;
    }

    #workspace-box {
        width: 100%;
        height: 1fr;
        layout: vertical;
        border: solid $info-blue;
        color: $foreground;
        background: $surface;
        overflow-y: auto;
    }

    Screen.-compact Static#workspace-box {
        padding: 0;
        margin: 0;
        border: none;
    }

    Screen.-normal Static#workspace-box {
        padding: 1 1;
        margin: 0;
    }

    #top-cards-container {
        height: auto;
        margin-bottom: 1;
    }

    Screen.-normal #top-cards-container {
        layout: horizontal;
    }

    Screen.-compact #top-cards-container {
        layout: vertical;
    }

    #card-health, #card-capabilities, #card-workload {
        height: auto;
        background: $surface;
        border: solid $info-blue;
        padding: 0 1;
    }

    Screen.-normal #card-health,
    Screen.-normal #card-capabilities,
    Screen.-normal #card-workload {
        width: 1fr;
        margin-right: 1;
    }

    Screen.-normal #card-workload {
        margin-right: 0;
    }

    Screen.-compact #card-health,
    Screen.-compact #card-capabilities,
    Screen.-compact #card-workload {
        width: 100%;
        margin-right: 0;
        margin-bottom: 1;
    }

    #lower-body-container {
        height: 1fr;
        min-height: 8;
    }

    Screen.-normal #lower-body-container {
        layout: horizontal;
    }

    Screen.-compact #lower-body-container {
        layout: vertical;
        overflow-y: auto;
    }

    #main-content-panel {
        background: $surface;
        border: solid $info-blue;
        padding: 1;
    }

    Screen.-normal #main-content-panel {
        width: 3fr;
        height: 100%;
    }

    Screen.-compact #main-content-panel {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    #nav-rail-panel {
        background: $surface;
        border: solid $navigation-cyan;
        padding: 1;
    }

    Screen.-normal #nav-rail-panel {
        width: 1fr;
        height: 100%;
        margin-left: 1;
    }

    Screen.-compact #nav-rail-panel {
        width: 100%;
        height: auto;
        margin-left: 0;
    }

    #workspace-box:focus {
        border: double $navigation-cyan;
    }

    *:focus {
        border: solid $navigation-cyan;
    }
    """

    def __init__(
        self,
        *args: Any,
        diagnostics_probe: DiagnosticsProbe | None = None,
        workspace_adapter: WorkspaceAdapter | None = None,
        status_adapter: StatusAdapter | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.diagnostics_probe = diagnostics_probe or DiagnosticsProbe()
        self.workspace_adapter = workspace_adapter or WorkspaceAdapter()
        self.status_adapter = status_adapter or StatusAdapter()
        self._refresh_count: int = 0

    def compose(self) -> ComposeResult:
        """Compose the executive grid hierarchy with rails and cards."""
        yield Header()
        yield NotificationRail(id="notification-rail")
        with Static(id="workspace-box"):
            with Container(id="top-cards-container"):
                yield SystemHealthCard(id="card-health", probe=self.diagnostics_probe)
                yield ComponentCapabilitiesCard(id="card-capabilities", probe=self.diagnostics_probe)
                yield ActiveWorkloadCard(id="card-workload", status_adapter=self.status_adapter)
            with Container(id="lower-body-container"):
                experiments = self.workspace_adapter.list_recent_experiments()
                if experiments:
                    yield RecentExperimentsTable(
                        experiments=experiments,
                        adapter=self.workspace_adapter,
                        id="main-content-panel",
                    )
                else:
                    yield CtaHeroPanel(id="main-content-panel")
                yield NavRail(id="nav-rail-panel")
        yield StatusBar(id="status-bar", status_adapter=self.status_adapter)
        yield Footer()

    def on_mount(self) -> None:
        """Initialize live diagnostics and schedule periodic background polling (D-02)."""
        if hasattr(self.app, "supervisor"):
            self.status_adapter.supervisor = getattr(self.app, "supervisor", None)
        self.refresh_diagnostics()
        # Non-blocking periodic refresh every 4 seconds
        self.set_interval(4.0, self.refresh_diagnostics)
        # Dedicated 0.5s timer for live workload status updates
        self.set_interval(0.5, self._refresh_workload_fast)

    def _refresh_workload_fast(self) -> None:
        """Lightweight 0.5s refresh for active workload card and status bar."""
        if hasattr(self.app, "supervisor") and self.status_adapter.supervisor is None:
            self.status_adapter.supervisor = getattr(self.app, "supervisor", None)
        status = self.status_adapter.get_status()
        try:
            self.query_one("#card-workload", ActiveWorkloadCard).update_status(status)
        except NoMatches:
            pass
        try:
            self.query_one("#status-bar", StatusBar).update_status(workload_status=status)
        except NoMatches:
            pass

    def refresh_diagnostics(self) -> None:
        """Non-blocking background refresh re-probing filesystem and environment state."""
        self._refresh_count += 1
        report = self.diagnostics_probe.probe_all()
        try:
            self.query_one("#card-health", SystemHealthCard).update_report(report)
        except NoMatches:
            pass
        try:
            self.query_one("#card-capabilities", ComponentCapabilitiesCard).update_report(report)
        except NoMatches:
            pass
        try:
            self.query_one("#card-workload", ActiveWorkloadCard).update_report(report)
        except NoMatches:
            pass
        try:
            self.query_one("#status-bar", StatusBar).update_report(report)
        except NoMatches:
            pass

        self.refresh_workspace()

    def refresh_workspace(self) -> None:
        """Refresh recent experiments table if mounted."""
        try:
            content_panel = self.query_one("#main-content-panel")
            if isinstance(content_panel, RecentExperimentsTable):
                content_panel.refresh_experiments()
        except NoMatches:
            pass

    def on_screen_resume(self) -> None:
        """Refresh workspace so newly completed runs appear automatically."""
        self.refresh_workspace()
        self.refresh_diagnostics()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Navigate to HistoryScreen when selecting a recent experiment (D-02)."""
        table = event.data_table
        if isinstance(table, RecentExperimentsTable) or table.id == "main-content-panel":
            try:
                self.app.push_screen("history")
            except Exception:
                if hasattr(self.app, "action_show_history"):
                    self.app.action_show_history()

    def action_simulation(self) -> None:
        """Switch to SimulationWorkflowScreen."""
        if self.app.screen is not self:
            return
        if self.app.focused is not None and isinstance(self.app.focused, Input):
            return
        self.app.switch_screen("simulation_workflow")

    def action_results(self) -> None:
        """Open session history browser (TUI-21, D-02)."""
        if self.app.screen is not self:
            return
        if self.app.focused is not None and isinstance(self.app.focused, Input):
            return
        try:
            self.app.push_screen("history")
        except Exception:
            if hasattr(self.app, "action_show_history"):
                self.app.action_show_history()

    def action_show_live_run(self) -> None:
        """Switch to LiveRunScreen monitor."""
        if hasattr(self.app, "action_show_live_run"):
            self.app.action_show_live_run()
        elif self.app.is_screen_installed("live_run"):
            self.app.switch_screen("live_run")

    action_live_run = action_show_live_run
    action_new_simulation = action_simulation
    action_show_results = action_results

    def action_dismiss_notification(self) -> None:
        """Dismiss active notification banner."""
        try:
            rail = self.query_one("#notification-rail", NotificationRail)
            rail.dismiss()
        except Exception:
            pass


__all__ = ["MainWorkspace"]
