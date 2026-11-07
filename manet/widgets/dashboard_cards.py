"""Executive dashboard status cards for MANET IDS operational workspace."""

from __future__ import annotations

from textual.widgets import Static

from manet.adapters.diagnostics import DiagnosticsProbe


class SystemHealthCard(Static):
    """Card displaying host runtime health including Python version and dependencies."""

    def __init__(
        self,
        *args,
        probe: DiagnosticsProbe | None = None,
        id: str | None = None,
        classes: str | None = None,
        **kwargs,
    ) -> None:
        self.probe = probe or DiagnosticsProbe()
        version_str, is_verified = self.probe.probe_python_version()
        status_tag = "[green]VERIFIED[/]" if is_verified else "[red]UNSUPPORTED[/]"
        initial_content = (
            f"[bold $primary]System Health[/]\n"
            f"[bold]Python Runtime:[/] {version_str} ({status_tag})"
        )
        super().__init__(initial_content, *args, id=id, classes=classes, **kwargs)


__all__ = ["SystemHealthCard"]
