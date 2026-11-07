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

        # State color styling
        workload_color = "cyan" if workload_state == "IDLE" else ("green" if workload_state == "RUNNING" else "yellow")
        engine_color = "green" if "Ready" in engine_state else "yellow"

        content = (
            f"[bold $primary]Active Workload[/]\n"
            f"[bold]Workload State:[/] [{workload_color}]{workload_state}[/] [dim]({desc})[/]\n"
            f"[bold]Routing Engine:[/] [{engine_color}]{engine_state}[/]\n"
            f"[bold]IDS Protection:[/] [dim]Standby (Ready for deployment)[/]"
        )
        self.update(content)

    def update_report(self, report: DiagnosticsReport | None = None) -> None:
        """Periodic refresh hook to poll active workload state."""
        self.update_status(self.status_adapter.get_status())


__all__ = [
    "ActiveWorkloadCard",
    "ComponentCapabilitiesCard",
    "SystemHealthCard",
]
