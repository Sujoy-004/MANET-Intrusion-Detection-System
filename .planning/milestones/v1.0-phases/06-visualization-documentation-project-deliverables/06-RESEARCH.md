# Phase 06: Visualization, Documentation & Project Deliverables - Research

**Date:** 2026-10-28  
**Phase:** 06-visualization-documentation-project-deliverables  
**Status:** Completed  
**Relevant Requirements:** RESP-03  
**Context Reference:** `.planning/phases/06-visualization-documentation-project-deliverables/06-CONTEXT.md`

---

## 1. Executive Summary & Objectives

Phase 06 represents the final capstone phase of the **Machine Learning-Based Intrusion Detection and Response System for MANET**. Its primary mission is to synthesize the empirical findings from all prior phases (Phases 1 through 5), generate high-resolution publication-grade figures, author a comprehensive 6-chapter academic B.Tech thesis, and assemble personal viva defense and live demonstration materials.

### Core Objectives
1. **Publication-Grade Plot Portfolio (`results/plots/`):** Generate clean, 300 DPI, academic whitegrid, colorblind-friendly figures visualizing the closed-loop QoS recovery triad, multi-classifier comparisons, feature importance, attack stress boundaries, and quarantine dynamics.
2. **Automated Plotting Infrastructure (`ml/plots.py` & `.archify/scripts/generate_all_plots.py`):** Provide a committed Python plotting library (`ml/plots.py`) to satisfy requirement `RESP-03` paired with an uncommitted zero-argument personal orchestration CLI (`.archify/scripts/generate_all_plots.py`) that reads authoritative CSVs and populates `.archify/PLOTS_CATALOG.md`.
3. **Formal 6-Chapter B.Tech Thesis (`docs/FINAL_PROJECT_REPORT.md`):** Deliver a monolithic academic report matching §11 of `MANET_IDS_BTech_Execution_Guide.md` featuring formal protocol/mathematical models, inline figure analysis, and strict provenance footnotes citing exact scenario JSONs, seeds, and CSV rows.
4. **Interactive Architecture Visuals (`.archify/diagrams/`):** Produce interactive, standalone HTML system architecture and closed-loop sequence diagrams using Archify (`C:\Users\KIIT0001\.agents\skills\archify\bin\archify.mjs`).
5. **Viva Defense & Live Demonstration Suite (`.archify/defense/`):** Construct an exhaustive academic viva defense guide answering all 12 guide questions, a rapid-fire one-page cheat sheet, a copy-pasteable 3-act live demonstration script (`DEMO_WALKTHROUGH.md`), and a 12–15 slide presentation deck outline.

---

## 2. Authoritative Data Sources & Provenance Architecture

All figures, tables, and claims in Phase 06 must strictly ingest authoritative CSV files already generated in `results/`. Under `AGENTS.md` Rule 8, **every number in the report must trace to a saved experiment run**.

| Source File | Dimensions / Records | Primary Contents & Metrics | Key Columns |
|---|---|---|---|
| `results/closed_loop_metrics.csv` | 36 runs (4 scenarios × 3 seeds × 3 modes) | 3-way triad QoS benchmark (`Baseline`, `Attack`, `AODV+IDS`) across Blackhole & Grayhole at 30n and 50n | `scenario, nodes, attack_type, drop_prob, seed, mode, pdr, throughput_kbps, avg_delay_ms, packet_loss_ratio, routing_overhead, delta_pdr_abs, recovery_ratio, overhead_cost` |
| `results/metrics.csv` | 3 models × 10 metrics | Phase 3/4 classifier benchmark on untouched Seed 44 test data (RF, DT, SVM) | `model, accuracy, precision, recall, f1_blackhole, fpr, tn, fp, fn, tp` |
| `results/feature_importance.csv` | 45 rows (3 models × 9 features × Gini/Permutation) | Permutation importance and Gini impurity for Random Forest, Decision Tree, SVM | `model, feature, source, importance_mean, importance_std` |
| `results/generalization_metrics.csv` | 18 parameter combinations | Generalization stress matrix across mobility speeds (1, 5, 10 m/s), drop probabilities (0.3, 0.5, 0.7), and node counts (30n, 50n) | `nodes, speed, drop_prob, seed, pdr, throughput_kbps, packet_loss_rate, avg_delay_sec, accuracy, precision, recall, f1, fpr, grayhole_recall, tp, fp, fn, tn` |
| `results/isolation_events.csv` | 142 event records | Detailed event log of all discrete mitigation actions (strikes, quarantines, expirations) | `sim_time, scenario_name, seed, node_id, strike_count, prob_malicious, predicted_type, action, quarantine_until, reason` |
| `results/closed_loop_report.md` | Markdown summary | Benchmark summary: 92.9% Blackhole PDR recovery, bounded routing overhead (+0.0307) | Key textual summaries and seed averages |

