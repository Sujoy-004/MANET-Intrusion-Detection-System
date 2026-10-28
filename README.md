<!-- generated-by: gsd-doc-writer -->
# Machine Learning-Based Intrusion Detection System for MANET

A Windows-native, pure-Python discrete-event network simulator and machine learning-driven intrusion detection and mitigation framework for Mobile Ad-Hoc Networks (MANET).

## Overview

Mobile Ad-Hoc Networks (MANETs) lack centralized routing infrastructure, exposing them to routing disruptions such as Blackhole (false high-sequence route spoofing) and Grayhole (selective or probabilistic packet dropping) attacks. This project provides a complete, reproducible software suite that couples:
1. An in-repo discrete-event MANET simulator (SimPy + NetworkX) executing RFC 3561 Ad hoc On-Demand Distance Vector (AODV) routing over dynamic Random Waypoint mobility.
2. Decoupled attack injection behaviors that manipulate routing tables and drop forwarded data packets.
3. Sliding-window, non-leaking feature extraction deriving tabular traffic metrics from packet event traces.
4. Cost-sensitive Scikit-learn classification models tuned under a strict False Positive Rate gate ($\text{FPR} \le 1.0\%$).
5. A dynamic closed-loop Online IDS response engine that isolates confirmed malicious nodes, invalidates poisoned routing table entries, and restores packet delivery ratio (achieving 92.9% QoS recovery on Blackhole).

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
- **Anti-Leakage Data Partitioning:** Train and test datasets are partitioned strictly by simulation seed (Seeds 42 & 43 for training, Seed 44 for held-out testing), eliminating temporal autocorrelation leakage.
- **Champion ML Classifier:** Random Forest and Decision Tree classifiers operating under an enforced $\text{FPR} \le 1.0\%$ threshold to prevent false-alarm network fragmentation.
- **Measurable QoS Recovery:** 3-way benchmark evaluation proves PDR recovers from 48.74% (under attack) back to 95.57% (with IDS active), representing a 92.9% recovery of baseline network utility.

| Metric | Baseline AODV | Blackhole Attack | AODV + Online IDS | Net Recovery |
|---|---|---|---|---|
| **Packet Delivery Ratio (PDR)** | 99.2% | 48.7% | 95.6% | **+46.8% absolute (92.9% relative)** |
| **Throughput (kbps)** | 42.1 kbps | 20.7 kbps | 40.5 kbps | **96.2% restored** |
| **Average Delay (s)** | 0.012 s | 0.008 s | 0.018 s | Low rerouting penalty |
| **Routing Overhead** | 0.041 | 0.019 | 0.049 | Minimal control overhead |

## Running the Automated Test Suite

Run the full automated test suite containing 69 unit, integration, and pipeline validation tests:

```bash
python -m pytest
```

## Repository Structure

```text
├── simulator/             # Pure-Python discrete-event network simulator (SimPy + NetworkX)
│   ├── aodv.py            # RFC 3561 AODV protocol (RREQ, RREP, RERR, route table, blacklist hook)
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
├── tests/                 # 69 pytest unit and integration tests
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
