# Phase 02: Blackhole Attack, Trace Logging & Feature Pipeline — Research Report

**Phase:** 02 — Blackhole Attack, Trace Logging & Feature Pipeline  
**Status:** Complete  
**Date:** 2026-10-25  
**Author:** Phase Researcher  

---

## 1. Executive Summary & Phase Mission

Phase 02 bridges the pure-Python discrete-event MANET simulator constructed in Phase 01 to the Machine Learning classification pipeline scheduled for Phase 03. The primary mission of this phase is threefold:
1. **Controlled Adversarial Injection:** Implement a decoupled Blackhole attack strategy adhering to RFC 3561 AODV mechanics (spoofed highest destination sequence number, 1-hop distance advertisement, and 100% silent dropping of intercepted data packets).
2. **Self-Contained Event Trace Logging:** Enhance packet trace logging with acting `node_id` annotations and periodic `NODE_STATUS` telemetry events, capturing dynamic node speed and neighbor counts directly within the CSV trace without requiring out-of-band state files.
3. **Non-Leaking Sliding-Window Feature Extraction:** Convert raw CSV traces into a standardized 10-column tabular dataset using a backward-looking sliding window ($W = 5.0\text{s}$, $\Delta t = 1.0\text{s}$), strictly isolating ground-truth labels from feature columns to prevent oracle leakage.
4. **Gate 2 Quantitative Verification:** Prove that the Blackhole attack causes a relative Packet Delivery Ratio (PDR) drop of $\ge 25\%$ under identical random seeds (42, 43, 44) versus baseline unprotected AODV before proceeding to ML training.

Empirical prototyping conducted during this research confirmed that dynamic intermediate node placement reduces network PDR by **52.60% (seed 42)**, **77.36% (seed 43)**, and **87.62% (seed 44)**, vastly exceeding the Gate 2 threshold ($\ge 25\%$).

---

## 2. Architectural Design & Decoupled Strategy Pattern

### 2.1 The Import Boundary Constraint (Binding Rule)
Per `AGENTS.md:67-69` and `ARCHITECTURE.md:134-135`, **no module under `simulator/` may import `attacks/` directly**. The core simulator engine (`mobility.py`, `radio.py`, `aodv.py`, `traffic.py`, `metrics.py`) must remain completely attack-agnostic. 

- **Composition Root:** All cross-package wiring occurs exclusively in `simulator/run_scenario.py`.
- **Duck-Typed Hook:** `AODVNode` exposes an optional attribute `self.attack_behavior: Optional[Any] = None`. In baseline runs, `self.attack_behavior is None`.
- **Attack Strategy Package:** `attacks/` is a top-level standalone package containing pure behavior strategies that depend only on the Python standard library. `attacks/` never imports `simulator/`.

```
                    ┌────────────────────────┐
                    │ simulator/run_scenario │ (Composition Root)
                    └───────────┬────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌──────────────────┐                         ┌──────────────────┐
│    simulator/    │                         │     attacks/     │
│  - aodv.py       │ ◄── injects strategy    │  - base.py       │
│  - radio.py      │     at scenario start   │  - blackhole.py  │
│  - mobility.py   │                         │  - registry.py   │
│  - traffic.py    │ (never imports attacks) │ (never imports   │
│  - metrics.py    │                         │  simulator)      │
└──────────────────┘                         └──────────────────┘
```

### 2.2 Attack Package Layout
The `attacks/` package is structured as follows:
- `attacks/__init__.py`: Package initialization and version exposure.
- `attacks/base.py`: Protocol/ABC `AttackStrategy` defining method hooks:
  - `get_spoofed_rrep_params(dest: int, rreq_dest_seq: int) -> Tuple[int, int]`
  - `should_drop_data(pkt_src: int, pkt_dst: int, pkt_id: int) -> bool`
- `attacks/blackhole.py`: `BlackholeStrategy` class implementing lying RREP sequence number offsets (+1000 default) and 100% data dropping.
- `attacks/registry.py`: Factory method `create_attack_strategy(attack_type: str, **params) -> AttackStrategy`.

---

## 3. Attack Mechanism: RFC 3561 Blackhole Spoofing & Dropping