### Provenance Footnote Standard
In `docs/FINAL_PROJECT_REPORT.md`, every quantitative table and figure caption must include an explicit provenance footnote following this format:
> *Provenance:* Sourced from `results/closed_loop_metrics.csv` (scenarios: `30n_blackhole.json`, `30n_grayhole_p50.json`, `30n_grayhole_p70.json`, `50n_grayhole_p50.json`; seeds: `[42, 43, 44]`; sliding window: $W=5.0\text{s}$; quarantine policy: $K=2, \tau=0.50, \Delta t=30.0\text{s}$).

---

## 3. Plot Portfolio & Publication Visualizations

### 3.1 Academic Aesthetic & Formatting Standards (D-01, D-04)
- **Engine:** Matplotlib 3.10.8 & Seaborn 0.13.2.
- **Headless Safety:** Always execute `import matplotlib; matplotlib.use('Agg')` before importing `pyplot` to prevent Windows GUI backend errors.
- **Theme:** `sns.set_theme(style="whitegrid", font="sans-serif")`.
- **Palette:** Colorblind-friendly / academic palette (`palette="colorblind"` or custom muted tri-color scheme for triad modes):
  - Baseline AODV: Slate Blue (`#4C72B0`)
  - Attack AODV: Crimson / Coral (`#C44E52`)
  - AODV + IDS: Emerald Green (`#55A868`)
- **Resolution:** 300 DPI (`dpi=300, bbox_inches="tight"`).
- **Target Location:** `results/plots/*.png` (explicitly un-ignored in `.gitignore` line 7: `!results/plots/`, tracked in Git).

### 3.2 Required Figures Specification (D-02, D-03)

```
results/plots/
├── qos_recovery_triad_dashboard.png       # Consolidated 4-panel executive QoS overview
├── qos_pdr_recovery.png                   # Focused PDR recovery bar chart with percentage labels
├── qos_throughput_recovery.png            # Throughput (kbps) comparison across triad modes
├── qos_delay_impact.png                   # End-to-end delay (ms) trade-off analysis
├── qos_routing_overhead_penalty.png       # Routing overhead ratio showing minimal penalty (+0.0307)
├── classifier_comparison_metrics.png      # Multi-metric grouped bar chart (Accuracy, Precision, Recall, F1, FPR)
├── feature_importance_ranking.png         # Horizontal bar chart of RF Permutation vs Gini feature ranking
├── stress_mobility_vs_recall.png          # Stress curve: Mobility speed (1, 5, 10 m/s) vs Recall & F1
├── stress_droprate_vs_pdr.png             # Stress curve: Grayhole drop probability vs Network PDR & Recall
├── mitigation_quarantine_timeline.png     # Timeline visualization of strikes, quarantines, and unblocks
├── confusion_matrix_random_forest.png     # Re-styled 300 DPI confusion matrix (RF champion)
├── confusion_matrix_decision_tree.png     # Re-styled 300 DPI confusion matrix (DT baseline)
└── confusion_matrix_svm.png               # Re-styled 300 DPI confusion matrix (SVM baseline)
```

#### Detailed Plot Specifications
1. **`qos_recovery_triad_dashboard.png` (4-Panel Executive Dashboard):**
   - Panel (a): Packet Delivery Ratio (PDR) across 4 scenario conditions (30n Blackhole, 30n Grayhole p=0.5, 30n Grayhole p=0.7, 50n Grayhole p=0.5).
   - Panel (b): Throughput (kbps).
   - Panel (c): Average End-to-End Delay (ms).
   - Panel (d): Routing Overhead Ratio (routing packets / data packets).
   - Layout: $2 \times 2$ grid with shared legend at top or bottom, value callouts on bars, standard error bars across seeds 42, 43, 44.
2. **`qos_pdr_recovery.png` (Standalone PDR Chart):**
   - Compares Baseline vs Attack vs AODV+IDS with explicit recovery percentage callouts ($92.9\%$ for Blackhole, $118.6\%$ for Grayhole p=0.5).
