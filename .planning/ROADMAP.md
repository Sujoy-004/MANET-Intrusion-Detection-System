# Roadmap: Machine Learning-Based Intrusion Detection System for MANET

## Overview

This roadmap delivers an end-to-end Machine Learning-Based Intrusion Detection and Response System for MANETs implemented in pure Python on Windows. Beginning with a deterministic discrete-event simulator (SimPy + NetworkX) and standard AODV protocol, the project progresses through controlled Blackhole attack injection and sliding-window trace feature engineering, builds multi-model ML classifiers with anti-leakage scenario partitioning, expands the threat model with subtle Grayhole attacks, integrates closed-loop routing exclusion to actively repair compromised paths, and concludes with automated comparative QoS benchmarking (PDR, throughput, delay, overhead) and academic presentation artifacts.

## Phases

- [x] **Phase 1: Pure-Python MANET Simulator Engine** - Build deterministic discrete-event simulator with RWP mobility, radio range, RFC 3561 AODV routing, and CBR/UDP traffic. (completed 2026-10-25)
- [x] **Phase 2: Blackhole Attack, Trace Logging & Feature Pipeline** - Implement decoupled Blackhole attack, packet-level event trace logging, and non-leaking sliding-window feature extractor. (completed 2026-10-25)
- [x] **Phase 3: Machine Learning Classification Pipeline & Evaluation** - Train classical ML classifiers (RF, DT, SVM) on scenario-held-out datasets with comprehensive security metrics. (completed 2026-10-27)
- [x] **Phase 4: Grayhole Attack & Generalization Testing** - Implement selective/probabilistic Grayhole attack and validate cross-scenario detection across unseen seeds and topologies. (completed 2026-10-27)
- [x] **Phase 5: Closed-Loop IDS Mitigation & Network Re-Evaluation** - Integrate ML predictions into AODV route selection and benchmark QoS recovery against unprotected AODV. (completed 2026-10-28)
- [x] **Phase 6: Visualization, Documentation & Project Deliverables** - Generate publication-quality Matplotlib/Seaborn plots, confusion matrices, and final experimental handbook documentation. (completed 2026-10-28)

## Phase Details

### Phase 1: Pure-Python MANET Simulator Engine

**Goal**: Establish a reproducible, pure-Python discrete-event network simulator supporting dynamic multi-hop ad-hoc wireless communication.
**Mode**: mvp
**Depends on**: Nothing (first phase)
**Requirements**: SIM-01, SIM-02, SIM-03, SIM-04, SIM-05
**Success Criteria** (what must be TRUE):
  1. Discrete-event clock executes simulation scenarios deterministically under explicit integer seeds.
  2. Mobile nodes move within a bounded simulation area following Random Waypoint dynamics.
  3. Dynamic 1-hop neighbor graphs update accurately as nodes enter and exit transmission ranges.
  4. RFC 3561 AODV discovers and maintains multi-hop routes (RREQ, RREP, RERR) with expiring routing table entries.
  5. CBR/UDP application flows successfully deliver packets across multi-hop routes with measurable baseline PDR and throughput.

**Plans**: TBD

Plans:
- [x] 01-01: Core SimPy clock, node model, and deterministic execution runner
- [x] 01-02: Random Waypoint mobility generator and Euclidean radio neighbor graph
- [x] 01-03: RFC 3561 AODV protocol engine and CBR/UDP application traffic generator

### Phase 2: Blackhole Attack, Trace Logging & Feature Pipeline

**Goal**: Introduce controlled adversarial routing behavior, log packet events, and extract non-leaking tabular features.
**Mode**: mvp
**Depends on**: Phase 1
**Requirements**: ATK-01, ATK-03, DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. Attacker node injects false high-sequence RREPs and drops all intercepted data packets via decoupled strategy pattern.
  2. The Blackhole attack causes a demonstrably measurable drop in network Packet Delivery Ratio under identical baseline seeds.
  3. Discrete packet events are logged to CSV traces containing timestamps, node IDs, packet IDs, types, and hop counts.
  4. Sliding-window feature extractor converts traces into tabular flow and node features without ground-truth label leakage.

**Plans**: TBD

Plans:
**Wave 1**
- [x] 02-01: Decoupled Blackhole attack strategy and runtime scenario injector

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 02-02: Structured packet trace logger and attack impact verification gate

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 02-03: Sliding-window feature extraction pipeline computing non-leaking behavioral metrics

