# Comprehensive Academic Viva Defense Guide: MANET ML-IDS

**Project:** Machine Learning-Based Intrusion Detection and Response System for Mobile Ad-Hoc Networks  
**Target Examination:** B.Tech Major Project Viva Voce & Technical Defense  
**Audience:** Internal Examiners, External Evaluators, Technical Project Committee  
**Confidentiality:** Academic Preparation (Uncommitted Personal Suite)

---

## 1. Executive Defense Strategy & Framing

When presenting this project to the examination panel, maintain three core technical themes:
1. **Engineering Pragmatism over Theoretical Complexity:** We chose pure Python (SimPy + NetworkX) over NS-3 because NS-3's C++ toolchain is brittle on native Windows, whereas our in-repo simulator executes a 300-second 50-node simulation in **0.83 seconds wall-clock time**, enabling 36-run multi-seed triad benchmarking that would take hours in NS-3.
2. **Methodological Rigor over Flattering Numbers:** We strictly prevented data leakage. We never used random row splits—our models were evaluated on an untouched simulation seed (Seed 44). We enforced a non-negotiable **False Positive Rate gate ($\text{FPR} \le 1.0\%$)**, refusing models that boast high recall at the cost of network fragmentation.
3. **Closed-Loop Demonstration over Passive Prediction:** Detecting an attacker is useless if the routing protocol cannot recover. We demonstrated that active route table invalidation (`invalidate_routes_through`) recovers **$92.9\%$ of lost baseline PDR** on Blackhole attacks with an overhead cost penalty of only **$+0.0307$** control packets per data packet.

---

## 2. Guide Viva Questions & Technical Model Answers

The following 12 questions are drawn directly from §12 of `MANET_IDS_BTech_Execution_Guide.md`.

---

### Question 1: Why is MANET more vulnerable than a conventional infrastructure-based network?

**Model Answer:**
"Conventional infrastructure networks possess a defined physical and logical perimeter. Gateways, switches, and edge firewalls separate internal trusted hosts from untrusted external networks. In a MANET, **no fixed perimeter or centralized authority exists**. Every node is simultaneously a terminal host and a routing switch. 

This introduces three structural vulnerabilities:
1. **Shared Wireless Broadcast Medium:** RF transmissions can be eavesdropped on, injected into, or jammed by any transceiver within physical radio range ($R=250\text{m}$) without physical tampering.
2. **Cooperative Routing Dependency:** Reactive routing protocols like AODV rely on implicit mutual trust. Intermediate nodes are assumed to forward control messages and data packets faithfully. A single insider can violate this assumption to hijack or drop traffic.
3. **Dynamic Topology & Volatility:** Node mobility causes legitimate link breaks that mimic malicious packet dropping, making anomaly disambiguation exceptionally difficult."

---

### Question 2: Why did you choose AODV over other routing protocols like DSR or OLSR?

**Model Answer:**
"We selected AODV (RFC 3561) over DSR and OLSR based on scalability, overhead, and attack surface:
- **AODV vs. OLSR (Proactive):** OLSR continuously broadcasts periodic link-state messages across the network to maintain routing tables for all destinations. In bandwidth-constrained and mobile MANETs, this consumes substantial RF capacity and battery power ($O(N^2)$ control message scaling). AODV is reactive (on-demand), creating routes only when application traffic is actively queued.
- **AODV vs. DSR (Dynamic Source Routing):** DSR embeds the complete hop-by-hop route in every packet header. For 5-to-10 hop paths, this introduces significant packet header overhead, reducing effective data payload efficiency. AODV maintains decentralized routing tables where each node stores only the next hop and destination sequence number.
- **The Research Relevance:** AODV's core mechanism for route freshness and loop prevention is the **Destination Sequence Number**. Because this protocol rule is deterministic, it provides a precise, standardized attack surface for the Blackhole exploit ($SeqNum = 2^{32}-1$), allowing us to rigorously measure both the attack's impact and the IDS's remediation."

---

### Question 3: What exactly is an 'intrusion' in your project?

