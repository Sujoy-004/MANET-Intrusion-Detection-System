# Academic Presentation Deck Outline (14 Slides)

**Project Title:** Machine Learning-Based Intrusion Detection and Closed-Loop Response System for MANET  
**Format:** 14-Slide Presentation Deck for B.Tech Major Project Defense  
**Timing:** 12–15 Minutes Presentation + 5–10 Minutes Q&A  
**Visual Asset Directory:** `results/plots/` and `.archify/diagrams/`

---

## Slide 1: Title & Project Overview

### Visual Layout
- Title in bold academic serif/sans-serif.
- Subtitle: A Reproducible, Windows-Native Pure-Python Discrete-Event Simulator & Closed-Loop ML Defense.
- Candidate Names, Roll Numbers, Supervisor Name, Department of Computer Science & Engineering.

### Bullet Points
- **Domain:** Mobile Ad-Hoc Networks (MANET) & Wireless Cyber-Security.
- **Target Threat:** Routing-layer insider attacks (Blackhole & Grayhole) exploiting RFC 3561 AODV sequence numbers.
- **Core Contribution:** Pure-Python discrete-event simulator + Non-leaking ML pipeline + Closed-loop dynamic route invalidation.
- **Key Headline:** Recovers **$92.9\%$ of lost baseline PDR** ($14.2\% \to 61.0\%$) with bounded routing overhead ($+0.0307$).

### Speaker Notes
> *"Respected chairperson, members of the evaluation committee, and faculty mentors. Today we present our major project: an end-to-end Machine Learning-Based Intrusion Detection and Closed-Loop Response System for Mobile Ad-Hoc Networks. We will demonstrate how our system models routing attacks, extracts telemetry without data leakage, and actively restores network communication through dynamic route table invalidation."*

---

## Slide 2: Problem Statement & MANET Vulnerabilities

### Visual Layout
- Split screen: Diagram showing infrastructure network with perimeter firewall vs. decentralized MANET mesh without perimeter.

### Bullet Points
- **The Cooperative Routing Dilemma:** MANETs lack fixed base stations or centralized controllers; intermediate nodes act as autonomous routers.
- **Mutual Trust Assumption:** RFC 3561 AODV assumes all nodes honestly report sequence numbers and faithfully forward transit packets.
- **The Insider Threat:** A single rogue insider can exploit protocol rules to intercept and drop traffic without cracking cryptographic keys.
- **Research Gap in Literature:** Published academic work suffers from severe data leakage (random row splits) and terminates at passive classifier metrics without demonstrating active routing recovery.

### Speaker Notes
> *"Unlike conventional wired or cellular networks, MANETs have no perimeter firewalls. Every node participates in route discovery. AODV relies on implicit trust: intermediate nodes are assumed to forward packets honestly. When an insider breaks this trust, network delivery collapses. Furthermore, existing research rarely demonstrates closed-loop mitigation, leaving the network partitioned even after detection."*

---

## Slide 3: Attack Models (Blackhole & Grayhole)

### Visual Layout
- Attack progression diagram showing RREQ broadcast, spoofed RREP with $SeqNum=2^{32}-1$, and downstream packet drops.

### Bullet Points
- **Blackhole Attack (RFC 3561 Sequence Number Exploit):**
  - Advertises maximum 32-bit sequence number: $SeqNum = 2^{32}-1$ and $HopCount = 1$.
  - Forces source nodes to accept its forged path as freshest and shortest.
  - Drops $100\%$ of intercepted data packets ($PDR \to 14.18\%$).
- **Grayhole Attack (Selective / Intermittent Dropping):**
  - Forwards control traffic (RREQ/RREP) honestly; drops data packets probabilistically ($p = 0.3, 0.5, 0.7$).
  - Mimics natural packet losses caused by RF fading and node mobility.

### Speaker Notes
> *"We evaluate two distinct attack models. In a Blackhole attack, the adversary advertises an impossible sequence number of 2^32-1, winning route elections unconditionally and dropping all traffic. In a Grayhole attack, the adversary drops packets probabilistically, evading simple threshold alarms by blending into normal wireless fading losses."*

---

## Slide 4: Pure-Python SimPy Simulator Architecture

