# Phase 06: Visualization, Documentation & Project Deliverables - Context

**Gathered:** 2026-10-28  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Phase 06 delivers the final consolidation, publication-quality visualizations, and academic project deliverables for the Machine Learning-Based Intrusion Detection and Response System for MANET. It produces committed, high-resolution figures in `results/plots/` (QoS recovery triad, multi-classifier comparison, ROC/PR curves, feature importance, attack stress curves), the comprehensive 6-chapter B.Tech thesis document in `docs/FINAL_PROJECT_REPORT.md` with strict data provenance tracing back to experiment CSVs, and generates uncommitted personal materials inside `.archify/` (Archify architecture diagrams, Viva defense question bank, and a zero-argument plot generator script).

</domain>

<decisions>
## Implementation Decisions

### 1. Plot Portfolio & Visualization Styling (Committed to `results/plots/`)
- **D-01:** Academic Seaborn whitegrid Styling — Publication-ready theme using `sns.set_theme(style="whitegrid")` with a muted/colorblind-friendly palette, distinct markers, and clear typography suitable for paper printing and slide decks. — **Reversibility:** reversible.
- **D-02:** Consolidated 4-Panel Executive Dashboard + Dedicated Individual Metric Figures — Generate individual standalone plots for each QoS metric (PDR, Throughput, Delay, Routing Overhead) across the Baseline vs Attack vs AODV+IDS triad for Blackhole and Grayhole across 30n and 50n, plus a 4-in-1 consolidated executive summary figure. — **Reversibility:** reversible.
- **D-03:** Full ML Evaluation Suite & Attack Stress Curves — Generate multi-classifier comparison bar chart (F1, Precision, Recall, FPR), ROC and Precision-Recall curves, feature importance ranking chart, and attack stress curves (mobility speed vs recall, packet drop rate vs PDR degradation). — **Reversibility:** reversible.
- **D-04:** High-Resolution 300 DPI PNG Exports — Output all figures as clean 300 DPI raster PNGs directly into `results/plots/`, tracked in Git. — **Reversibility:** reversible.

### 2. Project Report Architecture & Chapter Structure (Committed to `docs/FINAL_PROJECT_REPORT.md`)
- **D-05:** Monolithic Comprehensive Report Structure — Consolidate all 6 academic chapters prescribed by the execution guide (§11) into `docs/FINAL_PROJECT_REPORT.md` with unified Table of Contents, executive summary, and appendices. — **Reversibility:** costly — defines the primary academic deliverable format.
- **D-06:** Dual Academic Rigor + Engineering Depth — Formally define mathematical and protocol models (RFC 3561 AODV equations, SimPy discrete-event timing models, ML pipeline formulation, evaluation metrics equations like PDR, FPR, F1, 2-strike confirmation equations) paired with implementation architecture and code design patterns. — **Reversibility:** reversible.
- **D-07:** Strict Provenance & Verifiable Experiment Footnotes — Every table in the report explicitly references the exact scenario JSON config, seed list (`[42, 43, 44]`), and source CSV artifact (`closed_loop_metrics.csv`, `generalization_metrics.csv`, `metrics.csv`) to satisfy the non-negotiable evaluation integrity gate. — **Reversibility:** costly — ensures academic auditability.
- **D-08:** Fully Embedded Figure Analysis — Inline Markdown figure links (`../results/plots/*.png`) with formal figure numbers, captions, and analytical paragraphs detailing the QoS recovery trends and ML tradeoff curves. — **Reversibility:** reversible.

### 3. Viva Defense Guide & Live Demo Walkthrough (Personal / Uncommitted in `.archify/`)
- **D-09:** Uncommitted Personal Artifacts in `.archify/` — Store all personal defense materials, live demonstration scripts, and cheat sheets inside `.archify/`, which is strictly gitignored. — **Reversibility:** reversible.
- **D-10:** Dual Comprehensive Academic Defense Bank + One-Page Cheat Sheet — Comprehensive question bank covering MANET routing theory, ML selection vs deep learning, why NS-3 was dropped, leakage avoidance proofs, and 2-strike quarantine rationale, paired with a rapid-fire one-page cheat sheet for the viva table. — **Reversibility:** reversible.
- **D-11:** Interactive 3-Act Demonstration Script — Step-by-step presentation script (`.archify/DEMO_WALKTHROUGH.md`) with copy-pasteable PowerShell commands demonstrating Act 1 (Baseline AODV), Act 2 (Attack injection drop), and Act 3 (Closed-loop IDS quarantine & PDR recovery). — **Reversibility:** reversible.
- **D-12:** Presentation Slide Deck Outline — 12-15 slide presentation deck structure with slide titles, bullet points, speaker notes, and diagram placement guides for PowerPoint. — **Reversibility:** reversible.
- **D-13:** Archify Architecture & Sequence Visuals — Utilize the `archify` skill (`C:\Users\KIIT0001\.agents\skills\archify\bin\archify.mjs`) to render interactive HTML diagrams (`architecture` and `sequence`) into `.archify/` documenting the complete SimPy-AODV-ML closed-loop feedback system. — **Reversibility:** reversible.

