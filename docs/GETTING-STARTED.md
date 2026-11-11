<!-- generated-by: gsd-doc-writer -->
# Getting Started

This guide walks you through setting up, running, verifying, and evaluating the Machine Learning-Based Intrusion Detection and Response System for MANET on a native Windows environment.

## Prerequisites

- **Operating System:** Windows 10 or Windows 11 (native execution). No WSL, Linux VM, Docker, or external C/C++ compiler is required.
- **Python:** Python 3.11+ (verified on native CPython 3.11.8 64-bit).
- **Git:** Git 2.40+ (for source control).

---

## Installation & Environment Verification

### 1. Clone the Repository

Open PowerShell or Command Prompt:

```powershell
git clone https://github.com/Sujoy-004/MANET-Intrusion-Detection-System.git
cd "MANET-Intrusion-Detection-System"
```

### 2. Install Dependencies

Install the verified exact-pinned dependency stack using the root `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

> **Note:** Always invoke `python -m pip` rather than bare `pip` to ensure packages are installed directly into your active Python environment.

### 3. Verify Environment Health

Assert environment health and exact dependency pin compliance:

```powershell
python scripts/verify_environment.py
```

Expected output:
```text
ENVIRONMENT VERIFICATION: MANET IDS (Windows Native)
[OK] Python version: 3.11.8 (64-bit Windows)
[OK] Pinned dependency: simpy == 4.1.2
[OK] Pinned dependency: networkx == 3.6.1
[OK] Pinned dependency: scikit-learn == 1.8.0
[OK] Pinned dependency: pandas == 3.0.2
[OK] Pinned dependency: numpy == 1.26.4
[OK] Pinned dependency: matplotlib == 3.10.8
[OK] Pinned dependency: seaborn == 0.13.2
[OK] Pinned dependency: joblib == 1.5.3
[OK] Pinned dependency: textual == 8.2.8
[OK] Pinned dependency: pytest == 9.0.2
[OK] Entrypoint check: simulator.run_scenario (exit 0)
[OK] Entrypoint check: ml.train (exit 0)
[OK] Entrypoint check: ml.evaluate (exit 0)
[OK] Entrypoint check: manet (alive and responding)
ENVIRONMENT VERIFICATION PASSED: System ready.
```

---

## Step 0: Generate the Trained IDS Model (First Time Only)

On a fresh clone, the trained IDS model does not exist yet. The `.gitignore` rule `ml/models/*.joblib` excludes the model binaries from Git because they are deterministic products of seeded simulations that can be regenerated cleanly from canonical seeds.

Run the training sequence from the repository root in PowerShell:

```powershell
python scripts/build_dataset.py --multi-attack
python -m ml.train
python -m ml.evaluate
```

- **Dataset:** 52,200 total window rows (34,800 train on seeds 42 & 43; 17,400 held-out test on seed 44).
- **FPR Gate:** `ml/evaluate.py` enforces `FPR <= 1.0%`. Champion Random Forest achieves **F1 0.7593, FPR 0.0099 (0.99%)**, persisted to `ml/models/best_model.joblib`.

Confirm the model exists: `Test-Path ml/models/best_model.joblib` should return `True`.

---

## Option A: Interactive Terminal UI (TUI)

Launch the full-screen terminal application:

```powershell
python -m manet
```

### Quick Walkthrough

1. **Dashboard & Diagnostics:** The Executive Grid displays system diagnostics, model readiness, and recent experiment history. Press `[P]` to view detailed dependency and runtime health.
2. **Configure a Simulation (`[S]`):**
   - **Step 1 (Scenario Mode):** Select a preset scenario (e.g., `e1_normal_30n` or `e2_blackhole_30n`) or choose custom parameter mode.
   - **Step 2 (Parameters):** Adjust simulation duration, random seed, CBR traffic rate, or node count.
   - **Step 3 (Pre-Flight Review):** Review pre-flight validation checks and destination workspace path, then press **Launch Simulation**.
3. **Live Monitoring (`[R]`):** The Live Run screen tracks SimPy virtual time, wall-clock duration, real-time packet counters (`SENT`, `FWD`, `RECV`, `DROP`), and streaming event logs.
4. **Inspect Results:** Upon completion, the Results Screen displays the QoS Scorecard (PDR, throughput, delay, routing overhead), threshold status badges, and isolation logs.
5. **View Records (`[O]`):** The History screen lists past runs stored in `.manet-workspace/`, validates SHA-256 manifest checksums, and supports safe record pruning (`[D]`).
6. **Exit (`[Ctrl+Q]`):** Prompts a confirmation modal to safely exit the application.

---

## Option B: Command-Line Interface (CLI)

All CLI entrypoints remain fully supported and backward-compatible.

### 1. Run a Baseline Simulation

Execute a 30-node normal MANET simulation with Random Waypoint mobility:

```powershell
python -m simulator.run_scenario --scenario scenarios/e1_normal_30n.json --seed 42 --out traces/getting_started_baseline
```

Expected output:
```text
Running scenario: scenarios/e1_normal_30n.json (seed=42)
Simulation completed at time 300.0s.
Packets Sent: 6220
Packets Received: 4098
Packet Delivery Ratio (PDR): 65.88%
Throughput: 55.95 kbps
Trace written to: traces/getting_started_baseline/trace_seed42.csv
```

### 2. Run a Blackhole Attack Simulation

Run an identical scenario with an active Blackhole attacker injected:

```powershell
python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/getting_started_blackhole
```

Expected output (severe degradation):
```text
Packet Delivery Ratio (PDR): 18.10% (severe packet drop: 1126 received / 6220 sent)
Throughput: 15.37 kbps
```

### 3. Run Closed-Loop Online IDS Mitigation

Re-run with closed-loop machine learning mitigation enabled:

```powershell
python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/getting_started_ids --ids
```

Expected output:
```text
[IDS] Time 25.0s: Strike 1 registered for malicious node
[IDS] Time 30.0s: Strike 2 confirmed! Malicious node isolated from AODV routing.
Packet Delivery Ratio (PDR): 62.93% (restores 3914 received / 6220 sent; 95.5% baseline recovery)
Throughput: 53.44 kbps
```

---

## Running the Automated Test Suite

Verify full system integrity by running the automated pytest suite:

```powershell
# Run the complete test suite (293 tests across 38 modules)
python -m pytest -q

# Run architectural AST import boundary enforcement tests
python -m pytest tests/test_manet_import_boundaries.py tests/test_import_boundaries.py -q

# Run legacy CLI compatibility tests
python -m pytest tests/test_legacy_cli_compat.py -q
```

Expected result: **290 passed, 3 skipped** (Windows symlink privilege skips on non-elevated shells), **0 failed**.

---

## Common Setup Issues & Troubleshooting

### 1. `ModuleNotFoundError: No module named 'attacks'` (or `simulator`, `manet`)
- **Cause:** Running via bare `pytest` or bare python script invocation without current directory in `sys.path`.
- **Solution:** Always invoke tools using `python -m pytest` or `python -m manet`.

### 2. `PermissionError: [Errno 13] Permission denied: '...trace.csv'`
- **Cause:** Microsoft Excel locks open CSV files, preventing the simulator from overwriting trace outputs.
- **Solution:** Close any CSV trace files in Excel before re-running simulations.

### 3. Missing `ml/models/best_model.joblib`
- **Symptom:** Running `--ids` fails with a missing-file error.
- **Solution:** Execute Step 0: `python scripts/build_dataset.py --multi-attack`, then `python -m ml.train`, then `python -m ml.evaluate`.

### 4. TUI Display Artifacts on Small Terminals
- **Symptom:** Content clips or wraps awkwardly in `python -m manet`.
- **Solution:** Ensure your terminal window is at least 80 columns by 24 rows (`80x24`).

---

## Next Steps

- Explore the architecture and protocol implementation in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Learn how to configure custom scenarios in [docs/CONFIGURATION.md](docs/CONFIGURATION.md).
- Understand coding standards and AST boundary invariants in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
- Learn about the testing framework and quality gates in [docs/TESTING.md](docs/TESTING.md).