### Visual Layout
- Diagram embed: `.archify/diagrams/system_architecture.html` screenshot showing the SimPy clock, mobility, radio graph, AODV, and traffic modules.

### Bullet Points
- **Engine Selection:** Pure Python (SimPy 4.1.2 + NetworkX 3.6.1); 100% Windows-native.
- **Abandoning NS-3:** Eliminates complex C++ compiler requirements (`gcc`, `cmake`) and multi-hour build cycles.
- **Simulation Speed:** 50 nodes, 8 CBR flows, 300s simulated duration executes in **$0.83$ seconds wall-clock time** (~70,000 events/sec).
- **Physical Fidelity:** Random Waypoint mobility ($1–10\text{ m/s}$), Euclidean radio links ($R=250\text{m}$), multi-flow CBR/UDP generation ($10\text{ pps}$, $512\text{B}$).
- **Determinism:** Explicit integer seeds ensure $100\%$ reproducible traces.

### Speaker Notes
> *"To ensure true cross-platform reproducibility on Windows, we built our discrete-event simulator using SimPy and NetworkX. A complete 300-second scenario with 50 mobile nodes executes in under one second. Every run is deterministic and seed-driven, allowing us to perform rigorous multi-seed comparative benchmarking."*

---

## Slide 5: Non-Leaking Feature Extraction Pipeline

### Visual Layout
- Diagram showing backward-sliding window ($W=5.0\text{s}$) aggregating raw packet trace events into 9 features.

### Bullet Points
- **Zero Label Leakage:** Simulator logs only raw physical events (tx, rx, drop); ground truth is joined externally from scenario schedules.
- **Temporal Sliding Window:** $W = 5.0\text{s}$ backward aggregation; strictly zero forward-looking data access.
- **9 Behavioral Traffic Features:**
  - Forwarding & Drop Ratios ($PFR$, $PDR_{\text{drop}}$).
  - Transit Delay ($\overline{D}$).
  - Control Message Rates ($RREQ_{\text{rate}}$, $RREP_{\text{rate}}$).
  - Throughput ($\Theta$), Hop Count ($H$), Neighbor Count ($N_{\text{deg}}$), Mobility Speed ($v$).
- **Strict Seed-Based Holdout:** Trained on Seeds 42 & 43 ($34,800$ samples); tested on untouched Seed 44 ($17,400$ samples).

### Speaker Notes
> *"A primary contribution of this work is methodological integrity. We eliminated data leakage: features are calculated strictly from local event traces over 5-second sliding windows. Most importantly, we never split by random rows; our models were evaluated on an untouched simulation seed to test genuine out-of-sample generalization."*

---

## Slide 6: Multi-Classifier ML Evaluation & The FPR <= 1% Gate

### Visual Layout
- Figure embed: `results/plots/classifier_comparison_metrics.png` highlighting Accuracy, Precision, Recall, F1, and the dashed red FPR gate line.

### Bullet Points
- **The Security Operational Gate:** In MANET routing, false positives disconnect honest nodes. An operational gate of $\text{FPR} \le 1.0\%$ is mandatory.
- **Classifier Benchmark (Seed 44 Test Partition):**
  - **Random Forest:** Accuracy $97.44\%$, F1 $75.93\%$, **FPR $0.99\%$ (PASSED GATE)**.
  - **Decision Tree:** Accuracy $95.01\%$, F1 $67.66\%$, FPR $3.42\%$ (FAILED GATE).
  - **SVM (RBF):** Accuracy $54.68\%$, Recall $99.75\%$, FPR $46.38\%$ (FAILED GATE).
- **The SVM Fallacy:** While SVM achieved $99.75\%$ recall, its $46.4\%$ false alarm rate causes catastrophic network fragmentation.

### Speaker Notes
> *"This slide presents our classifier benchmark. While SVM achieved an impressive 99.75% recall, it failed our operational gate with a 46% false positive rate—quarantining half the honest network. Random Forest was the only model to pass our 1% gate, achieving 97.44% accuracy, a 75.93% F1-score, and a false positive rate of just 0.99%."*

---

## Slide 7: Feature Importance & Interpretability

