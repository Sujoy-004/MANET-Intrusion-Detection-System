# Machine Learning-Based Intrusion Detection System for MANET

*A Step-by-Step B.Tech Major Project Execution Handbook*

**Project mode:** 100% software/simulation based  
**Primary simulator:** In-repo pure-Python MANET simulator (SimPy + NetworkX)  
**Language:** Python only  
**ML:** Python + Scikit-learn

> **Architecture revision.** This project runs natively on Windows in pure Python. The
> original draft assumed NS-3 with C++ on Ubuntu; those sections are superseded. `AGENTS.md`
> carries the binding engineering rules and takes precedence where the two files differ.

## Purpose

This handbook is designed to take a student team from zero to a demonstrable, measurable MANET Intrusion Detection System (IDS). The recommended implementation detects malicious behavior in a simulated Mobile Ad Hoc Network, evaluates ML classifiers, and then adds a response mechanism that prevents detected malicious nodes from being preferred in subsequent routes.

The project should be treated as an engineering experiment: establish a reproducible baseline, introduce controlled attacks, collect data, train models, validate them on unseen scenarios, integrate detection with routing response, and compare the final system against baseline AODV.

### Recommended final title

**Machine Learning-Based Adaptive Intrusion Detection and Response System for Mobile Ad Hoc Networks**

If your guide wants a simpler title, use: **Machine Learning-Based Intrusion Detection System for MANET**.

---

## 1. What You Are Building

A MANET is a collection of mobile nodes that communicate without fixed infrastructure. Routing is dynamic because nodes move and links appear/disappear. This makes the network vulnerable to nodes that deliberately behave abnormally.

Your IDS will observe network behavior, convert it into measurable features, classify nodes/traffic as normal or malicious, and generate an intrusion response.

### Target architecture

```text
Python MANET Simulator → AODV → Traffic/Attack Simulation → Trace Collection
→ Feature Extraction → Dataset → ML Training → IDS Prediction
→ Alert/Isolation → Network Re-evaluation
```

### Minimum viable project (MVP)

- Create a reproducible MANET using the in-repo Python simulator and AODV.
- Create normal traffic and at least two attack scenarios.
- Extract network features from simulation traces.
- Build a labeled dataset.
- Train and compare at least three ML classifiers.
- Evaluate using accuracy, precision, recall, F1-score and confusion matrix.
- Integrate a response mechanism that identifies/excludes detected malicious nodes.
- Compare baseline AODV versus AODV + IDS using PDR, throughput, delay and packet loss.

### Recommended attack progression

Start with Blackhole because it is easy to demonstrate and directly affects packet delivery. Then add Grayhole for a harder detection problem. Add flooding/DoS only after the first two are stable.

## 2. Scope: Do Not Overbuild

For a B.Tech project, reliability is more valuable than a long attack list. Do not begin with six attacks, deep learning, federated learning, blockchain and a mobile application simultaneously.

0. **Phase 0:** Build and validate the Python simulator (replaces the former "install NS-3" step).
1. **Phase 1:** AODV + Blackhole + data collection.
2. **Phase 2:** ML classification.
3. **Phase 3:** Grayhole + generalization testing.
4. **Phase 4:** IDS response and performance comparison.
5. **Phase 5:** Dashboard, documentation and presentation.

### Stretch features, only if the core system works

- XGBoost/ensemble comparison.
- Online/incremental learning.
- Explainable AI with SHAP.
- Additional attack classes.
- Web dashboard.
- Cross-scenario validation with different node counts and mobility speeds.

### Important academic rule

Do not claim that your model “detects all MANET attacks”. State exactly which attacks, traffic conditions, mobility models and simulator settings were evaluated. Your conclusions must be supported by measured experiments.

## 3. System Architecture in Detail

### Module A — Network Simulator

Implemented in-repo under `simulator/` (pure Python, no external simulator to install).

- Create N mobile nodes.
- Configure wireless channel and propagation model.
- Configure mobility.
- Implement AODV (route discovery, route maintenance, sequence numbers).
- Create UDP/CBR or similar application traffic.
- Run the simulation and save trace/output data.

### Module B — Attack Generator

Implemented in-repo under `attacks/`, injected into the simulator at run time.

- Select one or more malicious nodes.
- Implement attack-specific abnormal behavior.
- Keep attack timing and node IDs controlled so labels can be generated reliably.

