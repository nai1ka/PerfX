#!/usr/bin/env python3
"""
Plot the signal-vs-noise separation from the E10 runs.

Reads the driver's result CSVs, takes the relative P95 shift of every
e10_noise_* run (no code change) and every e10_signal_* run (regression), and
draws them on one axis with the 15% threshold between. Writes figs/separation.png.

Usage:
  python3 separation_plot.py
  python3 separation_plot.py --results-dir results --threshold 15
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default=os.path.join(HERE, "results"))
    ap.add_argument("--threshold", type=float, default=15.0)
    args = ap.parse_args()

    csvs = [p for p in glob.glob(os.path.join(args.results_dir, "*.csv"))
            if not os.path.basename(p).startswith("summary_")]
    df = pd.concat([pd.read_csv(p) for p in csvs], ignore_index=True)
    df = df.dropna(subset=["delta_pct"])
    df["experiment_id"] = df["experiment_id"].astype(str)

    noise = df[df["experiment_id"].str.startswith("e10_noise")]["delta_pct"].astype(float).values
    signal = df[df["experiment_id"].str.startswith("e10_signal")]["delta_pct"].astype(float).values
    if len(noise) == 0 or len(signal) == 0:
        raise SystemExit(f"need both groups; got noise={len(noise)} signal={len(signal)}")

    thr = args.threshold
    ylo = min(float(noise.min()), -5.0)
    top = max(float(signal.max()), thr) * 1.18

    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(6.2, 5.2))

    ax.axhspan(ylo, thr, color="#4caf7d", alpha=0.07)
    ax.axhspan(thr, top, color="crimson", alpha=0.07)
    ax.axhline(thr, ls="--", color="black", lw=1.4)
    ax.text(2.55, thr + (top - ylo) * 0.012, f"{thr:.0f}% threshold",
            ha="right", fontsize=9)

    ax.scatter(rng.normal(1, 0.05, len(noise)), noise, s=95, color="#2e8b57",
               edgecolor="white", zorder=3, label=f"No change  (n={len(noise)})")
    ax.scatter(rng.normal(2, 0.05, len(signal)), signal, s=95, color="crimson",
               edgecolor="white", zorder=3, label=f"Regression  (n={len(signal)})")

    # separation margin
    nmax, smin = float(noise.max()), float(signal.min())
    ax.annotate("", xy=(2.5, smin), xytext=(2.5, nmax),
                arrowprops=dict(arrowstyle="<->", color="grey", lw=1.2))
    ax.text(2.46, (smin + nmax) / 2, f"gap\n{nmax:.0f}% to {smin:.0f}%",
            fontsize=8, color="dimgrey", va="center", ha="right")

    ax.set_xlim(0.5, 2.7)
    ax.set_ylim(ylo, top)
    ax.set_xticks([1, 2])
    ax.set_xticklabels(["No change\n(noise)", "Regression\n(signal)"])
    ax.set_ylabel("Relative P95 shift of frame time (%)")
    ax.set_title("The detector separates a regression from noise")
    ax.legend(loc="upper left", fontsize=9, frameon=True)

    fig.tight_layout()
    out = os.path.join(HERE, "figs", "separation.png")
    fig.savefig(out, dpi=150)

    print(f"noise (no change)  : {np.round(noise, 1)}   max {noise.max():.1f}%")
    print(f"signal (regression): {np.round(signal, 1)}   min {signal.min():.1f}%")
    print("saved", out)


if __name__ == "__main__":
    main()
