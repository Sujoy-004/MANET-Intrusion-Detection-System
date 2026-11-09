"""Dedicated live execution terminal monitor screen for MANET IDS TUI.

Provides:
- Authentic SimPy virtual-time progress bar (env.now / duration bounded to [0.0, 100.0]%).
- Monotonic wall-clock elapsed time display.
- Authentic packet counters (DATA_SENT, DATA_FWD, DATA_RECV, DATA_DROP, OVERFLOW).
- Throttled 20Hz (50ms) telemetry draining into bounded RichLog(max_lines=500).
- Permanent disabled Pause button with honest runner capability explanation (TUI-18).
- Safe stop controls triggering cooperative cancellation.
- Reconnectable observer architecture supporting background navigation.
"""

from __future__ import annotations

import time
from typing import Any, Optional

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Footer, Header, ProgressBar, RichLog, Static

from manet.runtime.keymap import (
    BINDING_BACKGROUND,
    BINDING_STOP,
)
from manet.runtime.supervisor import WorkloadState, WorkloadSupervisor


STAGE_BADGES = {
    "IDLE": "[dim]IDLE[/]",
    "CONFIGURED": "[cyan]CONFIGURED[/]",
    "INITIALIZING": "[cyan]INITIALIZING[/]",
    "SIMULATING": "[bold green]SIMULATING[/]",
    "FINALIZING": "[bold yellow]FINALIZING[/]",
    "COMPLETED": "[bold green]COMPLETED[/]",
    "INTERRUPTED": "[bold #d29922]INTERRUPTED[/]",
    "FAILED": "[bold red]FAILED[/]",
}


