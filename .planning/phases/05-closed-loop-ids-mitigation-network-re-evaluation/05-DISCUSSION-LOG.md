# Phase 05: Closed-Loop IDS Mitigation & Network Re-Evaluation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-27  
**Phase:** 05-Closed-Loop IDS Mitigation & Network Re-Evaluation  
**Areas discussed:** Mitigation Mechanism & Route Exclusion, Detection Frequency & Online Triggering, False Positive Dampening & Quarantine Confirmation, Comparative QoS Benchmarking Suite  

---

## Mitigation Mechanism & Route Exclusion

| Option | Description | Selected |
|--------|-------------|----------|
| Hard Exclusion & RREP Drop | Flagged nodes are added to an active blacklist; incoming RREPs from or traversing them are dropped, and active routes through them are invalidated via RERR. | ✓ |
| Soft Hop-Count Metric Penalty | Inflate routing metrics/hop counts through suspicious nodes so AODV prefers alternate paths without absolute disconnection if no other path exists. | |
| Quarantine Buffer & Packet Redirection | Divert packets around the suspicious node at the local forwarding hop rather than triggering an end-to-end route discovery. | |

**User's choice:** Hard Exclusion & RREP Drop  
**Notes:** Flagged nodes are strictly barred from participating in AODV routes.

| Option | Description | Selected |
|--------|-------------|----------|
| Distributed Synchronized Blacklist | A central or broadcast IDS response manager updates an exclusion list shared by all benign AODV nodes in the simulation run (cleanest simulation model and strongest QoS recovery). | ✓ |
| Purely Local Node Blacklists | Each node independently maintains its own isolated blacklist based only on its direct traffic interactions and observations. | |
| Source-Initiated RERR Isolation | Only the traffic source node blacklists the offender and issues route rediscovery excluding the malicious hop. | |

**User's choice:** Distributed Synchronized Blacklist  
**Notes:** Synchronized exclusion ensures all nodes drop spoofed control and data forwarding through the malicious node.

| Option | Description | Selected |
|--------|-------------|----------|
| Immediate RERR Invalidation & Route Rediscovery | Invalidate all routing table entries traversing the blacklisted node, emit RERRs to upstream sources, and trigger immediate clean RREQ route discovery around the offender. | ✓ |
| Passive Route Drop & Lazy Eviction | Mark the route as invalid for future packets without emitting RERR broadcasts, letting standard AODV timeout or drop-triggered rediscovery handle the change. | |
| Local Route Repair Seam | The upstream neighbor of the blacklisted node attempts 1-hop local repair before notifying the source. | |

**User's choice:** Immediate RERR Invalidation & Route Rediscovery  
**Notes:** Immediate RERR ensures fast route convergence and recovery.

| Option | Description | Selected |
|--------|-------------|----------|
| Permanent Exclusion for Phase 5 | Once confirmed malicious, the node remains in the network blacklist for the remainder of the scenario run (prevents cyclic re-infection, aligns with BTech scope). | |
| Time-Decayed Quarantine Window | Blacklist expires after a configurable cooling-off window (e.g., 30s) unless malicious behavior re-triggers the alert. | ✓ |
| Dynamic Trust Score Recovery | Incrementally restore routing trust if subsequent monitoring windows show zero drop violations. | |

**User's choice:** Time-Decayed Quarantine Window  
**Notes:** Nodes are quarantined for a 30-second cooling off window.

---

## Detection Frequency & Online Triggering

| Option | Description | Selected |
|--------|-------------|----------|
| Periodic Evaluation Tick | A dedicated SimPy IDS monitor process wakes up at fixed intervals (e.g., every 1.0s or 2.0s), computes windowed features for active nodes, and evaluates the ML classifier. | |
| Packet-Level Reactive Trigger | Feature extraction and inference fire on-demand whenever a node's observed drop count or failed delivery exceeds a local threshold. | |
| Hybrid Periodic + Event Trigger | Periodic background scanning combined with immediate evaluation if an anomalous burst of dropped packets is observed. | ✓ |

**User's choice:** Hybrid Periodic + Event Trigger  
**Notes:** Provides regular background health monitoring while reacting instantly to drop spikes.

