<!-- refreshed: 2026-10-22 -->
# Architecture

**Analysis Date:** 2026-10-22

> **Status legend — read this first.**
> - **[IMPLEMENTED]** — exists in the repo today, verified by reading the file.
> - **[SPECIFIED]** — mandated or directed by `AGENTS.md` / `MANET_IDS_BTech_Execution_Guide.md`, with the intended repo-relative path. **Not yet built.**
>
> **Verified repo contents (2026-10-22):** `AGENTS.md` (177 lines), `MANET_IDS_BTech_Execution_Guide.md` (391 lines), `.gitignore` (22 lines). Git repo on branch `main`, single commit `2246d39`, **no remote configured**. **No source code, no manifest, no CI, no test suite, no package directory.** Everything below marked [SPECIFIED] is a *design contract to be built*, not existing code. Do not assume any of it exists.

---

## System Overview

The system is a **staged, file-artifact data pipeline**. Each stage is a separately runnable Python program that reads one artifact from disk and writes another. Nothing is served; nothing is hosted; there is no long-running process.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ L1  COMPOSITION ROOT                                                            │
│     `simulator/run_scenario.py`                                                │
│     CLI: --scenario <json> --seed <int> --out <dir>        [SPECIFIED]         │
│     Owns: seed, config load, attack injection, trace writing, run record      │
└───────┬────────────────────────────────────────────┬─────────────────────────┘
        │ inject behaviour flags (ONE WAY)          │ writes CSV rows
        │ engine modules never import attacks/       ▼
        │                        ┌────────────────────────────────────────────┐
        ▼                        │ L3  TRACE ARTIFACT          [SPECIFIED]      │
┌───────────────────────────┐    │  `traces/<run_id>.csv`                      │
│ L2  SIMULATION ENGINE     │    │  one row per packet event                   │
│  `simulator/mobility.py`  │    │  time,src,dst,pkt_id,type,hop_count,        │
│  `simulator/radio.py`     │    │  dropped_by,...                            │
│  `simulator/aodv.py`  ◄───┼──┐ └──────────────────┬─────────────────────────┘
│  `simulator/traffic.py`   │  │                    │ read
│  `simulator/metrics.py`   │  │                    ▼
└───────────────────────────┘  │  ┌────────────────────────────────────────────┐
                               │  │ L4  FEATURE ANALYSIS                       │
                               │  │  `feature_extraction/`                     │
                               │  │  traces → per-node, per-window rows        │
                               │  └──────────────────┬─────────────────────────┘
┌───────────────────────────┐  │                     │ labels JOINED from
│ L2b ATTACK BEHAVIOUR      │  │                     │ `scenarios/*.json`
│  `attacks/blackhole.py`   │  │                     │ (never from the trace)
│  `attacks/grayhole.py`    │  │                     ▼
│  node behaviour flags     │  │  ┌────────────────────────────────────────────┐
│  lying reply / prob. drop │  │  │ L5  DATASET ARTIFACT                       │
└───────────────────────────┘  └──┘  │  `data/dataset.csv` + group key (run_id)  │
                                        └──────────────────┬─────────────────────────┘
                                                           ▼
                                        ┌────────────────────────────────────────────┐
                                        │ L6  LEARNING                    [SPECIFIED] │
                                        │  `ml/`  clean → group-split → fit →        │
                                        │  sklearn Pipeline → joblib artifact        │
                                        └──────────────────┬─────────────────────────┘
                                                           │ predict(node, window)
                                                           ▼
                                        ┌────────────────────────────────────────────┐
                                        │ L7  RESPONSE + RE-EVALUATION  [SPECIFIED] │
                                        │  alert → isolate → re-run same scenario    │
                                        │  and seed → compare vs IDS-off baseline    │
                                        └────────────────────────────────────────────┘
