"""Unit and integration tests for zero-shot transfer, multi-attack dataset, and generalization matrix."""

import json
from pathlib import Path
import pandas as pd
import pytest

from feature_extraction.extract_features import SCHEMA_COLUMNS
from ml.dataset import sha256_file
from ml.generalization import run_zero_shot_evaluation
from scripts.run_generalization_matrix import run_single_benchmark_case


def test_zero_shot_transfer_evaluation():
    """Verify zero-shot evaluation benchmarks model on test data and respects FPR <= 1.0% gate."""
    model_path = Path("ml/models/best_model.joblib")
    test_csv = Path("data/test.csv")

    assert model_path.exists(), "Trained best_model.joblib missing"
    assert test_csv.exists(), "Held-out data/test.csv missing"

    res = run_zero_shot_evaluation(model_path=model_path, test_data=test_csv)

    assert isinstance(res, dict)
    assert res["total_samples"] == 17400
    assert res["grayhole_samples"] == 200
    assert 0.0 <= res["grayhole_recall"] <= 1.0
    assert 0.0 <= res["precision"] <= 1.0
    assert 0.0 <= res["recall"] <= 1.0
    assert 0.0 <= res["f1"] <= 1.0
    assert res["fpr"] <= 0.01, f"Zero-shot transfer FPR {res['fpr']} exceeded 1.0% gate"


def test_multi_attack_dataset_integrity():
    """Verify train and test CSVs contain all 3 classes, 10 columns, and match manifest digests."""
    manifest_path = Path("data/dataset_manifest.json")
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    for fname in ["train.csv", "test.csv"]:
        fpath = Path("data") / fname
        assert fpath.exists()
        assert sha256_file(fpath) == manifest["files"][fname]["sha256"]

        df = pd.read_csv(fpath)
        assert list(df.columns) == SCHEMA_COLUMNS
        classes = set(df["label"].unique())
        assert classes == {"Normal", "Blackhole", "Grayhole"}
        assert not df.isna().any().any()


def test_champion_metadata_and_fpr_gate():
    """Verify model_metadata.json documents champion selection and strict FPR <= 1.0% satisfaction."""
    meta_path = Path("ml/models/model_metadata.json")
    assert meta_path.exists()

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["selection"]["fpr_gate_satisfied"] is True
    assert meta["selection"]["fpr_gate"] == 0.01
    assert meta["champion"] in ["random_forest", "decision_tree", "svm"]

    # Champion record has fpr <= 0.01
    champ_records = [c for c in meta["all_candidates"] if c["model"] == meta["champion"]]
    assert len(champ_records) == 1
    assert champ_records[0]["fpr"] <= 0.01


def test_generalization_benchmark_case():
    """Verify single benchmark case executes cleanly and produces valid QoS and ML metrics."""
    res = run_single_benchmark_case(
        base_scenario_path="scenarios/e4_grayhole_onset_30n.json",
        speed=5.0,
        drop_prob=0.5,
        seed=44,
        duration=25.0,
        onset_time=10.0,
    )

    assert isinstance(res, dict)
    assert res["nodes"] == 30
    assert res["speed"] == 5.0
    assert res["drop_prob"] == 0.5
    assert 0.0 <= res["pdr"] <= 1.0
    assert 0.0 <= res["packet_loss_rate"] <= 1.0
    assert res["throughput_kbps"] >= 0.0