| Option | Description | Selected |
|--------|-------------|----------|
| Strict 10-Second Historical Window (W = 10.0s) | Matches the exact window length used during model training in Phase 3/4, avoiding distribution drift in feature scaling and rates. | ✓ |
| Short Agility Window (W = 5.0s) | Reduces detection latency to isolate attackers faster, accepting slight feature rate variance. | |
| Progressive Window (min 3.0s, max 10.0s) | Allows earlier detection during the initial startup phase before full 10s history accumulates. | |

**User's choice:** Strict 10-Second Historical Window (W = 10.0s)  
**Notes:** Preserves feature consistency with the trained model's StandardScaler parameters.

| Option | Description | Selected |
|--------|-------------|----------|
| Active Traffic Participants Only | Only evaluate nodes that sent, received, or forwarded traffic within the window (optimizes SimPy execution time and avoids evaluating idle nodes). | ✓ |
| All Scenario Nodes Uniformly | Evaluate all N nodes on every cycle regardless of activity (computes neutral fallback features for idle nodes). | |
| Suspect Nodes with Non-Zero Drops | Prioritize nodes that logged dropped packets before cycling through others. | |

**User's choice:** Active Traffic Participants Only  
**Notes:** Eliminates overhead on non-transmitting nodes.

| Option | Description | Selected |
|--------|-------------|----------|
| Decoupled Engine in ml/response.py | Create an OnlineIDS controller in ml/response.py that plugs into SimulationRunner via a clean event/process interface (maintains clean separation of concerns and matches AGENTS.md layout). | ✓ |
| In-Runner Monitor in simulator/run_scenario.py | Embed the periodic inspection process directly inside SimulationRunner alongside topology and packet forwarders. | |
| Node-Attached Monitor in simulator/aodv.py | Embed local observation buffers directly within AODVNode instances. | |

**User's choice:** Decoupled Engine in ml/response.py  
**Notes:** Keeps simulator core clean while maintaining required repo layout.

---

## False Positive Dampening & Quarantine Confirmation

| Option | Description | Selected |
|--------|-------------|----------|
| 2-Consecutive-Window Confirmation (K=2) | A node must be flagged as malicious across 2 consecutive observation windows before isolation is enacted (suppresses transient mobility glitches while rapidly catching persistent attackers). | ✓ |
| Conservative Probability Threshold (P >= 0.85) | Enact isolation on a single window, but only if the model's predicted malicious class probability exceeds a high-confidence threshold. | |
| Strike Accumulator (2 alerts within 3 windows) | Allow non-consecutive warnings to accumulate within a sliding history window before triggering quarantine. | |

**User's choice:** 2-Consecutive-Window Confirmation (K=2)  
**Notes:** Dampens transient link-breakage false positives.

| Option | Description | Selected |
|--------|-------------|----------|
| Tunable Threshold Defaulting to Calibrated Model Cutoff (tau = 0.50 with FPR <= 1%) | Use the calibrated decision threshold from Phase 4 training, exposed as a configurable CLI / scenario parameter. | ✓ |
| Conservative Risk-Averse Threshold (tau = 0.70) | Require higher model confidence before logging a suspect strike to ensure minimal false positives in high-mobility topologies. | |
| Strict Argmax Threshold | Use standard discrete predict() class assignment directly from the pipeline. | |

**User's choice:** Tunable Threshold Defaulting to Calibrated Model Cutoff (tau = 0.50 with FPR <= 1%)  
**Notes:** Leverages the calibrated model threshold directly.

| Option | Description | Selected |
|--------|-------------|----------|
| Symmetric Detection with Source/Dest Exclusion Guard | All forwarding intermediates are subject to isolation; designated traffic endpoints (sources and destinations) are logged if suspicious but cannot be severed from their own flows. | ✓ |
| Pure Symmetric Evaluation | Every node in the network is equally vulnerable to blacklisting without exception (pure zero-knowledge architecture). | |
| Source-Only Immunity | Sources never isolate themselves or their designated final targets, only intermediate forwarding relays. | |

**User's choice:** Symmetric Detection with Source/Dest Exclusion Guard  
**Notes:** Protects application endpoints from severing their own sessions.