### 3.1 RFC 3561 Route Discovery Vulnerability
In standard AODV, route selection at originator nodes prioritizes:
1. Higher destination sequence number (`dest_seq > existing.dest_seq`), signifying fresher routing information.
2. Equal destination sequence number with smaller hop count (`dest_seq == existing.dest_seq and hop_count < existing.hop_count`).

A Blackhole attacker exploits this deterministic rule by immediately replying to any received `RREQ` (for which it is not the destination) with:
$$\text{dest\_seq}_{\text{spoofed}} = \max(\text{known\_seq}, \text{rreq.dest\_seq}) + \text{seq\_offset}$$
$$\text{hop\_count}_{\text{spoofed}} = 1$$

Because $\text{seq\_offset} \ge 500$ (default 1000), the originator node's `update_route` method evaluates `dest_seq > existing.dest_seq == True`, instantly installing the malicious node as the next-hop router. Legitimate RREPs arriving later from intermediate nodes or the genuine destination are discarded by the originator as stale.

### 3.2 Data Packet Interception & Dropping
Once the malicious route is established:
1. Source nodes forward CBR application `DataPacket` instances towards the attacker.
2. In `SimulationRunner._route_and_forward_data`, when a packet arrives at `current_hop`:
   ```python
   if aodv_node.attack_behavior is not None and aodv_node.attack_behavior.should_drop_data():
       self.log_event(
           sim_time=self.env.now,
           node_id=current_hop,
           src=pkt.src,
           dst=pkt.dst,
           pkt_id=pkt.pkt_id,
           pkt_type="DATA_DROP",
           hop_count=pkt.hop_count,
           dropped_by=current_hop,
       )
       return  # Halt forwarding pipeline
   ```
3. 100% of data traffic routed through the Blackhole is silently dropped. Control traffic (RREQ flooding, reverse path maintenance) continues so the node maintains network presence.

---

## 4. Dynamic Flow-Intercept Placement Algorithm

### 4.1 The Challenge of Static Placement
In mobile ad-hoc topologies with sparse traffic matrices (e.g. 6 CBR flows across 30 nodes), an arbitrarily chosen static attacker node (e.g., node 14) may not reside on any active forwarding path. Our empirical test on seed 42 demonstrated that static node 14 caused only a 15.58% PDR drop, failing Gate 2.

### 4.2 Dynamic Flow-Intercept Placement Formulation (`D-01`)
Per Decision `D-01`, `SimulationRunner` analyzes the initial network connectivity graph $G = (V, E)$ at $t = 0.0\text{s}$ and the configured traffic flows to select an intermediate node guaranteed to intercept active flows:

```python
def select_dynamic_attacker(runner: SimulationRunner, flows: List[Dict[str, Any]]) -> int:
    """Select intermediate node along active CBR flow paths to guarantee interception."""
    G = nx.Graph()
    for nid, node_state in runner.nodes.items():
        G.add_node(nid)
        for nb in node_state.neighbors:
            G.add_edge(nid, nb)

    # Protect flow endpoints from being selected as malicious nodes
    endpoints = set(f["src"] for f in flows) | set(f["dst"] for f in flows)

    # Step 1: Count intermediate occurrences on shortest multi-hop flow paths
    path_intermediates: Dict[int, int] = {}
    for f in flows:
        s, d = f["src"], f["dst"]
        if nx.has_path(G, s, d):
            p = nx.shortest_path(G, s, d)
            for node in p[1:-1]:
                if node not in endpoints:
                    path_intermediates[node] = path_intermediates.get(node, 0) + 1

    if path_intermediates:
        # Pick intermediate node appearing on the most paths, breaking ties by degree
        return max(path_intermediates.keys(), key=lambda n: (path_intermediates[n], G.degree[n]))

    # Step 2: Fallback to non-endpoint neighbors of active sources
    source_nbrs: Dict[int, int] = {}
    for f in flows:
        s = f["src"]
        for nbr in G.neighbors(s):
            if nbr not in endpoints:
                source_nbrs[nbr] = source_nbrs.get(nbr, 0) + G.degree[nbr]
    if source_nbrs:
        return max(source_nbrs.keys(), key=lambda n: source_nbrs[n])

    # Step 3: Fallback to highest betweenness centrality among non-endpoints
    bc = nx.betweenness_centrality(G)
    candidates = {n: bc[n] for n in sorted(G.nodes) if n not in endpoints}
    if candidates:
        return max(candidates.keys(), key=lambda n: candidates[n])

    # Final deterministic fallback
    non_endpoints = [n for n in sorted(runner.nodes.keys()) if n not in endpoints]
    return non_endpoints[0] if non_endpoints else 0
```

