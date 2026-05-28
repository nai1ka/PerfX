#!/bin/bash
# Run the SDK overhead measurement on a named AVD.
# Usage: ./run_overhead.sh <avd-name>
# Example: ./run_overhead.sh PerfX_Low
#
# Results are saved to results/<avd-name>/.

# ── argument ──────────────────────────────────────────────────────────────────
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <avd-name>"
    echo "Available AVDs:"
    ~/Library/Android/sdk/emulator/emulator -list-avds 2>/dev/null | sed 's/^/  /'
    exit 1
fi

AVD="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EVAL_DIR="$(dirname "$SCRIPT_DIR")"          # evaluation/ root
RESULTS_DIR="$EVAL_DIR/results/$AVD"
EMULATOR=~/Library/Android/sdk/emulator/emulator

# ── verify the AVD exists ─────────────────────────────────────────────────────
if ! "$EMULATOR" -list-avds 2>/dev/null | grep -qx "$AVD"; then
    echo "ERROR: AVD '$AVD' not found."
    echo "Available AVDs:"
    "$EMULATOR" -list-avds 2>/dev/null | sed 's/^/  /'
    exit 1
fi

echo "========================================"
echo "  AVD        : $AVD"
echo "  Results dir: $RESULTS_DIR"
echo "========================================"

# ── launch emulator ───────────────────────────────────────────────────────────
EMULATOR_LOG="/tmp/emulator_${AVD}.log"

echo ""
echo "=== Launching emulator '$AVD' (log: $EMULATOR_LOG) ==="
"$EMULATOR" -avd "$AVD" \
    -no-snapshot \
    -gpu host \
    -dns-server 8.8.8.8 \
    -no-boot-anim \
    -no-audio \
    -skin 1080x1920 \
    > "$EMULATOR_LOG" 2>&1 &

# ── wait for full boot ────────────────────────────────────────────────────────
echo "Waiting for device to connect..."
adb wait-for-device

echo "Waiting for boot to complete..."
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do
    sleep 3
done
echo "Device ready."
sleep 3   # brief pause so the launcher finishes drawing

# ── run noSdk flavor ──────────────────────────────────────────────────────────
echo ""
echo "=== Running noSdk measurement ==="
"$EVAL_DIR/measure/measure_overhead.sh" noSdk

# ── run withSdk flavor ────────────────────────────────────────────────────────
echo ""
echo "=== Running withSdk measurement ==="
"$EVAL_DIR/measure/measure_overhead.sh" withSdk

# ── save results ──────────────────────────────────────────────────────────────
echo ""
echo "=== Saving results to $RESULTS_DIR ==="
mkdir -p "$RESULTS_DIR"
cp "$EVAL_DIR/results/noSdk.csv" \
   "$EVAL_DIR/results/withSdk.csv" \
   "$EVAL_DIR/results/noSdk_startup.txt" \
   "$EVAL_DIR/results/withSdk_startup.txt" \
   "$RESULTS_DIR/"

echo ""
echo "========================================"
echo "  Done. Results saved to:"
echo "  $RESULTS_DIR"
echo "========================================"
