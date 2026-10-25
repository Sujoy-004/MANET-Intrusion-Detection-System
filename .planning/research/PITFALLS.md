# Pitfalls Research

**Domain:** MANET Simulation, Feature Engineering & Machine Learning Intrusion Detection  
**Researched:** 2026-10-23  
**Confidence:** HIGH  

## Critical Pitfalls

### Pitfall 1: Random Row Splitting on Correlated Trace Data

**What goes wrong:**
Using standard `train_test_split(shuffle=True)` on tabular feature rows. The test accuracy appears virtually perfect (e.g. 99.8%), but when tested on a completely new simulation run with a different random seed or node topology, detection performance collapses to random guessing.

**Why it happens:**
Packet trace features computed over sliding windows from the same node across time step $t$ and $t+1$ are heavily autocorrelated. Random row splitting places window $t$ in the training set and window $t+1$ in the test set, creating massive temporal data leakage.

**How to avoid:**
Partition the dataset strictly by **Scenario / Seed / Configuration**. Entire simulation runs (e.g., Seeds 1-10) are used for training, while completely distinct simulation runs (Seeds 11-15) are held out for testing.

**Warning signs:**
Near 100% test accuracy on row-split data, but failure to detect attacks on a freshly run simulation scenario.

**Phase to address:**
Phase 2 (Dataset generation and ML evaluation).

---

### Pitfall 2: Ground-Truth Feature Leakage

**What goes wrong:**
Including columns in the feature dataset that directly or indirectly reveal the attacker identity or attack presence without simulating observable network behavior (e.g., `is_attacker`, `attacker_node_id`, `attack_type`, or scenario-level metadata).

**Why it happens:**
Convenience during dataset creation where scenario configuration dictionaries are directly merged into trace event logs.

**How to avoid:**
Strict schema enforcement. The feature extractor must only observe traffic traces (forwarded packets, dropped packets, packet timestamps, hop counts, routing control message rates, neighbor count). The ground truth label (`label: 0 or 1`) is appended strictly as the target variable $y$, never included in the feature matrix $X$.

**Warning signs:**
Feature importance analysis shows one non-traffic or ID feature with near 1.0 importance; model performs unrealistically well.

**Phase to address:**
Phase 1 and Phase 2 (Feature extraction and dataset building).

---

### Pitfall 3: Reporting Accuracy Alone on Imbalanced Security Data

**What goes wrong:**
In a MANET with 50 nodes and 1 attacker, benign traffic represents 95-98% of all observations. A naive or broken classifier that simply predicts "Normal" for every single node achieves 98% accuracy while failing to detect the intruder.

**Why it happens:**
Reliance on `accuracy_score` without examining precision, recall, and false positive rates.

**How to avoid:**
Always report precision, recall, F1-score, False Positive Rate (FPR), and the full confusion matrix. Prioritize F1-score and recall for the malicious class.

**Warning signs:**
High overall accuracy (e.g. 96%) but minority class recall near 0%.

**Phase to address:**
Phase 2 (ML evaluation).

---

### Pitfall 4: Attack Has No Measurable Network Impact

**What goes wrong:**
An attack is implemented in code, but the simulated network's Packet Delivery Ratio (PDR) and throughput remain unchanged compared to the normal baseline run. Training an IDS on this data results in learning noise because the attack did not alter network physics.

**Why it happens:**
The attacker node is not placed on the active communication route between source and destination flows, or the attacker's fake RREP is ignored because standard AODV sequence number checks discard it.

**How to avoid:**
Validate the attack impact before training any ML model. Compare baseline PDR vs attack PDR on the exact same seed. A successful Blackhole attack must cause a distinct, measurable drop in PDR (e.g., from 85% down to 20-40%).

**Warning signs:**
Baseline PDR and Attack PDR are identical; malicious node forwarding counters remain zero.

**Phase to address:**
Phase 1 (Normal AODV & Blackhole validation gate).

---

### Pitfall 5: Non-Deterministic Simulation Runs

**What goes wrong:**
Running the exact same simulation script twice produces different packet delivery counts, differing traces, and irreproducible results.

**Why it happens:**
Missing explicit random seeds, relying on system time for RNG initialization, or non-deterministic iteration order over Python sets or dictionary keys.

**How to avoid:**
Pass an explicit integer seed (`--seed 42`) to every component: `random.seed(seed)`, `np.random.seed(seed)`, SimPy environment creation, and sort dictionary/set keys before iteration.

**Warning signs:**
Rerunning the same scenario JSON outputs different hash checksums on the trace CSV.

**Phase to address:**
Phase 0 & Phase 1.

---

### Pitfall 6: Claiming IDS Success Without Baseline Comparison

**What goes wrong:**
A report or presentation claims the ML IDS "effectively secures the MANET" but only presents classification metrics (e.g. F1 = 0.94) without measuring whether network delivery actually improved.

**Why it happens:**
Stopping at Module D (offline ML) without implementing Module E (closed-loop response and QoS re-evaluation).

**How to avoid:**
Always provide the QoS comparison matrix:
1. Normal AODV (clean baseline)
2. AODV under Attack (unprotected)
3. AODV + IDS (mitigated)
Showing PDR, throughput, delay, and packet loss across all three modes.

**Warning signs:**
Project has ML graphs but zero network performance plots or comparative tables.

**Phase to address:**
Phase 4 (IDS Response & QoS Comparison).

## "Looks Done But Isn't" Checklist

- [ ] **AODV Simulator:** Often missing route expiration / timeout — verify routes drop when nodes move out of range.
- [ ] **Blackhole Attack:** Often fails to attract traffic — verify the attacker's fake RREP actually updates the source's routing table.
- [ ] **Feature Extraction:** Often leaks future time steps in sliding window — verify windows only aggregate backward in time ($t - W \le t_{event} \le t$).
- [ ] **Train/Test Split:** Often shuffles rows across runs — verify test set contains exclusively unseen scenario seeds.
- [ ] **Mitigation:** Often blacklists benign nodes on false positives — verify network PDR doesn't degrade when IDS is active on normal traffic.

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification Method |
|---------|------------------|---------------------|
| Non-deterministic runs | Phase 0 | Hash comparison of trace files across identical seed runs |
| Attack without network impact | Phase 1 | PDR drop verification: Baseline PDR vs Attack PDR |
| Ground-truth label leakage | Phase 1 & 2 | Feature correlation audit; verify no attacker IDs in $X$ |
| Random row split inflation | Phase 2 | Hold out scenario seeds; test generalization on unseen runs |
| Accuracy-only reporting | Phase 2 | Confusion matrix, Precision, Recall, F1 for malicious class |
| Passive detection without mitigation | Phase 4 | Closed-loop re-run showing PDR recovery vs unprotected AODV |

---
*Pitfalls research for: MANET Intrusion Detection System*  
*Researched: 2026-10-23*  