### Module C — Feature Extraction

Convert raw traces into one row per observation window or node. A practical first schema is:

| Feature | Meaning |
|---|---|
| `packet_forward_ratio` | Forwarded packets relative to packets expected/received |
| `packet_drop_ratio` | Fraction of packets dropped |
| `avg_delay` | Average observed packet delay |
| `route_request_rate` | RREQ activity in a time window |
| `route_reply_rate` | RREP activity in a time window |
| `throughput` | Successfully delivered data rate |
| `hop_count` | Observed route length |
| `neighbor_count` | Number of relevant neighbors |
| `mobility_speed` | Node speed in the simulation |
| `label` | Normal / Blackhole / Grayhole / other |

### Module D — ML Engine

- Clean missing/invalid values.
- Split data by simulation scenario, not randomly by rows alone, when possible.
- Scale features only when the selected algorithm requires it.
- Train baseline models.
- Tune only after establishing a baseline.
- Save the final model and preprocessing pipeline.

### Module E — IDS Response

- Generate an alert when confidence exceeds a predefined threshold.
- Assign the node a malicious/low-trust state.
- Prevent or discourage routing through that node.
- Re-run the same scenario and quantify whether network performance improves.

## 4. Environment Setup

### Recommended development environment

| Component | Recommendation |
|---|---|
| OS | Windows 10/11 (native). No Linux VM, WSL or Docker needed |
| Simulator | In-repo pure-Python MANET simulator — SimPy for the event clock, NetworkX for topology |
| Language | Python only (3.11+). No C++, no compiler toolchain |
| ML | NumPy, Pandas, Scikit-learn, Matplotlib, Seaborn |
| Version control | Git + GitHub |
| Editor | VS Code |
| Optional | Jupyter Notebook, Flask/FastAPI dashboard |

### Setup checklist

- Install Python 3.11+ and create a project virtual environment.
- Install pandas, numpy, scikit-learn, matplotlib, seaborn, networkx and simpy.
- Install Git and create a private/public repository.
- Build the simulator, then validate it against expected AODV behaviour (PDR falls with
  distance and load, hop count grows with distance, routing overhead is non-zero) before
  writing any ML code.

### Repository structure

```text
manet-ids/
├── simulator/          # mobility, radio, AODV, traffic, metrics, CLI
├── scenarios/          # one config per experiment
├── attacks/            # blackhole / grayhole behaviour strategies
├── traces/
├── data/
├── feature_extraction/
├── ml/
├── results/
├── dashboard/
├── docs/
└── README.md
```

Do not commit huge generated trace files to GitHub. Keep code, configuration, small sample data and documentation under version control; archive large experiment outputs separately. Add `traces/` and `data/` to `.gitignore`.

## 5. Step-by-Step Implementation

### Step 1 — Build the normal MANET

- Create 20–30 nodes initially.
- Use a controlled area and mobility model.
- Install AODV.
- Create one or more source-destination pairs.
- Generate UDP traffic.
- Run 30–60 second simulations.
- Verify that packets reach destinations.

**Gate:** Do not implement ML until your normal AODV simulation works repeatedly with sensible output.

### Step 2 — Establish a baseline

- Run multiple seeds.
- Record PDR, throughput, delay, packet loss and routing overhead.
- Store the configuration for every run.

### Step 3 — Add Blackhole

- Select a malicious node.
- Make it advertise attractive routes while failing to forward data as expected.
- Verify visually/numerically that packet delivery decreases.

**Gate:** You must be able to demonstrate that the attack changes measurable network behavior before attempting detection.

### Step 4 — Generate labeled data

- Run normal scenarios and attack scenarios.
- Vary node count, mobility, traffic rate and attacker position.
- Extract features in fixed time windows.
- Label observations using the known simulation ground truth.

### Step 5 — Train baseline ML models

- Start with Decision Tree.
- Then Random Forest.
- Then SVM or XGBoost.
- Use the same train/test protocol for fair comparison.
- Generate confusion matrix and classification metrics.

### Step 6 — Test generalization

- Do not only test on data generated under identical settings.
- Train on some seeds/configurations and test on unseen seeds/configurations.
- Test at least one different node density and mobility condition.

### Step 7 — Add Grayhole

- Implement selective packet dropping.
- Re-run feature generation.
- Determine whether the model trained on blackhole-only data generalizes.
- If it does not, explicitly document the limitation and retrain a multi-class model.

