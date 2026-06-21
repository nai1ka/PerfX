#!/usr/bin/env python3
"""
Cheddar noise-floor driver — extends "Behaviour Under Noise" (Section 5.4.1)
beyond the synthetic demo app.

The existing E2 control runs (experiments.yaml: e2_control_*) already measure
how large a relative P95 shift pure noise produces, but they do it on the
synthetic `:demo` app's idle Compose screens. This script repeats the same
idea — two builds that differ ONLY in version code, no regression injected —
on Cheddar, the real Hacker News client used for the SDK overhead evaluation
(Section 5.2). Cheddar's workload (network requests, list rendering,
in-app navigation) is closer to a production app than the synthetic screens,
so this shows whether the noise-floor finding generalises.

For each repeat it:
  1. Builds a Cheddar APK with version code N (everything else unchanged).
  2. Installs + launches it; auto-scrolls the story feed for
     run_duration_minutes (same scroll worker as evaluation/overhead's
     measure_overhead.sh).
  3. Builds a second, otherwise-identical APK with version code N+1.
  4. Installs + launches it; scrolls for run_duration_minutes again.
  5. Waits flush_wait_seconds for the SDK to upload remaining batches.
  6. Queries ClickHouse directly for the per-version P95 of cpuUsage,
     memoryUsage, and frameTime under Cheddar's single reported screen,
     computes the relative shift itself, and writes one CSV row per metric
     to results/cheddar_noise/<run_id>_<device>.csv.

This talks to ClickHouse only — it does NOT go through the live detector
container or Postgres. The relative shift is the same quantity the detector
would compute (current_p95 - baseline_p95) / baseline_p95, so
`exceeds_threshold` in the CSV reproduces the detector's flagging rule
without depending on its poll cycle or on MIN_SAMPLES_PER_VERSION maturity
gating. Because nothing was actually changed between the two builds, any
row with exceeds_threshold=True would have been a false positive.

Prerequisites:
  - The Cheddar fork at --app-dir has the PerfX SDK wired in (see
    CheddarApplication.kt) and its app/build.gradle.kts accepts
    -PsyntheticVersionCode / -PsyntheticVersionName / -PprojectId /
    -PendpointUrl (added alongside this script).
  - Backend stack running and reachable (the SDK posts to /ingest, which
    writes into ClickHouse) — the detector container does not need to be
    running for this script.
  - The target AVD/device is booted and reachable via adb.

Usage:
  # Full run: 5 repeats, 15-minute collection windows (production settings)
  python3 run_cheddar_noise_experiments.py --device PerfX_Medium

  # Quick smoke test — one repeat, 2-minute windows
  python3 run_cheddar_noise_experiments.py \\
      --device PerfX_Medium --repeats 1 \\
      --run-duration-minutes 2 --flush-wait-seconds 15
"""

import argparse
import csv
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
HELPERS_DIR = Path(__file__).resolve().parent.parent / "helpers"

