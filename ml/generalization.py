"""Generalization and zero-shot transfer evaluation suite for MANET IDS."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from feature_extraction.extract_features import (
    SCHEMA_COLUMNS,
    extract_features_from_trace,
)
from simulator.run_scenario import SimulationRunner, load_scenario


def run_zero_shot_evaluation(
    model_path: Union[str, Path],
    test_data: Union[str, Path, pd.DataFrame],
    normal_label: str = "Normal",
    attack_labels: Tuple[str, ...] = ("Blackhole", "Grayhole"),
) -> Dict[str, Any]:
    """Benchmark a Blackhole-trained champion model directly on unseen Grayhole traffic without retraining.

    Evaluates zero-shot transfer recall, precision, F1, and false positive rate.
    Any non-Normal prediction from the binary model is mapped as an attack detection.
    """
    model = joblib.load(model_path)

    if isinstance(test_data, (str, Path)):
        df = pd.read_csv(test_data)
    else:
        df = test_data.copy()

    feature_cols = [c for c in SCHEMA_COLUMNS if c != "label"]
    X = df[feature_cols].to_numpy(dtype=float)
    y_true = df["label"].astype(str)

    # Predict with trained champion pipeline
    y_pred = model.predict(X)

    # Binary mapping: 0 = Normal, 1 = Attack (Blackhole or Grayhole)
    y_true_binary = np.array([0 if val == normal_label else 1 for val in y_true])
    y_pred_binary = np.array([0 if val == normal_label else 1 for val in y_pred])

    tn, fp, fn, tp = confusion_matrix(y_true_binary, y_pred_binary, labels=[0, 1]).ravel()

    accuracy = float((tp + tn) / (tp + tn + fp + fn)) if (tp + tn + fp + fn) > 0 else 0.0
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    # Separate metrics specifically on Grayhole rows
    grayhole_mask = (y_true == "Grayhole").to_numpy()
    grayhole_count = int(np.sum(grayhole_mask))
    if grayhole_count > 0:
        grayhole_detected = int(np.sum(y_pred_binary[grayhole_mask] == 1))
        grayhole_recall = float(grayhole_detected / grayhole_count)
    else:
        grayhole_detected = 0
        grayhole_recall = 0.0

    return {
        "model_path": str(model_path),
        "total_samples": int(len(df)),
        "normal_samples": int(np.sum(y_true == normal_label)),
        "attack_samples": int(np.sum(y_true != normal_label)),
        "grayhole_samples": grayhole_count,
        "grayhole_detected": grayhole_detected,
        "grayhole_recall": grayhole_recall,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }
