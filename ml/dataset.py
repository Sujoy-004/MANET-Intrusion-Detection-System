"""Dataset building, validation, and deterministic seed-holdout partitioning.

Produces auditable master, train, and test datasets with strict anti-leakage
seed separation and a tamper-evident SHA-256 manifest.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

# Bootstrap repository root into sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from feature_extraction.extract_features import (
    SCHEMA_COLUMNS,
    extract_features_from_trace,
)
from simulator.run_scenario import SimulationRunner, load_scenario

TRAIN_SEEDS: Tuple[int, ...] = (42, 43)
TEST_SEEDS: Tuple[int, ...] = (44,)


def sha256_file(path: Union[str, Path]) -> str:
    """Compute hex SHA-256 digest of file bytes on disk."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_feature_frame(frame: pd.DataFrame) -> None:
    """Validate that feature frame contains no NaNs/Infs, valid labels, and is non-degenerate.

    Raises ValueError if:
    - Any numeric column has NaN, +inf, or -inf
    - Any label is outside {'Normal', 'Blackhole'}
    - Any class has zero rows (degenerate dataset)
    """
    if frame.empty:
        raise ValueError("Feature frame is empty.")

    numeric_cols = [col for col in SCHEMA_COLUMNS if col != "label"]
    for col in numeric_cols:
        if col not in frame.columns:
            raise ValueError(f"Required numeric column '{col}' missing from frame.")
        vals = frame[col].to_numpy(dtype=float)
        if not np.all(np.isfinite(vals)):
            raise ValueError(f"Column '{col}' contains NaN or infinite values.")

    if "label" not in frame.columns:
        raise ValueError("Required 'label' column missing from frame.")

    unique_labels = set(frame["label"].unique())
    valid_labels = {"Normal", "Blackhole", "Grayhole"}
    if not unique_labels.issubset(valid_labels):
        raise ValueError(f"Frame contains invalid labels: {unique_labels - valid_labels}")

    if "Normal" not in unique_labels:
        raise ValueError(f"Degenerate frame: missing 'Normal' baseline class, found {unique_labels}")


def build_composite_run(
    seed: int,
    scenario_path: Union[str, Path],
    trace_dir: Union[str, Path],
    window_size: float = 5.0,
    step_size: float = 1.0,
    warmup: float = 10.0,
    duration: float = 300.0,
) -> pd.DataFrame:
    """Run a single seeded simulation with dynamic attack onset and extract tabular features."""
    cfg = load_scenario(scenario_path)
    scenario_id = cfg.get("scenario_id", "sim")
    trace_dir_path = Path(trace_dir)
    trace_dir_path.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir_path / f"{scenario_id}_seed{seed}.csv"

    runner = SimulationRunner(cfg, seed=seed, out_path=trace_path)
    runner.run(duration=duration)

    trace_df = pd.read_csv(trace_path)
    attack_cfg = cfg.get("attack", {})
    attack_start_time = attack_cfg.get("start_time")
    if attack_start_time is not None:
        attack_start_time = float(attack_start_time)

    feat_df = extract_features_from_trace(
        trace_df=trace_df,
        scenario_config=cfg,
        window_size=window_size,
        step_size=step_size,
        warmup=warmup,
        attacker_ids=runner.attacker_ids,
        attack_start_time=attack_start_time,
    )

    feat_df["seed"] = int(seed)
    return feat_df


def build_master(
    seeds: Tuple[int, ...] = (42, 43, 44),
    scenario_path: Union[str, Path, Sequence[Union[str, Path]]] = "scenarios/e3_blackhole_onset_30n.json",
    trace_dir: Union[str, Path] = "traces",
    window_size: float = 5.0,
    step_size: float = 1.0,
    warmup: float = 10.0,
    duration: float = 300.0,
) -> pd.DataFrame:
    """Build master dataset concatenated in deterministic sorted-seed order."""
    if isinstance(scenario_path, (str, Path)):
        scenario_list = [scenario_path]
    else:
        scenario_list = list(scenario_path)

    frames: List[pd.DataFrame] = []
    for scn in scenario_list:
        for s in sorted(seeds):
            frame = build_composite_run(
                seed=s,
                scenario_path=scn,
                trace_dir=trace_dir,
                window_size=window_size,
                step_size=step_size,
                warmup=warmup,
                duration=duration,
            )
            validate_feature_frame(frame)
            frames.append(frame)

    master_df = pd.concat(frames, ignore_index=True)
    # Ensure canonical column order: SCHEMA_COLUMNS + ["seed"]
    master_cols = SCHEMA_COLUMNS + ["seed"]
    master_df = master_df[master_cols]
    return master_df


