# Project Milestones: Machine Learning-Based Intrusion Detection System for MANET

## v1.0 MVP / Initial Release (Shipped: 2026-10-28)

**Delivered:** Pure-Python Windows-native MANET discrete-event simulator with RFC 3561 AODV routing, decoupled Blackhole/Grayhole attack injections, sliding-window anti-leakage feature engineering, cost-sensitive ML intrusion detection (FPR <= 1.0%), dynamic closed-loop route isolation proving 92.9% QoS recovery, and publication-grade deliverables with B.Tech thesis documentation.

**Phases completed:** 1-6 (15 plans total, 69 automated tests passing)

**Key accomplishments:**
- **Phase 01:** Pure-Python discrete-event MANET simulator engine (SimPy + NetworkX) with Random Waypoint mobility, Euclidean unit-disk radio, RFC 3561 AODV routing (RREQ/RREP/RERR), and CBR/UDP application flows.
- **Phase 02:** Decoupled Blackhole attack strategy, 10-column packet event trace logging, sliding-window anti-leakage feature pipeline, and quantitative Gate 2 network degradation verification (>50% PDR drop).
- **Phase 03:** Seed-partitioned anti-leakage dataset architecture (seeds 42 & 43 train, seed 44 test), multi-classifier training pipeline (Random Forest, Decision Tree, SVM), locked FPR <= 1.0% champion selection gate, and model persistence.
- **Phase 04:** Decoupled Grayhole probabilistic attack strategy, time-aware pre/post-onset window labeling, multi-attack classifier tuning (RF champion F1 0.7593, FPR 0.0099), and 18-combination cross-scenario generalization matrix.
- **Phase 05:** Closed-loop Online IDS mitigation engine (`OnlineIDS` with 2-strike confirmation $K=2, \tau=0.50$, 30s quarantine decay, dynamic route invalidation), and 3-way comparative QoS benchmarking proving 92.9% PDR recovery.
- **Phase 06:** Headless-safe publication-grade plotting suite (`ml/plots.py`), full 69-test test suite, 78 KB monolithic B.Tech project thesis report (`docs/FINAL_PROJECT_REPORT.md`), and comprehensive viva defense presentation materials.

**Stats:**
- 6,645 lines of Python code
- 6 phases, 15 plans, 69 automated tests (100% passing)
- Timeline: 2026-10-22 to 2026-10-28 (7 days)
- Git range: `feat(01-01)` to `docs(06)`

**What's next:** Milestone v1.0 shipped successfully. Future extensions (v2.0) may address RREQ Flooding / DoS attacks, interactive web visualization dashboard, and SHAP explainability.

---
