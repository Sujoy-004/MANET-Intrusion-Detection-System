# Phase 04: Grayhole Attack & Generalization Testing - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-27  
**Phase:** 04-Grayhole Attack & Generalization Testing  
**Areas discussed:** Grayhole Attack Strategy & AODV Routing Behavior, Time-Aware Labeling & Feature Discrimination, Evaluation Paradigm: Zero-Shot Transfer vs. Multi-Attack Retraining, Generalization Stress Matrix & Acceptance Gate  

---

## Grayhole Attack Strategy & AODV Routing Behavior

| Option | Description | Selected |
|---|---|---|
| Decoupled Honest Routing with Selective Drop | Honest AODV RREQ/RREP/RERR participation; selective/probabilistic drop on data packets only | ✓ |
| Malicious Routing with Probabilistic Drop | Deceptive RREP sequence numbers (like Blackhole) + partial drop | |
| Hybrid / Configurable Routing | Configurable honest vs deceptive control routing | |

**User's choice:** Decoupled Honest Routing with Selective Drop (Option 1)  
**Notes:** Unlike Blackhole which fabricates high sequence numbers and 1-hop distance, Grayhole acts as an honest router during route discovery to ensure selection along legitimate forwarding paths, dropping only data payloads.

| Option | Description | Selected |
|---|---|---|
| Bernoulli Probabilistic Drop (default 50%) + Selective Flow/Dest Mode | Configurable drop probability $p \in (0, 1)$ with optional targeted drop mode | ✓ |
| Pure Bernoulli Probabilistic Drop only | Fixed or uniform drop rate only | |
| Deterministic Periodic Drop | Periodic $k$-of-$n$ drop pattern | |

**User's choice:** Bernoulli Probabilistic Drop (default 50%) + Selective Flow/Dest Mode  
**Notes:** Provides flexibility across the generalization test matrix while accurately modeling classic Grayhole attack behavior.

| Option | Description | Selected |
|---|---|---|
| Dynamic Onset Runner Seam Integration | Reuse Phase 3 `_delayed_attack_activation` and `attack.start_time` parameter | ✓ |
| Static from $t=0$ only | Immediate attack activation at simulation start | |

**User's choice:** Dynamic Onset Runner Seam Integration  
**Notes:** Allows seamless transition from Normal to Grayhole behavior within composite runs, enabling realistic onset traces.

---

## Time-Aware Labeling & Feature Discrimination

| Option | Description | Selected |
|---|---|---|
| Pre-onset Normal, Post-onset Grayhole | Windows before `attack.start_time` labeled `Normal`; post-onset labeled `Grayhole` | ✓ |
| Full run labeled Grayhole | All windows of attacker node labeled `Grayhole` regardless of activation time | |

**User's choice:** Pre-onset Normal, Post-onset Grayhole  
**Notes:** Strictly prevents label corruption and leakage. Attacker node behaving normally prior to onset is labeled `Normal`. Feature matrix $X$ remains invariant.

| Option | Description | Selected |
|---|---|---|
| Temporal Multi-Feature Correlation | Discriminate subtle Grayhole drops from mobility drops via correlation of `packet_drop_ratio`, `packet_forward_ratio`, and `route_reply_rate` | ✓ |
| Threshold-only on `packet_drop_ratio` | Classify based on single drop threshold | |

**User's choice:** Temporal Multi-Feature Correlation  
**Notes:** Mobile ad-hoc networks exhibit natural packet drops due to route link breakages and buffer overflows. Multi-feature sliding window correlation allows the classifier to learn the behavioral signature of deliberate drops versus route discovery recovery.

---

## Evaluation Paradigm: Zero-Shot Transfer vs. Multi-Attack Retraining

| Option | Description | Selected |
|---|---|---|
| Dual-Track Evaluation (Track A Zero-Shot + Track B Multi-Attack Retraining) | Track A evaluates Phase 3 champion zero-shot; Track B trains and evaluates pooled multi-attack models | ✓ |
| Multi-Attack Retraining only | Discard zero-shot assessment and retrain immediately | |
| Zero-Shot Transfer only | Test Phase 3 model without expanding training dataset | |

**User's choice:** Dual-Track Evaluation (Track A Zero-Shot + Track B Multi-Attack Retraining)  
**Notes:** Track A rigorously tests out-of-distribution transferability of the Blackhole-trained champion model. Track B builds a unified model capable of multi-attack discrimination and binary isolation mapping for Phase 5.

---

## Generalization Stress Matrix & Acceptance Gate

| Option | Description | Selected |
|---|---|---|
| Comprehensive 3-Axis Matrix (Speed, Drop Prob, Density) | Speeds (1, 5, 10 m/s), Drop probs (0.3, 0.5, 0.7), Densities (30, 50 nodes) | ✓ |
| Drop Probability sweep only | Only vary drop probability at default speed/density | |
| Speed variations only | Only vary node speed | |

**User's choice:** Comprehensive 3-Axis Matrix (Speed, Drop Prob, Density)  
**Notes:** Evaluates robustness under realistic MANET conditions and determines the empirical detection boundary where Grayhole drops blend with mobility losses.

| Option | Description | Selected |
|---|---|---|
| Non-negotiable Locked FPR Gate ($\text{FPR} \le 1.0\%$) | Models with $\text{FPR} > 1.0\%$ across evaluation splits are disqualified | ✓ |
| Relaxed FPR Gate ($\text{FPR} \le 3.0\%$) | Relax threshold for subtle attacks | |
| F1-only ranking | Ignore FPR constraint | |

**User's choice:** Non-negotiable Locked FPR Gate ($\text{FPR} \le 1.0\%$)  
**Notes:** False alarms in MANETs isolate benign forwarding nodes, breaking network connectivity and defeating the purpose of the IDS.
