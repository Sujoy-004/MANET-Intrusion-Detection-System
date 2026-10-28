# Phase 1: Pure-Python MANET Simulator Engine - Context

**Gathered:** 2026-10-25  
**Status:** Ready for planning

<domain>
Build a deterministic discrete-event simulator (SimPy + NetworkX) implementing Random Waypoint mobility, unit-disk radio with 1-hop neighbors, RFC 3561 AODV routing, and CBR/UDP traffic to produce baseline network metrics (PDR, throughput, delay, packet loss, routing overhead).
</domain>

<decisions>

### Simulation scale & topology
- **Node count/area:** Medium (30 nodes, 1000x1000m). Balance between realism and simulation speed.
- **Initial placement:** Configurable per scenario (random uniform, grid, clustered). Random uniform as default. Must be specified in scenario JSON for experiment flexibility.
- **Topology:** Dynamic via mobility; neighbors determined by radio range.

### Mobility configuration
- **Model:** Random Waypoint (RWP)
- **Speed:** Medium mobility (1-10 m/s)
- **Pause time:** 5s
- **Boundaries:** To be decided by implementer (reflect/wrap consistent with determinism). Keep simple and deterministic.

### Radio & connectivity
- **Range:** 250m (unit-disk model)
- **Loss:** Probabilistic loss within range (more realistic than perfect)
- **Neighbors:** 1-hop neighbors where d <= transmission range

### Traffic workload
- **Type:** CBR/UDP flows
- **Flows:** ~6 flows (You decide)
- **Sources/destinations:** Random S-D pairs (configurable)
- **Packet rate:** ~4 packets/s
- **Packet size:** ~512 bytes
- **Start times:** Staggered
- **Duration:** 300s simulation time

### AODV implementation details
- **Compliance:** Strict RFC 3561
- **Features:** RREQ flooding, RREP unicast, RERR route maintenance, sequence numbers, hop counts, route table with expiry
- **Focus:** Core behavior needed for Blackhole/Grayhole testing

### Trace logging format
- **Detail:** Full event log including routing messages (RREQ/RREP/RERR) and data packets
- **Columns:** time, src, dst, pkt_id, type, hop_count, dropped_by, ... (as specified in AGENTS.md)
- **Purpose:** All events needed for feature extraction

### Metrics collection
- **Approach:** Both end-to-end per-run aggregates and sliding windows
- **Overall metrics:** PDR, throughput, end-to-end delay, packet loss, routing overhead (for QoS comparison)
- **Windowed metrics:** For feature extraction in Phase 2

</decisions>

<specifics>
- Deterministic execution with explicit integer seed (--seed). Same seed => identical traces.
- SimPy 4.1.2 has no env.seed()/env.random - use random.Random(seed) threaded explicitly.
- Never iterate over sets where order matters - sort.
- simulator/ must not import attacks/ (attack injection in scenario runner).
- Traces written to traces/ (CSV), features derived from traces, labels from scenario config (not trace).
- Use pathlib.Path for Windows paths (spaces in repo path).
</specifics>

<canonical_refs>
- AGENTS.md (binding engineering contract - precedence)
- MANET_IDS_BTech_Execution_Guide.md (project spec)
- .planning/PROJECT.md
- .planning/REQUIREMENTS.md (SIM-01..SIM-05)
- .planning/ROADMAP.md (Phase 1)
- .planning/codebase/STACK.md
- .planning/codebase/STRUCTURE.md
- .planning/codebase/CONVENTIONS.md
- RFC 3561 (AODV) - for strict implementation
</canonical_refs>

<code_context>
**Reusable patterns from codebase analysis:**
- Stack: Python 3.11.8, SimPy 4.1.2, NetworkX 3.6.1, pandas 3.0.2, scikit-learn 1.8.0
- Layout: simulator/ with mobility.py, radio.py, aodv.py, traffic.py, metrics.py, run_scenario.py
- Constraints: Windows-native, no C++, no NS-3, deterministic with seeds
- Import boundary: simulator/ must not import attacks/
- CLI: python -m simulator.run_scenario --scenario <json> --seed <int> --out <dir>

**New files needed:**
- simulator/__init__.py
- simulator/mobility.py (Random Waypoint)
- simulator/radio.py (unit-disk, neighbors, probabilistic loss)
- simulator/aodv.py (RFC 3561 - RREQ/RREP/RERR, seq nos, route table)
- simulator/traffic.py (CBR/UDP flows)
- simulator/metrics.py (PDR, throughput, delay, loss, overhead, windowing)
- simulator/run_scenario.py (CLI runner, composition root)
- scenarios/e1_normal_30n.json (baseline scenario)
</code_context>

<deferred_ideas>
- Different mobility models (Gauss-Markov, Manhattan) - defer to later if needed
- More complex radio propagation (shadowing/fading) - unit-disk + prob loss is sufficient
- Other traffic patterns (TCP-like) - CBR/UDP is fine
- Energy models - out of scope
</deferred_ideas>
