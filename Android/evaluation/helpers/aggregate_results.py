#!/usr/bin/env python3
"""
Aggregates all CSVs from results/release_pair/ into per-experiment-group
summary CSVs consumed by plots.py, tables.py, and the thesis chapter.

Outputs (all written to results/release_pair/):
  summary_e1.csv  — E1 injection detection, one row per (exp_id, device, metric)
  summary_e2.csv  — E2 false-positive control summary

Run:
  python3 aggregate_results.py [--results-dir <path>]
"""

import argparse
import re
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path(__file__).resolve().parent.parent / "regression" / "results"


def load_all(results_dir: Path) -> pd.DataFrame:
    csvs = [p for p in results_dir.glob("*.csv")
            if not p.name.startswith("summary_")]
    if not csvs:
        raise FileNotFoundError(f"No run CSVs found in {results_dir}")
    frames = [pd.read_csv(p) for p in csvs]
    df = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(df)} rows from {len(csvs)} CSV(s).")
    return df


def compute_outcome(row) -> str:
    gt = bool(row["ground_truth_regression"])
    det = bool(row["detected"])
    if gt and det:
        return "TP"
    if gt and not det:
        return "FN"
    if not gt and det:
        return "FP"
    return "TN"


def run(results_dir: Path = RESULTS_DIR) -> None:
    """Aggregate all run CSVs in *results_dir* and write summary_e*.csv files.

    Importable by run_release_pair_experiments.py so the caller does not have
    to shell out.  Also called by main() for standalone use.
    """
    df = load_all(results_dir)
    df["outcome"] = df.apply(compute_outcome, axis=1)

    # ── E1: injection detection ───────────────────────────────────────────────
    e1 = df[df["experiment_id"].str.startswith("e1_")].copy()
    if not e1.empty:
        e1_summary = (
            e1.groupby(["experiment_id", "device", "cohort",
                        "metric_id", "regression_type", "intensity"])
            .agg(
                baseline_p95=("baseline_p95", "mean"),
                current_p95=("current_p95", "mean"),
                delta_pct=("delta_pct", "mean"),
                detected_rate=("detected", "mean"),
                tp=("outcome", lambda x: (x == "TP").sum()),
                fn=("outcome", lambda x: (x == "FN").sum()),
                n_runs=("outcome", "count"),
            )
            .round(3)
            .reset_index()
        )
        out = results_dir / "summary_e1.csv"
        e1_summary.to_csv(out, index=False)
        print(f"E1: {len(e1_summary)} rows → {out}")

    # ── E2: false positives ───────────────────────────────────────────────────
    e2 = df[df["experiment_id"].str.startswith("e2_")].copy()
    if not e2.empty:
        e2_summary = (
            e2.groupby(["device", "cohort"])
            .agg(
                n_runs=("outcome", "count"),
                false_positives=("detected", "sum"),
                fp_rate=("detected", "mean"),
                mean_delta_pct=("delta_pct", "mean"),
                std_delta_pct=("delta_pct", "std"),
            )
            .round(4)
            .reset_index()
        )
        out = results_dir / "summary_e2.csv"
        e2_summary.to_csv(out, index=False)
        print(f"E2: {len(e2_summary)} rows → {out}")

    print("Aggregation done.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results-dir", default=str(RESULTS_DIR),
                    help="directory containing run CSVs")
    args = ap.parse_args()
    run(Path(args.results_dir))


if __name__ == "__main__":
    main()
