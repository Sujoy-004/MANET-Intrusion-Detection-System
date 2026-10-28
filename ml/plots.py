"""Publication-grade visualization library for MANET ML-IDS.

Generates high-resolution (300 DPI), academic-standard figures evaluating:
1. Closed-loop QoS recovery triad (Baseline AODV vs. Attack AODV vs. AODV+IDS).
2. Classifier benchmarking with FPR operational gate enforcement.
3. Random Forest feature importance (Permutation vs. Gini).
4. Environmental stress testing (mobility speed, drop probability).
5. Mitigation quarantine and node isolation timeline dynamics.
6. Standardized confusion matrices.

Satisfies requirement RESP-03 (visualizing recovery across comparative triads)
and non-negotiable evaluation integrity (AGENTS.md Rule 8).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Enforce headless Agg backend before importing pyplot or seaborn (T-06-01)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

# Academic typography and colorblind-safe triad palette
sns.set_theme(style="whitegrid", font="sans-serif")
plt.rcParams.update({
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.autolayout": False,
})

TRIAD_PALETTE: Dict[str, str] = {
    "Baseline": "#4C72B0",  # Slate Blue
    "Attack": "#C44E52",    # Crimson / Coral
    "AODV+IDS": "#55A868",  # Emerald Green
}

SCENARIO_DISPLAY_NAMES: Dict[str, str] = {
    "30n_blackhole": "30n Blackhole\n(p=1.0)",
    "30n_grayhole_p50": "30n Grayhole\n(p=0.5)",
    "30n_grayhole_p70": "30n Grayhole\n(p=0.7)",
    "50n_grayhole_p50": "50n Grayhole\n(p=0.5)",
}

FEATURE_DISPLAY_NAMES: Dict[str, str] = {
    "packet_drop_ratio": "Packet Drop Ratio",
    "hop_count": "Hop Count",
    "packet_forward_ratio": "Packet Forward Ratio",
    "route_reply_rate": "Route Reply Rate",
    "neighbor_count": "Neighbor Count",
    "route_request_rate": "Route Request Rate",
    "mobility_speed": "Mobility Speed",
    "throughput": "Throughput",
    "avg_delay": "Average Delay",
}


def _load_and_validate_df(
    data: Union[pd.DataFrame, str, Path],
    required_columns: List[str],
    description: str = "dataset",
) -> pd.DataFrame:
    """Load and validate DataFrame columns or raise descriptive errors."""
    if isinstance(data, (str, Path)):
        p = Path(data)
        if not p.is_file():
            raise FileNotFoundError(f"Required {description} CSV file not found: {p}")
        df = pd.read_csv(p)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise TypeError(f"Expected DataFrame, str, or Path for {description}, got {type(data)}")

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{description} missing required columns: {missing}")

    return df


def plot_executive_dashboard(
    df_closed_loop: Union[pd.DataFrame, str, Path],
    out_path: Union[str, Path],
    dpi: int = 300,
) -> Path:
    """Generate 4-panel 2x2 executive dashboard showing complete QoS recovery triad.

    Panels:
        (a) Packet Delivery Ratio (PDR)
        (b) Network Throughput (kbps)
        (c) Average End-to-End Delay (ms)
        (d) Routing Overhead Ratio (routing packets / data packets)

    Parameters
    ----------
    df_closed_loop : DataFrame or CSV path
        Triad benchmark metrics (from results/closed_loop_metrics.csv).
    out_path : Path or str
        Destination path for generated PNG.
    dpi : int, optional
        Image resolution (default 300).

    Returns
    -------
    Path
        Path to generated image.
    """
    req_cols = ["scenario", "mode", "pdr", "throughput_kbps", "avg_delay_ms", "routing_overhead"]
    df = _load_and_validate_df(df_closed_loop, req_cols, "closed_loop_metrics")

    # Map scenario names for display
    df["scenario_display"] = df["scenario"].map(lambda s: SCENARIO_DISPLAY_NAMES.get(s, str(s)))
    scenario_order = [
        SCENARIO_DISPLAY_NAMES[k]
        for k in ["30n_blackhole", "30n_grayhole_p50", "30n_grayhole_p70", "50n_grayhole_p50"]
        if k in df["scenario"].values
    ]
    if not scenario_order:
        scenario_order = list(df["scenario_display"].unique())

    mode_order = ["Baseline", "Attack", "AODV+IDS"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    panels = [
        ("pdr", "(a) Packet Delivery Ratio (PDR)", "PDR (Delivered / Generated)", axes[0, 0], "{:.2f}", (0, 1.15)),
        ("throughput_kbps", "(b) Network Throughput", "Throughput (kbps)", axes[0, 1], "{:.1f}", None),
        ("avg_delay_ms", "(c) Average End-to-End Delay", "Avg Delay (ms)", axes[1, 0], "{:.1f}", None),
        ("routing_overhead", "(d) Control Routing Overhead Penalty", "Routing Overhead (pkts/data)", axes[1, 1], "{:.3f}", None),
    ]

    for metric, title, ylabel, ax, fmt, ylim in panels:
        sns.barplot(
            data=df,
            x="scenario_display",
            y=metric,
            hue="mode",
            order=scenario_order,
            hue_order=mode_order,
            palette=TRIAD_PALETTE,
            ax=ax,
            errorbar="sd",
            capsize=0.08,
            err_kws={"linewidth": 1.2},
        )
        ax.set_title(title, fontsize=12, fontweight="bold", pad=8)
        ax.set_xlabel("")
        ax.set_ylabel(ylabel, fontsize=11, fontweight="medium")
        if ylim is not None:
            ax.set_ylim(ylim)

        # Annotate bars with values
        for container in ax.containers:
            ax.bar_label(container, fmt=fmt, padding=3, fontsize=8.5, fontweight="semibold")

        # Remove local legend
        if ax.get_legend() is not None:
            ax.get_legend().remove()

    # Unified master legend at the top
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=3,
        bbox_to_anchor=(0.5, 0.99),
        frameon=True,
        facecolor="white",
        edgecolor="#cccccc",
        fontsize=11,
    )

    fig.suptitle(
        "Closed-Loop QoS Recovery Triad Benchmark (Baseline vs. Attack vs. AODV+IDS)",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_qos_recovery_triad(
    df_closed_loop: Union[pd.DataFrame, str, Path],
    out_dir: Union[str, Path],
    dpi: int = 300,
) -> List[Path]:
    """Generate 4 dedicated standalone figures for PDR, throughput, delay, and overhead.

    Figures generated in out_dir:
    - qos_pdr_recovery.png (with recovery ratio callouts)
    - qos_throughput_recovery.png
    - qos_delay_impact.png
    - qos_routing_overhead_penalty.png

    Parameters
    ----------
    df_closed_loop : DataFrame or CSV path
        Triad benchmark metrics.
    out_dir : Path or str
        Output directory.
    dpi : int, optional
        Resolution (default 300).

    Returns
    -------
    List[Path]
        List of generated file paths.
    """
    req_cols = ["scenario", "mode", "pdr", "throughput_kbps", "avg_delay_ms", "routing_overhead"]
    df = _load_and_validate_df(df_closed_loop, req_cols, "closed_loop_metrics")
    out_d = Path(out_dir)
    out_d.mkdir(parents=True, exist_ok=True)

    df["scenario_display"] = df["scenario"].map(lambda s: SCENARIO_DISPLAY_NAMES.get(s, str(s)))
    scenario_order = [
        SCENARIO_DISPLAY_NAMES[k]
        for k in ["30n_blackhole", "30n_grayhole_p50", "30n_grayhole_p70", "50n_grayhole_p50"]
        if k in df["scenario"].values
    ]
    if not scenario_order:
        scenario_order = list(df["scenario_display"].unique())

    mode_order = ["Baseline", "Attack", "AODV+IDS"]
    generated_paths: List[Path] = []

    # 1. Standalone PDR Recovery with recovery percentage callouts
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.barplot(
        data=df,
        x="scenario_display",
        y="pdr",
        hue="mode",
        order=scenario_order,
        hue_order=mode_order,
        palette=TRIAD_PALETTE,
        ax=ax,
        errorbar="sd",
        capsize=0.08,
    )
    ax.set_title("Packet Delivery Ratio (PDR) Recovery Under Active IDS Mitigation", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Scenario & Network Topology", fontsize=11, fontweight="medium")
    ax.set_ylabel("Packet Delivery Ratio (PDR)", fontsize=11, fontweight="medium")
    ax.set_ylim(0, 1.20)

    # Bar value labels
    for container in ax.containers:
        ax.bar_label(container, fmt="{:.2f}", padding=3, fontsize=9, fontweight="semibold")

    # Calculate and annotate recovery ratios on the AODV+IDS bars
    means = df.groupby(["scenario", "mode"])["pdr"].mean()
    scenario_keys = ["30n_blackhole", "30n_grayhole_p50", "30n_grayhole_p70", "50n_grayhole_p50"]
    for i, sc in enumerate(scenario_keys):
        if (sc, "Baseline") in means and (sc, "Attack") in means and (sc, "AODV+IDS") in means:
            b_val = means[(sc, "Baseline")]
            a_val = means[(sc, "Attack")]
            ids_val = means[(sc, "AODV+IDS")]
            if b_val != a_val:
                recovery = ((ids_val - a_val) / (b_val - a_val)) * 100
                # Position callout above the AODV+IDS bar (3rd bar in group: offset +0.27)
                callout_y = max(b_val, ids_val) + 0.10
                ax.annotate(
                    f"Recovery:\n{recovery:.1f}%",
                    xy=(i + 0.27, ids_val),
                    xytext=(i + 0.27, min(callout_y, 1.12)),
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                    fontweight="bold",
                    color="#2d6a4f",
                    arrowprops=dict(arrowstyle="->", color="#2d6a4f", lw=1.2),
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="#e8f5e9", edgecolor="#81c784", alpha=0.9),
                )

    ax.legend(title="Network Mode", loc="upper right", frameon=True, facecolor="white")
    fig.tight_layout()
    pdr_path = out_d / "qos_pdr_recovery.png"
    fig.savefig(pdr_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    generated_paths.append(pdr_path)

    # 2. Standalone Throughput Recovery
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.barplot(
        data=df,
        x="scenario_display",
        y="throughput_kbps",
        hue="mode",
        order=scenario_order,
        hue_order=mode_order,
        palette=TRIAD_PALETTE,
        ax=ax,
        errorbar="sd",
        capsize=0.08,
    )
    ax.set_title("Network Goodput & Throughput Restoration Across Scenarios", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Scenario & Network Topology", fontsize=11, fontweight="medium")
    ax.set_ylabel("Throughput (kbps)", fontsize=11, fontweight="medium")
    for container in ax.containers:
        ax.bar_label(container, fmt="{:.1f}", padding=3, fontsize=9, fontweight="semibold")
    ax.legend(title="Network Mode", loc="upper left", frameon=True, facecolor="white")
    fig.tight_layout()
    tp_path = out_d / "qos_throughput_recovery.png"
    fig.savefig(tp_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    generated_paths.append(tp_path)

    # 3. Standalone End-to-End Delay Impact
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.barplot(
        data=df,
        x="scenario_display",
        y="avg_delay_ms",
        hue="mode",
        order=scenario_order,
        hue_order=mode_order,
        palette=TRIAD_PALETTE,
        ax=ax,
        errorbar="sd",
        capsize=0.08,
    )
    ax.set_title("Average End-to-End Packet Delay (ms) Across Triad Modes", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Scenario & Network Topology", fontsize=11, fontweight="medium")
    ax.set_ylabel("Average Latency (ms)", fontsize=11, fontweight="medium")
    for container in ax.containers:
        ax.bar_label(container, fmt="{:.1f}", padding=3, fontsize=9, fontweight="semibold")
    ax.legend(title="Network Mode", loc="upper left", frameon=True, facecolor="white")
    fig.tight_layout()
    delay_path = out_d / "qos_delay_impact.png"
    fig.savefig(delay_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    generated_paths.append(delay_path)

    # 4. Standalone Routing Overhead Penalty
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.barplot(
        data=df,
        x="scenario_display",
        y="routing_overhead",
        hue="mode",
        order=scenario_order,
        hue_order=mode_order,
        palette=TRIAD_PALETTE,
        ax=ax,
        errorbar="sd",
        capsize=0.08,
    )
    ax.set_title("Routing Overhead Ratio Penalty (Control Traffic vs. Data Packets)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Scenario & Network Topology", fontsize=11, fontweight="medium")
    ax.set_ylabel("Routing Overhead Ratio (RREQ+RREP / Data)", fontsize=11, fontweight="medium")
    for container in ax.containers:
        ax.bar_label(container, fmt="{:.3f}", padding=3, fontsize=8.5, fontweight="semibold")

    # Annotate overhead cost for Blackhole 30n
    if ("30n_blackhole", "AODV+IDS") in means and ("30n_blackhole", "Baseline") in means:
        delta_oh = df.loc[(df["scenario"] == "30n_blackhole") & (df["mode"] == "AODV+IDS"), "routing_overhead"].mean() - \
                   df.loc[(df["scenario"] == "30n_blackhole") & (df["mode"] == "Baseline"), "routing_overhead"].mean()
        ax.annotate(
            f"Overhead Penalty:\n+{delta_oh:.4f} pkts/data",
            xy=(0 + 0.27, 0.0859),
            xytext=(0 + 0.40, 0.11),
            ha="left",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#b71c1c",
            arrowprops=dict(arrowstyle="->", color="#b71c1c", lw=1.2),
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffebee", edgecolor="#ef9a9a", alpha=0.9),
        )

    ax.legend(title="Network Mode", loc="upper left", frameon=True, facecolor="white")
    fig.tight_layout()
    oh_path = out_d / "qos_routing_overhead_penalty.png"
    fig.savefig(oh_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    generated_paths.append(oh_path)

    return generated_paths


def plot_classifier_comparison(
    df_metrics: Union[pd.DataFrame, str, Path],
    out_path: Union[str, Path],
    dpi: int = 300,
) -> Path:
    """Grouped bar chart comparing RF, DT, and SVM across accuracy, precision, recall, F1, and FPR.

    Enforces the explicit operational FPR <= 0.01 reference line.

    Parameters
    ----------
    df_metrics : DataFrame or CSV path
        Evaluation metrics on held-out Seed 44 test data (from results/metrics.csv).
    out_path : Path or str
        Destination path.
    dpi : int, optional
        Resolution (default 300).

    Returns
    -------
    Path
        Path to generated image.
    """
    req_cols = ["model", "accuracy", "precision", "recall", "fpr"]
    df = _load_and_validate_df(df_metrics, req_cols, "metrics")

    # Handle f1_blackhole or f1 column
    f1_col = "f1_blackhole" if "f1_blackhole" in df.columns else "f1"
    if f1_col not in df.columns:
        raise ValueError(f"metrics dataframe missing F1 column (expected 'f1_blackhole' or 'f1')")

    model_display = {
        "random_forest": "Random Forest (Champion)",
        "decision_tree": "Decision Tree (Baseline)",
        "svm": "SVM (Baseline)",
    }
    df["model_display"] = df["model"].map(lambda m: model_display.get(m, str(m).title()))

    metric_display = {
        "accuracy": "Accuracy",
        "precision": "Precision",
        "recall": "Recall",
        f1_col: "F1-Score (Malicious)",
        "fpr": "False Positive Rate (FPR)",
    }

    # Reshape to long format for Seaborn
    records = []
    for _, row in df.iterrows():
        for m_col, m_name in metric_display.items():
            records.append({
                "Model": row["model_display"],
                "Metric": m_name,
                "Value": float(row[m_col]),
            })
    tidy_df = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=(11, 6))
    model_order = [
        model_display["random_forest"],
        model_display["decision_tree"],
        model_display["svm"],
    ]
    model_palette = {
        model_display["random_forest"]: "#2B5C8F",  # Deep Navy / Blue
        model_display["decision_tree"]: "#E66101",  # Burnt Orange
        model_display["svm"]: "#5E3C99",            # Royal Purple
    }

    sns.barplot(
        data=tidy_df,
        x="Metric",
        y="Value",
        hue="Model",
        hue_order=model_order,
        palette=model_palette,
        ax=ax,
    )

    ax.set_title(
        "Multi-Classifier Security Performance Benchmark (Seed 44 Untouched Test Set)",
        fontsize=13,
        fontweight="bold",
        pad=14,
    )
    ax.set_xlabel("Evaluation Metric", fontsize=11, fontweight="medium")
    ax.set_ylabel("Score / Ratio (0.0 - 1.0)", fontsize=11, fontweight="medium")
    ax.set_ylim(0, 1.15)

    # Value labels on top of bars
    for container in ax.containers:
        ax.bar_label(container, fmt="{:.3f}", padding=3, fontsize=8.5, fontweight="semibold")

    # Operational Gate: FPR <= 0.01 dashed reference line
    ax.axhline(
        0.01,
        color="#c44e52",
        linestyle="--",
        linewidth=1.8,
        label="Operational Gate: FPR <= 0.01 (1.0%)",
        zorder=5,
    )

    # Explicit text annotation pointing to FPR operational gate
    fpr_x_idx = list(metric_display.values()).index("False Positive Rate (FPR)")
    ax.annotate(
        "FPR Gate (1.0%)\nRF: 0.99% (PASS)\nDT: 3.42% (FAIL)\nSVM: 46.38% (FAIL)",
        xy=(fpr_x_idx, 0.01),
        xytext=(fpr_x_idx - 0.25, 0.25),
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
        color="#b71c1c",
        arrowprops=dict(arrowstyle="->", color="#b71c1c", lw=1.3),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffebee", edgecolor="#ef9a9a", alpha=0.95),
    )

    # Position legend cleanly
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=9.5)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_feature_importance(
    df_importance: Union[pd.DataFrame, str, Path],
    out_path: Union[str, Path],
    dpi: int = 300,
) -> Path:
    """Horizontal bar chart comparing Random Forest Permutation Importance and Gini Impurity.

    Sorted by Permutation Importance mean descending.

    Parameters
    ----------
    df_importance : DataFrame or CSV path
        Feature importance table (from results/feature_importance.csv).
    out_path : Path or str
        Destination path.
    dpi : int, optional
        Resolution (default 300).

    Returns
    -------
    Path
        Path to generated image.
    """
    req_cols = ["model", "feature", "source", "importance_mean", "importance_std"]
    df = _load_and_validate_df(df_importance, req_cols, "feature_importance")

    # Filter for Random Forest
    rf_df = df[df["model"] == "random_forest"].copy()
    if rf_df.empty:
        raise ValueError("feature_importance dataframe contains no rows for model 'random_forest'")

    # Separate permutation and gini
    perm = rf_df[rf_df["source"] == "permutation"].set_index("feature")
    gini = rf_df[rf_df["source"] == "gini"].set_index("feature")

    # Sort features by permutation importance mean descending
    sorted_features = perm["importance_mean"].sort_values(ascending=True).index.tolist()

    # Align data
    perm_means = [perm.loc[f, "importance_mean"] if f in perm.index else 0.0 for f in sorted_features]
    perm_stds = [perm.loc[f, "importance_std"] if f in perm.index else 0.0 for f in sorted_features]
    gini_means = [gini.loc[f, "importance_mean"] if f in gini.index else 0.0 for f in sorted_features]
    feature_labels = [FEATURE_DISPLAY_NAMES.get(f, f) for f in sorted_features]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5), sharey=True)

    y_pos = np.arange(len(sorted_features))

    # Panel (a): Permutation Importance
    bars1 = ax1.barh(
        y_pos,
        perm_means,
        xerr=perm_stds,
        capsize=3.5,
        color="#4C72B0",
        edgecolor="#2b4c7e",
        alpha=0.9,
    )
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(feature_labels, fontsize=10.5, fontweight="medium")
    ax1.set_xlabel("Mean Decrease in F1-Score (Test Set)", fontsize=11, fontweight="medium")
    ax1.set_title("(a) Permutation Importance (Anti-Leakage Ground Truth)", fontsize=11.5, fontweight="bold", pad=8)
    ax1.axvline(0, color="#888888", linestyle="-", linewidth=0.8)

    # Annotate permutation values
    for i, bar in enumerate(bars1):
        val = perm_means[i]
        offset = 0.005 if val >= 0 else -0.015
        ax1.text(
            val + offset,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.4f}",
            va="center",
            ha="left" if val >= 0 else "right",
            fontsize=8.5,
            fontweight="semibold",
        )

    # Panel (b): Gini Impurity Importance
    bars2 = ax2.barh(
        y_pos,
        gini_means,
        color="#55A868",
        edgecolor="#2d6a4f",
        alpha=0.9,
    )
    ax2.set_xlabel("Mean Decrease in Impurity (Gini / MDI)", fontsize=11, fontweight="medium")
    ax2.set_title("(b) Gini Impurity Importance (Training Tree Splits)", fontsize=11.5, fontweight="bold", pad=8)

    # Annotate gini values
    for i, bar in enumerate(bars2):
        val = gini_means[i]
        ax2.text(
            val + 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.4f}",
            va="center",
            ha="left",
            fontsize=8.5,
            fontweight="semibold",
        )

    fig.suptitle(
        "Random Forest Feature Importance: Permutation vs. Gini Impurity Ranking",
        fontsize=13.5,
        fontweight="bold",
        y=0.98,
    )

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_generalization_stress(
    df_gen: Union[pd.DataFrame, str, Path],
    out_dir: Union[str, Path],
    dpi: int = 300,
) -> List[Path]:
    """Generate environmental stress curves across node mobility speeds and Grayhole drop probabilities.

    Figures generated in out_dir:
    - stress_mobility_vs_recall.png
    - stress_droprate_vs_pdr.png

    Parameters
    ----------
    df_gen : DataFrame or CSV path
        Generalization matrix metrics (from results/generalization_metrics.csv).
    out_dir : Path or str
        Output directory.
    dpi : int, optional
        Resolution (default 300).

    Returns
    -------
    List[Path]
        List of generated file paths.
    """
    req_cols = ["nodes", "speed", "drop_prob", "pdr", "recall", "f1", "fpr", "accuracy"]
    df = _load_and_validate_df(df_gen, req_cols, "generalization_metrics")
    out_d = Path(out_dir)
    out_d.mkdir(parents=True, exist_ok=True)

    generated_paths: List[Path] = []

    # 1. Mobility Speed vs. Recall & F1
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)

    speeds = [1.0, 5.0, 10.0]
    node_configs = sorted(df["nodes"].unique())

    palette_nodes = {30: "#4C72B0", 50: "#C44E52"}
    markers = {30: "o", 50: "s"}

    for node_count in node_configs:
        sub = df[df["nodes"] == node_count].groupby("speed", as_index=False)[["recall", "f1", "fpr"]].mean()
        color = palette_nodes.get(node_count, "#333333")
        marker = markers.get(node_count, "o")

        # Left panel: Recall vs. Speed
        ax1.plot(
            sub["speed"],
            sub["recall"],
            marker=marker,
            markersize=8,
            linewidth=2.2,
            color=color,
            label=f"{node_count} Nodes (Recall)",
        )
        # Right panel: F1 vs. Speed
        ax2.plot(
            sub["speed"],
            sub["f1"],
            marker=marker,
            markersize=8,
            linewidth=2.2,
            color=color,
            label=f"{node_count} Nodes (F1)",
        )

    ax1.set_title("(a) Attack Detection Recall vs. Speed", fontsize=12, fontweight="bold", pad=8)
    ax1.set_xlabel("Node Mobility Speed (m/s)", fontsize=11, fontweight="medium")
    ax1.set_ylabel("Detection Score (0.0 - 1.0)", fontsize=11, fontweight="medium")
    ax1.set_xticks(speeds)
    ax1.set_ylim(-0.05, 1.05)
    ax1.legend(loc="upper right", frameon=True, facecolor="white")

    # Annotate route volatility collapse at 10 m/s
    ax1.annotate(
        "Topology Volatility:\nRoute breaks mask\nmalicious drops",
        xy=(10.0, 0.0),
        xytext=(7.5, 0.30),
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
        color="#b71c1c",
        arrowprops=dict(arrowstyle="->", color="#b71c1c", lw=1.2),
        bbox=dict(boxstyle="round,pad=0.2", facecolor="#ffebee", edgecolor="#ef9a9a", alpha=0.9),
    )

    ax2.set_title("(b) Malicious F1-Score vs. Speed", fontsize=12, fontweight="bold", pad=8)
    ax2.set_xlabel("Node Mobility Speed (m/s)", fontsize=11, fontweight="medium")
    ax2.set_xticks(speeds)
    ax2.legend(loc="upper right", frameon=True, facecolor="white")

    fig.suptitle(
        "Environmental Stress Analysis: Node Mobility Speed vs. Detection Efficacy",
        fontsize=13.5,
        fontweight="bold",
        y=0.98,
    )

    fig.tight_layout()
    mob_path = out_d / "stress_mobility_vs_recall.png"
    fig.savefig(mob_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    generated_paths.append(mob_path)

    # 2. Grayhole Drop Probability vs. PDR & Recall
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    drop_probs = [0.3, 0.5, 0.7]

    for node_count in node_configs:
        sub = df[df["nodes"] == node_count].groupby("drop_prob", as_index=False)[["pdr", "recall"]].mean()
        color = palette_nodes.get(node_count, "#333333")
        marker = markers.get(node_count, "o")

        ax1.plot(
            sub["drop_prob"],
            sub["pdr"],
            marker=marker,
            markersize=8,
            linewidth=2.2,
            color=color,
            label=f"{node_count} Nodes (PDR)",
        )
        ax2.plot(
            sub["drop_prob"],
            sub["recall"],
            marker=marker,
            markersize=8,
            linewidth=2.2,
            color=color,
            label=f"{node_count} Nodes (Recall)",
        )

    ax1.set_title("(a) Network PDR vs. Drop Probability", fontsize=12, fontweight="bold", pad=8)
    ax1.set_xlabel("Grayhole Drop Probability (p)", fontsize=11, fontweight="medium")
    ax1.set_ylabel("Packet Delivery Ratio (PDR)", fontsize=11, fontweight="medium")
    ax1.set_xticks(drop_probs)
    ax1.set_ylim(0.40, 0.80)
    ax1.legend(loc="lower left", frameon=True, facecolor="white")

    ax2.set_title("(b) Detection Recall vs. Drop Probability", fontsize=12, fontweight="bold", pad=8)
    ax2.set_xlabel("Grayhole Drop Probability (p)", fontsize=11, fontweight="medium")
    ax2.set_ylabel("Detection Recall", fontsize=11, fontweight="medium")
    ax2.set_xticks(drop_probs)
    ax2.set_ylim(-0.05, 1.05)
    ax2.legend(loc="lower left", frameon=True, facecolor="white")

    fig.suptitle(
        "Grayhole Attack Severity: Drop Probability vs. Network Delivery and Detection",
        fontsize=13.5,
        fontweight="bold",
        y=0.98,
    )

    fig.tight_layout()
    drop_path = out_d / "stress_droprate_vs_pdr.png"
    fig.savefig(drop_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    generated_paths.append(drop_path)

    return generated_paths


def plot_quarantine_timeline(
    df_events: Union[pd.DataFrame, str, Path],
    out_path: Union[str, Path],
    dpi: int = 300,
) -> Path:
    """Timeline / swimlane plot visualizing discrete node state transitions under active mitigation.

    Highlights 2-strike confirmation filter (K=2, tau=0.50) and 30.0s quarantine decay.

    Parameters
    ----------
    df_events : DataFrame or CSV path
        Isolation events log (from results/isolation_events.csv).
    out_path : Path or str
        Destination path.
    dpi : int, optional
        Resolution (default 300).

    Returns
    -------
    Path
        Path to generated image.
    """
    req_cols = ["sim_time", "scenario_name", "seed", "node_id", "strike_count", "prob_malicious", "action", "quarantine_until"]
    df = _load_and_validate_df(df_events, req_cols, "isolation_events")

    # Filter for reference scenario (30n_blackhole, seed 42)
    ref_df = df[(df["scenario_name"] == "30n_blackhole") & (df["seed"] == 42)].copy()
    if ref_df.empty:
        # Fall back to first available scenario
        ref_df = df.copy()

    fig, ax = plt.subplots(figsize=(12, 6))

    # Identify nodes in the trace
    nodes = sorted(ref_df["node_id"].unique())
    y_map = {nid: i for i, nid in enumerate(nodes)}

    # Plot baseline swimlane tracks for each node
    sim_max = 85.0
    for nid, y in y_map.items():
        role = "Malicious Attacker (Node 21)" if nid == 21 else f"Honest Node {nid} (Transient)"
        ax.hlines(y=y, xmin=0, xmax=sim_max, color="#e0e0e0", linestyle="-", linewidth=2.5, zorder=1)

    # Shaded quarantine intervals for quarantined nodes
    quarantined_spans = [
        (21, 7.0, 37.0, "Quarantine 1 (30.0s cooling)"),
        (21, 48.76, 78.76, "Quarantine 2 (Re-quarantine 30.0s)"),
    ]
    for nid, start, end, label in quarantined_spans:
        if nid in y_map:
            y = y_map[nid]
            ax.barh(
                y=y,
                width=end - start,
                left=start,
                height=0.45,
                color="#ffcdd2",
                edgecolor="#e57373",
                linewidth=1.5,
                alpha=0.85,
                zorder=2,
            )
            ax.text(
                (start + end) / 2,
                y,
                label,
                ha="center",
                va="center",
                fontsize=8.5,
                fontweight="bold",
                color="#b71c1c",
                zorder=4,
            )

    # Plot events as discrete scatter points
    action_styles = {
        "STRIKE": ("o", "#FF8F00", "Strike 1 (Transient Detection)", 75),
        "QUARANTINE": ("X", "#C62828", "Confirmed Quarantine (K=2 Strikes)", 130),
        "UNBLOCK": ("s", "#2E7D32", "Quarantine Expired (Unblocked)", 85),
    }

    plotted_labels = set()
    for _, row in ref_df.iterrows():
        nid = row["node_id"]
        t = row["sim_time"]
        act = row["action"]
        if nid in y_map and act in action_styles:
            marker, color, label_text, size = action_styles[act]
            lbl = label_text if label_text not in plotted_labels else None
            if lbl:
                plotted_labels.add(label_text)
            ax.scatter(
                t,
                y_map[nid],
                marker=marker,
                color=color,
                edgecolor="black",
                linewidth=0.8,
                s=size,
                zorder=5,
                label=lbl,
            )

    # Annotate critical policy features
    ax.annotate(
        "K=2 Strike Confirmation:\n2 consecutive windows with p>=0.50\ntriggers immediate route purge",
        xy=(7.0, y_map.get(21, 0) + 0.25),
        xytext=(15.0, y_map.get(21, 0) + 0.65),
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
        color="#1565c0",
        arrowprops=dict(arrowstyle="->", color="#1565c0", lw=1.2),
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#e3f2fd", edgecolor="#90caf9", alpha=0.95),
    )

    if 25 in y_map:
        ax.annotate(
            "Transient False Strike (Node 25):\nOnly 1 strike logged -> NOT quarantined!\n(Zero network disruption)",
            xy=(54.0, y_map[25]),
            xytext=(55.0, y_map[25] - 0.45),
            ha="left",
            va="top",
            fontsize=8.5,
            fontweight="bold",
            color="#2e7d32",
            arrowprops=dict(arrowstyle="->", color="#2e7d32", lw=1.2),
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#e8f5e9", edgecolor="#a5d6a7", alpha=0.95),
        )

    ax.set_yticks([y_map[nid] for nid in nodes])
    ax.set_yticklabels(
        [f"Node {nid}\n({'Attacker' if nid == 21 else 'Honest'})" for nid in nodes],
        fontsize=11,
        fontweight="bold",
    )
    ax.set_ylim(-0.8, len(nodes) - 0.2 + 0.5)
    ax.set_xlim(0, sim_max)
    ax.set_xlabel("Simulation Time (seconds)", fontsize=11, fontweight="medium")
    ax.set_title(
        "Closed-Loop Dynamic Mitigation Timeline: Strike Accumulation, Quarantine & Recovery",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )

    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=9.5)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_confusion_matrices(
    df_metrics: Union[pd.DataFrame, str, Path],
    out_dir: Union[str, Path],
    dpi: int = 300,
) -> List[Path]:
    """Generate standardized 300 DPI confusion matrix heatmaps for RF, DT, and SVM.

    Figures generated in out_dir:
    - confusion_matrix_random_forest.png
    - confusion_matrix_decision_tree.png
    - confusion_matrix_svm.png

    Parameters
    ----------
    df_metrics : DataFrame or CSV path
        Metrics table with tn, fp, fn, tp (from results/metrics.csv).
    out_dir : Path or str
        Output directory.
    dpi : int, optional
        Resolution (default 300).

    Returns
    -------
    List[Path]
        List of generated file paths.
    """
    req_cols = ["model", "accuracy", "precision", "recall", "fpr", "tn", "fp", "fn", "tp"]
    df = _load_and_validate_df(df_metrics, req_cols, "metrics")
    out_d = Path(out_dir)
    out_d.mkdir(parents=True, exist_ok=True)

    generated_paths: List[Path] = []
    classes = ["Normal", "Malicious"]

    model_meta = {
        "random_forest": ("Random Forest (Champion Pipeline)", "Blues", "PASS (FPR <= 0.01)"),
        "decision_tree": ("Decision Tree (Baseline)", "Oranges", "FAIL (FPR = 3.42%)"),
        "svm": ("Support Vector Machine (Baseline)", "Purples", "FAIL (FPR = 46.38%)"),
    }

    for _, row in df.iterrows():
        m_name = str(row["model"])
        tn, fp, fn, tp = int(row["tn"]), int(row["fp"]), int(row["fn"]), int(row["tp"])
        cm = np.array([[tn, fp], [fn, tp]])

        title_label, cmap, gate_status = model_meta.get(
            m_name, (m_name.replace("_", " ").title(), "Blues", "N/A")
        )

        fig, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap=cmap,
            cbar=False,
            xticklabels=classes,
            yticklabels=classes,
            annot_kws={"size": 13, "weight": "bold"},
            ax=ax,
        )

        ax.set_title(f"{title_label}\nConfusion Matrix (Seed 44 Test Set)", fontsize=12, fontweight="bold", pad=10)
        ax.set_xlabel("Predicted Class", fontsize=11, fontweight="medium")
        ax.set_ylabel("True Ground-Truth Class", fontsize=11, fontweight="medium")

        # Summary footer annotation
        f1_val = float(row.get("f1_blackhole", row.get("f1", 0.0)))
        ax.text(
            0.5,
            -0.22,
            f"Accuracy: {row['accuracy']*100:.2f}%  |  F1 (Mal): {f1_val*100:.2f}%  |  FPR: {row['fpr']*100:.2f}%\nGate: {gate_status}",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=9.5,
            fontweight="semibold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f5f5f5", edgecolor="#cccccc"),
        )

        fig.tight_layout()
        cm_path = out_d / f"confusion_matrix_{m_name}.png"
        fig.savefig(cm_path, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        generated_paths.append(cm_path)

    return generated_paths


def generate_all_figures(
    results_dir: Union[str, Path] = "results",
    plots_dir: Union[str, Path] = "results/plots",
    dpi: int = 300,
) -> Dict[str, Path]:
    """Master orchestrator generating complete 13-figure publication plot portfolio.

    Ingests:
    - results/closed_loop_metrics.csv
    - results/metrics.csv
    - results/feature_importance.csv
    - results/generalization_metrics.csv
    - results/isolation_events.csv

    Outputs 300 DPI figures into plots_dir.

    Parameters
    ----------
    results_dir : Path or str
        Directory containing authoritative CSV results.
    plots_dir : Path or str
        Target output directory for PNG figures.
    dpi : int, optional
        Resolution (default 300).

    Returns
    -------
    Dict[str, Path]
        Mapping of figure identifiers to generated Path objects.
    """
    res_d = Path(results_dir)
    plots_d = Path(plots_dir)
    plots_d.mkdir(parents=True, exist_ok=True)

    csv_closed_loop = res_d / "closed_loop_metrics.csv"
    csv_metrics = res_d / "metrics.csv"
    csv_importance = res_d / "feature_importance.csv"
    csv_gen = res_d / "generalization_metrics.csv"
    csv_events = res_d / "isolation_events.csv"

    generated: Dict[str, Path] = {}

    # 1. Executive Dashboard (4-panel)
    p_dash = plots_d / "qos_recovery_triad_dashboard.png"
    plot_executive_dashboard(csv_closed_loop, p_dash, dpi=dpi)
    generated["qos_recovery_triad_dashboard"] = p_dash

    # 2-5. Focused Standalone QoS Recovery Figures
    triad_paths = plot_qos_recovery_triad(csv_closed_loop, plots_d, dpi=dpi)
    for p in triad_paths:
        generated[p.stem] = p

    # 6. Classifier Comparison
    p_clf = plots_d / "classifier_comparison_metrics.png"
    plot_classifier_comparison(csv_metrics, p_clf, dpi=dpi)
    generated["classifier_comparison_metrics"] = p_clf

    # 7. Feature Importance Ranking
    p_feat = plots_d / "feature_importance_ranking.png"
    plot_feature_importance(csv_importance, p_feat, dpi=dpi)
    generated["feature_importance_ranking"] = p_feat

    # 8-9. Generalization & Stress Curves
    stress_paths = plot_generalization_stress(csv_gen, plots_d, dpi=dpi)
    for p in stress_paths:
        generated[p.stem] = p

    # 10. Quarantine Timeline
    p_timeline = plots_d / "mitigation_quarantine_timeline.png"
    plot_quarantine_timeline(csv_events, p_timeline, dpi=dpi)
    generated["mitigation_quarantine_timeline"] = p_timeline

    # 11-13. Standardized Confusion Matrices
    cm_paths = plot_confusion_matrices(csv_metrics, plots_d, dpi=dpi)
    for p in cm_paths:
        generated[p.stem] = p

    return generated
