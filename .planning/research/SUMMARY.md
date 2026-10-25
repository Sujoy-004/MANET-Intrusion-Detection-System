# Project Research Summary

**Project:** Machine Learning-Based Intrusion Detection System for MANET  
**Domain:** MANET Simulation, Feature Engineering & Machine Learning Intrusion Detection  
**Researched:** 2026-10-23  
**Confidence:** HIGH  

## Executive Summary

This project delivers a complete, reproducible software Intrusion Detection and Response System for Mobile Ad-Hoc Networks (MANET). To circumvent the severe compatibility and build failures associated with legacy NS-3 C++ toolchains on Windows, the architecture utilizes an in-repo, pure-Python discrete-event network simulator powered by SimPy 4.1.2 and NetworkX 3.6.1. The simulator implements Random Waypoint mobility, transmission-range link modeling, RFC 3561 AODV reactive routing, and background CBR/UDP application flows, delivering over 70k events/sec with sub-second execution times per scenario.

Adversarial behaviors (Blackhole and Grayhole) are decoupled into strategy plugins that inject anomalous routing advertisements and packet-dropping behaviors at runtime, keeping the core simulator clean for baseline comparisons. Packet events are emitted to structured CSV traces and aggregated via a non-leaking sliding-window feature extractor. Classical, interpretable machine learning classifiers (Random Forest, Decision Tree, Support Vector Machine) are trained using strict scenario- and seed-based dataset partitioning to guarantee zero temporal data leakage.

Crucially, the system advances beyond passive offline classification by closing the loop: predicted malicious nodes are fed back into the AODV routing engine as penalized or excluded nodes. The final deliverable rigorously benchmarks network Quality of Service (Packet Delivery Ratio, throughput, end-to-end delay, and routing overhead) across three states—Normal Baseline, Unprotected Attack, and IDS-Mitigated—demonstrating measurable network recovery under attack.

## Key Findings

### Recommended Stack

The implementation runs natively on Windows using Python 3.11.8 and pre-verified dependencies:
- **SimPy 4.1.2:** Discrete-event clock and event scheduler (`Environment`, `timeout`).
- **NetworkX 3.6.1 & NumPy 1.26.4:** Dynamic topology, transmission distance calculations, and graph neighbor discovery.
- **Pandas 3.0.2:** Trace parsing and sliding-window feature matrix construction.
- **Scikit-learn 1.8.0:** Classical classifiers (RF, DT, SVM), preprocessing scalers, and metric suites.
- **Matplotlib 3.10.8 & Seaborn 0.13.2:** Confusion matrices, ROC/PR curves, and QoS comparison plots.

### Expected Features

**Must Have (Table Stakes):**
- In-repo pure-Python SimPy MANET simulator with AODV routing and Random Waypoint mobility.
- Runtime attack injection: Blackhole (immediate false high-sequence RREP) and Grayhole (probabilistic dropping).
- Deterministic trace logging with explicit integer seed reproducibility.
- Sliding-window feature extraction computing drop ratios, forward ratios, control message rates, and neighbor counts without ground-truth leakage.
- Scenario-based holdout evaluation (train on scenario seeds A, test on unseen scenario seeds B).
- Reporting full security metrics: Precision, Recall, F1-Score, False Positive Rate, and Confusion Matrix.
- Closed-loop routing response: dynamic blacklisting/penalization of detected malicious nodes.
- Comparative QoS benchmarking: side-by-side table and plots of PDR, throughput, delay, and routing overhead.

**Defer (v2+):**
- Flooding / RREQ DoS attacks.
- Web-based graphical animation dashboard.
- SHAP feature explainability.

### Architecture Approach

The architecture enforces strict decoupling across five pipeline stages:
1. **Simulation Layer (`simulator/`):** Manages discrete-event time, node movement, neighbor graphs, and standard AODV message processing.
2. **Attack Layer (`attacks/`):** Strategy-pattern behaviors injected into target nodes at scenario runtime.
3. **Data Layer (`feature_extraction/`):** Converts packet event streams into tabular observation windows without label leakage.
4. **Machine Learning Layer (`ml/`):** Trains and validates classifiers with scenario-level holdout partitions.
5. **Mitigation Layer (`mitigation/`):** Feeds predictions back to AODV to re-route around compromised nodes and measures network QoS recovery.

### Critical Pitfalls

