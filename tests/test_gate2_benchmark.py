"""Integration test asserting quantitative Gate 2 attack impact threshold."""

from pathlib import Path
from scripts.verify_gate2_impact import run_benchmark


def test_gate2_quantitative_impact():
    """Verify Gate 2 threshold (>= 25% relative PDR degradation) on seed 42."""
    base_scenario = Path("scenarios/e1_normal_30n.json")
    atk_scenario = Path("scenarios/e2_blackhole_30n.json")

    passed, results = run_benchmark(
        base_scenario_path=base_scenario,
        atk_scenario_path=atk_scenario,
        seeds=[42],
        duration=100.0,
        min_relative_drop=0.25,
    )

    assert passed, f"Gate 2 benchmark failed: {results}"
    assert len(results) == 1
    assert results[0]["rel_drop"] >= 0.25
    assert results[0]["passed"] is True
