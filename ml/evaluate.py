"""Model evaluation, FPR-gated champion selection, and artifact export suite.

Evaluates trained classifiers on held-out test data (seed 44) with full security metrics:
Accuracy, Precision, Recall, F1 (Blackhole), FPR, and Confusion Matrix.
Enforces the locked FPR <= 0.01 gate (D-06), saves the champion pipeline, and exports
confusion heatmaps, feature importances, and evaluation reports.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    make_scorer,
    precision_score,
    recall_score,
)

# Headless matplotlib configuration before pyplot import
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# Bootstrap repository root into sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from feature_extraction.extract_features import SCHEMA_COLUMNS
from ml.train import load_training_data

FPR_GATE: float = 0.01


def load_candidates(
    models_dir: Union[str, Path] = Path("ml/models"),
    names: Tuple[str, ...] = ("random_forest", "decision_tree", "svm"),
) -> Dict[str, Any]:
    """Load serialized joblib candidate models from disk."""
    dir_path = Path(models_dir)
    candidates: Dict[str, Any] = {}
    for name in names:
        model_path = dir_path / f"{name}.joblib"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Candidate model file missing: {model_path}. Run ml/train.py first."
            )
        candidates[name] = joblib.load(model_path)
    return candidates


def evaluate_on_test(
    models: Dict[str, Any],
    test_csv_path: Union[str, Path] = Path("data/test.csv"),
) -> Tuple[List[Dict[str, Any]], pd.DataFrame, pd.Series]:
    """Evaluate candidate models on strictly held-out test dataset."""
    test_path = Path(test_csv_path)
    if not test_path.exists():
        raise FileNotFoundError(f"Held-out test dataset missing: {test_path}")

    df = pd.read_csv(test_path)
    feature_cols = [c for c in SCHEMA_COLUMNS if c != "label"]
    X = df[feature_cols].copy()
    y = df["label"].astype(str).copy()

    rows: List[Dict[str, Any]] = []
    # Evaluated in deterministic candidate order
    for name in ["random_forest", "decision_tree", "svm"]:
        if name not in models:
            continue
        pipeline = models[name]
        y_pred = pipeline.predict(X)

        # Explicit label ordering: Normal = 0, Blackhole = 1
        cm = confusion_matrix(y, y_pred, labels=["Normal", "Blackhole"])
        tn, fp, fn, tp = cm.ravel()

        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        acc = float(accuracy_score(y, y_pred))
        prec = float(precision_score(y, y_pred, pos_label="Blackhole", zero_division=0.0))
        rec = float(recall_score(y, y_pred, pos_label="Blackhole", zero_division=0.0))
        f1 = float(f1_score(y, y_pred, pos_label="Blackhole", zero_division=0.0))

        rows.append({
            "model": name,
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_blackhole": f1,
            "fpr": fpr,
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        })

    return rows, X, y


def select_champion(
    rows: List[Dict[str, Any]],
    candidates: Dict[str, Any],
    X_test: pd.DataFrame,
    models_dir: Union[str, Path] = Path("ml/models"),
) -> Tuple[Dict[str, Any], Any, Dict[str, Any]]:
    """Select champion model satisfying FPR <= 0.01 gate with latency and size tie-breakers."""
    dir_path = Path(models_dir)
    # Raw float compare — no rounding before gate check
    eligible = [r for r in rows if r["fpr"] <= FPR_GATE]

    if not eligible:
        raise RuntimeError(
            f"FPR gate failure: no candidate model achieved FPR <= {FPR_GATE}. "
            "Escalation chain: (1) widen RF/DT grids once, (2) widen SVM grid once, "
            "(3) if still none pass, STOP and request human verification. Gate must not be relaxed."
        )

    # Compute tie-breakers for eligible candidates
    eligible_with_meta = []
    for r in eligible:
        name = r["model"]
        pipe = candidates[name]
        # Latency pass
        t0 = time.perf_counter()
        pipe.predict(X_test)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        model_path = dir_path / f"{name}.joblib"
        file_size = model_path.stat().st_size if model_path.exists() else 0

        eligible_with_meta.append((r, pipe, {"latency_ms": latency_ms, "file_size_bytes": file_size}))

    # Tie-break key: max f1_blackhole, min latency, min file size
    champion_row, champion_pipe, tie_breakers = max(
        eligible_with_meta,
        key=lambda item: (item[0]["f1_blackhole"], -item[2]["latency_ms"], -item[2]["file_size_bytes"]),
    )

    return champion_row, champion_pipe, tie_breakers


def refit_with_probability(
    champion_name: str,
    champion_pipeline: Any,
    train_csv_path: Union[str, Path] = Path("data/train.csv"),
    test_csv_path: Union[str, Path] = Path("data/test.csv"),
) -> Any:
    """Ensure champion exposes predict_proba interface with verified prediction parity."""
    # RF and DT natively support predict_proba
    if champion_name != "svm":
        return champion_pipeline

    clf = champion_pipeline.named_steps["clf"]
    if getattr(clf, "probability", False):
        return champion_pipeline

    print("[*] Champion is SVM: refitting with probability=True on training data...")
    X_train, y_train = load_training_data(train_csv_path)

    # Clone pipeline and set probability=True
    from sklearn.base import clone
    refit_pipe = clone(champion_pipeline)
    refit_pipe.named_steps["clf"].probability = True
    refit_pipe.fit(X_train, y_train)

    # Verify prediction parity on held-out test data
    test_df = pd.read_csv(test_csv_path)
    feature_cols = [c for c in SCHEMA_COLUMNS if c != "label"]
    X_test = test_df[feature_cols]

    orig_preds = champion_pipeline.predict(X_test)
    refit_preds = refit_pipe.predict(X_test)
    if not np.array_equal(orig_preds, refit_preds):
        raise RuntimeError("Parity check failed: SVM hard predictions changed after probability refit!")

    return refit_pipe


def export_metrics_csv(
    rows: List[Dict[str, Any]],
    path: Union[str, Path] = Path("results/metrics.csv"),
) -> None:
    """Export benchmark metrics to CSV."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(p, index=False)


