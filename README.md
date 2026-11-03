<!-- generated-by: gsd-doc-writer -->
# Machine Learning-Based Intrusion Detection System for MANET

A Windows-native, pure-Python discrete-event network simulator and machine learning-driven intrusion detection and mitigation framework for Mobile Ad-Hoc Networks (MANET).

## Overview

Mobile Ad-Hoc Networks (MANETs) lack centralized routing infrastructure, exposing them to routing disruptions such as Blackhole (false high-sequence route spoofing) and Grayhole (selective or probabilistic packet dropping) attacks. This project provides a complete, reproducible software suite that couples:
1. An in-repo discrete-event MANET simulator (SimPy + NetworkX) executing RFC 3561 Ad hoc On-Demand Distance Vector (AODV) routing over dynamic Random Waypoint mobility.
2. Decoupled attack injection behaviors that manipulate routing tables and drop forwarded data packets.
3. Sliding-window, non-leaking feature extraction deriving tabular traffic metrics from packet event traces.
4. Cost-sensitive Scikit-learn classification models tuned under a strict False Positive Rate gate ($\text{FPR} \le 1.0\%$).
5. A dynamic closed-loop Online IDS response engine that isolates confirmed malicious nodes, invalidates poisoned routing table entries, and restores packet delivery ratio (achieving 62.93% PDR vs. 18.10% under attack in the 300s Seed-42 benchmark).

## Prerequisites & Installation

- **Operating System:** Windows 10/11 native (no WSL, Linux VM, or Docker required)
- **Python Version:** Python 3.11+ (verified on 3.11.8)

Install the required dependencies using `pip`:

```bash
python -m pip install simpy==4.1.2 networkx==3.6.1 scikit-learn==1.8.0 pandas==3.0.2 numpy==1.26.4 matplotlib==3.10.8 seaborn==0.13.2 pytest==9.0.2 joblib==1.5.3
```

## Quick Start

### 1. Run Baseline Normal Simulation

Execute a 30-node normal MANET simulation with Random Waypoint mobility:

```bash
python -m simulator.run_scenario --scenario scenarios/e1_normal_30n.json --seed 42 --out traces/baseline_normal
```

This generates packet-level CSV event traces in `traces/baseline_normal/trace_seed42.csv` and prints end-to-end metrics (Packet Delivery Ratio, throughput, latency, routing overhead).

### 2. Run Blackhole Attack Simulation

Run an identical scenario with an active Blackhole attacker injected:

```bash
python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/attack_blackhole
```

The Blackhole attacker intercepts RREQ broadcasts, advertises an inflated sequence number, and silently drops all intercepted application data.

### 3. Run Closed-Loop IDS Mitigation

Run the simulation with active closed-loop machine learning detection and route isolation enabled:

```bash
python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/ids_protected --ids
```

The online IDS evaluates sliding-window node behavior every 5.0 seconds. Upon 2 consecutive malicious classifications, the attacker is blacklisted, poisoned routes are expunged, and traffic reroutes around the attacker.

## Key Features & Results

- **Sub-Second Execution:** Built with SimPy discrete-event processing, running 300 seconds of simulated network activity in ~0.83 seconds wall-clock time (~70,000 events/sec).
- **Robust AODV Discovery Lifecycle:** Integrated RFC 3561 route discovery recovery featuring per-destination state machines, exponential backoff (2 retries, 3 total attempts: 2s -> 4s -> 8s), discovery timeouts with timer-generation protection, bounded packet buffering (queue limit 100 packets, TTL 20.0s), discovery cooldown (2.0s), and quarantine response guards to recover cleanly from temporary network partitions without broadcast storms.
- **Anti-Leakage Data Partitioning:** Train and test datasets are partitioned strictly by simulation seed (Seeds 42 & 43 for training, Seed 44 for held-out testing), eliminating temporal autocorrelation leakage.
- **Champion ML Classifier:** Random Forest classifier operating under an enforced $\text{FPR} \le 1.0\%$ threshold to prevent false-alarm network fragmentation.
- **Measurable QoS Recovery:** Evaluated on the standardized 300-second, Seed-42 comparative triad benchmark (`scenarios/e1_normal_30n.json` vs. `scenarios/e2_blackhole_30n.json`). The online IDS restores PDR from 18.10% under unmitigated attack back to 62.93% (recovering 95.51% of baseline delivery: 3,914 / 4,098 packets, +44.82 percentage points absolute PDR improvement over attack).

### 300-Second Benchmark Results (Seed 42 Reference)

> **Benchmark Provenance Note:** The table below documents the verified single-seed reference run (300 simulated seconds, Seed 42, 30 nodes, 6 CBR application flows). Metrics vary across mobility seeds and topologies; do not assume identical numerical results across unseeded configurations.