**Model Answer:**
"In our system, an intrusion is defined as an intentional, unauthorized deviation from RFC 3561 AODV protocol rules or honest multi-hop forwarding behavior that undermines network availability or data integrity:
1. **Control-Plane Intrusion:** Fabricating routing control messages, specifically generating an unsolicited Route Reply (RREP) with a spoofed destination sequence number ($2^{32}-1$) and a false 1-hop distance to intercept traffic.
2. **Data-Plane Intrusion:** Intentionally dropping forwarded transit data packets—either completely ($100\%$ in Blackhole) or probabilistically ($30\%–70\%$ in Grayhole)—after successfully winning route election through the control plane.
Crucially, our IDS distinguishes between natural wireless link breaks (where an honest node transmits an RERR upon neighbor departure) and malicious dropping (where a node remains within radio range but silently discards transit packets)."

---

### Question 4: How does a Blackhole attack exploit AODV sequence number mechanics?

**Model Answer:**
"RFC 3561 section 6.2 mandates that when a node receives competing route advertisements for destination $d$, it updates its routing table according to the freshness predicate:
$$\text{UpdateRoute}(d) \iff \left( Seq_d^{\text{new}} > Seq_d^{\text{current}} \right) \lor \left( Seq_d^{\text{new}} = Seq_d^{\text{current}} \land Hop^{\text{new}} < Hop^{\text{current}} \right)$$

When an honest source broadcasts an RREQ, the Blackhole node immediately intercepts it and unicasts a forged RREP back to the source advertising:
$$Seq_d^{\text{spoofed}} = 2^{32}-1 = 4,294,967,295, \quad Hop^{\text{spoofed}} = 1$$
Because $2^{32}-1$ is the theoretical maximum 32-bit unsigned integer, it strictly exceeds any legitimate sequence number maintained by the destination. The source node and all intermediate nodes unconditionally accept the attacker's route, evicting honest multi-hop paths. Once data packets arrive, the Blackhole node silently discards them:
$$P(\text{drop} \mid \text{data packet}) = 1.0$$
In our 30-node simulations, this single attack collapsed the Packet Delivery Ratio from $63.66\%$ down to $14.18\%$."

---

### Question 5: How did you generate ground-truth labels without introducing data leakage?

**Model Answer:**
"This was a non-negotiable architectural requirement (AGENTS.md Rule 5). 

Many flawed studies append an `is_attacker` column directly into packet traces, or have the simulator log the node label. If that column or any simulator-internal state is ingested by the feature extractor, the model cheats.

In our architecture:
1. The packet trace logger (`simulator/aodv.py`) logs **only raw physical events**: `time, node_id, event_type, pkt_id, pkt_type, src, dst, next_hop, hop_count, dropped_by, reason`.
2. The feature extractor calculates the 9 traffic features purely by aggregating these observed event rows over backward-looking $5.0$-second windows.
3. The ground-truth label (`Normal`, `Blackhole`, `Grayhole`) is assigned **externally** during dataset compilation by joining the feature window timestamps against the scenario configuration's declared attack schedule:
   $$\text{Label}(u, T_m) = \begin{cases} \text{AttackType}, & \text{if } u = \text{AttackerID} \land T_m \ge T_{\text{attack\_start}} \\ \text{Normal}, & \text{otherwise} \end{cases}$$
The model and the feature calculation logic never see the scenario configuration, guaranteeing zero label leakage."

---

### Question 6: Why are accuracy and F1-score both required? Why can't we report accuracy alone?

**Model Answer:**
"Reporting accuracy alone in network intrusion detection is a well-known methodological fallacy known as the **Accuracy Paradox**.

In our 300-second, 30-to-50 node simulations, malicious node-windows account for only $\approx 2.3\%$ of total observations ($400$ malicious windows vs. $17,000$ normal windows in the test set). 

If a naive, degenerate classifier simply predicts 'Normal' for every single observation:
$$\text{Accuracy} = \frac{17,000}{17,400} = 97.70\%$$
A researcher looking only at accuracy would conclude that the model is $97.7\%$ effective. However, its Recall is **$0.0\%$**, its Precision is **$0.0\%$**, and it misses every single attack, allowing the network to be completely destroyed.

Therefore, we must report:
- **Precision:** $\frac{TP}{TP + FP}$ — ensures flagged nodes are actually malicious.
- **Recall:** $\frac{TP}{TP + FN}$ — ensures actual attackers are caught.
- **F1-Score:** The harmonic mean of precision and recall ($2 \cdot \frac{P \cdot R}{P + R} = 75.93\%$ for our Random Forest champion).
- **False Positive Rate (FPR):** $\frac{FP}{FP + TN}$ — strictly capped at $\le 1.0\%$ ($0.99\%$ achieved) to prevent disconnecting honest nodes."