### 4.3 Determinism & Traceability
The dynamic selection is purely a deterministic function of the network topology generated by `random.Random(seed)` and the scenario flows. All ties are broken via sorted node IDs. The chosen attacker ID is recorded in the scenario run metadata, ensuring byte-identical reproducibility.

---

## 5. Trace Logging Architecture & `NODE_STATUS` Periodic Events

### 5.1 Unified Trace Header Specification
To fulfill `DATA-01` and Decision `D-06` while preserving backward compatibility with Phase 01 tools, the trace CSV schema is defined as:

```csv
time,src,dst,pkt_id,type,hop_count,dropped_by,node_id,speed,neighbor_count
```

- **`time`**: Floating-point simulation time in seconds (`%.6f`).
- **`src`**: Packet source node ID (or event creator).
- **`dst`**: Packet destination node ID (-1 for broadcast).
- **`pkt_id`**: Global unique packet ID (0 for node telemetry).
- **`type`**: Event discriminator string:
  - `DATA_SENT`, `DATA_FWD`, `DATA_RECV`, `DATA_DROP`
  - `RREQ`, `RREP`, `RREP_RECV`, `RERR`
  - `LINK_BROKEN`
  - `NODE_STATUS`
- **`hop_count`**: Current packet hop distance from source.
- **`dropped_by`**: Node ID that dropped the packet (empty string for non-drop events).
- **`node_id`**: ID of the node currently executing/observing the event.
- **`speed`**: Current node mobility speed in m/s (populated for `NODE_STATUS`).
- **`neighbor_count`**: Current count of 1-hop wireless neighbors (populated for `NODE_STATUS`).

### 5.2 Embedding Periodic `NODE_STATUS` Events (`D-06`)
In `SimulationRunner`, a SimPy generator process executes every status interval (default 1.0s):
```python
def _periodic_status_logger(self, interval: float = 1.0) -> Generator[simpy.Event, None, None]:
    while True:
        yield self.env.timeout(interval)
        now = self.env.now
        for nid in sorted(self.nodes.keys()):
            node = self.nodes[nid]
            self.trace_rows.append([
                f"{now:.6f}",
                nid,
                -1,
                0,
                "NODE_STATUS",
                0,
                "",
                nid,
                f"{node.speed:.4f}",
                len(node.neighbors),
            ])
```
This self-contained design guarantees that the downstream feature extractor can calculate `neighbor_count` and `mobility_speed` without reading out-of-band state or re-simulating mobility trajectories.

---

## 6. Sliding-Window Feature Extractor & Non-Leaking Tabular Schema

### 6.1 Sliding-Window Temporal Windowing
The feature pipeline aggregates packet events backward in time over a sliding window:
$$t - W \le t_{\text{event}} \le t$$
- **Window size ($W$):** $5.0\text{s}$ (captures immediate behavioral dynamics without excessive lag).
- **Step size ($\Delta t$):** $1.0\text{s}$ (produces overlapping samples for smooth temporal learning).
- **Warmup period (`--warmup`):** $10.0\text{s}$ default. Windows with $t < \text{warmup}$ are omitted from output datasets to discard initial routing discovery settling noise.
- **Min-packets threshold (`--min-packets`):** Configurable integer filter (default 0). Can filter out completely idle node windows if desired.

### 6.2 Feature Calculation Definitions
For node $i$ over window interval $[t - W, t]$:

