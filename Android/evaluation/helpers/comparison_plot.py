#!/usr/bin/env python3
"""
Baseline vs regression comparison chart.

Queries ClickHouse for every raw sample from two version codes (baseline and
regression), then produces a two-panel figure:
  • Left  — time series: individual samples in collection order, coloured by
             window, with P95 lines annotated.
  • Right — distribution: violin + jittered scatter for each window.

Output:
  results/figs/comparison_<metric_id>.pdf

Usage:
  python3 comparison_plot.py \\
      --project-id  <uuid> \\
      --baseline-vc 1001   \\
      --current-vc  1002   \\
      --metric-id   cpuUsage \\
      --screen-name "compose/cpu_load"

Optional:
  --figs-dir  path/to/output   (default: ../results/figs)
  --title     "CPU medium"     (added to figure suptitle)
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "Analysis"))

import clickhouse_connect  # noqa: E402
from regression_detection.config import (  # noqa: E402
    CH_HOST, CH_PORT, CH_USER, CH_PASSWORD, CH_DATABASE,
)

FIGS_DIR = Path(__file__).resolve().parent.parent / "regression" / "figs"

METRIC_LABELS = {
    "cpuUsage":    "CPU usage (%)",
    "memoryUsage": "RAM usage (MB)",
    "frameTime":   "Frame time (ms)",
}

BASELINE_COLOR   = "#4C72B0"   # muted blue
REGRESSION_COLOR = "#DD8452"   # muted orange


def fetch_values(ch, project_id: str, metric_id: str,
                 screen_name: str, version_code: int) -> np.ndarray:
    rows = ch.query(
        """
        SELECT value
        FROM metric_records
        WHERE project_id  = {pid:String}
          AND metric_id   = {mid:String}
          AND screen_name = {screen:String}
          AND version_code = {vc:Int32}
        ORDER BY ts
        """,
        parameters={
            "pid":    project_id,
            "mid":    metric_id,
            "screen": screen_name,
            "vc":     version_code,
        },
    ).result_rows
    return np.array([r[0] for r in rows], dtype=float)


def _draw_panel(ax, baseline: np.ndarray, regression: np.ndarray,
                metric_id: str, row_title: str) -> None:
    """Draw one baseline-vs-regression time-series panel onto *ax*."""
    ylabel = METRIC_LABELS.get(metric_id, metric_id)

    b_p95 = float(np.percentile(baseline,  95))
    r_p95 = float(np.percentile(regression, 95))

    b_x = np.arange(len(baseline))
    r_x = np.arange(len(regression)) + len(baseline)
    total = len(baseline) + len(regression)

    ax.plot(b_x, baseline,  color=BASELINE_COLOR,   linewidth=0.8, alpha=0.6, zorder=1)
    ax.plot(r_x, regression, color=REGRESSION_COLOR, linewidth=0.8, alpha=0.6, zorder=1)
    ax.scatter(b_x, baseline,  s=8, color=BASELINE_COLOR,   linewidths=0, zorder=2,
               label="Baseline")
    ax.scatter(r_x, regression, s=8, color=REGRESSION_COLOR, linewidths=0, zorder=2,
               label="Regression")

    sep = len(baseline) - 0.5
    ax.axvline(sep, color="grey", linewidth=0.9, linestyle="--")

    ax.axhline(b_p95, xmax=len(baseline) / total,
               color=BASELINE_COLOR, linewidth=1.2, linestyle=":",
               label=f"baseline P95 = {b_p95:.1f}")
    ax.axhline(r_p95, xmin=len(baseline) / total,
               color=REGRESSION_COLOR, linewidth=1.2, linestyle=":",
               label=f"regression P95 = {r_p95:.1f}")
    ax.set_xlabel("Sample index")
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=8, loc="upper left")
    ax.set_xlim(-1, total)


def plot_comparison(baseline: np.ndarray, regression: np.ndarray,
                    metric_id: str, title: str, out_path: Path) -> None:
    """Single-device convenience wrapper (used for standalone CLI invocations)."""
    fig, ax = plt.subplots(figsize=(10, 4))
    _draw_panel(ax, baseline, regression, metric_id, title or METRIC_LABELS.get(metric_id, metric_id))
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  → {out_path}")


def plot_multi_device_comparison(
    device_data: list[tuple[str, np.ndarray, np.ndarray]],
    metric_id: str,
    exp_title: str,
    out_path: Path,
) -> None:
    """One row per device, all on a single PNG.

    Args:
        device_data: list of (device_name, baseline_array, regression_array)
                     in the order you want them rendered top-to-bottom.
        metric_id:   e.g. "cpuUsage"
        exp_title:   figure suptitle, e.g. "e1_cpu_high (cpu intensity=3)"
        out_path:    where to save the PNG
    """
    n = len(device_data)
    fig, axes = plt.subplots(n, 1, figsize=(10, 4 * n))
    if n == 1:
        axes = [axes]

    for ax, (device, baseline, regression) in zip(axes, device_data):
        _draw_panel(ax, baseline, regression, metric_id, device)

    fig.suptitle(exp_title, fontsize=12, y=1.01)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  → {out_path}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--npz", default=None,
                    help="load data from a saved .npz file instead of querying ClickHouse "
                         "(e.g. results/comparison_data/e1_ui_low__PerfX_Low.npz)")
    ap.add_argument("--project-id",   default=None)
    ap.add_argument("--baseline-vc",  type=int, default=None,
                    help="version_code for the baseline window")
    ap.add_argument("--current-vc",   type=int, default=None,
                    help="version_code for the regression window")
    ap.add_argument("--metric-id",    default="cpuUsage")
    ap.add_argument("--screen-name",  default="compose/cpu_load")
    ap.add_argument("--figs-dir",     default=str(FIGS_DIR))
    ap.add_argument("--title",        default="",
                    help="optional label added to the figure title")
    args = ap.parse_args()

    if args.npz:
        d = np.load(args.npz, allow_pickle=True)
        baseline   = d["baseline"].astype(float)
        regression = d["regression"].astype(float)
        metric_id  = str(d["metric_id"]) if "metric_id" in d else args.metric_id
        title = args.title or Path(args.npz).stem
        out = Path(args.figs_dir) / f"comparison_{Path(args.npz).stem}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        plot_comparison(baseline, regression, metric_id, title, out)
        return

    if not args.project_id or args.baseline_vc is None or args.current_vc is None:
        ap.error("--project-id, --baseline-vc and --current-vc are required unless --npz is used")

    ch = clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT,
        username=CH_USER, password=CH_PASSWORD,
        database=CH_DATABASE,
    )

    print(f"Fetching baseline  (vc={args.baseline_vc}) …")
    baseline = fetch_values(ch, args.project_id, args.metric_id,
                            args.screen_name, args.baseline_vc)
    print(f"  {len(baseline)} samples  median={np.median(baseline):.2f}  "
          f"P95={np.percentile(baseline, 95):.2f}")

    print(f"Fetching regression (vc={args.current_vc}) …")
    regression = fetch_values(ch, args.project_id, args.metric_id,
                              args.screen_name, args.current_vc)
    print(f"  {len(regression)} samples  median={np.median(regression):.2f}  "
          f"P95={np.percentile(regression, 95):.2f}")

    if len(baseline) == 0 or len(regression) == 0:
        print("ERROR: one of the windows has no data — check project_id, "
              "version_code, and screen_name.")
        sys.exit(1)

    out = Path(args.figs_dir) / f"comparison_{args.metric_id}.png"
    plot_comparison(baseline, regression, args.metric_id, args.title, out)


if __name__ == "__main__":
    main()
