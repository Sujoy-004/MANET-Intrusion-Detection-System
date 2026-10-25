# Phase 1: Pure-Python MANET Simulator Engine - Research

**Researched:** 2026-10-25  
**Domain:** Discrete-event MANET simulation (SimPy + NetworkX, Random Waypoint, unit-disk radio, RFC 3561 AODV, CBR/UDP)  
**Confidence:** HIGH  

## Summary

Phase 1 requires a deterministic, pure-Python discrete-event simulator replacing NS-3. The architecture uses SimPy 4.1.2 for event scheduling, NetworkX 3.6.1 for topology/neighbor analysis, and stdlib `random.Random` for all stochasticity. Core components follow the prescribed layout: `mobility.py`, `radio.py`, `aodv.py`, `traffic.py`, `metrics.py`, `run_scenario.py`. The simulator must remain attack-agnostic (never import `attacks/`), produce CSV traces with fixed schema, and be fully reproducible with explicit integer seeds. RFC 3561 AODV is the routing core with sequence numbers, route table expiry, RREQ/RREP/RERR. 

**Primary recommendation:** Build in strict module order (`mobility -> radio -> aodv -> traffic -> metrics`), thread a single `random.Random(seed)` through all stochastic components, use SimPy `Environment`/processes/events, never rely on `env.seed()`/`env.random` (absent in 4.1.2), enforce sorted iteration over sets, and log every packet event to CSV for traceability.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Node count/area:** Medium (30 nodes, 1000x1000m). Balance realism and speed.
- **Initial placement:** Configurable per scenario (random uniform, grid, clustered). Random uniform as default. Must be specified in scenario JSON.
- **Topology:** Dynamic via mobility; neighbors determined by radio range.
- **Mobility:** Random Waypoint (RWP), speed 1-10 m/s, pause time 5s, boundaries to be decided by implementer (reflect/wrap consistent with determinism).
- **Radio:** Range 250m (unit-disk), probabilistic loss within range, neighbors are 1-hop where d <= transmission range.
- **Traffic:** CBR/UDP flows, ~6 flows, random S-D pairs (configurable), ~4 packets/s, ~512 bytes, staggered start times, 300s simulation time.
- **AODV:** Strict RFC 3561, core features needed for Blackhole/Grayhole testing (RREQ flooding, RREP unicast, RERR route maintenance, sequence numbers, hop counts, route table with expiry).
- **Trace logging:** Full event log including routing messages and data packets; columns include `time, src, dst, pkt_id, type, hop_count, dropped_by, ...` as specified in AGENTS.md.
- **Metrics:** Both end-to-end aggregates and sliding windows; overall: PDR, throughput, end-to-end delay, packet loss, routing overhead.

### the agent's Discretion
- **Boundaries:** RWP boundary handling (reflect/wrap) — keep simple and deterministic.
- **Exact flow counts/timings:** ~6 flows, ~4 pps, staggered starts (can be tuned within reason).
- **Routing table timers:** Choose reasonable RFC 3561-aligned expiry values consistent with testing needs.
- **Probabilistic loss model:** Within-range loss probability (implementer chooses deterministic form tied to seed).

