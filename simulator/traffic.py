"""Constant Bit Rate (CBR) / UDP traffic generation for MANET.

Manages application layer flows with configurable packet size, transmission rates,
staggered start times, and source-destination pairs.
"""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Any, Callable, Dict, Generator, List, Optional

import simpy


@dataclass
class DataPacket:
    """Represents a CBR/UDP application data packet."""
    pkt_id: int
    src: int
    dst: int
    payload_size: int
    timestamp: float
    hop_count: int = 0


class CBRTraffic:
    """Generates constant bit rate packet traffic for a flow."""

    def __init__(
        self,
        env: simpy.Environment,
        flow_id: int,
        src: int,
        dst: int,
        rate_pps: float,
        start_time: float,
        duration: float,
        payload_size: int,
        send_fn: Callable[[DataPacket], None],
        get_pkt_id_fn: Callable[[], int],
    ):
        self.env = env
        self.flow_id = flow_id
        self.src = src
        self.dst = dst
        self.rate_pps = float(rate_pps)
        self.start_time = float(start_time)
        self.duration = float(duration)
        self.payload_size = int(payload_size)
        self.send_fn = send_fn
        self.get_pkt_id = get_pkt_id_fn

        self.action = self.env.process(self._run())

    def _run(self) -> Generator[simpy.Event, None, None]:
        """Traffic generator event loop."""
        # Wait until flow start time
        if self.start_time > self.env.now:
            yield self.env.timeout(self.start_time - self.env.now)

        interval = 1.0 / self.rate_pps if self.rate_pps > 0 else 1.0
        end_time = self.start_time + self.duration

        while self.env.now < end_time:
            pkt = DataPacket(
                pkt_id=self.get_pkt_id(),
                src=self.src,
                dst=self.dst,
                payload_size=self.payload_size,
                timestamp=self.env.now,
                hop_count=0,
            )
            self.send_fn(pkt)
            yield self.env.timeout(interval)


def generate_flows(
    env: simpy.Environment,
    flow_configs: List[Dict[str, Any]],
    send_fn: Callable[[DataPacket], None],
    get_pkt_id_fn: Callable[[], int],
    default_payload: int = 512,
) -> List[CBRTraffic]:
    """Instantiate CBRTraffic instances from flow configurations."""
    flows: List[CBRTraffic] = []
    for cfg in flow_configs:
        flow = CBRTraffic(
            env=env,
            flow_id=cfg.get("flow_id", len(flows)),
            src=cfg["src"],
            dst=cfg["dst"],
            rate_pps=cfg.get("rate_pps", 4.0),
            start_time=cfg.get("start_time", 0.0),
            duration=cfg.get("duration", 280.0),
            payload_size=cfg.get("payload_size", default_payload),
            send_fn=send_fn,
            get_pkt_id_fn=get_pkt_id_fn,
        )
        flows.append(flow)
    return flows
