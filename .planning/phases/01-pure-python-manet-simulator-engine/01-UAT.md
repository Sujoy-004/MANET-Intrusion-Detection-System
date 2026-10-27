---
status: complete
phase: 01-pure-python-manet-simulator-engine
source:
  - .planning/phases/01-pure-python-manet-simulator-engine/01-01-SUMMARY.md
  - .planning/phases/01-pure-python-manet-simulator-engine/01-02-SUMMARY.md
  - .planning/phases/01-pure-python-manet-simulator-engine/01-03-SUMMARY.md
started: "2026-10-27T08:00:00Z"
updated: "2026-10-27T08:10:00Z"
---

# User Acceptance Testing (UAT) — Phase 01: Pure-Python MANET Simulator Engine

## Overview
Automated end-to-end verification of discrete-event simulator capabilities, Random Waypoint mobility, unit-disk radio model, RFC 3561 AODV routing protocol, and standard QoS metric computation.

---

## Tests

### 1. Pure-Python SimPy Discrete-Event Simulation Loop (SIM-01)
expected: simulator/run_scenario.py executes scenarios using discrete-event scheduling (simpy.Environment) without external C++ or NS-3 binaries on native Windows Python 3.11.
evidence: Executed SimulationRunner on scenarios/e1_normal_30n.json for 50s. Discrete-event clock processed all events cleanly with zero platform errors.
result: pass

### 2. Simulation Determinism Across Integer Seeds (AGENTS.md contract)
expected: Two consecutive runs with identical integer seed (e.g., seed 42) produce byte-for-byte identical trace files.
evidence: Generated traces/det_e1_run1.csv and traces/det_e1_run2.csv under seed 42. Computed SHA-256 digests (6ae9c6a82f8ed1240da9d1a7a99122390714b76d5bf5ab1379f4a0a6f34ed530) were 100% identical.
result: pass

### 3. Random Waypoint Mobility Model with Bounded Area (SIM-02)
expected: Mobile nodes dynamically transition between movement and pause intervals, with (x, y) coordinates staying bounded within the [0, 1000] x [0, 1000] simulation area.
evidence: Tested node trajectory across 100 simulated seconds; all node coordinates remained strictly in-bounds with periodic pauses.
result: pass

### 4. Dynamic Neighbor Discovery via Transmission Range (SIM-03)
expected: Dynamic 1-hop neighbor sets update dynamically according to unit-disk radio model (d <= 250m).
evidence: simulator.radio.get_neighbors correctly identified neighbor topology changes as nodes moved within and beyond range.
result: pass

### 5. RFC 3561 AODV Routing Protocol (SIM-04)
expected: Nodes dynamically discover multi-hop paths via RREQ floods, establish reverse/forward routes with sequence numbers via RREP, and maintain routes with timeout expiration.
evidence: Generated traces contain active RREQ, RREP, and RERR routing control packets propagating across multiple intermediate hops.
result: pass

### 6. CBR/UDP Application Traffic & Multi-Hop Delivery (SIM-05)
expected: CBR/UDP traffic source transmits packets that traverse multi-hop paths to destination nodes, delivering packets with positive delivery ratios.
evidence: In a 50s run on e1_normal_30n.json, 780 data packets were generated and 371 successfully delivered across multi-hop routes.
result: pass

### 7. Baseline QoS Metric Computation (SIM-05)
expected: simulator/metrics.py calculates Packet Delivery Ratio (PDR), throughput, end-to-end delay, packet loss ratio, and routing overhead.
evidence: Evaluated 50s trace: PDR = 47.56%, Throughput = 30.39 kbps, Delay = 2.98 ms, Packet Loss = 52.44%, Routing Overhead = 0.0449.
result: pass

---

## Summary

- **Total Tests:** 7
- **Passed:** 7
- **Issues:** 0
- **Final Verdict:** PASS