def partition_by_seed(master: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Partition master dataset strictly by seed into train and test splits."""
    if "seed" not in master.columns:
        raise ValueError("Master DataFrame must contain a 'seed' column for partitioning.")

    master_seeds = set(master["seed"].unique())
    train_seeds_set = set(TRAIN_SEEDS)
    test_seeds_set = set(TEST_SEEDS)

    if not train_seeds_set.isdisjoint(test_seeds_set):
        raise ValueError(f"TRAIN_SEEDS and TEST_SEEDS overlap: {train_seeds_set & test_seeds_set}")

    expected_seeds = train_seeds_set | test_seeds_set
    if master_seeds != expected_seeds:
        raise ValueError(
            f"Master seeds {master_seeds} do not match union of train/test seeds {expected_seeds}"
        )

    train_mask = master["seed"].isin(TRAIN_SEEDS)
    test_mask = master["seed"].isin(TEST_SEEDS)

    train_df = master[train_mask][SCHEMA_COLUMNS].copy().reset_index(drop=True)
    test_df = master[test_mask][SCHEMA_COLUMNS].copy().reset_index(drop=True)

    if len(train_df) + len(test_df) != len(master):
        raise ValueError(
            f"Row count mismatch: len(train)={len(train_df)} + len(test)={len(test_df)} != len(master)={len(master)}"
        )

    return train_df, test_df


def write_dataset_files(
    master: pd.DataFrame,
    train: pd.DataFrame,
    test: pd.DataFrame,
    out_dir: Union[str, Path] = Path("data"),
    scenario_path: Union[str, Path] = "scenarios/e3_blackhole_onset_30n.json",
    build_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Write master.csv, train.csv, test.csv and dataset_manifest.json to disk."""
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    master_path = out_dir_path / "master.csv"
    train_path = out_dir_path / "train.csv"
    test_path = out_dir_path / "test.csv"
    manifest_path = out_dir_path / "dataset_manifest.json"

    master.to_csv(master_path, index=False)
    train.to_csv(train_path, index=False)
    test.to_csv(test_path, index=False)

    master_sha = sha256_file(master_path)
    train_sha = sha256_file(train_path)
    test_sha = sha256_file(test_path)

    if isinstance(scenario_path, (str, Path)) and Path(scenario_path).is_file():
        cfg = load_scenario(scenario_path)
        scenario_id = cfg.get("scenario_id", str(scenario_path))
    else:
        cfg = {}
        scenario_id = "multi_attack" if not isinstance(scenario_path, (str, Path)) or str(scenario_path) == "multi_attack" else str(scenario_path)

    params = build_params or {}
    params_record = {
        "duration": params.get("duration", 300.0),
        "scenario_id": scenario_id,
        "scenario_path": str(scenario_path),
        "step_size": params.get("step_size", 1.0),
        "warmup": params.get("warmup", 10.0),
        "window_size": params.get("window_size", 5.0),
    }

    train_dist = {str(k): int(v) for k, v in train["label"].value_counts().items()}
    test_dist = {str(k): int(v) for k, v in test["label"].value_counts().items()}

    manifest = {
        "build_params": params_record,
        "files": {
            "master.csv": {"rows": len(master), "sha256": master_sha},
            "test.csv": {"rows": len(test), "sha256": test_sha},
            "train.csv": {"rows": len(train), "sha256": train_sha},
        },
        "master_columns": list(master.columns),
        "schema_columns": SCHEMA_COLUMNS,
        "splits": {
            "test": {
                "class_distribution": test_dist,
                "rows": len(test),
                "seeds": list(TEST_SEEDS),
            },
            "train": {
                "class_distribution": train_dist,
                "rows": len(train),
                "seeds": list(TRAIN_SEEDS),
            },
        },
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    return manifest
