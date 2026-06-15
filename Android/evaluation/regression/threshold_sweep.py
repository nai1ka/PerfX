#!/usr/bin/env python3
"""
E3 — Threshold sensitivity sweep.

Reads the release-pair run CSVs (which contain delta_pct and
ground_truth_regression) and re-derives the detection decision at a range of
thresholds.  No re-querying of the database is needed: we simply compare
delta_pct against each candidate threshold.

Output:
  results/release_pair/summary_e3.csv  — threshold × (TPR, FPR, precision, F1)

Run:
  python3 threshold_sweep.py [--results-dir <path>]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parent / "results"
THRESHOLDS  = np.round(np.arange(0.05, 0.55, 0.05), 2).tolist()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-dir", default=str(RESULTS_DIR))
    ap.add_argument("--thresholds", default="",
                    help="comma-separated float thresholds; default: 0.05…0.50")
    args = ap.parse_args()

    results_dir = Path(args.results_dir)
    thresholds = (
        [float(t) for t in args.thresholds.split(",") if t.strip()]
        if args.thresholds else THRESHOLDS
    )

    csvs = [p for p in results_dir.glob("*.csv")
            if not p.name.startswith("summary_")]
    if not csvs:
        raise FileNotFoundError(f"No run CSVs in {results_dir}")
    df = pd.concat([pd.read_csv(p) for p in csvs], ignore_index=True)
    df = df.dropna(subset=["delta_pct"])
    print(f"Loaded {len(df)} rows.")

    rows = []
    for thr in thresholds:
        would_detect = (df["delta_pct"] / 100.0) > thr
        gt = df["ground_truth_regression"].astype(bool)

        tp = int((would_detect &  gt).sum())
        fp = int((would_detect & ~gt).sum())
        fn = int((~would_detect &  gt).sum())
        tn = int((~would_detect & ~gt).sum())

        tpr  = tp / (tp + fn) if (tp + fn) else float("nan")
        fpr  = fp / (fp + tn) if (fp + tn) else float("nan")
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        f1   = (2 * prec * tpr / (prec + tpr)
                if (not any(x != x for x in [prec, tpr]) and prec + tpr > 0)
                else float("nan"))

        rows.append(dict(threshold=thr, tp=tp, fp=fp, fn=fn, tn=tn,
                         tpr=round(tpr, 4), fpr=round(fpr, 4),
                         precision=round(prec, 4), f1=round(f1, 4)))

    out = results_dir / "summary_e3.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"E3 threshold sweep: {len(rows)} thresholds → {out}")


if __name__ == "__main__":
    main()
