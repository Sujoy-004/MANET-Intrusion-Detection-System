# Changelog

All notable changes to the Machine Learning-Based Intrusion Detection System for MANET will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-03

### Added
- **AODV Route Discovery Recovery Lifecycle:** Per-destination route discovery state machine (`DiscoveryState`) in `simulator/aodv.py` supporting:
  - Initial wait timeout (`DEFAULT_RREQ_TIMEOUT = 2.0s`).
  - Bounded retries (`DEFAULT_RREQ_RETRIES = 2`, representing 3 total discovery attempts).
  - Exponential backoff multiplier (`DEFAULT_BACKOFF_MULT = 2.0`, scaling timeouts: 2s -> 4s -> 8s; no separate `MAX_RREQ_TIMEOUT` constant).
  - Discovery cooldown period (`DEFAULT_DISCOVERY_COOLDOWN = 2.0s`) after retry exhaustion to suppress RREQ broadcast storms.
- **Timer-Generation Token Protection:** Generation token tracking (`timer_token`) for SimPy discovery timeout callbacks, ensuring stale or late RREP callbacks do not interfere with subsequent route discovery cycles.
- **Bounded Packet Buffering & TTL:** Enforced per-destination queue limit (`DEFAULT_MAX_BUFFER_PER_DEST = 100` packets) and packet Time-To-Live expiration (`DEFAULT_MAX_BUFFER_TIME = 20.0s`) to prevent unbounded memory growth during persistent topological partitions.
- **Quarantine Local Egress Guard:** Explicit self-blacklisting check in `handle_rreq()` preventing quarantined nodes from locally constructing or transmitting RREPs.
- **Dedicated Recovery Test Suite:** 10 new unit and integration tests in `tests/test_aodv_recovery.py` covering timeout backoff, cooldown, partition recovery, queue limits, late RREPs, quarantine egress guards, and storm elimination (bringing test suite total to 79 passed tests).

### Changed
- **AODV Buffer Flushing Semantics:** Buffered packets are released only when a valid, non-blacklisted route is confirmed installed; rejected blacklisted RREPs no longer clear legitimate pending discovery state.
- **Documentation & Benchmark Provenance:** Updated `README.md`, `docs/ARCHITECTURE.md`, `docs/CONFIGURATION.md`, `docs/GETTING-STARTED.md`, `docs/TESTING.md`, `docs/DEVELOPMENT.md`, `docs/FINAL_PROJECT_REPORT.md`, and `results/closed_loop_report.md` to reflect:
  - Verified 300-second Seed-42 reference benchmark:
    - Baseline Normal: PDR 65.88% (4,098 / 6,220), throughput 55.95 kbps, delay 134.74 ms across 4,098 delivered packets, overhead 0.0950.
    - Blackhole Attack: PDR 18.10% (1,126 / 6,220), throughput 15.37 kbps, delay 138.66 ms across 1,126 delivered packets, overhead 0.1055.
    - Blackhole + IDS: PDR 62.93% (3,914 / 6,220), throughput 53.44 kbps, delay 102.29 ms across 3,914 delivered packets, overhead 0.1302.
    - Net Restoration: 95.51% baseline delivery restored (3,914 / 4,098 packets), +44.82 percentage points absolute PDR improvement over attack.
    - Delay Interpretation: Clarified that delay is computed exclusively over successfully delivered packets; removed unsupported causal latency claims.
  - Total automated test count updated from 69 to 79 across 11 test modules.

### Fixed
- **Permanent Route Discovery Stalls:** Resolved issue where flows experiencing initial unreplied RREQs during temporary topological partitions permanently retained stale pending state without retrying.
- **Blacklisted RREP Storm Loop:** Eliminated scenario runner loop where rejected blacklisted RREPs repeatedly cleared pending discovery state and flushed unrouted buffers, previously generating over 16,000 rogue control packets.
- **Quarantined Node RREP Generation:** Silenced quarantined nodes from generating and transmitting local RREPs when receiving RREQs destined to themselves.

## [1.0.0] - 2026-10-28

### Added
- Pure-Python discrete-event MANET simulator (SimPy 4.1.2 + NetworkX 3.6.1) implementing RFC 3561 AODV routing and Random Waypoint mobility.
- Decoupled adversarial strategies: Blackhole (sequence spoofing and unconditional drop) and Grayhole (probabilistic/selective drop).
- Non-leaking 10-column sliding-window feature extractor.
- Cost-sensitive Scikit-learn classification pipeline (Random Forest champion, FPR <= 1.0% operational gate).
- Closed-loop `OnlineIDS` controller with 2-strike confirmation and dynamic route invalidation (`invalidate_routes_through`).
- Initial automated test suite and publication-grade visualization suite.
