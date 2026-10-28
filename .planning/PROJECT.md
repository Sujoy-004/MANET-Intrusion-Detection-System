# Machine Learning-Based Intrusion Detection System for MANET

## What This Is

A complete software-based Intrusion Detection and Response System for Mobile Ad-Hoc Networks (MANET). It couples an in-repo, pure-Python discrete-event network simulator (SimPy + NetworkX) implementing RFC 3561 AODV routing and controlled attack injections (Blackhole and Grayhole) with Scikit-learn machine learning classifiers and an active routing isolation mechanism. The system is designed for Windows-native execution, publication-grade visualization, and academic demonstration.

## Core Value

Provide a fully reproducible end-to-end demonstration chain: from simulated normal and malicious MANET traffic traces and non-leaking feature extraction, to ML-based intrusion detection and active node exclusion, demonstrating measurable QoS recovery (Packet Delivery Ratio, throughput, end-to-end delay) over unprotected baseline AODV.

## Requirements

### Validated

- ✓ Pure-Python discrete-event MANET simulator implementing Random Waypoint mobility, transmission range/neighbor topology, CBR/UDP traffic, and standard RFC 3561 AODV routing (RREQ, RREP, RERR, sequence numbers, hop counts) - v1.0
- ✓ Attack injection strategies decoupled from core simulator: Blackhole (immediate false high-sequence RREP) and Grayhole (selective/probabilistic forwarding drops) - v1.0
- ✓ Deterministic trace logging outputting discrete packet events to structured 10-column CSV with explicit seed reproducibility - v1.0
- ✓ Sliding-window feature extraction pipeline computing node/flow behavioral metrics without label leakage - v1.0
- ✓ Rigorous scenario- and seed-based dataset partitioning (zero random row splitting) - v1.0
- ✓ Multi-classifier ML training pipeline (Random Forest, SVM, Decision Tree) evaluated on Precision, Recall, F1, FPR, and Confusion Matrix with locked FPR <= 1.0% champion gate - v1.0
- ✓ Closed-loop IDS response mechanism dynamically isolating detected malicious nodes with 2-strike confirmation and quarantine decay in AODV route selection - v1.0
- ✓ Comparative evaluation framework benchmarking Baseline AODV vs. Attack AODV vs. AODV + IDS across PDR, Throughput, Delay, and Routing Overhead (achieved 92.9% PDR recovery on Blackhole) - v1.0
- ✓ Publication-grade figure generation suite (Matplotlib/Seaborn 300 DPI) and comprehensive 6-chapter monolithic B.Tech project thesis report (`docs/FINAL_PROJECT_REPORT.md`) - v1.0

### Active (Future v2.0 Scope)

- [ ] RREQ Flooding / Denial-of-Service (DoS) attack strategy injection
- [ ] Interactive web dashboard for topology animation and packet flow replay
- [ ] Model explainability via SHAP (SHapley Additive exPlanations) feature attributions

### Out of Scope

- NS-3, C++, Docker, WSL, or Linux VM dependencies — strictly pure-Python Windows-native architecture per AGENTS.md
- Deep learning (LSTM, CNN, GNN), federated learning, blockchain, or mobile apps — scope restricted to proven, interpretable ML models suitable for B.Tech project rigor
- More than two initial attack classes in v1.0 (Flooding/DoS deferred to v2.0) — Blackhole and Grayhole are the validated targets
- Real physical hardware testbeds — 100% software discrete-event simulation with mathematical determinism

## Context

- Target OS: Windows 10/11 native (Python 3.11.8, SimPy 4.1.2, NetworkX 3.6.1, Pandas 3.0.2, Scikit-learn 1.8.0, Matplotlib 3.10.8, Seaborn 0.13.2).
- Governing Specifications: `MANET_IDS_BTech_Execution_Guide.md` and `AGENTS.md` (contract takes precedence).
- Codebase state: 6,645 lines of pure Python, 69 unit/integration/pipeline tests passing (100%), 15 publication figures generated, 78 KB thesis report completed.
- Shipped Milestone: v1.0 MVP on 2026-10-28.

## Constraints

- **Language**: Python 3.11+ only; no C/C++ or external compilation toolchains
- **Determinism**: Every simulation and split must take an explicit integer seed for reproducible traces and metrics
- **Data Integrity**: No label leakage into feature sets; zero random-row splitting (hold out by scenario/seed/configuration)
- **Evaluation Integrity**: Always report comprehensive classification metrics (precision, recall, F1, FPR, confusion matrix) alongside network QoS metrics (PDR, throughput, delay, routing overhead)
- **Comparison Baseline**: Every claim of IDS efficacy must be quantitatively backed by side-by-side comparison with unprotected AODV under identical scenario seeds

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Pure-Python SimPy/NetworkX Simulator | Avoids brittle NS-3 C++ build issues on Windows; achieves ~70k events/sec with sub-second runs | ✓ Good |
| Decoupled Attack Injection | Attack behaviors injected at scenario runtime to keep core AODV simulator clean for baseline runs | ✓ Good |
| Scenario/Seed-Based Data Holdout | Prevents temporal correlation leakage inherent in random row splits of packet traces | ✓ Good |
| Locked FPR <= 1.0% Gate | Prevents benign node false-isolation cascades in closed-loop operation | ✓ Good |
| OnlineIDS 2-Strike Confirmation | Two consecutive positive predictions required before node isolation; prevents false-alarm route teardowns | ✓ Good |
| Active Routing Isolation for Mitigation | Demonstrates tangible closed-loop network value rather than passive offline detection (92.9% PDR recovery) | ✓ Good |
| Monolithic LaTeX-Grade Markdown Thesis Report | Monolithic 6-chapter report with explicit provenance footnotes fulfilling all B.Tech degree requirements | ✓ Good |

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
*Last updated: 2026-10-28 after v1.0 milestone completion*
