"""Automated multi-seed Gate 2 verification benchmark verifying >= 25% relative PDR degradation."""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Ensure repo root is on sys.path for standalone invocation
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from simulator.run_scenario import SimulationRunner, load_scenario


def run_benchmark(
    base_scenario_path: Path = Path("scenarios/e1_normal_30n.json"),
    atk_scenario_path: Path = Path("scenarios/e2_blackhole_30n.json"),
    seeds: List[int] = [42, 43, 44],
    duration: float = 300.0,
    min_relative_drop: float = 0.25,
) -> Tuple[bool, List[Dict[str, float]]]:
    """Execute paired baseline vs attack simulations across multiple seeds and verify Gate 2 degradation."""
    base_scenario = load_scenario(base_scenario_path)
    atk_scenario = load_scenario(atk_scenario_path)

    results = []
    all_passed = True

    print("\n" + "=" * 95)
    print("GATE 2 VERIFICATION BENCHMARK: Blackhole Attack Impact Assessment")
    print("=" * 95)
    print(f"{'Seed':<6} | {'Base PDR':<10} | {'Atk PDR':<10} | {'Rel Drop':<10} | {'Base Tput (bps)':<16} | {'Atk Tput (bps)':<16} | {'Status':<8}")
    print("-" * 95)

    for seed in seeds:
        runner_base = SimulationRunner(scenario_config=base_scenario, seed=seed)
        m_base = runner_base.run(duration=duration)

        runner_atk = SimulationRunner(scenario_config=atk_scenario, seed=seed)
        m_atk = runner_atk.run(duration=duration)

        pdr_base = m_base["pdr"]
        pdr_atk = m_atk["pdr"]
        rel_drop = (pdr_base - pdr_atk) / pdr_base if pdr_base > 0 else 0.0

        passed = rel_drop >= min_relative_drop
        if not passed:
            all_passed = False

        status_str = "PASSED" if passed else "FAILED"
        print(f"{seed:<6} | {pdr_base*100:>8.2f}% | {pdr_atk*100:>8.2f}% | {rel_drop*100:>8.2f}% | {m_base['throughput_bps']:>16.1f} | {m_atk['throughput_bps']:>16.1f} | {status_str:<8}")

        results.append({
            "seed": seed,
            "pdr_base": pdr_base,
            "pdr_atk": pdr_atk,
            "rel_drop": rel_drop,
            "tput_base": m_base["throughput_bps"],
            "tput_atk": m_atk["throughput_bps"],
            "passed": passed,
        })

    print("-" * 95)
    if all_passed:
        print("=== GATE 2 PASSED: Blackhole attack causes significant measurable QoS degradation across all seeds ===\n")
    else:
        print("=== GATE 2 FAILED: Attack failed to achieve >= 25% relative PDR degradation on one or more seeds ===\n")

    return all_passed, results


if __name__ == "__main__":
    success, _ = run_benchmark()
    sys.exit(0 if success else 1)
