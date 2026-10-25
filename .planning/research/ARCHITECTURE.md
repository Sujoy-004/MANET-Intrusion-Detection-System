# Architecture Research

**Domain:** MANET Simulation, Feature Engineering & Machine Learning Intrusion Detection  
**Researched:** 2026-10-23  
**Confidence:** HIGH  

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Simulation & Execution Layer                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │  SimPy Clock │──▶│ Mobility/RWP │──▶│  Radio Graph │──▶│ AODV Engine  │  │
│  └──────────────┘   └──────────────┘   └──────────────┘   └──────┬───────┘  │
│                                                                  │          │
│  ┌─────────────────────────────┐                                 │          │
│  │   Attacks: Blackhole /      │◀── Injected behavior Strategy   │          │
│  │   Grayhole Node Behaviors   │                                 │          │
│  └─────────────────────────────┘                                 ▼          │
│                                                          ┌──────────────┐   │
│                                                          │ Trace Logger │   │
│                                                          └──────┬───────┘   │
├─────────────────────────────────────────────────────────────────┼───────────┤
│                     Feature Engineering & Data Layer            │           │
├─────────────────────────────────────────────────────────────────┼───────────┤
│                                                          ┌──────▼───────┐   │
│                                                          │ CSV Traces   │   │
│                                                          └──────┬───────┘   │
│                                                                 │           │
│  ┌──────────────────────────────────────────────────────────────▼────────┐  │
│  │ Sliding-Window Aggregator (Forwarding/Drop Ratio, Rates, Neighbors)    │  │
│  └──────────────────────────────┬────────────────────────────────────────┘  │
│                                 ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Non-Leaking Labeled Dataset (Scenario / Seed Partitioning)            │  │
│  └──────────────────────────────┬────────────────────────────────────────┘  │
├─────────────────────────────────┼───────────────────────────────────────────┤
│                     Machine Learning & Inference Layer                      │
├─────────────────────────────────┼───────────────────────────────────────────┤
│                                 ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Scikit-learn Pipeline: StandardScaler + RF / DecisionTree / SVM       │  │
│  └──────────────────────────────┬────────────────────────────────────────┘  │
│                                 ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Classification Evaluator (Accuracy, Precision, Recall, F1, FPR, ROC)  │  │
│  └──────────────────────────────┬────────────────────────────────────────┘  │
├─────────────────────────────────┼───────────────────────────────────────────┤
│                     Closed-Loop Response & Evaluation Layer                 │
├─────────────────────────────────┼───────────────────────────────────────────┤
│                                 ▼                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ IDS Response Engine: Dynamic Malicious Node Isolation / Route Penalty │  │
│  └──────────────────────────────┬────────────────────────────────────────┘  │
│                                 ▼ (Feedback into AODV Route Selection)      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ Comparative QoS Benchmarking (Baseline AODV vs Attack vs AODV + IDS)  │  │
│  │ Metrics: PDR, Throughput, End-to-End Delay, Routing Overhead          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implementation Details |
|-----------|----------------|------------------------|
| `simulator.mobility` | Updates node (x, y) coordinates according to Random Waypoint model | SimPy timeout loop updating positions and speeds based on explicit RNG seeds. |
| `simulator.radio` | Computes pairwise node distances; identifies 1-hop neighbor sets | Transmission range circle model ($d \le R$). Pure NumPy/math calculations. |
| `simulator.aodv` | Implements RFC 3561 reactive routing (RREQ, RREP, RERR) | Sequence numbering, routing table entries with expiration, hop counts, and forward callbacks. |
| `simulator.traffic` | Generates UDP/CBR packet flows between source-destination pairs | Periodic SimPy event triggers passing packets into local AODV queues. |
| `attacks` | Implements attacker-specific abnormal behaviors | Strategy pattern decoupled from simulator: Blackhole sends false zero-hop/max-seq RREP and drops; Grayhole drops probabilistically. |
| `feature_extraction` | Converts event-stream CSV traces into sliding-window tabular features | Windowed aggregation of forwarded, dropped, received packets, RREQ/RREP rates, and neighbor density. |
| `ml` | Trains and evaluates classifiers using scenario-based train/test splits | Scikit-learn pipelines (`RandomForestClassifier`, `DecisionTreeClassifier`, `SVC`), confusion matrices, model persistence. |
| `mitigation` | Feeds IDS predictions back into AODV route discovery | Low-trust node penalization: routes containing flagged nodes are rejected or penalized during route selection. |
| `evaluation` | Calculates network QoS across comparative scenario runs | PDR ($P_{recv}/P_{sent}$), throughput (bps), end-to-end delay (ms), and routing overhead ($Pkts_{routing}/Pkts_{data}$). |

## Recommended Project Structure

