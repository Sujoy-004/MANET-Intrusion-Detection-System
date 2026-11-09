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
from textual.widgets import DataTable, Static, TabbedContent

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
