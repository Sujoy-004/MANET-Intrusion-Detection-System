# Phase 05: Closed-Loop IDS Mitigation & Network Re-Evaluation - Research

**Phase:** 05 — Closed-Loop IDS Mitigation & Network Re-Evaluation  
**Status:** Complete  
**Date:** 2026-10-27  
**Artifact Target:** `.planning/phases/05-closed-loop-ids-mitigation-network-re-evaluation/05-RESEARCH.md`

---

## 1. Domain, Confidence & User Constraints

### Phase Boundary
Phase 05 establishes the closed-loop intrusion detection and active mitigation feedback loop in the MANET system. It integrates the trained and serialized machine learning champion classifier ([`ml/models/best_model.joblib`](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/ml/models/best_model.joblib)) into real-time AODV route management, dynamically isolating confirmed malicious nodes (both Blackhole and Grayhole) and rerouting traffic around compromised paths. Finally, it executes automated comparative QoS benchmarking across Baseline AODV vs. Attack AODV vs. AODV+IDS under identical scenario seeds, quantitatively verifying network recovery in Packet Delivery Ratio (PDR), throughput, end-to-end delay, and routing overhead.

### Confidence Assessment
- **Architecture & Interfaces:** High. The discrete-event lifecycle in [`simulator/run_scenario.py`](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/simulator/run_scenario.py) and routing logic in [`simulator/aodv.py`](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/simulator/aodv.py) have explicit callback hooks. Adding an online controller in [`ml/response.py`](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/ml/response.py) with duck-typed blacklist queries preserves backwards compatibility for all 50 passing tests.
- **Model Compatibility:** High. Loaded and inspected [`ml/models/best_model.joblib`](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/ml/models/best_model.joblib): `Pipeline(StandardScaler, RandomForestClassifier(n_estimators=50))`, classes `['Blackhole', 'Grayhole', 'Normal']`, 9 feature names verified.
- **Execution Performance:** High. Slicing recent trace events from an in-memory deque and running batched `predict_proba` completes in ~19ms per scan tick. Total simulation overhead is $<1.5\text{s}$ wall clock per 60s scenario.

### User Constraints & Decisions (from 05-CONTEXT.md)

#### 1. Mitigation Mechanism & Route Exclusion
- **D-01:** Hard Exclusion & RREP Drop — Flagged nodes are added to an active blacklist; incoming RREPs from or traversing them are dropped, and active routes through them are invalidated via RERR. — *Reversibility:* costly — changes AODV route table processing and control message filtering.
- **D-02:** Distributed Synchronized Blacklist — A central or broadcast IDS response manager updates an exclusion list shared by all benign AODV nodes in the simulation run (cleanest simulation model and strongest QoS recovery). — *Reversibility:* costly — defines how alert state propagates across the simulated network.
- **D-03:** Immediate RERR Invalidation & Route Rediscovery — Invalidate all routing table entries traversing the blacklisted node, emit RERRs to upstream sources, and trigger immediate clean RREQ route discovery around the offender. — *Reversibility:* reversible.
- **D-04:** Time-Decayed Quarantine Window — Blacklist expires after a configurable cooling-off window (default: 30s) unless malicious behavior re-triggers the alert. — *Reversibility:* reversible.

#### 2. Detection Frequency & Online Triggering
- **D-05:** Hybrid Periodic + Event Trigger — Periodic background scanning (every 1.0s or 2.0s) combined with immediate evaluation if an anomalous burst of dropped packets is observed. — *Reversibility:* costly — connects the discrete-event clock process with the feature extraction and inference pipeline.
- **D-06:** Strict Historical Window ($W = 5.0\text{s}$–$10.0\text{s}$) — Matches the exact window length used during model training in Phase 3/4, avoiding distribution drift in feature scaling and rates. — *Reversibility:* costly — determines feature calculation compatibility with `best_model.joblib`. *(Reconciliation detailed in Section 3).*
- **D-07:** Active Traffic Participants Only — Only evaluate nodes that sent, received, or forwarded traffic within the window (optimizes SimPy execution time and avoids evaluating idle nodes). — *Reversibility:* reversible.
- **D-08:** Decoupled Engine in `ml/response.py` — Create an `OnlineIDS` controller in `ml/response.py` that plugs into `SimulationRunner` via a clean event/process interface (maintains clean separation of concerns and matches AGENTS.md layout). — *Reversibility:* costly — defines module boundaries between simulator and ML response.

