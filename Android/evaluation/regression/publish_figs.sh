#!/usr/bin/env bash
# Re-generate all summary CSVs and figures from existing experiment data.
#
# Use this to regenerate figures without re-running experiments, e.g. after
# tweaking a plot style.  During a normal evaluation run, figures are produced
# automatically by run_release_pair_experiments.py.
#
# Usage:
#   Android/evaluation/run/publish_figs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELPERS_DIR="$SCRIPT_DIR/../helpers"
RESULTS_DIR="$SCRIPT_DIR/results"
FIGS_DIR="$SCRIPT_DIR/figs"

mkdir -p "$FIGS_DIR"

echo "=== Aggregating CSVs ==="
python3 "$HELPERS_DIR/aggregate_results.py" --results-dir "$RESULTS_DIR"

echo ""
echo "=== Generating summary figures ==="
python3 "$HELPERS_DIR/plots.py" --results-dir "$RESULTS_DIR" --figs-dir "$FIGS_DIR"

echo ""
echo "=== Generating multi-device comparison plots ==="
python3 - <<'EOF'
import sys, numpy as np
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "helpers"))
from comparison_plot import plot_multi_device_comparison

npz_dir  = Path(__file__).resolve().parent / "results" / "comparison_data"
figs_dir = Path(__file__).resolve().parent / "figs"

if not npz_dir.exists():
    print("  No comparison_data/ found — skipping.")
    sys.exit(0)

groups = defaultdict(list)
for p in sorted(npz_dir.glob("*.npz")):
    if "__" not in p.stem:
        continue
    exp_id, dev = p.stem.split("__", 1)
    groups[exp_id].append((dev, p))

figs_dir.mkdir(parents=True, exist_ok=True)
for exp_id, entries in sorted(groups.items()):
    device_data, metric_id_val, reg_info = [], "cpuUsage", ""
    for dev, path in entries:
        d = np.load(path, allow_pickle=True)
        metric_id_val = str(d["metric_id"])
        reg_info = f"{d['reg_type']} intensity={d['intensity']}"
        device_data.append((dev, d["baseline"], d["regression"]))
    plot_multi_device_comparison(
        device_data, metric_id_val,
        f"{exp_id}  ({reg_info})",
        figs_dir / f"comparison_{exp_id}.png",
    )
EOF

echo ""
echo "Done. Figures in $FIGS_DIR"