| Metric | Baseline AODV (Normal) | Blackhole Attack (No IDS) | AODV + Online IDS | Net Mitigation Impact |
|---|---|---|---|---|
| **Packet Delivery Ratio (PDR)** | 65.88% (4,098 / 6,220) | 18.10% (1,126 / 6,220) | 62.93% (3,914 / 6,220) | **+44.82 percentage points absolute PDR (+247.6% relative to attack; 95.51% baseline restored: 3,914 / 4,098)** |
| **Throughput (kbps)** | 55.95 kbps | 15.37 kbps | 53.44 kbps | **+38.07 kbps (+247.7% relative to attack; 95.51% baseline restored)** |
| **Average Delay (ms)** | 134.74 ms (4,098 delivered pkts) | 138.66 ms (1,126 delivered pkts) | 102.29 ms (3,914 delivered pkts) | **Cohort comparison: 36.37 ms vs. attack, 32.45 ms vs. baseline (delivered pkts only)** |
| **Routing Overhead Ratio** | 0.0950 | 0.1055 | 0.1302 | **+0.0247 bounded control packet overhead** |

> **Delay Measurement Note:** Average end-to-end delay is calculated in `simulator/metrics.py` exclusively across successfully delivered packets (inner join between `DATA_SENT` and `DATA_RECV` on packet ID). Packets dropped by attacks, buffer overflow, or topology partitions are excluded from delay computation. Latency comparisons between modes represent descriptive statistics across distinct delivered-packet populations rather than causal proof of path-level delay optimization.

## Running the Automated Test Suite

Run the full automated test suite containing 79 unit, integration, recovery, and pipeline validation tests:

```bash
python -m pytest
```

## Repository Structure

```text
├── simulator/             # Pure-Python discrete-event network simulator (SimPy + NetworkX)
│   ├── aodv.py            # RFC 3561 AODV protocol (bounded retries/backoff, discovery lifecycle, buffer TTL, blacklist guards)
│   ├── mobility.py        # 2D Random Waypoint mobility model
│   ├── radio.py           # Unit-disk transmission range & dynamic neighbor discovery
│   ├── traffic.py         # CBR/UDP application traffic generator
│   ├── metrics.py         # PDR, throughput, delay, and routing overhead calculators
│   └── run_scenario.py    # CLI entry point for scenario execution
├── attacks/               # Decoupled adversarial strategies
│   ├── base.py            # AttackStrategy base interface
│   ├── blackhole.py       # Sequence-spoofing & unconditional packet drop strategy
│   ├── grayhole.py        # Honest routing & selective/probabilistic drop strategy
│   └── registry.py        # Factory registry for strategy injection
├── feature_extraction/    # Sliding-window trace feature engineering
│   └── extract_features.py# 10-column canonical anti-leakage feature extractor
├── ml/                    # Machine learning models, evaluation & closed-loop response
│   ├── dataset.py         # Seed-partitioned train/test splitting and scaling
│   ├── train.py           # Cost-sensitive pipeline training with 5-fold Stratified CV
│   ├── evaluate.py        # Multi-metric security evaluator (Precision, Recall, F1, FPR, Confusion Matrix)
│   ├── response.py        # OnlineIDS real-time sliding controller with 2-strike confirmation
│   ├── generalization.py  # Cross-scenario domain transfer analysis
│   ├── plots.py           # Headless-safe 300 DPI Matplotlib/Seaborn visualization suite
│   └── models/            # Serialized champion models and metadata
├── scenarios/             # Declarative scenario JSON configurations
├── scripts/               # Benchmarking, dataset assembly, and evaluation scripts
│   ├── build_dataset.py
│   ├── run_generalization_matrix.py
│   └── run_closed_loop_benchmark.py
├── tests/                 # 79 pytest unit, integration, and recovery tests
├── results/               # Metric CSVs and publication-grade plots (results/plots/)
└── docs/                  # Detailed documentation and thesis report
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Simulator mechanics, decoupled attack injection, feature pipeline, and closed-loop response.
- [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md): Step-by-step setup, scenario execution, and quick experimentation guide.
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md): Scenario JSON specifications, feature schema, and IDS hyperparameters.
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): Architectural contracts, guidelines for extending attacks, and coding conventions.
- [docs/TESTING.md](docs/TESTING.md): Test suite organization, Gate 2 impact verification, and benchmark validation.
- [docs/FINAL_PROJECT_REPORT.md](docs/FINAL_PROJECT_REPORT.md): Complete B.Tech project thesis report with mathematical models and full experimental results.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
