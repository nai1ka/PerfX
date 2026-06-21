#!/usr/bin/env python3
"""
Offline P95 recompute for the thesis evaluation.

The release-pair runs were originally aggregated with the MEDIAN, but the
detector and the thesis use the P95 relative shift. The raw per-version sample
arrays are saved in results/comparison_data/*.npz (keys: baseline, regression),
so the P95 shift can be recomputed offline with no device re-run.

Outputs:
  results/summary_e1_p95.csv  — per injected cell: baseline/current P95, delta, detected
  results/summary_e3_p95.csv  — threshold sweep (TPR/FPR) from P95 deltas
and prints both tables.
"""
import glob
import os
import csv
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CD = os.path.join(HERE, "results", "comparison_data")
OUT = os.path.join(HERE, "results")
THRESHOLD = 0.15
SWEEP = [round(t, 2) for t in np.arange(0.05, 0.55, 0.05)]


def p95(a):
    return float(np.percentile(np.asarray(a, dtype=float), 95))


def load(path):
    d = np.load(path, allow_pickle=True)
    base, cur = p95(d["baseline"]), p95(d["regression"])
    delta = (cur - base) / base * 100 if base > 0 else float("nan")
    name = os.path.basename(path).replace(".npz", "")
    exp, dev = name.split("__")
    cohort = dev.replace("PerfX_", "")
    return dict(exp=exp, cohort=cohort, metric=str(d["metric_id"]),
                base=base, cur=cur, delta=delta)


def main():
    e1 = [load(p) for p in sorted(glob.glob(os.path.join(CD, "e1_*.npz")))]
    e2 = [load(p) for p in sorted(glob.glob(os.path.join(CD, "e2_*.npz")))]

    # ---- per-cell injected table ----
    with open(os.path.join(OUT, "summary_e1_p95.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["exp", "cohort", "metric", "baseline_p95", "current_p95",
                    "delta_pct", "detected"])
        for r in e1:
            det = r["delta"] / 100 > THRESHOLD
            w.writerow([r["exp"], r["cohort"], r["metric"],
                        round(r["base"], 3), round(r["cur"], 3),
                        round(r["delta"], 2), det])

    print(f"{'cell':26s} {'metric':12s} {'baseP95':>9s} {'curP95':>9s} {'Δ%':>9s}  det")
    for r in e1:
        det = "Yes" if r["delta"] / 100 > THRESHOLD else "No"
        print(f"{r['exp']:26s} {r['metric']:12s} {r['base']:9.2f} {r['cur']:9.2f} "
              f"{r['delta']:9.1f}  {det}")

    # ---- threshold sweep ----
    inj = np.array([r["delta"] / 100 for r in e1])
    ctl = np.array([r["delta"] / 100 for r in e2])
    print(f"\ninjected cells={len(inj)}  control cells={len(ctl)}")
    print(f"\n{'thr':>5s} {'TPR':>6s} {'FPR':>6s}  tp/inj  fp/ctl")
    with open(os.path.join(OUT, "summary_e3_p95.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["threshold", "tpr", "fpr", "tp", "n_inj", "fp", "n_ctl"])
        for t in SWEEP:
            tp = int((inj > t).sum()); fp = int((ctl > t).sum())
            tpr = tp / len(inj); fpr = fp / len(ctl)
            w.writerow([t, round(tpr, 3), round(fpr, 3), tp, len(inj), fp, len(ctl)])
            print(f"{t:5.2f} {tpr:6.2f} {fpr:6.2f}  {tp:2d}/{len(inj)}   {fp:2d}/{len(ctl)}")


if __name__ == "__main__":
    main()
