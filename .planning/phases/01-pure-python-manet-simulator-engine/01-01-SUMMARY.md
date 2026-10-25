---
phase: 01-pure-python-manet-simulator-engine
plan: 01
subsystem: simulator
tags: [simpy, networkx, python, determinism, tracer]

requires: []
provides:
  - "Pure-Python discrete-event MANET simulator package"
  - "Deterministic scenario runner with explicit integer seeding"
  - "Baseline 30-node scenario configuration"
  - "Initial packet trace CSV writer"
affects: [01-02, 01-03, phase-02]

actuals:
  tokens: 1200
  tasks: 3
  commits: 2

tech-stack:
  added: [simpy, random.Random]
  patterns: [Deterministic explicit-seed threading, Windows-safe pathlib I/O]

key-files:
  created:
    - simulator/__init__.py
    - simulator/run_scenario.py
    - scenarios/e1_normal_30n.json
  modified: []

key-decisions:
  - "Used explicit random.Random(seed) threaded through all simulation components rather than global random"
  - "Standardized trace CSV header: time,src,dst,pkt_id,type,hop_count,dropped_by"

patterns-established:
  - "Pattern 1: Deterministic SimPy environment initialization without global random/env.seed"
  - "Pattern 2: Pathlib-based safe path resolution for Windows execution"

requirements-completed:
  - SIM-01

coverage:
  - id: D1
    description: "Discrete-event clock executes simulation scenarios deterministically under explicit integer seeds"
    requirement: "SIM-01"
    verification:
      - kind: automated
        ref: "python -m simulator.run_scenario --scenario scenarios/e1_normal_30n.json --seed 42 --out traces/test_tracer.csv"
        status: pass
---

# Plan 01-01 Summary: Determinism & Simulator Foundation

## Accomplishments
1. Created `simulator/` package structure and composition root in `simulator/run_scenario.py`.
2. Established deterministic random number generator architecture with explicit `random.Random(seed)` threading.
3. Created baseline 30-node normal scenario configuration in `scenarios/e1_normal_30n.json`.
4. Verified end-to-end tracer slice: scenario loading -> discrete-event initialization -> deterministic trace logging.

## Self-Check: PASSED
- Verified identical hash across consecutive executions with identical seed.
- Verified Windows-safe paths and CLI parameters (`--scenario`, `--seed`, `--out`).