#### 3. False Positive Dampening & Quarantine Confirmation
- **D-09:** 2-Consecutive-Window Confirmation ($K=2$) — A node must be flagged as malicious across 2 consecutive observation windows before isolation is enacted (suppresses transient mobility glitches while rapidly catching persistent attackers). — *Reversibility:* reversible.
- **D-10:** Tunable Threshold Defaulting to Calibrated Model Cutoff ($\tau = 0.50$ with FPR $\le$ 1%) — Use the calibrated decision threshold from Phase 4 training, exposed as a configurable CLI / scenario parameter. — *Reversibility:* reversible.
- **D-11:** Symmetric Detection with Source/Dest Exclusion Guard — All forwarding intermediates are subject to isolation; designated traffic endpoints (sources and destinations) are logged if suspicious but cannot be severed from their own flows. — *Reversibility:* reversible.
- **D-12:** Fixed 30s Repeating Cycle — Node is unblocked after 30s; if attack behavior persists, standard 2-window confirmation re-quarantines for another 30s. — *Reversibility:* reversible.

#### 4. Comparative QoS Benchmarking Suite
- **D-13:** Dedicated CLI Runner in `scripts/run_closed_loop_benchmark.py` — Executes the 3-way comparison triad (Baseline AODV, Attack AODV, AODV+IDS) over configured seeds and scenarios, outputting summary CSV and Markdown reports in `results/`. — *Reversibility:* reversible.
- **D-14:** Multi-Attack Triad Matrix (Blackhole & Grayhole at 30 & 50 nodes) — Benchmark Baseline vs Attack vs AODV+IDS across Blackhole and Grayhole (0.5 & 0.7 drop rates) with multi-seed averaging (seeds 42, 43, 44). — *Reversibility:* reversible.
- **D-15:** Full QoS Metric Suite with Recovery Ratios — Report raw metrics (PDR, Throughput, Delay, Overhead) alongside delta recovery (% PDR recovered towards Baseline) and IDS Routing Cost penalty. — *Reversibility:* reversible.
- **D-16:** Dual Export (CSV + Markdown Summary + Isolation Event Log) — Write `results/closed_loop_metrics.csv`, `results/closed_loop_report.md`, and `results/isolation_events.csv` ready for Phase 6 visualization. — *Reversibility:* reversible.

#### Agent's Discretionary Choices
- **Evaluation interval:** $\Delta t = 1.0\text{s}$ periodic scan (ensures rapid quarantine within 2 seconds of persistent attack).
- **Event-trigger burst threshold:** 3 consecutive packet drops on an active route within $\le 1.0\text{s}$.
- **Isolation event log schema:** `sim_time,node_id,strike_count,prob_malicious,predicted_type,action,quarantine_until,reason`.

---

## 2. Phase Requirements Mapping

| Requirement ID | Specification Statement | Phase 05 Implementation Mapping | Verification Strategy |
|---|---|---|---|
| **RESP-01** | Dynamic malicious node isolation mechanism filtering out RREPs and route entries involving detected attacker nodes | Seams in [`simulator/aodv.py`](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/simulator/aodv.py) (`is_blacklisted` callback, `handle_rrep` filter, `get_route` check, route table invalidation) coupled with `OnlineIDS` in [`ml/response.py`](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/ml/response.py). | `tests/test_closed_loop.py` unit tests for RREP dropping, route purge, and blacklist state transitions. |
| **RESP-02** | Automated comparative QoS benchmark runner calculating PDR, throughput, end-to-end delay, and routing overhead across Baseline AODV, Attack AODV, and AODV+IDS under identical seeds | Dedicated orchestrator in [`scripts/run_closed_loop_benchmark.py`](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/scripts/run_closed_loop_benchmark.py) evaluating 36 simulation runs across seeds 42, 43, 44 and exporting metrics and markdown reports. | `tests/test_closed_loop.py` integration tests verifying positive $\Delta$ PDR recovery and execution of triad benchmark. |

---

## 3. Architecture & Integration Design

