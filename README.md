<!-- generated-by: gsd-doc-writer -->
# Machine Learning-Based Intrusion Detection System for MANET

A Windows-native, pure-Python discrete-event network simulator, machine learning-driven intrusion detection and mitigation framework, and full-screen Interactive Terminal UI (TUI) for Mobile Ad-Hoc Networks (MANET).

## Overview

Mobile Ad-Hoc Networks (MANETs) lack centralized routing infrastructure, exposing them to routing disruptions such as Blackhole (false high-sequence route spoofing) and Grayhole (selective or probabilistic packet dropping) attacks. This project provides a complete, reproducible software suite that couples:
1. **Discrete-Event MANET Simulator:** An in-repo pure-Python simulator (SimPy + NetworkX) executing RFC 3561 Ad hoc On-Demand Distance Vector (AODV) routing over dynamic Random Waypoint mobility.
2. **Decoupled Adversarial Injection:** Swappable attack strategies (Blackhole and Grayhole) injected at the composition root without contaminating core protocol code.
3. **Anti-Leakage Feature Extraction:** Sliding-window traffic aggregation deriving 10-column tabular metrics without ground-truth label or identity leakage.
4. **FPR-Gated Machine Learning:** Cost-sensitive Scikit-learn classifiers operating under an enforced False Positive Rate gate ($\text{FPR} \le 1.0\%$) to prevent false-alarm network fragmentation.
5. **Closed-Loop Mitigation:** Dynamic `OnlineIDS` controller with a 2-strike confirmation filter that isolates confirmed malicious nodes and expunges poisoned routes (recovering 95.51% of baseline delivery in the 300s Seed-42 benchmark).
6. **Interactive Terminal UI (TUI):** A full-screen, keyboard-first presentation layer (`python -m manet`, app name `MANET IDS`) built with Textual 8.2.8, offering real-time SOC monitoring, scenario configuration wizards, QoS scorecards, and experiment management.

---

## Prerequisites & Installation

- **Operating System:** Windows 10 / Windows 11 native (no WSL, Linux VM, Docker, or external C/C++ compiler required).
- **Python Version:** Python 3.11+ (verified on native CPython 3.11.8 64-bit).

### 1. Install Dependencies

Clone the repository and install the exact pinned dependency stack from [requirements.txt](requirements.txt):

```powershell
git clone https://github.com/Sujoy-004/MANET-Intrusion-Detection-System.git
cd "MANET-Intrusion-Detection-System"
python -m pip install -r requirements.txt
```

### 2. Verify Environment Health

Run the on-demand environment verification script to assert runtime version, dependency exact pins, CLI entry points, and presentation layer wiring:

```powershell
python scripts/verify_environment.py
```

Expected output: All runtime and dependency checks report `[OK]`, artifact availability is checked, and the script exits with code `0`.

---

## Interactive Terminal UI (TUI)

The v2.0 milestone introduces an interactive, full-screen terminal application providing an operational flight deck for configuring simulations, monitoring live packet traffic, and evaluating IDS mitigation metrics.

### Launching the Application

Launch the TUI from the repository root:

```powershell
python -m manet
```

### Key TUI Features

- **Executive Dashboard:** Live status cards for system diagnostics, ML model readiness, active workload state, and quick CTA actions.
- **Scenario Wizard (`[S]`):** 3-step interactive wizard for selecting presets or custom parameters, configuring mobility/traffic, setting duration/seed, and previewing pre-flight checks.
- **Live Run Monitor (`[R]`):** Real-time SOC-style monitor with SimPy virtual-time progress bar, wall-clock timer, live packet counters (`SENT`, `FWD`, `RECV`, `DROP`), throttled RichLog packet event stream, and safe cooperative cancellation (`[X]`).
- **Results & QoS Scorecard:** Post-run evaluation screen displaying delivery metrics (PDR, throughput, delay, routing overhead), color-coded threshold badges, raw packet trace viewers, and isolation event ledgers.
- **Experiment Records & Workspace (`[O]`):** History screen listing past runs from `.manet-workspace/`, manifest inspect views with SHA-256 checksum validation, and safe workspace pruning modal (`[D]`).
- **Diagnostics Probe (`[P]`):** Real-time system health card displaying Python version, dependency checks, model artifact paths, and active process metrics.
- **Command Palette (`[Ctrl+P]`):** Searchable command launcher for jumping to any screen, toggling settings, or triggering actions.

