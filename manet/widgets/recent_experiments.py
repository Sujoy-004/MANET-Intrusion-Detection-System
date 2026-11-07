"""Recent experiments table widget displaying past runs discovered strictly read-only."""

from __future__ import annotations

from rich.markup import escape
from textual.widgets import DataTable

from manet.adapters.workspace import ExperimentSummary, WorkspaceAdapter


class RecentExperimentsTable(DataTable):
    """DataTable displaying past simulation runs discovered in .manet-workspace/."""

    COLUMNS = ("Run ID", "Scenario", "Seed", "Status", "PDR", "Date")

    def __init__(
        self,
        experiments: list[ExperimentSummary] | None = None,
        *args,
        adapter: WorkspaceAdapter | None = None,
        id: str | None = "recent-experiments-table",
        classes: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(
            *args,
            cursor_type="row",
            zebra_stripes=True,
            id=id,
            classes=classes,
            **kwargs,
        )
        self.adapter = adapter or WorkspaceAdapter()
        self._initial_experiments = experiments
        self._columns_initialized = False

    def on_mount(self) -> None:
        """Initialize columns and populate rows on mount."""
        self._ensure_columns()
        if self._initial_experiments is not None:
            self.populate_experiments(self._initial_experiments)
        else:
            self.refresh_experiments()

    def _ensure_columns(self) -> None:
        """Add table columns if not already added."""
        if not self._columns_initialized:
            for col in self.COLUMNS:
                self.add_column(col, key=col.lower().replace(" ", "_"))
            self._columns_initialized = True

    def populate_experiments(self, experiments: list[ExperimentSummary]) -> None:
        """Populate table with sanitized experiment summaries."""
        self._ensure_columns()
        self.clear()
        for exp in experiments:
            # Sanitize values to prevent markup injection (T-08-05 mitigation)
            run_id = escape(exp.experiment_id)
            scenario = escape(exp.scenario_name)
            seed = str(exp.seed)
            status = escape(exp.status)
            pdr_str = f"{exp.pdr:.4f}" if exp.pdr is not None else "N/A"
            date_str = escape(exp.created_at) if exp.created_at else "N/A"

            self.add_row(run_id, scenario, seed, status, pdr_str, date_str)

    def refresh_experiments(self, limit: int = 10) -> None:
        """Fetch recent experiments strictly read-only and repopulate table."""
        experiments = self.adapter.list_recent_experiments(limit=limit)
        self.populate_experiments(experiments)


__all__ = ["RecentExperimentsTable"]
