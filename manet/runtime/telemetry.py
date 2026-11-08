"""Thread-safe bounded live telemetry ring buffer and authentic event aggregation.

Decouples high-frequency discrete-event simulation emissions from UI rendering
using a synchronized bounded deque (drop-oldest eviction) and atomic integer counters.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass
import threading
from typing import List

from manet.adapters.execution import TelemetryEvent


@dataclass(frozen=True)
class TelemetrySnapshot:
    """Immutable snapshot of drained telemetry events and current counters."""

    sim_now: float
    duration: float
    data_sent: int
    data_fwd: int
    data_recv: int
    data_drop: int
    overflow_count: int
    events: List[TelemetryEvent]


class TelemetrySink:
    """Thread-safe bounded ring buffer with O(1) event ingestion and authentic counters."""

    def __init__(self, maxlen: int = 500) -> None:
        self.maxlen = maxlen
        self._lock = threading.Lock()
        self._events: collections.deque[TelemetryEvent] = collections.deque(maxlen=maxlen)
        self._sim_now = 0.0
        self._duration = 0.0
        self._data_sent = 0
        self._data_fwd = 0
        self._data_recv = 0
        self._data_drop = 0
        self._overflow_count = 0

    def reset(self, duration: float = 0.0) -> None:
        """Reset ring buffer and counters for a new simulation run."""
        with self._lock:
            self._events.clear()
            self._sim_now = 0.0
            self._duration = float(duration)
            self._data_sent = 0
            self._data_fwd = 0
            self._data_recv = 0
            self._data_drop = 0
            self._overflow_count = 0

    def update_progress(self, sim_now: float, duration: float) -> None:
        """Update simulation progress coordinates under lock."""
        with self._lock:
            self._sim_now = float(sim_now)
            self._duration = float(duration)

    def record_event(self, event: TelemetryEvent) -> None:
        """Record an event, increment authentic counters, and buffer with drop-oldest eviction."""
        with self._lock:
            pkt_type = event.pkt_type
            if pkt_type == "DATA_SENT":
                self._data_sent += 1
            elif pkt_type == "DATA_FWD":
                self._data_fwd += 1
            elif pkt_type == "DATA_RECV":
                self._data_recv += 1
            elif pkt_type == "DATA_DROP":
                self._data_drop += 1

            if len(self._events) >= self.maxlen:
                self._overflow_count += 1

            self._events.append(event)
            self._sim_now = float(event.sim_time)

    def drain_batch(self, max_items: int = 100) -> TelemetrySnapshot:
        """Drain up to max_items events from the ring buffer and return a snapshot."""
        with self._lock:
            popped: List[TelemetryEvent] = []
            count = min(max_items, len(self._events))
            for _ in range(count):
                popped.append(self._events.popleft())

            return TelemetrySnapshot(
                sim_now=self._sim_now,
                duration=self._duration,
                data_sent=self._data_sent,
                data_fwd=self._data_fwd,
                data_recv=self._data_recv,
                data_drop=self._data_drop,
                overflow_count=self._overflow_count,
                events=popped,
            )

    @property
    def sim_now(self) -> float:
        with self._lock:
            return self._sim_now

    @property
    def duration(self) -> float:
        with self._lock:
            return self._duration

    @property
    def data_sent(self) -> int:
        with self._lock:
            return self._data_sent

    @property
    def data_fwd(self) -> int:
        with self._lock:
            return self._data_fwd

    @property
    def data_recv(self) -> int:
        with self._lock:
            return self._data_recv

    @property
    def data_drop(self) -> int:
        with self._lock:
            return self._data_drop

    @property
    def overflow_count(self) -> int:
        with self._lock:
            return self._overflow_count

    def __len__(self) -> int:
        with self._lock:
            return len(self._events)


__all__ = [
    "TelemetrySink",
    "TelemetrySnapshot",
]
