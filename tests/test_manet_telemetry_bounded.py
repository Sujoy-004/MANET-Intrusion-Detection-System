"""Concurrency stress, boundedness, and overflow validation tests for TelemetrySink.

Verifies:
- Telemetry ring buffer strictly respects maxlen=500 under high-rate burst.
- Drop-oldest eviction increments overflow_count without blocking producers.
- Authentic packet counters preserve exact totals across buffer evictions.
- Multi-threaded concurrent producer-consumer operates cleanly without deadlocks or counter races.
- Draining batches respects max_items bound and leaves remainder in ring buffer.
"""

from __future__ import annotations

import threading
import time

from manet.adapters.execution import TelemetryEvent
from manet.runtime.telemetry import TelemetrySink


def _make_event(pkt_id: int, pkt_type: str = "DATA_SENT", sim_time: float = 0.0) -> TelemetryEvent:
    return TelemetryEvent(
        sim_time=sim_time,
        src=1,
        dst=2,
        pkt_id=pkt_id,
        pkt_type=pkt_type,
        hop_count=1,
        dropped_by="",
        node_id=1,
        speed="0.0",
        neighbor_count="5",
    )


def test_bounded_telemetry_under_burst():
    """Verify TelemetrySink retains exactly maxlen items and tracks overflow accurately."""
    sink = TelemetrySink(maxlen=500)
    total_events = 10000

    for i in range(total_events):
        sink.record_event(_make_event(pkt_id=i, sim_time=float(i) * 0.01))

    # Assert exactly 500 events remain
    assert len(sink._events) == 500
    assert sink.overflow_count == 9500

    # Assert newest events (IDs 9500 to 9999) are preserved in order
    snapshot = sink.drain_batch(max_items=500)
    assert len(snapshot.events) == 500
    assert snapshot.events[0].pkt_id == 9500
    assert snapshot.events[-1].pkt_id == 9999


def test_authentic_counter_aggregation():
    """Verify authentic packet counters track true totals even after buffer eviction."""
    sink = TelemetrySink(maxlen=100)

    # Emit 300 DATA_SENT, 700 DATA_FWD, 250 DATA_RECV, 50 DATA_DROP (1300 total)
    for i in range(300):
        sink.record_event(_make_event(pkt_id=i, pkt_type="DATA_SENT"))
    for i in range(700):
        sink.record_event(_make_event(pkt_id=i + 300, pkt_type="DATA_FWD"))
    for i in range(250):
        sink.record_event(_make_event(pkt_id=i + 1000, pkt_type="DATA_RECV"))
    for i in range(50):
        sink.record_event(_make_event(pkt_id=i + 1250, pkt_type="DATA_DROP"))

    assert sink.data_sent == 300
    assert sink.data_fwd == 700
    assert sink.data_recv == 250
    assert sink.data_drop == 50

    # Ensure snapshot carries identical counters
    snapshot = sink.drain_batch(max_items=50)
    assert snapshot.data_sent == 300
    assert snapshot.data_fwd == 700
    assert snapshot.data_recv == 250
    assert snapshot.data_drop == 50
    assert snapshot.overflow_count == 1200


def test_concurrent_producer_consumer_lock_safety():
    """Verify multi-threaded producers and a consumer run concurrently without deadlocks or count skew."""
    sink = TelemetrySink(maxlen=500)
    stop_event = threading.Event()
    num_producers = 4
    producer_counts = [0] * num_producers
    threads: list[threading.Thread] = []

    def producer_worker(idx: int) -> None:
        count = 0
        pkt_types = ["DATA_SENT", "DATA_FWD", "DATA_RECV", "DATA_DROP"]
        while not stop_event.is_set():
            t = pkt_types[count % 4]
            sink.record_event(_make_event(pkt_id=count, pkt_type=t, sim_time=float(count) * 0.001))
            count += 1
        producer_counts[idx] = count

    def consumer_worker() -> None:
        while not stop_event.is_set():
            sink.drain_batch(max_items=100)
            time.sleep(0.01)

    for i in range(num_producers):
        t = threading.Thread(target=producer_worker, args=(i,))
        threads.append(t)
        t.start()

    c_thread = threading.Thread(target=consumer_worker)
    c_thread.start()

    # Run for 1.0 second
    time.sleep(1.0)
    stop_event.set()

    for t in threads:
        t.join(timeout=2.0)
    c_thread.join(timeout=2.0)

    total_produced = sum(producer_counts)
    total_counted = sink.data_sent + sink.data_fwd + sink.data_recv + sink.data_drop
    assert total_produced > 0
    assert total_counted == total_produced


def test_drain_batch_bounds():
    """Verify drain_batch respects max_items and leaves the remainder in the sink."""
    sink = TelemetrySink(maxlen=500)
    for i in range(500):
        sink.record_event(_make_event(pkt_id=i))

    snapshot = sink.drain_batch(max_items=100)
    assert len(snapshot.events) == 100
    assert snapshot.events[0].pkt_id == 0
    assert snapshot.events[-1].pkt_id == 99
    assert len(sink._events) == 400

    remainder = sink.drain_batch(max_items=500)
    assert len(remainder.events) == 400
    assert remainder.events[0].pkt_id == 100
    assert remainder.events[-1].pkt_id == 499
    assert len(sink._events) == 0
