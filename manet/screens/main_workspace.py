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
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from manet.adapters.diagnostics import DiagnosticsProbe
from manet.adapters.status import StatusAdapter
from manet.adapters.workspace import WorkspaceAdapter
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
        Binding("s", "new_simulation", "New Simulation", show=True),
        Binding("r", "show_results", "Results", show=True),
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
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize live diagnostics and schedule periodic background polling (D-02)."""
        self.refresh_diagnostics()
        # Non-blocking periodic refresh every 4 seconds
        self.set_interval(4.0, self.refresh_diagnostics)

    def refresh_diagnostics(self) -> None:
        """Non-blocking background refresh re-probing filesystem and environment state."""
        report = self.diagnostics_probe.probe_all()
        try:
            self.query_one("#card-health", SystemHealthCard).update_report(report)
        except Exception:
            pass
        try:
            self.query_one("#card-capabilities", ComponentCapabilitiesCard).update_report(report)
        except Exception:
            pass
        try:
            self.query_one("#card-workload", ActiveWorkloadCard).update_report(report)
        except Exception:
            pass
        try:
            self.query_one("#status-bar", StatusBar).update_report(report)
        except Exception:
            pass

        self.refresh_workspace()

    def refresh_workspace(self) -> None:
        """Refresh recent experiments table if mounted."""
        try:
            content_panel = self.query_one("#main-content-panel")
            if isinstance(content_panel, RecentExperimentsTable):
                content_panel.refresh_experiments()
        except Exception:
            pass

    def action_new_simulation(self) -> None:
        """Display informative notice that simulation workflow is pending in Phase 9."""
        try:
            rail = self.query_one("#notification-rail", NotificationRail)
            rail.notify_user("Simulation workflow will be available in Phase 9 (TUI-09)")
        except Exception:
            pass

    def action_show_results(self) -> None:
        """Display informative notice that results browser is pending in Phase 11."""
        try:
            rail = self.query_one("#notification-rail", NotificationRail)
            rail.notify_user("Experiment results browser will be available in Phase 11 (TUI-19)")
        except Exception:
            pass

    def action_dismiss_notification(self) -> None:
        """Dismiss active notification banner."""
        try:
            rail = self.query_one("#notification-rail", NotificationRail)
            rail.dismiss()
        except Exception:
            pass


__all__ = ["MainWorkspace"]