3. **`classifier_comparison_metrics.png` (ML Evaluation Suite):**
   - Compares Random Forest, Decision Tree, and SVM across Accuracy, Precision, Recall, F1 (Malicious), and FPR.
   - Includes a red dashed reference line at $\text{FPR} = 0.01$ (1.0%) indicating the non-negotiable security operational gate.
4. **`feature_importance_ranking.png`:**
   - Top 9 features sorted by Random Forest Permutation Importance, displaying both Permutation Importance (with error bars) and Gini Impurity side-by-side.
5. **`stress_mobility_vs_recall.png` & `stress_droprate_vs_pdr.png`:**
   - Visualizes network dynamics: demonstrates how high node speed ($10\text{ m/s}$) increases route volatility and drops detection recall, and how stealthy Grayhole dropping ($p=0.3$ to $0.7$) affects delivery ratio and detection latency.
6. **`mitigation_quarantine_timeline.png`:**
   - Gantt or stem timeline showing sim time vs node isolation status, highlighting the 2-strike confirmation interval and 30-second quarantine expiration.

---

## 4. Plotting Infrastructure & CLI Architecture (D-14, D-15, D-16, D-17)

To satisfy `RESP-03` and maintain architectural clean separation:

1. **Committed Library `ml/plots.py`:**
   - Pure, reusable plotting functions:
     * `plot_qos_recovery_triad(df_closed_loop, out_dir, dpi=300)`
     * `plot_executive_dashboard(df_closed_loop, out_dir, dpi=300)`
     * `plot_classifier_comparison(df_metrics, out_dir, dpi=300)`
     * `plot_feature_importance(df_importance, out_dir, dpi=300)`
     * `plot_generalization_stress(df_gen, out_dir, dpi=300)`
     * `plot_quarantine_timeline(df_events, out_dir, dpi=300)`
     * `plot_confusion_matrices(df_metrics, out_dir, dpi=300)`
   - Pure CSV ingestion with robust fallback checks (returns descriptive error if required CSV is missing).
   - Full test coverage in `tests/test_plots.py`.

2. **Personal Orchestrator `.archify/scripts/generate_all_plots.py` (Uncommitted):**
   - Zero-argument CLI: `python .archify/scripts/generate_all_plots.py`
   - Ingests all CSVs from `results/` and outputs all 300 DPI figures to `results/plots/`.
   - Generates `.archify/PLOTS_CATALOG.md` containing thumbnail previews, file sizes, image resolutions, and source CSV lineages.
   - CLI overrides: `--results-dir`, `--plots-dir`, `--dpi`, `--catalog-path`.

---

## 5. Archify Interactive Visualizations (`.archify/diagrams/`)

### 5.1 Tooling & Verification
- Archify binary: `C:\Users\KIIT0001\.agents\skills\archify\bin\archify.mjs`
- Node.js runtime: Verified v24.14.0 on Windows (`archify doctor` passed with 100% OK).
- Validation command: `node "C:\Users\KIIT0001\.agents\skills\archify\bin\archify.mjs" validate <type> <json>`
- Render command: `node "C:\Users\KIIT0001\.agents\skills\archify\bin\archify.mjs" render <type> <input.json> <output.html> --quality showcase`

### 5.2 Deliverable Diagrams

1. **System Architecture (`.archify/diagrams/system_architecture.json` -> `.html`):**
   - Type: `architecture` (schema_version: 1).
   - Components:
     * *Simulation Subsystem:* SimPy Event Engine, RWP Mobility Model, Dynamic Radio Graph (Euclidean range $R=250\text{m}$), RFC 3561 AODV State Machine, CBR/UDP Traffic Generator.
     * *Attack Injection Subsystem:* Decoupled Strategy Pattern (`BlackholeStrategy`, `GrayholeStrategy`), Dynamic Placement Seam.
     * *Feature Engineering Subsystem:* Non-leaking Trace Logger, Sliding-Window Aggregator ($W=5.0\text{s}$), Anti-leakage Scaler.
     * *Machine Learning Engine:* Random Forest Champion Pipeline, Decision Tree & SVM Baselines, FPR $\le 0.01$ Gate.
     * *Closed-Loop Response Subsystem:* `OnlineIDS` Controller, In-memory Sliding Deque, 2-Strike Confirmation ($K=2, \tau=0.50$), 30-second Quarantine Table, AODV Route Invalidator (`invalidate_routes_through`), Flow Endpoint Protection.
   - Boundaries: `Simulation Runtime`, `Feature Pipeline`, `ML Detection & Response`.