```
simulator/               # Core discrete-event MANET simulation engine
├── __init__.py
├── node.py              # Node state, position, buffers, network interfaces
├── mobility.py          # Random Waypoint mobility generator
├── radio.py             # Propagation & neighbor discovery (transmission range)
├── packet.py            # Packet definitions (RREQ, RREP, RERR, DATA)
├── aodv.py              # AODV protocol implementation (routing table, sequence numbers)
├── traffic.py           # CBR / UDP application traffic generator
├── metrics.py           # Network QoS calculators (PDR, delay, throughput, overhead)
└── run_scenario.py      # CLI runner (--scenario config.json --seed 42 --out traces/)
attacks/                 # Adversarial behavior strategies (decoupled from simulator)
├── __init__.py
├── base.py              # Abstract attacker behavior interface
├── blackhole.py         # Malicious immediate high-seq RREP + traffic swallowing
└── grayhole.py          # Selective / probabilistic packet forwarding drop
scenarios/               # JSON experiment scenario specifications
├── baseline_50nodes.json
├── blackhole_single.json
├── blackhole_multi.json
└── grayhole_eval.json
feature_extraction/      # Trace-to-feature transformation pipeline
├── __init__.py
├── schema.py            # Feature definitions and column schemas
└── extractor.py         # Sliding-window trace aggregator
ml/                      # Machine learning training, tuning, and evaluation
├── __init__.py
├── dataset.py           # Scenario/seed-based train/test splitter (zero leakage)
├── train.py             # Model training (RF, DT, SVM) with cross-validation
├── evaluate.py          # Metrics reporter (Precision, Recall, F1, FPR, Confusion Matrix)
└── models/              # Serialized trained model artifacts (.joblib / .pkl)
mitigation/              # Closed-loop IDS response mechanism
├── __init__.py
└── response_engine.py   # Node blacklisting / route selection penalty filter
results/                 # Benchmark logs, QoS tables, and academic plots
├── baseline_comparison.csv
└── plots/               # Matplotlib / Seaborn figures
```

### Structure Rationale

- **Decoupled `attacks/` from `simulator/`:** Ensures the core simulator remains clean and identical for baseline (IDS-off, attack-off) runs and IDS-mitigated runs.
- **Separate `feature_extraction/`:** Guarantees features are computed from traces without injecting ground-truth scenario flags into the feature vector.
- **Dedicated `mitigation/`:** Keeps the IDS decision engine distinct from the underlying protocol, allowing independent testing of detection and response.

## Architectural Patterns

### Pattern 1: Strategy Pattern for Attack Injection

Attacker behaviors subclass an abstract `NodeBehavior` or `AODVBehavior` interface. A benign node delegates forwarding and RREP processing to standard AODV logic, while a compromised node delegates to a `BlackholeBehavior` or `GrayholeBehavior`.

```python
class NodeBehavior(ABC):
    @abstractmethod
    def handle_rreq(self, node, rreq_packet): ...
    @abstractmethod
    def forward_data(self, node, data_packet): ...

class NormalBehavior(NodeBehavior):
    def handle_rreq(self, node, rreq_packet):
        return node.standard_aodv_rreq_handler(rreq_packet)

class BlackholeBehavior(NodeBehavior):
    def handle_rreq(self, node, rreq_packet):
        # Lie immediately: advertise highest destination sequence number and 1 hop
        return node.send_spoofed_rrep(rreq_packet.dest, seq_num=999999, hop_count=1)
    
    def forward_data(self, node, data_packet):
        # Drop all data packets silently
        node.log_packet_drop(data_packet, reason="blackhole_swallowed")
        return False
```

### Pattern 2: Scenario-Based Partitioning (Anti-Leakage)

Rather than randomly partitioning tabular rows, datasets are split by scenario configurations or seeds.

```python
# Partition data strictly by simulation run / scenario ID:
train_scenarios = ["scenario_seed_42", "scenario_seed_43", "scenario_seed_44"]
test_scenarios  = ["scenario_seed_99", "scenario_seed_100"]

train_df = df[df["scenario_id"].isin(train_scenarios)]
test_df  = df[df["scenario_id"].isin(test_scenarios)]
```

### Pattern 3: Closed-Loop Route Re-Evaluation

When the IDS model predicts node $K$ is malicious during or after an observation window, node $K$ is added to an exclusion list or penalized in the AODV routing table. Subsequent route requests explicitly ignore RREPs originating from or passing through $K$, triggering route re-discovery.

```
[Simulation Run 1: Baseline] ──▶ Measure PDR_base, Delay_base
[Simulation Run 2: Attack]   ──▶ Measure PDR_attack (sharp drop expected)
[Simulation Run 3: AODV+IDS] ──▶ IDS isolates attacker ──▶ Measure PDR_mitigated (recovery demonstrated)
```

## Anti-Patterns

### Anti-Pattern 1: In-Memory Flag Leakage
- **What people do:** Setting `packet.is_from_attacker = True` or adding `node.is_malicious` as a column in the feature dataset.
- **Why it's wrong:** The ML classifier achieves 100% accuracy instantly by learning the label flag rather than behavioral patterns.
- **Do this instead:** Feature extractor only sees standard network traffic metrics (ratios, rates, neighbor counts, packet headers).

### Anti-Pattern 2: Random Row Train/Test Split
- **What people do:** Using `train_test_split(df, test_size=0.2, shuffle=True)` on windowed packet trace rows.
- **Why it's wrong:** Consecutive time windows from the same node in the same simulation run are highly autocorrelated, producing fake test performance.
- **Do this instead:** Hold out whole scenario runs, random seeds, or different mobility topologies.

---
*Architecture research for: MANET Intrusion Detection System*  
*Researched: 2026-10-23*  
