#!/bin/bash
# SDK Accuracy Measurement Script
# Collects ground truth via adb and SDK-reported values from ClickHouse
# for the same time window, then saves both to CSV for comparison in the notebook.
#
# Usage:
#   ./measure_accuracy.sh <project_id>
#
# Outputs (in results/accuracy/):
#   startup_groundtruth.txt   — TotalTime from am start -W
#   startup_sdk.csv           — appStartup metric from ClickHouse
#   system_groundtruth.csv    — CPU% + PSS polled via adb every 1s
#   cpu_sdk.csv               — cpuUsage metric from ClickHouse
#   ram_sdk.csv               — memoryUsage metric from ClickHouse
#   frames_groundtruth.csv    — per-frame render time from gfxinfo framestats
#   frames_sdk.csv            — frameTime metric from ClickHouse

set -e

PROJECT_ID=${1:-""}
PACKAGE="co.adrianblan.cheddar.debug"
ACTIVITY="co.adrianblan.cheddar.MainActivity"
STARTUP_RUNS=10
DURATION_SECS=60
RESULTS_DIR="$(dirname "$0")/results/accuracy"

CH_HOST="localhost"
CH_PORT="8123"
CH_USER="metrics_user"
CH_PASS="metrics_pass"
CH_DB="metrics"

mkdir -p "$RESULTS_DIR"

# ── helpers ───────────────────────────────────────────────────────────────────

ch_query() {
    curl -s "http://${CH_HOST}:${CH_PORT}/" \
        --data-urlencode "query=$1" \
        -G \
        -d "user=${CH_USER}" \
        -d "password=${CH_PASS}" \
        -d "database=${CH_DB}" \
        -d "default_format=CSV"
}

require_project_id() {
    if [ -z "$PROJECT_ID" ]; then
        echo "ERROR: project_id is required."
        echo "Usage: $0 <project_id>"
        exit 1
    fi
}

check_device() {
    if ! adb get-state > /dev/null 2>&1; then
        echo "ERROR: No device connected via adb."
        exit 1
    fi
}

# ── auto-scroll scenario (same as overhead script) ────────────────────────────

auto_scroll() {
    local pkg=$1
    SCREEN=$(adb shell wm size | awk '{print $NF}')
    WIDTH=$(echo "$SCREEN" | cut -d'x' -f1)
    HEIGHT=$(echo "$SCREEN" | cut -d'x' -f2)
    MID_X=$((WIDTH / 2))
    SCROLL_FROM=$((HEIGHT * 3 / 4))
    SCROLL_TO=$((HEIGHT / 4))

    local tick=0
    while true; do
        PID_CHECK=$(adb shell pidof "$pkg" 2>/dev/null | tr -d '\r')
        [ -z "$PID_CHECK" ] && break
        adb shell input swipe "$MID_X" "$SCROLL_FROM" "$MID_X" "$SCROLL_TO" 400 \
            > /dev/null 2>&1
        sleep 2
        tick=$((tick + 1))
        if [ $((tick % 10)) -eq 0 ]; then
            adb shell input tap "$MID_X" 40 > /dev/null 2>&1
            sleep 1
        fi
    done
}

# ═════════════════════════════════════════════════════════════════════════════
# 1. STARTUP
# ═════════════════════════════════════════════════════════════════════════════

measure_startup() {
    echo ""
    echo "=== Startup accuracy ($STARTUP_RUNS cold starts) ==="

    local gt_file="$RESULTS_DIR/startup_groundtruth.txt"
    echo "startup_ms" > "$gt_file"

    STARTUP_BEGIN=$(date -u +%s)

    for i in $(seq 1 "$STARTUP_RUNS"); do
        adb shell am force-stop "$PACKAGE" > /dev/null
        sleep 1
        TIME=$(adb shell am start -W -n "$PACKAGE/$ACTIVITY" \
               | grep "TotalTime" | awk '{print $2}' | tr -d '\r')
        echo "$TIME" >> "$gt_file"
        echo "  Run $i: ${TIME} ms"
        adb shell am force-stop "$PACKAGE" > /dev/null
        sleep 1
    done

    STARTUP_END=$(date -u +%s)  # used as lower bound for ClickHouse query window

    echo "  Ground truth saved: $gt_file"

    if [ -n "$PROJECT_ID" ]; then
        local sdk_file="$RESULTS_DIR/startup_sdk.csv"
        echo "  Waiting 30s for SDK to flush and upload startup data..."
        sleep 30
        echo "  Fetching SDK startup values from ClickHouse..."
        ch_query "
            SELECT
                toUnixTimestamp(ts) AS timestamp_s,
                value               AS startup_ms
            FROM metric_records
            WHERE
                project_id = '${PROJECT_ID}'
                AND metric_id = 'appStartup'
                AND ts >= toDateTime(${STARTUP_BEGIN})
                AND ts <= now()
            ORDER BY ts
        " > "$sdk_file"
        echo "  SDK values saved:   $sdk_file"
    fi
}

