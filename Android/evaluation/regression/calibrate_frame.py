#!/usr/bin/env python3
"""
Calibration harness for the tier-sensitive FRAME regression (experiment e7).

Goal: find a per-frame CPU work size (loop iterations) such that the frame-time
P95 shift stays BELOW the 15% threshold on a high-tier device and ABOVE it on a
low-tier device. Run this once per device, compare the printed tables, and pick a
count that lands in that window. Then put it into frameWorkIterations() in
ExperimentMode.kt (intensity 2) and run e7_frame_tier through the normal driver.

It reuses the main driver's primitives so nothing is duplicated:
  build_apk / install_apk / query_p95 / clear_version_metrics / resolve_serial / adb

How it works:
  - Builds ONE clean APK (no baked regression) at a fixed versionCode.
  - For each candidate iteration count it force-stops, relaunches the app with
    the intent extras  navigate_to=ui_responsiveness  frame_iterations=<N>,
    collects for --secs, then reads the frame-time P95 from ClickHouse.
  - Because the candidate count is passed by intent, no rebuild is needed between
    candidates. The ClickHouse group is wiped before each candidate so the single
    versionCode only ever holds the current candidate's samples.

Usage:
  python3 calibrate_frame.py --project-id <uuid> --device PerfX_High
  python3 calibrate_frame.py --project-id <uuid> --device PerfX_Low \
      --candidates 0,100000,200000,400000,800000 --secs 75

Prerequisites: backend stack up, the target AVD running, the demo app buildable.
"""

import argparse
import sys
import time
from pathlib import Path

# Reuse everything from the main driver in this same directory.
import run_release_pair_experiments as drv

METRIC_ID = "frameTime"
SCREEN_NAME = "compose/ui_responsiveness"
TARGET_SCREEN = "ui_responsiveness"
CAL_VERSION_CODE = 9001


def launch_with_iterations(iterations: int, serial=None) -> None:
    """Force-stop and relaunch on the animation screen with a frame load of N iters."""
    drv.adb(["shell", "am", "force-stop", drv.PACKAGE], serial)
    time.sleep(1)
    drv.adb([
        "shell", "am", "start", "-n", drv.ACTIVITY,
        "--es", "navigate_to", TARGET_SCREEN,
        "--ei", "frame_iterations", str(iterations),
    ], serial)


def collect_p95(ch, project_id: str, iterations: int, secs: int,
                settle: int, serial=None) -> float | None:
    """Wipe the group, run one candidate for `secs`, return its frame-time P95."""
    drv.clear_version_metrics(ch, project_id, CAL_VERSION_CODE, CAL_VERSION_CODE,
                              METRIC_ID, SCREEN_NAME)
    launch_with_iterations(iterations, serial)
    print(f"  [collect] iterations={iterations:>8}  {secs}s ...")
    time.sleep(secs)
    # Let the last in-flight batch reach the backend before reading.
    time.sleep(settle)
    return drv.query_p95(ch, project_id, METRIC_ID, SCREEN_NAME, CAL_VERSION_CODE)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-id", default=drv.DEFAULT_PROJECT_ID,
                    help=f"project_id UUID (default: {drv.DEFAULT_PROJECT_ID})")
    ap.add_argument("--device", required=True, help="AVD name or adb serial")
    ap.add_argument("--candidates", default="0,100000,200000,400000,800000",
                    help="comma-separated iteration counts; 0 is the clean baseline")
    ap.add_argument("--secs", type=int, default=75, help="collection seconds per candidate")
    ap.add_argument("--settle", type=int, default=12, help="post-run flush wait (s)")
    ap.add_argument("--threshold", type=float, default=0.15, help="relative shift threshold")
    ap.add_argument("--endpoint", default="http://10.0.2.2:8080/",
                    help="backend URL baked into the APK (default: local stack)")
    ap.add_argument("--no-build", action="store_true", help="skip the one-time APK build")
    args = ap.parse_args()

    candidates = [int(c.strip()) for c in args.candidates.split(",") if c.strip() != ""]
    if 0 not in candidates:
        candidates = [0] + candidates
    candidates = sorted(set(candidates))

    serial = drv.resolve_serial(args.device.strip())

    ch = drv.clickhouse_connect.get_client(
        host=drv.CH_HOST, port=drv.CH_PORT, username=drv.CH_USER,
        password=drv.CH_PASSWORD, database=drv.CH_DATABASE,
    )

    if not args.no_build:
        drv.build_apk(CAL_VERSION_CODE, f"{CAL_VERSION_CODE}-frame-cal",
                      "none", 0, TARGET_SCREEN, serial,
                      endpoint_url=args.endpoint, project_id=args.project_id)
    drv.install_apk(serial)

    print(f"\n=== Frame calibration on {args.device} "
          f"(threshold {args.threshold*100:.0f}%) ===")
    results = []
    baseline_p95 = None
    for n in candidates:
        p95 = collect_p95(ch, args.project_id, n, args.secs, args.settle, serial)
        if n == 0:
            baseline_p95 = p95
        shift = None
        if baseline_p95 and p95 and baseline_p95 > 0:
            shift = (p95 - baseline_p95) / baseline_p95
        results.append((n, p95, shift))
        sh = f"{shift*100:+6.1f}%" if shift is not None else "   n/a"
        flag = ""
        if shift is not None and n != 0:
            flag = "FLAGGED" if shift > args.threshold else "quiet"
        print(f"    -> iterations={n:>8}  P95={p95}  shift={sh}  {flag}")

    drv.adb(["shell", "am", "force-stop", drv.PACKAGE], serial)

    print(f"\n=== Summary ({args.device}) ===")
    print(f"  {'iterations':>10}  {'P95 (ms)':>10}  {'shift':>8}  outcome")
    for n, p95, shift in results:
        p95s = f"{p95:.2f}" if p95 is not None else "n/a"
        if n == 0:
            print(f"  {n:>10}  {p95s:>10}  {'baseline':>8}")
            continue
        sh = f"{shift*100:+.1f}%" if shift is not None else "n/a"
        outcome = ("FLAGGED" if shift is not None and shift > args.threshold
                   else "quiet")
        print(f"  {n:>10}  {p95s:>10}  {sh:>8}  {outcome}")

    print("\nPick an iteration count that is 'quiet' on PerfX_High and 'FLAGGED' on")
    print("PerfX_Low, then set it as intensity 2 in frameWorkIterations() and run")
    print("e7_frame_tier through run_release_pair_experiments.py on all three cohorts.")


if __name__ == "__main__":
    main()
