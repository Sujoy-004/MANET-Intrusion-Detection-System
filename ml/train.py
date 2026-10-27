"""Train and tune Random Forest, Decision Tree, and SVM classifiers on MANET features.

Enforces cost-sensitive learning (class_weight='balanced'), stratified 5-fold cross-validation,
deterministic hyperparameters (random_state=42), and native string labels.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

# Bootstrap repository root into sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from feature_extraction.extract_features import SCHEMA_COLUMNS

SVM_SUBSAMPLE_ROWS: int = 10000


def load_training_data(
    path: Union[str, Path] = Path("data/train.csv"),
) -> Tuple[pd.DataFrame, pd.Series]:
    """Load training features and labels with schema and finiteness validation.

    Labels are kept as native string objects ('Normal', 'Blackhole') with NO
    LabelEncoder, avoiding alphabetical semantic inversion.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Training file not found: {p}")

    df = pd.read_csv(p)
    if df.empty:
        raise ValueError("Training file is empty.")

    feature_cols = [c for c in SCHEMA_COLUMNS if c != "label"]
    for c in feature_cols:
        if c not in df.columns:
            raise ValueError(f"Missing required feature column: {c}")
        vals = df[c].to_numpy(dtype=float)
        if not np.all(np.isfinite(vals)):
            raise ValueError(f"Feature column '{c}' contains NaN or infinite values.")

    if "label" not in df.columns:
        raise ValueError("Missing 'label' column in training dataset.")

    unique_labels = set(df["label"].unique())
    valid_labels = {"Normal", "Blackhole", "Grayhole"}
    if not unique_labels.issubset(valid_labels):
        raise ValueError(f"Unexpected labels found: {unique_labels - valid_labels}")

    if "Normal" not in unique_labels:
        raise ValueError("Training dataset has zero 'Normal' rows (degenerate).")

    if not (unique_labels - {"Normal"}):
        raise ValueError("Training dataset has zero attack rows (degenerate).")

    X = df[feature_cols].copy()
    y = df["label"].astype(str).copy()
    return X, y


def build_scoring() -> Dict[str, Any]:
    """Construct multi-metric scoring dictionary."""
    def make_class_scorer(target_label: str):
        def scorer_func(y_true, y_pred):
            y_true_bin = [1 if v == target_label else 0 for v in y_true]
            y_pred_bin = [1 if v == target_label else 0 for v in y_pred]
            return float(f1_score(y_true_bin, y_pred_bin, pos_label=1, zero_division=0))
        return make_scorer(scorer_func)

    def attack_f1(y_true, y_pred):
        y_true_bin = [0 if v == "Normal" else 1 for v in y_true]
        y_pred_bin = [0 if v == "Normal" else 1 for v in y_pred]
        return float(f1_score(y_true_bin, y_pred_bin, pos_label=1, zero_division=0))

    return {
        "f1_blackhole": make_class_scorer("Blackhole"),
        "f1_grayhole": make_class_scorer("Grayhole"),
        "f1_attack": make_scorer(attack_f1),
        "f1_macro": "f1_macro",
        "balanced_accuracy": "balanced_accuracy",
    }


