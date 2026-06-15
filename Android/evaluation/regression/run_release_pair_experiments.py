#!/usr/bin/env python3
"""
Version-based regression-detection driver for the thesis evaluation (Phase 2).

For each experiment in experiments.yaml it:
  1. Builds a clean ("baseline") APK with the given versionCode and no regression.
  2. Installs + launches on the target device; navigates to the right screen.
  3. Collects for run_duration_minutes.
  4. Builds a regressed APK with the next versionCode and the baked regression.
  5. Installs + launches; collects for run_duration_minutes.
  6. Waits flush_wait_seconds for the SDK to upload remaining batches.
  7. Waits for the Docker Compose detector to run (it polls every 30 s).
  8. Queries ClickHouse for per-version medians and Postgres for detection result.
  9. Writes one CSV row per experiment to results/<run_id>_<device>.csv.

Usage:
  # Single device
  python3 run_release_pair_experiments.py \\
      --project-id <uuid> --device PerfX_Medium

  # All three AVDs in sequence (unattended)
  python3 run_release_pair_experiments.py \\
      --project-id <uuid> \\
      --device PerfX_Low,PerfX_Medium,PerfX_High

  # Quick smoke test — one experiment
  python3 run_release_pair_experiments.py \\
      --project-id <uuid> --device PerfX_Medium \\
      --experiments e1_cpu_high

Prerequisites:
  - Backend stack running (ClickHouse + Postgres reachable).
  - All named AVDs running and reachable via adb before the script starts.
  - Python deps: clickhouse_connect, psycopg2-binary, pyyaml (Analysis/requirements.txt).
"""

import argparse
import csv
import os
import subprocess
import sys
import numpy as np
import time
from datetime import datetime
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
HELPERS_DIR = Path(__file__).resolve().parent.parent / "helpers"

# Third-party / project imports — both paths must be on sys.path first.
sys.path.insert(0, str(REPO_ROOT / "Analysis"))
sys.path.insert(0, str(HELPERS_DIR))

import clickhouse_connect  # noqa: E402
import psycopg2           # noqa: E402
from regression_detection.config import (  # noqa: E402
    CH_HOST, CH_PORT, CH_USER, CH_PASSWORD, CH_DATABASE,
    PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD,
    DEFAULT_P95_THRESHOLD,
)
import aggregate_results as _agg   # noqa: E402
import plots as _plots              # noqa: E402
from comparison_plot import (       # noqa: E402
    fetch_values, plot_comparison, plot_multi_device_comparison,
)

PACKAGE = "com.ndevelop.perfx"
ACTIVITY = f"{PACKAGE}/.ui.MainActivity"
GRADLE_DIR = REPO_ROOT / "Android" / "PerfX"
APK_PATH = GRADLE_DIR / "demo/build/outputs/apk/withSdk/debug/demo-withSdk-debug.apk"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
FIGS_DIR    = Path(__file__).resolve().parent / "figs"

SCREEN_OF = {
    "cpu":    "compose/cpu_load",
    "memory": "compose/ram_load",
    "ui":     "compose/ui_responsiveness",
    "none":   "compose/cpu_load",
}
METRIC_OF = {
    "cpu":    "cpuUsage",
    "memory": "memoryUsage",
    "ui":     "frameTime",
    "none":   "cpuUsage",
}
# Maps experiments.yaml target_screen to SDK screen_name
SCREEN_NAME_OF = {
    "cpu_load":         "compose/cpu_load",
    "ram_load":         "compose/ram_load",
    "ui_responsiveness": "compose/ui_responsiveness",
}
METRIC_NAME_OF = {
    "cpu_load":         "cpuUsage",
    "ram_load":         "memoryUsage",
    "ui_responsiveness": "frameTime",
}


def resolve_serial(device: str) -> str:
    """Map an AVD name (e.g. 'PerfX_Medium') to its adb serial (e.g. 'emulator-5554').

    If device is already a known adb serial, return it unchanged.
    """
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()[1:]
    serials = [l.split("\t")[0] for l in lines if "\t" in l]

    if device in serials:
        return device

    for serial in serials:
        if not serial.startswith("emulator-"):
            continue
        name_out = subprocess.run(
            ["adb", "-s", serial, "emu", "avd", "name"],
            capture_output=True, text=True,
        ).stdout.strip().splitlines()
        avd_name = name_out[0].strip() if name_out else ""
        if avd_name == device:
            print(f"  [serial] {device} → {serial}")
            return serial

    print(f"  [warn] could not resolve serial for '{device}', using as-is")
    return device