### 4. Plotting Suite CLI & Automation Seam (Personal / Uncommitted in `.archify/`)
- **D-14:** Uncommitted Personal Script `.archify/scripts/generate_all_plots.py` — Resides inside `.archify/` for personal use without cluttering the public repository. — **Reversibility:** reversible.
- **D-15:** Zero-Argument Automatic Execution with CLI Overrides — One command `python .archify/scripts/generate_all_plots.py` regenerates every figure in `results/plots/` automatically, supporting optional CLI arguments for specific targets. — **Reversibility:** reversible.
- **D-16:** Pure CSV Ingestion with Missing File Verification — Ingests existing authoritative CSVs from `results/` without re-running long simulations. — **Reversibility:** reversible.
- **D-17:** Local Visual Gallery Index `.archify/PLOTS_CATALOG.md` — Automatically creates a local visual catalog of all generated figures with thumbnails, file paths, and descriptions. — **Reversibility:** reversible.

### Agent's Discretion
- Aspect ratios and figure dimensions for standalone vs. multi-panel grid plots.
- Color palette nuances within Seaborn (`deep`, `colorblind`, or `muted`).
- Layout organization within `.archify/` (e.g., `.archify/scripts/`, `.archify/defense/`).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & Engineering Rules
- `AGENTS.md` — Non-negotiable engineering contract: Python-only, discrete-event determinism, comparison against plain AODV without IDS reporting PDR, throughput, delay, and routing overhead.
- `MANET_IDS_BTech_Execution_Guide.md` §10, §11 — Final deliverables and formal 6-chapter report structure (Introduction, Literature Review, System Design, Implementation, Results and Analysis, Conclusion and Future Work).
- `.planning/REQUIREMENTS.md` — `RESP-03` (automated visualization generator plotting confusion matrices and comparative QoS recovery charts).

### Source Data Artifacts
- `results/closed_loop_metrics.csv` — 36-run comparative triad QoS metrics (Baseline vs Attack vs AODV+IDS) across Blackhole & Grayhole at 30n and 50n.
- `results/closed_loop_report.md` — Detailed quantitative summary of QoS recovery and routing penalties.
- `results/metrics.csv` — Phase 3 classifier comparison metrics (RF, DT, SVM) on held-out test data.
- `results/feature_importance.csv` — Random Forest feature importance rankings.
- `results/generalization_metrics.csv` — 18-combination generalization matrix across speeds, drop rates, and topologies.
- `results/isolation_events.csv` — Log of discrete node isolation events during closed-loop execution.

### Skills & Tools
- `C:\Users\KIIT0001\.agents\skills\archify\bin\archify.mjs` — Archify executable for generating interactive HTML system architecture and sequence diagrams.
- `matplotlib 3.10.8` & `seaborn 0.13.2` — Verified plotting libraries installed in the Python 3.11 environment.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `results/plots/` directory already exists and contains initial confusion matrices and generalization curves.
- `results/*.csv` files provide clean, verified, and complete datasets containing all required empirical figures.
- `simulator/metrics.py` contains the authoritative calculation definitions for all network QoS metrics.
- `MANET_IDS_BTech_Execution_Guide.md` provides complete chapter descriptions and viva questions.

### Established Patterns
- Clean separation between public repository code/docs (committed) and personal tooling/diagrams (`.archify/`, gitignored).
- Provenance enforcement: All quantitative figures and tables must trace directly to saved scenario seeds and CSV records.
- 300 DPI publication formatting with consistent visual aesthetic.

### Integration Points
- `.archify/scripts/generate_all_plots.py` reads `results/*.csv` and writes figures directly into `results/plots/*.png`.
- `docs/FINAL_PROJECT_REPORT.md` references images from `../results/plots/*.png`.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly requested:
  - Options 1 & 2 (Plot Portfolio & Project Report) must be committed to the repository as standard docs and artifacts (`results/plots/`, `docs/FINAL_PROJECT_REPORT.md`).
  - Options 3 & 4 (Viva Defense Guide, Live Demo Script, Plotting CLI) must NOT be committed and must reside in `.archify/` which is entirely gitignored.
  - The `archify` skill should be used to generate rich interactive HTML architecture diagrams into `.archify/`.

</specifics>

<deferred>
## Deferred Ideas

- Optional web dashboard (FastAPI/Flask/Dash) deferred to future work per project scope rules.
- Live real-time packet animation viewer.

</deferred>

---

*Phase: 06-Visualization, Documentation & Project Deliverables*  
*Context gathered: 2026-10-28*
