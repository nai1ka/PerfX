#!/usr/bin/env python3
"""
End-to-end regression-detection driver for the thesis evaluation (Chapter 5, Part 3).

For each cell of an experiment matrix it:
  1. force-stops and launches the PerfX demo app in *experiment mode* via adb
     intent extras (regression_type / intensity / baseline_secs / current_secs);
  2. the app idles for the baseline window, then enables the synthetic regression;
  3. after the windows elapse (plus an SDK-flush margin), it queries ClickHouse for
     the raw metric samples in the baseline and current windows;
  4. it runs the real detection logic (`validate_regression` from the regression
     detector) and records the outcome.

It also sweeps the current window to estimate detection latency, and runs control
experiments (no regression) to measure the false-positive rate.

Output: results/regression/runs.csv  — one row per run.

Prerequisites:
  - Backend stack up (ClickHouse reachable), demo app endpoint reachable.
  - A device/emulator connected via adb (set --serial or ANDROID_SERIAL).
  - The demo app installed:  ./gradlew :demo:installWithSdkDebug
  - Python deps: clickhouse_connect, scipy, numpy  (Analysis/requirements.txt).

Usage:
  python3 run_regression_experiments.py --project-id <uuid> [options]
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

# ── make the regression detector importable ───────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "Analysis"))

import clickhouse_connect  # noqa: E402
from regression_detection.config import (  # noqa: E402
    CH_HOST, CH_PORT, CH_USER, CH_PASSWORD, CH_DATABASE,
    DEFAULT_P95_THRESHOLD, MIN_SAMPLES,
)
from regression_detection.detector import validate_regression  # noqa: E402

PACKAGE = "com.ndevelop.perfx"
ACTIVITY = f"{PACKAGE}/.ui.MainActivity"

# regression_type -> (clickhouse metric_id, screen_name as tracked by the SDK)
METRIC_OF = {
    "cpu":     ("cpuUsage",     "compose/cpu_load"),
    "memory":  ("memoryUsage",  "compose/ram_load"),
    "ui":      ("frameTime",    "compose/ui_responsiveness"),
    "control": ("cpuUsage",     "compose/cpu_load"),  # control idles on the cpu screen
}

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "regression"

# Margins (seconds): skip app-startup noise, let the regression ramp, let the SDK flush.
WARMUP_SECS = 10
SETTLE_SECS = 10
FLUSH_MARGIN_SECS = 10


def adb(args, serial=None, capture=True):
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd += args
    return subprocess.run(cmd, capture_output=capture, text=True, check=True)


def build_and_install(serial=None):
    """Build and install the withSdk demo-app flavor (needed so the SDK runs)."""
    gradle_dir = REPO_ROOT / "Android" / "PerfX"
    env = dict(os.environ)
    if serial:
        env["ANDROID_SERIAL"] = serial
    print("=== Building + installing :demo withSdk flavor ===")
    subprocess.run(
        ["./gradlew", ":demo:installWithSdkDebug"],
        cwd=gradle_dir, env=env, check=True,
    )


def device_epoch(serial=None) -> int:
    """Current device wall-clock epoch (seconds). SDK metric timestamps use the
    device clock, so windows must be expressed against it, not the host clock."""
    return int(adb(["shell", "date", "+%s"], serial).stdout.strip())


def launch_experiment(reg_type, intensity, baseline, current, serial=None):
    adb(["shell", "am", "force-stop", PACKAGE], serial)
    time.sleep(1)
    adb([
        "shell", "am", "start", "-n", ACTIVITY,
        "--es", "regression_type", reg_type,
        "--ei", "intensity", str(intensity),
        "--ei", "baseline_secs", str(baseline),
        "--ei", "current_secs", str(current),
    ], serial)


def fetch_samples(ch, project_id, metric_id, screen_name, start_epoch, end_epoch):
    rows = ch.query(
        """
        SELECT value FROM metric_records
        WHERE project_id = {pid:String}
          AND metric_id = {mid:String}
          AND screen_name = {screen:String}
          AND ts >= toDateTime({start:Int64})
          AND ts <  toDateTime({end:Int64})
        ORDER BY ts
        """,
        parameters={
            "pid": project_id, "mid": metric_id, "screen": screen_name,
            "start": start_epoch, "end": end_epoch,
        },
    ).result_rows
    return [float(r[0]) for r in rows]


def evaluate(baseline_vals, current_vals, threshold):
    """P95 shift + Mann-Whitney U, returning the per-run record fields."""
    if not baseline_vals or not current_vals:
        return dict(baseline_p95=None, current_p95=None, degradation_pct=None,
                    p_value=None, candidate=False, confirmed=False,
                    note="no samples")
    b_p95 = float(np.percentile(baseline_vals, 95))
    c_p95 = float(np.percentile(current_vals, 95))
    degradation = (c_p95 - b_p95) / b_p95 if b_p95 > 0 else 0.0
    confirmed, p_value = validate_regression(
        baseline_vals, current_vals, b_p95, c_p95, threshold,
    )
    note = ""
    if (len(baseline_vals) < MIN_SAMPLES or len(current_vals) < MIN_SAMPLES):
        note = f"few samples (b={len(baseline_vals)}, c={len(current_vals)})"
    return dict(
        baseline_p95=round(b_p95, 3),
        current_p95=round(c_p95, 3),
        degradation_pct=round(degradation * 100, 2),
        p_value=None if p_value is None else round(float(p_value), 6),
        candidate=degradation > threshold,
        confirmed=bool(confirmed),
        note=note,
    )


def detection_latency(ch, project_id, metric_id, screen_name,
                      baseline_start, baseline_end, onset, current_end,
                      threshold, step=15):
    """Smallest current-window length (s) at which the regression is first
    confirmed. Reuses already-collected data — no extra device runtime."""
    baseline = fetch_samples(ch, project_id, metric_id, screen_name,
                             baseline_start, baseline_end)
    for cut in range(step, (current_end - onset) + 1, step):
        current = fetch_samples(ch, project_id, metric_id, screen_name,
                                onset, onset + cut)
        res = evaluate(baseline, current, threshold)
        if res["confirmed"]:
            return cut
    return None


def run_cell(ch, project_id, reg_type, intensity, baseline, current,
             threshold, serial):
    metric_id, screen_name = METRIC_OF[reg_type]
    print(f"\n=== {reg_type} intensity={intensity} "
          f"(baseline={baseline}s current={current}s) ===")

    launch = device_epoch(serial)
    launch_experiment(reg_type, intensity, baseline, current, serial)

    total = baseline + current + FLUSH_MARGIN_SECS
    print(f"  running {total}s (incl. {FLUSH_MARGIN_SECS}s flush margin)...")
    time.sleep(total)
    adb(["shell", "am", "force-stop", PACKAGE], serial)

    baseline_start = launch + WARMUP_SECS
    baseline_end = launch + baseline
    onset = baseline_end                     # regression enabled here
    current_start = onset + SETTLE_SECS
    current_end = onset + current

    baseline_vals = fetch_samples(ch, project_id, metric_id, screen_name,
                                  baseline_start, baseline_end)
    current_vals = fetch_samples(ch, project_id, metric_id, screen_name,
                                 current_start, current_end)
    res = evaluate(baseline_vals, current_vals, threshold)

    latency = None
    if reg_type != "control" and res["confirmed"]:
        latency = detection_latency(
            ch, project_id, metric_id, screen_name,
            baseline_start, baseline_end, onset, current_end, threshold,
        )

    expected = reg_type != "control"
    confirmed = res["confirmed"]
    outcome = ("TP" if expected and confirmed else
               "FN" if expected and not confirmed else
               "FP" if not expected and confirmed else "TN")

    row = dict(
        regression_type=reg_type, intensity=intensity, metric_id=metric_id,
        screen_name=screen_name, baseline_secs=baseline, current_secs=current,
        baseline_samples=len(baseline_vals), current_samples=len(current_vals),
        expected_regression=expected, outcome=outcome,
        detection_latency_secs=latency, **res,
    )
    print(f"  baseline_p95={res['baseline_p95']} current_p95={res['current_p95']} "
          f"degradation={res['degradation_pct']}% p={res['p_value']} "
          f"-> {outcome}" + (f" latency={latency}s" if latency else ""))
    if res["note"]:
        print(f"  note: {res['note']}")
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-id", required=True,
                    help="project_id the demo app reports under")
    ap.add_argument("--serial", default=os.environ.get("ANDROID_SERIAL"),
                    help="adb device serial (default: ANDROID_SERIAL env)")
    ap.add_argument("--build", action="store_true",
                    help="build + install the withSdk demo app flavor first")
    ap.add_argument("--types", default="cpu,memory,ui",
                    help="comma-separated regression types to test")
    ap.add_argument("--intensities", default="1,2,3",
                    help="comma-separated intensity levels (1=low,2=med,3=high)")
    ap.add_argument("--reps", type=int, default=1,
                    help="repetitions per (type,intensity) cell")
    ap.add_argument("--controls", type=int, default=3,
                    help="number of control runs (no regression)")
    ap.add_argument("--baseline", type=int, default=90,
                    help="baseline window length, seconds")
    ap.add_argument("--current", type=int, default=90,
                    help="current window length, seconds")
    ap.add_argument("--threshold", type=float, default=DEFAULT_P95_THRESHOLD,
                    help="relative P95 degradation threshold")
    ap.add_argument("--out", default=str(RESULTS_DIR / "runs.csv"),
                    help="output CSV path")
    args = ap.parse_args()

    if args.build:
        build_and_install(args.serial)

    ch = clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT, username=CH_USER,
        password=CH_PASSWORD, database=CH_DATABASE,
    )

    types = [t.strip() for t in args.types.split(",") if t.strip()]
    intensities = [int(i) for i in args.intensities.split(",") if i.strip()]

    rows = []
    for reg_type in types:
        for intensity in intensities:
            for _ in range(args.reps):
                rows.append(run_cell(ch, args.project_id, reg_type, intensity,
                                     args.baseline, args.current,
                                     args.threshold, args.serial))
    for _ in range(args.controls):
        rows.append(run_cell(ch, args.project_id, "control", 0,
                             args.baseline, args.current,
                             args.threshold, args.serial))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "regression_type", "intensity", "metric_id", "screen_name",
        "baseline_secs", "current_secs", "baseline_samples", "current_samples",
        "baseline_p95", "current_p95", "degradation_pct", "p_value",
        "candidate", "confirmed", "expected_regression", "outcome",
        "detection_latency_secs", "note",
    ]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    n = len(rows)
    tp = sum(r["outcome"] == "TP" for r in rows)
    fp = sum(r["outcome"] == "FP" for r in rows)
    fn = sum(r["outcome"] == "FN" for r in rows)
    tn = sum(r["outcome"] == "TN" for r in rows)
    print(f"\n=== Done: {n} runs -> {out_path} ===")
    print(f"  TP={tp}  FP={fp}  FN={fn}  TN={tn}")
    print("  Open regression_analysis.ipynb to aggregate the metrics.")


if __name__ == "__main__":
    main()
