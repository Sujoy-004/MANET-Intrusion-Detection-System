# Phase 02 Plan 01 Summary: Decoupled Blackhole Attack Strategy & Dynamic Placement Engine

## Overview
Implemented the decoupled RFC 3561 Blackhole attack strategy and the dynamic flow-intercept attacker placement algorithm. The core simulator remains completely attack-agnostic (satisfying ATK-03), while the composition root dynamically identifies intermediate nodes across multi-hop CBR flows to inject adversarial RREP spoofing and silent data drops (satisfying ATK-01).

## Implementation Details
1. **Decoupled Strategy Package (`attacks/`):**
   - `attacks/base.py`: Defines `AttackStrategy(ABC)` with `get_spoofed_rrep_params` and `should_drop_data`.
   - `attacks/blackhole.py`: Implements `BlackholeStrategy` generating spoofed sequence numbers (`rreq_dest_seq + seq_offset`) and 1-hop distance advertisement, along with silent data dropping.
   - `attacks/registry.py`: Factory method `create_attack_strategy` to instantiate attacks by name without circular dependencies.
   - `attacks/__init__.py`: Package export.

2. **Duck-Typed Hook on `AODVNode` (`simulator/aodv.py`):**
   - Added `attack_behavior: Optional[Any] = None` attribute.
   - Intercepts RREQ messages at intermediate malicious nodes to unicast spoofed RREP with high sequence numbers back to originators without forwarding broadcast RREQs.

3. **Dynamic Flow-Intercept Placement & Composition Root (`simulator/run_scenario.py`):**
   - Added `select_dynamic_attacker(flows)` analyzing the initial NetworkX connectivity graph and active CBR flow paths to select intermediate nodes while strictly excluding flow endpoints.
   - Added attack configuration handling in `initialize_nodes` connecting `create_attack_strategy` to target AODV nodes.
   - Added intercepted data packet drop logic in `_route_and_forward_data` logging `DATA_DROP` events with `dropped_by`.

4. **Scenario Configuration (`scenarios/e2_blackhole_30n.json`):**
   - Created 30-node scenario mirroring `e1_normal_30n.json` with dynamic Blackhole attack enabled (`seq_offset=1000`, `spoofed_hops=1`).

5. **Architectural & Unit Test Suite (`tests/`):**
   - `tests/test_attacks_blackhole.py`: Tests strategy mechanics, parameter spoofing, dropping decisions, and factory creation.
   - `tests/test_import_boundaries.py`: AST parsing tests ensuring `simulator/` core modules never import `attacks/` directly.

## Verification
- Unit & boundary tests: `python -m pytest tests/test_attacks_blackhole.py tests/test_import_boundaries.py -v` (9 passed in 0.07s).
- Simulation benchmark: `python -m simulator.run_scenario --scenario scenarios/e2_blackhole_30n.json --seed 42 --out traces/test_blackhole.csv`
  - Packets Sent: 6220, Received: 210
  - PDR: 3.38% (drastic reduction from baseline ~80-90%)
  - Packet Loss Ratio: 96.62%
  - Trace verified: Abundant `DATA_DROP` events logged by malicious node 21.