### Step 8 — Integrate response

- Define a detection threshold.
- Flag suspicious nodes.
- Modify route selection/participation so flagged nodes are avoided.
- Compare network performance before and after response.

## 6. Experimental Design

A major-project evaluation should contain controlled experiments rather than a single demo.

| Experiment | Variables | Purpose |
|---|---|---|
| E1 Normal | 20/30/50 nodes | Baseline behavior |
| E2 Blackhole | 1 attacker, varied position | Verify attack impact |
| E3 ML comparison | DT/RF/SVM or XGBoost | Compare classifiers |
| E4 Mobility | Low/medium/high speed | Robustness to mobility |
| E5 Traffic | Low/medium/high load | Robustness to congestion |
| E6 Grayhole | Different drop rates | Harder attack detection |
| E7 Response | IDS off/on | Measure security benefit |
| E8 Unseen scenario | New seed/configuration | Generalization |

### Minimum metrics

- **Detection:** Accuracy, Precision, Recall, F1-score, False Positive Rate, confusion matrix.
- **Network:** Packet Delivery Ratio, throughput, end-to-end delay, packet loss, routing overhead.
- **Cost:** IDS processing time and additional routing/communication overhead if measurable.

Avoid accuracy-only claims. In security problems, a model can appear highly accurate while missing most attacks if the dataset is imbalanced. Recall, precision and F1-score are essential.

### Suggested plots

- Confusion matrix for each classifier.
- Precision/Recall/F1 comparison bar chart.
- PDR vs. number of malicious nodes.
- Throughput vs. attack intensity.
- End-to-end delay with IDS OFF vs ON.
- Detection rate vs. mobility speed.

## 7. 21-Day Execution Plan

This schedule assumes a 3–4 person team working consistently. If you have more academic workload, extend each phase rather than skipping validation.

| Day | Work | Deliverable |
|---|---|---|
| **Day 1 — Freeze scope** | Finalize title, attack set, routing protocol, simulator, ML models and deliverables. Create Git repository. | One-page scope, team responsibilities, and repository. |
| **Day 2 — Environment + simulator core** | Set up the Python environment, install dependencies, record versions. Implement mobility, radio, AODV and traffic generation. | Simulator core runs. |
| **Day 3 — MANET baseline** | Validate the simulator against expected AODV behaviour, then create a 20–30 node mobile network with AODV and UDP traffic. | Validated simulator, first successful MANET run. |
| **Day 4 — Baseline metrics** | Add PDR, throughput, delay, packet loss and routing overhead extraction. | Baseline results. |
| **Day 5 — Repeatability** | Run multiple random seeds and verify results are stable and files are organized. | Reproducible baseline. |
| **Day 6 — Blackhole** | Implement or adapt a controlled blackhole attack. Validate attack behavior. | Working attack scenario. |
| **Day 7 — Attack metrics** | Compare normal vs blackhole network behavior. Produce first plots. | Attack validation report. |
| **Day 8 — Trace pipeline** | Design feature schema and extract node/time-window features from traces. | CSV dataset pipeline. |
| **Day 9 — Dataset generation** | Generate normal and blackhole datasets across multiple seeds/settings. | Versioned dataset. |
| **Day 10 — Data cleaning** | Handle missing values, duplicates, class imbalance and preprocessing. | Clean training dataset. |
| **Day 11 — First ML model** | Train Decision Tree and establish baseline classification results. | Baseline classifier. |
| **Day 12 — Model comparison** | Train Random Forest and SVM/XGBoost. Compare precision, recall, F1 and false positives. | Model comparison table. |
| **Day 13 — Error analysis** | Inspect false positives/negatives and determine which features drive errors. | Error analysis. |
| **Day 14 — Generalization** | Test on unseen seeds, node counts or mobility conditions. | Generalization results. |
| **Day 15 — Grayhole** | Implement selective dropping and create a second attack dataset. | Grayhole scenario. |
| **Day 16 — Multi-attack IDS** | Train/evaluate a model that distinguishes normal, blackhole and grayhole, or clearly justify a binary classifier candidate. | Final design. |
| **Day 17 — Response** | Connect IDS output to node isolation/route avoidance. Compare IDS OFF vs ON. | Working detection-response loop. |
| **Day 18 — Full experiments** | Run the complete experiment matrix with controlled seeds and configurations. | Final raw results. |
| **Day 19 — Dashboard & plots** | Build a lightweight dashboard or results viewer; finalize publication-quality figures. | Demonstration interface. |
| **Day 20 — Report** | Write methodology, experiments, results, limitations, conclusion and future work. Add architecture diagrams. | Complete draft. |
| **Day 21 — Validation & defense** | Re-run key experiments, verify every reported number, prepare PPT, demo script and likely viva questions. | Final project package. |

