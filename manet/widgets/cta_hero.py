"""Guided Call-to-Action (CTA) Hero Panel for empty workspace state (D-04, TUI-07)."""

from __future__ import annotations

from textual.widgets import Static

CTA_HERO_CONTENT = (
    "[bold $primary]Guided First-Run • Workspace Initialized[/]\n"
    "[dim]Ready for Simulation • Workflow Pending (Phase 9) • Press \\[S] for workflow preview notice[/]\n\n"
    "[dim]────────────────────────────────────────────────────────────[/]\n\n"
    "[bold $secondary]Recommended Getting-Started Guidance:[/bold $secondary]\n"
    "  1. [bold]Review Scenario Presets:[/] Inspect preset JSON files under [cyan]scenarios/[/]\n"
    "  2. [bold]Verify Model Readiness:[/] Check dataset and model artifacts in [cyan]data/[/] and [cyan]ml/models/[/]\n"
    "  3. [bold]Baseline Architecture:[/] Review AODV protocol and multi-attack injection specs\n"
    "  4. [bold]Session Console:[/] Press [bold $navigation-cyan]\\[Ctrl+O][/] for logs & diagnostics, [bold $navigation-cyan]\\[F1][/] for help\n\n"
    "[dim]Note: Active simulation runner workflow will be unlocked in Phase 9 (TUI-09).[/]"
)


class CtaHeroPanel(Static):
    """Guided empty-state CTA panel displayed when .manet-workspace/ has no past runs."""

    def __init__(
        self,
        *args,
        id: str | None = "cta-hero-panel",
        classes: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(CTA_HERO_CONTENT, *args, id=id, classes=classes, **kwargs)


__all__ = ["CTA_HERO_CONTENT", "CtaHeroPanel"]
