# 3-Act Live Demonstration Script: MANET ML-IDS

**Target Audience:** Viva Examination Committee & Technical Demonstrators  
**Estimated Duration:** 7–10 Minutes  
**Demonstration Mode:** Live PowerShell Terminal Execution  
**Pre-requisites:** Working directory set to project root; CPython 3.11 environment active.

---

## Demonstration Setup & Checklist

Open a standard Windows PowerShell window at the project root:
```powershell
cd "C:\Users\KIIT0001\Documents\projects\Machine Learning-Based Intrusion Detection System for MANET"
```
Verify the Python environment and test suite in 5 seconds:
```powershell
python -m pytest tests/ -q
```
*Expected Output:* `59 passed in ~1.5s`.

---

## Act 1: Baseline Normal AODV Routing

### Objective
Demonstrate honest, cooperative multi-hop AODV routing operating under normal mobile conditions without attacks.

### Speaker Script
> *"Good morning, respected members of the committee. To evaluate our Intrusion Detection and Response system, we first establish baseline network behavior. I am executing our pure-Python discrete-event simulator running a 30-node network with 8 concurrent CBR traffic flows over 300 simulated seconds using Seed 42."*

### Command
```powershell
python simulator/run_scenario.py --scenario scenarios/e1_baseline_30n.json --seed 42 --out traces/demo_baseline.csv
```

### Expected Output
```text
Loaded scenario: e1_baseline_30n (30 nodes, duration: 300.0s)
Simulation finished in 0.42s wall-clock time.
[METRICS] Packet Delivery Ratio (PDR): 0.6366 (63.66%)
[METRICS] Throughput:                 44.33 kbps
[METRICS] Average End-to-End Delay:   5.13 ms
[METRICS] Routing Overhead Ratio:     0.0552
Trace written to: traces/demo_baseline.csv
```

### Explanatory Commentary
> *"Notice the simulation completed in under half a second. Across the 30-node network, honest nodes discover multi-hop paths via standard RREQ/RREP exchanges, achieving a **63.66% Packet Delivery Ratio** and a low routing overhead of **0.0552**. The remaining ~36% loss is natural packet dropping caused by dynamic node mobility breaks as nodes move between 1 and 5 meters per second."*

---

## Act 2: Malicious Attack Injection (Blackhole Route Hijacking)

### Objective
Demonstrate the catastrophic destruction of network delivery when a Blackhole node exploits RFC 3561 sequence numbers.

### Speaker Script
> *"Now, we inject an unmitigated Blackhole attack using Node 21. At simulation time t=50s, Node 21 begins intercepting all RREQ broadcasts and transmitting spoofed RREPs advertising sequence number 2^32-1 and a hop count of 1. Watch the delivery metrics collapse."*

### Command
```powershell
python simulator/run_scenario.py --scenario scenarios/e2_blackhole_onset_30n.json --seed 42 --out traces/demo_attack.csv
```

### Expected Output
```text
Loaded scenario: e2_blackhole_onset_30n (30 nodes, duration: 300.0s)
[ATTACK] Node 21 configured as BlackholeStrategy (start_time=50.0s, drop_prob=1.0)
Simulation finished in 0.45s wall-clock time.
[METRICS] Packet Delivery Ratio (PDR): 0.1418 (14.18%)
[METRICS] Throughput:                 9.88 kbps
[METRICS] Average End-to-End Delay:   6.69 ms
[METRICS] Routing Overhead Ratio:     0.0873
Trace written to: traces/demo_attack.csv
```

### Explanatory Commentary
> *"As seen on screen, PDR collapsed catastrophically from **63.66% down to 14.18%**—an 82.7% reduction in network throughput. Because RFC 3561 trusts the sequence number unconditionally, honest nodes routed their data packets directly into Node 21, where every packet was silently dropped. Standard AODV has zero native ability to detect or recover from this attack."*

---

## Act 3: Closed-Loop Detection, Quarantine & QoS Recovery

### Objective
Demonstrate the complete closed-loop chain: real-time sliding-window feature aggregation, Random Forest inference, 2-strike confirmation, dynamic route table invalidation, and PDR recovery.

### Speaker Script
> *"Now, we activate our machine learning intrusion detection and dynamic response engine by passing the `--ids` flag. The simulation runs under the exact same scenario and Seed 42, but now our OnlineIDS controller evaluates sliding windows every 5 seconds, confirms anomalies with a 2-strike filter, and invalidates poisoned routes."*

### Command
```powershell
python simulator/run_scenario.py --scenario scenarios/e2_blackhole_onset_30n.json --seed 42 --ids --out traces/demo_ids.csv
```

### Expected Output
```text
Loaded scenario: e2_blackhole_onset_30n (30 nodes, duration: 300.0s)
[IDS] Initialized OnlineIDS controller with RandomForest champion (K=2, tau=0.50, cooling=30.0s)
[IDS:55.0s] Node 21 flagged as anomalous (P=0.91) -> STRIKE 1 recorded.
[IDS:60.0s] Node 21 confirmed anomalous (P=0.94) -> STRIKE 2 confirmed.
[MITIGATION:60.0s] Quarantining Node 21 until t=90.0s.
[MITIGATION:60.0s] Invalidating routes through Node 21 across 29 active nodes.
[AODV:60.2s] Honest nodes broadcasting fresh RREQs bypassing blacklisted Node 21.
[AODV:60.8s] Legitimate alternate multi-hop paths established.
Simulation finished in 0.78s wall-clock time.
[METRICS] Packet Delivery Ratio (PDR): 0.6101 (61.01%)
[METRICS] Throughput:                 42.48 kbps
[METRICS] Average End-to-End Delay:   5.19 ms
[METRICS] Routing Overhead Ratio:     0.0859
Trace written to: traces/demo_ids.csv
```

### Explanatory Commentary
> *"Look at the sequence of events logged in the terminal:
> 1. At **t=55s** (one window after attack onset), the Random Forest model flags Node 21 with probability 0.91, logging Strike 1.
> 2. At **t=60s**, Strike 2 confirms the malicious behavior. The 2-strike filter prevents false isolations.
> 3. The controller places Node 21 into the quarantine table for 30 seconds and purges all routes pointing through Node 21.
> 4. Honest nodes broadcast fresh RREQs, ignoring Node 21's replies.
> 5. Alternate multi-hop routes are discovered, and the data packets resume flowing.
>
> **The final result:** PDR recovered from **14.18% back to 61.01%**—recovering **92.9% of the baseline delivery ratio**. Furthermore, our routing overhead increased by only **+0.0307** control packets per data packet, demonstrating that our defense restores security without congesting the network."*

---

## Supplementary Commands for Examiner Inquiries

### If the Examiner asks: "Can I see the comparative triad plots?"
Run:
```powershell
start results/plots/qos_recovery_triad_dashboard.png
start results/plots/qos_pdr_recovery.png
```

### If the Examiner asks: "How do you know Random Forest was better than SVM?"
Run:
```powershell
python -c "import pandas as pd; print(pd.read_csv('results/metrics.csv')[['model','accuracy','precision','recall','f1_blackhole','fpr']])"
```

### If the Examiner asks: "Can you prove there was no data leakage in your train/test split?"
Run:
```powershell
python -c "import pandas as pd; train=pd.read_csv('data/train.csv'); test=pd.read_csv('data/test.csv'); print('Train seeds:', train['seed'].unique(), 'Test seeds:', test['seed'].unique())"
```
*Expected Output:* `Train seeds: [42 43] Test seeds: [44]` — Proving zero seed overlap!

---
*End of Live Demonstration Walkthrough. Rehearse commands once prior to presentation.*
