"""Sliding-window feature extractor assembling non-leaking 10-column tabular datasets.

Converts raw packet event traces into temporal behavioral features for machine learning
intrusion detection with strict anti-leakage isolation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd


SCHEMA_COLUMNS = [
    "packet_forward_ratio",
    "packet_drop_ratio",
    "avg_delay",
    "route_request_rate",
    "route_reply_rate",
    "throughput",
    "hop_count",
    "neighbor_count",
    "mobility_speed",
    "label",
]


def extract_features_from_trace(
    trace_df: pd.DataFrame,
    scenario_config: Dict[str, Any],
    window_size: float = 5.0,
    step_size: float = 1.0,
    warmup: float = 10.0,
    min_packets: int = 0,
    attacker_ids: Optional[List[int]] = None,
) -> pd.DataFrame:
    """Extract sliding-window tabular features from event trace DataFrame.

    Aggregates events over sliding intervals [t - window_size, t] for each node.
    Enforces strict anti-leakage boundaries: feature matrix X contains zero node
    identities, coordinates, or oracle markers.
    """
    if trace_df.empty:
        return pd.DataFrame(columns=SCHEMA_COLUMNS)

    # Coerce types cleanly
    df = trace_df.copy()
    df["time"] = pd.to_numeric(df["time"], errors="coerce").fillna(0.0)
    df["node_id"] = pd.to_numeric(df["node_id"], errors="coerce").fillna(-1).astype(int)
    df["hop_count"] = pd.to_numeric(df["hop_count"], errors="coerce").fillna(0).astype(int)
    df["speed"] = pd.to_numeric(df["speed"], errors="coerce")
    df["neighbor_count"] = pd.to_numeric(df["neighbor_count"], errors="coerce")
    if "dropped_by" in df.columns:
        df["dropped_by"] = pd.to_numeric(df["dropped_by"], errors="coerce").fillna(-1).astype(int)
    else:
        df["dropped_by"] = -1

    # Extract attacker set strictly from scenario configuration or explicit argument
    attacker_nodes: Set[int] = set()
    if attacker_ids is not None:
        attacker_nodes = set(attacker_ids)
    else:
        attack_cfg = scenario_config.get("attack", {})
        if attack_cfg.get("enabled", False):
            attackers_spec = attack_cfg.get("attackers", [])
            if isinstance(attackers_spec, list) and all(isinstance(x, int) for x in attackers_spec):
                attacker_nodes = set(attackers_spec)
            elif isinstance(attackers_spec, int):
                attacker_nodes = {attackers_spec}
            elif "attacker_ids" in attack_cfg:
                attacker_nodes = set(attack_cfg["attacker_ids"])
            elif "attacker_ids" in scenario_config:
                attacker_nodes = set(scenario_config["attacker_ids"])

    # Determine node set
    num_nodes = int(scenario_config.get("nodes", 30))
    all_nodes = list(range(num_nodes))

    # Pre-calculate end-to-end delays for delivered packets (pkt_id -> delay)
    sent_events = df[df["type"] == "DATA_SENT"][["pkt_id", "time"]].drop_duplicates("pkt_id")
    recv_events = df[df["type"] == "DATA_RECV"][["pkt_id", "time"]].drop_duplicates("pkt_id")
    merged_delays = pd.merge(sent_events, recv_events, on="pkt_id", suffixes=("_sent", "_recv"))
    pkt_delays: Dict[int, float] = {}
    if not merged_delays.empty:
        merged_delays["delay"] = merged_delays["time_recv"] - merged_delays["time_sent"]
        pkt_delays = dict(zip(merged_delays["pkt_id"], merged_delays["delay"]))

    # Sort trace by time for status tracking
    df = df.sort_values("time").reset_index(drop=True)

    max_time = float(df["time"].max())
    if max_time < warmup:
        return pd.DataFrame(columns=SCHEMA_COLUMNS)

    # Time steps for sliding window
    time_steps = np.arange(warmup, max_time + 1e-9, step_size)

    # Pre-filter status events
    status_df = df[df["type"] == "NODE_STATUS"]

    rows: List[Dict[str, Any]] = []

    for t in time_steps:
        t_start = t - window_size
        win = df[(df["time"] >= t_start) & (df["time"] <= t)]
        win_status = status_df[(status_df["time"] >= t_start) & (status_df["time"] <= t)]

        # Group window by node_id for efficient aggregation
        win_by_node = {nid: grp for nid, grp in win.groupby("node_id")} if not win.empty else {}
        status_by_node = {nid: grp for nid, grp in win_status.groupby("node_id")} if not win_status.empty else {}

        for nid in all_nodes:
            node_win = win_by_node.get(nid, None)

            if node_win is not None:
                pkt_events = node_win[node_win["type"] != "NODE_STATUS"]
                total_pkts = len(pkt_events)
            else:
                total_pkts = 0

            # Filter if below min_packets threshold
            if total_pkts < min_packets:
                continue

            # 1 & 2: Forward and Drop ratio
            if node_win is not None:
                fwd_count = len(node_win[node_win["type"] == "DATA_FWD"])
                # Count drops where node dropped the packet
                drop_count = len(win[(win["type"] == "DATA_DROP") & ((win["node_id"] == nid) | (win["dropped_by"] == nid))])
            else:
                fwd_count = 0
                drop_count = 0

            total_traffic = fwd_count + drop_count
            if total_traffic == 0:
                # D-07 Neutral zero-traffic handling
                p_fwd_ratio = 1.0
                p_drop_ratio = 0.0
            else:
                p_fwd_ratio = float(fwd_count) / float(total_traffic)
                p_drop_ratio = float(drop_count) / float(total_traffic)

            # 3: Average delay of delivered packets traversed or terminating at nid
            avg_delay = 0.0
            if node_win is not None:
                handled_pkts = node_win[node_win["type"].isin(["DATA_SENT", "DATA_FWD", "DATA_RECV"])]["pkt_id"].unique()
                delays = [pkt_delays[pid] for pid in handled_pkts if pid in pkt_delays]
                if delays:
                    avg_delay = float(np.mean(delays))

            # 4: Route request rate (Hz)
            rreq_count = len(node_win[node_win["type"] == "RREQ"]) if node_win is not None else 0
            route_req_rate = float(rreq_count) / window_size

            # 5: Route reply rate (Hz)
            rrep_count = len(node_win[node_win["type"] == "RREP"]) if node_win is not None else 0
            route_rep_rate = float(rrep_count) / window_size

            # 6: Throughput (bps) for packets successfully received by nid
            recv_count = len(node_win[node_win["type"] == "DATA_RECV"]) if node_win is not None else 0
            throughput = float(recv_count * 512 * 8) / window_size

            # 7: Average hop count of data/routing packets handled
            hop_count = 0.0
            if node_win is not None and not pkt_events.empty:
                hop_count = float(pkt_events["hop_count"].mean())

            # 8 & 9: Neighbor count and mobility speed from NODE_STATUS
            node_status = status_by_node.get(nid, None)
            if node_status is not None and not node_status.empty:
                nbr_count = float(node_status["neighbor_count"].dropna().mean()) if not node_status["neighbor_count"].dropna().empty else 0.0
                mob_speed = float(node_status["speed"].dropna().mean()) if not node_status["speed"].dropna().empty else 0.0
            else:
                # Fallback to latest known status up to time t
                prev_status = status_df[(status_df["node_id"] == nid) & (status_df["time"] <= t)]
                if not prev_status.empty:
                    last_row = prev_status.iloc[-1]
                    nbr_count = float(last_row["neighbor_count"]) if pd.notna(last_row["neighbor_count"]) else 0.0
                    mob_speed = float(last_row["speed"]) if pd.notna(last_row["speed"]) else 0.0
                else:
                    nbr_count = 0.0
                    mob_speed = 0.0

            # 10: Ground truth label strictly from scenario metadata
            label = "Blackhole" if nid in attacker_nodes else "Normal"

            rows.append({
                "packet_forward_ratio": p_fwd_ratio,
                "packet_drop_ratio": p_drop_ratio,
                "avg_delay": avg_delay,
                "route_request_rate": route_req_rate,
                "route_reply_rate": route_rep_rate,
                "throughput": throughput,
                "hop_count": hop_count,
                "neighbor_count": nbr_count,
                "mobility_speed": mob_speed,
                "label": label,
            })

    out_df = pd.DataFrame(rows, columns=SCHEMA_COLUMNS)
    # Ensure no NaN or inf values remain
    out_df = out_df.fillna(0.0)
    for col in SCHEMA_COLUMNS[:-1]:
        out_df[col] = out_df[col].replace([np.inf, -np.inf], 0.0)

    return out_df


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI options for feature extraction."""
    parser = argparse.ArgumentParser(description="Sliding-Window MANET Feature Extractor")
    parser.add_argument("--trace", type=str, required=True, help="Path to input trace CSV")
    parser.add_argument("--scenario", type=str, required=True, help="Path to scenario JSON config")
    parser.add_argument("--out", type=str, required=True, help="Path to output feature CSV")
    parser.add_argument("--window", type=float, default=5.0, help="Sliding window size in seconds (default: 5.0)")
    parser.add_argument("--step", type=float, default=1.0, help="Step size in seconds (default: 1.0)")
    parser.add_argument("--warmup", type=float, default=10.0, help="Warmup period in seconds (default: 10.0)")
    parser.add_argument("--min-packets", type=int, default=0, help="Minimum packet count threshold (default: 0)")
    return parser.parse_args(args)


def main() -> None:
    """CLI execution entrypoint."""
    args = parse_args()
    trace_path = Path(args.trace)
    scenario_path = Path(args.scenario)
    out_path = Path(args.out)

    if not trace_path.exists():
        raise FileNotFoundError(f"Trace file not found: {trace_path}")
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

    trace_df = pd.read_csv(trace_path)
    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario = json.load(f)

    # Check if attacker is dynamic; if so, trace may tell us which node was the dynamic attacker
    # if it was recorded in scenario metadata or we identify attacker from scenario setup
    features_df = extract_features_from_trace(
        trace_df=trace_df,
        scenario_config=scenario,
        window_size=args.window,
        step_size=args.step,
        warmup=args.warmup,
        min_packets=args.min_packets,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(out_path, index=False)
    print(f"Extracted {len(features_df)} feature rows to: {out_path}")


if __name__ == "__main__":
    main()