2. **Closed-Loop Mitigation Sequence (`.archify/diagrams/closed_loop_sequence.json` -> `.html`):**
   - Type: `sequence` (schema_version: 1).
   - Participants: `AppTraffic`, `AODVNode`, `MaliciousNode`, `TraceLogger`, `OnlineIDS`, `MLClassifier`, `QuarantineTable`, `RouteTable`.
   - Flow:
     * Traffic transmission & malicious packet drop.
     * Periodic telemetry collection ($t=5.0\text{s}$).
     * Sliding-window feature extraction.
     * ML inference ($P(\text{malicious}) \ge 0.50$).
     * Strike 1 logged.
     * Subsequent window ($t=10.0\text{s}$): Strike 2 confirmed!
     * Quarantine triggered: Node added to blacklist for $30.0\text{s}$.
     * Route invalidation: Route table purges all entries pointing to attacker.
     * Fresh RREQ flood initiated; alternate honest route established.
     * PDR restored to baseline levels.

---

## 6. Monolithic 6-Chapter B.Tech Thesis (`docs/FINAL_PROJECT_REPORT.md`)

The comprehensive thesis report must be written in GitHub-flavored Markdown at `docs/FINAL_PROJECT_REPORT.md`. It must rigorously mirror §11 of `MANET_IDS_BTech_Execution_Guide.md` while incorporating all technical specifics, mathematical formulations, and empirical tables.

### Chapter Breakdown & Essential Content

#### Chapter 1: Introduction
- **Background & Context:** MANET fundamentals (infrastructureless, decentralized, multi-hop routing, open RF medium, dynamic topology).
- **The Security Challenge:** Why traditional perimeter security fails; vulnerability of cooperative routing protocols to inside attacks.
- **Problem Statement:** Impact of sequence number spoofing (Blackhole) and selective packet forwarding (Grayhole) on QoS.
- **Objectives & Scope:** Pure-Python Windows-native simulator, anti-leakage feature pipeline, seed-holdout ML evaluation, closed-loop mitigation demonstrating QoS recovery.
- **Key Contributions & Deliverables:** End-to-end reproducible chain, 92.9% PDR recovery, bounded routing overhead (+0.0307).

#### Chapter 2: Literature Review
- **Routing in Ad-Hoc Networks:** Proactive (OLSR, DSDV) vs Reactive (AODV RFC 3561, DSR). Detailed analysis of AODV message exchange (RREQ, RREP, RERR) and destination sequence numbers.
- **Attack Taxonomies:** Blackhole attacks (fictitious high sequence number $2^{32}-1$, minimum hop count $1$), Grayhole attacks (honest control path, probabilistic or periodic data dropping), DoS flooding.
- **Intrusion Detection Systems in MANET:** Standalone vs Distributed vs Hierarchical; Anomaly-based vs Misuse-based.
- **Machine Learning for MANET Security:** Survey of Decision Trees, Random Forests, SVMs, and neural approaches; identification of common methodological flaws (random row splitting, temporal autocorrelation, ground-truth label leakage).
- **Identified Research Gap:** Lack of reproducible, closed-loop evaluation comparing network QoS recovery under identical deterministic seeds.

#### Chapter 3: System Design
- **System Architecture:** Detailed block diagram and dataflow between simulator, trace logger, feature pipeline, ML classifier, and online response controller.
- **Formal Protocol & Mathematical Models:**
  * RFC 3561 Sequence Number comparison: $SeqNum_A > SeqNum_B \lor (SeqNum_A = SeqNum_B \land HopCount_A < HopCount_B)$
  * SimPy discrete-event clock scheduling formulation.
  * Random Waypoint Mobility equations ($x(t), y(t)$ with uniform velocity $v \in [v_{\min}, v_{\max}]$ and pause time $t_p$).
  * Sliding-window feature extraction equations ($W=5.0\text{s}$, backward aggregation): Forwarding Ratio, Drop Ratio, Average Delay, RREQ/RREP rates, Throughput, Hop Count.
  * Cost-sensitive ML formulation: Balanced class weighting $w_j = \frac{N}{2 \cdot N_j}$.
  * Closed-loop 2-strike confirmation filter: $K=2$ consecutive windows with $P(\text{malicious}) \ge \tau = 0.50$.
  * Quarantine decay function: $t_{\text{unblock}} = t_{\text{quarantine}} + \Delta t_{\text{cooling}}$ ($\Delta t = 30.0\text{s}$).
  * Dynamic route invalidation algorithm (`invalidate_routes_through`).