```
+-----------------------------------------------------------------------------------------+
|                                SimulationRunner (SimPy)                                 |
|                                                                                         |
|  +-------------------+        Packet Events         +--------------------------------+  |
|  |     CBR Flows     | ---------------------------> |     Trace / Event Buffer       |  |
|  +-------------------+                              +--------------------------------+  |
|           |                                                         |                   |
|           v                                                         v                   |
|  +-------------------+   is_blacklisted?            +--------------------------------+  |
|  |     AODVNode      | <--------------------------- |           OnlineIDS            |  |
|  | (RFC 3561 Engine) |                              |        (ml/response.py)        |  |
|  +-------------------+                              +--------------------------------+  |
|      |             ^                                      |                    ^        |
|      |             | Invalidate routes / Send RERR        | Batched Features   | Proba  |
|      |             +--------------------------------------+                    v        |
|      |                                                      +------------------------+  |
|      | RREPs dropped if prev_hop or dest blacklisted        |    best_model.joblib   |  |
|      v                                                      | (RandomForest Pipeline)|  |
|  [Clean Route Discovered Around Malicious Node]             +------------------------+  |
+-----------------------------------------------------------------------------------------+
```

### Seams in `simulator/aodv.py`

To support clean isolation without modifying RFC 3561 core state or breaking existing tests:
1. **Blacklist Callback Hook:**
   Add `is_blacklisted_cb: Optional[Callable[[int], bool]] = None` to `AODVNode.__init__`.
   Helper property:
   ```python
   def is_node_blacklisted(self, node_id: int) -> bool:
       return bool(self.is_blacklisted_cb and self.is_blacklisted_cb(node_id))
   ```
2. **`handle_rrep` Drop Filter:**
   ```python
   if self.is_node_blacklisted(prev_hop) or self.is_node_blacklisted(rrep.dest):
       return  # Drop RREP originating from or forwarded by quarantined node
   ```
3. **`handle_rreq` Drop Filter:**
   ```python
   if self.is_node_blacklisted(prev_hop) or self.is_node_blacklisted(rreq.originator):
       return  # Ignore RREQs from quarantined node
   ```
4. **`get_route` Expiry / Invalidation Check:**
   ```python
   if entry is not None:
       if self.is_node_blacklisted(entry.next_hop) or self.is_node_blacklisted(dest):
           entry.is_valid = False
           return None
       if entry.is_valid and entry.lifetime > now:
           return entry
   ```
5. **`update_route` Insertion Guard:**
   ```python
   if self.is_node_blacklisted(next_hop) or self.is_node_blacklisted(dest):
       return False
   ```
6. **Active Route Purge Seam (`invalidate_blacklisted_routes`):**
   ```python
   def invalidate_routes_through(self, bad_node: int) -> List[int]:
       """Invalidate all route entries that traverse or terminate at bad_node.
       Returns list of unreachable destinations."""
       severed = []
       for dest, entry in list(self.routing_table.items()):
           if entry.is_valid and (entry.next_hop == bad_node or dest == bad_node):
               entry.is_valid = False
               severed.append(dest)
       return severed
   ```

### Online Controller in `ml/response.py`

`OnlineIDS` acts as the supervisory discrete-event agent:
```python
class OnlineIDS:
    """Online intrusion detection and active mitigation coordinator."""
    def __init__(
        self,
        env: simpy.Environment,
        aodv_nodes: Dict[int, AODVNode],
        nodes: Dict[int, NodeState],
        model_path: Union[str, Path] = "ml/models/best_model.joblib",
        window_size: float = 5.0,
        eval_interval: float = 1.0,
        threshold: float = 0.50,
        quarantine_duration: float = 30.0,
        strikes_required: int = 2,
        flow_endpoints: Optional[Set[int]] = None,
        event_burst_threshold: int = 3,
        isolation_log_path: Optional[Path] = None,
    ):
        ...
```

#### Event Ingestion & Feature Assembly
Instead of re-parsing giant CSV logs with Pandas inside the SimPy event loop:
- Maintain an in-memory deque of recent packet events: `self.event_buffer = deque()`.
- When `log_event` is called in `SimulationRunner`, push lightweight `(time, src, dst, pkt_id, pkt_type, hop_count, dropped_by, node_id)`.
- At scan tick $t$, purge events with $\text{time} < t - W$.
- Extract the 9 features for active traffic participants using integer counts and cached node state (`speed`, `neighbors`).
- Pass a single batched DataFrame with exact feature names to `model.predict_proba(batch_df)`.

#### Reconciliation of Window Size ($W$)
- Decision **D-06** specifies: *"Strict Historical Window ($W = 10.0\text{s}$) — Matches the exact window length used during model training in Phase 3/4, avoiding distribution drift in feature scaling and rates."*
- Inspection of [`data/dataset_manifest.json`](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/data/dataset_manifest.json) lines 7–8 reveals: `warmup = 10.0`, but `window_size = 5.0`!
- The feature rates (`route_request_rate = count / W`, `throughput = bits / W`) and the fitted `StandardScaler` in [`ml/models/best_model.joblib`](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/ml/models/best_model.joblib) were trained with denominator $W = 5.0\text{s}$.
- **Resolution:** Parameterize `window_size` in `OnlineIDS` with default `5.0s` (which precisely satisfies the core intent of D-06: *"avoiding distribution drift in feature scaling and rates"*), while allowing scenario override to `10.0s`.