def plot_confusion_matrices(
    models: Dict[str, Any],
    X_test: pd.DataFrame,
    y_test: pd.Series,
    out_dir: Union[str, Path] = Path("results/plots"),
) -> None:
    """Plot and save confusion matrix heatmaps for all candidate models."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for name, pipeline in models.items():
        y_pred = pipeline.predict(X_test)
        cm = confusion_matrix(y_test, y_pred, labels=["Normal", "Blackhole"])

        fig, ax = plt.subplots(figsize=(5, 4))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=["Normal", "Blackhole"],
            yticklabels=["Normal", "Blackhole"],
            ax=ax,
        )
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")
        ax.set_title(f"Confusion Matrix: {name}")

        fig_file = out_path / f"confusion_matrix_{name}.png"
        fig.savefig(fig_file, dpi=150, bbox_inches="tight")
        plt.close(fig)


def export_feature_importance(
    models: Dict[str, Any],
    X_test: pd.DataFrame,
    y_test: pd.Series,
    path: Union[str, Path] = Path("results/feature_importance.csv"),
) -> pd.DataFrame:
    """Compute Gini and permutation feature importances."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    feature_cols = list(X_test.columns)

    for name, pipeline in models.items():
        clf = pipeline.named_steps["clf"]

        # 1. Native Gini importance (RF and DT)
        if hasattr(clf, "feature_importances_"):
            for feat, val in zip(feature_cols, clf.feature_importances_):
                rows.append({
                    "model": name,
                    "feature": feat,
                    "source": "gini",
                    "importance_mean": float(val),
                    "importance_std": 0.0,
                })

        # 2. Permutation importance (all models)
        perm = permutation_importance(
            estimator=pipeline,
            X=X_test,
            y=y_test,
            n_repeats=5,
            random_state=42,
            scoring=make_scorer(f1_score, pos_label="Blackhole"),
        )
        for feat, mean, std in zip(feature_cols, perm.importances_mean, perm.importances_std):
            rows.append({
                "model": name,
                "feature": feat,
                "source": "permutation",
                "importance_mean": float(mean),
                "importance_std": float(std),
            })

    importance_df = pd.DataFrame(rows)
    importance_df.to_csv(p, index=False)
    return importance_df


