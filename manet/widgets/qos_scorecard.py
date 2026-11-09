"""Academic QoS Scorecard widget for MANET experiment results (TUI-19)."""

from __future__ import annotations

import math
from typing import Any, Callable

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static


def _is_valid_number(val: Any) -> bool:
    return val is not None and isinstance(val, (int, float)) and not isinstance(val, bool) and not math.isnan(float(val)) and not math.isinf(float(val))


def _format_metric(val: Any, formatter: Callable[[float], str], unit: str = "") -> str:
    """Validate and format a metric value; returns dim N/A for invalid values."""
    if not _is_valid_number(val):
        return "[dim]N/A[/]"
    formatted = formatter(float(val))
    if unit:
        formatted = f"{formatted}{unit}"
    return escape(formatted)


class QosScorecard(Container):
    """QoS Scorecard rendering the four primary MANET metrics with SOC color badges."""

    DEFAULT_CSS = """
    QosScorecard {
        height: auto;
        border: solid #30363d;
        background: #0d1117;
        padding: 0 1;
        margin-bottom: 1;
    }
    QosScorecard #scorecard-cards {
        height: auto;
        layout: horizontal;
    }
    QosScorecard .scorecard-card {
        width: 1fr;
        height: auto;
        border: solid #21262d;
        padding: 0 1;
        margin: 0 1 0 0;
    }
    QosScorecard .metric-val {
        text-style: bold;
    }
    QosScorecard #scorecard-subcounters {
        height: auto;
        margin-top: 1;
        padding: 0 1;
        color: #8b949e;
    }
    """

    def __init__(
        self,
        metrics: dict[str, float] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.metrics = metrics or {}

    def _fmt_pdr(self, pdr: Any) -> str:
        if not _is_valid_number(pdr):
            return "[dim]N/A[/]"
        v = float(pdr)
        # Visual presentation heuristic: green >=80%, yellow 50-79.9%, red <50%
        if v >= 0.8:
            color = "#3fb950"
        elif v >= 0.5:
            color = "#d29922"
        else:
            color = "#f85149"
        pct = escape(f"{v * 100:.1f}%")
        ratio = escape(f"({v:.4f})")
        return f"[bold {color}]{pct}[/] [dim]{ratio}[/]"

    def _fmt_throughput(self, thru: Any) -> str:
        if not _is_valid_number(thru):
            return "[dim]N/A[/]"
        v = float(thru)
        if v >= 1_000_000:
            s = f"{v / 1_000_000:.2f} Mbps"
        elif v >= 1_000:
            s = f"{v / 1_000:.2f} kbps"
        else:
            s = f"{v:.0f} bps"
        return f"[bold #58a6ff]{escape(s)}[/]"

    def _fmt_delay(self, delay: Any) -> str:
        if not _is_valid_number(delay):
            return "[dim]N/A[/]"
        v = float(delay)
        if v < 1.0:
            s = f"{v * 1000:.1f} ms"
        else:
            s = f"{v:.3f} s"
        return f"[bold #39c5cf]{escape(s)}[/]"

    def _fmt_overhead(self, overhead: Any) -> str:
        if not _is_valid_number(overhead):
            return "[dim]N/A[/]"
        v = float(overhead)
        s = f"{v:.4f}"
        return f"[bold #d29922]{escape(s)}[/] [dim]pkts/data[/]"

    def _fmt_count(self, val: Any) -> str:
        if not _is_valid_number(val):
            return "[dim]N/A[/]"
        return f"[bold]{escape(str(int(round(float(val)))))}[/]"

    def _loss_text(self) -> str:
        loss_ratio = self.metrics.get("packet_loss_ratio")
        pdr = self.metrics.get("pdr")
        if _is_valid_number(loss_ratio):
            return f"loss: {float(loss_ratio) * 100:.1f}%"
        if _is_valid_number(pdr):
            derived = (1.0 - float(pdr)) * 100.0
            return f"loss: {derived:.1f}%"
        return "loss: N/A"

    def compose(self) -> ComposeResult:
        pdr = self.metrics.get("pdr")
        thru = self.metrics.get("throughput_bps")
        delay = self.metrics.get("avg_delay_s")
        overhead = self.metrics.get("routing_overhead")
        sent = self.metrics.get("data_sent")
        recv = self.metrics.get("data_received")
        routing = self.metrics.get("routing_packets")

        with Horizontal(id="scorecard-cards"):
            with Vertical(classes="scorecard-card"):
                yield Static("[dim]PACKET DELIVERY RATIO[/]")
                yield Static(self._fmt_pdr(pdr), classes="metric-val")
            with Vertical(classes="scorecard-card"):
                yield Static("[dim]NETWORK THROUGHPUT[/]")
                yield Static(self._fmt_throughput(thru), classes="metric-val")
            with Vertical(classes="scorecard-card"):
                yield Static("[dim]END-TO-END DELAY[/]")
                yield Static(self._fmt_delay(delay), classes="metric-val")
            with Vertical(classes="scorecard-card"):
                yield Static("[dim]ROUTING OVERHEAD[/]")
                yield Static(self._fmt_overhead(overhead), classes="metric-val")

        loss_part = escape(self._loss_text())
        sub = (
            f"[dim]Data Traffic:[/] {self._fmt_count(sent)} sent | "
            f"{self._fmt_count(recv)} recvd ({loss_part}) | "
            f"[dim]Routing:[/] {self._fmt_count(routing)} packets"
        )
        with Horizontal(id="scorecard-subcounters"):
            yield Static(sub, id="subcounters-text")


__all__ = ["QosScorecard", "_format_metric"]
