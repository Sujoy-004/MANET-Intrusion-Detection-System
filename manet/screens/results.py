"""Academic Results Screen for completed MANET IDS experiment inspection (TUI-19/TUI-20)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static, TabbedContent, TabPane
from textual.worker import get_current_worker

from manet.adapters.workspace import WorkspaceAdapter, get_experiment_manifest
from manet.widgets.qos_scorecard import QosScorecard

ISOLATION_SCHEMA_FIELDS = ("sim_time", "node_id", "predicted_type", "action", "prob_malicious", "reason")


class ResultsScreen(Screen):
    """Split-pane academic results inspector with QoS scorecard and detail tabs."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("b", "app.pop_screen", "Back"),
    ]

    DEFAULT_CSS = """
    ResultsScreen {
        layout: vertical;
        background: #0a0e14;
        color: #e6edf3;
    }
    #results-top-pane {
        height: auto;
        background: #0d1117;
        padding: 0 1;
    }
    #results-partial-banner {
        height: auto;
        padding: 0 1;
        color: #d29922;
    }
    #results-tabs {
        height: 1fr;
        border-top: solid #30363d;
    }
    .results-static {
        padding: 1;
    }
    """

    def __init__(
        self,
        experiment_id: str | None = None,
        experiment_dir: Path | None = None,
        workspace_adapter: WorkspaceAdapter | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.workspace_adapter = workspace_adapter or WorkspaceAdapter()
        self._requested_experiment_id = experiment_id
        self.experiment_dir: Path | None = Path(experiment_dir) if experiment_dir is not None else None
        self.experiment_id: str | None = experiment_id
        self.manifest: dict[str, Any] | None = None
        self._artifact_results: dict[str, dict[str, Any]] = {}
        self._resolve_failed_no_completed = False
        self._resolved = False
        self._resolve_target()

    def _notify(self, message: str) -> None:
        try:
            self.app.notify(message, severity="warning")
        except Exception:
            pass

    def _resolve_target(self) -> bool:
        """Resolve experiment target. Returns False if screen should not render results."""
        if self._resolved:
            return not self._resolve_failed_no_completed
        self._resolved = True
        if self.experiment_dir is not None:
            self.manifest = get_experiment_manifest(self.experiment_dir)
            if self.manifest:
                self.experiment_id = str(self.manifest.get("experiment_id") or self.experiment_dir.name)
            else:
                self.experiment_id = self.experiment_dir.name
            return True

        if self._requested_experiment_id:
            self.experiment_dir = self.workspace_adapter.workspace_root / self._requested_experiment_id
            self.manifest = get_experiment_manifest(self.experiment_dir)
            self.experiment_id = self._requested_experiment_id
            return True

        # No ID/dir: latest COMPLETED, ignore newer FAILED/INTERRUPTED
        recent_runs = self.workspace_adapter.list_recent_experiments(limit=None)
        completed = next((r for r in recent_runs if r.status == "COMPLETED"), None)
        if completed is None:
            self._resolve_failed_no_completed = True
            return False
        self.experiment_id = completed.experiment_id
        self.experiment_dir = self.workspace_adapter.workspace_root / completed.experiment_id
        self.manifest = get_experiment_manifest(self.experiment_dir)
        return True

    def _ids_enabled(self) -> bool:
        if not self.manifest:
            return False
        cfg = self.manifest.get("configuration") or {}
        if isinstance(cfg, dict):
            if cfg.get("ids_enabled") is True:
                return True
            if cfg.get("champion_model"):
                return True
            if str(cfg.get("ids_enabled", "")).lower() == "true":
                return True
        return False

    def _load_isolation_events(self) -> list[dict[str, Any]]:
        if not self.experiment_dir:
            return []
        json_path = self.experiment_dir / "isolation_log.json"
        csv_path = self.experiment_dir / "isolation_log.csv"
        events: list[dict[str, Any]] = []
        if json_path.is_file():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    events = [e for e in data if isinstance(e, dict)]
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                events = []
        elif csv_path.is_file():
            try:
                with open(csv_path, "r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    events = [dict(row) for row in reader]
            except (OSError, csv.Error, UnicodeDecodeError):
                events = []
        return events

    def _config_summary_text(self) -> str:
        m = self.manifest or {}
        cfg = m.get("configuration") or {}
        if not isinstance(cfg, dict):
            cfg = {}
        lines = [
            f"[bold]Experiment:[/] {escape(str(m.get('experiment_id', self.experiment_id or 'Unknown')))}",
            f"[bold]Scenario:[/] {escape(str(m.get('scenario_name', cfg.get('name', 'Unknown'))))}",
            f"[bold]Seed:[/] {escape(str(m.get('seed', cfg.get('seed', 'N/A'))))}",
            f"[bold]Node Count:[/] {escape(str(cfg.get('nodes', cfg.get('num_nodes', 'N/A'))))}",
            f"[bold]Duration:[/] {escape(str(cfg.get('duration', 'N/A')))}",
            f"[bold]Radio Range:[/] {escape(str(cfg.get('radio_range', cfg.get('tx_range', 'N/A'))))}",
            f"[bold]Speed:[/] {escape(str(cfg.get('speed', cfg.get('max_speed', 'N/A'))))}",
            f"[bold]Software Version:[/] {escape(str(m.get('software_version', 'N/A')))}",
            f"[bold]Status:[/] {escape(str(m.get('status', 'UNKNOWN')))}",
            f"[bold]created_at:[/] {escape(str(m.get('created_at', 'N/A')))}",
            f"[bold]started_at:[/] {escape(str(m.get('started_at', 'N/A')))}",
            f"[bold]completed_at:[/] {escape(str(m.get('completed_at', 'N/A')))}",
            f"[bold]updated_at:[/] {escape(str(m.get('updated_at', 'N/A')))}",
        ]
        err = m.get("error_details") or m.get("error")
        if err:
            lines.append(f"[bold red]Error:[/] {escape(str(err))}")
        return "\n".join(lines)

    def _artifact_initial_text(self) -> str:
        m = self.manifest or {}
        artifacts = m.get("artifacts") if isinstance(m.get("artifacts"), dict) else {}
        lines = ["[bold]Artifacts & Integrity[/]\n"]
        if not artifacts and self.experiment_dir:
            # legacy / no recorded artifacts: show known files
            for name in ("trace.csv", "isolation_log.csv", "isolation_log.json"):
                p = self.experiment_dir / name
                if p.is_file():
                    lines.append(f"- {escape(name)}: {escape(str(p))} ({p.stat().st_size} bytes)")
            if len(lines) == 1:
                lines.append("[dim]No artifact records found.[/]")
        else:
            for name, info in (artifacts or {}).items():
                if not isinstance(info, dict):
                    continue
                rel = escape(str(info.get("relative_path") or info.get("filename") or name))
                abs_p = escape(str((self.experiment_dir / rel).resolve())) if self.experiment_dir else rel
                size = info.get("size_bytes", "N/A")
                rows = info.get("row_count", "N/A")
                lines.append(
                    f"[bold]{escape(str(name))}[/]\n"
                    f"  Path: {abs_p}\n  Relative: {rel}\n  Size: {escape(str(size))} bytes | Rows/records: {escape(str(rows))}\n"
                    f"  Integrity: [bold cyan]VERIFYING CHECKSUMS...[/]"
                )
        return "\n".join(lines)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        if self._resolve_failed_no_completed:
            yield Static("[bold yellow]No completed experiment records found in workspace.[/]", classes="results-static")
            yield Footer()
            return

        status = str((self.manifest or {}).get("status", "UNKNOWN"))
        metrics = (self.manifest or {}).get("metrics")
        if not isinstance(metrics, dict):
            metrics = None

        with Container(id="results-top-pane"):
            if metrics:
                yield QosScorecard(metrics=metrics)
            if status in ("INTERRUPTED", "FAILED") or (metrics and status != "COMPLETED"):
                yield Static(
                    f"[bold #d29922]Simulation Status: {escape(status)} - Showing available partial metrics[/]",
                    id="results-partial-banner",
                )

        with TabbedContent(id="results-tabs"):
            with TabPane("Artifacts & Integrity", id="tab-artifacts"):
                yield Static(self._artifact_initial_text(), id="artifacts-content", classes="results-static")

            with TabPane("Security & Isolation Log", id="tab-security"):
                yield from self._compose_security_tab()

            with TabPane("Configuration & Execution", id="tab-config"):
                yield Static(self._config_summary_text(), id="config-content", classes="results-static")

        yield Footer()

    def _compose_security_tab(self) -> ComposeResult:
        ids_enabled = self._ids_enabled()
        events = self._load_isolation_events()
        if not ids_enabled:
            yield Static(
                "[dim]Online IDS Defense was disabled in configuration for this run.[/]",
                id="security-content",
                classes="results-static",
            )
            return
        if not events:
            yield Static(
                "[dim green]Online IDS Defense was active — 0 nodes flagged or isolated (no malicious activity detected or attacks evaded).[/]",
                id="security-content",
                classes="results-static",
            )
            return
        table = DataTable(id="security-table", zebra_stripes=True)
        table.add_columns("Time", "Node ID", "Attack Type", "Action", "Confidence", "Reason")
        for ev in events:
            row = [
                escape(str(ev.get("sim_time", ""))),
                escape(str(ev.get("node_id", ""))),
                escape(str(ev.get("predicted_type", ""))),
                escape(str(ev.get("action", ""))),
                escape(str(ev.get("prob_malicious", ""))),
                escape(str(ev.get("reason", ""))),
            ]
            table.add_row(*row)
        yield table

    def on_mount(self) -> None:
        if self._resolve_failed_no_completed:
            self._notify("[bold yellow]No completed experiment records found in workspace.[/]")
            # Redirect to history if available, else pop
            try:
                if self.app.is_screen_installed("history"):
                    self.app.switch_screen("history")
                else:
                    self.app.pop_screen()
            except Exception:
                try:
                    self.app.pop_screen()
                except Exception:
                    pass
            return
        if self.experiment_dir and self.experiment_dir.is_dir():
            self.verify_artifacts_worker()

    @work(thread=True)
    def verify_artifacts_worker(self) -> None:
        """Synchronous file hashing running in worker thread."""
        worker = get_current_worker()
        try:
            if worker.is_cancelled:
                return
            if not self.experiment_dir:
                return
            results = self.workspace_adapter.verify_artifact_checksums(self.experiment_dir)
            if worker.is_cancelled:
                return
            try:
                self.app.call_from_thread(self._apply_verification_results, results)
            except (RuntimeError, Exception):
                pass
        except Exception as exc:
            if not worker.is_cancelled:
                try:
                    self.app.call_from_thread(self._apply_verification_error, str(exc))
                except (RuntimeError, Exception):
                    pass

    def _render_verification_text(self, results: dict[str, dict[str, Any]]) -> str:
        m = self.manifest or {}
        artifacts = m.get("artifacts") if isinstance(m.get("artifacts"), dict) else {}
        if not artifacts and self.experiment_dir:
            # legacy path: show results by filename
            lines = ["[bold]Artifacts & Integrity[/]\n"]
            for name, res in results.items():
                badge = self._badge_for(res)
                p = self.experiment_dir / name
                rel = escape(name)
                abs_p = escape(str(p.resolve())) if p.exists() else rel
                lines.append(f"[bold]{rel}[/]\n  Path: {abs_p}\n  Integrity: {badge}")
            return "\n".join(lines) if len(lines) > 1 else "[dim]No artifacts.[/]"
        lines = ["[bold]Artifacts & Integrity[/]\n"]
        for name, info in (artifacts or {}).items():
            if not isinstance(info, dict):
                continue
            rel = escape(str(info.get("relative_path") or info.get("filename") or name))
            abs_p = escape(str((self.experiment_dir / rel).resolve())) if self.experiment_dir else rel
            size = info.get("size_bytes", "N/A")
            rows = info.get("row_count", "N/A")
            res = results.get(str(name), {})
            badge = self._badge_for(res)
            lines.append(
                f"[bold]{escape(str(name))}[/]\n"
                f"  Path: {abs_p}\n  Relative: {rel}\n  Size: {escape(str(size))} bytes | Rows/records: {escape(str(rows))}\n"
                f"  Integrity: {badge}"
            )
        return "\n".join(lines)

    def _badge_for(self, res: dict[str, Any]) -> str:
        status = res.get("status")
        if status == "VERIFIED":
            cur = escape(str(res.get("current_sha256") or "")[:16])
            return f"[bold green]VERIFIED ✓[/] (sha256: {cur}...)"
        if status == "CORRUPTED":
            exp = escape(str(res.get("expected_sha256") or "")[:16])
            cur = escape(str(res.get("current_sha256") or "")[:16])
            return f"[bold red]CORRUPTED / TAMPERED ✗[/] (expected: {exp}..., current: {cur}...)"
        if status == "MISSING":
            return "[yellow]MISSING ✗[/]"
        if status == "RECORDED":
            cur = escape(str(res.get("current_sha256") or "")[:16])
            return f"[cyan]RECORDED[/] (sha256: {cur}...)"
        if status == "ERROR":
            return f"[bold red]VERIFICATION ERROR[/] ({escape(str(res.get('error', 'unknown')))})"
        if status == "SECURITY_VIOLATION":
            return f"[bold red]SECURITY VIOLATION[/] ({escape(str(res.get('error', '')))}))"
        return "[dim]UNKNOWN[/]"

    def _apply_verification_results(self, results: dict[str, dict[str, Any]]) -> None:
        if not self.is_mounted:
            return
        self._artifact_results = results
        try:
            w = self.query_one("#artifacts-content", Static)
            w.update(self._render_verification_text(results))
        except Exception:
            pass

    def _apply_verification_error(self, error_msg: str) -> None:
        if not self.is_mounted:
            return
        try:
            w = self.query_one("#artifacts-content", Static)
            w.update(f"[bold red]VERIFICATION ERROR[/] ({escape(error_msg)})")
        except Exception:
            pass

    def on_unmount(self) -> None:
        # Cancel only screen-scoped workers; never cancel_all()
        try:
            self.workers.cancel_node(self)
        except Exception:
            pass


__all__ = ["ResultsScreen"]