#### Chapter 4: Implementation
- **In-Repo Pure-Python Simulator Engine:** Modules `node.py`, `mobility.py`, `radio.py`, `aodv.py`, `traffic.py`, `metrics.py`. Rationale for eliminating NS-3 and C++ toolchains.
- **Decoupled Attack Strategies:** `BlackholeStrategy` (spoofed RREP, zero-forwarding) and `GrayholeStrategy` (honest AODV routing, Bernoulli $p \in \{0.3, 0.5, 0.7\}$ drop). Dynamic flow-intercept placement.
- **Feature Extraction & Dataset Pipeline:** Non-leaking CSV trace logger, sliding window computation, anti-leakage neutral fallbacks, seed-based dataset partitioning (`data/train.csv` seeds 42, 43; `data/test.csv` seed 44).
- **Machine Learning Pipelines:** Scikit-learn uniform pipelines with `StandardScaler` and `class_weight='balanced'`. Random Forest, Decision Tree, Support Vector Machine.
- **Closed-Loop Response Integration:** `OnlineIDS` controller, in-memory deque, real-time feature alignment, AODV route table purging, flow source/destination endpoint protection.

#### Chapter 5: Results and Analysis
- **Classifier Benchmark & Model Selection:** Comparative performance table on Seed 44 test data; enforcement of the operational gate $\text{FPR} \le 0.01$; selection of Random Forest as champion (F1 0.7593, FPR 0.0099).
- **Feature Importance Analysis:** Gini impurity vs Permutation Importance; discussion of `packet_drop_ratio` ($0.2156$), `hop_count` ($0.1685$), and `packet_forward_ratio` ($0.0147$) as primary indicators.
- **Generalization & Environmental Stress:** 18-combination matrix across node speeds ($1, 5, 10\text{ m/s}$), drop rates ($0.3, 0.5, 0.7$), and network densities ($30\text{n}, 50\text{n}$). Analysis of recall degradation at $10\text{ m/s}$ due to route breakage.
- **Closed-Loop Comparative Triad Benchmark:** 36-run matrix (`Baseline` vs `Attack` vs `AODV+IDS` across seeds 42, 43, 44).
  * 30n Blackhole: PDR drops from $0.6366$ to $0.1418$; AODV+IDS recovers to $0.6101$ ($92.9\%$ recovery ratio, $+0.4683$ absolute $\Delta$PDR).
  * 30n Grayhole ($p=0.5$): PDR drops to $0.5634$; recovers to $0.6935$ ($118.6\%$ recovery ratio).
  * Routing Overhead Cost: Bounded penalty of $+0.0307$ (Blackhole) and $+0.0098$ (Grayhole), proving lightweight mitigation.
- **Inline Figures & Commentary:** Direct Markdown embeds of all generated plots in `../results/plots/` with detailed analytical narratives.
- **Strict Provenance Footnotes:** Verified references for every empirical claim.

#### Chapter 6: Conclusion and Future Work
- **Summary of Findings:** Validation of the end-to-end demonstration chain; proof of QoS recovery; verification of all non-negotiable engineering gates.
- **Technical Limitations:** Discrete-event packet abstraction vs physical multi-path fading; 2D flat topology; single-attacker scenario assumption.
- **Future Work:** Multi-attacker collusive attacks, distributed cooperative trust voting, cross-layer MAC 802.11 contention metrics, web-based replay dashboard.

#### Appendices
- **Appendix A:** Scenario JSON Configuration Schemas.
- **Appendix B:** Full Test Suite Verification Matrix (59/59 tests passing).
- **Appendix C:** Complete CLI Reproduction Playbook.

---

## 7. Viva Defense & Live Demonstration Suite (`.archify/defense/`)

All files in this section reside in `.archify/defense/` (uncommitted, gitignored).