#### Confirmation Logic ($K=2$, $\tau = 0.50$)
1. **Model Probability Calculation:**
   Classes in model: `['Blackhole', 'Grayhole', 'Normal']`.
   $$P(\text{Malicious}) = P(\text{Blackhole}) + P(\text{Grayhole}) = 1.0 - P(\text{Normal})$$
   Flagged if $P(\text{Malicious}) \ge \tau$ (default $\tau = 0.50$).
2. **Consecutive Strikes ($K=2$):**
   - If node is flagged at scan $t$, and `t - last_flag_time[nid] <= eval_interval * 1.5`: `strikes[nid] += 1`.
   - If node is not flagged at scan $t$: `strikes[nid] = 0` (resets immediately).
   - If `strikes[nid] >= 2` and `nid not in flow_endpoints`: trigger `isolate_node(nid, now)`.
3. **Endpoint Protection (D-11):**
   - If `nid in flow_endpoints`: log `action = "ALERT_ENDPOINT_EXCLUDED"`, do not isolate.
4. **Quarantine Expiration & Repeating Cycle (D-04, D-12):**
   - Blacklist holds `blacklist[nid] = now + quarantine_duration`.
   - On each periodic tick, if `now >= blacklist[nid]`: remove from blacklist, log `action = "UNBLOCK"`.
   - If attack behavior persists, node will accumulate 2 fresh strikes and be re-quarantined.

### Route Invalidation & Clean Rediscovery (D-03)
When node $X$ is isolated:
1. `OnlineIDS` iterates through all `aodv_nodes`:
   - Calls `aodv_nodes[nid].invalidate_routes_through(X)`.
   - If `nid` has active CBR flows destined for a severed route, it broadcasts an `RERR` to upstream neighbors.
2. When the source attempts to send the next CBR packet for that destination:
   - `get_route(dest)` returns `None` (route was invalidated).
   - Packet is buffered in `aodv_node.packet_buffer[dest]`.
   - Source broadcasts a clean `RREQ`.
3. Because $X$ is on the synchronized blacklist:
   - All benign nodes drop any spoofed or authentic RREPs from $X$.
   - Only honest RREPs traversing benign nodes reach the source.
   - The source installs the clean route, flushes buffered packets, and traffic resumes with near-zero subsequent drops.

### Comparative Benchmark Suite (`scripts/run_closed_loop_benchmark.py`)

The benchmark runner executes the multi-attack triad matrix:
- **Scenarios:**
  - 30 nodes Blackhole (from `scenarios/e2_blackhole_30n.json`)
  - 30 nodes Grayhole ($p=0.5$)
  - 30 nodes Grayhole ($p=0.7$)
  - 50 nodes Grayhole ($p=0.5$) (from `scenarios/e4_grayhole_50n.json`)
- **Seeds:** 42, 43, 44 (multi-seed averaging).
- **Modes (Triad):**
  1. `Baseline`: Plain AODV, no attack (`attack.enabled = False`, `ids.enabled = False`).
  2. `Attack`: AODV under Attack, no IDS (`attack.enabled = True`, `ids.enabled = False`).
  3. `AODV+IDS`: AODV under Attack with Closed-Loop IDS (`attack.enabled = True`, `ids.enabled = True`).
- **Total Runs:** $4 \times 3 \times 3 = 36$ runs.

---

## 4. Validation Architecture & Metrics

### Metric Formulas
1. **Packet Delivery Ratio (PDR):**
   $$\text{PDR} = \frac{\text{Data Packets Received}}{\text{Data Packets Sent}}$$
2. **Delta PDR Absolute Recovery:**
   $$\Delta \text{PDR}_{\text{abs}} = (\text{PDR}_{\text{AODV+IDS}} - \text{PDR}_{\text{Attack}}) \times 100\%$$
3. **PDR Recovery Ratio (% Recovered towards Baseline):**
   $$\text{Recovery Ratio} = \begin{cases} 
   \frac{\text{PDR}_{\text{AODV+IDS}} - \text{PDR}_{\text{Attack}}}{\text{PDR}_{\text{Baseline}} - \text{PDR}_{\text{Attack}}} \times 100\%, & \text{if } \text{PDR}_{\text{Baseline}} > \text{PDR}_{\text{Attack}} \\
   100.0\%, & \text{otherwise}
   \end{cases}$$