| # | Feature Column | Calculation Formula & Logic | Neutral Zero-Traffic Fallback (`D-07`) |
|---|---|---|---|
| 1 | `packet_forward_ratio` | $\frac{\text{DATA\_FWD}_i}{\text{DATA\_FWD}_i + \text{DATA\_DROP}_i}$ | If $\text{FWD} + \text{DROP} == 0$, assign `1.0` |
| 2 | `packet_drop_ratio` | $\frac{\text{DATA\_DROP}_i}{\text{DATA\_FWD}_i + \text{DATA\_DROP}_i}$ | If $\text{FWD} + \text{DROP} == 0$, assign `0.0` |
| 3 | `avg_delay` | Average end-to-end delay $(t_{\text{recv}} - t_{\text{sent}})$ of delivered packets terminating at node $i$ or traversing node $i$ in window | If no delivered packets observed, assign `0.0` |
| 4 | `route_request_rate` | $\frac{\text{Count}(\text{RREQ events where } node\_id == i)}{W}$ (Hz) | Assign `0.0` |
| 5 | `route_reply_rate` | $\frac{\text{Count}(\text{RREP events where } node\_id == i)}{W}$ (Hz) | Assign `0.0` |
| 6 | `throughput` | $\frac{\text{DATA\_RECV}_i \times 512 \times 8}{W}$ (bps) | Assign `0.0` |
| 7 | `hop_count` | Average `hop_count` of data/routing packets handled by node $i$ in window | If no packets handled, assign `0.0` |
| 8 | `neighbor_count` | Average `neighbor_count` from `NODE_STATUS` events for node $i$ in window | If missing, use most recent known status |
| 9 | `mobility_speed` | Average `speed` from `NODE_STATUS` events for node $i$ in window | If missing, use most recent known status |
| 10 | `label` | String ground-truth label: `"Blackhole"` if $i \in \text{attackers}$, else `"Normal"` | Derived strictly from scenario config metadata |

### 6.3 Anti-Leakage Protocol (`DATA-03`)
- **Zero Identity in $X$:** The exported feature dataset contains **strictly the 10 schema columns**. Node ID, IP address, coordinates $(x,y)$, scenario name, and seed are never included in the feature table.
- **Invariance Test:** An automated test verifies that running the extractor with an altered ground-truth config produces **byte-identical feature columns $X$**, altering only the target column `label`.

---

## 7. Gate 2 Benchmark Specification & Quantitative Verification Results

### 7.1 Quantitative Impact Threshold (`D-09`)
Gate 2 (`AGENTS.md:137` and `02-CONTEXT.md:30`) mandates that before any ML classifier is trained, the attack must demonstrably degrade network performance:
$$\text{Relative PDR Drop} = \frac{\text{PDR}_{\text{baseline}} - \text{PDR}_{\text{attack}}}{\text{PDR}_{\text{baseline}}} \ge 25\%$$

### 7.2 Multi-Seed Empirical Verification Results
To validate Gate 2 feasibility, empirical simulations were executed across three paired seeds (42, 43, 44) under 30 nodes, 6 CBR flows, and 300s duration:

| Seed | Baseline PDR | Attack Attacker Node | Attack PDR | Relative PDR Drop | Routing Overhead Change | Status |
|---|---|---|---|---|---|---|
| **42** | 7.12% (443/6220) | Node 21 (Dynamic) | 3.38% (210/6220) | **52.60%** | $0.0066 \to 0.0071$ | **PASSED** ($\ge 25\%$) |
| **43** | 42.46% (2641/6220) | Node 2 (Dynamic) | 9.61% (598/6220) | **77.36%** | $0.0084 \to 0.0092$ | **PASSED** ($\ge 25\%$) |
| **44** | 37.65% (2342/6220) | Node 27 (Dynamic) | 4.66% (290/6220) | **87.62%** | $0.0079 \to 0.0088$ | **PASSED** ($\ge 25\%$) |

**Conclusion:** All three seeds demonstrate catastrophic network degradation under the Blackhole attack ($52\%$ to $87\%$ relative PDR drop), completely satisfying Gate 2.

---

## 8. Edge Cases, Pitfalls & Mitigation Strategies