---

### Question 7: How did you prevent data leakage during train/test splitting?

**Model Answer:**
"We enforced three strict anti-leakage barriers:
1. **Seed-Based Partitioning (AGENTS.md Rule 4):** We never performed random row splitting. Consecutive time windows in a discrete-event simulation are temporally correlated (sharing identical node coordinates, channel fading states, and traffic queues). Splitting randomly allows a model to memorize node trajectories. We trained exclusively on **Seeds 42 and 43** ($34,800$ samples) and evaluated on an entirely untouched **Seed 44** ($17,400$ samples).
2. **Backward-Looking Sliding Windows:** Feature windows of duration $W=5.0\text{s}$ compute metrics strictly over the interval $[T_m - W, T_m)$. No packet event occurring at or after $T_m$ is ever accessed.
3. **Safe Default Imputation:** When a node experiences zero transit packets during a window, we apply mathematically neutral defaults ($PFR = 1.0, PDR_{\text{drop}} = 0.0, \text{Delay} = 0.0$) rather than global dataset means, preventing information leakage across time windows."

---

### Question 8: Why did you choose Random Forest over Deep Learning (LSTM, GNN)?

**Model Answer:**
"We evaluated the computational constraints of MANET nodes and the mathematical structure of our telemetry:
1. **Tabular vs. Sequential Telemetry:** Our feature pipeline aggregates packet events into 9 discrete tabular behavioral features per $5$-second window. Tree-based ensembles (Random Forest, XGBoost) consistently outperform deep architectures on tabular data with structured physical indicators.
2. **CPU Inference Latency:** MANET nodes are typically embedded devices or tactical radios without dedicated GPUs. Random Forest executes inference in **sub-microsecond CPU time** ($<1\mu\text{s}$ per feature vector), enabling real-time inline evaluation without delaying packet forwarding. An LSTM or Transformer would introduce tens of milliseconds of inference latency, stalling routing buffers.
3. **Sample Efficiency:** Deep learning models require hundreds of thousands of parameter instances to converge. Our 34,800-sample training set trained Random Forest to convergence in under 3 seconds.
4. **Interpretability:** Permutation importance directly verified that our model relies on `packet_drop_ratio` ($0.2156$) and `hop_count` ($0.1685$), ensuring the defense is explainable to network administrators."

---

### Question 9: How does node mobility affect IDS detection accuracy?

**Model Answer:**
"As demonstrated in our Environmental Stress Matrix (Table 5.3 and Figure 5.11):
- At low to moderate speeds ($1.0\text{ m/s}$ walking speed, $5.0\text{ m/s}$ running/cycling), the model maintains high F1-scores ($90\%–96\%$) and false positive rates remain near zero ($0.0\%–0.8\%$).
- At high mobility ($10.0\text{ m/s} = 36\text{ km/h}$ vehicular speed), performance degrades significantly: Recall drops to $0.0\%$ in 30-node networks and FPR rises to $9.0\%$.

**The Physical Cause:**
At $10\text{ m/s}$ with a $250\text{m}$ transmission range, wireless links break frequently. When a node's next-hop neighbor moves out of radio range, buffered data packets are dropped by honest intermediate nodes before route error (RERR) messages can propagate. These mobility-induced packet drops elevate `packet_drop_ratio` on honest nodes, causing them to exhibit Grayhole-like drop patterns. This empirical finding highlights that single-layer behavioral IDS reaches a physical limit in highly mobile networks unless paired with cross-layer physical link-quality metrics."

---

### Question 10: What happens after a node is quarantined? How does the network recover?

**Model Answer:**
"The isolation triggers an active, 4-step route re-convergence:
1. **Quarantine Registration:** The node ID is added to the active blacklist with a 30-second cooling timestamp: `quarantine_table[u] = sim_time + 30.0`.
2. **Dynamic Route Invalidation:** The controller executes `invalidate_routes_through(u)` across all nodes. Any route table entry where $\text{next\_hop} = u$ is immediately purged, and an RFC 3561 RERR message is generated.
3. **Legitimate Route Rediscovery:** When source nodes have queued data packets for affected destinations, the missing route triggers a fresh RREQ broadcast flood.
4. **Blacklist Enforcement:** When the quarantined node attempts to respond with an RREP, honest neighbors invoke `is_blacklisted(sender)` and silently drop its reply. Honest nodes discover alternate multi-hop paths around the adversary, restoring delivery to **$61.01\%$**."

