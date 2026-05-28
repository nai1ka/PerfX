#!/bin/bash
# End-to-end regression-detection experiment runner.
#
# Usage: ./run_regression_full.sh [options]
#
# Options (all optional):
#   --serial <id>          adb device serial (default: ANDROID_SERIAL or first connected device)
#   --types  <list>        comma-separated regression types  (default: cpu,memory,ui)
#   --intensities <list>   comma-separated intensity levels  (default: 1,2,3)
#   --reps   <n>           repetitions per (type,intensity)  (default: 1)
#   --controls <n>         number of control runs            (default: 3)
#   --baseline <secs>      baseline window length            (default: 90)
#   --current  <secs>      current window length             (default: 90)
#   --no-backend           skip docker compose (backend already running)
#   --no-build             skip Gradle build + install
#   --no-deps              skip pip install

set -euo pipefail

# ── paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EVAL_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$(dirname "$EVAL_DIR")")"
ANDROID_DIR="$REPO_ROOT/Android/PerfX"
BACKEND_DIR="$REPO_ROOT/Backend"
ANALYSIS_DIR="$REPO_ROOT/Analysis"
VENV="$ANALYSIS_DIR/.venv"
PYTHON="$VENV/bin/python3"
PROJECT_ID="ce96511b-500e-407e-ab9c-9d7a6c966dc5"

# ── defaults ──────────────────────────────────────────────────────────────────
SERIAL="${ANDROID_SERIAL:-}"
TYPES="cpu,memory,ui"
INTENSITIES="1,2,3"
REPS=1
CONTROLS=5
BASELINE=40
CURRENT=30
RUN_BACKEND=true
RUN_BUILD=true
RUN_DEPS=true

# ── argument parsing ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --serial)      SERIAL="$2";      shift 2 ;;
        --types)       TYPES="$2";       shift 2 ;;
        --intensities) INTENSITIES="$2"; shift 2 ;;
        --reps)        REPS="$2";        shift 2 ;;
        --controls)    CONTROLS="$2";    shift 2 ;;
        --baseline)    BASELINE="$2";    shift 2 ;;
        --current)     CURRENT="$2";     shift 2 ;;
        --no-backend)  RUN_BACKEND=false; shift ;;
        --no-build)    RUN_BUILD=false;   shift ;;
        --no-deps)     RUN_DEPS=false;    shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── helpers ───────────────────────────────────────────────────────────────────
step() { echo; echo "=== $* ==="; }
die()  { echo "ERROR: $*" >&2; exit 1; }

# ── prerequisite checks ───────────────────────────────────────────────────────
step "Checking prerequisites"

command -v adb    >/dev/null 2>&1 || die "adb not found — install Android SDK platform-tools"
command -v docker >/dev/null 2>&1 || die "docker not found"
[[ -x "$PYTHON" ]]                || die "venv Python not found at $PYTHON — run: cd Analysis && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"

# ── adb device ────────────────────────────────────────────────────────────────
step "Checking adb device"

if [[ -n "$SERIAL" ]]; then
    adb -s "$SERIAL" get-state >/dev/null 2>&1 || die "Device '$SERIAL' not connected"
    echo "Using device: $SERIAL"
else
    DEVICE_COUNT=$(adb devices | tail -n +2 | grep -c "device$" || true)
    [[ "$DEVICE_COUNT" -ge 1 ]] || die "No adb device connected. Start an emulator or plug in a device."
    [[ "$DEVICE_COUNT" -eq 1 ]] || echo "WARNING: multiple devices connected — adb will pick one. Use --serial to be explicit."
    echo "Device ready."
fi

# ── backend ───────────────────────────────────────────────────────────────────
if $RUN_BACKEND; then
    step "Starting backend (docker compose)"
    docker compose -f "$BACKEND_DIR/docker-compose.yml" up -d --build

    echo "Waiting for backend health check at http://localhost:8080/health ..."
    for i in $(seq 1 30); do
        if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
            echo "Backend is up."
            break
        fi
        [[ $i -eq 30 ]] && die "Backend did not become healthy after 60s"
        sleep 2
    done
else
    echo "Skipping backend start (--no-backend)."
    curl -sf http://localhost:8080/health >/dev/null 2>&1 || die "Backend not reachable at localhost:8080"
fi

# ── pip deps ──────────────────────────────────────────────────────────────────
if $RUN_DEPS; then
    step "Installing Python dependencies"
    "$VENV/bin/pip" install -q -r "$ANALYSIS_DIR/requirements.txt"
else
    echo "Skipping pip install (--no-deps)."
fi

# ── build + install ───────────────────────────────────────────────────────────
if $RUN_BUILD; then
    step "Building and installing demo app (withSdk flavor)"
    ADB_SERIAL_ENV=""
    [[ -n "$SERIAL" ]] && ADB_SERIAL_ENV="ANDROID_SERIAL=$SERIAL"
    (cd "$ANDROID_DIR" && env $ADB_SERIAL_ENV ./gradlew :demo:installWithSdkDebug)
else
    echo "Skipping build (--no-build)."
fi

# ── estimate runtime ──────────────────────────────────────────────────────────
step "Starting regression experiments"
N_TYPES=$(echo "$TYPES" | tr ',' '\n' | wc -l | tr -d ' ')
N_INT=$(echo "$INTENSITIES" | tr ',' '\n' | wc -l | tr -d ' ')
TOTAL_RUNS=$(( N_TYPES * N_INT * REPS + CONTROLS ))
RUN_SECS=$(( BASELINE + CURRENT + 30 ))
TOTAL_MINS=$(( TOTAL_RUNS * RUN_SECS / 60 ))

echo "Experiment matrix:"
echo "  types=$TYPES  intensities=$INTENSITIES  reps=$REPS  controls=$CONTROLS"
echo "  baseline=${BASELINE}s  current=${CURRENT}s  (+30s flush margin per run)"
echo "  Total runs: $TOTAL_RUNS  (~${TOTAL_MINS} min)"

# ── run ───────────────────────────────────────────────────────────────────────
SERIAL_ARG=""
[[ -n "$SERIAL" ]] && SERIAL_ARG="--serial $SERIAL"

"$PYTHON" "$SCRIPT_DIR/run_regression_experiments.py" \
    --project-id "$PROJECT_ID" \
    --types       "$TYPES" \
    --intensities "$INTENSITIES" \
    --reps        "$REPS" \
    --controls    "$CONTROLS" \
    --baseline    "$BASELINE" \
    --current     "$CURRENT" \
    $SERIAL_ARG

# ── done ──────────────────────────────────────────────────────────────────────
echo
echo "========================================"
echo "  Results: Android/evaluation/results/regression/runs.csv"
echo "  Next:    open Android/evaluation/analysis/regression_analysis.ipynb"
echo "========================================"