### Phase 3: Machine Learning Classification Pipeline & Evaluation

**Goal**: Train, tune, and evaluate classical ML classifiers using rigorous scenario- and seed-based dataset partitioning.
**Mode**: mvp
**Depends on**: Phase 2
**Requirements**: DATA-04, ML-01, ML-02, ML-03
**Success Criteria** (what must be TRUE):
  1. Datasets are partitioned strictly by scenario configuration and seed, guaranteeing zero random row splitting.
  2. Scikit-learn pipelines train and optimize Random Forest, Decision Tree, and Support Vector Machine classifiers.
  3. Model evaluation outputs full security metrics: Accuracy, Precision, Recall, F1-Score, False Positive Rate, and Confusion Matrix.
  4. Best-performing trained models and scalers are serialized to disk for closed-loop inference.

**Plans**: TBD

Plans:
**Wave 1**
- [x] 03-01: Anti-leakage scenario/seed dataset builder and preprocessor

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 03-02: Multi-classifier training and hyperparameter tuning pipeline (RF, DT, SVM)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 03-03: Comprehensive classification evaluation suite and model persistence

### Phase 4: Grayhole Attack & Generalization Testing

**Goal**: Expand adversarial coverage to subtle selective dropping and evaluate model generalization across diverse network scenarios.
**Mode**: mvp
**Depends on**: Phase 3
**Requirements**: ATK-02
**Success Criteria** (what must be TRUE):
  1. Grayhole attacker forwards routing control packets but probabilistically or selectively drops payload traffic.
  2. Feature extractor captures nuanced behavioral degradation under subtle packet loss rates.
  3. Trained intrusion detection models are evaluated on unseen topologies, varying node speeds, and Grayhole variants.

**Plans**: 2 plans

**Wave 1**
- [x] 04-01: Grayhole attack strategy, honest routing hook, dynamic scenario & time-aware feature extraction

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 04-02: Zero-shot transfer, multi-attack dataset & model training, and generalization stress matrix

### Phase 5: Closed-Loop IDS Mitigation & Network Re-Evaluation

**Goal**: Couple ML predictions with dynamic AODV route isolation to repair network connectivity and quantify performance recovery.
**Mode**: mvp
**Depends on**: Phase 4
**Requirements**: RESP-01, RESP-02
**Success Criteria** (what must be TRUE):
  1. Predicted malicious nodes are dynamically isolated or penalized during AODV route discovery and selection.
  2. Closed-loop simulation re-routes traffic around compromised nodes without blacklisting benign nodes.
  3. Comparative QoS benchmarks quantify PDR, throughput, end-to-end delay, and routing overhead across Baseline AODV vs Attack AODV vs AODV+IDS under identical seeds.

**Plans**: 2 plans

**Wave 1**
- [x] 05-01: Closed-loop IDS response engine and AODV route exclusion integration

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 05-02: Comparative QoS benchmarking pipeline (Baseline vs Attack vs AODV+IDS)

### Phase 6: Visualization, Documentation & Project Deliverables

**Goal**: Consolidate experimental results, generate publication-grade figures, and prepare the project report and presentation.
**Mode**: mvp
**Depends on**: Phase 5
**Requirements**: RESP-03
**Success Criteria** (what must be TRUE):
  1. Automated Matplotlib/Seaborn scripts render confusion matrices, ROC/PR curves, and QoS recovery comparison bar/line charts.
  2. Complete experiment logs and metric summary tables map directly to scenario configurations.
  3. Final project documentation and demonstration walkthrough guide are fully validated against the codebase.

**Plans**: TBD

Plans:
**Wave 1**
- [x] 06-01: Automated plotting suite for classification metrics and network QoS recovery

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06-02: Final project report synthesis, viva defense guide, and experiment handbook validation

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Pure-Python MANET Simulator Engine | 3/3 | Complete    | 2026-10-25 |
| 2. Blackhole Attack, Trace Logging & Feature Pipeline | 3/3 | Complete    | 2026-10-25 |
| 3. Machine Learning Classification Pipeline & Evaluation | 3/3 | Complete    | 2026-10-27 |
| 4. Grayhole Attack & Generalization Testing | 2/2 | Complete    | 2026-10-27 |
| 5. Closed-Loop IDS Mitigation & Network Re-Evaluation | 0/2 | Not started | - |
| 6. Visualization, Documentation & Project Deliverables | 2/2 | Complete    | 2026-10-28 |
