"""Online intrusion detection and active mitigation coordinator.

Implements OnlineIDS which buffers sliding-window packet events, extracts non-leaking
temporal features matching the training schema, queries the trained champion ML model,
and coordinates dynamic AODV quarantine and route invalidation.
"""

from __future__ import annotations

from collections import deque
import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple, Union

import joblib
import numpy as np
import pandas as pd
import simpy

from feature_extraction.extract_features import SCHEMA_COLUMNS
from simulator.aodv import AODVNode


@dataclass
class BufferedEvent:
    """Lightweight in-memory representation of a packet or node telemetry event."""
    time: float
    src: int
    dst: int
    pkt_id: int
    pkt_type: str
    hop_count: int
    dropped_by: Optional[int]
    node_id: int
    speed: Optional[float]
    neighbor_count: Optional[int]


@dataclass
class IsolationEvent:
    """Record of an active intrusion detection alert, strike, or mitigation action."""
    sim_time: float
    scenario_name: str
    seed: int
    node_id: int
    strike_count: int
    prob_malicious: float
    predicted_type: str
    action: str
    quarantine_until: float
    reason: str


class OnlineIDS:
    """Online intrusion detection and active mitigation coordinator."""

    def __init__(
        self,
        env: simpy.Environment,
        aodv_nodes: Dict[int, AODVNode],
        nodes: Dict[int, Any],
        model_path: Union[str, Path] = "ml/models/best_model.joblib",
        window_size: float = 5.0,
        eval_interval: float = 1.0,
        threshold: float = 0.50,
        quarantine_duration: float = 30.0,
        strikes_required: int = 2,
        flow_endpoints: Optional[Set[int]] = None,
        isolation_log_path: Optional[Path] = None,
        scenario_name: str = "default",
        seed: int = 42,
    ):
        self.env = env
        self.aodv_nodes = aodv_nodes
        self.nodes = nodes
        self.model_path = Path(model_path)
        self.window_size = float(window_size)
        self.eval_interval = float(eval_interval)
        self.threshold = float(threshold)
        self.quarantine_duration = float(quarantine_duration)
        self.strikes_required = int(strikes_required)
        self.flow_endpoints = set(flow_endpoints) if flow_endpoints else set()
        self.isolation_log_path = Path(isolation_log_path) if isolation_log_path else None
        self.scenario_name = scenario_name
        self.seed = seed

        # Load trained champion pipeline
        self.model = joblib.load(self.model_path)

        # In-memory sliding window buffer and delay lookup
        self.event_buffer: deque[BufferedEvent] = deque()
        self.sent_times: Dict[int, float] = {}
        self.delivered_delays: Dict[int, float] = {}
        self.recent_drops: deque[Tuple[float, int]] = deque()

        # Mitigation state trackers
        self.strikes: Dict[int, int] = {}
        self.last_strike_time: Dict[int, float] = {}
        self.quarantined_nodes: Dict[int, float] = {}  # node_id -> expire_time
        self.isolation_events: List[IsolationEvent] = []

    def is_blacklisted(self, node_id: int, now: Optional[float] = None) -> bool:
        """Check whether node_id is currently in the active quarantine blacklist."""
        if node_id not in self.quarantined_nodes:
            return False
        current_time = now if now is not None else self.env.now
        if current_time < self.quarantined_nodes[node_id]:
            return True
        return False

    def ingest_event(
        self,
        sim_time: float,
        src: int,
        dst: int,
        pkt_id: int,
        pkt_type: str,
        hop_count: int = 0,
        dropped_by: Optional[int] = None,
        node_id: Optional[int] = None,
        speed: Optional[float] = None,
        neighbor_count: Optional[int] = None,
    ) -> None:
        """Ingest a packet or status event into the online sliding-window buffer."""
        acting_node = node_id if node_id is not None else src
        d_by = int(dropped_by) if (dropped_by is not None and str(dropped_by) != "") else None
        spd = float(speed) if (speed is not None and str(speed) != "") else None
        nbr = int(neighbor_count) if (neighbor_count is not None and str(neighbor_count) != "") else None

        ev = BufferedEvent(
            time=float(sim_time),
            src=int(src),
            dst=int(dst),
            pkt_id=int(pkt_id),
            pkt_type=str(pkt_type),
            hop_count=int(hop_count) if hop_count is not None else 0,
            dropped_by=d_by,
            node_id=int(acting_node),
            speed=spd,
            neighbor_count=nbr,
        )
        self.event_buffer.append(ev)

        # Track packet transit times for delivered delay calculation
        if ev.pkt_type == "DATA_SENT":
            if ev.pkt_id not in self.sent_times:
                self.sent_times[ev.pkt_id] = ev.time
        elif ev.pkt_type == "DATA_RECV":
            if ev.pkt_id in self.sent_times and ev.pkt_id not in self.delivered_delays:
                self.delivered_delays[ev.pkt_id] = ev.time - self.sent_times[ev.pkt_id]

        # Hybrid event trigger on drop burst (D-05)
        if ev.pkt_type == "DATA_DROP" and ev.dropped_by is not None:
            self.recent_drops.append((ev.time, ev.dropped_by))
            # Prune drops older than 1.0s
            cutoff = ev.time - 1.0
            while self.recent_drops and self.recent_drops[0][0] < cutoff:
                self.recent_drops.popleft()
            drops_by_node = sum(1 for t, nid in self.recent_drops if nid == ev.dropped_by)
            if drops_by_node >= 3:
                # Trigger evaluation step
                self.step_detection(now=ev.time)

    def get_active_nodes(self, now: float) -> List[int]:
        """Identify nodes with active traffic participation in [now - window_size, now]."""
        t_start = now - self.window_size
        active = set()
        for e in self.event_buffer:
            if t_start <= e.time <= now and e.pkt_type != "NODE_STATUS":
                active.add(e.node_id)
                if e.dropped_by is not None and e.dropped_by >= 0:
                    active.add(e.dropped_by)
        return sorted(active)

    def compute_features_for_node(self, nid: int, now: float) -> Optional[Dict[str, float]]:
        """Compute the 9 non-leaking features for a specific node at time now."""
        t_start = now - self.window_size
        win = [e for e in self.event_buffer if t_start <= e.time <= now]
        status_events = [e for e in win if e.pkt_type == "NODE_STATUS" and e.node_id == nid]
        node_pkts = [e for e in win if e.node_id == nid and e.pkt_type != "NODE_STATUS"]

        fwd_count = sum(1 for e in node_pkts if e.pkt_type == "DATA_FWD")
        drop_count = sum(1 for e in win if e.pkt_type == "DATA_DROP" and (e.node_id == nid or e.dropped_by == nid))
        total_traffic = fwd_count + drop_count

        if total_traffic == 0:
            p_fwd_ratio = 1.0
            p_drop_ratio = 0.0
        else:
            p_fwd_ratio = float(fwd_count) / float(total_traffic)
            p_drop_ratio = float(drop_count) / float(total_traffic)

        # Avg delay of delivered packets traversed or terminating at nid
        handled_pids = {e.pkt_id for e in node_pkts if e.pkt_type in ("DATA_SENT", "DATA_FWD", "DATA_RECV")}
        delays = [self.delivered_delays[pid] for pid in handled_pids if pid in self.delivered_delays]
        avg_delay = float(np.mean(delays)) if delays else 0.0

        rreq_count = sum(1 for e in node_pkts if e.pkt_type == "RREQ")
        route_req_rate = float(rreq_count) / self.window_size

        rrep_count = sum(1 for e in node_pkts if e.pkt_type == "RREP")
        route_rep_rate = float(rrep_count) / self.window_size

        recv_count = sum(1 for e in node_pkts if e.pkt_type == "DATA_RECV")
        throughput = float(recv_count * 512 * 8) / self.window_size

        hop_count = float(np.mean([e.hop_count for e in node_pkts])) if node_pkts else 0.0

        # Neighbor count and mobility speed from NODE_STATUS, with node state fallback
        if status_events:
            nbr_vals = [e.neighbor_count for e in status_events if e.neighbor_count is not None]
            nbr_count = float(np.mean(nbr_vals)) if nbr_vals else 0.0
            spd_vals = [e.speed for e in status_events if e.speed is not None]
            mob_speed = float(np.mean(spd_vals)) if spd_vals else 0.0
        else:
            prev_status = [e for e in self.event_buffer if e.pkt_type == "NODE_STATUS" and e.node_id == nid and e.time <= now]
            if prev_status:
                last_st = prev_status[-1]
                nbr_count = float(last_st.neighbor_count) if last_st.neighbor_count is not None else 0.0
                mob_speed = float(last_st.speed) if last_st.speed is not None else 0.0
            elif nid in self.nodes:
                node = self.nodes[nid]
                nbr_count = float(len(getattr(node, "neighbors", [])))
                mob_speed = float(getattr(node, "speed", 0.0))
            else:
                nbr_count = 0.0
                mob_speed = 0.0

        return {
            "packet_forward_ratio": p_fwd_ratio,
            "packet_drop_ratio": p_drop_ratio,
            "avg_delay": avg_delay,
            "route_request_rate": route_req_rate,
            "route_reply_rate": route_rep_rate,
            "throughput": throughput,
            "hop_count": hop_count,
            "neighbor_count": nbr_count,
            "mobility_speed": mob_speed,
        }

    def step_detection(self, now: Optional[float] = None) -> None:
        """Run a single detection and mitigation evaluation cycle at current time."""
        eval_now = now if now is not None else self.env.now

        # Prune events older than window_size + 30.0s to avoid memory bloat
        cutoff = eval_now - max(self.window_size, 30.0)
        while self.event_buffer and self.event_buffer[0].time < cutoff:
            self.event_buffer.popleft()

        # 1. Quarantine maintenance (D-04, D-12)
        for nid, unblock_time in list(self.quarantined_nodes.items()):
            if eval_now >= unblock_time:
                del self.quarantined_nodes[nid]
                self.strikes[nid] = 0
                self.isolation_events.append(
                    IsolationEvent(
                        sim_time=eval_now,
                        scenario_name=self.scenario_name,
                        seed=self.seed,
                        node_id=nid,
                        strike_count=0,
                        prob_malicious=0.0,
                        predicted_type="Normal",
                        action="UNBLOCK",
                        quarantine_until=0.0,
                        reason="Quarantine duration expired; node unblocked",
                    )
                )

        # 2. Active traffic participants (D-07)
        active_nodes = self.get_active_nodes(eval_now)
        if not active_nodes:
            return

        # 3. Extract features for active nodes
        feature_rows: List[List[float]] = []
        valid_nodes: List[int] = []
        feature_cols = SCHEMA_COLUMNS[:9]

        for nid in active_nodes:
            feats = self.compute_features_for_node(nid, eval_now)
            if feats is not None:
                feature_rows.append([feats[col] for col in feature_cols])
                valid_nodes.append(nid)

        if not feature_rows:
            return

        # 4. Batched inference
        batch_df = pd.DataFrame(feature_rows, columns=feature_cols)
        try:
            probas = self.model.predict_proba(batch_df)
        except Exception:
            return

        classes = list(self.model.classes_)
        normal_idx = classes.index("Normal") if "Normal" in classes else -1
        attack_classes = [c for c in classes if c != "Normal"]

        # 5. Confirmation & quarantine logic (D-09, D-10, D-11)
        for i, nid in enumerate(valid_nodes):
            if normal_idx >= 0:
                p_mal = 1.0 - probas[i, normal_idx]
            else:
                p_mal = float(np.max(probas[i]))

            pred_idx = int(np.argmax(probas[i]))
            if classes[pred_idx] != "Normal":
                pred_type = classes[pred_idx]
            else:
                if attack_classes:
                    best_atk_idx = max([classes.index(c) for c in attack_classes], key=lambda idx: probas[i, idx])
                    pred_type = classes[best_atk_idx]
                else:
                    pred_type = "Malicious"

            if p_mal >= self.threshold:
                # Flow endpoint protection (D-11)
                if nid in self.flow_endpoints:
                    self.isolation_events.append(
                        IsolationEvent(
                            sim_time=eval_now,
                            scenario_name=self.scenario_name,
                            seed=self.seed,
                            node_id=nid,
                            strike_count=self.strikes.get(nid, 0),
                            prob_malicious=float(p_mal),
                            predicted_type=pred_type,
                            action="ALERT_ENDPOINT_EXCLUDED",
                            quarantine_until=0.0,
                            reason=f"Suspicious activity (p={p_mal:.4f}) on protected flow endpoint",
                        )
                    )
                else:
                    if nid in self.quarantined_nodes:
                        # Already quarantined
                        continue

                    # Rate-limit strike increments to distinct observation intervals
                    last_time = self.last_strike_time.get(nid, -999.0)
                    if eval_now - last_time >= (self.eval_interval * 0.8):
                        self.strikes[nid] = self.strikes.get(nid, 0) + 1
                        self.last_strike_time[nid] = eval_now

                    cur_strikes = self.strikes[nid]
                    if cur_strikes >= self.strikes_required:
                        quarantine_until = eval_now + self.quarantine_duration
                        self.quarantined_nodes[nid] = quarantine_until
                        # Purge routes through nid across all nodes (D-01, D-03)
                        for aodv_node in self.aodv_nodes.values():
                            aodv_node.invalidate_routes_through(nid)

                        self.isolation_events.append(
                            IsolationEvent(
                                sim_time=eval_now,
                                scenario_name=self.scenario_name,
                                seed=self.seed,
                                node_id=nid,
                                strike_count=cur_strikes,
                                prob_malicious=float(p_mal),
                                predicted_type=pred_type,
                                action="QUARANTINE",
                                quarantine_until=quarantine_until,
                                reason=f"Confirmed malicious behavior after {cur_strikes} strikes (p={p_mal:.4f})",
                            )
                        )
                    else:
                        self.isolation_events.append(
                            IsolationEvent(
                                sim_time=eval_now,
                                scenario_name=self.scenario_name,
                                seed=self.seed,
                                node_id=nid,
                                strike_count=cur_strikes,
                                prob_malicious=float(p_mal),
                                predicted_type=pred_type,
                                action="STRIKE",
                                quarantine_until=0.0,
                                reason=f"Malicious behavior detected strike {cur_strikes}/{self.strikes_required} (p={p_mal:.4f})",
                            )
                        )
            else:
                # Normal behavior observed
                if nid not in self.quarantined_nodes:
                    self.strikes[nid] = 0

    def _periodic_detection_loop(self) -> Generator[simpy.Event, None, None]:
        """SimPy process executing periodic IDS detection scan."""
        while True:
            yield self.env.timeout(self.eval_interval)
            self.step_detection()

    def write_isolation_log(self) -> None:
        """Write isolation events to CSV log."""
        if not self.isolation_log_path:
            return
        self.isolation_log_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "sim_time",
            "scenario_name",
            "seed",
            "node_id",
            "strike_count",
            "prob_malicious",
            "predicted_type",
            "action",
            "quarantine_until",
            "reason",
        ]
        with open(self.isolation_log_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for ev in self.isolation_events:
                writer.writerow(asdict(ev))
