"""Executive dashboard status cards for MANET IDS operational workspace."""

from __future__ import annotations

import platform
from textual.widgets import Static

from manet.adapters.diagnostics import DiagnosticsProbe, DiagnosticsReport
from manet.adapters.status import StatusAdapter, WorkloadStatus


class SystemHealthCard(Static):
    """Card displaying host runtime health including Python version, platform, and dependencies."""

    def __init__(
        self,
        *args,
        probe: DiagnosticsProbe | None = None,
        report: DiagnosticsReport | None = None,
        id: str | None = None,
        classes: str | None = None,
        **kwargs,
    ) -> None:
        self.probe = probe or DiagnosticsProbe()
        super().__init__("", *args, id=id, classes=classes, **kwargs)
        if report is not None:
            self.update_report(report)
        else:
            self.update_report(self.probe.probe_all())

    def update_report(self, report: DiagnosticsReport) -> None:
        """Update card content from a diagnostics report."""
        version_str, is_verified = report.python_version
        status_tag = "[green]VERIFIED[/]" if is_verified else "[red]UNSUPPORTED[/]"
        os_plat = platform.system() or "Unknown"

        total_deps = len(report.dependencies)
        avail_deps = sum(1 for avail, _ in report.dependencies.values() if avail)
        if avail_deps == total_deps:
            dep_tag = f"[green]ALL AVAILABLE ({avail_deps}/{total_deps})[/]"
        elif avail_deps > 0:
            dep_tag = f"[amber]PARTIAL ({avail_deps}/{total_deps})[/]"
        else:
            dep_tag = f"[red]UNAVAILABLE (0/{total_deps})[/]"

        content = (
            f"[bold $primary]System Health[/]\n"
            f"[bold]Python Runtime:[/] {version_str} ({status_tag})\n"
            f"[bold]OS Platform:[/]    {os_plat}\n"
            f"[bold]Dependencies:[/]   {dep_tag}"
        )
        self.update(content)


class ComponentCapabilitiesCard(Static):
    """Card displaying availability and validation state of scenarios, datasets, and models."""

    def __init__(
        self,
        *args,
        probe: DiagnosticsProbe | None = None,
        report: DiagnosticsReport | None = None,
        id: str | None = None,
        classes: str | None = None,
        **kwargs,
    ) -> None:
        self.probe = probe or DiagnosticsProbe()
        super().__init__("", *args, id=id, classes=classes, **kwargs)
        if report is not None:
            self.update_report(report)
        else:
            self.update_report(self.probe.probe_all())

    @staticmethod
    def _badge_for_state(state: str, details: str = "") -> str:
        if state == "VERIFIED":
            return "[green]VERIFIED[/]"
        elif state == "PARTIAL":
            if "Grayhole F1: 0.0" in details or "Ineffective Detection" in details:
                return "[amber]PARTIAL (Grayhole F1: 0.0 - Ineffective Detection)[/]"
            return "[amber]PARTIAL[/]"
        elif state == "EXPERIMENTAL":
            return "[yellow]EXPERIMENTAL[/]"
        elif state == "UNAVAILABLE":
            return "[red]UNAVAILABLE[/]"
        return f"[dim]{state}[/]"

    def update_report(self, report: DiagnosticsReport) -> None:
        """Update component capabilities content with inline contextual badges and remediation."""
        scenarios_badge = self._badge_for_state(report.scenarios.state, report.scenarios.details)
        datasets_badge = self._badge_for_state(report.datasets.state, report.datasets.details)
        model_badge = self._badge_for_state(report.model_artifact.state, report.model_artifact.details)

        lines: list[str] = [
            "[bold $primary]Component Capabilities[/]",
            f"[bold]Scenarios:[/] {report.scenarios.details} {scenarios_badge}",
        ]
        if report.scenarios.remediation and report.scenarios.state == "UNAVAILABLE":
            lines.append(f"[dim]  ↳ Fix: {report.scenarios.remediation}[/]")

        lines.append(f"[bold]Datasets:[/]  {report.datasets.details} {datasets_badge}")
        if report.datasets.remediation and report.datasets.state == "UNAVAILABLE":
            lines.append(f"[dim]  ↳ Fix: {report.datasets.remediation}[/]")

        lines.append(f"[bold]Champion:[/]  {report.model_artifact.details} {model_badge}")
        if report.model_artifact.remediation and report.model_artifact.state in ("UNAVAILABLE", "PARTIAL"):
            lines.append(f"[dim]  ↳ Fix: {report.model_artifact.remediation}[/]")

        self.update("\n".join(lines))