| Risk / Pitfall | Impact | Mitigation Strategy |
|---|---|---|
| **Simulator Importing Attacks** | Violates binding engineering contract `AGENTS.md:67-69`. | Only `simulator/run_scenario.py` imports `attacks/`. `simulator/aodv.py` checks duck-typed `self.attack_behavior` hooks. Static AST test enforces boundary. |
| **Attacker Picked as Flow Source/Dest** | Distorts CBR traffic generation; node drops its own originated packets. | `select_dynamic_attacker` builds `endpoints = set(f["src"]) \| set(f["dst"])` and explicitly excludes them. |
| **Trace Format Desynchronization** | Feature extractor crashes or mismatches columns with runner. | Define `TRACE_HEADER` as a single constant in `simulator/run_scenario.py` and import it into `metrics.py` and `feature_extraction/`. |
| **Division by Zero on Idle Nodes** | `NaN` values corrupting downstream ML training. | Decision `D-07`: Assign neutral forward ratio `1.0` and drop ratio `0.0` when total handled packets $= 0$. Fill missing delay with `0.0`. |
| **Temporal / Future Peeking Leakage** | Inflated ML performance on future events. | Sliding window strictly enforces backward filter $t - W \le t_{\text{event}} \le t$. |
| **Non-Deterministic Dynamic Selection** | Different runs with same seed picking different attackers. | Dynamic selector sorts node keys (`sorted(...)`) before degree or centrality maximization. |

---

## 9. Verification & Validation Plan

### 9.1 Unit & Contract Tests
- `tests/test_attacks_blackhole.py`: Validates `BlackholeStrategy` spoofed parameters and data drop flags.
- `tests/test_import_boundaries.py`: AST scan asserting no module in `simulator/` imports `attacks/` (except `run_scenario.py`).
- `tests/test_trace_logging.py`: Asserts `NODE_STATUS` events appear at 1.0s intervals with valid speeds and neighbor counts.
- `tests/test_feature_pipeline.py`: Validates sliding window output schema (exactly 10 columns), checks zero `NaN`s, and runs invariance test against label leakage.

### 9.2 Gate 2 Verification Benchmark Script
- `scripts/verify_gate2.py` / `tests/test_gate2_blackhole.py`:
  - Runs paired seeds 42, 43, 44.
  - Computes PDR, throughput, delay, packet loss, and routing overhead.
  - Automatically asserts $\text{Relative Drop} \ge 25\%$ for each seed.
  - Generates a formatted ASCII comparison table.

---

## 10. Recommended Implementation Plans Breakdown

To execute Phase 02 with atomic verification gates, the phase should be broken down into **three distinct plans**:

### Plan 02-01: Decoupled Attack Strategy & Dynamic Placement Engine
- Create `attacks/` package (`base.py`, `blackhole.py`, `registry.py`).
- Enhance `AODVNode` in `simulator/aodv.py` with duck-typed `self.attack_behavior` hook.
- Implement dynamic flow-intercept placement in `simulator/run_scenario.py`.
- Add scenario config `scenarios/e2_blackhole_30n.json`.
- Add unit tests for attack behavior and decoupled boundary checks.

### Plan 02-02: Enhanced Trace Logging & Gate 2 Benchmark
- Update `TRACE_HEADER` with `node_id`, `speed`, and `neighbor_count`.
- Add periodic `NODE_STATUS` telemetry logging process to `SimulationRunner`.
- Synchronize `simulator/metrics.py` with new header schema.
- Implement Gate 2 verification script `scripts/verify_gate2.py` running seeds 42, 43, 44.
- Verify $\ge 25\%$ relative PDR drop across all three seeds.

### Plan 02-03: Sliding-Window Feature Extractor & Dataset Generation
- Build `feature_extraction/` package (`extract_features.py`).
- Implement temporal sliding-window logic ($W = 5.0\text{s}$, $\Delta t = 1.0\text{s}$, `--warmup 10.0`).
- Compute the 9 behavioral features with zero-traffic neutral handling (`D-07`).
- Join ground-truth labels from scenario JSON (`D-08`).
- Verify strict anti-leakage compliance (exactly 10 schema columns, zero oracle metadata).
- Generate sample baseline and attack datasets under `data/`.

---

## RESEARCH COMPLETE