### Global Keyboard Shortcuts

| Shortcut | Action | Description |
|---|---|---|
| `[S]` | **Simulate** | Open Scenario Configuration Wizard |
| `[R]` | **Live Run** | Jump to Live Simulation Monitor |
| `[O]` | **Records** | View Experiment History & Artifacts |
| `[P]` | **Diagnostics** | Open System & Environment Diagnostics |
| `[Ctrl+P]` | **Palette** | Open Quick Command Palette |
| `[F1]` | **Help** | View Shortcuts & Documentation |
| `[Esc]` | **Back / Close** | Return to Main Workspace or close modal |
| `[Ctrl+Q]` | **Quit** | Safe exit with confirmation modal |

### Terminal Requirements & Limitations

- **Minimum Geometry:** 80 columns × 24 rows minimum geometry recommended. Screen layouts adaptively reflow; geometries below 80×24 may truncate panels.
- **Supported Terminals:** Verified on native Windows Terminal and standard Windows Console host (`conhost.exe`). Untested on PuTTY or tmux.
- **Session Settings:** Display toggles (High Contrast, Reduced Motion, Compact Density) are session-only and reside in-memory.
- **Symlink Fallback:** On non-elevated Windows without Developer Mode, workspace pruning automatically falls back to copy-based operations.

---

## Quick Start (CLI Workflows)

All legacy CLI workflows remain 100% operational, backward-compatible, and regression-tested.

### 0. First-Time Model Preparation (After Fresh Clone)

Trained model artifacts (`ml/models/*.joblib`) are excluded from Git via `.gitignore` to keep the repository lightweight and deterministic. Generate the champion model locally:

```powershell
python scripts/build_dataset.py --multi-attack
python -m ml.train
python -m ml.evaluate
```

- **Dataset:** 52,200 total window rows (34,800 train on seeds 42 & 43; 17,400 held-out test on seed 44).
- **FPR Gate:** `ml/evaluate.py` enforces `FPR <= 1.0%`. Champion Random Forest achieves **F1 0.7593, FPR 0.0099 (0.99%)**, persisted to `ml/models/best_model.joblib`.

### 1. Run Baseline Normal Simulation

```powershell
python -m simulator.run_scenario --scenario scenarios/e1_normal_30n.json --seed 42 --out traces/baseline_normal
```

### 2. Run Blackhole Attack Simulation

```powershell
python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/attack_blackhole
```

### 3. Run Closed-Loop IDS Mitigation

```powershell
python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/ids_protected --ids
```

The online IDS evaluates sliding-window node behavior every 5.0s. After 2 consecutive positive detections, the attacker is isolated, poisoned routes are expunged, and traffic reroutes around the malicious node.

---

## 300-Second Benchmark Results (Seed 42 Reference)

> **Benchmark Provenance:** Verified reference run (300 simulated seconds, Seed 42, 30 nodes, 6 CBR application flows). Metrics vary across seeds and topologies.

| Metric | Baseline AODV (Normal) | Blackhole Attack (No IDS) | AODV + Online IDS | Net Mitigation Impact |
|---|---|---|---|---|
| **Packet Delivery Ratio (PDR)** | 65.88% (4,098 / 6,220) | 18.10% (1,126 / 6,220) | 62.93% (3,914 / 6,220) | **+44.82 percentage points (+247.6% relative to attack; 95.51% baseline restored)** |
| **Throughput (kbps)** | 55.95 kbps | 15.37 kbps | 53.44 kbps | **+38.07 kbps (+247.7% relative to attack; 95.51% baseline restored)** |
| **Average Delay (ms)** | 134.74 ms (4,098 pkts) | 138.66 ms (1,126 pkts) | 102.29 ms (3,914 pkts) | **Descriptive cohort comparison across delivered packets** |
| **Routing Overhead Ratio** | 0.0950 | 0.1055 | 0.1302 | **+0.0247 bounded control packet overhead** |

---