### Deferred Ideas
- Different mobility models (Gauss-Markov, Manhattan) — defer
- More complex radio propagation (shadowing/fading) — unit-disk + prob loss sufficient
- Other traffic patterns (TCP-like) — CBR/UDP fine
- Energy models — out of scope

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Discrete-event scheduling | API/Backend (simulator core) | — | SimPy Environment drives all time-ordered events |
| Node mobility/state | API/Backend (mobility/radio) | — | Coordinates/timings computed in-process, affects topology |
| Wireless connectivity | API/Backend (radio) | — | Euclidean distance + range/loss determines neighbor graph |
| Routing (AODV) | API/Backend (aodv) | — | Multi-hop route discovery/maintenance per RFC 3561 |
| Traffic generation | API/Backend (traffic) | — | CBR/UDP flows generate data packets into network |
| Metrics/trace logging | API/Backend (metrics/run_scenario) | — | Aggregate and log all events for feature extraction |
| Attack injection | API/Backend (attacks/ injected by runner) | — | Decoupled via flags; simulator remains agnostic |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| [python](https://www.python.org/) | 3.11.8 | Runtime | Windows-native, pure Python per constraints |
| [simpy](https://simpy.readthedocs.io/) | 4.1.2 | Discrete-event simulation | Environment/processes/events, simple and deterministic when seeded externally |
| [networkx](https://networkx.org/) | 3.6.1 | Graph structures/analysis | Topology, neighbor sets, route graphs |
| [numpy](https://numpy.org/) | 1.26.4 | Numerical utilities | Vector ops if needed (note numpy 2 not used) |
| [pandas](https://pandas.pydata.org/) | 3.0.2 | Data handling | Trace/metrics processing; aware of CoW/`map` changes |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| [scipy](https://scipy.org/) | 1.17.1 | Optional utilities | Only if specific functions needed; not central to core sim |
| [matplotlib](https://matplotlib.org/) | 3.10.8 | Plotting (later phases) | For results/plots; set `Agg` backend if headless |
| [seaborn](https://seaborn.pydata.org/) | 0.13.2 | Plotting (later phases) | Statistical viz |

**Installation:**
```bash
pip install -r requirements.txt  # with pins as specified
```

**Version verification:** Use `pip show <pkg>` or `python -c "import <pkg>; print(<pkg>.__version__)"`. Environment already has these versions installed.

## Package Legitimacy Audit
> Not applicable for this phase — no new external packages being introduced beyond already verified stack in environment. All dependencies are standard, pure-Python where needed, Windows-safe.

## Architecture Patterns

### System Architecture Diagram
```
[Scenario JSON] 
  -> run_scenario.py (composition root, seeds random.Random)
    -> mobility (RWP) updates positions over time
    -> radio (unit-disk + prob loss) builds neighbor graph
    -> aodv (RFC 3561) handles RREQ/RREP/RERR, route tables
    -> traffic (CBR/UDP) generates data packets
    -> metrics/trace logger records events to CSV
[traces/*.csv] -> (Phase 2 feature extraction)
```

Data flow: scenario config + seed -> deterministic SimPy env processes -> packet events logged with full routing/data info -> traces written to `traces/`.

### Recommended Project Structure
```
simulator/
├── __init__.py
├── mobility.py      # Random Waypoint
├── radio.py         # unit-disk, neighbors, probabilistic loss
├── aodv.py          # RFC 3561 engine
├── traffic.py       # CBR/UDP flows
├── metrics.py       # PDR/throughput/delay/loss/overhead, windowing
├── run_scenario.py  # CLI + composition root
└── tests/
    ├── __init__.py
    └── test_aodv.py  # (and others as needed)
```

### Pattern 1: Deterministic Simulation with SimPy
**What:** Use `simpy.Environment()`, schedule processes via `env.process()`, yield `env.timeout()` for delays. Do **not** use `env.seed()` or `env.random` (not present in SimPy 4.1.2).  
**When to use:** Always for this project.  
**Example:**
```python
import random
import simpy

def main(seed):
    rng = random.Random(seed)
    env = simpy.Environment()
    # pass rng to all components that need randomness
    ...
    env.run(until=300.0)
```
Source: SimPy docs (core concepts) [CITED: simpy.readthedocs.io/en/latest/simpy_intro/index.html]

### Pattern 2: Random Waypoint Mobility
**What:** Nodes choose random destination in area, random speed in [v_min, v_max], move at constant speed, pause at destination for pause_time, repeat. Handle boundaries (wrap or reflect) deterministically.  
**When to use:** As specified.  
**Example sketch:**
```python
# for each node: pick (x1,y1), speed, pause; compute travel time; 
# at arrival yield pause, then repeat
```
Notes: Initial positions uniform/random per scenario config; track `mobility_speed` feature source.

### Pattern 3: Unit-Disk Radio + Neighbor Discovery
**What:** For each time step/update, compute Euclidean distance d between all pairs; neighbor if d <= R. Apply probabilistic loss within range (e.g. Bernoulli(p_loss) per transmission event) to affect delivery, not just connectivity.  
**When to use:** Always.  
**Example:**
```python
import math
d = math.hypot(x2-x1,y2-y1)
if d <= R and rng.random() > loss_p: connected
```

### Pattern 4: RFC 3561 AODV (core)
**What:** Maintain route table entries (dest, next_hop, hop_count, seq_num, lifetime/expiry). RREQ broadcast with sequence numbers, RREP unicast back, RERR on link break. Route discovery on demand.  
**When to use:** Core routing.  
**Key points:** increment own sequence numbers appropriately; use sequence numbers to avoid old routes; expire entries; handle intermediate nodes forwarding RREQ/RREP; record routing message rates for features.  
**Reference:** RFC 3561 [CITED: https://www.rfc-editor.org/rfc/rfc3561]

### Pattern 5: CBR/UDP Traffic
**What:** Generate constant bit rate flows as UDP packets between random S-D pairs, staggered start, fixed packet size/rate for duration.  
**When to use:** As specified.  
**Example:**
```python
# schedule flow: at start_t send packet every 1/rate for flow_duration
```

### Pattern 6: Trace Logging
**What:** Log every event (routing control messages RREQ/RREP/RERR and data packets) with columns `time, src, dst, pkt_id, type, hop_count, dropped_by, ...`. Write CSV to `traces/`. Labels come from scenario config, not trace.  
**When to use:** Always.  
**Notes:** Ensure deterministic ordering when iterating structures (sort lists/sets). Include enough fields for sliding-window feature extraction later.

### Anti-Patterns to Avoid
- **Using SimPy's random:** SimPy 4.1.2 has no `env.seed()`/`env.random` — must pass `random.Random(seed)`.
- **Set iteration order:** Never iterate over Python sets where order affects outcomes; sort keys.
- **Simulator importing attacks:** `simulator/` must not import `attacks/` (injection via scenario runner only).
- **Leakage in traces/labels:** Labels from scenario config only; no attacker identity in trace fields used as features.
- **Random row split later:** Design traces/features so grouping by run is easy (use `run_id` convention).
- **Non-deterministic I/O order:** Write traces in deterministic event order.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Discrete-event scheduling | Custom event heap/timer loop | SimPy Environment | Correct, tested, simple API |
| Graph algorithms/topology | Ad-hoc adjacency structures | NetworkX | Easy neighbor sets, path queries, analysis |
| Random number generation | `random` without control | `random.Random(seed)` threaded explicitly | Determinism critical |
| CSV writing | Manual string formatting | `csv` module or `pandas` | Robust, handles quoting |
| Distance calcs | Reimplement carefully | `math.hypot`/stdlib | Simple and clear |

**Key insight:** Focus implementation effort on AODV correctness and determinism; leverage SimPy/NetworkX/stdlib for infrastructure.

## Runtime State Inventory
> Omit entirely (greenfield phase, no rename/refactor/migration).

## Common Pitfalls

### Pitfall 1: Non-determinism from SimPy/random
**What goes wrong:** Runs give different traces with same seed.  
**Why it happens:** Using global `random` or iterating unordered collections.  
**How to avoid:** Create single `random.Random(seed)`, pass to all components; sort all iteration order (node lists, neighbor lists).  
**Warning signs:** Different packet order/timings across runs.

### Pitfall 2: Incorrect AODV sequence numbers/route freshness
**What goes wrong:** Routes not updated properly, stale routes used.  
**Why it happens:** Not handling seq nums per RFC 3561 (destination seq nums, incrementing own).  
**How to avoid:** Follow RFC carefully for RREQ/RREP generation and route table updates (only accept fresher routes).  
**Warning signs:** Routes persist when topology changes, or fail to discover new paths.

### Pitfall 3: RERR/route maintenance gaps
**What goes wrong:** Packets dropped after link break with no recovery.  
**Why it happens:** Not detecting link failures or not sending RERR.  
**How to avoid:** Implement basic link break detection (e.g. failed forwarding) and RERR propagation as needed for core behavior.  
**Warning signs:** PDR collapses after mobility changes.

### Pitfall 4: Timing/processing order in SimPy
**What goes wrong:** Events processed in unexpected order causing race conditions.  
**Why it happens:** Improper process yields/scheduling.  
**How to avoid:** Model packet transmission/propagation with appropriate timeouts/delays; be explicit about event ordering.  
**Warning signs:** Inconsistent results between runs.

### Pitfall 5: Trace schema drift
**What goes wrong:** Feature extraction breaks later.  
**Why it happens:** Missing columns or different naming.  
**How to avoid:** Fix trace columns to `time, src, dst, pkt_id, type, hop_count, dropped_by, ...` and write consistently.  
**Warning signs:** Column mismatches in Phase 2.

### Pitfall 6: Simulator importing attacks
**What goes wrong:** Tight coupling, breaks attack-agnostic requirement.  
**Why it happens:** Importing `attacks/` in simulator modules.  
**How to avoid:** Only `run_scenario.py` may import `attacks/`; use behavior flags injected into nodes.  
**Warning signs:** Import errors or architectural violation.

## Code Examples

### SimPy basic pattern (deterministic)
```python
import random
import simpy

class Node:
    def __init__(self, env, node_id, rng, pos):
        self.env = env
        self.id = node_id
        self.rng = rng
        self.pos = pos
        self.process = env.process(self.run())

    def run(self):
        while True:
            # do something
            yield self.env.timeout(1.0)

def main(scenario, seed, out_dir):
    rng = random.Random(seed)
    env = simpy.Environment()
    nodes = [Node(env, i, rng, initial_pos(i, scenario, rng)) for i in range(scenario['nodes'])]
    env.run(until=scenario['duration'])
```
Source: SimPy 4.x patterns [CITED: simpy.readthedocs.io]

### Random Waypoint sketch
```python
def waypoint_process(env, node, area, vmin, vmax, pause, rng):
    while True:
        x0,y0 = node.pos
        x1 = rng.uniform(0, area[0]); y1 = rng.uniform(0, area[1])
        dx,dy = x1-x0,y1-y0
        dist = (dx*dx+dy*dy)**0.5
        if dist == 0:
            speed = 0
        else:
            speed = rng.uniform(vmin,vmax)
        travel = dist/speed if speed>0 else 0
        # move over time or jump with events; simpler: update at waypoints with travel time
        yield env.timeout(travel)
        node.pos = (x1,y1)
        yield env.timeout(pause)
```
(Note: implement deterministic boundary handling as decided.)

### AODV route table entry (concept)
```python
@dataclass
class RouteEntry:
    dest: int
    next_hop: int
    hop_count: int
    dest_seq: int
    lifetime: float  # env.now + expiry
```

### Trace row structure
```python
# columns: time, src, dst, pkt_id, type, hop_count, dropped_by, ...
# type in {rreq,rrep,rerr,data}
row = {'time': env.now, 'src': s, 'dst': d, 'pkt_id': pid, 'type': 'data', 'hop_count': h, 'dropped_by': -1}
```

## State of the Art
| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| NS-3 (C++) | Pure-Python SimPy | Project decision (AGENTS.md) | Windows-native, no toolchain, easier to integrate with ML |
| ad-hoc C++ routing | RFC 3561 in Python | Standard | Familiar, testable for attacks |

**Deprecated/outdated:**
- Relying on external NS-3 installs — explicitly dropped per constraints.

## Assumptions Log

> All claims tagged `[ASSUMED]` in this research. The planner and discuss-phase use this section to identify decisions that need user confirmation before execution.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Boundary handling for RWP (reflect/wrap) — implementer chooses simple deterministic approach | User Constraints/Discretion | Different boundary behavior affects topology/connectivity; need consistency across runs |
| A2 | Probabilistic loss model within range (exact distribution/form) not fully specified | Radio & connectivity/Discretion | Affects PDR/loss metrics; must be deterministic and documented |
| A3 | Specific RFC 3561 timer values (route lifetime, RREQ retry, etc.) not pinned | AODV implementation/Discretion | Timing affects route discovery/expiry behavior; must be reasonable and consistent |
| A4 | Exact flow generation details beyond ranges (~6 flows, 4 pps) not fully specified | Traffic workload/Discretion | Affects traffic load; scenario JSON must control precisely |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions

1. **RWP boundaries**
   - What we know: Must be deterministic (reflect/wrap). Discretion to implementer.
   - What's unclear: Preferred approach for this project.
   - Recommendation: Implement reflect or wrap consistently; document choice in code/comments and ensure determinism.

2. **Probabilistic loss**
   - What we know: Probabilistic loss within transmission range.
   - What's unclear: Loss probability/value/model.
   - Recommendation: Make configurable per scenario or use fixed small probability; tie to rng for determinism.

3. **AODV timers**
   - What we know: Need expiry, core behaviors.
   - What's unclear: Exact timer constants.
   - Recommendation: Use RFC 3561 reasonable defaults (e.g. ACTIVE_ROUTE_TIMEOUT, DELETE_PERIOD) and document.

## Environment Availability

> Skip this section if the phase has no external dependencies (code/config-only changes).
> Not skipped — uses SimPy/NetworkX/numpy/pandas/scikit-learn already installed.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.11.8 | — |
| SimPy | Discrete-event sim | ✓ | 4.1.2 | — |
| NetworkX | Topology/graphs | ✓ | 3.6.1 | — |
| numpy | Numerics | ✓ | 1.26.4 | — |
| pandas | Data/CSV | ✓ | 3.0.2 | — |
| scipy | Utils | ✓ | 1.17.1 | — |
| scikit-learn | Later phases | ✓ | 1.8.0 | — |
| matplotlib/seaborn | Plotting later | ✓ | 3.10.8/0.13.2 | — |

**Missing dependencies with no fallback:** None.  
**Missing dependencies with fallback:** None.

## Validation Architecture

> Skip this section entirely if workflow.nyquist_validation is explicitly set to false in .planning/config.json. If the key is absent, treat as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (recommended) |
| Config file | none — see Wave 0 |
| Quick run command | `pytest simulator/tests/ -v` |
| Full suite command | `pytest -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SIM-01 | Deterministic discrete-event clock with explicit seeds | unit/integration | `pytest simulator/tests/test_determinism.py -v` | ❌ Wave 0 |
| SIM-02 | Random Waypoint mobility in bounded area | unit | `pytest simulator/tests/test_mobility.py -v` | ❌ Wave 0 |
| SIM-03 | Unit-disk radio + dynamic 1-hop neighbor sets | unit | `pytest simulator/tests/test_radio.py -v` | ❌ Wave 0 |
| SIM-04 | RFC 3561 AODV (RREQ/RREP/RERR, seq nos, route table/expiry) | integration | `pytest simulator/tests/test_aodv.py -v` | ❌ Wave 0 |
| SIM-05 | CBR/UDP traffic flows with measurable PDR/throughput | integration | `pytest simulator/tests/test_traffic_metrics.py -v` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest simulator/tests/ -v`
- **Per wave merge:** `pytest -v`
- **Phase gate:** Full suite green before marking phase complete

### Wave 0 Gaps
- [ ] `simulator/tests/test_determinism.py` — same seed => identical traces
- [ ] `simulator/tests/test_mobility.py` — positions stay in bounds, RWP behavior
- [ ] `simulator/tests/test_radio.py` — neighbor sets by distance/range/loss
- [ ] `simulator/tests/test_aodv.py` — route discovery/maintenance basics
- [ ] `simulator/tests/test_traffic_metrics.py` — flow delivery and metrics
- [ ] `simulator/tests/__init__.py` — test package setup
- [ ] Framework install: ensure pytest available (add if needed)

*(Note: tests live inside owning packages per structure conventions.)*

## Security Domain

> Required when `security_enforcement` is enabled (absent = enabled). Omit only if explicitly `false` in config.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A (simulation, no auth) |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | yes | Validate scenario JSON schema; sanitize paths (use pathlib.Path) |
| V6 Cryptography | no | N/A |

### Known Threat Patterns for {stack}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via scenario/out paths | Tampering | Use `pathlib.Path.resolve()` and validate under repo boundaries |
| Malformed scenario JSON | Tampering/DoS | JSON schema validation, type checks, defaults |
| Resource exhaustion (large runs) | DoS | Reasonable defaults (30 nodes, 300s) as per context |

## Sources

### Primary (HIGH confidence)
- [SimPy Documentation](https://simpy.readthedocs.io/) - Environment/processes/events, core concepts
- [RFC 3561 - Ad hoc On-Demand Distance Vector (AODV) Routing](https://www.rfc-editor.org/rfc/rfc3561) - Routing protocol specification
- [NetworkX Documentation](https://networkx.org/documentation/) - Graph structures
- AGENTS.md (binding contract) - Architecture, constraints, rules
- .planning/phases/01-pure-python-manet-simulator-engine/01-CONTEXT.md - Locked decisions

### Secondary (MEDIUM confidence)
- [Random Waypoint Model](https://en.wikipedia.org/wiki/Random_waypoint_model) - Standard mobility model description
- [MANET_IDS_BTech_Execution_Guide.md](../../MANET_IDS_BTech_Execution_Guide.md) - Project specification

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Verified versions from environment and project constraints
- Architecture: HIGH - Follows prescribed layout and patterns from codebase analysis
- Pitfalls: HIGH - Common issues for SimPy/AODV/determinism well-known

**Research date:** 2026-10-25  
**Valid until:** 2026-11-24 (30 days for stable stack)
