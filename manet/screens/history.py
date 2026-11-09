"""Full-screen session history browser for MANET IDS experiment records (TUI-21, D-02).

Provides searchable, sortable browsing of all persisted experiments, status
filtering, results inspection, and safe pruning with callback-owned deletion
and error handling.
"""

from __future__ import annotations

from typing import Any

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Static

from manet.adapters.workspace import ExperimentSummary, WorkspaceAdapter
from manet.screens.prune_modal import PruneConfirmationModal
from manet.screens.results import ResultsScreen


_SORT_COLUMNS = {
    "run_id": "run_id",
    "scenario": "scenario",
    "seed": "seed",
    "status": "status",
    "pdr": "pdr",
    "date": "date",
}
_COLUMN_LABELS = {
    "run_id": "Run ID",
    "scenario": "Scenario",
    "seed": "Seed",
    "status": "Status",
    "pdr": "PDR",
    "date": "Date",
}


class HistoryScreen(Screen):
    """Session history browser with search, status filters, sorting, and pruning."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("b", "go_back", "Back", show=False),
        Binding("r", "refresh_runs", "Refresh", show=True),
        Binding("d", "prune_selected", "Delete Run", show=True),
        Binding("enter", "select_run", "View Results", show=True),
    ]

    DEFAULT_CSS = """
    HistoryScreen {
        layout: vertical;
        background: #0a0e14;
        color: #e6edf3;
    }
    #history-filter-bar {
        height: auto;
        min-height: 3;
        layout: horizontal;
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 0 1;
        align: left middle;
    }
    #history-search {
        width: 1fr;
        min-width: 24;
        margin-right: 1;
    }
    .filter-btn {
        min-width: 10;
        margin-right: 1;
    }
    .filter-btn.active {
        background: #1f6feb;
        color: #ffffff;
        text-style: bold;
    }
    #history-table {
        height: 1fr;
        border: solid #21262d;
    }
    #history-hints {
        dock: bottom;
        height: 1;
        background: #161b22;
        color: #8b949e;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        workspace_adapter: WorkspaceAdapter | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.workspace_adapter = workspace_adapter or WorkspaceAdapter()
        self._all_runs: list[ExperimentSummary] = []
        self._active_status_filter: str = "ALL"
        self._search_query: str = ""
        self._sort_column: str = "date"
        self._sort_reverse: bool = True  # newest first by default

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="history-filter-bar"):
            yield Input(
                placeholder="Search scenario, tag, run ID, or seed...",
                id="history-search",
            )
            yield Button("All", id="filter-all", classes="filter-btn active")
            yield Button("Completed", id="filter-completed", classes="filter-btn")
            yield Button("Interrupted", id="filter-interrupted", classes="filter-btn")
            yield Button("Failed", id="filter-failed", classes="filter-btn")
        yield DataTable(id="history-table", cursor_type="row", zebra_stripes=True)
        yield Static(
            "[Enter] View Results | [D] Delete | [R] Refresh | [Esc] Back",
            id="history-hints",
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        table.add_column("Run ID", key="run_id")
        table.add_column("Scenario", key="scenario")
        table.add_column("Seed", key="seed")
        table.add_column("Status", key="status")
        table.add_column("PDR", key="pdr")
        table.add_column("Date", key="date")
        self.refresh_runs()

    def refresh_runs(self) -> None:
        """Reload all persisted experiments from disk (no truncation)."""
        try:
            self._all_runs = list(self.workspace_adapter.list_recent_experiments(limit=None))
        except Exception:
            self._all_runs = []
        self._refresh_table()

    def action_refresh_runs(self) -> None:
        self.refresh_runs()
        try:
            self.app.notify("Experiment list refreshed.", severity="information")
        except Exception:
            pass

    def action_go_back(self) -> None:
        try:
            self.app.pop_screen()
        except Exception:
            try:
                self.app.switch_screen("workspace")
            except Exception:
                pass

    def _set_filter(self, status: str) -> None:
        self._active_status_filter = status
        for btn_id, val in (
            ("#filter-all", "ALL"),
            ("#filter-completed", "COMPLETED"),
            ("#filter-interrupted", "INTERRUPTED"),
            ("#filter-failed", "FAILED"),
        ):
            try:
                btn = self.query_one(btn_id, Button)
                if val == status:
                    btn.add_class("active")
                else:
                    btn.remove_class("active")
            except Exception:
                pass
        self._refresh_table()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        mapping = {
            "filter-all": "ALL",
            "filter-completed": "COMPLETED",
            "filter-interrupted": "INTERRUPTED",
            "filter-failed": "FAILED",
        }
        btn_id = event.button.id or ""
        if btn_id in mapping:
            event.stop()
            self._set_filter(mapping[btn_id])

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "history-search":
            self._search_query = event.value or ""
            self._refresh_table()

    def _filtered_runs(self) -> list[ExperimentSummary]:
        runs = list(self._all_runs)
        if self._active_status_filter != "ALL":
            runs = [r for r in runs if str(r.status).upper() == self._active_status_filter]
        q = (self._search_query or "").strip().lower()
        if q:
            def matches(r: ExperimentSummary) -> bool:
                hay = " ".join(
                    [
                        str(r.experiment_id or ""),
                        str(r.scenario_name or ""),
                        str(getattr(r, "tag", "") or ""),
                        str(r.seed),
                    ]
                ).lower()
                return q in hay

            runs = [r for r in runs if matches(r)]
        return runs

    def _sort_key(self, r: ExperimentSummary):
        col = self._sort_column
        if col == "run_id":
            return str(r.experiment_id or "")
        if col == "scenario":
            return str(r.scenario_name or "").lower()
        if col == "seed":
            try:
                return int(r.seed)
            except Exception:
                return 0
        if col == "status":
            return str(r.status or "")
        if col == "pdr":
            if r.pdr is None:
                return (1, 0.0)  # Nones last in asc; handled by reverse logic
            try:
                return (0, float(r.pdr))
            except Exception:
                return (1, 0.0)
        if col == "date":
            return str(r.created_at or "")
        return str(r.experiment_id or "")

    def _set_sort(self, column: str) -> None:
        key = _SORT_COLUMNS.get(column, column)
        if self._sort_column == key:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = key
            # sensible defaults: numeric/date desc on first click? keep asc for text
            self._sort_reverse = key in ("date", "pdr")

    def action_sort_by(self, column: str) -> None:
        self._set_sort(column)
        self._refresh_table()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        if event.data_table.id != "history-table":
            return
        col_key = getattr(event.column_key, "value", event.column_key)
        self._set_sort(str(col_key))
        self._refresh_table()

    def _refresh_table(self) -> None:
        runs = self._filtered_runs()
        try:
            runs.sort(key=self._sort_key, reverse=self._sort_reverse)
        except Exception:
            pass
        # For PDR with None-last semantics in ascending, adjust when not reverse
        if self._sort_column == "pdr" and not self._sort_reverse:
            runs.sort(key=lambda r: (r.pdr is None, float(r.pdr) if r.pdr is not None else 0.0))
        elif self._sort_column == "pdr" and self._sort_reverse:
            runs.sort(key=lambda r: (r.pdr is None, -(float(r.pdr) if r.pdr is not None else 0.0)))

        table = self.query_one("#history-table", DataTable)
        cursor_row = table.cursor_row
        table.clear(columns=False)
        for r in runs:
            run_id = escape(str(r.experiment_id))
            scenario = escape(str(r.scenario_name))
            seed = str(r.seed)
            status = escape(str(r.status))
            pdr_str = f"{r.pdr:.4f}" if r.pdr is not None else "N/A"
            date_str = escape(str(r.created_at or "N/A"))
            try:
                table.add_row(run_id, scenario, seed, status, pdr_str, date_str, key=str(r.experiment_id))
            except Exception:
                table.add_row(run_id, scenario, seed, status, pdr_str, date_str)
        if table.row_count > 0:
            try:
                table.move_cursor(row=min(max(0, cursor_row), table.row_count - 1))
            except Exception:
                pass

    def _selected_experiment_id(self) -> str | None:
        table = self.query_one("#history-table", DataTable)
        if table.row_count <= 0:
            return None
        try:
            row_idx = table.cursor_row
            if row_idx is None or row_idx < 0:
                return None
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            if row_key is not None and getattr(row_key, "value", None) is not None:
                return str(row_key.value)
        except Exception:
            pass
        # fallback: parse from rendered row
        try:
            row = table.get_row_at(table.cursor_row)
            # first column is run_id (escaped markup stripped conceptually not needed; DataTable returns renderables)
            return str(row[0])
        except Exception:
            return None

    def _open_results(self, experiment_id: str) -> None:
        try:
            self.app.push_screen(
                ResultsScreen(experiment_id=experiment_id, workspace_adapter=self.workspace_adapter)
            )
        except Exception as exc:
            try:
                self.app.notify(f"Failed to open results: {exc}", severity="error")
            except Exception:
                pass

    def action_select_run(self) -> None:
        exp_id = self._selected_experiment_id()
        if exp_id:
            # strip rich escape artifacts if any
            clean = exp_id.replace("\\[", "[").replace("\\]", "]")
            self._open_results(clean)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id != "history-table":
            return
        try:
            key = event.row_key
            if key is not None and getattr(key, "value", None) is not None:
                self._open_results(str(key.value))
                return
        except Exception:
            pass
        exp_id = self._selected_experiment_id()
        if exp_id:
            self._open_results(exp_id)

    def action_prune_selected(self) -> None:
        exp_id = self._selected_experiment_id()
        if not exp_id:
            try:
                self.app.notify("No experiment selected.", severity="warning")
            except Exception:
                pass
            return
        try:
            preview = self.workspace_adapter.preview_experiment_deletion(exp_id)
        except Exception as exc:
            try:
                self.app.notify(f"Cannot preview deletion: {exc}", severity="error")
            except Exception:
                pass
            return
        self.app.push_screen(
            PruneConfirmationModal(preview),
            callback=lambda confirmed: self._handle_prune_result(exp_id, preview, bool(confirmed)),
        )

    def _handle_prune_result(self, run_id: str, preview: dict[str, Any], confirmed: bool) -> None:
        if not confirmed:
            return
        try:
            self.workspace_adapter.delete_experiment_run(run_id, expected_preview=preview)
        except (RuntimeError, OSError, ValueError) as exc:
            try:
                self.app.notify(f"Deletion failed: {exc}", title="Pruning Error", severity="error")
            except Exception:
                pass
            # Leave HistoryScreen active and table intact
            return
        try:
            self.app.notify(
                f"Deleted experiment record '{run_id}'.",
                title="Experiment Deleted",
                severity="information",
            )
        except Exception:
            pass
        self.refresh_runs()

    def on_screen_resume(self) -> None:
        """Refresh when returning so newly finalized runs appear."""
        self.refresh_runs()


__all__ = ["HistoryScreen"]