def adb(args, serial=None, capture=True, check=True):
    cmd = ["adb"]
    if serial:
        cmd += ["-s", serial]
    cmd += args
    result = subprocess.run(cmd, capture_output=capture,
                            text=True, check=False)
    if check and result.returncode != 0:
        # Print adb's own error message before raising so the cause is visible.
        if result.stderr:
            print(f"  [adb error] {result.stderr.strip()}")
        if result.stdout:
            print(f"  [adb stdout] {result.stdout.strip()}")
        raise subprocess.CalledProcessError(result.returncode, cmd,
                                            result.stdout, result.stderr)
    return result


def build_apk(version_code: int, version_name: str,
              regression_type: str, regression_intensity: int,
              target_screen: str, serial=None) -> None:
    env = dict(os.environ)
    if serial:
        env["ANDROID_SERIAL"] = serial
    gradle_args = [
        "./gradlew", ":demo:assembleWithSdkDebug",
        f"-PsyntheticVersionCode={version_code}",
        f"-PsyntheticVersionName={version_name}",
        f"-PregressionType={regression_type}",
        f"-PregressionIntensity={regression_intensity}",
        f"-PtargetScreen={target_screen}",
    ]
    print(f"  [build] versionCode={version_code} type={regression_type} "
          f"intensity={regression_intensity} screen={target_screen}")
    subprocess.run(gradle_args, cwd=GRADLE_DIR, env=env, check=True)


def install_apk(serial=None) -> None:
    print(f"  [install] {APK_PATH.name}")
    # Uninstall first so version downgrades and signature changes never block us.
    adb(["uninstall", PACKAGE], serial, check=False)
    adb(["install", str(APK_PATH)], serial)


def launch_app(target_screen: str, serial=None) -> None:
    adb(["shell", "am", "force-stop", PACKAGE], serial)
    time.sleep(1)
    adb([
        "shell", "am", "start", "-n", ACTIVITY,
        "--es", "navigate_to", target_screen,
    ], serial)


def force_stop(serial=None) -> None:
    adb(["shell", "am", "force-stop", PACKAGE], serial)


def clear_version_metrics(ch_client, project_id: str,
                          baseline_vc: int, current_vc: int,
                          metric_id: str, screen_name: str) -> None:
    """Delete ALL ClickHouse rows for this project/metric/screen combination.

    Clearing only the current experiment's two version codes is not enough:
    data from previous experiments that share the same (metric_id, screen_name)
    group causes the detector's auto-resolve logic to immediately supersede the
    freshly-created regression row (because a newer version_code is present).
    Wiping the whole group gives each experiment a clean slate.
    """
    before = ch_client.query(
        "SELECT count() FROM metric_records "
        "WHERE project_id={pid:String} "
        "  AND metric_id={mid:String} "
        "  AND screen_name={screen:String}",
        parameters={"pid": project_id,
                    "mid": metric_id, "screen": screen_name},
    ).result_rows[0][0]

    if before == 0:
        return

    print(
        f"  [clear] {metric_id}/{screen_name}: {before} stale rows → deleting all...")
    ch_client.command(
        "ALTER TABLE metric_records DELETE "
        "WHERE project_id={pid:String} "
        "  AND metric_id={mid:String} "
        "  AND screen_name={screen:String}",
        parameters={"pid": project_id,
                    "mid": metric_id, "screen": screen_name},
    )

    # Poll until the mutation is applied (usually <5 s on local ClickHouse).
    for _ in range(30):
        time.sleep(1)
        remaining = ch_client.query(
            "SELECT count() FROM metric_records "
            "WHERE project_id={pid:String} "
            "  AND metric_id={mid:String} "
            "  AND screen_name={screen:String}",
            parameters={"pid": project_id,
                        "mid": metric_id, "screen": screen_name},
        ).result_rows[0][0]
        if remaining == 0:
            break
    else:
        print(
            f"  [warn] {metric_id}/{screen_name}: rows may not be fully deleted yet")


