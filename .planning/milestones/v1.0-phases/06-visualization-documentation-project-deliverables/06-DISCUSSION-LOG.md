# Phase 06: Visualization, Documentation & Project Deliverables - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.  
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-10-28  
**Phase:** 06-visualization-documentation-project-deliverables  
**Areas discussed:** Plot Portfolio & Visualization Styling, Project Report Architecture & Chapter Structure, Viva Defense Guide & Live Demo Walkthrough, Plotting Suite CLI & Automation Seam  

---

## 1. Plot Portfolio & Visualization Styling (Committed)

| Option | Description | Selected |
|--------|-------------|----------|
| Academic Seaborn whitegrid | Publication-ready, muted/colorblind-friendly contrast for reports & slides | ✓ |
| IEEE Transactions classic | Grayscale hatches with distinct line markers | |
| Minimalist modern style | Darker accents with custom borders | |

| Option | Description | Selected |
|--------|-------------|----------|
| Multi-panel 4-in-1 QoS grid | Complete QoS recovery triad side-by-side in one figure | |
| Individual standalone figures | Dedicated PNG files for PDR, Throughput, Delay, Overhead | |
| Both combined | Standalone metric plots plus a consolidated executive summary 4-panel dashboard | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Full ML evaluation suite | PR/ROC curves, multi-model bars, feature importance chart | ✓ |
| Core metrics only | Multi-model performance comparison bar chart and feature importance | ✓ |
| Comprehensive attack stress suite | Speed vs recall and drop rate vs PDR degradation curves | ✓ |

*(User selected all 3 ML evaluation and stress plot categories)*

| Option | Description | Selected |
|--------|-------------|----------|
| 300 DPI PNG only | Clean raster format, guaranteed compatibility with Git, Markdown, Word, LaTeX | ✓ |
| Dual 300 DPI PNG + Vector SVG/PDF | Vector zooming in LaTeX/Overleaf with PNG previews | |

**User's choice:** Academic Seaborn whitegrid style, 300 DPI PNG, both standalone metric plots and a consolidated 4-panel executive dashboard, plus the full set of ML evaluation and attack stress curves. Committed to `results/plots/`.

---

## 2. Project Report Architecture & Chapter Structure (Committed)

| Option | Description | Selected |
|--------|-------------|----------|
| Monolithic docs/FINAL_PROJECT_REPORT.md | Complete 6-chapter document with unified Table of Contents | ✓ |
| Modular docs/report/ structure | Separate chapter files stitched by a master index | |

| Option | Description | Selected |
|--------|-------------|----------|
| Formal academic B.Tech thesis standard | Full mathematical formulations, architecture diagrams, literature context | ✓ |
| Engineering handbook style | Practical focus on simulator implementation, design patterns, empirical findings | ✓ |

*(User selected both academic rigor and engineering depth)*

| Option | Description | Selected |
|--------|-------------|----------|
| Strict provenance tables | Every table explicitly cites scenario JSON, seed list, and source CSV artifact | ✓ |
| Standard academic tables | Clear consolidated tables without verbose data citations | |

| Option | Description | Selected |
|--------|-------------|----------|
| Fully embedded visual analysis | Every generated figure embedded with Figure numbers, captions, and analysis | ✓ |
| Appendix gallery | Summary plots in text, remaining figures placed in appendix | |

**User's choice:** Monolithic comprehensive `docs/FINAL_PROJECT_REPORT.md` combining academic mathematical rigor and engineering handbook depth, strict experiment provenance tables, and fully embedded figure analyses. Committed to repository.

---

## 3. Viva Defense Guide & Live Demo Walkthrough (Personal / Uncommitted in .archify/)

| Option | Description | Selected |
|--------|-------------|----------|
| Use archify skill & directory | Automatic .archify/ folder used for all uncommitted/personal materials | ✓ |
| docs/personal/ with .gitignore | Local subfolder under docs | |
| personal/ at repository root | Root directory | |

| Option | Description | Selected |
|--------|-------------|----------|
| Comprehensive Academic Defense Bank | Theory, AODV mechanics, ML selection vs DL, discrete-event choices, leakage proofs | ✓ |
| Rapid-fire Q&A Cheat Sheet | Concise answers to top 20 most predictable viva questions | ✓ |

*(User selected both combined: full defense bank + one-page cheat sheet)*

| Option | Description | Selected |
|--------|-------------|----------|
| Interactive 3-Act Demo Script | 1: Baseline AODV, 2: Attack drop, 3: Closed-loop IDS isolation & PDR recovery | ✓ |
| Automated one-command runner | Single execution command printing summary table | |

| Option | Description | Selected |
|--------|-------------|----------|
| Include 12-15 slide presentation outline | PPT structure with bullet points, speaker notes, and diagram placement | ✓ |
| Viva Q&A and demo script only | No presentation slides | |

**User's choice:** Store all personal materials in `.archify/` (uncommitted/gitignored). Produce a comprehensive viva question bank + one-page cheat sheet, an interactive 3-Act demonstration script, a 12-15 slide presentation outline, and interactive HTML architecture diagrams using the `archify` skill.

---

## 4. Plotting Suite CLI & Automation Seam (Personal / Uncommitted in .archify/)

| Option | Description | Selected |
|--------|-------------|----------|
| .archify/scripts/generate_all_plots.py | Whole .archify/ directory is uncommitted and gitignored | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| Simple zero-argument script | Single command python .archify/scripts/generate_all_plots.py regenerates all | ✓ |
| Granular CLI flags | Supports selective flags | |

| Option | Description | Selected |
|--------|-------------|----------|
| Pure CSV ingestion | Ingests existing authoritative CSVs from results/ with missing-file checks | ✓ |
| Hybrid ingestion + recompute | Automatically re-runs simulations if missing | |

| Option | Description | Selected |
|--------|-------------|----------|
| Local visual gallery index in .archify/ | PLOTS_CATALOG.md for instant local inspection before report writing | ✓ |
| Console terminal receipt only | Stdout output only | |

**User's choice:** Place generator script in `.archify/scripts/generate_all_plots.py` with zero-argument default execution, ingesting authoritative CSVs from `results/`, and building a local image catalog `.archify/PLOTS_CATALOG.md`. The entire `.archify/` directory is gitignored.

---

## Agent's Discretion
- Aspect ratios, figure heights, and specific color shades within Seaborn whitegrid.
- Layout organization of subfolders within `.archify/`.

## Deferred Ideas
- Live real-time packet animation viewer.
- Interactive web dashboard (FastAPI/Dash).