## 8. Team Division

| Role | Primary responsibility | Secondary |
|---|---|---|
| Member 1 — Network | Python simulator: AODV, mobility, radio, attack implementation | Network metrics |
| Member 2 — Data/ML | Trace parsing, feature engineering, models | Statistical evaluation |
| Member 3 — IDS/Integration | Detection logic, response, route exclusion | Testing |
| Member 4 — UI/Documentation | Dashboard, plots, report, PPT | Experiment management |

Every member should understand the complete pipeline. Do not create a situation where only one student can run the project.

## 9. Common Failure Points

- **Starting with ML:** Fix the simulator and attack behavior first.
- **Random row split:** Rows from the same simulation can be highly correlated. Prefer scenario/seed-based holdout for a stronger evaluation.
- **Data leakage:** Do not include a feature that directly reveals the ground-truth attacker identity or attack label.
- **Too little data:** Generate multiple independent seeds and configurations.
- **Overfitting:** Excellent test accuracy on nearly identical simulations is not proof of robustness.
- **Unclear attack implementation:** Demonstrate the attack independently before training the detector.
- **No baseline:** Always compare against standard AODV without IDS.
- **Unverified numbers:** Every number in the report should trace back to a saved experiment.

## 10. Final Deliverables

- Source code with reproducible configuration.
- Python simulator source and scenario configuration files.
- Attack implementations.
- Feature extraction scripts.
- Clean datasets or dataset-generation scripts.
- Trained ML model and preprocessing pipeline.
- Experiment results and plots.
- IDS response mechanism.
- Optional dashboard.
- Project report.
- Presentation and live demonstration.

## 11. Report Structure

### Chapter 1 — Introduction

MANET background, security problem, motivation, objectives and contributions.

### Chapter 2 — Literature Review

MANET routing, AODV, intrusion attacks, IDS approaches, ML-based detection, research gap.

### Chapter 3 — System Design

Architecture, attack model, feature design, ML pipeline, detection and response algorithm.

### Chapter 4 — Implementation

Simulator design and implementation (mobility, radio model, AODV, traffic, attacks), dataset generation and ML implementation.

### Chapter 5 — Results and Analysis

Classifier comparison, attack detection, generalization, network performance, IDS response.

### Chapter 6 — Conclusion and Future Work

Findings, limitations and extensions.

## 12. Viva Questions You Should Be Able to Answer

- Why is MANET more vulnerable than a conventional infrastructure-based network?
- Why did you choose AODV?
- What exactly is an intrusion in your project?
- How does a blackhole attack affect AODV?
- How did you generate the ground-truth labels?
- Why are accuracy and F1-score both required?
- How did you avoid data leakage?
- Why did you choose Random Forest over the other models?
- How does mobility affect IDS performance?
- What happens after a node is detected as malicious?
- What is the overhead introduced by your IDS?
- How would the system behave against an attack not present in the training set?

## 13. Definition of Success

The project is successful when you can reproduce the following chain on demand: launch simulation → generate normal/attack traffic → extract features → run trained IDS → identify malicious behavior → trigger response → show measurable improvement compared with baseline. A polished dashboard is secondary to this chain.

### Recommended final demonstration

Show two identical MANET scenarios side-by-side: standard AODV and AODV with your IDS. Introduce the same malicious node. Show the attack reducing packet delivery in the baseline, then show the IDS detecting/isolating the node and the resulting recovery in PDR/throughput. Finally display the ML confusion matrix and classifier comparison.

## Mentor checkpoint rule

At the end of each week, freeze a working version. Never continue adding features to a broken foundation. If an advanced feature threatens the core demonstration, remove the advanced feature and preserve the reproducible baseline.

## Final note

The technically strongest version of this project is not the one with the largest number of algorithms. It is the one with a clean experimental design, reproducible simulation, realistic attack behavior, leakage-free evaluation, measurable IDS overhead, and a clear security improvement over baseline AODV.
