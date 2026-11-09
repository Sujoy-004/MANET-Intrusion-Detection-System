"""Tests for HistoryScreen session browser (Phase 11, TUI-21)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Button, DataTable, Input, Static

from manet.adapters.workspace import WorkspaceAdapter, record_launch_manifest, update_manifest_status
from manet.screens.history import HistoryScreen
from manet.screens.results import ResultsScreen


def _make_exp(
    root: Path,
    name: str,
    *,
    scenario: str = "scenario_a",
    seed: int = 1,
    status: str = "COMPLETED",
    pdr: float | None = 0.9,
    tag: str | None = None,
    created_at: str = "2024-01-01T12:00:00Z",
) -> Path:
    exp_dir = root / name
    exp_dir.mkdir(parents=True, exist_ok=True)
    cfg: dict[str, Any] = {"name": scenario, "seed": seed, "duration": 100, "nodes": 10}
    if tag:
        cfg["tag"] = tag
    record_launch_manifest(exp_dir, name, scenario, seed, cfg, tag=tag)
    metrics = {"pdr": pdr, "throughput_bps": 100.0, "avg_delay_s": 0.01, "routing_overhead": 0.1, "packet_loss_ratio": 0.1, "data_sent": 10.0, "data_received": 9.0, "routing_packets": 1.0} if pdr is not None else None
    if status in ("COMPLETED", "INTERRUPTED", "FAILED"):
        (exp_dir / "trace.csv").write_text("time,src\n1,1\n", encoding="utf-8")
        update_manifest_status(exp_dir, status, metrics=metrics)
    # override created_at for deterministic sorting tests
    mpath = exp_dir / "manifest.json"
    m = json.loads(mpath.read_text(encoding="utf-8"))
    m["created_at"] = created_at
    m["status"] = status
    if pdr is not None:
        m["pdr"] = pdr
        m["metrics"] = metrics
    if tag:
        m["tag"] = tag
    mpath.write_text(json.dumps(m), encoding="utf-8")
    return exp_dir


class HistoryTestApp(App[None]):
    def __init__(self, screen: Screen) -> None:
        super().__init__()
        self._screen = screen
        self.notifications: list[tuple[str, str]] = []

    def notify(self, message: str, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        sev = str(kwargs.get("severity", "information"))
        self.notifications.append((str(message), sev))
        try:
            super().notify(message, *args, **kwargs)
        except Exception:
            pass

    def on_mount(self) -> None:
        self.install_screen(ResultsScreen(), "results")
        self.push_screen(self._screen)


def _history_table_text(screen: HistoryScreen) -> str:
    table = screen.query_one("#history-table", DataTable)
    rows = []
    for i in range(table.row_count):
        row = table.get_row_at(i)
        rows.append(" | ".join(str(c) for c in row))
    return "\n".join(rows)


@pytest.mark.asyncio
async def test_history_screen_browses_all_runs(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    # create > 100-like scenario not necessary; key is limit=None used (no truncation at 10 default)
    for i in range(15):
        _make_exp(ws, f"exp_{i:03d}_s_{i}", scenario=f"scen_{i}", seed=i, status="COMPLETED", pdr=0.5 + i / 100)
    adapter = WorkspaceAdapter(workspace_root=ws)
    screen = HistoryScreen(workspace_adapter=adapter)
    app = HistoryTestApp(screen)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        assert screen.query_one("#history-table", DataTable)
        assert screen.query_one("#history-search", Input)
        # filter buttons exist
        assert screen.query_one("#filter-all", Button)
        assert screen.query_one("#filter-completed", Button)
        table = screen.query_one("#history-table", DataTable)
        assert table.row_count == 15


@pytest.mark.asyncio
async def test_history_screen_sortable_columns(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _make_exp(ws, "exp_b", scenario="beta", seed=20, status="FAILED", pdr=0.2, created_at="2024-01-03T00:00:00Z")
    _make_exp(ws, "exp_a", scenario="alpha", seed=5, status="COMPLETED", pdr=0.9, created_at="2024-01-01T00:00:00Z")
    _make_exp(ws, "exp_c", scenario="gamma", seed=10, status="INTERRUPTED", pdr=None, created_at="2024-01-02T00:00:00Z")
    adapter = WorkspaceAdapter(workspace_root=ws)
    screen = HistoryScreen(workspace_adapter=adapter)
    app = HistoryTestApp(screen)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        # sort by seed ascending via action/method if available, else click header; prefer method
        if hasattr(screen, "action_sort_by"):
            screen.action_sort_by("seed")
            await pilot.pause(0.1)
        else:
            # try header click fallback - first column is Run ID index 0 etc; seed is column 2
            # simulate by calling internal sort helper
            screen._set_sort("seed")  # type: ignore[attr-defined]
            screen._refresh_table()  # type: ignore[attr-defined]
            await pilot.pause(0.1)
        txt = _history_table_text(screen)
        # seed order 5,10,20 should appear in that sequence
        pos5 = txt.find("| 5 |") if "| 5 |" in txt else txt.find(" 5 ")
        pos10 = txt.find("| 10 |") if "| 10 |" in txt else txt.find(" 10 ")
        pos20 = txt.find("| 20 |") if "| 20 |" in txt else txt.find(" 20 ")
        assert pos5 != -1 and pos10 != -1 and pos20 != -1
        assert pos5 < pos10 < pos20


@pytest.mark.asyncio
async def test_history_screen_scenario_tag_search(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _make_exp(ws, "exp_alpha_run", scenario="alpha_net", seed=11, tag="baseline", status="COMPLETED", pdr=0.8)
    _make_exp(ws, "exp_beta_run", scenario="beta_net", seed=22, tag="attack", status="COMPLETED", pdr=0.7)
    adapter = WorkspaceAdapter(workspace_root=ws)
    screen = HistoryScreen(workspace_adapter=adapter)
    app = HistoryTestApp(screen)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        inp = screen.query_one("#history-search", Input)
        inp.value = "alpha"
        await pilot.pause(0.15)
        txt = _history_table_text(screen)
        assert "alpha_net" in txt
        assert "beta_net" not in txt
        # tag search
        inp.value = "attack"
        await pilot.pause(0.15)
        txt = _history_table_text(screen)
        assert "beta_net" in txt
        assert "alpha_net" not in txt
        # seed search
        inp.value = "11"
        await pilot.pause(0.15)
        txt = _history_table_text(screen)
        assert "alpha_net" in txt


@pytest.mark.asyncio
async def test_history_screen_status_filter(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _make_exp(ws, "exp_c", scenario="s1", seed=1, status="COMPLETED", pdr=0.9)
    _make_exp(ws, "exp_f", scenario="s2", seed=2, status="FAILED", pdr=0.1)
    _make_exp(ws, "exp_i", scenario="s3", seed=3, status="INTERRUPTED", pdr=0.4)
    adapter = WorkspaceAdapter(workspace_root=ws)
    screen = HistoryScreen(workspace_adapter=adapter)
    app = HistoryTestApp(screen)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        await pilot.click("#filter-completed")
        await pilot.pause(0.15)
        txt = _history_table_text(screen)
        assert "COMPLETED" in txt
        assert "FAILED" not in txt
        assert "INTERRUPTED" not in txt
        await pilot.click("#filter-failed")
        await pilot.pause(0.15)
        txt = _history_table_text(screen)
        assert "FAILED" in txt
        assert "COMPLETED" not in txt
        await pilot.click("#filter-all")
        await pilot.pause(0.15)
        assert screen.query_one("#history-table", DataTable).row_count == 3


@pytest.mark.asyncio
async def test_history_screen_enter_opens_results(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _make_exp(ws, "exp_open_me", scenario="s1", seed=1, status="COMPLETED", pdr=0.9)
    adapter = WorkspaceAdapter(workspace_root=ws)
    screen = HistoryScreen(workspace_adapter=adapter)
    pushed: list[Any] = []
    orig_push = None

    class CaptureApp(HistoryTestApp):
        def push_screen(self, screen_obj: Any, *a: Any, **k: Any) -> Any:  # type: ignore[override]
            pushed.append(screen_obj)
            # don't actually push nested in a problematic way during test; but ResultsScreen is fine
            try:
                return super().push_screen(screen_obj, *a, **k)
            except Exception:
                return None

    app = CaptureApp(screen)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        table = screen.query_one("#history-table", DataTable)
        table.focus()
        table.move_cursor(row=0)
        await pilot.pause(0.05)
        await pilot.press("enter")
        await pilot.pause(0.2)
    assert any(isinstance(s, ResultsScreen) for s in pushed)
    # the results screen should target the run
    rs = [s for s in pushed if isinstance(s, ResultsScreen)][0]
    assert rs.experiment_id == "exp_open_me" or getattr(rs, "_requested_experiment_id", None) == "exp_open_me"


@pytest.mark.asyncio
async def test_history_screen_pruning_workflow_success_and_cancellation(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _make_exp(ws, "exp_del1", scenario="s1", seed=1, status="COMPLETED", pdr=0.9)
    _make_exp(ws, "exp_keep", scenario="s2", seed=2, status="COMPLETED", pdr=0.8)
    adapter = WorkspaceAdapter(workspace_root=ws)
    screen = HistoryScreen(workspace_adapter=adapter)
    app = HistoryTestApp(screen)
    calls: list[tuple[str, Any]] = []
    orig_delete = adapter.delete_experiment_run

    def tracked_delete(exp_id: str, expected_preview: Any = None) -> int:
        calls.append((exp_id, expected_preview))
        return orig_delete(exp_id, expected_preview=expected_preview)

    adapter.delete_experiment_run = tracked_delete  # type: ignore[method-assign]

    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        table = screen.query_one("#history-table", DataTable)
        table.focus()
        # select exp_del1 (find row)
        target_row = None
        for i in range(table.row_count):
            row = table.get_row_at(i)
            if "exp_del1" in str(row[0]):
                target_row = i
                break
        assert target_row is not None
        table.move_cursor(row=target_row)
        await pilot.pause(0.05)

        # intercept modal push: cancel first
        real_push = app.push_screen

        def intercept(screen_obj: Any, callback: Any = None, *a: Any, **k: Any) -> Any:
            from manet.screens.prune_modal import PruneConfirmationModal
            if isinstance(screen_obj, PruneConfirmationModal) and callback is not None:
                callback(False)
                return None
            return real_push(screen_obj, callback, *a, **k)

        app.push_screen = intercept  # type: ignore[method-assign]
        await pilot.press("d")
        await pilot.pause(0.15)
        assert calls == []
        assert screen.query_one("#history-table", DataTable).row_count == 2

        # confirm delete
        def intercept_confirm(screen_obj: Any, callback: Any = None, *a: Any, **k: Any) -> Any:
            from manet.screens.prune_modal import PruneConfirmationModal
            if isinstance(screen_obj, PruneConfirmationModal) and callback is not None:
                callback(True)
                return None
            return real_push(screen_obj, callback, *a, **k)

        app.push_screen = intercept_confirm  # type: ignore[method-assign]
        # re-find exp_del1 after refresh not needed yet (cancel didn't change)
        target_row = None
        for i in range(table.row_count):
            row = table.get_row_at(i)
            if "exp_del1" in str(row[0]):
                target_row = i
                break
        assert target_row is not None
        table.focus()
        table.move_cursor(row=target_row)
        await pilot.pause(0.05)
        await pilot.press("d")
        await pilot.pause(0.25)
        assert len(calls) == 1
        assert calls[0][0] == "exp_del1"
        assert calls[0][1] is not None  # expected_preview passed
        assert screen.query_one("#history-table", DataTable).row_count == 1
        assert "exp_keep" in _history_table_text(screen)


@pytest.mark.asyncio
async def test_history_screen_pruning_error_notification(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _make_exp(ws, "exp_err", scenario="s1", seed=1, status="COMPLETED", pdr=0.9)
    adapter = WorkspaceAdapter(workspace_root=ws)
    screen = HistoryScreen(workspace_adapter=adapter)
    app = HistoryTestApp(screen)

    def fail_delete(exp_id: str, expected_preview: Any = None) -> int:
        raise RuntimeError("Windows file lock: handle in use")

    adapter.delete_experiment_run = fail_delete  # type: ignore[method-assign]

    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        table = screen.query_one("#history-table", DataTable)
        table.focus()
        table.move_cursor(row=0)
        await pilot.pause(0.05)
        real_push = app.push_screen

        def intercept_confirm(screen_obj: Any, callback: Any = None, *a: Any, **k: Any) -> Any:
            from manet.screens.prune_modal import PruneConfirmationModal
            if isinstance(screen_obj, PruneConfirmationModal) and callback is not None:
                callback(True)
                return None
            return real_push(screen_obj, callback, *a, **k)

        app.push_screen = intercept_confirm  # type: ignore[method-assign]
        await pilot.press("d")
        await pilot.pause(0.2)
        # screen still active, table intact
        assert app.screen is screen
        assert screen.query_one("#history-table", DataTable).row_count == 1
        assert any("Deletion failed" in m or "Windows file lock" in m for m, _ in app.notifications)
        assert any(sev == "error" for _, sev in app.notifications)
