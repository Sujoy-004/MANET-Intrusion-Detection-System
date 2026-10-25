"""Automated end-to-end dataset generation pipeline producing sample training data."""

import json
from pathlib import Path
import sys
from typing import List

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import pandas as pd

from feature_extraction.extract_features import (
    SCHEMA_COLUMNS,
    extract_features_from_trace,
)
from simulator.run_scenario import SimulationRunner, load_scenario


def generate_all_datasets(
    seeds: List[int] = [42, 43],
    duration: float = 300.0,
    out_dir: Path = Path("data"),
    trace_dir: Path = Path("traces"),
) -> Path:
    """Run normal and attack simulations, extract non-leaking features, and assemble dataset."""
    trace_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    normal_cfg = load_scenario("scenarios/e1_normal_30n.json")
    blackhole_cfg = load_scenario("scenarios/e2_blackhole_30n.json")

    all_dfs: List[pd.DataFrame] = []

    print("\n" + "=" * 80)
    print("DATASET GENERATION PIPELINE")
    print("=" * 80)

    for seed in seeds:
        # 1. Normal run
        trace_normal = trace_dir / f"e1_normal_seed{seed}.csv"
        print(f"\n[Seed {seed}] Simulating Normal Baseline -> {trace_normal.name} ...")
        runner_norm = SimulationRunner(normal_cfg, seed=seed, out_path=trace_normal)
        runner_norm.run(duration=duration)
        df_norm_trace = pd.read_csv(trace_normal)
        feats_norm = extract_features_from_trace(
            trace_df=df_norm_trace,
            scenario_config=normal_cfg,
            window_size=5.0,
            step_size=1.0,
            warmup=10.0,
        )
        print(f"  Extracted {len(feats_norm)} samples (Normal)")
        all_dfs.append(feats_norm)

        # 2. Blackhole run
        trace_bh = trace_dir / f"e2_blackhole_seed{seed}.csv"
        print(f"[Seed {seed}] Simulating Blackhole Attack -> {trace_bh.name} ...")
        runner_bh = SimulationRunner(blackhole_cfg, seed=seed, out_path=trace_bh)
        runner_bh.run(duration=duration)
        df_bh_trace = pd.read_csv(trace_bh)
        # Pass the identified dynamic attacker node to feature extractor
        feats_bh = extract_features_from_trace(
            trace_df=df_bh_trace,
            scenario_config=blackhole_cfg,
            window_size=5.0,
            step_size=1.0,
            warmup=10.0,
            attacker_ids=runner_bh.attacker_ids,
        )
        print(f"  Extracted {len(feats_bh)} samples (Attacker Node: {runner_bh.attacker_ids})")
        all_dfs.append(feats_bh)

    # Combine all feature frames
    combined_df = pd.concat(all_dfs, ignore_index=True)

    sample_out_path = out_dir / "dataset_sample.csv"
    combined_df.to_csv(sample_out_path, index=False)

    total_samples = len(combined_df)
    counts = combined_df["label"].value_counts().to_dict()
    normal_cnt = counts.get("Normal", 0)
    bh_cnt = counts.get("Blackhole", 0)
    bh_pct = (bh_cnt / total_samples * 100) if total_samples > 0 else 0.0

    print("\n" + "-" * 80)
    print("DATASET GENERATION SUMMARY")
    print("-" * 80)
    print(f"Total samples:     {total_samples}")
    print(f"Normal samples:    {normal_cnt} ({100 - bh_pct:.2f}%)")
    print(f"Blackhole samples: {bh_cnt} ({bh_pct:.2f}%)")
    print(f"Schema columns:    {list(combined_df.columns)}")
    print(f"Missing values:    {combined_df.isna().sum().sum()}")
    print(f"Saved dataset to:  {sample_out_path.resolve()}")
    print("=" * 80 + "\n")

    return sample_out_path


if __name__ == "__main__":
    generate_all_datasets()