class LiveRunScreen(Screen):
    """Live simulation telemetry monitor screen."""

    BINDINGS = [
        Binding(BINDING_BACKGROUND, "background_run", "Background", show=True),
        Binding("escape", "background_run", "Back", show=False),
        Binding(BINDING_STOP, "stop_run", "Stop", show=True),
    ]

    CSS = """
    LiveRunScreen {
        layout: vertical;
        background: #0a0e14;
        color: #e6edf3;
        padding: 0;
    }

    #live-header-container {
        dock: top;
        height: 1;
        background: #161b22;
        color: #58a6ff;
        padding: 0 1;
    }

    #live-metadata-strip {
        height: 2;
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 0 1;
    }

    #live-progress-container {
        height: 4;
        background: #0d1117;
        padding: 0 1;
        border-bottom: solid #30363d;
    }

    #live-progress-bar {
        width: 100%;
        margin-top: 0;
        margin-bottom: 0;
    }

    #live-progress-labels {
        height: 1;
        layout: horizontal;
    }

    #live-sim-time-label {
        width: 1fr;
        color: #58a6ff;
    }

    #live-elapsed-time-label {
        width: 1fr;
        text-align: right;
        color: #8b949e;
    }

    #live-counters-grid {
        height: 2;
        background: #161b22;
        border-bottom: solid #30363d;
        padding: 0 1;
    }

    #live-event-log {
        height: 1fr;
        background: #0a0e14;
        border: solid #21262d;
        padding: 0 1;
    }

    #live-controls-bar {
        dock: bottom;
        height: 3;
        background: #161b22;
        border-top: solid #30363d;
        layout: horizontal;
        align: center middle;
        padding: 0 1;
    }

    #live-controls-bar Button {
        margin: 0 1;
        min-width: 18;
    }

    #btn-pause:disabled {
        opacity: 50%;
        color: #8b949e;
    }
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._drain_timer: Optional[Timer] = None
        self._terminal_drained: bool = False

    def compose(self) -> ComposeResult:
        """Compose 80x24 responsive monitor layout."""
        yield Header(show_clock=True)
        yield Static("[bold #58a6ff]LIVE SIMULATION MONITOR[/] - MANET Discrete-Event Telemetry", id="live-header-container")

        yield Static("Initializing workload metadata...", id="live-metadata-strip")

        with Vertical(id="live-progress-container"):
            yield ProgressBar(show_eta=False, id="live-progress-bar", total=100.0)
            with Horizontal(id="live-progress-labels"):
                yield Static("Simulated: 0.0s / 0.0s", id="live-sim-time-label")
                yield Static("Elapsed: 0.0s", id="live-elapsed-time-label")

        yield Static("SENT: 0 | FWD: 0 | RECV: 0 | DROP: 0 | OVERFLOW: 0", id="live-counters-grid")

        yield RichLog(max_lines=500, markup=True, auto_scroll=True, id="live-event-log")

        with Horizontal(id="live-controls-bar"):
            yield Button("[B] Background", id="btn-background", variant="default")
            pause_btn = Button("[P] Pause (Disabled)", id="btn-pause", variant="default", disabled=True)
            pause_btn.tooltip = "Pause not supported by runner"
            yield pause_btn
            yield Button("[X] Stop", id="btn-stop", variant="error")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize telemetry draining timer and refresh observer state."""
        self._terminal_drained = False
        self._update_metadata()
        self._drain_telemetry()
        self._drain_timer = self.set_interval(0.05, self._drain_telemetry)

    def _get_supervisor(self) -> Optional[WorkloadSupervisor]:
        return getattr(self.app, "supervisor", None)

    def _update_metadata(self) -> None:
        sup = self._get_supervisor()
        if not sup or not sup.current_request:
            self.query_one("#live-metadata-strip", Static).update(
                "[dim]No active simulation request found on supervisor.[/]"
            )
            return

        req = sup.current_request
        ids_badge = "[bold green]ACTIVE[/]" if req.ids_enabled else "[dim]OFF[/]"
        stage_badge = STAGE_BADGES.get(sup.stage, f"[cyan]{sup.stage}[/]")

        meta_line1 = f"Experiment: [bold]{escape(req.experiment_id)}[/] | Scenario: [bold]{escape(req.scenario_name)}[/] | Seed: [bold]{req.seed}[/]"
        meta_line2 = f"IDS Defense: {ids_badge} | Stage: {stage_badge}"
        self.query_one("#live-metadata-strip", Static).update(f"{meta_line1}\n{meta_line2}")

    def _drain_telemetry(self) -> None:
        """Periodic 20Hz UI telemetry drain and widget synchronizer."""
        sup = self._get_supervisor()
        if not sup:
            return

        # Synchronize metadata badges
        self._update_metadata()

        # Drain up to 100 events
        snapshot = sup.telemetry.drain_batch(max_items=100)

        # Update Progress Bar (SimPy virtual time)
        duration = max(1.0, snapshot.duration)
        ratio = min(1.0, max(0.0, snapshot.sim_now / duration)) * 100.0
        try:
            pbar = self.query_one("#live-progress-bar", ProgressBar)
            pbar.progress = ratio
        except Exception:
            pass

        # Update simulated & wall elapsed time labels
        elapsed = (time.monotonic() - sup.start_monotonic) if sup.start_monotonic > 0 else 0.0
        try:
            self.query_one("#live-sim-time-label", Static).update(
                f"Simulated: [bold]{snapshot.sim_now:.1f}s[/] / {snapshot.duration:.1f}s"
            )
            self.query_one("#live-elapsed-time-label", Static).update(
                f"Wall Elapsed: [bold]{elapsed:.1f}s[/]"
            )
        except Exception:
            pass

        # Update Authentic Counters Grid
        overflow_badge = (
            f"[bold #d29922]{snapshot.overflow_count}[/]"
            if snapshot.overflow_count > 0
            else f"{snapshot.overflow_count}"
        )
        counters_text = (
            f"DATA_SENT: [bold #58a6ff]{snapshot.data_sent}[/] | "
            f"DATA_FWD: [bold #39c5cf]{snapshot.data_fwd}[/] | "
            f"DATA_RECV: [bold #3fb950]{snapshot.data_recv}[/] | "
            f"DATA_DROP: [bold #f85149]{snapshot.data_drop}[/] | "
            f"OVERFLOW: {overflow_badge}"
        )
        try:
            self.query_one("#live-counters-grid", Static).update(counters_text)
        except Exception:
            pass

        # Append drained events to RichLog
        try:
            log_widget = self.query_one("#live-event-log", RichLog)
            for event in snapshot.events:
                line = self._format_event_line(event)
                log_widget.write(line)
        except Exception:
            pass

        # Check terminal states
        if sup.state in (WorkloadState.COMPLETED, WorkloadState.INTERRUPTED, WorkloadState.FAILED):
            if not self._terminal_drained:
                self._handle_terminal_state(sup)

    def _format_event_line(self, event: Any) -> str:
        """Format raw network telemetry event with SOC colors."""
        t_type = event.pkt_type
        if t_type == "DATA_SENT":
            type_tag = "[bold #58a6ff]DATA_SENT[/]"
        elif t_type == "DATA_FWD":
            type_tag = "[bold #39c5cf]DATA_FWD [/]"
        elif t_type == "DATA_RECV":
            type_tag = "[bold #3fb950]DATA_RECV[/]"
        elif t_type == "DATA_DROP":
            type_tag = f"[bold #f85149]DATA_DROP (by {escape(str(event.dropped_by))})[/]"
        elif t_type == "NODE_STATUS":
            type_tag = f"[bold #d29922]STATUS Node {event.node_id} (spd={escape(str(event.speed))}, nbrs={escape(str(event.neighbor_count))})[/]"
        else:
            type_tag = f"[cyan]{escape(t_type)}[/]"

        return f"[dim]{event.sim_time:8.2f}s[/] | {type_tag} | src={event.src} dst={event.dst} pkt={event.pkt_id} hops={event.hop_count}"

    def _handle_terminal_state(self, sup: WorkloadSupervisor) -> None:
        """Flush final telemetry buffer and finalize UI on simulation termination."""
        self._terminal_drained = True

        # Stop periodic draining timer
        if self._drain_timer is not None:
            self._drain_timer.stop()

        # Perform final drain to capture any remaining events in ring buffer
        final_snapshot = sup.telemetry.drain_batch(max_items=500)
        try:
            log_widget = self.query_one("#live-event-log", RichLog)
            for event in final_snapshot.events:
                log_widget.write(self._format_event_line(event))

            # Terminal announcement in event log
            if sup.state == WorkloadState.COMPLETED:
                pdr_pct = f"{sup.metrics.get('pdr', 0.0) * 100:.1f}%" if sup.metrics else "N/A"
                thru = f"{sup.metrics.get('throughput_bps', 0.0):.0f} bps" if sup.metrics else "N/A"
                log_widget.write(f"\n[bold green]>>> SIMULATION COMPLETED SUCCESSFULLY: PDR={pdr_pct}, Throughput={thru}[/]")
            elif sup.state == WorkloadState.INTERRUPTED:
                log_widget.write("\n[bold #d29922]>>> SIMULATION INTERRUPTED BY OPERATOR: Partial traces preserved on disk.[/]")
            elif sup.state == WorkloadState.FAILED:
                err_msg = escape(str(sup.last_error or 'Unknown simulation failure'))
                log_widget.write(f"\n[bold red]>>> SIMULATION FAILED: {err_msg}[/]")
        except Exception:
            pass

        # Update stop button to back button
        try:
            stop_btn = self.query_one("#btn-stop", Button)
            stop_btn.label = "[Esc] Back to Workspace"
            stop_btn.variant = "primary"
        except Exception:
            pass

    def action_background_run(self) -> None:
        """Switch view back to main workspace without stopping background simulation."""
        if hasattr(self.app, "switch_screen"):
            self.app.switch_screen("workspace")
        else:
            self.dismiss()

    def action_stop_run(self) -> None:
        """Signal cooperative cancellation to running simulation."""
        sup = self._get_supervisor()
        if sup and sup.is_running:
            sup.cancel_simulation()
            self._update_metadata()
            try:
                self.query_one("#live-event-log", RichLog).write(
                    "[bold #d29922]Cancellation requested by operator. Waiting for worker to finalize...[/]"
                )
            except Exception:
                pass
        else:
            # If already stopped/completed, act like back button
            self.action_background_run()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle control button clicks."""
        if event.button.id == "btn-background":
            self.action_background_run()
        elif event.button.id == "btn-stop":
            sup = self._get_supervisor()
            if sup and sup.is_running:
                self.action_stop_run()
            else:
                self.action_background_run()


__all__ = ["LiveRunScreen"]
