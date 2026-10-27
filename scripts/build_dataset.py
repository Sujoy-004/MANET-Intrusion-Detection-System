"""CLI orchestrator for building reproducible seed-partitioned datasets with SHA-256 manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import List, Optional

# Bootstrap repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ml.dataset import (
    TRAIN_SEEDS,
    TEST_SEEDS,
    build_master,
    partition_by_seed,
    write_dataset_files,
)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments for dataset builder."""
    parser = argparse.ArgumentParser(
        description="Build deterministic, seed-partitioned intrusion detection dataset with manifest."
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default="42,43,44",
        help="Comma-separated integer seeds (default: 42,43,44)",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="scenarios/e3_blackhole_onset_30n.json",
        help="Path to scenario JSON config (default: scenarios/e3_blackhole_onset_30n.json)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="data",
        help="Output directory for generated datasets and manifest (default: data)",
    )
    parser.add_argument(
        "--trace-dir",
        type=str,
        default="traces",
        help="Directory for intermediary simulation traces (default: traces)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=300.0,
        help="Simulation duration in seconds (default: 300.0)",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=5.0,
        help="Sliding window size in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--step",
        type=float,
        default=1.0,
        help="Sliding window step size in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--warmup",
        type=float,
        default=10.0,
        help="Warmup interval in seconds (default: 10.0)",
    )
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Run simulation runs, assemble master, partition splits, and write manifest."""
    parsed = parse_args(args)
    seed_list = tuple(int(s.strip()) for s in parsed.seeds.split(",") if s.strip())

    print("=" * 80)
    print("MANET INTRUSION DETECTION SYSTEM - DATASET BUILDER (D-01 / D-02 / DATA-04)")
    print("=" * 80)
    print(f"Scenario:    {parsed.scenario}")
    print(f"Seeds:       {seed_list}")
    print(f"Duration:    {parsed.duration}s (warmup: {parsed.warmup}s, window: {parsed.window}s, step: {parsed.step}s)")
    print(f"Output dir:  {parsed.out_dir}")
    print(f"Trace dir:   {parsed.trace_dir}")
    print("-" * 80)

    build_params = {
        "duration": parsed.duration,
        "step_size": parsed.step,
        "warmup": parsed.warmup,
        "window_size": parsed.window,
    }

    try:
        print("[*] Generating simulation runs and extracting features per seed...")
        master_df = build_master(
            seeds=seed_list,
            scenario_path=parsed.scenario,
            trace_dir=parsed.trace_dir,
            window_size=parsed.window,
            step_size=parsed.step,
            warmup=parsed.warmup,
            duration=parsed.duration,
        )
        print(f"[+] Master dataset assembled: {len(master_df)} rows, {len(master_df.columns)} columns.")

        print("[*] Partitioning splits strictly by seed (Holdout D-01)...")
        train_df, test_df = partition_by_seed(master_df)
        print(f"    - Train split (seeds {TRAIN_SEEDS}): {len(train_df)} rows")
        print(f"    - Test split  (seeds {TEST_SEEDS}):  {len(test_df)} rows")

        print("[*] Writing CSV files and computing SHA-256 manifest...")
        manifest = write_dataset_files(
            master=master_df,
            train=train_df,
            test=test_df,
            out_dir=parsed.out_dir,
            scenario_path=parsed.scenario,
            build_params=build_params,
        )

        print("-" * 80)
        print("DATASET BUILD COMPLETE")
        print(f"Train samples: {len(train_df)} | Dist: {manifest['splits']['train']['class_distribution']}")
        print(f"Test samples:  {len(test_df)}  | Dist: {manifest['splits']['test']['class_distribution']}")
        print("Manifest files & hashes:")
        for fname, info in manifest["files"].items():
            print(f"  - {fname:12s} ({info['rows']} rows) SHA256: {info['sha256']}")
        print("=" * 80)
        return 0

    except Exception as e:
        print(f"\n[ERROR] Dataset build failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