### Visual Layout
- Figure embed: `results/plots/feature_importance_ranking.png` showing side-by-side Permutation Importance and Gini Impurity.

### Bullet Points
- **Permutation Importance Dominance:**
  - **`packet_drop_ratio` ($0.2156$):** Directly captures malicious packet sink behavior.
  - **`hop_count` ($0.1685$):** Identifies anomalous single-hop claims in spoofed RREPs.
  - **`packet_forward_ratio` ($0.0147$):** Verifies relay consistency.
- **Debunking Gini Artifacts:** `mobility_speed` showed high Gini impurity ($0.5461$) due to continuous numeric splits, but permutation importance proved its actual predictive contribution is near zero ($0.0006$).

### Speaker Notes
> *"Using permutation importance, we validated that our model makes decisions based on genuine physical attack dynamics. The two dominant features are Packet Drop Ratio and Hop Count. This proves the classifier is identifying Blackholes and Grayholes by their drop and spoofing behaviors, rather than memorizing environmental artifacts."*

---

## Slide 8: Environmental Stress & Generalization Matrix

### Visual Layout
- Figure embed: `results/plots/stress_mobility_vs_recall.png` and `stress_droprate_vs_pdr.png`.

### Bullet Points
- **18-Parameter Stress Matrix:** Evaluated across speeds ($1, 5, 10\text{ m/s}$), drop rates ($p=0.3, 0.5, 0.7$), and densities ($30\text{n}, 50\text{n}$).
- **Mobility Impact ($10.0\text{ m/s}$):** High node velocity causes frequent link breaks ($2–4\text{s}$ link lifespan); honest drop bursts reduce recall and elevate false alarms.
- **Grayhole Boundary ($p=0.3$ to $0.7$):** Low drop rates ($p=0.3$) maintain higher delivery but are harder to isolate; multi-feature sliding windows achieve over $82\%$ recall on $p \ge 0.5$.

### Speaker Notes
> *"We stress-tested the model across 18 parameter combinations. At walking and running speeds (1 to 5 m/s), detection is robust. However, at vehicular speeds of 10 m/s, frequent mobility-induced link breaks cause honest nodes to drop packets, illustrating the physical boundary of single-layer behavioral detection."*

---

## Slide 9: Closed-Loop IDS & Dynamic Route Exclusion

### Visual Layout
- Diagram embed: `.archify/diagrams/closed_loop_sequence.html` screenshot illustrating 2-strike confirmation and route invalidation sequence.

### Bullet Points
- **OnlineIDS Controller:** Runs periodically every $5.0\text{s}$ during simulation execution.
- **2-Strike Confirmation Filter ($K=2$):** Requires 2 consecutive anomalous windows to prevent route flapping from transient fading.
- **Endpoint Protection Guard:** Flow sources and destinations are immune from isolation.
- **Route Invalidation (`invalidate_routes_through`):** Purges next_hop entries pointing to attacker; triggers fresh RREQ broadcasts.
- **Quarantine Cooling Table:** 30.0-second temporary isolation before provisional rehabilitation.

### Speaker Notes
> *"Slide 9 shows our closed-loop architecture. When the classifier detects an anomaly, it logs Strike 1. If confirmed in the next window, Strike 2 triggers quarantine. The controller immediately purges all routes pointing through the attacker, allowing honest nodes to broadcast a fresh RREQ and discover legitimate alternate paths."*

---

## Slide 10: Comparative Triad QoS Results (PDR Recovery)

### Visual Layout
- Figure embed: `results/plots/qos_recovery_triad_dashboard.png` and `qos_pdr_recovery.png`.
- Summary table comparing Baseline vs Attack vs AODV+IDS.

### Bullet Points
- **36-Run Triad Benchmark:** Evaluated across Seeds 42, 43, 44 under identical random trajectories.
- **Blackhole PDR Recovery (30 Nodes):**
  - Baseline AODV: **$63.66\%$**
  - Attack AODV: **$14.18\%$**
  - AODV + IDS: **$61.01\%$**
  - **Recovery Ratio: $92.9\%$** (Absolute $\Delta\text{PDR} = +46.83\%$).
