# Regression-detection experiments (Chapter 5)

Internal helpers (imported by scripts below) live in `../helpers/`.

---

### `run_release_pair_experiments.py`
Main experiment driver. Builds baseline + regressed APK pairs, installs them,
collects metrics, waits for the detector, and writes one CSV row per experiment.

```bash
# Full matrix on one device (~12 h at 15 min/version)
python3 run_release_pair_experiments.py --project-id <uuid> --device PerfX_Medium

# Quick smoke test — one experiment (~30 min)
python3 run_release_pair_experiments.py \
    --project-id <uuid> --device PerfX_Medium --experiments e1_cpu_high
```

Run once per device. Results → `results/`. Figures → `figs/`.

---

### `threshold_sweep.py` — E3
Re-evaluates the detector at thresholds 5 %–50 % using `delta_pct` values
already in the run CSVs (no database queries needed).
Output → `../results/release_pair/summary_e3.csv`.

```bash
python3 threshold_sweep.py
```

### `publish_figs.sh`
Re-generates all summary CSVs and PNGs from existing run data without
re-running experiments. Useful after tweaking a plot style.

```bash
./publish_figs.sh
```

### `clear_project_metrics.sh`
Deletes all ClickHouse metric records for a given project. Useful for resetting
state between experiment runs.

```bash
./clear_project_metrics.sh <project-id>
```
