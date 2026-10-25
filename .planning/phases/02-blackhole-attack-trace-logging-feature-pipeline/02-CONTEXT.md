# Phase 02: Blackhole Attack, Trace Logging & Feature Pipeline - Context

**Gathered:** 2026-10-25  
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers controlled adversarial routing behavior (Blackhole attack), structured packet-level event trace logging to CSV, and a sliding-window feature extractor generating non-leaking tabular behavioral datasets for ML intrusion detection. It also establishes the automated Gate 2 verification benchmark proving the attack demonstrably degrades network QoS prior to model training.
</domain>

<decisions>
## Implementation Decisions

### Attacker Placement & Strategy
- **D-01:** Dynamic flow-intercept placement — The scenario runner dynamically identifies and selects an intermediate node situated along the multi-hop forwarding path between active CBR flows to guarantee the Blackhole attacker intercepts legitimate traffic. - **Reversibility:** costly - downstream scenario configs and trace generators expect dynamic intermediate node selection or explicit fallback mapping.
- **D-02:** Configurable spoofed RREP parameters — Scenario JSON specifies custom sequence number bump offset (e.g., +500 to +10000, setting `dest_seq = max(known_seq, rreq.dest_seq) + offset`) and advertised hop count (default 1) so attack aggressiveness is tunable per experiment. - **Reversibility:** reversible
- **D-03:** Silent intercepted data drop — The Blackhole attacker drops 100% of intercepted `DATA` packets while participating aggressively in RREQ/RREP route discovery to attract traffic into the hole. - **Reversibility:** reversible

### Sliding-Window Aggregation & Timing
- **D-04:** Fine-grained sliding window — Default window duration $W = 5.0\text{s}$ with sliding step $\Delta t = 1.0\text{s}$ to produce high sample density for ML training while capturing transient behavioral dynamics. - **Reversibility:** costly - affects the size and sample distribution of all downstream feature datasets.
- **D-05:** Warmup and idle node filtering — Include all simulation windows starting from $t = 0.0\text{s}$, with a configurable `--warmup` flag (default 10.0s to allow initial route discovery settling) and a configurable `--min-packets` threshold filter to exclude uninformative, zero-traffic periods. - **Reversibility:** reversible

### Feature Extraction Calculation & Schema
- **D-06:** Embedded periodic `NODE_STATUS` events in trace — The simulator logs periodic `NODE_STATUS` events directly into the packet trace CSV recording `time, node_id, mobility_speed, neighbor_count`. This keeps traces completely self-contained without needing out-of-band state files. - **Reversibility:** costly - modifies trace CSV parser and feature extractor input format.
- **D-07:** Neutral baseline forward ratio for zero-traffic nodes — If a node receives 0 packets to forward within a window, assign `packet_forward_ratio = 1.0` and `packet_drop_ratio = 0.0` to prevent division-by-zero errors and avoid falsely accusing inactive nodes. - **Reversibility:** reversible
- **D-08:** Non-leaking tabular schema — Exactly 10 columns: `packet_forward_ratio`, `packet_drop_ratio`, `avg_delay`, `route_request_rate`, `route_reply_rate`, `throughput`, `hop_count`, `neighbor_count`, `mobility_speed`, `label`. Ground truth labels (`Normal` vs `Blackhole`) are applied from scenario metadata, with zero attacker IDs or direct oracle indicators in the feature matrix $X$. - **Reversibility:** one-way - binding contract for Phase 3 ML pipelines.

### Attack Impact Verification Gate (Gate 2)
- **D-09:** Quantitative impact threshold — Require a relative Packet Delivery Ratio (PDR) drop of at least 25% under Blackhole attack compared to plain baseline AODV under the same integer seed. - **Reversibility:** costly - hard gate before proceeding to ML training.
- **D-10:** Dedicated multi-seed verification script — Automated benchmark script running 3 paired seeds (42, 43, 44) for baseline vs blackhole, generating a comparative QoS table (PDR, throughput, delay, routing overhead), and asserting the $\ge 25\%$ PDR degradation. - **Reversibility:** reversible

### the agent's Discretion
- CLI argument names and defaults for the feature extractor (e.g. `python -m feature_extraction.extract_features --trace <csv> --scenario <json> --out <csv> --window 5.0 --step 1.0 --warmup 10.0`).
- Internal implementation details of `attacks/` package (e.g. `attacks/blackhole.py` implementing `BlackholeStrategy`) decoupled from `simulator/`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engineering Contract & Specification
- `AGENTS.md` - Binding engineering contract (Windows-native Python, determinism, decoupled attacks, anti-leakage, Gate 2)
- `MANET_IDS_BTech_Execution_Guide.md` - Execution guide (Module B, Module C, feature schema table, Gate 2 criteria)
- `.planning/PROJECT.md` - Core value and requirements
- `.planning/REQUIREMENTS.md` - Requirements ATK-01, ATK-03, DATA-01, DATA-02, DATA-03
- `.planning/ROADMAP.md` - Phase 2 scope and success criteria
- `.planning/phases/01-pure-python-manet-simulator-engine/01-VERIFICATION.md` - Phase 1 baseline verification report
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `simulator/aodv.py` - Core AODV protocol implementation (`AODVNode`, `RouteEntry`, `RREQ`, `RREP`, `RERR`)
- `simulator/run_scenario.py` - CLI scenario runner with SimPy environment and trace logging
- `simulator/metrics.py` - QoS calculation module (`compute_pdr`, `compute_throughput`, `compute_delay`)
- `scenarios/e1_normal_30n.json` - Baseline 30-node normal scenario config

### Established Patterns
- Pure Python SimPy 4.1.2 discrete-event clock
- Explicit integer seed threading via `random.Random(seed)`
- Windows-safe `pathlib.Path` handling
- Vectorized Pandas metric computation
- Clean decoupled architecture: `simulator/` must never import `attacks/`

### Integration Points
- `attacks/blackhole.py` will define `BlackholeBehavior` / `BlackholeStrategy`
- `simulator/run_scenario.py` injects attack behavior at node initialization
- `feature_extraction/` parses CSV traces generated by `simulator/run_scenario.py`
</code_context>

<specifics>
## Specific Ideas

- Blackhole node dynamically placed along active CBR flow path to guarantee interception.
- Spoofed RREP sequence offset configurable in scenario JSON (default +1000).
- 5-second window, 1-second step for sliding-window dataset extraction.
- Periodic `NODE_STATUS` events logged into trace CSV for self-contained topology metrics.
- Gate 2 verification script asserts $\ge 25\%$ PDR drop across seeds 42, 43, 44.
</specifics>

<deferred>
## Deferred Ideas

- Grayhole attack implementation (scheduled for Phase 4)
- Machine learning classification pipeline (scheduled for Phase 3)
- Dynamic closed-loop routing mitigation (scheduled for Phase 5)
</deferred>

---

*Phase: 02-Blackhole Attack, Trace Logging & Feature Pipeline*  
*Context gathered: 2026-10-25*
