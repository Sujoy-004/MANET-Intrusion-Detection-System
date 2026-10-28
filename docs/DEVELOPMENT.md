<!-- generated-by: gsd-doc-writer -->
# Development Guide

This guide establishes the engineering conventions, architectural guidelines, development workflows, and extension mechanisms for contributors working on the Machine Learning-Based Intrusion Detection System for MANET.

## Engineering Contracts & Non-Negotiables

All development in this repository is strictly governed by the engineering contracts set in `AGENTS.md`. Key non-negotiables:

1. **Python Only (Windows Native):** No C/C++, no NS-3, no Cython, no external compilers. All simulator and ML code must run natively on CPython 3.11+.
2. **Explicit Seed Determinism:** Every stochastic component (Random Waypoint mobility, radio range, packet jitter, attack decisions) MUST be seeded using an explicit integer seed. A simulation run with identical seeds must produce byte-for-byte identical traces.
3. **Architectural Seam Decoupling:** `simulator/` MUST NEVER import from `attacks/`. Adversarial strategies are injected at runtime by `simulator/run_scenario.py`.
4. **Zero Random-Row Data Splitting:** Packet traces exhibit heavy temporal autocorrelation. Train/test sets MUST be partitioned strictly by scenario and seed (e.g., Seeds 42 & 43 for training, Seed 44 for testing). Never use `train_test_split(..., shuffle=True)` on raw packet or window rows.
5. **Anti-Leakage Feature Pipeline:** Never introduce features that encode ground-truth attacker identity, node coordinates, or scenario metadata into the feature matrix $X$.
6. **Low False Positive Rate Gate:** Any candidate classifier must satisfy $\text{FPR} \le 1.0\%$ before being eligible for deployment as a champion model in closed-loop routing.

## Development Commands

| Command | Purpose |
|---|---|
| `python -m pytest` | Run the complete 69-test automated test suite. |
| `python -m simulator.run_scenario --scenario <json> --seed <int> --out <dir>` | Run an individual simulation scenario. |
| `python -m simulator.run_scenario --scenario <json> --seed <int> --out <dir> --ids` | Run a scenario with real-time Online IDS mitigation. |
| `python scripts/build_dataset.py` | Generate seed-partitioned train (`data/train.csv`) and test (`data/test.csv`) datasets. |
| `python -m ml.train` | Train Random Forest, Decision Tree, and SVM pipelines with 5-fold Stratified CV. |
| `python -m ml.evaluate` | Evaluate trained models on the held-out test split and export metrics. |
| `python scripts/run_generalization_matrix.py` | Run the 18-combination cross-scenario generalization benchmark. |
| `python scripts/run_closed_loop_benchmark.py` | Run the authoritative 36-run 3-way comparative QoS benchmark triad. |
| `python -m ml.plots` | Generate all publication-grade 300 DPI figures in `results/plots/`. |

## Adding a New Attack Strategy

To implement a new attack behavior (e.g., RREQ Flooding or Selective Drop variant):

### Step 1: Subclass `AttackStrategy` in `attacks/`

Create a new file (e.g., `attacks/my_attack.py`):

```python
from typing import Optional
from attacks.base import AttackStrategy
from simulator.aodv import AodvNode, RreqPacket, Packet

class MyAttackStrategy(AttackStrategy):
    def __init__(self, node: AodvNode, drop_rate: float = 0.5):
        super().__init__(node)
        self.drop_rate = drop_rate

    def recv_rreq_hook(self, rreq: RreqPacket) -> Optional[bool]:
        """
        Intercept incoming RREQ.
        Return True to suppress default processing, False to drop, or None to allow default.
        """
        return None

    def forward_data_hook(self, packet: Packet) -> Optional[bool]:
        """
        Intercept data packet forwarding.
        Return True to allow forwarding, or False to silently drop.
        """
        if self.node.rng.random() < self.drop_rate:
            return False  # Drop packet
        return True       # Forward packet
```

### Step 2: Register the Strategy in `attacks/registry.py`

Add your strategy class to the factory dictionary in [attacks/registry.py](file:///C:/Users/KIIT0001/Documents/projects/Machine%20Learning-Based%20Intrusion%20Detection%20System%20for%20MANET/attacks/registry.py):

```python
from attacks.my_attack import MyAttackStrategy

STRATEGY_REGISTRY = {
    "blackhole": BlackholeStrategy,
    "grayhole": GrayholeStrategy,
    "my_attack": MyAttackStrategy,
}
```

### Step 3: Add Unit Tests

Create `tests/test_attacks_my_attack.py` asserting:
1. Strategy initialization and parameter parsing.
2. Routing behavior changes (e.g., drops vs forwards).
3. Non-interference with honest nodes.
4. Conformance to architectural import boundaries (asserted automatically by `tests/test_import_boundaries.py`).

## Code Style & Conventions

- **Python Version:** 3.11.8.
- **Style Guide:** Follow PEP 8 (4 spaces indent, snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants).
- **Paths:** Always use `pathlib.Path` for cross-platform Windows compatibility; never concatenate paths with raw slashes or backslashes.
- **Type Annotations:** Use typing hints (`typing.Optional`, `typing.List`, `typing.Dict`, `typing.Tuple`).
- **Dependencies:** Never add heavy framework dependencies (e.g., PyTorch, TensorFlow, Flask) to the core simulator or ML engine.

## Branching & Pull Request Workflow

1. **Default Branch:** `main`.
2. **Branch Naming:** Use feature branches (`feat/attack-rreq-flood`, `fix/quarantine-decay-timer`).
3. **Pre-Commit Checks:** Run `python -m pytest` locally and ensure all 69 tests pass before opening a PR.
4. **PR Guidelines:**
   - Clearly document scenario configurations and random seeds used for testing.
   - Attach side-by-side QoS comparison tables for any changes affecting routing protocols.
   - Maintain provenance: all benchmark numbers in PR descriptions must trace to an executable scenario and seed.
