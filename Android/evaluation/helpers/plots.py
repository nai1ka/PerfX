#!/usr/bin/env python3
"""
Generates all evaluation plots for Chapter 5 of the thesis.

Reads summary CSVs from results/release_pair/ (produced by aggregate_results.py,
threshold_sweep.py, and sample_size_sweep.py) and writes figures to
analysis/figs/.

Run:
  python3 plots.py [--results-dir <path>] [--figs-dir <path>]
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parent.parent / "regression" / "results"
FIGS_DIR    = Path(__file__).resolve().parent.parent / "regression" / "figs"

METRIC_LABELS = {
    "cpuUsage":     "CPU usage (%)",
    "memoryUsage":  "RAM usage (MB)",
    "frameTime":    "Frame time (ms)",
}
COHORT_ORDER  = ["Low", "Medium", "High"]
INTENSITY_LABELS = {1: "Low", 2: "Medium", 3: "High"}


def load(results_dir: Path, name: str) -> pd.DataFrame | None:
    p = results_dir / name
    if not p.exists():
        print(f"  [skip] {name} not found")
        return None
    return pd.read_csv(p)


# ── E1: detection rate bar chart ──────────────────────────────────────────────

def plot_e1_detection_rate(df: pd.DataFrame, figs_dir: Path) -> None:
    metrics = df["metric_id"].unique()
    n_metrics = len(metrics)
    fig, axes = plt.subplots(1, n_metrics, figsize=(4 * n_metrics, 4), sharey=True)
    if n_metrics == 1:
        axes = [axes]

    for ax, metric in zip(axes, metrics):
        sub = df[df["metric_id"] == metric]
        intensities = sorted(sub["intensity"].unique())
        x = np.arange(len(intensities))
        width = 0.25
        for j, cohort in enumerate(COHORT_ORDER):
            c_sub = sub[sub["cohort"] == cohort]
            rates = [
                float(c_sub[c_sub["intensity"] == i]["detected_rate"].mean())
                if not c_sub[c_sub["intensity"] == i].empty else 0.0
                for i in intensities
            ]
            ax.bar(x + j * width, rates, width, label=cohort)
        ax.set_xticks(x + width)
        ax.set_xticklabels([INTENSITY_LABELS.get(i, str(i)) for i in intensities])
        ax.set_xlabel("Injection intensity")
        ax.set_title(METRIC_LABELS.get(metric, metric))
        ax.set_ylim(0, 1.1)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=1))

    axes[0].set_ylabel("Detection rate")
    axes[-1].legend(title="Cohort")
    fig.suptitle("E1 — Detection rate by metric and intensity")
    plt.tight_layout()
    out = figs_dir / "e1_detection_rate.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  → {out}")


# ── E1: delta_pct heat map ────────────────────────────────────────────────────

def plot_e1_delta_heatmap(df: pd.DataFrame, figs_dir: Path) -> None:
    pivot = (df.groupby(["metric_id", "intensity"])["delta_pct"]
               .mean()
               .unstack("intensity"))
    fig, ax = plt.subplots(figsize=(6, 3))
    im = ax.imshow(pivot.values, aspect="auto", cmap="RdYlGn_r")
    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels([INTENSITY_LABELS.get(c, str(c)) for c in pivot.columns])
    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels([METRIC_LABELS.get(m, m) for m in pivot.index])
    ax.set_xlabel("Injection intensity")
    ax.set_title("E1 — Mean Δ% (P95 shift) per metric × intensity")
    plt.colorbar(im, ax=ax, label="Δ%")
    plt.tight_layout()
    out = figs_dir / "e1_delta_heatmap.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  → {out}")


# ── E3: threshold sensitivity curve ──────────────────────────────────────────

def plot_e3_threshold_sweep(df: pd.DataFrame, figs_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(df["threshold"], df["tpr"],       marker=".", label="TPR (recall)")
    ax.plot(df["threshold"], df["fpr"],       marker=".", label="FPR")
    ax.plot(df["threshold"], df["precision"], marker=".", label="Precision")
    ax.plot(df["threshold"], df["f1"],        marker=".", label="F1")
    ax.axvline(0.15, color="grey", linestyle="--", linewidth=0.8, label="default 15%")
    ax.set_xlabel("Threshold")
    ax.set_ylabel("Score")
    ax.set_title("E3 — Detector quality vs regression threshold")
    ax.legend()
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1.05)
    plt.tight_layout()
    out = figs_dir / "e3_threshold_sweep.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  → {out}")


# ── E4: cohort consistency ────────────────────────────────────────────────────

def plot_e4_cohort_consistency(df: pd.DataFrame, figs_dir: Path) -> None:
    sub = df[(df["regression_type"] == "cpu") & (df["intensity"] == 2)]
    if sub.empty:
        print("  [skip] no cpu/intensity=2 rows for E4 cohort consistency plot")
        return

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))

    # Absolute delta
    cohorts = [c for c in COHORT_ORDER if c in sub["cohort"].values]
    abs_vals = [float(sub[sub["cohort"] == c]["delta_pct"].mean()) for c in cohorts]
    axes[0].bar(cohorts, abs_vals)
    axes[0].set_ylabel("Mean Δ% (absolute)")
    axes[0].set_title("Absolute P95 shift")

    # Relative delta normalised to cohort median baseline
    # proxy: delta_pct / baseline_p95 * 100 gives a rough normalised shift
    sub = sub.copy()
    sub["rel_shift"] = sub["delta_pct"] / sub["baseline_p95"].replace(0, float("nan"))
    rel_vals = [float(sub[sub["cohort"] == c]["rel_shift"].mean()) for c in cohorts]
    axes[1].bar(cohorts, rel_vals)
    axes[1].set_ylabel("Δ% / baseline P95")
    axes[1].set_title("Relative P95 shift")

    fig.suptitle("E4 — CPU medium injection: cohort consistency")
    plt.tight_layout()
    out = figs_dir / "e4_cohort_consistency.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  → {out}")


def run(results_dir: Path = RESULTS_DIR, figs_dir: Path = FIGS_DIR) -> None:
    """Render all available summary CSVs to PDF figures in *figs_dir*.

    Importable by run_release_pair_experiments.py.  Also called by main() for
    standalone use.  Missing summary files are silently skipped.
    """
    figs_dir.mkdir(parents=True, exist_ok=True)
    print("Generating summary plots...")

    e1 = load(results_dir, "summary_e1.csv")
    if e1 is not None:
        plot_e1_detection_rate(e1, figs_dir)
        plot_e1_delta_heatmap(e1, figs_dir)
        plot_e4_cohort_consistency(e1, figs_dir)

    e3 = load(results_dir, "summary_e3.csv")
    if e3 is not None:
        plot_e3_threshold_sweep(e3, figs_dir)

    print("Summary plots done.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-dir", default=str(RESULTS_DIR))
    ap.add_argument("--figs-dir",    default=str(FIGS_DIR))
    args = ap.parse_args()
    run(Path(args.results_dir), Path(args.figs_dir))


if __name__ == "__main__":
    main()