def query_p95(ch_client, project_id: str, metric_id: str,
              screen_name: str, version_code: int) -> float | None:
    rows = ch_client.query(
        """
        SELECT quantile(0.95)(value)
        FROM metric_records
        WHERE project_id  = {pid:String}
          AND metric_id   = {mid:String}
          AND screen_name = {screen:String}
          AND version_code = {vc:Int32}
        """,
        parameters={
            "pid": project_id, "mid": metric_id,
            "screen": screen_name, "vc": version_code,
        },
    ).result_rows
    val = rows[0][0] if rows else None
    return float(val) if val is not None else None


def clear_postgres_regressions(pg_conn, project_id: str,
                               baseline_vc: int, current_vc: int) -> None:
    """Delete any pre-existing Postgres regression rows for these version codes.

    Without this, a row left over from a previous run (with status != 'open')
    blocks the upsert from re-inserting, so query_detected() never returns True.
    """
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM regressions
            WHERE project_id            = %s::uuid
              AND baseline_version_code = %s
              AND current_version_code  = %s
            """,
            (project_id, baseline_vc, current_vc),
        )
        deleted = cur.rowcount
    pg_conn.commit()
    if deleted:
        print(f"  [clear-pg] deleted {deleted} stale regression row(s) "
              f"for versions {baseline_vc}/{current_vc}")


def query_detected(pg_conn, project_id: str, metric_id: str,
                   screen_name: str,
                   baseline_vc: int, current_vc: int) -> bool:
    # Accept any status: we clear the row before each run, so any row that
    # appears afterward was created by the detector in this experiment cycle.
    # Checking only 'open' fails when the auto-resolve logic immediately
    # supersedes the row because older experiments share the same screen group.
    with pg_conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM regressions
            WHERE project_id           = %s::uuid
              AND metric_id            = %s
              AND screen_name          = %s
              AND baseline_version_code = %s
              AND current_version_code  = %s
            """,
            (project_id, metric_id, screen_name, baseline_vc, current_vc),
        )
        return cur.fetchone()[0] > 0


def device_cohort(device_serial: str) -> str:
    mapping = {
        "PerfX_Low":    "Low",
        "PerfX_Medium": "Medium",
        "PerfX_High":   "High",
    }
    return mapping.get(device_serial, device_serial)