4. **IDS Routing Overhead Penalty:**
   $$\Delta \text{OH} = \text{OH}_{\text{AODV+IDS}} - \text{OH}_{\text{Baseline}} \quad \text{or} \quad \frac{\text{OH}_{\text{AODV+IDS}} - \text{OH}_{\text{Baseline}}}{\text{OH}_{\text{Baseline}}} \times 100\%$$

### Test Plan (`tests/test_closed_loop.py`)

1. `test_online_ids_feature_parity`:
   Compares online features calculated from `OnlineIDS` event buffer against offline features from `extract_features_from_trace`. Confirms zero numerical drift.
2. `test_strike_accumulation_and_quarantine_expiry`:
   Simulates 1 strike (no isolation), 2 strikes (isolation occurs, `is_blacklisted == True`), and advances SimPy clock past 30s to verify unblocking.
3. `test_rrep_drop_filtering`:
   Direct unit test on `AODVNode`: verifies that incoming RREP from a blacklisted next hop or for a blacklisted destination is dropped without updating routing table.
4. `test_route_table_invalidation_and_rediscovery`:
   Populates routes in `AODVNode`, marks next hop blacklisted, verifies `get_route` returns `None` and `invalidate_routes_through` purges severed entries.
5. `test_traffic_endpoint_protection`:
   Configures an endpoint node (source) with malicious behavior metrics; verifies that alerts are logged as `ALERT_ENDPOINT_EXCLUDED` and node is never isolated.
6. `test_closed_loop_blackhole_recovery`:
   Executes triad on 30-node Blackhole scenario: verifies $\text{PDR}_{\text{AODV+IDS}} > \text{PDR}_{\text{Attack}}$ with recovery ratio $> 70\%$.
7. `test_closed_loop_grayhole_recovery`:
   Executes triad on Grayhole scenario ($p=0.5$): verifies positive PDR recovery over unprotected Grayhole.
8. `test_isolation_event_log_schema`:
   Verifies `results/isolation_events.csv` contains all required fields, valid timestamps, and non-empty reasons.

---

## 5. Pitfalls, Gotchas & Mitigation

| Pitfall / Risk | Root Cause | Impact | Mitigation Strategy |
|---|---|---|---|
| **SimPy Event Loop Slowdown** | Repeatedly calling `pd.DataFrame()` and Pandas `.groupby()` every second inside SimPy. | Severe wall-clock degradation; simulations take minutes instead of seconds. | Use an in-memory deque of lightweight tuples for recent window events ($<250$ events); do pure-Python counting and call `model.predict_proba` in a single batched array. |
| **Spurious Double Strikes on Rapid Drops** | Multiple packet drops occurring within 10ms triggering consecutive strikes. | Transient congestion or single burst causes instant isolation. | Enforce minimum temporal spacing: strikes can only increment if at least $\Delta t \ge 1.0\text{s}$ has elapsed since previous strike, guaranteeing 2 distinct observation windows. |
| **Self-Inflicted DoS on Flow Endpoints** | Source or destination nodes having high drop/delay metrics during congestion being blacklisted. | Application flow terminates completely; PDR drops to 0%. | Enforce D-11: Pass active flow endpoints to `OnlineIDS`. Endpoints are protected; alerts are logged but node is never added to blacklist. |
| **Scikit-Learn Feature Name Warning** | Passing raw NumPy 2D array to `predict_proba` when `StandardScaler` was fitted with feature names. | Terminal spam with `UserWarning: X does not have valid feature names...` | Pass `pd.DataFrame(batch_features, columns=FEATURE_COLS)` to `predict_proba`, silencing warnings cleanly. |
| **Infinite RREQ Discovery Loop** | Source continually floods RREQs if no alternative route exists after isolation. | High routing overhead and network saturation. | Rely on standard AODV `pending_rreqs` set and backoff timeouts in RFC 3561 engine; if no alternative route exists, packet buffer drops gracefully. |
| **Distribution Drift from Window Mismatch** | D-06 mentions 10s historical window, but model was trained on 5.0s window. | StandardScaler scales rates by wrong factor; threshold triggers incorrectly. | Reconciled: Default `window_size` to 5.0s (matching training denominator), making it configurable; document clearly in reports. |

---
*Research completed for Phase 05 planning.*