| Option | Description | Selected |
|--------|-------------|----------|
| Exponential Backoff with Probation | Node returns to routing after 30s, but enters probation: a subsequent strike immediately re-isolates it with doubled cooldown (30s -> 60s -> indefinite), deterring oscillating attackers. | |
| Clean Reset to Normal | Quarantine expires completely after 30s; requires 2 fresh consecutive strikes to isolate again. | |
| Fixed 30s Repeating Cycle | Node is unblocked after 30s; if attack behavior persists, standard 2-window confirmation re-quarantines for another 30s. | ✓ |

**User's choice:** Fixed 30s Repeating Cycle  
**Notes:** Re-quarantines persistently malicious nodes every 30s upon re-detection.

---

## Comparative QoS Benchmarking Suite

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated CLI Runner in scripts/run_closed_loop_benchmark.py | Executes the 3-way comparison triad (Baseline AODV, Attack AODV, AODV+IDS) over configured seeds and scenarios, outputting summary CSV and Markdown reports in results/. | ✓ |
| Simulator Flag in simulator/run_scenario.py | Add a --mitigation [off|on] flag to the standard scenario runner and run them via shell script. | |
| Jupyter Notebook Driven Suite | Execute the comparative benchmark through an interactive analysis notebook. | |

**User's choice:** Dedicated CLI Runner in scripts/run_closed_loop_benchmark.py  
**Notes:** Standalone script supports batch execution and reproducibility.

| Option | Description | Selected |
|--------|-------------|----------|
| Multi-Attack Triad Matrix (Blackhole & Grayhole at 30 & 50 nodes) | Benchmark Baseline vs Attack vs AODV+IDS across Blackhole and Grayhole (0.5 & 0.7 drop rates) with multi-seed averaging (e.g., seeds 42, 43, 44). | ✓ |
| Blackhole Focused Matrix | Evaluate only Blackhole attack scenarios where PDR degradation and recovery are sharpest. | |
| Comprehensive Speed & Density Stress Grid | Run all 18 combinations of mobility and drop rate with IDS enabled. | |

**User's choice:** Multi-Attack Triad Matrix (Blackhole & Grayhole at 30 & 50 nodes)  
**Notes:** Covers both attack modalities across multiple network topologies.

| Option | Description | Selected |
|--------|-------------|----------|
| Full QoS Metric Suite with Recovery Ratios | Report raw metrics (PDR, Throughput, Delay, Overhead) alongside delta recovery (% PDR recovered towards Baseline) and IDS Routing Cost penalty. | ✓ |
| Standard 4 QoS Metrics Only | Report PDR, throughput, delay, and routing overhead side-by-side without derived recovery indices. | |
| PDR-Centric Summary Table | Focus primarily on PDR recovery percentages and packet drop reductions. | |

**User's choice:** Full QoS Metric Suite with Recovery Ratios  
**Notes:** Quantifies both absolute network recovery and routing overhead trade-offs.

| Option | Description | Selected |
|--------|-------------|----------|
| Dual Export (CSV + Markdown Summary + Isolation Event Log) | Write results/closed_loop_metrics.csv, results/closed_loop_report.md, and results/isolation_events.csv ready for Phase 6 visualization. | ✓ |
| Single Consolidated CSV in results/ | Save only results/closed_loop_metrics.csv containing all run parameters and QoS metrics. | |
| Per-Scenario Log Directory in results/closed_loop/ | Create a dedicated subdirectory with individual per-run JSON and CSV logs. | |

**User's choice:** Dual Export (CSV + Markdown Summary + Isolation Event Log)  
**Notes:** Provides rich data for Phase 6 plotting and inspection.

---

## Agent's Discretion
- Exact periodic evaluation interval ($\Delta t = 1.0\text{s}$ or $2.0\text{s}$) in the online IDS loop.
- Exact event-trigger threshold for drop bursts (e.g. 3 consecutive packet drops on an active route).
- Formats and header schemas for `results/isolation_events.csv`.

## Deferred Ideas
- Phase 6 will generate publication-grade Matplotlib/Seaborn plots from `results/closed_loop_metrics.csv` (bar charts for PDR recovery, delay comparisons, and overhead penalty).
- Multi-channel or collaborative cryptographic reputation exchanges are deferred to v2.
