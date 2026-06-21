#!/usr/bin/env python3
"""
Three-way overhead comparison chart: noSdk / withSdk (PerfX) / withFirebase.

Reads the per-flavor CSVs and startup logs from
    Android/evaluation/overhead/results/Redmi_Note_9_Pro/
and produces a bar chart with three bars per metric, saved next to the
other overhead PNGs in Thesis/figs/.

Usage:
    python3 overhead_three_way_plot.py [--device Redmi_Note_9_Pro]
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RESULTS = REPO_ROOT / "Android" / "evaluation" / "overhead" / "results"
DEFAULT_FIGS = REPO_ROOT / "Thesis" / "figs"


def load_flavor(results_dir: Path, flavor: str):
    csv = pd.read_csv(results_dir / f"{flavor}.csv")
    csv["pss_mb"] = csv["pss_kb"] / 1024
    csv["java_heap_mb"] = csv["java_heap_kb"] / 1024
    startup = pd.read_csv(results_dir / f"{flavor}_startup.txt").squeeze("columns")
    return csv, startup


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="Redmi_Note_9_Pro")
    parser.add_argument("--results-root", default=str(DEFAULT_RESULTS))
    parser.add_argument("--out", default=str(DEFAULT_FIGS / "overhead_redmi_three_way.png"))
    args = parser.parse_args()

    results_dir = Path(args.results_root) / args.device

    no_sdk_csv, no_sdk_startup = load_flavor(results_dir, "noSdk")
    with_sdk_csv, with_sdk_startup = load_flavor(results_dir, "withSdk")
    with_fb_csv, with_fb_startup = load_flavor(results_dir, "withFirebase")

    labels = ["No SDK", "PerfX", "Firebase"]
    colors = ["steelblue", "darkorange", "#4caf50"]

    metrics = ["CPU (%)", "PSS (MB)", "Cold start (ms)"]
    no_vals = [no_sdk_csv.cpu_pct.mean(), no_sdk_csv.pss_mb.mean(), no_sdk_startup.mean()]
    perfx_vals = [with_sdk_csv.cpu_pct.mean(), with_sdk_csv.pss_mb.mean(), with_sdk_startup.mean()]
    fb_vals = [with_fb_csv.cpu_pct.mean(), with_fb_csv.pss_mb.mean(), with_fb_startup.mean()]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, metric, no_v, perfx_v, fb_v in zip(
        axes, metrics, no_vals, perfx_vals, fb_vals
    ):
        values = [no_v, perfx_v, fb_v]
        bars = ax.bar(labels, values, color=colors, alpha=0.85)
        fmt = "%.0f" if metric.startswith("Cold") else "%.2f"
        ax.bar_label(bars, fmt=fmt, padding=3, fontsize=9)
        ax.set_title(metric)
        ax.set_ylim(0, max(values) * 1.18)

    fig.suptitle(f"Resource Overhead on {args.device}, three-way", fontsize=13)
    fig.tight_layout()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f"Saved: {out}")

    print("\nSummary:")
    print(f"  {'metric':<18} {'noSdk':>10} {'withSdk':>10} {'withFirebase':>14}")
    for metric, no_v, perfx_v, fb_v in zip(metrics, no_vals, perfx_vals, fb_vals):
        print(f"  {metric:<18} {no_v:>10.2f} {perfx_v:>10.2f} {fb_v:>14.2f}")


if __name__ == "__main__":
    main()