# ═════════════════════════════════════════════════════════════════════════════
# 2. CPU + RAM  (polled every 1s via adb, compared to SDK cpuUsage/memoryUsage)
# ═════════════════════════════════════════════════════════════════════════════

measure_system() {
    echo ""
    echo "=== CPU + RAM accuracy ($DURATION_SECS seconds) ==="

    adb shell am force-stop "$PACKAGE" > /dev/null
    sleep 1
    adb shell am start -n "$PACKAGE/$ACTIVITY" > /dev/null
    sleep 4

    auto_scroll "$PACKAGE" &
    SCROLL_PID=$!
    trap 'kill $SCROLL_PID 2>/dev/null; adb shell am force-stop '"$PACKAGE"' > /dev/null' EXIT

    local gt_file="$RESULTS_DIR/system_groundtruth.csv"
    echo "timestamp_s,cpu_pct,pss_kb" > "$gt_file"

    SYSTEM_BEGIN=$(date -u +%s)

    for i in $(seq 1 "$DURATION_SECS"); do
        TS=$((SYSTEM_BEGIN + i - 1))

        PID=$(adb shell pidof "$PACKAGE" 2>/dev/null | tr -d '\r')
        if [ -z "$PID" ]; then
            sleep 1
            continue
        fi

        STAT1=$(adb shell cat /proc/"$PID"/stat 2>/dev/null | tr -d '\r')
        UPTIME1=$(adb shell cat /proc/uptime 2>/dev/null | awk '{print $1}')
        sleep 1
        STAT2=$(adb shell cat /proc/"$PID"/stat 2>/dev/null | tr -d '\r')
        UPTIME2=$(adb shell cat /proc/uptime 2>/dev/null | awk '{print $1}')

        UTIME1=$(echo "$STAT1" | awk '{print $14}')
        STIME1=$(echo "$STAT1" | awk '{print $15}')
        UTIME2=$(echo "$STAT2" | awk '{print $14}')
        STIME2=$(echo "$STAT2" | awk '{print $15}')

        CPU_TICKS=$(( (UTIME2 + STIME2) - (UTIME1 + STIME1) ))
        WALL_TICKS=$(echo "$UPTIME2 $UPTIME1" | awk '{printf "%.0f", ($1-$2)*100}')
        if [ "$WALL_TICKS" -gt 0 ]; then
            CPU=$(echo "$CPU_TICKS $WALL_TICKS" | awk '{printf "%.2f", $1/$2*100}')
        else
            CPU="0.00"
        fi

        PSS=$(adb shell cat /proc/"$PID"/smaps_rollup 2>/dev/null \
              | grep "^Pss:" | awk '{print $2}')
        if [ -z "$PSS" ] || [ "$PSS" = "0" ]; then
            PSS=$(adb shell dumpsys meminfo "$PACKAGE" 2>/dev/null \
                  | grep -E "(TOTAL PSS:|^[ ]*TOTAL[ ]+[0-9])" \
                  | head -1 | grep -oE '[0-9]+' | head -1)
        fi
        PSS=${PSS:-0}

        echo "$TS,$CPU,$PSS" >> "$gt_file"
        echo "  t=${i}s  CPU=${CPU}%  PSS=${PSS}KB"
    done

    kill $SCROLL_PID 2>/dev/null
    trap - EXIT

    echo "  Ground truth saved: $gt_file"

    if [ -n "$PROJECT_ID" ]; then
        echo "  Waiting 3 seconds for SDK to flush and upload system data..."
        sleep 3
        echo "  Fetching SDK CPU values from ClickHouse (window: ${SYSTEM_BEGIN} → now)..."
        ch_query "
            SELECT
                toUnixTimestamp(ts) AS timestamp_s,
                value               AS cpu_pct
            FROM metric_records
            WHERE
                project_id = '${PROJECT_ID}'
                AND metric_id = 'cpuUsage'
                AND ts >= toDateTime(${SYSTEM_BEGIN})
                AND ts <= now()
            ORDER BY ts
        " > "$RESULTS_DIR/cpu_sdk.csv"
        echo "  cpu_sdk.csv: $(wc -l < "$RESULTS_DIR/cpu_sdk.csv") rows"

        echo "  Fetching SDK RAM values from ClickHouse..."
        ch_query "
            SELECT
                toUnixTimestamp(ts) AS timestamp_s,
                value               AS ram_mb
            FROM metric_records
            WHERE
                project_id = '${PROJECT_ID}'
                AND metric_id = 'memoryUsage'
                AND ts >= toDateTime(${SYSTEM_BEGIN})
                AND ts <= now()
            ORDER BY ts
        " > "$RESULTS_DIR/ram_sdk.csv"
        echo "  ram_sdk.csv: $(wc -l < "$RESULTS_DIR/ram_sdk.csv") rows"

        echo "  SDK values saved: cpu_sdk.csv, ram_sdk.csv"
    fi

    adb shell am force-stop "$PACKAGE" > /dev/null
}

