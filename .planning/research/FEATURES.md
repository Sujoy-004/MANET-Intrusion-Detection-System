# Feature Research

**Domain:** MANET Simulation, Feature Engineering & Machine Learning Intrusion Detection  
**Researched:** 2026-10-23  
**Confidence:** HIGH  

## Feature Landscape

### Table Stakes (Users & Examiners Expect These)

Features required for an academically rigorous and verifiable B.Tech major project.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Discrete-event MANET engine | Foundation for multi-hop ad-hoc wireless communication | MEDIUM | SimPy clock, nodes with (x,y) positions, transmission range circles. |
| Random Waypoint mobility | Standard MANET mobility model for moving nodes | LOW | Configurable min/max speed, pause time, boundary bounding box. |
| RFC 3561 AODV routing protocol | Standard reactive routing protocol in MANET research | MEDIUM | Route Requests (RREQ), Route Replies (RREP), Route Errors (RERR), sequence numbers, hop counts, routing tables with timeouts. |
| CBR / UDP traffic generator | Creates background application payload traffic | LOW | Source-destination pairs, configurable packet rate and size. |
| Blackhole attack injection | Primary adversarial baseline; immediately drops packets | LOW | Node advertises high sequence number and 0/1 hop count, swallows traffic. |
| Grayhole attack injection | Advanced subtle attack; selective/probabilistic dropping | MEDIUM | Forwards control traffic but drops payload packets probabilistically or selectively. |
| Structured packet trace logging | Generates raw data for offline and online inspection | LOW | CSV trace of all events (`time, event_type, node_id, pkt_id, pkt_type, src, dst, hop_count`). |
| Non-leaking windowed feature extraction | Converts packet events into ML training instances | MEDIUM | Sliding observation window per node/flow calculating forwarding ratios, drop ratios, request/reply rates, and neighbor counts. |
| Classical ML classifiers (≥3) | Core requirement of ML-based detection | MEDIUM | Random Forest, Decision Tree, Support Vector Machine / Logistic Regression. |
| Full classification metric suite | Standard security evaluation rigor | LOW | Precision, Recall, F1-Score, False Positive Rate (FPR), Confusion Matrix. |
| Closed-loop routing mitigation | Core differentiator proving IDS practical utility | MEDIUM | When IDS flags a node as malicious, AODV routing penalizes/blacklists it, seeking alternative paths. |
| QoS comparative benchmarking | Verifies network recovery under IDS protection | MEDIUM | Packet Delivery Ratio (PDR), Throughput, End-to-End Delay, Routing Overhead across Baseline vs Attack vs AODV+IDS. |

### Differentiators (Competitive Academic Advantage)

Features that set this project apart from basic student implementations.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Strict seed-level determinism | Unlocks 100% reproducible experiments across different seeds | LOW | Random seeds explicitly propagated to SimPy, mobility, traffic, and ML splits. |
| Scenario-based holdout validation | Demonstrates true ML generalization without temporal leakage | MEDIUM | Train on scenarios A, B, C; test on unseen scenarios D, E with different topology/seeds. |
| Side-by-side QoS recovery tables | Quantifiable proof that ML improves the network | MEDIUM | Automated tabular comparison showing PDR drop under attack and recovery under IDS. |
| Clean separation of attack logic | Allows running identical simulator code with or without attacks | LOW | Attacker strategy pattern injected at runtime via scenario config. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that appear desirable on the surface but create failure points for a B.Tech timeline.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| NS-3 C++ simulation | Traditional academic simulator | Extremely difficult Windows installation, brittle C++ builds, high debugging overhead | In-repo pure-Python SimPy simulator (~70k events/sec). |
| Deep Learning (LSTM, CNN, GNN) | Modern ML buzzwords | Prone to overfitting on small datasets, slow training, opaque decisions, high parameter tuning burden | Random Forest and Decision Trees (interpretable, robust, fast). |
| 6+ attack vectors simultaneously | Apparent scope ambition | Dilutes depth; prevents reliable attack modeling and verification | Blackhole first, followed by Grayhole. |
| Blockchain for trust management | Trendy distributed ledger | Massive computational and message overhead entirely unsuited for resource-constrained MANETs | Local trust/reputation scoring and dynamic AODV route filtering. |
| Physical hardware / SDR testbed | Real-world validation | High hardware costs, RF interference, lack of reproducibility | Controlled discrete-event simulation with statistical variation. |

## Feature Dependencies

```
[SimPy Engine] 
    └──requires──> [Mobility & Radio Range]
                       └──requires──> [AODV Routing Protocol]
                                          └──requires──> [CBR Traffic Generator]
                                                             ├──requires──> [Trace Logger]
                                                             │                  └──requires──> [Feature Extraction]
                                                             │                                     └──requires──> [ML Training]
                                                             │                                                        └──requires──> [IDS Classifier]
                                                             └──requires──> [Attack Injectors]                                             │
                                                                                └──threatens──> [Network QoS] <──mitigated by── [Active Route Exclusion]
```

### Dependency Notes

- **AODV Routing requires Mobility & Radio:** Route discovery can only be evaluated when nodes move and link availability changes dynamically.
- **Trace Logger requires Traffic & Attacks:** Raw events must represent both normal operations and attack anomalies.
- **ML Training requires Feature Extraction:** Models cannot ingest raw event logs; they require window-aggregated tabular features.
- **Active Route Exclusion requires IDS Classifier:** Mitigation depends on high-precision detection to avoid blacklisting benign nodes.
- **QoS Comparison requires all components:** Meaningful evaluation requires running identical scenario seeds across Baseline, Attack, and IDS-mitigated runs.

## MVP Definition

### Launch With (v1 - Core Chain)

Minimum viable pipeline to satisfy all project gates:
- [x] Pure-Python SimPy MANET discrete-event simulator with AODV routing
- [x] Blackhole attack injection strategy
- [x] Trace logging and sliding-window feature extractor (non-leaking)
- [x] Scikit-learn classification pipeline (Random Forest, Decision Tree, SVM)
- [x] Scenario/seed holdout evaluation with full metrics (Precision, Recall, F1, FPR, Confusion Matrix)
- [x] Closed-loop AODV malicious node exclusion
- [x] End-to-end comparative QoS benchmark table (PDR, Throughput, Delay, Overhead)

### Add After Validation (v1.x)

- [ ] Grayhole attack injection strategy and generalization testing
- [ ] Multi-seed variance analysis and confidence intervals
- [ ] Automated Matplotlib/Seaborn report figure generation

### Future Consideration (v2+)

- [ ] Flooding / RREQ DoS attack injection
- [ ] Lightweight Flask/FastAPI simulation visualizer / dashboard
- [ ] SHAP feature importance explainability

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| SimPy AODV Simulator | HIGH | MEDIUM | P1 |
| Blackhole Attack Model | HIGH | LOW | P1 |
| Deterministic Trace Logging | HIGH | LOW | P1 |
| Windowed Feature Extraction | HIGH | MEDIUM | P1 |
| ML Multi-Classifier Pipeline | HIGH | LOW | P1 |
| Scenario Holdout Evaluation | HIGH | LOW | P1 |
| Active Route Exclusion Mitigation | HIGH | MEDIUM | P1 |
| Baseline vs IDS Comparison Table | HIGH | LOW | P1 |
| Grayhole Attack Model | HIGH | MEDIUM | P2 |
| Statistical Plot Generation | MEDIUM | LOW | P2 |
| Web Dashboard Visualizer | LOW | MEDIUM | P3 |

---
*Feature research for: MANET Intrusion Detection System*  
*Researched: 2026-10-23*  
