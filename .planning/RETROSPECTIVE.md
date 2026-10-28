# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 - Machine Learning-Based Intrusion Detection System for MANET

**Shipped:** 2026-10-28  
**Phases:** 6 | **Plans:** 15 | **Sessions:** 6

### What Was Built
- Pure-Python discrete-event MANET simulator (SimPy + NetworkX) with RWP mobility, Euclidean radio, RFC 3561 AODV routing, and CBR/UDP traffic.
- Decoupled Blackhole and Grayhole attack injection strategies with zero core simulator pollution.
- Deterministic 10-column packet event trace logging and anti-leakage sliding-window tabular feature engineering.
- Seed-partitioned train/test dataset splits (seeds 42 & 43 train, seed 44 test) with zero random row splitting.
- Multi-classifier Scikit-learn pipelines with 5-fold CV, locked FPR <= 1.0% champion selection gate, and model persistence.
- Closed-loop Online IDS response engine (2-strike confirmation, 30s quarantine decay, route invalidation) achieving 92.9% PDR recovery on Blackhole.
- Headless-safe publication-grade plotting suite (`ml/plots.py`), 69-test test suite, and 78 KB monolithic B.Tech thesis project report (`docs/FINAL_PROJECT_REPORT.md`).

### What Worked
- **Pure Python over NS-3:** Dropping NS-3 C++ on Ubuntu in favor of in-repo SimPy + NetworkX eliminated complex toolchain issues, delivered sub-second execution (~70k events/sec), and enabled complete reproducibility on native Windows.
- **Strict Anti-Leakage Discipline:** Decoupling attack logic, enforcing seed-disjoint splits, and isolating ground truth labels preserved scientific integrity.
- **Online IDS 2-Strike Confirmation:** Requiring $K=2$ consecutive detection windows before route isolation prevented catastrophic false isolation cascades while still recovering 92.9% of normal delivery ratio.
- **Contract-First Development:** Rigid compliance with `AGENTS.md` non-negotiable gates prevented architectural regression.

### What Was Inefficient
- Initial Phase 2/3 executions lacked the unified verification frontmatter structure, requiring retroactive validation alignment during milestone closeout.
- Subagent type resolution in this specific CLI environment required falling back to `TypeName: "self"` due to missing optional tool components in named subagent specs.

### Patterns Established
- Decoupled attack strategy pattern: simulator receives attack strategies via scenario injection, keeping baseline code identical across normal and attack runs.
- Anti-leakage invariance testing: asserting that permuting ground truth labels causes exactly zero numerical difference in feature matrix $X$.
- 3-Way QoS Triad Benchmarking: running Baseline AODV, Attack AODV, and AODV+IDS across identical seeds to quantify net recovery.

### Key Lessons
1. Strict seed determinism across mobility, radio loss, and attack decisions is the single most important factor for reliable multi-run MANET evaluation.
2. In network security ML, low False Positive Rate (FPR <= 1.0%) is vastly more critical than raw accuracy or recall, because false isolations fracture ad-hoc topology.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | 6 | 6 | Established pure-Python simulator, decoupled attacks, anti-leakage ML pipeline, closed-loop mitigation, and thesis deliverables |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 69 | 100% core pass | Zero C++ or external binaries |

### Top Lessons (Verified Across Milestones)

1. Seed-disjoint holdouts are mandatory for discrete-event packet data; random row splits produce artificial overoptimism.
2. Active closed-loop feedback provides real-world validation of intrusion detection efficacy far beyond static classification metrics.
