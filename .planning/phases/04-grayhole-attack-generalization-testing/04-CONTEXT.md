# Phase 04: Grayhole Attack & Generalization Testing - Context

**Gathered:** 2026-10-27  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 04 expands the adversarial scope of the MANET IDS by implementing the decoupled Grayhole attack (selective/probabilistic payload dropping with honest control routing), verifying behavioral observability across subtle drop ratios, and benchmarking detector generalization across multi-scenario variations (mobility speeds, drop probabilities, and network densities) while preserving the locked $\text{FPR} \le 1.0\%$ acceptance gate.

</domain>

<decisions>
## Implementation Decisions

### 1. Grayhole Attack Strategy & AODV Routing Behavior
- **D-01:** Implement `GrayholeStrategy` extending `AttackStrategyBase` in `attacks/grayhole.py`. Unlike Blackhole, Grayhole participates honestly in AODV route discovery—it forwards RREQs, emits honest RREPs (accurate sequence numbers and actual hop counts), and handles RERRs compliantly. This ensures the node is legitimately selected along forwarding paths. - **Reversibility:** costly - defines attack strategy interface and simulator hooks.
- **D-02:** Support two configurable dropping modes: (1) Bernoulli probabilistic dropping with configurable rate `drop_prob` (default: 0.5 / 50% data packet drop), and (2) flow-targeted or destination-targeted selective dropping. Control packets are never dropped. - **Reversibility:** reversible.
- **D-03:** Attack activation integrates seamlessly with the Phase 3 dynamic onset runner seam (`_delayed_attack_activation`), supporting `attack.start_time` in scenario configs. - **Reversibility:** reversible.

### 2. Time-Aware Labeling & Feature Discrimination
- **D-04:** Extend feature extraction labeling logic: prior to `attack.start_time`, attacker windows are labeled `Normal`; at/after onset, attacker windows are labeled `Grayhole`. Feature matrix $X$ remains strictly invariant to attack metadata. - **Reversibility:** costly - governs dataset schema and multi-attack ground truth.
- **D-05:** Address subtle drop discrimination: distinguish between network-induced drops (mobility link breakages, collision losses) and malicious Grayhole drops via temporal multi-feature correlation (`packet_drop_ratio`, `packet_forward_ratio`, and `route_reply_rate`). - **Reversibility:** reversible.

### 3. Evaluation Paradigm: Zero-Shot Transfer vs. Multi-Attack Retraining
- **D-06:** **Track A (Zero-Shot Transfer Evaluation):** Benchmark the existing Phase 3 Decision Tree champion (`ml/models/best_model.joblib`) directly against unseen Grayhole test traces without retraining, measuring cross-attack transferability and false alarm stability. - **Reversibility:** reversible.
- **D-07:** **Track B (Multi-Attack Modeling & Phase 5 Unified Champion):** Assemble a pooled multi-attack dataset combining Normal, Blackhole, and Grayhole traffic under seed holdout (train: seeds 42+43; test: seed 44). Train multi-class models (RF, DT, SVM) and evaluate both 3-class discrimination (`Normal`, `Blackhole`, `Grayhole`) and binary isolation mapping (`Normal` vs `Attack`) for Phase 5 mitigation readiness. - **Reversibility:** costly - shapes the model consumed by Phase 5 closed-loop mitigation.

### 4. Generalization Stress Matrix & Acceptance Gate
- **D-08:** Generalization benchmark grid varies:
  - **Mobility speeds:** 1.0 m/s (low), 5.0 m/s (medium baseline), 10.0 m/s (high mobility).
  - **Drop probabilities:** 0.3 (subtle 30%), 0.5 (moderate 50%), 0.7 (aggressive 70%).
  - **Node densities:** 30 nodes (baseline) and 50 nodes (dense network).
- **D-09:** **Locked FPR Gate ($\text{FPR} \le 1.0\%$):** Retained as a non-negotiable constraint across all generalization test splits. Any model exceeding 1.0% FPR is disqualified to prevent benign node isolation during live Phase 5 mitigation. - **Reversibility:** one-way - fundamental reliability guarantee of the IDS.
- **D-10:** Detection boundary analysis: establish the empirical threshold (drop probability $p$) where Grayhole becomes statistically distinguishable from background mobility loss. - **Reversibility:** reversible.

### Agent's Discretion
- Specific scenario file naming under `scenarios/` (e.g., `e4_grayhole_30n.json`, `e4_grayhole_50n.json`).
- Exact layout of generalization metric tables in `results/generalization_report.md`.
- Permutation feature importance analysis for Grayhole discrimination.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & Engineering Rules
- `AGENTS.md` - Core engineering contract (Windows Python-native, zero C++, no random row splits, FPR reporting, Plain AODV comparison).
- `MANET_IDS_BTech_Execution_Guide.md` §Module B, §Module D - Grayhole attack specifications and generalization requirements.
- `.planning/REQUIREMENTS.md` - `ATK-02` requirement definition.

### Precedent Phases & Artifacts
- `.planning/phases/02-blackhole-attack-trace-logging-feature-pipeline/02-01-SUMMARY.md` - Attack strategy interface and decoupled injection pattern.
- `.planning/phases/03-machine-learning-classification-pipeline-evaluation/03-03-SUMMARY.md` - Seed-holdout evaluation, FPR gate protocol, and champion model persistence.
- `ml/models/best_model.joblib` - Persisted Phase 3 champion model for zero-shot transfer evaluation.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `attacks/base.py` & `attacks/registry.py`: Extensible base class `AttackStrategyBase` and factory registry ready for `GrayholeStrategy`.
- `simulator/run_scenario.py`: Dynamic attacker selection, composition root, and `_delayed_attack_activation` method.
- `feature_extraction/extract_features.py`: Sliding-window non-leaking feature computation with `attack_start_time` support.
- `ml/dataset.py`: Deterministic seed-holdout dataset partitioner and SHA-256 manifest generator.
- `ml/train.py`: Uniform pipeline construction, cost-sensitive class weights, and 5-fold CV.
- `ml/evaluate.py`: Security metrics calculation, FPR gate enforcement, and artifact export suite.

### Established Patterns
- Strategy pattern for attack behaviors: `should_drop_data` hook in `SimulationRunner`.
- Discrete-event determinism: explicit integer seeds, sorted dictionary/node iterations.
- Anti-leakage isolation: feature matrix $X$ contains zero identity columns or scenario oracles.

### Integration Points
- `attacks/grayhole.py` registers with `attacks.registry.register_attack_strategy("grayhole", GrayholeStrategy)`.
- `scenarios/` gains Grayhole scenarios (`type: "Grayhole"`, `drop_prob: 0.5`).
- `ml/` evaluates zero-shot transfer and trains multi-attack generalization pipelines.

</code_context>

<specifics>
## Specific Ideas
- Generate side-by-side comparison tables in `results/generalization_report.md` contrasting Blackhole vs Grayhole detection metrics across varying drop probabilities.
- Plot ROC / Precision-Recall curves or detection boundary plots showing detection sensitivity as a function of Grayhole drop probability.

</specifics>

<deferred>
## Deferred Ideas
- Phase 6 will incorporate Grayhole generalization metrics and comparison charts into the final project documentation and slides.
- RREQ flooding / DoS attacks (`ATK-04`) remain deferred to future releases (v2).
</deferred>
