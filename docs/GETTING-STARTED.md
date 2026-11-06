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

## Step 0: Generate the Trained IDS Model (First Time Only)

On a fresh clone, the IDS model does not exist yet. The `.gitignore` rule `ml/models/*.joblib` excludes the trained model binaries from version control because they are deterministic products of seeded simulations — the IDS model is a build-time artifact, not a source asset, and it can be regenerated losslessly from the canonical seeds.

Run the following sequence from the repository root in PowerShell:

```powershell
python scripts/build_dataset.py --multi-attack
python -m ml.train
python -m ml.evaluate
```

Expected outputs (verified reference run): the dataset totals 52,200 rows — a training split of 34,800 rows from seeds 42 & 43 and a held-out test split of 17,400 rows from seed 44. `python -m ml.train` writes candidate pipelines to `ml/models/`. `python -m ml.evaluate` selects the champion under the FPR <= 1.0% gate (verified reference: Random Forest, F1 0.7593, FPR 0.0099) and writes `ml/models/best_model.joblib` together with `ml/models/model_metadata.json`.

The full chain fits comfortably in a standard terminal session. When it finishes, confirm the model exists — `Test-Path ml/models/best_model.joblib` in PowerShell should return `True`.

## First Run: Running Your First Simulation

### Step 1: Run a Baseline Simulation

Execute a baseline 30-node ad-hoc simulation with no active attacks:

```powershell
python -m simulator.run_scenario --scenario scenarios/e1_normal_30n.json --seed 42 --out traces/getting_started_baseline
```

Expected output (300-second Seed-42 reference benchmark):
```text
Running scenario: scenarios/e1_normal_30n.json (seed=42)
Simulation completed at time 300.0s.
Packets Sent: 6220
Packets Received: 4098
Packet Delivery Ratio (PDR): 65.88%
Throughput: 55.95 kbps
Trace written to: traces/getting_started_baseline/trace_seed42.csv
```

### Step 2: Run a Blackhole Attack Simulation

Run an identical network configuration, but with a malicious Blackhole node injected:

```powershell
python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/getting_started_blackhole
```

Notice the immediate degradation in network delivery:
```text
Packet Delivery Ratio (PDR): 18.10% (severe packet drop: 1126 received / 6220 sent)
Throughput: 15.37 kbps
```

### Step 3: Run with Closed-Loop Online IDS Active

This step requires the model generated in Step 0 (`ml/models/best_model.joblib`); the `--ids` runtime loads it on startup.

Re-run the Blackhole scenario with the `--ids` flag enabled:

```powershell
python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/getting_started_ids --ids
```

The online IDS detects the attacker within two sliding windows and purges it from routing tables:
```text
[IDS] Time 25.0s: Strike 1 registered for malicious node
[IDS] Time 30.0s: Strike 2 confirmed! Malicious node isolated from AODV routing.
Packet Delivery Ratio (PDR): 62.93% (restores 3914 received / 6220 sent; 95.5% baseline recovery)
Throughput: 53.44 kbps
```

## Running the Automated Test Suite

Verify complete system functionality by running the 79-test automated suite:

```powershell
python -m pytest
```

All 79 unit, integration, and recovery tests should pass in under 120 seconds.

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

### 4. Missing `ml/models/best_model.joblib`
- **Symptom:** Running `--ids` (or `python -m ml.evaluate`, `scripts/run_closed_loop_benchmark.py`) fails with a missing-file / invalid-load error for `ml/models/best_model.joblib`.
- **Cause:** Model binaries are excluded from the repo (`ml/models/*.joblib` in `.gitignore`) and must be regenerated locally.
- **Solution:** Execute the Step 0 sequence from the repository root: `python scripts/build_dataset.py --multi-attack`, then `python -m ml.train`, then `python -m ml.evaluate`.

## Next Steps

- **Fresh clone?** Complete the full model preparation starting at [Step 0](#step-0-generate-the-trained-ids-model-first-time-only) before continuing with any `--ids` or ML workflow below.
- Explore the architecture and protocol implementation in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Learn how to configure custom scenarios in [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
- Understand coding standards and how to add new attacks in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
- Learn about the testing framework and benchmarks in [docs/TESTING.md](docs/TESTING.md).
