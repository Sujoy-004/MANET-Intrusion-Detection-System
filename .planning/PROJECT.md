# Machine Learning-Based Intrusion Detection System for MANET

## What This Is

A complete software-based Intrusion Detection and Response System for Mobile Ad-Hoc Networks (MANET). It couples an in-repo, pure-Python discrete-event network simulator (SimPy + NetworkX) implementing AODV routing and controlled attack injections (Blackhole and Grayhole) with Scikit-learn machine learning classifiers and an active routing isolation mechanism. The system is designed for Windows-native execution and academic demonstration.

## Core Value

Provide a fully reproducible end-to-end demonstration chain: from simulated normal and malicious MANET traffic traces and non-leaking feature extraction, to ML-based intrusion detection and active node exclusion, demonstrating measurable QoS recovery (Packet Delivery Ratio, throughput, end-to-end delay) over unprotected baseline AODV.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Pure-Python discrete-event MANET simulator implementing Random Waypoint mobility, transmission range/neighbor topology, CBR/UDP traffic, and standard AODV routing (RREQ, RREP, RERR, sequence numbers, hop counts)
- [ ] Attack injection strategies decoupled from core simulator: Blackhole (immediate false high-sequence RREP) and Grayhole (selective/probabilistic forwarding drops)
- [ ] Deterministic trace logging outputting discrete packet events to structured CSV with explicit seed reproducibility
- [ ] Sliding-window feature extraction pipeline computing node/flow behavioral metrics without label leakage
- [ ] Rigorous scenario- and seed-based dataset partitioning (zero random row splitting)
- [ ] Multi-classifier ML training pipeline (Random Forest, SVM, Decision Tree / Logistic Regression) evaluated on Precision, Recall, F1, FPR, and Confusion Matrix
- [ ] Closed-loop IDS response mechanism dynamically blacklisting/penalizing detected malicious nodes in AODV route selection
- [ ] Comparative evaluation framework benchmarking Baseline AODV vs. Attack AODV vs. AODV + IDS across PDR, Throughput, Delay, and Routing Overhead

### Out of Scope

- NS-3, C++, Docker, WSL, or Linux VM dependencies — strictly pure-Python Windows-native architecture per AGENTS.md
- Deep learning, federated learning, blockchain, or mobile apps — scope restricted to proven, interpretable ML models suitable for B.Tech project rigor
- More than two initial attack classes (Flooding/DoS deferred) — Blackhole and Grayhole are the required primary targets
- Real physical hardware testbeds — 100% software discrete-event simulation

## Context

- Target OS: Windows 10/11 native (Python 3.11.8, SimPy 4.1.2, NetworkX 3.6.1, Pandas 3.0.2, Scikit-learn 1.8.0).
- Governing Specifications: `MANET_IDS_BTech_Execution_Guide.md` and `AGENTS.md` (contract takes precedence).
- Codebase mapping documentation is pre-established in `.planning/codebase/`.

## Constraints

- **Language**: Python 3.11+ only; no C/C++ or external compilation toolchains
- **Determinism**: Every simulation and split must take an explicit integer seed for reproducible traces and metrics
- **Data Integrity**: No label leakage into feature sets; zero random-row splitting (hold out by scenario/seed/configuration)
- **Evaluation Integrity**: Always report comprehensive classification metrics (precision, recall, F1, FPR, confusion matrix) alongside network QoS metrics (PDR, throughput, delay, routing overhead)
- **Comparison Baseline**: Every claim of IDS efficacy must be quantitatively backed by side-by-side comparison with unprotected AODV under identical scenario seeds

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Pure-Python SimPy/NetworkX Simulator | Avoids brittle NS-3 C++ build issues on Windows; achieves ~70k events/sec with sub-second runs | — Pending |
| Decoupled Attack Injection | Attack behaviors injected at scenario runtime to keep core AODV simulator clean for baseline runs | — Pending |
| Scenario/Seed-Based Data Holdout | Prevents temporal correlation leakage inherent in random row splits of packet traces | — Pending |
| Active Routing Isolation for Mitigation | Demonstrates tangible closed-loop network value rather than passive offline detection | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-10-23 after initialization*