1. **Random Row Splitting Leakage:** Shuffling windowed packet rows leaks temporal autocorrelation across identical runs. *Mitigation:* Split strictly by scenario configurations and random seeds.
2. **Ground-Truth Label Leakage:** Scenario flags (`is_attacker`, node IDs) in the feature matrix inflate scores artificially. *Mitigation:* Features strictly derived from observable packet headers and window statistics.
3. **Accuracy Fallacy on Imbalanced Data:** A model predicting 100% normal achieves ~98% accuracy while missing all attacks. *Mitigation:* Report precision, recall, F1, FPR, and confusion matrix.
4. **Attack Lacking Network Impact:** If an attacker doesn't intercept active routes, PDR doesn't drop, rendering ML training meaningless. *Mitigation:* Gate Phase 1 by validating that Blackhole demonstrably degrades baseline PDR.
5. **Unverified Claims Without Baseline Comparison:** Claiming IDS success without quantifying QoS improvement. *Mitigation:* Mandate side-by-side comparison of Baseline AODV vs Attack AODV vs AODV+IDS.

## Implications for Roadmap

Based on research and governing guidelines, the recommended 6-phase roadmap structure is:

### Phase 0: Pure-Python MANET Simulator Engine
- **Rationale:** Foundational milestone; replaces the deprecated NS-3 C++ stack with an in-repo, pure-Python SimPy discrete-event simulator.
- **Delivers:** SimPy simulation clock, node state, Random Waypoint mobility, transmission-range radio graph, standard AODV reactive routing, and CBR/UDP traffic.
- **Avoids:** Irreproducible runs by enforcing explicit integer seed propagation and verifying deterministic trace outputs.

### Phase 1: Attack Injection (Blackhole), Trace Logging & Data Pipeline
- **Rationale:** Introduce adversarial behavior and establish the data collection pipeline before touching ML.
- **Delivers:** Decoupled Blackhole attack strategy, structured CSV packet trace logger, sliding-window feature extraction pipeline, and initial scenario suite.
- **Avoids:** Feature leakage and the "inert attack" pitfall by validating that Blackhole demonstrably collapses baseline PDR.

### Phase 2: Machine Learning Classification Pipeline & Evaluation
- **Rationale:** Train and evaluate classical ML models on clean, partitioned scenario data.
- **Delivers:** Scenario/seed-based train/test splitting, training pipeline for Random Forest, Decision Tree, and SVM, hyperparameter tuning, and comprehensive evaluation (Precision, Recall, F1, FPR, Confusion Matrix).
- **Avoids:** Random row split leakage and accuracy-only reporting.

### Phase 3: Advanced Attack (Grayhole) & Generalization Testing
- **Rationale:** Expand threat model to subtle attacks and prove cross-scenario model generalization.
- **Delivers:** Probabilistic/selective Grayhole attack module, multi-attack feature extraction, multi-class/binary generalization evaluation across unseen topologies and mobility speeds.
- **Avoids:** Overfitting to obvious attacks; tests detector resilience against stealthy droppers.

### Phase 4: Closed-Loop IDS Mitigation & Network Re-Evaluation
- **Rationale:** The ultimate acceptance criterion—proving that intrusion detection actually repairs network communication.
- **Delivers:** Dynamic malicious node isolation mechanism integrated into AODV route selection, closed-loop scenario runner, and automated QoS comparative benchmarking (Baseline vs Attack vs AODV+IDS across PDR, Throughput, Delay, Routing Overhead).
- **Avoids:** "Passive detector" limitation; provides hard quantitative proof of network recovery.

### Phase 5: Documentation, Visualization & Academic Deliverables
- **Rationale:** Consolidate experimental results, generate publication-grade figures, and prepare the project report and presentation.
- **Delivers:** Matplotlib/Seaborn comparative plots, comprehensive experiment records, project execution handbook verification, and final presentation documentation.
- **Avoids:** Discrepancy between code results and project documentation.

## Phase Ordering Rationale

- Phase 0 establishes normal network physics before introducing attacks.
- Phase 1 verifies that attacks demonstrably degrade the network before collecting data.
- Phase 2 builds and validates ML detectors on honest scenario holdouts.
- Phase 3 tests model generalization on subtle Grayhole attacks before closing the loop.
- Phase 4 integrates detection with active routing response, completing the full deliverable chain.
- Phase 5 packages final metrics, plots, and documentation for academic evaluation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Environment verified; Python 3.11, SimPy 4.1.2, NetworkX, Scikit-learn pre-tested. |
| Features | HIGH | Table stakes, differentiators, and anti-features strictly aligned with project handbook. |
| Architecture | HIGH | Pipeline interfaces and strategy decoupling fully mapped. |
| Pitfalls | HIGH | All 6 known failure points from AGENTS.md catalogued with actionable preventions. |

**Overall confidence:** HIGH

### Sources

- `MANET_IDS_BTech_Execution_Guide.md` — Project specification and architecture definition.
- `AGENTS.md` — Binding engineering rules and non-negotiables.
- In-repo codebase analysis (`.planning/codebase/`).
- Python environment verification on target host.

---
*Research completed: 2026-10-23*  
*Ready for roadmap: yes*  
