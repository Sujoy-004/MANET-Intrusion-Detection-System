# Phase 05: Closed-Loop IDS Mitigation & Network Re-Evaluation - Context

**Gathered:** 2026-10-27  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 05 establishes the closed-loop intrusion detection and active mitigation feedback loop in the MANET system. It integrates the trained and serialized machine learning champion classifier (`ml/models/best_model.joblib`) into real-time AODV route management, dynamically isolating confirmed malicious nodes (both Blackhole and Grayhole) and rerouting traffic around compromised paths. Finally, it executes automated comparative QoS benchmarking across Baseline AODV vs. Attack AODV vs. AODV+IDS under identical scenario seeds, quantitatively verifying network recovery in Packet Delivery Ratio (PDR), throughput, end-to-end delay, and routing overhead.

</domain>

<decisions>
## Implementation Decisions

### 1. Mitigation Mechanism & Route Exclusion
- **D-01:** Hard Exclusion & RREP Drop — Flagged nodes are added to an active blacklist; incoming RREPs from or traversing them are dropped, and active routes through them are invalidated via RERR. — **Reversibility:** costly — changes AODV route table processing and control message filtering.
- **D-02:** Distributed Synchronized Blacklist — A central or broadcast IDS response manager updates an exclusion list shared by all benign AODV nodes in the simulation run (cleanest simulation model and strongest QoS recovery). — **Reversibility:** costly — defines how alert state propagates across the simulated network.
- **D-03:** Immediate RERR Invalidation & Route Rediscovery — Invalidate all routing table entries traversing the blacklisted node, emit RERRs to upstream sources, and trigger immediate clean RREQ route discovery around the offender. — **Reversibility:** reversible.
- **D-04:** Time-Decayed Quarantine Window — Blacklist expires after a configurable cooling-off window (default: 30s) unless malicious behavior re-triggers the alert. — **Reversibility:** reversible.

### 2. Detection Frequency & Online Triggering
- **D-05:** Hybrid Periodic + Event Trigger — Periodic background scanning (every 1.0s or 2.0s) combined with immediate evaluation if an anomalous burst of dropped packets is observed. — **Reversibility:** costly — connects the discrete-event clock process with the feature extraction and inference pipeline.
- **D-06:** Strict 10-Second Historical Window ($W = 10.0\text{s}$) — Matches the exact window length used during model training in Phase 3/4, avoiding distribution drift in feature scaling and rates. — **Reversibility:** costly — determines feature calculation compatibility with `best_model.joblib`.
- **D-07:** Active Traffic Participants Only — Only evaluate nodes that sent, received, or forwarded traffic within the window (optimizes SimPy execution time and avoids evaluating idle nodes). — **Reversibility:** reversible.
- **D-08:** Decoupled Engine in `ml/response.py` — Create an `OnlineIDS` controller in `ml/response.py` that plugs into `SimulationRunner` via a clean event/process interface (maintains clean separation of concerns and matches AGENTS.md layout). — **Reversibility:** costly — defines module boundaries between simulator and ML response.

### 3. False Positive Dampening & Quarantine Confirmation
- **D-09:** 2-Consecutive-Window Confirmation ($K=2$) — A node must be flagged as malicious across 2 consecutive observation windows before isolation is enacted (suppresses transient mobility glitches while rapidly catching persistent attackers). — **Reversibility:** reversible.
- **D-10:** Tunable Threshold Defaulting to Calibrated Model Cutoff ($\tau = 0.50$ with FPR $\le$ 1%) — Use the calibrated decision threshold from Phase 4 training, exposed as a configurable CLI / scenario parameter. — **Reversibility:** reversible.
- **D-11:** Symmetric Detection with Source/Dest Exclusion Guard — All forwarding intermediates are subject to isolation; designated traffic endpoints (sources and destinations) are logged if suspicious but cannot be severed from their own flows. — **Reversibility:** reversible.
- **D-12:** Fixed 30s Repeating Cycle — Node is unblocked after 30s; if attack behavior persists, standard 2-window confirmation re-quarantines for another 30s. — **Reversibility:** reversible.

### 4. Comparative QoS Benchmarking Suite
- **D-13:** Dedicated CLI Runner in `scripts/run_closed_loop_benchmark.py` — Executes the 3-way comparison triad (Baseline AODV, Attack AODV, AODV+IDS) over configured seeds and scenarios, outputting summary CSV and Markdown reports in `results/`. — **Reversibility:** reversible.
- **D-14:** Multi-Attack Triad Matrix (Blackhole & Grayhole at 30 & 50 nodes) — Benchmark Baseline vs Attack vs AODV+IDS across Blackhole and Grayhole (0.5 & 0.7 drop rates) with multi-seed averaging (seeds 42, 43, 44). — **Reversibility:** reversible.
- **D-15:** Full QoS Metric Suite with Recovery Ratios — Report raw metrics (PDR, Throughput, Delay, Overhead) alongside delta recovery (% PDR recovered towards Baseline) and IDS Routing Cost penalty. — **Reversibility:** reversible.
- **D-16:** Dual Export (CSV + Markdown Summary + Isolation Event Log) — Write `results/closed_loop_metrics.csv`, `results/closed_loop_report.md`, and `results/isolation_events.csv` ready for Phase 6 visualization. — **Reversibility:** reversible.