def run_experiment(exp: dict, project_id: str, device: str,
                   run_duration_minutes: int, flush_wait_seconds: int,
                   ch_client, pg_conn,
                   no_build: bool = False) -> dict:
    serial = resolve_serial(device)
    exp_id = exp["id"]
    reg_type = exp["type"]
    intensity = exp["intensity"]
    target_screen = exp["target_screen"]
    baseline_vc = exp["baseline_version_code"]
    current_vc = exp["current_version_code"]
    screen_name = SCREEN_NAME_OF.get(target_screen,
                                     f"compose/{target_screen}")
    metric_id = METRIC_NAME_OF.get(target_screen, "cpuUsage")
    run_secs = run_duration_minutes * 60
    cohort = device_cohort(device)
    ground_truth = reg_type != "none"

    print(
        f"\n=== {exp_id} | device={device} | {reg_type} intensity={intensity} ===")

    # Clear any stale data from a previous run of this screen/metric group.
    clear_version_metrics(ch_client, project_id, baseline_vc, current_vc,
                          metric_id, screen_name)

    # ── Baseline APK (clean) ───────────────────────────────────────────────────
    if not no_build:
        build_apk(baseline_vc, f"{baseline_vc}-clean",
                  "none", 0, target_screen, serial)
    install_apk(serial)
    launch_app(target_screen, serial)
    print(f"  [collect baseline] {run_duration_minutes} min...")
    time.sleep(run_secs)
    force_stop(serial)

    # ── Regressed APK ─────────────────────────────────────────────────────────
    if not no_build:
        build_apk(current_vc, f"{current_vc}-{reg_type}-i{intensity}",
                  reg_type, intensity, target_screen, serial)
    install_apk(serial)
    launch_app(target_screen, serial)
    print(f"  [collect regressed] {run_duration_minutes} min...")
    time.sleep(run_secs)
    force_stop(serial)

    # ── Query results from ClickHouse ─────────────────────────────────────────
    baseline_p95 = query_p95(ch_client, project_id, metric_id,
                             screen_name, baseline_vc)
    current_p95 = query_p95(ch_client, project_id, metric_id,
                             screen_name, current_vc)

    if baseline_p95 and current_p95 and baseline_p95 > 0:
        delta_pct = round((current_p95 - baseline_p95) /
                          baseline_p95 * 100, 2)
    else:
        delta_pct = None

    # ── Wait for Docker detector to fire ─────────────────────────────────────
    # Poll Postgres until a regression row appears (or until DETECTOR_WAIT_SECS).
    # The detector polls every POLL_INTERVAL_SECONDS (30 s); we allow two full
    # cycles so a missed beat doesn't cause a false negative in the CSV.
    DETECTOR_WAIT_SECS = 40
    print(f"  [detect] polling Postgres for up to {DETECTOR_WAIT_SECS}s...")
    detected = False
    for elapsed in range(0, DETECTOR_WAIT_SECS, 5):
        detected = query_detected(pg_conn, project_id, metric_id,
                                  screen_name, baseline_vc, current_vc)
        if detected:
            print(f"  [detect] regression found after ~{elapsed}s")
            break
        time.sleep(5)
    else:
        print(f"  [detect] no regression in Postgres after {DETECTOR_WAIT_SECS}s "
              f"(delta={delta_pct}%)")

    row = dict(
        experiment_id=exp_id,
        device=device,
        cohort=cohort,
        baseline_version_code=baseline_vc,
        current_version_code=current_vc,
        metric_id=metric_id,
        screen_name=screen_name,
        baseline_p95=baseline_p95,
        current_p95=current_p95,
        delta_pct=delta_pct,
        ground_truth_regression=ground_truth,
        detected=detected,
        threshold=DEFAULT_P95_THRESHOLD,
        regression_type=reg_type,
        intensity=intensity,
        run_duration_minutes=run_duration_minutes,
        timestamp=datetime.utcnow().isoformat(),
    )

    outcome = ("TP" if ground_truth and detected else
               "FN" if ground_truth and not detected else
               "FP" if not ground_truth and detected else "TN")
    print(f"  baseline_p95={baseline_p95}  current_p95={current_p95}  "
          f"delta={delta_pct}%  detected={detected}  → {outcome}")

    # ── Save raw samples for the multi-device comparison plot ─────────────────
    # ClickHouse data is cleared before each new device's run, so arrays must be
    # persisted to disk here while they are still available.
    try:
        b_vals = fetch_values(ch_client, project_id, metric_id,
                              screen_name, baseline_vc)
        r_vals = fetch_values(ch_client, project_id, metric_id,
                              screen_name, current_vc)
        npz_dir = RESULTS_DIR / "comparison_data"
        npz_dir.mkdir(parents=True, exist_ok=True)
        np.savez(npz_dir / f"{exp_id}__{device}.npz",
                 baseline=b_vals, regression=r_vals,
                 metric_id=np.array(metric_id),
                 reg_type=np.array(reg_type),
                 intensity=np.array(intensity))
        print(f"  [data] saved comparison arrays → {npz_dir / f'{exp_id}__{device}.npz'}")
    except Exception as exc:
        print(f"  [data] comparison arrays skipped: {exc}")

    return row


CSV_FIELDS = [
    "experiment_id", "device", "cohort",
    "baseline_version_code", "current_version_code",
    "metric_id", "screen_name",
    "baseline_p95", "current_p95", "delta_pct",
    "ground_truth_regression", "detected", "threshold",
    "regression_type", "intensity", "run_duration_minutes", "timestamp",
]


def _summarise(rows: list, label: str, out_path) -> None:
    n = len(rows)
    tp = sum(1 for r in rows if r["ground_truth_regression"] and r["detected"])
    fp = sum(1 for r in rows if not r["ground_truth_regression"] and r["detected"])
    fn = sum(1 for r in rows if r["ground_truth_regression"] and not r["detected"])
    tn = sum(1 for r in rows if not r["ground_truth_regression"] and not r["detected"])
    print(f"\n=== {label}: {n} experiment(s) → {out_path} ===")
    print(f"  TP={tp}  FP={fp}  FN={fn}  TN={tn}")