def build_pipelines() -> Dict[str, Tuple[Pipeline, Dict[str, List[Any]]]]:
    """Construct Scikit-learn Pipeline and parameter grid for each classifier candidate."""
    pipelines: Dict[str, Tuple[Pipeline, Dict[str, List[Any]]]] = {
        "random_forest": (
            Pipeline([
                ("scaler", StandardScaler()),
                (
                    "clf",
                    RandomForestClassifier(
                        class_weight="balanced",
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]),
            {
                "clf__n_estimators": [50, 100],
                "clf__max_depth": [12, None],
                "clf__class_weight": [
                    "balanced_subsample",
                    {"Normal": 1.0, "Blackhole": 25.0, "Grayhole": 10.0},
                ],
            },
        ),
        "decision_tree": (
            Pipeline([
                ("scaler", StandardScaler()),
                (
                    "clf",
                    DecisionTreeClassifier(
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]),
            {
                "clf__max_depth": [4, 8, 12, None],
                "clf__min_samples_split": [2, 10],
            },
        ),
        "svm": (
            Pipeline([
                ("scaler", StandardScaler()),
                (
                    "clf",
                    SVC(
                        kernel="rbf",
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]),
            {
                "clf__C": [1, 10, 100],
                "clf__gamma": ["scale", 0.01],
            },
        ),
    }
    return pipelines


def stratified_subsample(
    X: pd.DataFrame,
    y: pd.Series,
    n: int = 10000,
    random_state: int = 0,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Extract a balanced, stratified subsample of size min(n, len(X))."""
    if len(X) <= n:
        return X.copy(), y.copy()

    X_sub, _, y_sub, _ = train_test_split(
        X,
        y,
        train_size=n,
        stratify=y,
        random_state=random_state,
    )
    return X_sub.reset_index(drop=True), y_sub.reset_index(drop=True)


def fit_pipeline(
    pipeline: Pipeline,
    param_grid: Dict[str, List[Any]],
    X: pd.DataFrame,
    y: pd.Series,
    cv: int = 5,
    refit: Optional[str] = None,
) -> GridSearchCV:
    """Run stratified 5-fold GridSearchCV tuning on f1_macro or attack-specific scoring."""
    if refit is None:
        refit = "f1_macro" if "Grayhole" in set(y) else "f1_blackhole"
    grid = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        scoring=build_scoring(),
        refit=refit,
        cv=cv,
        n_jobs=1,
        return_train_score=False,
    )
    grid.fit(X, y)
    return grid


def tune_and_save(
    model_names: List[str],
    train_csv_path: Union[str, Path] = Path("data/train.csv"),
    models_dir: Union[str, Path] = Path("ml/models"),
    subsample_rows: int = SVM_SUBSAMPLE_ROWS,
) -> Dict[str, GridSearchCV]:
    """Train, tune, and serialize candidate pipelines."""
    X, y = load_training_data(train_csv_path)
    pipelines_dict = build_pipelines()

    models_dir_path = Path(models_dir)
    models_dir_path.mkdir(parents=True, exist_ok=True)

    results: Dict[str, GridSearchCV] = {}

    print("=" * 80)
    print("MANET INTRUSION DETECTION SYSTEM - MODEL TRAINING (ML-01)")
    print(f"Training samples: {len(X)} | Target distribution: {dict(y.value_counts())}")
    print(f"Models to train: {model_names}")
    print("=" * 80)

    for name in model_names:
        if name not in pipelines_dict:
            raise ValueError(f"Unknown model name '{name}'. Available: {list(pipelines_dict.keys())}")

        pipeline, param_grid = pipelines_dict[name]

        print(f"\n[*] Tuning candidate '{name}'...")
        start_t = time.perf_counter()

        if name == "svm":
            print(f"    - Subsampling to {subsample_rows} rows for SVM CV budget...")
            X_fit, y_fit = stratified_subsample(X, y, n=subsample_rows, random_state=0)
        else:
            X_fit, y_fit = X, y

        grid = fit_pipeline(pipeline, param_grid, X_fit, y_fit, cv=5)
        elapsed = time.perf_counter() - start_t

        best_score = grid.best_score_
        best_params = grid.best_params_
        out_path = models_dir_path / f"{name}.joblib"
        joblib.dump(grid.best_estimator_, out_path, compress=3)

        print(f"[+] '{name}' completed in {elapsed:.2f}s:")
        print(f"    - Best CV F1 (Blackhole): {best_score:.4f}")
        print(f"    - Best Params: {best_params}")
        print(f"    - Serialized: {out_path} ({out_path.stat().st_size} bytes)")

        results[name] = grid

    print("\n" + "=" * 80)
    print("ALL REQUESTED CANDIDATE MODELS TRAINED & PERSISTED")
    print("=" * 80)
    return results


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for model training."""
    parser = argparse.ArgumentParser(
        description="Train and tune IDS classification models using 5-fold CV on training data."
    )
    parser.add_argument(
        "--models",
        type=str,
        default="random_forest,decision_tree,svm",
        help="Comma-separated model names: random_forest,decision_tree,svm",
    )
    parser.add_argument(
        "--train-csv",
        type=str,
        default="data/train.csv",
        help="Path to training CSV file (default: data/train.csv)",
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default="ml/models",
        help="Output directory for serialized joblib models (default: ml/models)",
    )
    parser.add_argument(
        "--subsample",
        type=int,
        default=SVM_SUBSAMPLE_ROWS,
        help=f"Stratified subsample size for SVM (default: {SVM_SUBSAMPLE_ROWS})",
    )
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """CLI entrypoint."""
    parsed = parse_args(args)
    model_names = [m.strip() for m in parsed.models.split(",") if m.strip()]
    try:
        tune_and_save(
            model_names=model_names,
            train_csv_path=parsed.train_csv,
            models_dir=parsed.models_dir,
            subsample_rows=parsed.subsample,
        )
        return 0
    except Exception as e:
        print(f"\n[ERROR] Model training failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
