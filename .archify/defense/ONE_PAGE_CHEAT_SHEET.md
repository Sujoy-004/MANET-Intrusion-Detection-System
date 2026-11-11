# Rapid-Fire Viva Defense Cheat Sheet

**Project:** Machine Learning-Based Intrusion Detection and Response System for MANET  
**Format:** High-Density Exam Desk Quick Reference Sheet

---

## 1. Core Empirical Results & QoS Recovery Triad

| Scenario | Attack Type | Baseline PDR | Attack PDR | AODV+IDS PDR | Absolute $\Delta$PDR | Recovery Ratio | Overhead Penalty |
|---|---|---|---|---|---|---|---|
| `30n_blackhole` | Blackhole ($p=1.0$) | **$0.6366$** ($63.7\%$) | **$0.1418$** ($14.2\%$) | **$0.6101$** ($61.0\%$) | **$+0.4683$** ($+46.8\%$) | **$92.9\%$** | **$+0.0307$** |
| `30n_grayhole_p50` | Grayhole ($p=0.5$) | **$0.6366$** ($63.7\%$) | **$0.5634$** ($56.3\%$) | **$0.6935$** ($69.4\%$) | **$+0.1301$** ($+13.0\%$) | **$118.6\%$** | **$+0.0098$** |
| `30n_grayhole_p70` | Grayhole ($p=0.7$) | **$0.6366$** ($63.7\%$) | **$0.5654$** ($56.5\%$) | **$0.6225$** ($62.3\%$) | **$+0.0572$** ($+5.7\%$) | **$68.0\%$** | **$+0.0003$** |
| `50n_grayhole_p50` | Grayhole ($p=0.5$) | **$0.7333$** ($73.3\%$) | **$0.5256$** ($52.6\%$) | **$0.5969$** ($59.7\%$) | **$+0.0713$** ($+7.1\%$) | **$40.0\%$** | **$+0.0114$** |

*Key Takeaway:* In Blackhole attacks, the active IDS restores **$92.9\%$** of lost baseline delivery with an overhead penalty of only **$+0.0307$** routing packets per data packet.

---

## 2. Machine Learning Classifier Benchmark (Seed 44 Test Holdout)

| Model | Accuracy | Precision | Recall | F1-Score | False Positive Rate (FPR) | Operational Gate ($\text{FPR} \le 1.0\%$) |
|---|---|---|---|---|---|---|
| **Random Forest (Champion)** | **$97.44\%$** | **$0.4212$** | **$0.3075$** | **$0.7593$** | **$0.0099$ ($0.99\%$)** | **PASSED (Champion)** |
| Decision Tree (Baseline) | $95.01\%$ | $0.1628$ | $0.2825$ | $0.6766$ | $0.0342$ ($3.42\%$) | FAILED (FPR too high) |
| Support Vector Machine (Baseline) | $54.68\%$ | $0.0482$ | $0.9975$ | $0.5552$ | $0.4638$ ($46.38\%$) | FAILED (Severe false alarms) |

*Key Takeaway:* Random Forest was the **only classifier** to pass the security operational gate ($\text{FPR} \le 1.0\%$). SVM had $99.75\%$ recall but destroyed the network by disconnecting $46.4\%$ of honest nodes.

---

## 3. Feature Importance Ranking (Permutation vs. Gini)

| Feature Name | Permutation Importance | Gini Impurity | Role in Detection |
|---|---|---|---|
| **`packet_drop_ratio`** | **$0.2156$** | $0.1035$ | **#1 Predictor:** Directly measures discarded transit data packets |
| **`hop_count`** | **$0.1685$** | $0.0595$ | **#2 Predictor:** Identifies spoofed 1-hop distance claims in RREPs |
| **`packet_forward_ratio`**| **$0.0147$** | $0.0749$ | **#3 Predictor:** Verifies whether received transit traffic was forwarded |
| `route_reply_rate` | $0.0105$ | $0.0137$ | Detects aggressive unsolicited RREP reply floods |
| `neighbor_count` | $0.0044$ | $0.1705$ | Evaluates local node connectivity degree |
| `mobility_speed` | $0.0006$ | $0.5461$ | Gini artifact! Permutation shows speed has near-zero predictive power |

---

## 4. Key System Hyperparameters & Architecture

- **Discrete-Event Simulator:** SimPy 4.1.2 + NetworkX 3.6.1 (Pure Python, Windows native, zero C++ compilers).
- **Simulation Speed:** 50 nodes, 8 CBR flows, 300 seconds simulated time $\to$ **$0.83$ seconds wall-clock time** (~70k events/sec).
- **Radio Transmission Range:** $R = 250\text{ meters}$ (Euclidean 2D disc propagation model).
- **Node Velocity:** $v \in [1.0, 10.0]\text{ m/s}$ (Random Waypoint mobility, pause $t_p = 5.0\text{s}$).
- **CBR Traffic Load:** 8 multi-hop flows, $10\text{ packets/sec}$, $512\text{ bytes}$ payload.
- **Sliding Observation Window:** $W = 5.0\text{ seconds}$ (non-overlapping backward aggregation).
- **Confirmation Filter:** $K = 2\text{ consecutive windows}$ with $P(\text{malicious}) \ge \tau = 0.50$.
- **Quarantine Policy:** $30.0\text{ seconds}$ temporary cooling decay before provisional rehabilitation.
- **Route Invalidation:** `invalidate_routes_through()` purges corrupted next_hop entries and triggers fresh RREQ.
- **Endpoint Protection:** Flow source and destination nodes are immune from isolation.

---

## 5. Non-Negotiables & Methodological Integrity Rules

1. **Zero Data Leakage:** Features are computed strictly from local event logs; ground-truth labels are joined externally from scenario schedules.
2. **Zero Random Row Splitting:** Dataset split strictly by seed: Train on Seeds 42 & 43 ($34,800$ rows); Test on Seed 44 ($17,400$ rows).
3. **Never Report Accuracy Alone:** Imbalanced dataset ($2.3\%$ attacks); a dummy model achieves $97.7\%$ accuracy with $0\%$ recall.
4. **Always Baseline Against Plain AODV:** All QoS claims compare Baseline vs Attack vs AODV+IDS under identical seeds.
5. **Full Traceability:** Every number traces to `results/closed_loop_metrics.csv` and versioned scenario configs.

---

## 6. 30-Second Elevator Pitch

> *"We developed a 100% Windows-native, pure-Python intrusion detection and response system for MANET that solves the classic Blackhole and Grayhole routing attacks. Using SimPy, we simulate 50 mobile nodes in under 1 second. We engineered 9 non-leaking traffic features over 5-second sliding windows and trained a Random Forest model that passes our strict 1% false positive gate. Most importantly, we implemented closed-loop mitigation: upon a 2-strike confirmation, the system invalidates corrupted routes, enabling honest AODV nodes to discover alternate paths and restoring packet delivery ratio from 14.2% back to 61.0%—a 92.9% recovery ratio—with a negligible routing overhead penalty of only +0.0307."*