### Agent's Discretion
- Exact periodic evaluation interval ($\Delta t = 1.0\text{s}$ or $2.0\text{s}$) in the online IDS loop.
- Exact event-trigger threshold for drop bursts (e.g. 3 consecutive packet drops on an active route).
- Formats and header schemas for `results/isolation_events.csv`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & Engineering Rules
- `AGENTS.md` — Non-negotiable engineering contract: Python-only, discrete-event determinism, comparison against plain AODV without IDS reporting PDR, throughput, delay, and routing overhead.
- `MANET_IDS_BTech_Execution_Guide.md` §Module E, §Module F, §Experiment E7 — IDS response specification, node isolation, and side-by-side benchmark comparison.
- `.planning/REQUIREMENTS.md` — `RESP-01` (dynamic malicious node isolation) and `RESP-02` (automated comparative QoS benchmark runner).

### Precedent Phases & Artifacts
- `ml/models/best_model.joblib` — Serialized Phase 4 multi-attack champion Random Forest classifier with `StandardScaler` and `predict_proba`.
- `simulator/aodv.py` — AODV routing protocol engine (`handle_rreq`, `handle_rrep`, `get_route`, `send_rerr`).
- `simulator/run_scenario.py` — `SimulationRunner` discrete-event composition root, data packet forwarding (`_route_and_forward_data`), and trace logger.
- `simulator/metrics.py` — Authoritative network QoS metric calculations (PDR, throughput, end-to-end delay, routing overhead).
- `feature_extraction/extract_features.py` — 10-feature non-leaking sliding window feature extractor.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ml/models/best_model.joblib`: Phase 4 champion model ready for immediate loading via `joblib.load()` with probability calibration.
- `simulator/aodv.py`: `AODVNode` class contains complete routing table and packet handling logic ready for blacklist / exclusion checking.
- `simulator/metrics.py`: `compute_qos_metrics()` and individual metric functions calculate PDR, throughput, delay, and overhead directly from packet traces.
- `simulator/run_scenario.py`: `SimulationRunner` orchestrates the SimPy discrete-event environment, packet buffering, and logging.
- `feature_extraction/extract_features.py`: Feature calculation logic (`_compute_window_features`) can be adapted for online sliding window calculation in `ml/response.py`.

### Established Patterns
- Strategy and Duck-Typing pattern: Behavior hooks attach cleanly to `AODVNode` without modifying core routing protocol structure.
- Deterministic random seeding: All processes take explicit `self.seed` and pass `self.rng`.
- Anti-leakage isolation: Feature calculation operates solely on observable traffic metrics without reading attack flags or node identities.

### Integration Points
- `ml/response.py`: Houses `OnlineIDS` engine, sliding-window trace buffer, and blacklist coordinator.
- `simulator/aodv.py`: Hook in `handle_rrep` and `update_route` to consult `is_blacklisted(node_id)` before routing or accepting RREPs.
- `simulator/run_scenario.py`: Runner hooks `OnlineIDS` process into `self.env`, checking periodically and triggering RERR broadcasts on confirmed isolation.
- `scripts/run_closed_loop_benchmark.py`: Runs baseline, attack, and mitigation configurations, saving tables into `results/`.

</code_context>

<specifics>
## Specific Ideas
- In `results/closed_loop_report.md`, format a clear Markdown table presenting the 3-column triad side-by-side:
  - Metric: PDR (%), Throughput (kbps), Delay (s), Routing Overhead
  - Baseline AODV | Attack AODV | AODV + IDS | $\Delta$ Recovery (%)
- Log timestamped isolation alerts in `results/isolation_events.csv` with fields: `sim_time, node_id, strike_count, prob_malicious, action, reason`.

</specifics>

<deferred>
## Deferred Ideas
- Phase 6 will generate publication-grade Matplotlib/Seaborn plots from `results/closed_loop_metrics.csv` (bar charts for PDR recovery, delay comparisons, and overhead penalty).
- Multi-channel or collaborative cryptographic reputation exchanges are deferred to v2.

</deferred>

---

*Phase: 05-Closed-Loop IDS Mitigation & Network Re-Evaluation*  
*Context gathered: 2026-10-27*  
