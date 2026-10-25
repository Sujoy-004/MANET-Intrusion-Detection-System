# Requirements: Machine Learning-Based Intrusion Detection System for MANET

**Defined:** 2026-10-23  
**Core Value:** Provide a reproducible end-to-end demonstration chain: from simulated normal and malicious MANET traffic traces and non-leaking feature extraction, to ML-based intrusion detection and active node exclusion, demonstrating measurable QoS recovery (Packet Delivery Ratio, throughput, end-to-end delay) over unprotected baseline AODV.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Simulator & AODV Routing

- [x] **SIM-01**: SimPy discrete-event clock engine scheduling node movement and packet transmissions with explicit seed determinism
- [x] **SIM-02**: Random Waypoint (RWP) mobility model updating node coordinates $(x,y)$ with configurable velocity range, pause time, and boundary bounding box
- [x] **SIM-03**: Radio transmission model calculating pairwise Euclidean distance and maintaining dynamic 1-hop neighbor sets ($d \le R$)
- [x] **SIM-04**: RFC 3561 AODV routing protocol implementation supporting RREQ flooding, RREP unicast, RERR route maintenance, sequence numbers, hop counts, and routing table expiration
- [x] **SIM-05**: Application CBR/UDP traffic generator creating data packet flows across source-destination node pairs

### Attack Injection

- [ ] **ATK-01**: Decoupled Blackhole attack strategy advertising highest destination sequence number and 1-hop distance in spoofed RREP, silently dropping all intercepted data traffic
- [ ] **ATK-02**: Decoupled Grayhole attack strategy forwarding control traffic while selectively or probabilistically dropping data packets
- [ ] **ATK-03**: Scenario configuration runner injecting attacker behaviors at runtime without modifying baseline simulator code

### Trace Logging & Feature Engineering

- [ ] **DATA-01**: Packet-level CSV event trace logger recording timestamp, event type, node ID, packet ID, packet type, source, destination, and hop count
- [ ] **DATA-02**: Sliding-window feature extractor aggregating backward in time ($t - W \le t_{event} \le t$) per node/flow calculating forwarding ratio, drop ratio, delay, RREQ rate, RREP rate, throughput, hop count, neighbor count, and speed
- [ ] **DATA-03**: Anti-leakage feature pipeline ensuring zero direct ground-truth metadata in feature matrix $X$
- [ ] **DATA-04**: Scenario- and seed-based dataset partitioner splitting train and test sets strictly across independent scenario runs (zero random row splitting)

### Machine Learning Classification

- [ ] **ML-01**: Multi-classifier training pipeline implementing Random Forest, Decision Tree, and Support Vector Machine models
- [ ] **ML-02**: Security metric evaluator reporting Accuracy, Precision, Recall, F1-Score, False Positive Rate (FPR), and Confusion Matrix for malicious class detection
- [ ] **ML-03**: Model persistence saving trained pipeline estimators and scalers to disk

### Closed-Loop Mitigation & QoS Evaluation

- [ ] **RESP-01**: Dynamic malicious node isolation mechanism filtering out RREPs and route entries involving detected attacker nodes
- [ ] **RESP-02**: Automated comparative QoS benchmark runner calculating PDR, throughput, end-to-end delay, and routing overhead across Baseline AODV, Attack AODV, and AODV+IDS under identical seeds
- [ ] **RESP-03**: Automated visualization generator plotting confusion matrices and comparative QoS recovery charts (Matplotlib / Seaborn)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Extended Attacks & Visualizations

- **ATK-04**: RREQ Flooding / DoS attack injection
- **VIZ-01**: Interactive web dashboard for topology animation and packet flow replay
- **XAI-01**: SHAP-based feature importance explainability analysis

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| NS-3 C++ Simulator | Excluded per AGENTS.md; pure-Python Windows-native architecture eliminates C++ build failures. |
| Deep Learning (LSTM, CNN, GNN) | Overkill for tabular network features; high risk of overfitting and slow closed-loop inference. |
| Blockchain Trust Management | Excessive computational and transmission overhead unsuited for ad-hoc mobile nodes. |
| Physical Hardware / SDR Testbed | Prohibitive hardware cost and irreproducible RF environment; discrete-event simulation provides controlled validation. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SIM-01 | Phase 1 | Complete |
| SIM-02 | Phase 1 | Complete |
| SIM-03 | Phase 1 | Complete |
| SIM-04 | Phase 1 | Complete |
| SIM-05 | Phase 1 | Complete |
| ATK-01 | Phase 2 | Pending |
| ATK-03 | Phase 2 | Pending |
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| DATA-04 | Phase 3 | Pending |
| ML-01 | Phase 3 | Pending |
| ML-02 | Phase 3 | Pending |
| ML-03 | Phase 3 | Pending |
| ATK-02 | Phase 4 | Pending |
| RESP-01 | Phase 5 | Pending |
| RESP-02 | Phase 5 | Pending |
| RESP-03 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---
*Requirements defined: 2026-10-23*  
*Last updated: 2026-10-23 after initial definition*  
