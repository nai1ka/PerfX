#!/bin/bash
# SDK Overhead Measurement Script
# Usage:
#   ./measure_overhead.sh [withSdk|noSdk] [--build] [options]
#
#   withSdk|noSdk      flavor to install and measure (default: withSdk)
#   --build            build the flavor APK first; without it the script
#                      reuses the already-built APK and only installs it
#   --app-dir PATH     host-app project directory (default: Cheddar)
#   --package NAME     application id of the installed app
#   --activity NAME    launch activity
#
# Results saved to results/withSdk.csv and results/noSdk.csv.
# Run both flavors, then analyse in overhead_analysis.ipynb.

set -e

FLAVOR="withSdk"
DO_BUILD=false
APP_DIR="/Users/nai1ka/Projects/Cheddar"
PACKAGE="co.adrianblan.cheddar.debug"
ACTIVITY="co.adrianblan.cheddar.MainActivity"

while [[ $# -gt 0 ]]; do
    case "$1" in
        withSdk|noSdk) FLAVOR="$1"; shift ;;
        --build)       DO_BUILD=true; shift ;;
        --app-dir)     APP_DIR="$2"; shift 2 ;;
        --package)     PACKAGE="$2"; shift 2 ;;
        --activity)    ACTIVITY="$2"; shift 2 ;;
        -h|--help)     grep '^#' "$0" | sed 's/^#\{1,2\} \{0,1\}//'; exit 0 ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

DURATION_SECS=90
RESULTS_DIR="$(cd "$(dirname "$0")/.." && pwd)/results"
OUTPUT="$RESULTS_DIR/${FLAVOR}.csv"
STARTUP_OUTPUT="$RESULTS_DIR/${FLAVOR}_startup.txt"

mkdir -p "$RESULTS_DIR"

# ── check device connected ──────────────────────────────────────────────────
if ! adb get-state > /dev/null 2>&1; then
    echo "ERROR: No device connected via adb."
    exit 1
fi

# ── build APK (optional) ────────────────────────────────────────────────────
APK_PATH="$APP_DIR/app/build/outputs/apk/${FLAVOR}/debug/app-${FLAVOR}-debug.apk"
if [ "$DO_BUILD" = true ]; then
    echo "=== Building $FLAVOR debug APK ==="
    FLAVOR_CAP="$(echo "${FLAVOR:0:1}" | tr '[:lower:]' '[:upper:]')${FLAVOR:1}"
    cd "$APP_DIR"
    ./gradlew ":app:assemble${FLAVOR_CAP}Debug" --quiet
    cd - > /dev/null
fi

if [ ! -f "$APK_PATH" ]; then
    echo "APK not found at: $APK_PATH"
    echo "Pass --build to build it first."
    exit 1
fi

echo "=== Installing $FLAVOR APK ==="
adb install -r "$APK_PATH"

# ── startup time (10 cold starts) ──────────────────────────────────────────
echo ""
echo "=== Measuring startup time (10 cold starts) ==="
echo "startup_ms" > "$STARTUP_OUTPUT"

for i in $(seq 1 20); do
    adb shell am force-stop "$PACKAGE" > /dev/null
    sleep 1
    TIME=$(adb shell am start -W -n "$PACKAGE/$ACTIVITY" \
           | grep "TotalTime" | awk '{print $2}')
    echo "$TIME" >> "$STARTUP_OUTPUT"
    echo "  Run $i: ${TIME} ms"
done

# ── auto-scroll worker ─────────────────────────────────────────────────────
# Runs in background: scrolls down every 2s, taps back to top every 20s
auto_scroll() {
    local pkg=$1
    # get screen dimensions once
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

        # scroll down
        adb shell input swipe "$MID_X" "$SCROLL_FROM" "$MID_X" "$SCROLL_TO" 400 \
            > /dev/null 2>&1
        sleep 2

        tick=$((tick + 1))
        # every 20s (~10 swipes) tap the status bar to scroll back to top
        if [ $((tick % 10)) -eq 0 ]; then
            adb shell input tap "$MID_X" 40 > /dev/null 2>&1
            sleep 1
        fi
    done
}

# ── CPU and memory over time ────────────────────────────────────────────────
echo ""
echo "=== Starting app for CPU/memory measurement ($DURATION_SECS seconds) ==="
echo "Auto-scrolling the feed via adb..."
echo ""

adb shell am force-stop "$PACKAGE" > /dev/null
sleep 1
adb shell am start -n "$PACKAGE/$ACTIVITY" > /dev/null
sleep 4  # wait for feed to load

# start auto-scroll in background
auto_scroll "$PACKAGE" &
SCROLL_PID=$!
disown   # untrack the job so the shell stays quiet when it is killed below
trap 'kill $SCROLL_PID 2>/dev/null' EXIT

echo "timestamp_s,cpu_pct,pss_kb,java_heap_kb" > "$OUTPUT"

for i in $(seq 1 "$DURATION_SECS"); do
    TS=$i

    PID=$(adb shell pidof "$PACKAGE" 2>/dev/null | tr -d '\r')
    if [ -z "$PID" ]; then
        echo "  Warning: app process not found at second $i"
        sleep 1
        continue
    fi

    # CPU: two /proc/<pid>/stat readings 1s apart
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

    # Memory: PSS via /proc/<pid>/smaps_rollup (reliable on API 28+)
    PSS=$(adb shell cat /proc/"$PID"/smaps_rollup 2>/dev/null \
          | grep "^Pss:" | awk '{print $2}')
    # Fallback: dumpsys meminfo — handles "TOTAL PSS:" and "TOTAL:" formats
    if [ -z "$PSS" ] || [ "$PSS" = "0" ]; then
        MEMINFO=$(adb shell dumpsys meminfo "$PACKAGE" 2>/dev/null)
        PSS=$(echo "$MEMINFO" \
              | grep -E "(TOTAL PSS:|^[ ]*TOTAL[ ]+[0-9])" \
              | head -1 | grep -oE '[0-9]+' | head -1)
    fi
    PSS=${PSS:-0}

    # Java heap: from /proc/<pid>/status (VmRSS is close enough without root)
    JAVA=$(adb shell cat /proc/"$PID"/status 2>/dev/null \
           | grep "^VmRSS:" | awk '{print $2}')
    JAVA=${JAVA:-0}

    echo "$TS,$CPU,$PSS,$JAVA" >> "$OUTPUT"
    echo "  t=${TS}s  CPU=${CPU}%  PSS=${PSS}KB  VmRSS=${JAVA}KB"
done

kill $SCROLL_PID 2>/dev/null
adb shell am force-stop "$PACKAGE" > /dev/null

adb shell am force-stop "$PACKAGE" > /dev/null

echo ""
echo "Done. Results:"
echo "  $OUTPUT"
echo "  $STARTUP_OUTPUT"
echo ""
echo "Run both flavors, then: python3 analyze_overhead.py"