def _generate_comparison_plots(results_dir: Path, figs_dir: Path) -> None:
    """Build one multi-device comparison PNG per experiment from saved .npz files.

    Files are named  {exp_id}__{device}.npz  (double-underscore separator).
    All .npz files present are included regardless of which device is current,
    so plots accumulate across successive single-device runs.
    """
    from collections import defaultdict
    npz_dir = results_dir / "comparison_data"
    if not npz_dir.exists():
        print("  No comparison_data/ found — skipping.")
        return

    groups: dict = defaultdict(list)
    for npz_path in sorted(npz_dir.glob("*.npz")):
        if "__" not in npz_path.stem:
            continue
        exp_id_key, dev = npz_path.stem.split("__", 1)
        groups[exp_id_key].append((dev, npz_path))

    figs_dir.mkdir(parents=True, exist_ok=True)
    for exp_id_key, entries in sorted(groups.items()):
        try:
            device_data = []
            metric_id_val, reg_info = "cpuUsage", ""
            for dev, npz_path in entries:
                d = np.load(npz_path, allow_pickle=True)
                metric_id_val = str(d["metric_id"])
                reg_info = f"{d['reg_type']} intensity={d['intensity']}"
                device_data.append((dev, d["baseline"], d["regression"]))
            plot_multi_device_comparison(
                device_data,
                metric_id=metric_id_val,
                exp_title=f"{exp_id_key}  ({reg_info})",
                out_path=figs_dir / f"comparison_{exp_id_key}.png",
            )
        except Exception as exc:
            print(f"  [plot] {exp_id_key} skipped: {exc}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-id", required=True,
                    help="project_id UUID the demo app reports under")
    ap.add_argument("--device", required=True,
                    help="adb serial or AVD name of the target device")
    ap.add_argument("--config", default=str(Path(__file__).parent / "experiments.yaml"),
                    help="path to experiments.yaml")
    ap.add_argument("--experiments", default="",
                    help="comma-separated experiment IDs to run; empty = all")
    ap.add_argument("--no-build", action="store_true",
                    help="skip Gradle build (APK already installed)")
    args = ap.parse_args()

    device = args.device.strip()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    run_duration = cfg.get("run_duration_minutes", 15)
    flush_wait = cfg.get("flush_wait_seconds", 60)
    experiments = cfg["experiments"]

    if args.experiments:
        ids = {e.strip() for e in args.experiments.split(",")}
        experiments = [e for e in experiments if e["id"] in ids]
        if not experiments:
            print(f"No experiments matched: {args.experiments}", file=sys.stderr)
            sys.exit(1)

    ch = clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT, username=CH_USER,
        password=CH_PASSWORD, database=CH_DATABASE,
    )
    pg = psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB,
        user=PG_USER, password=PG_PASSWORD,
    )

    # Clear detector state from any previous run on this project
    with pg.cursor() as cur:
        cur.execute("DELETE FROM regressions WHERE project_id = %s::uuid",
                    (args.project_id,))
        print(f"[init] cleared {cur.rowcount} existing regression row(s)")
    pg.commit()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    out_path = RESULTS_DIR / f"{run_id}_{device}.csv"
    rows = []

    try:
        for exp in experiments:
            row = run_experiment(
                exp, args.project_id, device,
                run_duration, flush_wait,
                ch, pg,
                no_build=args.no_build,
            )
            rows.append(row)

            # Write incrementally so partial runs are preserved
            with out_path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            print(f"  [saved] {out_path}")

    finally:
        pg.close()

    _summarise(rows, f"Done ({device})", out_path)

    # ── Post-run analysis ─────────────────────────────────────────────────────
    print("\n=== Post-run analysis ===")
    try:
        _agg.run(RESULTS_DIR)
        _plots.run(RESULTS_DIR, FIGS_DIR)
    except Exception as exc:
        print(f"  [analysis] skipped: {exc}")

    # ── Multi-device comparison plots (accumulates across runs) ───────────────
    print("\n=== Multi-device comparison plots ===")
    _generate_comparison_plots(RESULTS_DIR, FIGS_DIR)


if __name__ == "__main__":
    main()