---

### Question 11: What is the routing overhead penalty of your IDS response?

**Model Answer:**
"Examiners often suspect that active route invalidation will cause catastrophic broadcast storms. We measured this quantitatively.

Routing overhead is defined as:
$$\text{Overhead} = \frac{\text{Total Control Packets (RREQ + RREP + RERR)}}{\text{Total Successfully Delivered Data Packets}}$$

In our 30-node Blackhole evaluations:
- Baseline AODV overhead: **$0.0552$**
- AODV + IDS overhead: **$0.0859$**
- **Overhead Penalty: $+0.0307$ control packets per delivered data packet.**

Because our route invalidation is targeted (purging only routes using the attacker as next-hop) and temporary ($30.0\text{s}$ cooling decay), the rediscovery RREQ burst lasts only $1–2$ seconds. Once alternate paths are cached, overhead returns to baseline levels. This negligible $+0.0307$ cost proves that active mitigation is highly viable in bandwidth-constrained networks."

---

### Question 12: How does your model behave when exposed to an unseen attack?

**Model Answer:**
"We tested this explicitly in Phase 4 when evaluating Grayhole attacks using a model trained strictly on Blackhole and Normal data:
1. **Zero-Shot Transfer (Untrained on Grayhole):** The Blackhole-only model achieved a Grayhole Recall of only **$28.0\%$** on intermittent Grayhole dropping ($p=0.5$). The model expected severe drop ratios ($PDR_{\text{drop}} \approx 1.0$) and high sequence numbers. When the Grayhole dropped only $50\%$ of packets and forwarded control traffic honestly, the Blackhole model missed over $70\%$ of attack windows.
2. **Multi-Attack Retraining:** When retrained on a balanced dataset including both Blackhole and Grayhole examples, the Random Forest model achieved **$86.7\%$ recall on Grayhole $p=0.5$** and an overall F1-score of **$75.93\%$**.
This proves that signature-only models fail against selective attackers, whereas our multi-feature sliding window successfully captures intermittent dropping once calibrated."

---

## 3. Project-Specific Architectural Inquiries

### Why did you abandon NS-3 in favor of an in-repo pure-Python simulator?
"NS-3 is an outstanding academic tool, but it assumes a Linux/C++ toolchain. On native Windows, building NS-3 requires WSL or virtual machines, introducing non-native compilation overhead, 20-minute build cycles, and complex C++ debugging. Furthermore, PyPI contains zero Windows-native AODV packages (`pymansim`, `manet`, and `aodv` are absent). `ns.py` is a wired IP-flow simulator with no wireless, mobility, or AODV layer. 

By building our discrete-event simulator using **SimPy 4.1.2** and **NetworkX 3.6.1**, we achieved:
- Complete Windows-native execution (zero C++ compilers).
- Strict determinism (explicit integer seeds drive mobility, traffic jitter, and drops).
- High execution performance: a 300-second 50-node simulation runs in **0.83 seconds wall-clock time**, enabling 36-run comparative triad benchmarks in minutes."

### Why did you implement a 2-strike confirmation filter instead of instant quarantine?
"In wireless ad-hoc networks, packet drops occur naturally due to mobility-induced link breaks and temporary buffer overflows. If the IDS quarantined a node on a single $5.0$-second anomalous window ($K=1$), transient wireless drops would cause honest nodes to be isolated. This causes 'route flapping,' where routes are repeatedly broken and rediscovered. Requiring $K=2$ consecutive detection windows ($10.0$ seconds of confirmed dropping) eliminates transient noise and prevents false isolations while remaining fast enough to isolate Blackholes before severe data loss occurs."

### Why are flow endpoints protected from quarantine?
"In multi-hop routing, source nodes generate traffic and destination nodes absorb traffic. A destination node receives packets but forwards zero packets ($PFR = 0.0$), mathematically mimicking a Blackhole sink. If our IDS evaluated destination nodes without context, it would isolate the very recipient of the communication flow. By asserting `node_id not in active_sources and node_id not in active_destinations`, we ensure that only transit forwarding nodes are evaluated for route exclusion, preserving end-to-end communication."

---
*End of Viva Defense Guide. Review thoroughly prior to technical committee examination.*
