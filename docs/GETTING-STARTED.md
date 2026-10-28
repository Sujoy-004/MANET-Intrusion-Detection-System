<!-- generated-by: gsd-doc-writer -->
# Getting Started

This guide walks you through setting up, running, and evaluating the Machine Learning-Based Intrusion Detection and Response System for MANET on a Windows environment.

## Prerequisites

- **Operating System:** Windows 10 or Windows 11 (native execution). No WSL, Linux VM, Docker, or external C/C++ compiler is required.
- **Python:** Python 3.11+ (verified on Python 3.11.8).
- **Git:** Git 2.40+ (for source control).

## Installation

### 1. Clone the Repository

Open PowerShell or Command Prompt:

```powershell
git clone https://github.com/Sujoy-004/MANET-Intrusion-Detection-System.git
cd "MANET-Intrusion-Detection-System"
```

### 2. Install Required Python Packages

Install the exact verified dependency stack using the current interpreter:

```powershell
python -m pip install simpy==4.1.2 networkx==3.6.1 scikit-learn==1.8.0 pandas==3.0.2 numpy==1.26.4 matplotlib==3.10.8 seaborn==0.13.2 pytest==9.0.2 joblib==1.5.3
```

> **Note:** Always invoke `python -m pip` rather than bare `pip` to ensure packages are installed directly into your active Python environment.

## First Run: Running Your First Simulation

### Step 1: Run a Baseline Simulation

Execute a baseline 30-node ad-hoc simulation with no active attacks:

```powershell
python -m simulator.run_scenario --scenario scenarios/e1_normal_30n.json --seed 42 --out traces/getting_started_baseline
```

Expected output:
```text
Running scenario: scenarios/e1_normal_30n.json (seed=42)
Simulation completed at time 100.0s.
Packets Sent: 380
Packets Received: 377
Packet Delivery Ratio (PDR): 99.21%
Throughput: 30.89 kbps
Trace written to: traces/getting_started_baseline/trace_seed42.csv
```

### Step 2: Run a Blackhole Attack Simulation

Run an identical network configuration, but with a malicious Blackhole node injected:

```powershell
python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/getting_started_blackhole
```

Notice the immediate degradation in network quality:
```text
Packet Delivery Ratio (PDR): ~48.74% (severe packet drop detected)
```

### Step 3: Run with Closed-Loop Online IDS Active

Re-run the Blackhole scenario with the `--ids` flag enabled:

```powershell
python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/getting_started_ids --ids
```

The online IDS detects the attacker within two sliding windows and purges it from routing tables:
```text
[IDS] Time 25.0s: Strike 1 registered for node 12 (prob=0.89)
[IDS] Time 30.0s: Strike 2 confirmed! Node 12 isolated from AODV routing.
Packet Delivery Ratio (PDR): 95.57% (92.9% recovery of lost traffic)
```

## Running the Automated Test Suite

Verify complete system functionality by running the 69-test automated suite:

```powershell
python -m pytest
```

All 69 unit and integration tests should pass in under 60 seconds.

## Common Setup Issues & Troubleshooting

### 1. `ModuleNotFoundError: No module named 'attacks'` (or `simulator`)
- **Cause:** Running pytest via bare `pytest` instead of `python -m pytest` prevents Python from adding the current directory to `sys.path`.
- **Solution:** Always invoke tests using `python -m pytest`.

### 2. `PermissionError: [Errno 13] Permission denied: '...trace.csv'`
- **Cause:** Microsoft Excel locks open CSV files, preventing the simulator or feature extractor from overwriting trace outputs.
- **Solution:** Close any CSV trace files in Excel before re-running simulations.

### 3. Missing Output Directories
- **Cause:** Specifying a custom `--out` directory that does not exist.
- **Solution:** The simulator automatically creates destination directories via `pathlib.Path.mkdir(parents=True, exist_ok=True)`. Ensure your user account has write permissions in the project directory.

## Next Steps

- Explore the architecture and protocol implementation in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Learn how to configure custom scenarios in [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
- Understand coding standards and how to add new attacks in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
- Learn about the testing framework and benchmarks in [docs/TESTING.md](docs/TESTING.md).