### 7.1 Comprehensive Academic Question Bank (`VIVA_DEFENSE_GUIDE.md`)
Must provide in-depth technical answers for all 12 questions from §12 of the execution guide, plus project-specific architectural inquiries:
1. *Why is MANET more vulnerable than conventional networks?* (Lack of centralized perimeter, dynamic topology, shared wireless broadcast medium, cooperative trust assumption).
2. *Why choose AODV over DSR or OLSR?* (On-demand reactive efficiency avoids proactive periodic broadcast overhead in bandwidth-constrained networks; destination sequence numbers guarantee loop-freeness).
3. *What constitutes an intrusion in MANET?* (Behavioral deviation from RFC 3561 compliance resulting in unauthorized traffic diversion, interception, or intentional disruption).
4. *How does Blackhole exploit AODV sequence numbers?* (Crafts RREP with maximum sequence number $2^{32}-1$ and hop count $1$, guaranteeing that source routes traffic through the attacker).
5. *How were ground-truth labels generated without leakage?* (Derived purely from scenario configuration knowledge of attacker node ID and attack activation window; never logged in packet traces or feature vectors).
6. *Why are Accuracy and F1-score both required?* (Extreme class imbalance: attack samples represent $\approx 2.3\%$ of observation windows; an idle classifier achieves $97.7\%$ accuracy with $0\%$ recall).
7. *How was data leakage avoided?* (Zero random row splitting; partitioning strictly by independent simulation seeds; sliding window strictly aggregates backwards $t-W \le t_{event} \le t$; neutral fallbacks for zero-traffic nodes).
8. *Why Random Forest over Deep Learning?* (Tabular network telemetry with low sample count; fast microsecond CPU inference suitable for real-time closed-loop control; zero GPU dependencies; superior interpretability via feature importance).
9. *How does mobility affect IDS performance?* (High speed $10\text{ m/s}$ increases link breakage and natural packet drops, conflating mobility-induced loss with malicious dropping and reducing detection recall).
10. *What happens after a node is quarantined?* (AODV table invalidates routes pointing through the node, drops incoming RREPs from it, and broadcasts fresh RREQs to discover alternative honest routes).
11. *What is the routing overhead introduced by the IDS?* (Measured as $+0.0307$ routing packets per data packet in Blackhole, caused by rediscovery RREQs; highly bounded and acceptable).
12. *How would the system behave against zero-shot / unseen attacks?* (Evaluated on Grayhole without training: achieved $28.0\%$ zero-shot recall; retrained multi-attack model achieved $75.9\%$ F1).
13. *Why was NS-3 replaced with pure-Python SimPy?* (Windows-native execution without C++ build failures; discrete-event determinism; 300s simulation runs in $0.83\text{s}$ wall clock vs minutes in NS-3).

### 7.2 One-Page Viva Table Cheat Sheet (`ONE_PAGE_CHEAT_SHEET.md`)
A high-density quick reference for the student's desk:
- **Key Empirical Numbers:**
  * Blackhole Baseline PDR: $63.66\%$ $\to$ Attack PDR: $14.18\%$ $\to$ AODV+IDS PDR: $61.01\%$ ($92.9\%$ recovery).
  * Grayhole ($p=0.5$) Recovery: $118.6\%$ ($56.34\% \to 69.35\%$).
  * Routing Overhead Penalty: $+0.0307$ (Blackhole), $+0.0098$ (Grayhole).
  * Champion Model (Random Forest): Accuracy $97.44\%$, F1 $75.93\%$, FPR $0.99\%$ (under $1.0\%$ gate), Latency $61.59\text{ms}$.
  * Top Features: Packet Drop Ratio ($0.2156$), Hop Count ($0.1685$), Forwarding Ratio ($0.0147$).
  * Dataset: 52,200 total samples across seeds 42, 43, 44.
  * Confirmation Policy: $K=2$ strikes, $\tau=0.50$ threshold, $W=5.0\text{s}$ window, $30.0\text{s}$ quarantine cooling.

### 7.3 Interactive 3-Act Demonstration Script (`DEMO_WALKTHROUGH.md`)
A structured 10-minute presentation walkthrough with exact PowerShell commands:
- **Act 1: Baseline Normal Network (Honest AODV):**
  * Command: `python simulator/run_scenario.py --scenario scenarios/e1_baseline_30n.json --seed 42 --out traces/demo_baseline.csv`
  * Action: Highlight clean routing, high PDR ($>63\%$), zero drops.