sys.path.insert(0, str(REPO_ROOT / "Analysis"))
sys.path.insert(0, str(HELPERS_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import clickhouse_connect  # noqa: E402
from regression_detection.config import (  # noqa: E402
    CH_HOST, CH_PORT, CH_USER, CH_PASSWORD, CH_DATABASE,
    DEFAULT_P95_THRESHOLD,
)
from comparison_plot import fetch_values, plot_multi_device_comparison  # noqa: E402

# Reuse the adb/ClickHouse/Postgres helpers already written for the demo-app
# driver instead of duplicating them — importing the module does not run its
# main() (guarded by `if __name__ == "__main__"`).
import run_release_pair_experiments as rpe  # noqa: E402

METRICS = ["frameTime"]

DEFAULT_APP_DIR = "/Users/nai1ka/Projects/Cheddar"
DEFAULT_PACKAGE = "co.adrianblan.cheddar.debug"
DEFAULT_ACTIVITY = "co.adrianblan.cheddar.MainActivity"
# Cheddar never calls PerfX.attachNavController(), so every metric is
# reported under the resumed Activity's simple class name (see
# PerfX.currentScreenName() fallback) — a single screen for the whole run.
DEFAULT_SCREEN_NAME = "MainActivity"
# Same UUID CheddarApplication.kt falls back to when -PprojectId is omitted.
DEFAULT_PROJECT_ID = "17b80ec6-9a51-4ece-8f4b-05a3cb3a04d0"
DEFAULT_ENDPOINT = "http://10.0.2.2:8080/"

RESULTS_DIR = Path(__file__).resolve().parent / "results" / "cheddar_noise"
FIGS_DIR = Path(__file__).resolve().parent / "figs"

CSV_FIELDS = [
    "experiment_id", "app", "device", "cohort",
    "baseline_version_code", "current_version_code",
    "metric_id", "screen_name",
    "baseline_p95", "current_p95", "delta_pct",
    "exceeds_threshold", "threshold", "run_duration_seconds", "timestamp",
]


# ── Cheddar-specific build/install/launch (Cheddar has no RegressionInjector,
#    no synthetic screens, and a different package/activity than the demo
#    app, so these can't just be reused from run_release_pair_experiments) ──

def build_apk(app_dir: Path, version_code: int, version_name: str,
              project_id: str, endpoint_url: str, serial=None) -> None:
    env = dict(os.environ)
    if serial:
        env["ANDROID_SERIAL"] = serial
    gradle_args = [
        "./gradlew", ":app:assembleWithSdkDebug",
        f"-PsyntheticVersionCode={version_code}",
        f"-PsyntheticVersionName={version_name}",
        f"-PprojectId={project_id}",
        f"-PendpointUrl={endpoint_url}",
    ]
    print(f"  [build] versionCode={version_code} ({version_name})")
    subprocess.run(gradle_args, cwd=app_dir, env=env, check=True)


def install_apk(apk_path: Path, package: str, serial=None) -> None:
    print(f"  [install] {apk_path.name}")
    rpe.adb(["uninstall", package], serial, check=False)
    rpe.adb(["install", str(apk_path)], serial)


def launch_app(package: str, activity: str, serial=None) -> None:
    rpe.adb(["shell", "am", "force-stop", package], serial)
    time.sleep(1)
    rpe.adb(["shell", "am", "start", "-n", f"{package}/{activity}"], serial)
    time.sleep(4)  # let the feed load before scrolling starts


def force_stop(package: str, serial=None) -> None:
    rpe.adb(["shell", "am", "force-stop", package], serial)


def _screen_size(serial=None) -> tuple[int, int]:
    out = rpe.adb(["shell", "wm", "size"], serial).stdout.strip()
    # "Physical size: 1080x2340"
    dims = out.split(":")[-1].strip()
    w, h = dims.split("x")
    return int(w), int(h)


def auto_scroll_worker(package: str, serial, stop_event: threading.Event) -> None:
    """Mirrors the auto_scroll() loop in evaluation/overhead/measure_overhead.sh:
    scroll down every 2s, tap back to the top every ~20s, so the workload
    looks the same as the one already used for the overhead measurement."""
    width, height = _screen_size(serial)
    mid_x = width // 2
    scroll_from = height * 3 // 4
    scroll_to = height // 4

    tick = 0
    while not stop_event.is_set():
        pid = rpe.adb(["shell", "pidof", package], serial, check=False).stdout.strip()
        if not pid:
            break
        rpe.adb(["shell", "input", "swipe", str(mid_x), str(scroll_from),
                str(mid_x), str(scroll_to), "400"], serial, check=False)
        if stop_event.wait(2):
            break
        tick += 1
        if tick % 10 == 0:
            rpe.adb(["shell", "input", "tap", str(mid_x), "40"], serial, check=False)
            stop_event.wait(1)


def collect(package: str, serial, duration_secs: int) -> None:
    stop_event = threading.Event()
    worker = threading.Thread(
        target=auto_scroll_worker, args=(package, serial, stop_event), daemon=True,
    )
    worker.start()
    time.sleep(duration_secs)
    stop_event.set()
    worker.join(timeout=5)


# ── One baseline/current pair ──────────────────────────────────────────────

def run_noise_repeat(repeat_idx: int, args, apk_path: Path,
                     ch_client) -> list[dict]:
    serial = rpe.resolve_serial(args.device)
    cohort = rpe.device_cohort(args.device)
    baseline_vc = args.start_version_code + repeat_idx * 2
    current_vc = baseline_vc + 1
    exp_id = f"cheddar_noise_{repeat_idx + 1}"
    run_secs = args.run_duration_seconds

    print(f"\n=== {exp_id} | device={args.device} | "
          f"versionCode {baseline_vc} -> {current_vc} (no change) ===")

    for metric_id in METRICS:
        rpe.clear_version_metrics(ch_client, args.project_id, baseline_vc,
                                  current_vc, metric_id, args.screen_name)

    # ── Build A ───────────────────────────────────────────────────────────
    if not args.no_build:
        build_apk(args.app_dir, baseline_vc, f"{baseline_vc}-noise-a",
                  args.project_id, args.endpoint, serial)
    install_apk(apk_path, args.package, serial)
    launch_app(args.package, args.activity, serial)
    print(f"  [collect A] {args.run_duration_seconds}s, scrolling...")
    collect(args.package, serial, run_secs)
    force_stop(args.package, serial)

    # ── Build B (identical app, version code only) ──────────────────────────
    if not args.no_build:
        build_apk(args.app_dir, current_vc, f"{current_vc}-noise-b",
                  args.project_id, args.endpoint, serial)
    install_apk(apk_path, args.package, serial)
    launch_app(args.package, args.activity, serial)
    print(f"  [collect B] {args.run_duration_seconds}s, scrolling...")
    collect(args.package, serial, run_secs)
    force_stop(args.package, serial)

    print(f"  [flush] waiting {args.flush_wait_seconds}s for SDK upload...")
    time.sleep(args.flush_wait_seconds)

    rows = []
    for metric_id in METRICS:
        baseline_p95 = rpe.query_p95(ch_client, args.project_id, metric_id,
                                     args.screen_name, baseline_vc)
        current_p95 = rpe.query_p95(ch_client, args.project_id, metric_id,
                                    args.screen_name, current_vc)
        if baseline_p95 and current_p95 and baseline_p95 > 0:
            delta_pct = round((current_p95 - baseline_p95) / baseline_p95 * 100, 2)
        else:
            delta_pct = None
        # Same rule the detector applies, computed locally so this script
        # doesn't depend on the live detector container or Postgres.
        exceeds_threshold = (delta_pct is not None
                             and delta_pct > DEFAULT_P95_THRESHOLD * 100)

        row = dict(
            experiment_id=exp_id, app="cheddar",
            device=args.device, cohort=cohort,
            baseline_version_code=baseline_vc, current_version_code=current_vc,
            metric_id=metric_id, screen_name=args.screen_name,
            baseline_p95=baseline_p95, current_p95=current_p95, delta_pct=delta_pct,
            exceeds_threshold=exceeds_threshold, threshold=DEFAULT_P95_THRESHOLD,
            run_duration_seconds=args.run_duration_seconds,
            timestamp=datetime.utcnow().isoformat(),
        )
        outcome = "FP" if exceeds_threshold else "TN"
        print(f"  {metric_id}: baseline_p95={baseline_p95}  current_p95={current_p95}  "
              f"delta={delta_pct}%  exceeds_threshold={exceeds_threshold}  -> {outcome}")
        rows.append(row)

        try:
            b_vals = fetch_values(ch_client, args.project_id, metric_id,
                                  args.screen_name, baseline_vc)
            r_vals = fetch_values(ch_client, args.project_id, metric_id,
                                  args.screen_name, current_vc)
            npz_dir = RESULTS_DIR / "comparison_data"
            npz_dir.mkdir(parents=True, exist_ok=True)
            np.savez(npz_dir / f"{exp_id}_{metric_id}__{args.device}.npz",
                     baseline=b_vals, regression=r_vals,
                     metric_id=np.array(metric_id))
        except Exception as exc:
            print(f"  [data] comparison arrays skipped for {metric_id}: {exc}")

    return rows


def _summarise(rows: list, out_path: Path) -> None:
    n = len(rows)
    fp = sum(1 for r in rows if r["exceeds_threshold"])
    print(f"\n=== Done: {n} (metric x repeat) row(s) -> {out_path} ===")
    print(f"  exceeds_threshold = {fp} / {n}")
    for metric_id in METRICS:
        deltas = [r["delta_pct"] for r in rows
                 if r["metric_id"] == metric_id and r["delta_pct"] is not None]
        if not deltas:
            continue
        print(f"  {metric_id}: mean delta={np.mean(deltas):.2f}%  "
              f"max delta={np.max(deltas):.2f}%  n={len(deltas)}")


def _generate_comparison_plots(results_dir: Path, figs_dir: Path, device: str) -> None:
    npz_dir = results_dir / "comparison_data"
    if not npz_dir.exists():
        return
    figs_dir.mkdir(parents=True, exist_ok=True)
    for npz_path in sorted(npz_dir.glob(f"*__{device}.npz")):
        try:
            d = np.load(npz_path, allow_pickle=True)
            metric_id = str(d["metric_id"])
            exp_key = npz_path.stem.replace(f"__{device}", "")
            plot_multi_device_comparison(
                [(device, d["baseline"], d["regression"])],
                metric_id=metric_id,
                exp_title=f"{exp_key} (Cheddar, no change)",
                out_path=figs_dir / f"comparison_{exp_key}__{device}.png",
            )
        except Exception as exc:
            print(f"  [plot] {npz_path.name} skipped: {exc}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-id", default=DEFAULT_PROJECT_ID,
                    help=f"project_id UUID Cheddar reports under (default: {DEFAULT_PROJECT_ID})")
    ap.add_argument("--device", required=True,
                    help="adb serial or AVD name of the target device")
    ap.add_argument("--repeats", type=int, default=5,
                    help="number of independent baseline/current pairs to run (default: 5, "
                         "matching the demo app's e2_control_1..5)")
    ap.add_argument("--start-version-code", type=int, default=9001,
                    help="version code of the first repeat's baseline build; each repeat "
                         "consumes two consecutive codes (default: 9001)")
    ap.add_argument("--run-duration-seconds", type=int, default=180,
                    help="collection time per build in seconds (default: 180)")
    ap.add_argument("--flush-wait-seconds", type=int, default=60,
                    help="wait after each pair for the SDK to flush + detector to poll "
                         "(default: 60, matching production settings in experiments.yaml)")
    ap.add_argument("--app-dir", default=DEFAULT_APP_DIR,
                    help=f"Cheddar checkout directory (default: {DEFAULT_APP_DIR})")
    ap.add_argument("--package", default=DEFAULT_PACKAGE)
    ap.add_argument("--activity", default=DEFAULT_ACTIVITY)
    ap.add_argument("--screen-name", default=DEFAULT_SCREEN_NAME,
                    help="screen_name PerfX reports for Cheddar (default: the resumed "
                         f"Activity's simple class name, '{DEFAULT_SCREEN_NAME}')")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT,
                    help="backend URL baked into the APK (default: local stack via the "
                         "emulator host alias)")
    ap.add_argument("--no-build", action="store_true",
                    help="skip Gradle build (APK already installed)")
    args = ap.parse_args()

    args.app_dir = Path(args.app_dir)
    args.device = args.device.strip()
    apk_path = args.app_dir / "app/build/outputs/apk/withSdk/debug/app-withSdk-debug.apk"

    ch = clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT, username=CH_USER,
        password=CH_PASSWORD, database=CH_DATABASE,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    out_path = RESULTS_DIR / f"{run_id}_{args.device}.csv"
    rows = []

    for i in range(args.repeats):
        rows.extend(run_noise_repeat(i, args, apk_path, ch))
        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  [saved] {out_path}")

    _summarise(rows, out_path)

    print("\n=== Comparison plots ===")
    try:
        _generate_comparison_plots(RESULTS_DIR, FIGS_DIR, args.device)
    except Exception as exc:
        print(f"  [plot] skipped: {exc}")


if __name__ == "__main__":
    main()