def write_model_metadata(
    champion_name: str,
    champion_pipeline: Any,
    champion_row: Dict[str, Any],
    all_rows: List[Dict[str, Any]],
    tie_breakers: Dict[str, Any],
    path: Union[str, Path] = Path("ml/models/model_metadata.json"),
) -> None:
    """Serialize deterministic metadata JSON describing the persisted champion model."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    clf = champion_pipeline.named_steps["clf"]
    params = {k: v for k, v in clf.get_params().items() if isinstance(v, (int, float, str, bool, type(None)))}

    metadata = {
        "all_candidates": all_rows,
        "champion": champion_name,
        "champion_params": params,
        "feature_columns": [c for c in SCHEMA_COLUMNS if c != "label"],
        "labels": {
            "classes": sorted([str(c) for c in champion_pipeline.classes_]),
            "positive_class": "Blackhole",
        },
        "persistence": {
            "champion_path": "ml/models/best_model.joblib",
            "format": "joblib compress=3",
        },
        "selection": {
            "fpr_gate": FPR_GATE,
            "fpr_gate_satisfied": bool(champion_row["fpr"] <= FPR_GATE),
            "primary_metric": "f1_blackhole",
            "tie_breakers": ["latency_ms", "file_size_bytes"],
        },
        "test_metrics": champion_row,
        "telemetry": tie_breakers,
    }

    with open(p, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)


def write_evaluation_report(
    rows: List[Dict[str, Any]],
    champion_name: str,
    champion_row: Dict[str, Any],
    tie_breakers: Dict[str, Any],
    importance_df: pd.DataFrame,
    path: Union[str, Path] = Path("results/evaluation_report.md"),
) -> None:
    """Generate comprehensive evaluation report markdown document."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    table_lines = [
        "| Model | Accuracy | Precision | Recall | F1 (Blackhole) | FPR | TN | FP | FN | TP |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        table_lines.append(
            f"| {r['model']} | {r['accuracy']:.4f} | {r['precision']:.4f} | {r['recall']:.4f} | "
            f"{r['f1_blackhole']:.4f} | {r['fpr']:.4f} | {r['tn']} | {r['fp']} | {r['fn']} | {r['tp']} |"
        )
    table_md = "\n".join(table_lines)

    # Top features
    perm_rf = importance_df[(importance_df["model"] == champion_name) & (importance_df["source"] == "permutation")]
    top_features = perm_rf.sort_values("importance_mean", ascending=False).head(5)
    top_feat_lines = ["| Feature | Permutation Importance Mean | Std |", "|---|---|---|"]
    for _, item in top_features.iterrows():
        top_feat_lines.append(f"| {item['feature']} | {item['importance_mean']:.4f} | {item['importance_std']:.4f} |")
    top_feat_md = "\n".join(top_feat_lines)

    report_content = f"""# Intrusion Detection System - Phase 3 Evaluation Report

## 1. Methodology & Experimental Rigor
- **Evaluation Holdout (D-01):** Evaluated strictly on seed 44 (`data/test.csv`, 8,700 samples), kept completely untouched during 5-fold cross-validation training on seeds 42 & 43 (`data/train.csv`).
- **Cost-Sensitive Learning (D-05):** All pipelines trained with `class_weight='balanced'` to offset MANET class imbalance (2.3% attack windows).
- **False Positive Rate Acceptance Gate (D-06):** Locked threshold of $\\text{{FPR}} \\le 0.01$ (1.0%). Models exceeding this gate are disqualified to prevent routing disruption during live mitigation.

---

## 2. Benchmark Security Metrics (Held-Out Test Set: Seed 44)

{table_md}

---

## 3. Champion Model Selection Rationale (D-11, D-12)
- **Champion:** `{champion_name}`
- **FPR Gate Satisfied:** `{champion_row['fpr'] <= FPR_GATE}` (FPR = `{champion_row['fpr']:.6f}` vs limit `{FPR_GATE:.4f}`)
- **Primary Metric F1 (Blackhole):** `{champion_row['f1_blackhole']:.4f}`
- **Evaluation Latency:** `{tie_breakers['latency_ms']:.2f} ms`
- **Model Binary Size:** `{tie_breakers['file_size_bytes']} bytes`
- **Persistence Target:** `ml/models/best_model.joblib` with verified `predict_proba` interface for Phase 5 closed-loop mitigation.

---

## 4. Feature Importance Analysis (Champion: `{champion_name}`)

{top_feat_md}

---

## 5. Artifact Ledger & Reproducibility Chain
To reproduce this entire evaluation pipeline deterministically:
```bash
python scripts/build_dataset.py
python -m ml.train
python -m ml.evaluate
```

Confusion matrix figures saved:
- `results/plots/confusion_matrix_random_forest.png`
- `results/plots/confusion_matrix_decision_tree.png`
- `results/plots/confusion_matrix_svm.png`
"""
    p.write_text(report_content, encoding="utf-8")


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for evaluation runner."""
    parser = argparse.ArgumentParser(
        description="Evaluate candidate models on held-out test data, gate champion, and export metrics."
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default="ml/models",
        help="Directory containing serialized joblib candidates (default: ml/models)",
    )
    parser.add_argument(
        "--test-csv",
        type=str,
        default="data/test.csv",
        help="Path to held-out test dataset CSV (default: data/test.csv)",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Directory for evaluation metrics, plots, and reports (default: results)",
    )
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """Run evaluation, champion selection, and artifact generation."""
    parsed = parse_args(args)
    models_dir = Path(parsed.models_dir)
    results_dir = Path(parsed.results_dir)

    print("=" * 80)
    print("MANET INTRUSION DETECTION SYSTEM - MODEL EVALUATION (ML-02 / ML-03)")
    print(f"Candidates dir: {models_dir}")
    print(f"Test split:     {parsed.test_csv}")
    print(f"Results dir:    {results_dir}")
    print(f"Locked FPR Gate: {FPR_GATE * 100:.1f}%")
    print("=" * 80)

    try:
        candidates = load_candidates(models_dir)
        rows, X_test, y_test = evaluate_on_test(candidates, parsed.test_csv)

        print("\n[*] Evaluation results on held-out test set:")
        for r in rows:
            print(
                f"    - {r['model']:14s} | F1: {r['f1_blackhole']:.4f} | FPR: {r['fpr']:.4f} | "
                f"Prec: {r['precision']:.4f} | Rec: {r['recall']:.4f} | Acc: {r['accuracy']:.4f}"
            )

        print(f"\n[*] Applying FPR Gate <= {FPR_GATE} and selecting champion...")
        champion_row, champion_pipe, tie_breakers = select_champion(
            rows=rows,
            candidates=candidates,
            X_test=X_test,
            models_dir=models_dir,
        )
        champion_name = champion_row["model"]
        print(f"[+] Champion selected: '{champion_name}' with F1={champion_row['f1_blackhole']:.4f}, FPR={champion_row['fpr']:.4f}")

        # Ensure predict_proba interface with parity
        persisted_champion = refit_with_probability(
            champion_name=champion_name,
            champion_pipeline=champion_pipe,
            train_csv_path="data/train.csv",
            test_csv_path=parsed.test_csv,
        )

        best_model_path = models_dir / "best_model.joblib"
        joblib.dump(persisted_champion, best_model_path, compress=3)
        print(f"[+] Persisted champion to {best_model_path} ({best_model_path.stat().st_size} bytes)")

        # Write model metadata JSON
        write_model_metadata(
            champion_name=champion_name,
            champion_pipeline=persisted_champion,
            champion_row=champion_row,
            all_rows=rows,
            tie_breakers=tie_breakers,
            path=models_dir / "model_metadata.json",
        )
        print(f"[+] Wrote metadata to {models_dir / 'model_metadata.json'}")

        # Export metrics CSV
        metrics_csv_path = results_dir / "metrics.csv"
        export_metrics_csv(rows, metrics_csv_path)
        print(f"[+] Exported metrics to {metrics_csv_path}")

        # Export confusion matrix plots
        plots_dir = results_dir / "plots"
        plot_confusion_matrices(candidates, X_test, y_test, plots_dir)
        print(f"[+] Saved confusion matrix plots to {plots_dir}")

        # Export feature importance CSV
        feat_imp_path = results_dir / "feature_importance.csv"
        importance_df = export_feature_importance(candidates, X_test, y_test, feat_imp_path)
        print(f"[+] Saved feature importance to {feat_imp_path}")

        # Write markdown evaluation report
        report_path = results_dir / "evaluation_report.md"
        write_evaluation_report(
            rows=rows,
            champion_name=champion_name,
            champion_row=champion_row,
            tie_breakers=tie_breakers,
            importance_df=importance_df,
            path=report_path,
        )
        print(f"[+] Generated evaluation report at {report_path}")

        print("\n" + "=" * 80)
        print("EVALUATION & ARTIFACT EXPORT COMPLETE")
        print("=" * 80)
        return 0

    except Exception as e:
        print(f"\n[ERROR] Evaluation failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