## Running the Automated Test Suite

The test suite contains **293 collected tests across 38 test modules**:

```powershell
# Run the complete test suite
python -m pytest -q

# Run AST architectural import boundary enforcement tests (fast)
python -m pytest tests/test_manet_import_boundaries.py tests/test_import_boundaries.py -q

# Run CLI compatibility regression harness
python -m pytest tests/test_legacy_cli_compat.py -q
```

Expected result: **290 passed, 3 skipped** (symlink privilege skips on non-elevated Windows), **0 failed**.

---

## Repository Structure

```text
├── manet/                 # Full-screen Textual 8.2.8 TUI presentation layer (Zero business logic)
│   ├── adapters/          # One-way adapters: diagnostics, scenario, execution, workspace, status
│   ├── commands/          # Command palette provider, registry, console driver
│   ├── runtime/           # Paths, settings, supervisor, telemetry sink, theme, keymap
│   ├── screens/           # Workspace, workflow wizard, live run monitor, results, history, prune
│   └── widgets/           # Dashboard cards, QoS scorecard, nav rails, status bars
├── bootstrap.py           # Composition root bridging TUI to simulator and ML (never inside manet/)
├── simulator/             # Pure-Python discrete-event network simulator (SimPy + NetworkX)
│   ├── aodv.py            # RFC 3561 AODV protocol (state machine, backoff, queue TTL, blacklist)
│   ├── mobility.py        # 2D Random Waypoint mobility model
│   ├── radio.py           # Unit-disk transmission range & dynamic neighbor discovery
│   ├── traffic.py         # CBR/UDP application traffic generator
│   ├── metrics.py         # PDR, throughput, delay, and routing overhead calculators
│   └── run_scenario.py    # CLI entry point for scenario execution
├── attacks/               # Decoupled adversarial strategies (injected at composition root)
│   ├── base.py            # AttackStrategy base interface
│   ├── blackhole.py       # Sequence-spoofing & unconditional packet drop strategy
│   ├── grayhole.py        # Honest routing & selective/probabilistic drop strategy
│   └── registry.py        # Factory registry for strategy injection
├── feature_extraction/    # Sliding-window trace feature engineering
│   └── extract_features.py# 10-column canonical anti-leakage feature extractor
├── ml/                    # Machine learning models, evaluation & closed-loop response
│   ├── dataset.py         # Seed-partitioned train/test splitting and scaling
│   ├── train.py           # Cost-sensitive pipeline training with 5-fold Stratified CV
│   ├── evaluate.py        # Multi-metric security evaluator (Precision, Recall, F1, FPR)
│   ├── response.py        # OnlineIDS real-time sliding controller with 2-strike confirmation
│   ├── generalization.py  # Cross-scenario domain transfer analysis
│   ├── plots.py           # Headless-safe 300 DPI Matplotlib/Seaborn visualization suite
│   └── models/            # Serialized champion models and metadata
├── scenarios/             # Declarative scenario JSON configurations
├── scripts/               # Environment verification, benchmarking, dataset assembly scripts
│   ├── verify_environment.py # On-demand environment & dependency pin verification
│   ├── build_dataset.py
│   ├── run_generalization_matrix.py
│   └── run_closed_loop_benchmark.py
├── tests/                 # 293 pytest tests across 38 modules (unit, integration, TUI, AST boundaries)
├── requirements.txt       # Exact-pinned dependencies (10 packages)
├── results/               # Metric CSVs and publication-grade plots (results/plots/)
└── docs/                  # Detailed documentation and thesis report
```

---

## Documentation Index

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Architectural design, presentation/core decoupling, AST boundary enforcement, and data flows.
- [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md): Complete setup guide, TUI walkthrough, and CLI execution tutorials.
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md): Scenario schemas, TUI session settings, and IDS hyperparameters.
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md): Architectural contracts, extension points, coding standards, and testing guidelines.
- [docs/TESTING.md](docs/TESTING.md): Test suite architecture, coverage metrics, and verification gates.
- [docs/FINAL_PROJECT_REPORT.md](docs/FINAL_PROJECT_REPORT.md): Comprehensive thesis report with theoretical formulations and benchmark analysis.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