- **Grayhole PDR Recovery ($p=0.5$):** Delivery recovered from $56.34\%$ to **$69.35\%$** ($118.6\%$ recovery ratio).

### Speaker Notes
> *"This is our core result. Across 36 controlled runs under identical seeds, an unmitigated Blackhole attack destroys PDR down to 14.18%. With our closed-loop IDS enabled, delivery recovers to 61.01%—restoring 92.9% of the baseline network delivery ratio."*

---

## Slide 11: Routing Overhead & Latency Trade-offs

### Visual Layout
- Figure embed: `results/plots/qos_routing_overhead_penalty.png` and `qos_delay_impact.png`.

### Bullet Points
- **The Overhead Question:** Does route rediscovery flood the network with excessive control packets?
- **Measured Routing Overhead Cost:**
  - Baseline Overhead: $0.0552$ control packets per data packet.
  - AODV + IDS Overhead: $0.0859$.
  - **Net Overhead Penalty: $+0.0307$** (strictly bounded).
- **End-to-End Latency:** Virtually unchanged ($5.13\text{ ms}$ baseline vs. $5.19\text{ ms}$ under IDS).
- **Conclusion:** Security recovery is achieved without network congestion or latency degradation.

### Speaker Notes
> *"Examiners often ask if route invalidation creates excessive overhead. We measured this directly: routing overhead increases by only +0.0307 control packets per data packet, while average packet latency remains virtually flat at 5.19 milliseconds. Mitigation is lightweight and scalable."*

---

## Slide 12: Architectural Lessons & Engineering Governance

### Visual Layout
- Icons representing Python ecosystem, test suite badge (59/59 passing), and provenance audit trail.

### Bullet Points
- **Engineering Discipline (AGENTS.md Contract):**
  - Zero NS-3 / C++ dependencies; 100% native Windows execution.
  - Deterministic random seeding ensures every run is bitwise reproducible.
  - 59 automated unit and integration tests passing in $<2\text{ seconds}$.
- **Data Traceability:** Every figure and table traces back to versioned scenario JSONs and empirical CSV files.

### Speaker Notes
> *"Throughout development, we maintained strict engineering discipline. Every claim in our report traces to saved CSV records and scenario configurations. We established 59 automated unit and integration tests covering the simulator, attacks, features, and closed-loop isolation."*

---

## Slide 13: Technical Limitations & Future Work

### Visual Layout
- Roadmap graphic indicating Current Capstone vs. Future Post-Graduate Research.

### Bullet Points
- **Current Limitations:**
  - 2D flat Euclidean propagation (abstracts 3D terrain elevation and multipath fading).
  - Single-attacker injection per scenario.
  - Simplified 802.11 MAC contention modeling to preserve sub-second simulation speeds.
- **Future Directions:**
  - Cross-layer integration with MAC-layer retry counters and RSSI signal metrics.
  - Multi-attacker collusive Wormhole detection.
  - Distributed reputation consensus voting among 1-hop neighbors.

### Speaker Notes
> *"While our system fully satisfies our project requirements, we acknowledge key limitations. Our physical model abstracts 3D terrain and MAC-layer contention. In future work, we plan to incorporate cross-layer MAC retry metrics to help disambiguate high-speed mobility breaks from packet dropping attacks."*

---

## Slide 14: Conclusion & Q&A

### Visual Layout
- Executive summary badge: 92.9% PDR Recovery | 0.99% FPR | 59/59 Tests Passing | 100% Windows Native.
- Repository link & "Thank you for your time and guidance."

### Bullet Points
- **Demonstrated:** Fully working end-to-end MANET ML intrusion detection and active routing recovery chain.
- **Verified:** $92.9\%$ PDR recovery on Blackhole attacks with bounded overhead ($+0.0307$).
- **Reproducible:** Complete codebase, interactive Archify diagrams, and live demo commands ready for evaluation.
- **Open for Questions.**

### Speaker Notes
> *"In conclusion, we have designed, implemented, and proven a complete, reproducible Intrusion Detection and Response system for Mobile Ad-Hoc Networks. Thank you to our mentors and the committee for your time. We are now open for questions and ready to demonstrate the live system."*

---
*End of Presentation Deck Outline. Adapt slide themes to departmental templates.*
