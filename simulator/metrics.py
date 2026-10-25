"""Network Quality of Service (QoS) and Routing Performance Metrics.

Computes Packet Delivery Ratio (PDR), throughput, end-to-end delay, packet loss,
and routing overhead from simulation traces.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import pandas as pd


@dataclass
class NetworkMetrics:
    """Summary of standard MANET QoS performance metrics."""
    pdr: float
    throughput_bps: float
    avg_delay_s: float
    packet_loss_ratio: float
    routing_overhead: float
    data_sent: int
    data_received: int
    routing_packets: int


def compute_pdr(data_sent: int, data_received: int) -> float:
    """Compute Packet Delivery Ratio (PDR)."""
    if data_sent <= 0:
        return 0.0
    return float(data_received) / float(data_sent)


def compute_metrics_from_df(df: pd.DataFrame, sim_duration: float = 300.0) -> NetworkMetrics:
    """Compute all network metrics from a trace DataFrame."""
    if df.empty:
        return NetworkMetrics(
            pdr=0.0,
            throughput_bps=0.0,
            avg_delay_s=0.0,
            packet_loss_ratio=0.0,
            routing_overhead=0.0,
            data_sent=0,
            data_received=0,
            routing_packets=0,
        )

    # Filter events
    sent_events = df[df["type"] == "DATA_SENT"]
    recv_events = df[df["type"] == "DATA_RECV"]
    routing_events = df[df["type"].isin(["RREQ", "RREP", "RERR"])]

    data_sent = len(sent_events)
    data_received = len(recv_events)
    routing_packets = len(routing_events)

    pdr = compute_pdr(data_sent, data_received)
    loss_ratio = 1.0 - pdr if data_sent > 0 else 0.0

    # Calculate average end-to-end delay by matching pkt_id between SENT and RECV
    avg_delay = 0.0
    if not sent_events.empty and not recv_events.empty:
        # Merge on pkt_id
        sent_sub = sent_events[["pkt_id", "time"]].rename(columns={"time": "send_time"}).astype({"send_time": float})
        recv_sub = recv_events[["pkt_id", "time"]].rename(columns={"time": "recv_time"}).astype({"recv_time": float})
        merged = pd.merge(sent_sub, recv_sub, on="pkt_id")
        if not merged.empty:
            delays = merged["recv_time"] - merged["send_time"]
            avg_delay = float(delays.mean())

    # Throughput in bits per second (assuming 512-byte payload = 4096 bits)
    payload_bits = data_received * 512 * 8
    duration = max(sim_duration, 1.0)
    throughput_bps = float(payload_bits) / duration

    # Routing overhead
    routing_overhead = float(routing_packets) / float(data_sent) if data_sent > 0 else 0.0

    return NetworkMetrics(
        pdr=pdr,
        throughput_bps=throughput_bps,
        avg_delay_s=avg_delay,
        packet_loss_ratio=loss_ratio,
        routing_overhead=routing_overhead,
        data_sent=data_sent,
        data_received=data_received,
        routing_packets=routing_packets,
    )


def compute_metrics(
    trace_source: Union[str, Path, pd.DataFrame, Sequence[Sequence[Any]]],
    sim_duration: float = 300.0,
) -> Dict[str, float]:
    """Calculate network metrics dictionary from trace file, DataFrame, or rows."""
    if isinstance(trace_source, (str, Path)):
        path = Path(trace_source)
        if not path.exists():
            raise FileNotFoundError(f"Trace file not found: {path}")
        df = pd.read_csv(path)
    elif isinstance(trace_source, pd.DataFrame):
        df = trace_source
    else:
        header = ["time", "src", "dst", "pkt_id", "type", "hop_count", "dropped_by"]
        df = pd.DataFrame(trace_source, columns=header)

    m = compute_metrics_from_df(df, sim_duration=sim_duration)
    return {
        "pdr": m.pdr,
        "throughput_bps": m.throughput_bps,
        "avg_delay_s": m.avg_delay_s,
        "packet_loss_ratio": m.packet_loss_ratio,
        "routing_overhead": m.routing_overhead,
        "data_sent": float(m.data_sent),
        "data_received": float(m.data_received),
        "routing_packets": float(m.routing_packets),
    }
