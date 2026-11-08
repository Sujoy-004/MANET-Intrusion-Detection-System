"""Persistent status bar widget fulfilling D-05 mounting contract."""

from __future__ import annotations

from typing import Optional

from textual.widgets import Static

from manet.adapters.diagnostics import DiagnosticsReport
from manet.adapters.status import StatusAdapter, WorkloadStatus


class StatusBar(Static):
    """System status bar mounted at the base of the operational workspace."""

    def __init__(
        self,
        *args,
        status_adapter: Optional[StatusAdapter] = None,
        id: str | None = "status-bar",
        classes: str | None = None,
        **kwargs,
    ) -> None:
        self.status_adapter = status_adapter
        super().__init__("", *args, id=id, classes=classes, **kwargs)
        self.update_status()

    def update_status(
        self,
        status_text: str = "System Ready",
        workspace_indicator: str = "Nominal",
        engine_indicator: str = "Offline Ready",
        workload_status: Optional[WorkloadStatus] = None,
    ) -> None:
        """Format and render status bar indicators."""
        if workload_status is None and self.status_adapter is not None:
            workload_status = self.status_adapter.get_status()

        if workload_status is not None:
            state = workload_status.workload_state
            if state == "RUNNING":
                workspace_indicator = "[green]RUNNING[/]"
                engine_indicator = "[green]SIMULATING[/]"
                status_text = "Simulation Active"
            elif state == "STOPPING":
                workspace_indicator = "[amber]STOPPING[/]"
                engine_indicator = "[amber]STOPPING[/]"
                status_text = "Stopping..."
            elif state == "COMPLETED":
                workspace_indicator = "[green]COMPLETED[/]"
                engine_indicator = "[green]Offline Ready[/]"
            elif state in ("INTERRUPTED", "FAILED"):
                workspace_indicator = f"[red]{state}[/]"
                engine_indicator = "[dim]Offline Ready[/]"

        content = (
            f" [green]●[/] [bold]{status_text}[/]  "
            f"[dim]|[/]  [dim]Workspace:[/] [cyan]{workspace_indicator}[/]  "
            f"[dim]|[/]  [dim]Engine:[/] [green]{engine_indicator}[/]  "
            f"[dim]|[/]  [dim]Press [bold $primary]F1[/] for Shortcuts[/]"
        )
        self.update(content)

    def update_report(self, report: DiagnosticsReport | None = None) -> None:
        """Periodic refresh hook to update status bar from diagnostic state."""
        if report is not None:
            python_ok = report.python_version[1]
            deps_ok = all(avail for avail, _ in report.dependencies.values())
            if python_ok and deps_ok:
                status_text = "System Ready"
            else:
                status_text = "System Degraded"
            self.update_status(status_text=status_text)
        else:
            self.update_status()


__all__ = ["StatusBar"]
