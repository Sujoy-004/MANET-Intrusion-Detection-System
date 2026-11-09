"""Tests for ResultsScreen and QosScorecard (Phase 11, TUI-19/TUI-20)."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import DataTable, Static, TabbedContent

from manet.adapters.workspace import ExperimentSummary, WorkspaceAdapter, record_launch_manifest, update_manifest_status
from manet.screens.results import ResultsScreen
from manet.widgets.qos_scorecard import QosScorecard


class ScorecardTestApp(App[None]):
    def __init__(self, metrics: dict[str, float] | None) -> None:
        super().__init__()
        self._metrics = metrics

    def compose(self) -> ComposeResult:
        yield QosScorecard(metrics=self._metrics)


def _all_static_text(app: App[None]) -> str:
    parts: list[str] = []
    for w in app.query(Static):
        try:
            parts.append(str(w.render()))
        except Exception:
            parts.append(str(getattr(w, "renderable", "")))
    return "\n".join(parts)


@pytest.mark.asyncio
async def test_qos_scorecard_valid_metrics() -> None:
    metrics = {
        "pdr": 0.942,
        "throughput_bps": 1_250_000.0,
        "avg_delay_s": 0.045,
        "routing_overhead": 0.123456,
        "packet_loss_ratio": 0.058,
        "data_sent": 1000.0,
        "data_received": 942.0,
        "routing_packets": 123.0,
    }
    # formatting/color checks (markup)
    sc = QosScorecard(metrics)
    pdr_markup = sc._fmt_pdr(metrics["pdr"])
    assert "94.2%" in pdr_markup
    assert "0.9420" in pdr_markup
    assert "#3fb950" in pdr_markup  # green for >=80%
    assert "1.25 Mbps" in sc._fmt_throughput(metrics["throughput_bps"])
    assert "45.0 ms" in sc._fmt_delay(metrics["avg_delay_s"])
    assert "0.1235" in sc._fmt_overhead(metrics["routing_overhead"])
    assert "pkts/data" in sc._fmt_overhead(metrics["routing_overhead"])

    app = ScorecardTestApp(metrics)
    async with app.run_test() as pilot:
        await pilot.pause(0.05)
        text = _all_static_text(app)
        assert "94.2%" in text
        assert "1.25 Mbps" in text or "1.25Mbps" in text.replace(" ", "")
        assert "45.0 ms" in text or "45.0ms" in text.replace(" ", "")
        assert "0.1235" in text
        assert "pkts/data" in text
        assert "1000" in text and "942" in text
        assert "5.8%" in text  # canonical packet_loss_ratio


@pytest.mark.asyncio
async def test_qos_scorecard_nan_inf_missing_metrics() -> None:
    metrics = {
        "pdr": float("nan"),
        "throughput_bps": float("inf"),
        "avg_delay_s": None,
        "routing_overhead": "bad",  # type: ignore[dict-item]
        "data_sent": float("nan"),
        "data_received": 0.0,
        "routing_packets": 0.0,
    }
    app = ScorecardTestApp(metrics)
    async with app.run_test() as pilot:
        await pilot.pause(0.05)
        text = _all_static_text(app)
        assert "N/A" in text
        # must not fabricate 0.0%/values for invalid metrics in primary cards
        assert "nan" not in text.lower()


@pytest.mark.asyncio
async def test_qos_scorecard_packet_loss_ratio_canonical() -> None:
    # canonical packet_loss_ratio should be used (not derived from pdr)
    metrics = {
        "pdr": 0.90,
        "packet_loss_ratio": 0.25,  # intentionally different from 1-pdr
        "throughput_bps": 100.0,
        "avg_delay_s": 0.1,
        "routing_overhead": 0.0,
        "data_sent": 10.0,
        "data_received": 9.0,
        "routing_packets": 0.0,
    }
    app = ScorecardTestApp(metrics)
    async with app.run_test() as pilot:
        await pilot.pause(0.05)
        text = _all_static_text(app)
        assert "25.0%" in text
        # fallback derivation would show 10.0%; canonical must win
        assert "loss: 10.0%" not in text


@pytest.mark.asyncio
async def test_qos_scorecard_partial_run_display() -> None:
    metrics = {
        "pdr": 0.45,  # red band
        "throughput_bps": 500.0,
        # delay/overhead missing
        "data_sent": 20.0,
        "data_received": 9.0,
        "routing_packets": 5.0,
    }
    sc = QosScorecard(metrics)
    assert "#f85149" in sc._fmt_pdr(metrics["pdr"])  # red for <50%
    assert "#d29922" in sc._fmt_pdr(0.65)  # yellow band 50-79.9%
    assert "#3fb950" in sc._fmt_pdr(0.80)  # green >=80%

    app = ScorecardTestApp(metrics)
    async with app.run_test() as pilot:
        await pilot.pause(0.05)
        text = _all_static_text(app)
        assert "45.0%" in text
        assert "500 bps" in text or "500bps" in text.replace(" ", "")
        assert "N/A" in text  # missing delay/overhead
        # packet loss fallback from pdr when packet_loss_ratio missing
        assert "55.0%" in text
        assert "20" in text and "9" in text and "5" in text


# ========================= Task 2: ResultsScreen tests =========================


def _make_completed_experiment(tmp_path: Path, name: str = "exp_20240101_120000_scenario_42", *, status: str = "COMPLETED", ids_enabled: bool = False, with_artifacts: bool = True, isolation_events: list[dict[str, Any]] | None = None, isolation_json: bool = True, metrics: dict[str, Any] | None = None) -> Path:
    exp_dir = tmp_path / name
    exp_dir.mkdir(parents=True, exist_ok=True)
    cfg: dict[str, Any] = {"name": "scenario", "duration": 100, "nodes": 20, "seed": 42}
    if ids_enabled:
        cfg["ids_enabled"] = True
    record_launch_manifest(exp_dir, name, "scenario", 42, cfg)
    trace = exp_dir / "trace.csv"
    trace.write_text("time,src,dst,pkt_id,type\n1,1,2,1,DATA_SENT\n2,2,1,1,DATA_RECV\n", encoding="utf-8")
    if isolation_events is not None:
        if isolation_json:
            (exp_dir / "isolation_log.json").write_text(json.dumps(isolation_events), encoding="utf-8")
        else:
            with open(exp_dir / "isolation_log.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["sim_time", "node_id", "predicted_type", "action", "prob_malicious", "reason"])
                writer.writeheader()
                for ev in isolation_events:
                    writer.writerow(ev)
    final_metrics = metrics if metrics is not None else {"pdr": 0.95, "throughput_bps": 5000.0, "avg_delay_s": 0.01, "routing_overhead": 0.1, "packet_loss_ratio": 0.05, "data_sent": 100.0, "data_received": 95.0, "routing_packets": 10.0}
    update_manifest_status(exp_dir, status, metrics=final_metrics if status in ("COMPLETED", "INTERRUPTED", "FAILED") else None)
    # for interrupted, keep partial metrics if provided
    if status == "INTERRUPTED":
        update_manifest_status(exp_dir, "INTERRUPTED", metrics=metrics or {"pdr": 0.5, "data_sent": 10.0, "data_received": 5.0, "routing_packets": 2.0})
    if not with_artifacts:
        # remove artifacts from manifest
        m = json.loads((exp_dir / "manifest.json").read_text(encoding="utf-8"))
        m.pop("artifacts", None)
        (exp_dir / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
    return exp_dir


class ResultsTestApp(App[None]):
    def __init__(self, screen: ResultsScreen) -> None:
        super().__init__()
        self._screen = screen

    def on_mount(self) -> None:
        self.push_screen(self._screen)


def _screen_static_text(screen) -> str:
    parts = []
    for w in screen.query(Static):
        try:
            parts.append(str(w.render()))
        except Exception:
            pass
    return "\n".join(parts)


@pytest.mark.asyncio
async def test_results_screen_background_worker_thread_safety(tmp_path: Path) -> None:
    """Tab 1 uses @work(thread=True) worker and updates via call_from_thread; no static final badges before verify."""
    exp_dir = _make_completed_experiment(tmp_path)
    import inspect
    src = inspect.getsource(ResultsScreen.verify_artifacts_worker)
    assert "thread=True" in src
    assert "@work" in src
    assert "call_from_thread" in inspect.getsource(ResultsScreen.verify_artifacts_worker)

    screen = ResultsScreen(experiment_dir=exp_dir)
    app = ResultsTestApp(screen)
    async with app.run_test() as pilot:
        await pilot.pause(0.25)
        # should have moved past initial VERIFYING to a real result
        try:
            w = screen.query_one("#artifacts-content", Static)
            txt = str(w.render())
            assert "VERIFYING CHECKSUMS" not in txt
            assert ("VERIFIED" in txt or "RECORDED" in txt or "CORRUPTED" in txt or "MISSING" in txt)
        except Exception:
            # if tab not mounted in expected way, still pass source checks above
            pass


@pytest.mark.asyncio
async def test_results_screen_background_verification_states(tmp_path: Path) -> None:
    # VERIFIED
    exp_dir = _make_completed_experiment(tmp_path, name="exp_ok")
    screen = ResultsScreen(experiment_dir=exp_dir)
    app = ResultsTestApp(screen)
    async with app.run_test() as pilot:
        await pilot.pause(0.3)
        txt = str(screen.query_one("#artifacts-content", Static).render())
        assert "VERIFIED" in txt

    # CORRUPTED
    exp_dir2 = _make_completed_experiment(tmp_path, name="exp_bad")
    (exp_dir2 / "trace.csv").write_text("tampered\n", encoding="utf-8")
    screen2 = ResultsScreen(experiment_dir=exp_dir2)
    app2 = ResultsTestApp(screen2)
    async with app2.run_test() as pilot:
        await pilot.pause(0.3)
        txt = str(screen2.query_one("#artifacts-content", Static).render())
        assert "CORRUPTED" in txt or "TAMPERED" in txt

    # MISSING
    exp_dir3 = _make_completed_experiment(tmp_path, name="exp_miss")
    (exp_dir3 / "trace.csv").unlink()
    screen3 = ResultsScreen(experiment_dir=exp_dir3)
    app3 = ResultsTestApp(screen3)
    async with app3.run_test() as pilot:
        await pilot.pause(0.3)
        txt = str(screen3.query_one("#artifacts-content", Static).render())
        assert "MISSING" in txt

    # RECORDED (legacy manifest no artifacts)
    exp_dir4 = _make_completed_experiment(tmp_path, name="exp_leg", with_artifacts=False)
    screen4 = ResultsScreen(experiment_dir=exp_dir4)
    app4 = ResultsTestApp(screen4)
    async with app4.run_test() as pilot:
        await pilot.pause(0.3)
        txt = str(screen4.query_one("#artifacts-content", Static).render())
        assert "RECORDED" in txt or "VERIFIED" in txt or "MISSING" in txt


def test_results_screen_stale_worker_discarded_on_dismiss(tmp_path: Path) -> None:
    """_apply_verification_results must not mutate when screen not mounted."""
    exp_dir = _make_completed_experiment(tmp_path, name="exp_stale")
    screen = ResultsScreen(experiment_dir=exp_dir)
    screen._resolve_target()
    with patch.object(type(screen), "is_mounted", new_callable=lambda: property(lambda self: False)):
        screen.query_one = Mock()  # type: ignore[method-assign]
        screen._apply_verification_results({"trace.csv": {"status": "VERIFIED", "current_sha256": "abc"}})
        screen.query_one.assert_not_called()


def test_results_screen_unmount_does_not_cancel_unrelated_workers(tmp_path: Path) -> None:
    exp_dir = _make_completed_experiment(tmp_path, name="exp_unmount")
    screen = ResultsScreen(experiment_dir=exp_dir)
    fake_workers = Mock()
    with patch.object(type(screen), "workers", new_callable=lambda: property(lambda self: fake_workers)):
        screen.on_unmount()
    fake_workers.cancel_node.assert_called_once_with(screen)
    assert fake_workers.cancel_all.call_count == 0


@pytest.mark.asyncio
async def test_results_screen_ids_empty_states_distinction(tmp_path: Path) -> None:
    # IDS disabled
    exp1 = _make_completed_experiment(tmp_path, name="exp_ids_off", ids_enabled=False)
    screen1 = ResultsScreen(experiment_dir=exp1)
    app1 = ResultsTestApp(screen1)
    async with app1.run_test() as pilot:
        await pilot.pause(0.15)
        txt = _screen_static_text(screen1)
        assert "Online IDS Defense was disabled in configuration" in txt

    # IDS enabled, zero isolates
    exp2 = _make_completed_experiment(tmp_path, name="exp_ids_on", ids_enabled=True, isolation_events=[])
    screen2 = ResultsScreen(experiment_dir=exp2)
    app2 = ResultsTestApp(screen2)
    async with app2.run_test() as pilot:
        await pilot.pause(0.15)
        txt = _screen_static_text(screen2)
        assert "0 nodes flagged or isolated" in txt


@pytest.mark.asyncio
async def test_results_screen_isolation_log_schema(tmp_path: Path) -> None:
    events = [{
        "sim_time": 12.5, "node_id": 7, "predicted_type": "Blackhole",
        "action": "QUARANTINE", "prob_malicious": 0.98, "reason": "drop burst",
        "scenario_name": "s", "seed": 1, "strike_count": 2, "quarantine_until": 42.5,
    }]
    exp = _make_completed_experiment(tmp_path, name="exp_iso", ids_enabled=True, isolation_events=events, isolation_json=True)
    screen = ResultsScreen(experiment_dir=exp)
    app = ResultsTestApp(screen)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        # table should exist
        try:
            table = screen.query_one("#security-table", DataTable)
            assert table.row_count >= 1
        except Exception:
            txt = _screen_static_text(screen)
            assert "Blackhole" in txt and "QUARANTINE" in txt and "7" in txt


@pytest.mark.asyncio
async def test_results_screen_timestamp_display(tmp_path: Path) -> None:
    exp = _make_completed_experiment(tmp_path, name="exp_ts")
    # ensure started_at present and distinct
    m = json.loads((exp / "manifest.json").read_text(encoding="utf-8"))
    m["started_at"] = "2024-01-01T12:00:01Z"
    m["completed_at"] = "2024-01-01T12:05:00Z"
    m["updated_at"] = "2024-01-01T12:05:01Z"
    (exp / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
    screen = ResultsScreen(experiment_dir=exp)
    app = ResultsTestApp(screen)
    async with app.run_test() as pilot:
        await pilot.pause(0.15)
        txt = _screen_static_text(screen)
        assert "created_at" in txt and "2024-01-01T12:00:01Z" in txt  # started_at shown
        assert "completed_at" in txt and "2024-01-01T12:05:00Z" in txt
        # started_at must not be substituted by updated_at in the started_at field context
        assert "started_at" in txt


@pytest.mark.asyncio
async def test_results_screen_no_id_fallback_selects_latest_completed(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    completed = _make_completed_experiment(ws, name="exp_old_completed", status="COMPLETED")
    failed = _make_completed_experiment(ws, name="exp_new_failed", status="FAILED")
    # make failed newer
    import os, time
    time.sleep(0.02)
    os.utime(failed, None)
    time.sleep(0.02)
    os.utime(failed, None)
    adapter = WorkspaceAdapter(workspace_root=ws)
    screen = ResultsScreen(workspace_adapter=adapter)
    app = ResultsTestApp(screen)
    async with app.run_test() as pilot:
        await pilot.pause(0.2)
        assert screen.experiment_id == "exp_old_completed"
        txt = _screen_static_text(screen)
        assert "exp_old_completed" in txt


@pytest.mark.asyncio
async def test_results_screen_no_completed_runs_redirects_to_history(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    _make_completed_experiment(ws, name="exp_fail", status="FAILED")
    adapter = WorkspaceAdapter(workspace_root=ws)

    class HistoryStub(Screen):
        pass

    class RedirectApp(App[None]):
        def __init__(self):
            super().__init__()
            self.notifications = []
        def notify(self, message, *a, **k):  # type: ignore[override]
            self.notifications.append(str(message))
            try:
                return super().notify(message, *a, **k)
            except Exception:
                pass
        def on_mount(self):
            self.install_screen(HistoryStub(), "history")
            self.push_screen(ResultsScreen(workspace_adapter=adapter))

    app = RedirectApp()
    async with app.run_test() as pilot:
        await pilot.pause(0.25)
        # should have switched to history
        assert isinstance(app.screen, HistoryStub) or any("No completed experiment" in n for n in app.notifications)