- **Act 2: Malicious Attack Injection (Blackhole Active, IDS Off):**
  * Command: `python simulator/run_scenario.py --scenario scenarios/e2_blackhole_onset_30n.json --seed 42 --out traces/demo_attack.csv`
  * Action: Show route diversion to node 21, data packets dropped, PDR collapse to $<15\%$.
- **Act 3: Closed-Loop Detection & Quarantine (AODV + OnlineIDS):**
  * Command: `python simulator/run_scenario.py --scenario scenarios/e2_blackhole_onset_30n.json --seed 42 --ids --out traces/demo_ids.csv`
  * Action: Point to live console logs: Strike 1 at $t=5.5\text{s}$, Strike 2 & Quarantine at $t=7.0\text{s}$, Route Invalidation trigger, alternate route establishment, PDR recovery to $>61\%$.

### 7.4 Presentation Deck Structure (`PRESENTATION_DECK_OUTLINE.md`)
A 14-slide academic presentation structure including slide titles, bullet points, talking scripts, and diagram placements for Microsoft PowerPoint.

---

## 8. Potential Pitfalls & Mitigation Strategies

| Pitfall | Risk | Mitigation Strategy |
|---|---|---|
| **Matplotlib Headless Crash** | `pyplot` attempting to open interactive Windows GUI during automated batch plotting. | Force `matplotlib.use('Agg')` at the top of `ml/plots.py` and `generate_all_plots.py` before any other matplotlib imports. |
| **Number Inconsistency (Rule 8)** | Discrepancy between thesis text and empirical CSV outputs. | Scripted table generation or direct programmatic verification linking text tables to CSV columns. |
| **Broken Markdown Image Links** | Relative links breaking when rendered in GitHub vs local viewers. | Use canonical relative paths `../results/plots/<name>.png` from `docs/` and verify in both previewers. |
| **Archify Schema Rejection** | Invalid JSON syntax or missing coordinates causing Archify rendering failure. | Run `node archify.mjs validate <type> <json>` before running `render`. Keep coordinates within standard viewBox. |
| **Accidental Git Tracking of `.archify/`** | Committing personal materials to public repository. | Verified: `.gitignore` already contains `.archify/`. Always verify `git status` before commit. |
| **Incomplete Requirement Coverage (`RESP-03`)** | Reviewer checks for committed plotting code while plots were only generated via uncommitted script. | Provide committed `ml/plots.py` module implementing `RESP-03` with pytest tests, while keeping personal CLI orchestrator in `.archify/scripts/`. |

---

## 9. Recommended Plan Breakdown for Phase 06

Phase 06 is cleanly partitioned into two sequential, highly cohesive plans:

### Plan 06-01: Publication Plot Portfolio & Plotting Suite Automation
- **Goal:** Implement the committed plotting suite `ml/plots.py`, generate all high-resolution 300 DPI figures in `results/plots/`, build the uncommitted orchestrator `.archify/scripts/generate_all_plots.py`, generate `.archify/PLOTS_CATALOG.md`, and verify requirement `RESP-03` with unit tests.
- **Key Artifacts:**
  * `ml/plots.py` (Committed plotting library)
  * `tests/test_plots.py` (Unit tests for plotting)
  * `results/plots/*.png` (12+ publication-grade 300 DPI figures)
  * `.archify/scripts/generate_all_plots.py` (Uncommitted zero-arg CLI)
  * `.archify/PLOTS_CATALOG.md` (Uncommitted visual catalog)

### Plan 06-02: 6-Chapter Thesis Report, Interactive Archify Diagrams & Viva Defense Suite
- **Goal:** Render interactive HTML system architecture and sequence diagrams via Archify, author the comprehensive 6-chapter B.Tech thesis (`docs/FINAL_PROJECT_REPORT.md`) with strict provenance footnotes, and create the complete viva defense, cheat sheet, and 3-act live demonstration guide in `.archify/defense/`.
- **Key Artifacts:**
  * `docs/FINAL_PROJECT_REPORT.md` (Committed 6-chapter thesis report)
  * `.archify/diagrams/system_architecture.json` & `.html`
  * `.archify/diagrams/closed_loop_sequence.json` & `.html`
  * `.archify/defense/VIVA_DEFENSE_GUIDE.md`
  * `.archify/defense/ONE_PAGE_CHEAT_SHEET.md`
  * `.archify/defense/DEMO_WALKTHROUGH.md`
  * `.archify/defense/PRESENTATION_DECK_OUTLINE.md`

---

## RESEARCH COMPLETE