```

**The chain in one sentence** (`AGENTS.md:163-166`, `MANET_IDS_BTech_Execution_Guide.md:379`):
`launch simulation → generate normal/attack traffic → extract features → run trained IDS → identify malicious node → trigger response → show measurable improvement vs. baseline AODV`.

**The loop that closes it** (`MANET_IDS_BTech_Execution_Guide.md:381-383`): run scenario S with seed N twice — once with the IDS off, once with the IDS on — and show the PDR/throughput recovery side by side. The two runs must use the **identical scenario config and seed**, or the comparison is meaningless.

---

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Engineering contract | Binding rules; wins on engineering questions; must be kept in sync with the guide | `AGENTS.md` **[IMPLEMENTED]** |
| Project specification | Scope, phases, experiment matrix, feature schema, metrics, deliverables, viva questions | `MANET_IDS_BTech_Execution_Guide.md` **[IMPLEMENTED]** |
| Artifact policy | Which generated output is never committed | `.gitignore` **[IMPLEMENTED]** |
| Scenario runner / composition root | Load scenario JSON, build the seeded RNG, construct the engine, inject attack behaviour, run SimPy, write the trace, write the per-run record | `simulator/run_scenario.py` **[SPECIFIED]** `AGENTS.md:65` |
| Mobility | Random Waypoint node movement; node speed is the `mobility_speed` feature | `simulator/mobility.py` **[SPECIFIED]** `AGENTS.md:56` |
| Radio | Transmission range / link availability; drives `neighbor_count`; supplies the topology graph | `simulator/radio.py` **[SPECIFIED]** `AGENTS.md:57` |
| AODV routing | RREQ/RREP/RERR, sequence numbers, route table with hop count and expiry; records `route_request_rate` / `route_reply_rate` per time window | `simulator/aodv.py` **[SPECIFIED]** `AGENTS.md:58-59` |
| Traffic | CBR/UDP flows: source–dest pairs, packet rate, payload size | `simulator/traffic.py` **[SPECIFIED]** `AGENTS.md:60` |
| Network metrics | PDR, throughput, end-to-end delay, packet loss, routing overhead | `simulator/metrics.py` **[SPECIFIED]** `AGENTS.md:64` |
| Attack behaviour | Blackhole (lying RREP) and Grayhole (probabilistic drop) as **node behaviour flags** | `attacks/blackhole.py`, `attacks/grayhole.py` **[SPECIFIED]** `AGENTS.md:61-63` |
| Scenario config | The single source of truth for topology, mobility, traffic, seed, attack type and attacker node id — and therefore the **only** legitimate source of ground-truth labels | `scenarios/*.json` **[SPECIFIED]** `AGENTS.md:84-85,116` |
| Trace artifact | CSV, one row per packet event | `traces/<run_id>.csv` **[SPECIFIED]** `AGENTS.md:81-83` |
| Feature analysis | Traces → one feature row per node per fixed observation window | `feature_extraction/` **[SPECIFIED]** `MANET_IDS_BTech_Execution_Guide.md:102-117` |
| Dataset artifact | The joined, labelled feature table plus a group key | `data/dataset.csv` **[SPECIFIED]** `AGENTS.md:118` |
| ML engine | Clean → group-split → fit baseline models → persist model **and** preprocessing pipeline | `ml/` **[SPECIFIED]** `MANET_IDS_BTech_Execution_Guide.md:119-126` |
| IDS response | Confidence threshold → alert → node marked malicious / low-trust → route selection avoids it | `ml/response.py` **[SPECIFIED]** `MANET_IDS_BTech_Execution_Guide.md:128-133` |
| Run record | Per-run JSON tying a metric set back to its scenario config + seed | `results/runs/<run_id>.json` **[SPECIFIED]** `AGENTS.md:151` |
| Figures | Confusion matrix per classifier, P/R/F1 bars, PDR vs. attackers, delay IDS off/on | `results/plots/` **[SPECIFIED]** `MANET_IDS_BTech_Execution_Guide.md:263-270` |
| Optional viewer | Local results viewer; **last phase only** | `dashboard/` **[SPECIFIED-OPTIONAL]** `AGENTS.md:166-167` |
| Notes & deviations | Experiment log, architecture deviations, decision records | `docs/` **[SPECIFIED]** `AGENTS.md:123` |

---

## Pattern Overview

**Overall:** *Staged offline data pipeline (batch ETL over file artifacts) with dependency injection at the simulator boundary.*

This is not a web app, not a service, not a library. There is no request/response cycle. Each stage is a script that a human (or a scheduled batch) runs, and the output of one stage is the input of the next.

**Key Characteristics:**

1. **File-artifact handoff.** Stage boundaries are CSV/JSON files on the local disk, not in-memory calls across processes. A stage can be re-run in isolation on an artifact produced days earlier. `AGENTS.md:34-35` fixes the order: `simulator → traces → features → dataset → ML → IDS response → network re-evaluation`.
2. **Composition root with an attack-agnostic engine.** All cross-package wiring happens in one place (`simulator/run_scenario.py`). The engine modules are pure and know nothing about attacks, ML, or the filesystem layout. `AGENTS.md:67-69`.
3. **Deterministic seeded execution.** The same `(scenario, seed)` pair must produce byte-identical traces. This is what makes "multiple seeds" in the experiment matrix (`MANET_IDS_BTech_Execution_Guide.md:193-195`, E1–E8 table at `:244-253`) a controlled variable instead of noise. `AGENTS.md:72-74`.
4. **Labels are inputs, not outputs.** Ground truth comes from the scenario config, which the operator chose. It is *joined onto* features, never *derived from* traffic. `AGENTS.md:84-85`.
5. **The attack's effect is observable-only.** A blackhole must manifest as drops, PDR collapse and route anomalies — never as a flag that the metrics layer can read to shortcut the detection. `AGENTS.md:86-87`.
6. **Local-only, single-process, no services.** No network, no database, no auth, no CI, no remote. `AGENTS.md:6-7,27`.
7. **Every reported number traces to a saved run.** The metric set and the config that produced it are both persisted. `AGENTS.md:151`, `MANET_IDS_BTech_Execution_Guide.md:320`.

---

## Layers

### L1 — Composition Root / Orchestration

- **Purpose:** The only place where packages are wired together. Owns the seed, parses the CLI, loads the scenario JSON, builds the simulation, injects attack behaviour, writes the trace and the run record.
- **Location:** `simulator/run_scenario.py` **[SPECIFIED]**
- **Contains:** `argparse` CLI (`--scenario <json> --seed <int> --out <dir>`), scenario-config loading and validation, `random.Random(seed)` construction, engine assembly, attack selection from the config, trace writer, run-record writer.
- **Depends on:** `simulator/mobility.py`, `simulator/radio.py`, `simulator/aodv.py`, `simulator/traffic.py`, `simulator/metrics.py`, `attacks/` (the **only** sanctioned import of `attacks/`), `simpy`, `networkx`, stdlib `json`/`csv`/`random`/`pathlib`.
- **Used by:** a human operator, the experiment batch driver, and the IDS-on/IDS-off comparison driver.
- **Contract:** `AGENTS.md:65` — `--scenario <json> --seed <int> --out <dir>`. Keep these three flags working exactly as written; they are quoted in the spec and will be quoted by the report.

### L2 — Simulation Engine

- **Purpose:** Simulate a mobile ad hoc network: nodes move, links appear and vanish, AODV discovers and maintains routes, CBR traffic flows, metrics are computed.
- **Location:** `simulator/` **[SPECIFIED]**
- **Contains:** `mobility.py`, `radio.py`, `aodv.py`, `traffic.py`, `metrics.py` (one module per concern, per `AGENTS.md:54-64`).
- **Depends on:** `simpy` (event clock), `networkx` (topology/neighbour graphs), stdlib `random` (via an injected seeded instance), stdlib `dataclasses`/`json`/`csv` (`AGENTS.md:52`).
- **Used by:** `simulator/run_scenario.py` and the IDS-on/IDS-off driver.
- **Hard rule:** **No module under `simulator/` may import `attacks/` or `ml/`.** `AGENTS.md:67-69`.

#### Intra-package dependency order (prescriptive)

The engine is a DAG. Enforce this order; it eliminates every circular-import risk the project could plausibly hit:

```text
simulator/mobility.py   (no intra-package deps)
        │
        ▼
simulator/radio.py      (needs node positions)
        │
        ▼
simulator/aodv.py       (needs neighbour sets, owns routes + behaviour flags)
        │
        ▼
simulator/traffic.py    (needs next-hop from the routing layer)
        │
        ▼
simulator/metrics.py    (reads from all of the above; never called back into)

simulator/run_scenario.py  (composition root — may import all of the above + attacks/)
```

`metrics.py` is a **leaf consumer**: it observes and never mutates or is mutated by. If you find yourself wanting `aodv.py` to call `metrics.py` directly, that is a design error — emit a trace row and let the metrics layer aggregate it.

### L2b — Attack Behaviour

- **Purpose:** Provide the malicious node's abnormal behaviour as an injectable object.
- **Location:** `attacks/` (top-level package, the guide's Module B) **[SPECIFIED]**
- **Contains:** `blackhole.py` (lying RREP — advertises an attractive route then drops/forwards nothing), `grayhole.py` (probabilistic drop), a shared base/protocol, and a small registry mapping the scenario's `attack` string to a factory.
- **Depends on:** stdlib only. **It must not import `simulator/`** either — the contract is defined by the flags it sets, not by simulator classes.
- **Used by:** `simulator/run_scenario.py` only.
- **Implementation shape (mandated, not a suggestion):** *node behaviour flags on the AODV node* — "a lying reply (blackhole) and probabilistic drop (grayhole)" (`AGENTS.md:61-63`). This is the deliberate payoff of dropping NS-3: no hook framework, no C++ callbacks, no simulator patch points. `AGENTS.md:61-63` — "This is far simpler than NS-3 hooks and is the main payoff of dropping NS-3."

**The interface the engine knows about (duck-typed, not imported):**

Every AODV node carries an optional `node.attack_behavior` attribute. It is **`None` for a clean node**. When present it exposes the behaviour flags the engine consults:

| Flag on `node.attack_behavior` | Type | Meaning | Attack that sets it |
|-------|------|---------|---------------------|
| lying reply / advertises a false route | bool or callable | When set, the node answers RREQs with an attractive but unusable route | Blackhole |
| drop probability | float in `[0,1]` | Fraction of data packets this node silently discards | Grayhole |

The engine reads these flags; it never learns which attack set them, and it never imports the module that did. That is precisely why the engine can also run the **clean baseline** with the very same code path — the clean run is simply the case where `node.attack_behavior is None`. The `attacks/` package therefore has no dependency on `simulator/` at all; the contract is the flags it sets, not simulator classes.

### L3 — Trace Artifact

- **Purpose:** The immutable, auditable record of what happened on the network. It is the only thing the ML side ever sees about the network.
- **Location:** `traces/<run_id>.csv` **[SPECIFIED]**, gitignored (`.gitignore:2`)
- **Contains:** one row per packet event, columns beginning `time, src, dst, pkt_id, type, hop_count, dropped_by, ...` (`AGENTS.md:81-83`).
- **Depends on:** nothing — it is a leaf artifact.
- **Used by:** `feature_extraction/`, and humans auditing a run.
- **Rule:** *Features are derived from traces, never embedded in them* (`AGENTS.md:83`). The trace must not contain the label, the attack type, or any field derived from the attack config.

### L4 — Feature Analysis

- **Purpose:** Convert raw packet events into one row per observation window per node.
- **Location:** `feature_extraction/` **[SPECIFIED]**
- **Contains:** windowing logic, per-feature computation, label joining, dataset assembly.
- **Depends on:** `traces/*.csv` (read), `scenarios/*.json` (read, **for labels only**), `pandas`, `numpy`.
- **Used by:** `ml/`.
- **Mandated feature schema** (`MANET_IDS_BTech_Execution_Guide.md:104-117`):

  | Feature | Meaning | Primary source |
  |---------|---------|----------------|
  | `packet_forward_ratio` | Forwarded packets relative to packets expected/received | trace rows, `simulator/radio.py` neighbour logic |
  | `packet_drop_ratio` | Fraction of packets dropped | trace `dropped_by` |
  | `avg_delay` | Average observed packet delay | trace send/receive timestamps |
  | `route_request_rate` | RREQ activity in a time window | `simulator/aodv.py` |
  | `route_reply_rate` | RREP activity in a time window | `simulator/aodv.py` |
  | `throughput` | Successfully delivered data rate | trace |
  | `hop_count` | Observed route length | trace `hop_count` |
  | `neighbor_count` | Number of relevant neighbours | `simulator/radio.py` |
  | `mobility_speed` | Node speed in the simulation | `simulator/mobility.py` |
  | `label` | Normal / Blackhole / Grayhole / other | **`scenarios/*.json` — never the trace** |

### L5 — Dataset Artifact

- **Purpose:** The joined, labelled feature table that the ML engine consumes, carrying a group key so it can be split correctly.
- **Location:** `data/dataset.csv` **[SPECIFIED]**, gitignored (`.gitignore:3`)
- **Contains:** the 9 feature columns + `label` + a group column identifying the run (scenario × seed).
- **Depends on:** `feature_extraction/` output.
- **Used by:** `ml/`.
- **The group key is not optional.** Without a run identifier there is no way to do a scenario/seed holdout, and a random row split is a rule violation (`AGENTS.md:142-143`).

### L6 — Learning

- **Purpose:** Clean, split, train, evaluate, persist.
- **Location:** `ml/` **[SPECIFIED]**
- **Contains:** dataset loading/cleaning, group splitting, model definitions, training loop, evaluation/report generation, saved artifacts.
- **Depends on:** `data/*.csv`, `scikit-learn`, `pandas`, `numpy`, `joblib`.
- **Used by:** the report, the figures, and the IDS response path.
- **Mandated order** (`AGENTS.md:138`): *data generation → baseline model → comparison → generalization, in that order.* Model order (`MANET_IDS_BTech_Execution_Guide.md:213-217`): Decision Tree → Random Forest → SVM or XGBoost, all under the same train/test protocol. Tune only after a baseline exists (`MANET_IDS_BTech_Execution_Guide.md:126`).
- **Mandatory output:** the model **and** the preprocessing pipeline, saved together (`MANET_IDS_BTech_Execution_Guide.md:126-127,329`). Use `sklearn.pipeline.Pipeline` so scaler + classifier persist as one artifact.

### L7 — Response + Re-evaluation

- **Purpose:** Turn predictions into a network-level effect and prove it helped.
- **Location:** `ml/response.py` (the detection + response logic) and `ml/run_evaluation.py` (the integration driver that composes `ml/` with `simulator/`) **[SPECIFIED]**
- **Contains:** detection threshold, malicious/low-trust node assignment, route-avoidance policy, and the IDS-off vs IDS-on comparison driver.
- **Depends on:** the saved model (for prediction) and `simulator/` (to re-run the scenario).
- **Used by:** the final demonstration.
- **Mandated behaviour** (`MANET_IDS_BTech_Execution_Guide.md:129-133`): generate an alert when confidence exceeds a predefined threshold; assign the node a malicious/low-trust state; prevent or discourage routing through that node; re-run the same scenario and quantify whether network performance improves.
- **Constraint:** the response must act on the **simulator's routing decisions**, not on a post-hoc analysis script. The engine therefore exposes a *route-exclusion hook* that the driver installs; the engine never imports `ml/`.
- **Documented exception to the layer rule (record it in `docs/deviations.md` when Phase 4 is built):** the *model layer* of `ml/` (`ml/dataset.py`, `ml/split.py`, `ml/train.py`, `ml/evaluate.py`) reads only `data/*.csv` and imports nothing from `simulator/`. Only the *integration module* — `ml/run_evaluation.py` / `ml/response.py` — may import `simulator/`, because the re-evaluation run is by definition a simulation. This is the one place in the codebase where the `ml → simulator` arrow is allowed, and it points upward only (never the reverse). The alternative — letting `simulator/run_scenario.py` import `ml/` — would pull scikit-learn into every plain simulation run and would put the model layer underneath the engine, which is the wrong direction.

### L8 — Presentation

- **Purpose:** Figures and (optionally) a viewer.
- **Location:** `results/plots/` **[SPECIFIED, committed]**, `dashboard/` **[SPECIFIED-OPTIONAL]**
- **Rule:** the dashboard is the **last** thing built, never the first. "A dashboard is secondary to this chain. Do not build one before the chain works." `AGENTS.md:166-167`, `MANET_IDS_BTech_Execution_Guide.md:74,332`.

---

## Data Flow

### Primary Request Path — Simulation Run (clean baseline or attack)

1. **Invoke** — `python -m simulator.run_scenario --scenario scenarios/e1_normal_50n.json --seed 1 --out traces/` (`simulator/run_scenario.py`)
2. **Load & validate config** — parse the scenario JSON; extract node count, area, mobility model/speed, traffic flows, and the optional `attack` / `attacker` fields (`simulator/run_scenario.py`)
3. **Seed** — construct `rng = random.Random(seed)` and thread it into every stochastic component. SimPy 4.x has no `env.seed()` and no `env.random`; do not rely on the `random` module globals (`AGENTS.md:72-74`)
4. **Build engine** — instantiate mobility, radio, AODV and traffic over a `simpy.Environment`; build the topology graph in NetworkX
5. **Inject attack (or not)** — if the config names an attack, the runner instantiates the corresponding `attacks/` behaviour and applies it to the attacker's node flags. **The engine modules are not modified and do not know which attack, if any, is active** (`AGENTS.md:61-69`)
6. **Simulate** — `env.run()`; mobility ticks, RREQ floods, hop-by-hop forwarding and packet drops all advance *simulated* time
7. **Observe** — each packet event is appended as a trace row; routing events contribute to `route_request_rate` / `route_reply_rate` windows (`AGENTS.md:58-59`)
8. **Write artifacts** — `traces/<run_id>.csv` and `results/runs/<run_id>.json` (the run record: scenario path, seed, metric set, timestamp) (`AGENTS.md:151`)

### Secondary Flow — Dataset Build

1. **Invoke** — `python -m feature_extraction.extract_features --traces traces/ --scenarios scenarios/ --out data/dataset.csv` (`feature_extraction/extract_features.py`) **[SPECIFIED — filename recommended; the spec fixes the directory, not the file name]**
2. **Read traces** — parse every `traces/*.csv` with pandas, one row per packet event
3. **Window** — bucket events into fixed observation windows per node (`MANET_IDS_BTech_Execution_Guide.md:209`)
4. **Compute features** — the 9 columns in the L4 table, each derived **only** from observed traffic
5. **Join labels** — read the scenario config that produced each trace and attach `label` to the rows from that run. **This is the only legitimate source of ground truth** (`AGENTS.md:84-85`)
6. **Attach the group key** — every row inherits the `run_id` of the trace it came from
7. **Write** — `data/dataset.csv`

### Tertiary Flow — Model Training & Evaluation

1. **Load** — `data/dataset.csv`
2. **Clean** — missing/invalid values, duplicates, class imbalance (`MANET_IDS_BTech_Execution_Guide.md:121`, `:287`)
3. **Split by group, never by row** — hold out by scenario / seed / configuration (`AGENTS.md:142-143`; use `GroupShuffleSplit` / `StratifiedGroupKFold` with the group column)
4. **Fit baselines in order** — Decision Tree, then Random Forest, then SVM/XGBoost, all under the identical protocol (`MANET_IDS_BTech_Execution_Guide.md:213-217`)
5. **Evaluate fully** — accuracy **plus** precision, recall, F1, false-positive rate, confusion matrix. "Never report accuracy alone" (`AGENTS.md:148-149`)
6. **Generalize** — test on unseen seeds/configurations, and at least one different node density and mobility condition (`MANET_IDS_BTech_Execution_Guide.md:222-224`)
7. **Persist** — `Pipeline` (scaler + classifier) → `ml/models/<name>__<dataset>.joblib`; write the metric report and figures to `results/`

### Quaternary Flow — IDS Response & Network Re-evaluation

1. **Re-run the scenario** — same config, same seed, IDS **off** → baseline metrics (PDR, throughput, end-to-end delay, packet loss, routing overhead) (`AGENTS.md:150`)
2. **Extract features** for the attack run exactly as in the secondary flow
3. **Predict** — the saved `Pipeline` scores each node/window; confidence above the threshold raises an alert (`MANET_IDS_BTech_Execution_Guide.md:130`)
4. **Isolate** — flagged nodes enter a malicious/low-trust set; the route-exclusion hook makes the engine prefer routes that avoid them (`MANET_IDS_BTech_Execution_Guide.md:131-132`)
5. **Re-run the same scenario and seed** with the hook installed → IDS-on metrics
6. **Compare** — report PDR, throughput, end-to-end delay, packet loss and routing overhead for **both** arms, plus the IDS's own overhead (processing time and added routing/communication overhead) (`AGENTS.md:150`, `MANET_IDS_BTech_Execution_Guide.md:258-259`)

**State Management:**
- The simulation is **stateless between stages**. Every artifact is a file; no stage holds state in memory for another stage. Re-running a stage on a saved artifact must reproduce the same result.
- Within a run, the **only** mutable state that matters is: the SimPy event queue, the AODV route tables (`simulator/aodv.py`), and the per-node counters the metrics layer aggregates (`simulator/metrics.py`).
- Across runs, the **only** state is the file system: `traces/`, `data/`, `results/`, `ml/models/`.
- There is **no** cache layer, no database, no session, no global registry (`MANET_IDS_BTech_Execution_Guide.md:322-328`).
- Model persistence is a file artifact, not in-memory state.

---

## Key Abstractions

### Scenario Config
- **Purpose:** One JSON file describing one complete experiment — topology, area, mobility model and speed, traffic flows and rates, and optionally an attack with its attacker node id.
- **Examples:** `scenarios/e1_normal_50n.json`, `scenarios/e2_blackhole_50n.json` **[SPECIFIED]**
- **Pattern:** Immutable data loaded once at the start of a run. Deserialise into a `dataclasses` dataclass (`AGENTS.md:52` — stdlib `dataclasses`/`json`/`csv` for scenarios, traces, and metrics). Never mutate it during a run.
- **Role:** It is simultaneously the *run configuration* and the *ground truth*. That dual role is why it must be committed to git and never derived from the trace.

### Node Behaviour Flags
- **Purpose:** The single interface through which a malicious node's behaviour enters the simulation.
- **Examples:** `attacks/blackhole.py`, `attacks/grayhole.py` **[SPECIFIED]**
- **Pattern:** **Dependency injection / strategy object applied to node state.** The engine reads the flags; the attack writes them. There is no registry lookup inside the engine, no plugin discovery, no `import attacks` in the engine.
- **Why it matters:** the clean baseline runs through the *identical* code path with the flags absent. If the engine branched on "is this a blackhole?", the baseline and the attack run would be different code and the comparison would be invalid.

### Trace Event Row
- **Purpose:** One packet-level event, the atomic unit of the entire dataset pipeline.
- **Examples:** `traces/<run_id>.csv` **[SPECIFIED]**
- **Pattern:** Append-only CSV. Fixed column set beginning `time, src, dst, pkt_id, type, hop_count, dropped_by, ...` (`AGENTS.md:81-83`). **Keep the column set stable** — `feature_extraction/` and any downstream notebook depend on it.
- **Invariants:** contains no label, no attack type, no attacker identity, no derived feature.

### Observation Window
- **Purpose:** The unit of feature aggregation — a fixed time slice over which per-node statistics are computed.
- **Examples:** `feature_extraction/windows.py` **[SPECIFIED]**
- **Pattern:** Fixed-duration bucketing keyed by `(node_id, window_index)`. Window length is a scenario/dataset parameter, not a magic constant buried in code.

### Labelled Feature Row
- **Purpose:** One row per `(node, window)` in the dataset — the 9 features plus `label` plus the group key.
- **Examples:** `data/dataset.csv` **[SPECIFIED]**
- **Pattern:** Flat tabular row, scikit-learn-ready. `label` ∈ {`Normal`, `Blackhole`, `Grayhole`, other}.

### Group Key (`run_id`)
- **Purpose:** Identifies the simulation run a row came from (scenario × seed).
- **Examples:** `scenarios/e1_normal_50n.json` + `--seed 1` → `run_id = "e1_normal_50n__s1"` **[SPECIFIED — naming recommended]**
- **Pattern:** Grouping column for `GroupShuffleSplit` / `StratifiedGroupKFold`. This is the mechanism that satisfies `AGENTS.md:142-143`.

### Detection Model Pipeline
- **Purpose:** A persisted, self-contained scorer: preprocessing + classifier in one object.
- **Examples:** `ml/models/rf__dataset.joblib` **[SPECIFIED]**
- **Pattern:** `sklearn.pipeline.Pipeline`. Saved with `joblib`. Must round-trip: loading the artifact and calling `predict` must work without re-running any training code.

### Response Policy / Route-Exclusion Hook
- **Purpose:** The mechanism by which a detected node stops being preferred in routes.
- **Examples:** `ml/response.py` + the hook interface on the AODV node in `simulator/aodv.py` **[SPECIFIED]**
- **Pattern:** Injected callback. The engine calls it; the policy decides. The engine does not import `ml/`.

### Per-Run Record
- **Purpose:** The audit trail that makes every reported number defensible.
- **Examples:** `results/runs/<run_id>.json` **[SPECIFIED]**
- **Pattern:** One JSON per run containing the scenario config path, the seed, the metric set, the attack configuration, and a timestamp. `AGENTS.md:151` — "Every number in the report/README must trace to a saved experiment run + its config."

---

## Entry Points

### Scenario Runner (primary)
- **Location:** `simulator/run_scenario.py` **[SPECIFIED]**
- **Triggers:** `python -m simulator.run_scenario --scenario <json> --seed <int> --out <dir>` — invoked by a human, by the experiment batch, and by the IDS-off/IDS-on comparison driver.
- **Responsibilities:** parse CLI → load and validate scenario JSON → build seeded RNG → construct engine → inject attack behaviour flags → run SimPy → write trace CSV → write per-run record → print a one-line summary to stdout.
- **Contract:** `AGENTS.md:65`. Do not rename the three flags. An optional `--log-level` flag (`DEBUG`/`INFO`/`WARNING`/`ERROR`, default `INFO`) may be added on top of them.
- **Invocation style:** run it **as a module** (`python -m simulator.run_scenario`), not as a file path (`python simulator/run_scenario.py`). The file-path form breaks package-relative imports and double-imports modules, producing two distinct copies of the same dataclass.

### Dataset Builder
- **Location:** `feature_extraction/extract_features.py` **[SPECIFIED — filename recommended]**
- **Triggers:** `python -m feature_extraction.extract_features --traces traces/ --scenarios scenarios/ --out data/dataset.csv`
- **Responsibilities:** parse traces → window → compute the 9 features → join labels from scenario configs → attach the `run_id` group key → write `data/dataset.csv`.

### Trainer / Evaluator
- **Location:** `ml/train.py`, `ml/evaluate.py` **[SPECIFIED — filenames recommended]**
- **Triggers:** `python -m ml.train --data data/dataset.csv --out ml/models/`
- **Responsibilities:** clean → group-split → fit the three baseline models → full metric set → confusion matrix → save pipeline artifacts → write the comparison table and figures.

### Response / Comparison Driver
- **Location:** `ml/run_evaluation.py` (driver) and `ml/response.py` (detection + route-exclusion logic) **[SPECIFIED — location recommended]**
- **Triggers:** `python -m ml.run_evaluation --scenario <json> --seed <int> --model <path>`
- **Responsibilities:** run IDS-off → extract features → predict → threshold → build the excluded-node set → re-run the identical scenario+seed with the hook installed → emit the two-arm comparison.

### (Optional) Dashboard
- **Location:** `dashboard/` **[SPECIFIED-OPTIONAL]**
- **Triggers:** manual, `127.0.0.1` only.
- **Responsibilities:** read `results/` and render views. **Do not build before the acceptance chain works** (`AGENTS.md:166-167`).

---

## Architectural Constraints

- **Threading:** Single-threaded, single-process. The simulation is a SimPy discrete-event loop (`AGENTS.md:49-50`) — it does not use real threads; "concurrency" is cooperative event ordering on the simulated clock. scikit-learn runs single-threaded by default. **Do not introduce `multiprocessing` for the simulation** — it would break the seed→identical-traces guarantee and the ~70k events/sec budget does not need it. The dataset build may use pandas' internal vectorisation, which is fine and deterministic.
- **Global state:** There must be **no** module-level mutable singletons in `simulator/`, `attacks/`, `feature_extraction/` or `ml/`. Specifically: do not use the `random` module's global generator — construct `rng = random.Random(seed)` once in the runner and pass it down (`AGENTS.md:72-74`). Do not cache parsed datasets in module-level dicts across runs. The only sanctioned module-level state is immutable configuration (e.g. the feature schema column list) and the sklearn artifact loaded per invocation.
- **Circular imports:** The intra-`simulator/` DAG (`mobility → radio → aodv → traffic → metrics`) is specified above to eliminate the realistic cycle risks (aodv↔radio over neighbour sets, aodv↔traffic over next-hop). `metrics.py` is a leaf consumer. `attacks/` imports nothing from `simulator/`; `simulator/` imports nothing from `attacks/` (except the runner). `ml/` may import `simulator/` for the re-evaluation run, but `simulator/` must never import `ml/`.
- **Import boundary (the single most important rule):** `simulator/` must **not** import `attacks/` directly — attack behaviour is injected by the scenario runner so the simulator stays attack-agnostic and the same code produces the clean baseline runs used as the IDS-off comparison (`AGENTS.md:67-69`). **Precise reading:** the prohibition binds the engine modules (`simulator/mobility.py`, `simulator/radio.py`, `simulator/aodv.py`, `simulator/traffic.py`, `simulator/metrics.py`). The single sanctioned import point is the scenario runner `simulator/run_scenario.py`, which is the composition root. A future executor must neither (a) put `import attacks` inside `aodv.py`, nor (b) refuse to ever import `attacks/` anywhere.
- **Determinism:** every run is driven by an explicit integer seed; same seed ⇒ identical traces (`AGENTS.md:72-74`). Corollary: **never iterate over a `set`** where the order affects behaviour — always `sorted(...)`. `AGENTS.md:175-176` names "non-deterministic iteration order over sets" as a known failure point.
- **Simulated time ≠ wall time.** A representative workload (50 nodes / 8 flows / 10 pps / 300 s simulated, blackhole attacker) completes in **0.83 s wall**, ~70k events/sec (`AGENTS.md:75-80`). A 30–60 s run takes well under a second. **If a run is slow, per-packet Python overhead is the culprit — profile before increasing node count** (`AGENTS.md:79-80`). Never "optimise" by reaching for C++/Cython/Numba (`AGENTS.md:25`).
- **Label provenance:** labels come from the scenario config, never from the trace (`AGENTS.md:84-85`). Ground truth is an *input*, not a derived quantity.
- **Observable-only attack effect:** the attack's effect must live in the network behaviour (drops, PDR), not in a flag the metrics can read directly (`AGENTS.md:86-87`). Otherwise detection becomes trivial and the result is worthless.
- **Platform:** Windows-native. No WSL, no Linux VM, no Docker, no C++ toolchain, no NS-3 (`AGENTS.md:26-27,30-31`). Python 3.11+, `python -m pip` only (`AGENTS.md:107`).
- **No leakage features:** no `is_attacker` column and no field derived from the attack config rather than from observed traffic (`AGENTS.md:145-146`).
- **Grouped holdout:** never split by random rows; rows from one simulation run are correlated (`AGENTS.md:142-143`).
- **Full metric set + baseline:** precision, recall, F1, false-positive rate and a confusion matrix — never accuracy alone (`AGENTS.md:148-149`); and always compare against plain AODV without the IDS (`AGENTS.md:150`).
- **Documentation sync:** `AGENTS.md` and `MANET_IDS_BTech_Execution_Guide.md` must be changed together in the same commit whenever the architecture changes (`AGENTS.md:14-16,36-37`).

---

## Anti-Patterns

### Engine imports the attack package

**What happens:** `simulator/aodv.py` does `from attacks.blackhole import Blackhole` and branches on attack type to decide how to answer an RREQ.
**Why it's wrong:** the engine stops being attack-agnostic. The clean baseline then runs through a *different* code path than the attack run, so the IDS-off vs IDS-on comparison measures a code difference, not the IDS. It also couples the simulator's core to the attack set, so adding an attack means editing the routing protocol.
**Do this instead:** the engine reads duck-typed behaviour flags off the node (lying reply, drop probability); the runner injects them. See the L2b table.

### The attack leaves a readable tell

**What happens:** the attacking node sets `node.is_malicious = True` (or an equivalent marker), and `simulator/metrics.py` or `feature_extraction/` reads it and adds it as a column.
**Why it's wrong:** detection becomes trivial and the reported accuracy is meaningless — the model is reading the answer key. This is the leakage rule (`AGENTS.md:145-146`) and the observable-only rule (`AGENTS.md:86-87`) in one.
**Do this instead:** the attack manifests only as drops, false routes, PDR collapse and route anomalies. The flag that the *engine* uses to lie or drop is a private implementation detail of the node, and no feature extractor may read it.

### Random row split for train/test

**What happens:** `train_test_split(df, test_size=0.2)` on the flat feature table.
**Why it's wrong:** rows from one simulation run are correlated; a random split puts near-duplicate windows of the same run on both sides and inflates the score. `AGENTS.md:142-143` calls this out as a rule, not a preference.
**Do this instead:** carry a `run_id` group column through the dataset and split with `GroupShuffleSplit` / `StratifiedGroupKFold` on that column.

### Accuracy-only reporting

**What happens:** a results table with one column, "Accuracy: 0.97".
**Why it's wrong:** imbalanced security data can look perfect while missing most attacks. `AGENTS.md:148-149`; `MANET_IDS_BTech_Execution_Guide.md:261`.
**Do this instead:** always report precision, recall, F1, false-positive rate and a confusion matrix.

### Embedding derived features in the trace

**What happens:** the simulator writes a `pdr` or `drop_ratio` column into the trace alongside the raw events.
**Why it's wrong:** it breaks the layer contract — features are derived from traces, never embedded in them (`AGENTS.md:83`) — and it lets a future extractor accidentally train on a simulator-internal quantity rather than observed traffic.
**Do this instead:** the trace stays raw; `feature_extraction/` derives everything.

### Deriving the label from the trace

**What happens:** a post-processing step labels a node malicious because its drop ratio is high.
**Why it's wrong:** the label is then a function of the features and the model learns to reproduce the labelling function rather than detect an attack. Ground truth must be independent of the observations.
**Do this instead:** join the label from the scenario config, which the operator set before the run.

### Non-deterministic iteration

**What happens:** `for node in some_set:` or `set` iteration inside mobility, radio or attack code.
**Why it's wrong:** set iteration order varies between processes, so "identical" runs differ. `AGENTS.md:175-176` lists this as a known failure point.
**Do this instead:** `sorted(...)` every set-derived ordering, and use an explicit `random.Random(seed)` rather than the module-level generator.

### Building the dashboard first

**What happens:** `dashboard/` is scaffolded in Phase 1 with a placeholder chart, and the acceptance chain is left half-built.
**Why it's wrong:** "A dashboard is secondary to this chain. Do not build one before the chain works." `AGENTS.md:166-167`. The dashboard is Phase 5 (`MANET_IDS_BTech_Execution_Guide.md:66`).
**Do this instead:** build the chain; the viewer comes last.

### Starting with six attacks and four subsystems

**What happens:** Blackhole, Grayhole, flooding, DoS, wormhole, Sybil plus deep learning, federated learning, blockchain and a mobile app, all at once.
**Why it's wrong:** `AGENTS.md:155-157` and `MANET_IDS_BTech_Execution_Guide.md:59` — reliability beats breadth for a B.Tech project. The attack order is Blackhole → Grayhole → flooding/DoS only if the first two are stable.
**Do this instead:** follow the phase order in `MANET_IDS_BTech_Execution_Guide.md:61-66` and the gates in `AGENTS.md:134-138`.

### Committing generated traces and datasets

**What happens:** `traces/*.csv` and `data/*.csv` are added to the repo.
**Why it's wrong:** `.gitignore:2-3` already excludes them and the guide is explicit: "Do not commit huge generated trace files to GitHub" (`MANET_IDS_BTech_Execution_Guide.md:175`).
**Do this instead:** commit code, scenario configs, small sample data, plots and docs; archive big experiment outputs separately (`AGENTS.md:129-130`).

---

## Error Handling

**Strategy:** *Fail fast and loudly at the boundary; never let a partial run masquerade as a complete one.*

**Patterns (prescriptive — the spec does not define an error-handling convention, so use these):**

- **Bad scenario config → hard failure, non-zero exit.** A missing file, malformed JSON, an unknown attack type, a negative node count, or a missing `seed` must abort the run with a clear message naming the offending field. Do not silently substitute defaults — a silently-defaulted node count produces a run whose config does not match its output, breaking traceability (`AGENTS.md:151`).
- **Missing dependency → fail at import with the install command.** If `simpy`/`networkx` are absent, the import error should tell the user to run `python -m pip install -r requirements.txt` (`AGENTS.md:107`).
- **Run failures must not write a partial trace that looks complete.** Either write the trace atomically (write to a temp name, then rename) or write a per-run record with a `status: "failed"` field. Windows file locking makes a partially-written CSV easy to mistake for a good one.
- **No bare `except:` and no silent `return None`.** A swallowed exception in `feature_extraction/` yields a short feature table that trains a model on garbage. Let it propagate or handle it explicitly and record it in the run record.
- **Simulation-internal errors are programming bugs, not conditions.** A `KeyError` on a route table means a logic bug in `simulator/aodv.py`; do not convert it into a graceful no-op.
- **The trace writer is the one place that must never lose an event silently** — a dropped row silently corrupts every downstream feature.

---

## Cross-Cutting Concerns

**Logging:** No logging framework is configured and none is required. Use the stdlib `logging` module for diagnostics (`logging.INFO` for the run summary, `logging.DEBUG` for per-event detail), and keep the console output terse. **The project's real observability is the metrics artifact, not log scraping**: PDR, throughput, end-to-end delay, packet loss, routing overhead (`AGENTS.md:150`), plus IDS processing time and added routing overhead (`MANET_IDS_BTech_Execution_Guide.md:259`). Console is for the operator; `results/` is for the record.

**Validation:** Validation lives at the boundaries. (a) Scenario JSON is validated once at load time in the runner — schema, ranges, referenced node ids. (b) Trace CSVs are validated once at parse time in `feature_extraction/` — required columns present, no unparseable timestamps, no duplicate `pkt_id`s within a run. (c) The feature table is validated in `ml/` — no NaN in the label column, no constant columns, group key present. Feature *values* are not range-validated against hard-coded ranges; that would embed simulator knowledge into the ML side.

**Authentication:** None, and none is needed. There are no users, no credentials, no secrets. Node identity is a simulation-internal integer (`src`/`dst` in the trace, `attacker node id` in the scenario config), not a principal. The optional dashboard binds to `127.0.0.1` and has no login (`AGENTS.md:6-7`; `MANET_IDS_BTech_Execution_Guide.md:147`).

**Provenance & reproducibility:** Every artifact chain carries identity forward — `scenario file + seed → run_id → trace filename → dataset group column → model artifact → results/runs/<run_id>.json`. This is the mechanism behind `AGENTS.md:151` and `MANET_IDS_BTech_Execution_Guide.md:320`, and it is what makes a claim like "PDR improved from 0.41 to 0.83 with the IDS on" defensible.

**Windows path safety:** The repo root path contains spaces. Use `pathlib.Path` exclusively; never build paths with `+` string concatenation or hard-coded separators; always quote paths in shell commands.

**Versioning of the schema:** The trace column set (`time, src, dst, pkt_id, type, hop_count, dropped_by, ...`) and the feature schema (9 columns + `label`) are contracts. If either changes, note it in `docs/` and regenerate dependent artifacts — do not mix traces from two schema versions in one dataset.

**Documentation sync:** Any change to this architecture must land in `AGENTS.md` **and** `MANET_IDS_BTech_Execution_Guide.md` in the same commit (`AGENTS.md:14-16,36-37`). Where they conflict, `AGENTS.md` wins on engineering rules and the guide wins on project specification.

---

*Architecture analysis: 2026-10-22 — derived from `AGENTS.md`, `MANET_IDS_BTech_Execution_Guide.md`, `.gitignore`, direct inspection of the repository, and the existing `.planning/codebase/STACK.md` and `.planning/codebase/INTEGRATIONS.md` from the tech mapping pass. No packages were installed and no network or package-manager write commands were run.*