class ActiveWorkloadCard(Static):
    """Card displaying active workload state and routing engine availability."""

    def __init__(
        self,
        *args,
        status_adapter: StatusAdapter | None = None,
        workload_status: WorkloadStatus | None = None,
        id: str | None = None,
        classes: str | None = None,
        **kwargs,
    ) -> None:
        self.status_adapter = status_adapter or StatusAdapter()
        super().__init__("", *args, id=id, classes=classes, **kwargs)
        if workload_status is not None:
            self.update_status(workload_status)
        else:
            self.update_status(self.status_adapter.get_status())

    def update_status(self, status: WorkloadStatus) -> None:
        """Update card content from workload status."""
        workload_state = status.workload_state
        engine_state = status.engine_state
        desc = status.description

        lines: list[str] = ["[bold $primary]Active Workload[/]"]

        # Supervisor metrics and request if available
        sup = getattr(self.status_adapter, "supervisor", None)
        metrics = getattr(sup, "metrics", None) if sup else None
        req = getattr(sup, "current_request", None) if sup else None
        ids_enabled = bool(getattr(req, "ids_enabled", False)) if req else False

        if workload_state == "RUNNING":
            lines.append(f"[bold]Workload State:[/] [green]RUNNING[/] [dim]({desc})[/]")
            lines.append(f"[bold]Routing Engine:[/] [green]{engine_state}[/]")
            if ids_enabled:
                lines.append("[bold]IDS Protection:[/] [green]Active[/]")
            else:
                lines.append("[bold]IDS Protection:[/] [dim]Disabled[/]")
            lines.append("[bold $navigation-cyan]\\[L][/] Live Monitor")
        elif workload_state == "STOPPING":
            lines.append(f"[bold]Workload State:[/] [amber]STOPPING...[/] [dim]({desc})[/]")
            lines.append(f"[bold]Routing Engine:[/] [yellow]{engine_state}[/]")
            if ids_enabled:
                lines.append("[bold]IDS Protection:[/] [amber]Stopping...[/]")
            else:
                lines.append("[bold]IDS Protection:[/] [dim]Disabled[/]")
            lines.append("[bold $navigation-cyan]\\[L][/] Live Monitor")
        elif workload_state == "INTERRUPTED":
            lines.append(f"[bold]Workload State:[/] [amber]INTERRUPTED[/] [dim]({desc})[/]")
            lines.append(f"[bold]Routing Engine:[/] [dim]{engine_state}[/]")
            if ids_enabled:
                lines.append("[bold]IDS Protection:[/] [amber]Interrupted[/]")
            else:
                lines.append("[bold]IDS Protection:[/] [dim]Disabled[/]")
            lines.append("[bold $navigation-cyan]\\[L][/] View Run  [dim]|[/]  [bold $navigation-cyan]\\[S][/] New Simulation")
        elif workload_state == "FAILED":
            lines.append(f"[bold]Workload State:[/] [red]FAILED[/] [dim]({desc})[/]")
            lines.append(f"[bold]Routing Engine:[/] [dim]{engine_state}[/]")
            if ids_enabled:
                lines.append("[bold]IDS Protection:[/] [red]Failed[/]")
            else:
                lines.append("[bold]IDS Protection:[/] [dim]Disabled[/]")
            lines.append("[bold $navigation-cyan]\\[S][/] New Simulation")
        elif workload_state == "COMPLETED":
            lines.append(f"[bold]Workload State:[/] [bright_green]COMPLETED[/] [dim]({desc})[/]")
            lines.append(f"[bold]Routing Engine:[/] [green]{engine_state}[/]")
            if ids_enabled:
                lines.append("[bold]IDS Protection:[/] [green]Protected (Completed)[/]")
            else:
                lines.append("[bold]IDS Protection:[/] [dim]Disabled[/]")
            if metrics:
                pdr = f"{metrics.get('pdr', 0.0) * 100:.1f}%"
                thru = f"{metrics.get('throughput_bps', 0.0):.0f} bps"
                delay = f"{metrics.get('avg_delay_s', 0.0):.4f} s"
                lines.append(f"[bold]Results:[/] PDR: [green]{pdr}[/] | Thru: [cyan]{thru}[/] | Delay: [yellow]{delay}[/]")
            lines.append("[bold $navigation-cyan]\\[L][/] View Run  [dim]|[/]  [bold $navigation-cyan]\\[S][/] New Simulation")
        else:
            lines.append(f"[bold]Workload State:[/] [cyan]IDLE[/] [dim]({desc})[/]")
            lines.append(f"[bold]Routing Engine:[/] [green]{engine_state}[/]")
            lines.append("[bold]IDS Protection:[/] [dim]Standby (Ready for deployment)[/]")

        self.update("\n".join(lines))

    def update_report(self, report: DiagnosticsReport | None = None) -> None:
        """Periodic refresh hook to poll active workload state."""
        self.update_status(self.status_adapter.get_status())


__all__ = [
    "ActiveWorkloadCard",
    "ComponentCapabilitiesCard",
    "SystemHealthCard",
]