# ═════════════════════════════════════════════════════════════════════════════
# 3. FRAME TIME  (gfxinfo framestats vs SDK frameTime)
# ═════════════════════════════════════════════════════════════════════════════

measure_frames() {
    echo ""
    echo "=== Frame time accuracy ($DURATION_SECS seconds) ==="

    adb shell am force-stop "$PACKAGE" > /dev/null
    sleep 1
    adb shell dumpsys gfxinfo "$PACKAGE" reset > /dev/null 2>&1
    adb shell am start -n "$PACKAGE/$ACTIVITY" > /dev/null
    sleep 4

    auto_scroll "$PACKAGE" &
    SCROLL_PID=$!
    trap 'kill $SCROLL_PID 2>/dev/null; adb shell am force-stop '"$PACKAGE"' > /dev/null' EXIT

    FRAMES_BEGIN=$(date -u +%s)
    echo "  Scrolling for $DURATION_SECS seconds..."
    sleep "$DURATION_SECS"
    kill $SCROLL_PID 2>/dev/null
    trap - EXIT

    echo "  Pulling framestats..."
    local raw_file="$RESULTS_DIR/frames_raw.txt"
    local gt_file="$RESULTS_DIR/frames_groundtruth.csv"

    adb shell dumpsys gfxinfo "$PACKAGE" framestats > "$raw_file"

    # Parse framestats: columns are nanosecond timestamps
    # frame_ms = (FrameCompleted - IntendedVsync) / 1e6
    # Header: Flags(1),FrameTimelineVsyncId(2),IntendedVsync(3),...,FrameCompleted(17)
    echo "frame_ms" > "$gt_file"
    awk -F',' '
        /^---PROFILEDATA---/ { in_data=1; next }
        /^Flags,/            { next }
        in_data && NF >= 17 && $1 == 0 {
            frame_ms = ($17 - $3) / 1000000.0
            if (frame_ms > 0 && frame_ms < 2000)
                printf "%.3f\n", frame_ms
        }
    ' "$raw_file" >> "$gt_file"

    FRAME_COUNT=$(wc -l < "$gt_file")
    echo "  Captured $((FRAME_COUNT - 1)) frames → $gt_file"

    if [ -n "$PROJECT_ID" ]; then
        echo "  Waiting 3s for SDK to flush and upload frame data..."
        sleep 3
        echo "  Fetching SDK frame time values from ClickHouse..."
        ch_query "
            SELECT
                toUnixTimestamp(ts) AS timestamp_s,
                value               AS frame_ms
            FROM metric_records
            WHERE
                project_id = '${PROJECT_ID}'
                AND metric_id = 'frameTime'
                AND ts >= toDateTime(${FRAMES_BEGIN})
                AND ts <= now()
            ORDER BY ts
        " > "$RESULTS_DIR/frames_sdk.csv"
        echo "  SDK values saved: frames_sdk.csv"
    fi

    adb shell am force-stop "$PACKAGE" > /dev/null
}

# ═════════════════════════════════════════════════════════════════════════════
# main
# ═════════════════════════════════════════════════════════════════════════════

check_device
require_project_id

echo "Project ID: $PROJECT_ID"
echo "Verifying ClickHouse connectivity..."
CH_CHECK=$(curl -s "http://${CH_HOST}:${CH_PORT}/" \
    -G \
    --data-urlencode "query=SELECT count() FROM metric_records WHERE project_id = '${PROJECT_ID}'" \
    -d "user=${CH_USER}" \
    -d "password=${CH_PASS}" \
    -d "database=${CH_DB}" \
    -d "default_format=CSV")
if [ -z "$CH_CHECK" ]; then
    echo "ERROR: ClickHouse not reachable at ${CH_HOST}:${CH_PORT}"
    exit 1
fi
echo "  ClickHouse OK — project has ${CH_CHECK} existing records"

# measure_startup
measure_system
measure_frames

echo ""
echo "=== Done. Results in $RESULTS_DIR ==="
ls -1 "$RESULTS_DIR/"
echo ""
echo "Open overhead_analysis.ipynb and point it at results/accuracy/ to compare."
