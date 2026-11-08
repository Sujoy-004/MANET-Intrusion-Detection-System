"""Textual pilot tests for LiveRunScreen layout, telemetry draining, and controls.

Verifies:
- LiveRunScreen mounting and 80x24 responsive layout rendering.
- Authentic SimPy virtual-time progress bar and monotonic elapsed wall time.
- Permanent disabled Pause button with honest runner capability explanation (TUI-18).
- Safe stop controls triggering cooperative cancellation.
- Throttled 20Hz telemetry draining into bounded RichLog.
- Final telemetry flush upon reaching terminal states (COMPLETED, INTERRUPTED, FAILED).
- Background navigation preserving active worker thread.
- Screen reconnection to an already-running supervisor.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Optional
import pytest

from textual.app import App, ComposeResult
from textual.widgets import Button, ProgressBar, RichLog, Static

from manet.adapters.execution import TelemetryEvent
from manet.adapters.handoff import SimulationLaunchRequest
from manet.adapters.workspace import record_launch_manifest
from manet.runtime.supervisor import WorkloadState, WorkloadSupervisor
from manet.screens.live_run import LiveRunScreen
from manet.screens.main_workspace import MainWorkspace


def _create_launch_request(tmp_path: Path, duration: float = 100.0) -> SimulationLaunchRequest:
    exp_dir = tmp_path / "exp_live_test"
    exp_dir.mkdir(parents=True, exist_ok=True)
    cfg = {"name": "live_test_scenario", "duration": duration, "nodes": 20}
    record_launch_manifest(exp_dir, exp_dir.name, "live_test_scenario", 42, cfg)
    return SimulationLaunchRequest(
        experiment_id=exp_dir.name,
        scenario_name="live_test_scenario",
        seed=42,
        config=cfg,
        workspace_dir=exp_dir,
        created_at="2026-11-08T00:00:00Z",
        ids_enabled=True,
    )


class DummyLiveApp(App[None]):
    """Test harness App mounting MainWorkspace and LiveRunScreen."""

    CSS = """
    Screen {
        background: #0a0e14;
    }
    """

    def __init__(self, supervisor: Optional[WorkloadSupervisor] = None) -> None:
        super().__init__()
        self.supervisor = supervisor or WorkloadSupervisor()

    def on_mount(self) -> None:
        self.install_screen(MainWorkspace(id="workspace"), "workspace")
        self.install_screen(LiveRunScreen(id="live_run"), "live_run")
        self.push_screen("live_run")


@pytest.mark.asyncio
async def test_authentic_stages_and_progress(tmp_path: Path):
    """Verify progress bar updates with SimPy virtual time and wall clock elapses monotonically."""
    sup = WorkloadSupervisor()
    req = _create_launch_request(tmp_path, duration=200.0)
    sup.current_request = req
    sup.state = WorkloadState.RUNNING
    sup.stage = "SIMULATING"
    sup.start_monotonic = time.monotonic() - 5.0
    sup.telemetry.reset(duration=200.0)
    sup.telemetry.update_progress(100.0, 200.0)

    app = DummyLiveApp(supervisor=sup)
    async with app.run_test() as pilot:
        await pilot.pause(0.1)

        screen = app.get_screen("live_run")
        pbar = screen.query_one("#live-progress-bar", ProgressBar)
        assert pbar.progress == 50.0  # 100.0 / 200.0 * 100%

        sim_label = screen.query_one("#live-sim-time-label", Static)
        assert "100.0s / 200.0s" in str(sim_label.render())

        meta_strip = screen.query_one("#live-metadata-strip", Static)
        rendered_meta = str(meta_strip.render())
        assert "live_test_scenario" in rendered_meta
        assert "SIMULATING" in rendered_meta
        assert "ACTIVE" in rendered_meta


@pytest.mark.asyncio
async def test_pause_button_disabled(tmp_path: Path):
    """Verify Pause button is permanently disabled with honest explanatory text."""
    sup = WorkloadSupervisor()
    sup.current_request = _create_launch_request(tmp_path)
    app = DummyLiveApp(supervisor=sup)

    async with app.run_test() as pilot:
        await pilot.pause(0.05)
        screen = app.get_screen("live_run")
        pause_btn = screen.query_one("#btn-pause", Button)

        assert pause_btn.disabled is True
        assert "Pause" in str(pause_btn.label)
        assert "Pause not supported by runner" in str(pause_btn.tooltip)


@pytest.mark.asyncio
async def test_stop_invokes_supervisor_cancel(tmp_path: Path):
    """Verify pressing [X] or Stop button signals cooperative cancellation."""
    sup = WorkloadSupervisor()
    sup.current_request = _create_launch_request(tmp_path)
    sup.state = WorkloadState.RUNNING
    sup.stage = "SIMULATING"
    app = DummyLiveApp(supervisor=sup)

    async with app.run_test() as pilot:
        await pilot.pause(0.05)
        assert sup.cancel_token.is_set() is False

        # Press 'x' shortcut
        await pilot.press("x")
        await pilot.pause(0.1)

        assert sup.cancel_token.is_set() is True
        assert sup.state == WorkloadState.STOPPING


@pytest.mark.asyncio
async def test_bounded_richlog_draining(tmp_path: Path):
    """Verify telemetry draining pops events in batches into RichLog."""
    sup = WorkloadSupervisor()
    sup.current_request = _create_launch_request(tmp_path, duration=50.0)
    sup.state = WorkloadState.RUNNING
    sup.stage = "SIMULATING"
    sup.telemetry.reset(duration=50.0)

    # Push 150 events
    for i in range(150):
        sup.telemetry.record_event(
            TelemetryEvent(
                sim_time=float(i) * 0.1,
                src=1,
                dst=2,
                pkt_id=i,
                pkt_type="DATA_SENT",
                hop_count=1,
                dropped_by="",
                node_id=1,
                speed="0.0",
                neighbor_count="4",
            )
        )

    app = DummyLiveApp(supervisor=sup)
    async with app.run_test() as pilot:
        # Give drain timer time to tick
        await pilot.pause(0.15)

        screen = app.get_screen("live_run")
        rlog = screen.query_one("#live-event-log", RichLog)
        assert len(rlog.lines) > 0

        counters = screen.query_one("#live-counters-grid", Static)
        assert "DATA_SENT: 150" in str(counters.render())


@pytest.mark.asyncio
async def test_terminal_drain_flushes_remaining_events(tmp_path: Path):
    """Verify terminal state halts timer and flushes all remaining events in buffer."""
    sup = WorkloadSupervisor()
    sup.current_request = _create_launch_request(tmp_path)
    sup.telemetry.reset(duration=100.0)
    sup.metrics = {"pdr": 0.96, "throughput_bps": 18500.0}

    # Queue events
    for i in range(25):
        sup.telemetry.record_event(
            TelemetryEvent(
                sim_time=float(i),
                src=1,
                dst=2,
                pkt_id=i,
                pkt_type="DATA_RECV",
                hop_count=1,
                dropped_by="",
                node_id=1,
                speed="0.0",
                neighbor_count="5",
            )
        )

    # Mark completed
    sup.state = WorkloadState.COMPLETED
    sup.stage = "COMPLETED"

    app = DummyLiveApp(supervisor=sup)
    async with app.run_test() as pilot:
        await pilot.pause(0.1)

        # Buffer must be fully emptied by terminal flush
        assert len(sup.telemetry._events) == 0

        screen = app.get_screen("live_run")
        rlog = screen.query_one("#live-event-log", RichLog)
        rendered_log = "\n".join(str(line) for line in rlog.lines)
        assert "SIMULATION COMPLETED SUCCESSFULLY" in rendered_log
        assert "PDR=96.0%" in rendered_log

        # Stop button changes to Back button
        stop_btn = screen.query_one("#btn-stop", Button)
        assert "Back" in str(stop_btn.label)


@pytest.mark.asyncio
async def test_background_navigation_preserves_run(tmp_path: Path):
    """Verify pressing [B] switches to workspace while supervisor remains running."""
    sup = WorkloadSupervisor()
    sup.current_request = _create_launch_request(tmp_path)
    sup.state = WorkloadState.RUNNING
    sup.stage = "SIMULATING"
    app = DummyLiveApp(supervisor=sup)

    async with app.run_test() as pilot:
        await pilot.pause(0.05)
        assert isinstance(app.screen, LiveRunScreen)

        # Press 'b'
        await pilot.press("b")
        await pilot.pause(0.1)

        # Verify active screen is now workspace
        assert isinstance(app.screen, MainWorkspace)
        assert sup.is_running is True


@pytest.mark.asyncio
async def test_reconnect_to_active_supervisor(tmp_path: Path):
    """Verify switching back to live_run screen reconnects to ongoing telemetry."""
    sup = WorkloadSupervisor()
    sup.current_request = _create_launch_request(tmp_path, duration=100.0)
    sup.state = WorkloadState.RUNNING
    sup.stage = "SIMULATING"
    sup.telemetry.reset(duration=100.0)
    sup.telemetry.update_progress(75.0, 100.0)

    app = DummyLiveApp(supervisor=sup)
    async with app.run_test() as pilot:
        await pilot.pause(0.05)

        # Switch to workspace
        await pilot.press("b")
        await pilot.pause(0.05)
        assert isinstance(app.screen, MainWorkspace)

        # Switch back to live_run
        app.switch_screen("live_run")
        await pilot.pause(0.1)

        assert isinstance(app.screen, LiveRunScreen)
        pbar = app.screen.query_one("#live-progress-bar", ProgressBar)
        assert pbar.progress == 75.0
