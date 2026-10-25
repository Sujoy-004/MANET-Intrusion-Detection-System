# Stack Research

**Domain:** MANET Simulation, Feature Engineering & Machine Learning Intrusion Detection  
**Researched:** 2026-10-23  
**Confidence:** HIGH  

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11.8 | Core implementation language | Pre-installed, Windows native, robust standard library (`dataclasses`, `math`, `csv`, `json`), zero compilation overhead. |
| SimPy | 4.1.2 | Discrete-event clock & simulation engine | Process-based event scheduler (`Environment`, `env.process`, `env.timeout`). Tested ~70k events/sec on target machine without external dependencies. |
| NetworkX | 3.6.1 | Ad-hoc network topology & neighbor graph | Efficient dynamic graph operations, transmission range distance queries, and topology tracking. Pure Python. |
| Scikit-learn | 1.8.0 | Classical ML classifiers & evaluation | Industry standard for Random Forest, SVM, Decision Trees, standard scalers, and metric suites (`classification_report`, `confusion_matrix`). |
| NumPy | 1.26.4 | Numerical vector computation | High-performance array operations for feature calculation and distance matrix manipulation. |
| Pandas | 3.0.2 | Trace ingestion, window aggregation & tabular datasets | High-throughput structured feature extraction and scenario aggregation. (Uses Copy-on-Write, `map` instead of deprecated `applymap`). |
| Matplotlib | 3.10.8 | Academic publication plots & ROC/PR curves | Standard charting library for confusion matrices, QoS recovery curves, and model comparison bar charts. |
| Seaborn | 0.13.2 | Statistical heatmap & metric visualization | Clean visual styling for confusion matrices and feature correlation heatmaps. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SciPy | 1.17.1 | Statistical hypothesis testing | When evaluating significance of QoS performance recovery (AODV vs AODV+IDS). |
| JupyterLab | 4.5.6 | Interactive exploratory analysis | For data validation, EDA, and notebook-based project presentation. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| PowerShell 7+ / Windows PowerShell | Native terminal execution | Target OS shell; scripts must avoid POSIX path separators and Unix idioms. |
| Git | Version control | Local repository tracking; large trace directories and raw CSVs gitignored. |

## Installation

```powershell
# Dependencies are verified pre-installed on this machine:
python -m pip install simpy networkx numpy pandas scikit-learn matplotlib seaborn scipy
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Pure-Python SimPy | NS-3 (C++ on Linux) | Only when simulating physical PHY/MAC layer bit-level radio physics (out of scope for B.Tech ML focus, and fails on Windows). |
| Pure-Python SimPy | ns.py | ns.py only models wired IP flows (TCP/BBR, FatTree), lacks wireless, radio propagation, and AODV mobility layers. |
| Scikit-learn Classifiers | PyTorch / TensorFlow | Only for complex deep representation learning on raw packet streams; overkill and prone to overfitting on tabular MANET flow features. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| NS-3 / ns-3-dev / C++ toolchain | Requires Linux VM/WSL, complex build tools (CMake, Ninja), fails on native Windows, distracts from ML core. | In-repo pure-Python SimPy simulator. |
| Deep Learning (PyTorch/TensorFlow) | Violates B.Tech scope boundaries; high risk of training failures, low interpretability, slow inference in closed-loop. | Random Forest, Decision Tree, Support Vector Machine. |
| Random train/test split (`train_test_split(shuffle=True)`) | Leaks temporal packet correlations between identical simulation runs, producing artificially inflated metrics. | Scenario- and seed-based dataset partitioning. |
| Direct ground-truth trace columns (`is_attacker`, attack flags) | Causes catastrophic feature leakage; classifier learns ground-truth flag instead of anomalous behavior. | Features derived solely from observed packet headers and windowed transmission statistics. |

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Pandas 3.0.2 | NumPy 1.26.4 | String columns default to `str` dtype; Copy-on-Write enabled by default. |
| Scikit-learn 1.8.0 | SciPy 1.17.1 | Metric functions support modern array-like parameter types. |

## Sources

- `MANET_IDS_BTech_Execution_Guide.md` — Project specification and architecture definition.
- `AGENTS.md` — Binding engineering rules and verified environment audit.
- Python environment verification via PowerShell runtime queries.

---
*Stack research for: MANET Intrusion Detection System*  
*Researched: 2026-10-23*  
