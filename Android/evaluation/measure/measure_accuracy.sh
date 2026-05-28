#!/bin/bash
# SDK Accuracy Measurement Script
# Collects ground truth metrics from the device via adb.
# SDK-side data is fetched and compared separately in accuracy_analysis.ipynb.
#
# Usage:
#   ./measure_accuracy.sh [--build] [options]
#
#   --build            build the withSdk APK first; without it the script
#                      reuses the already-built APK and only installs it
#   --app-dir PATH     host-app project directory (default: Cheddar)
#   --package NAME     application id of the installed app
#   --activity NAME    launch activity
#
# Outputs (in results/accuracy/):
#   startup_groundtruth.csv   — timestamp_s,startup_ms  (one row per cold start)
#   system_groundtruth.csv    — timestamp_s,cpu_pct,pss_kb  (one row per second)
#   frames_groundtruth.csv    — timestamp_s,frame_ms  (one row per frame)

set -e

DO_BUILD=false
APP_DIR="/Users/nai1ka/Projects/Cheddar"
PACKAGE="co.adrianblan.cheddar.debug"
ACTIVITY="co.adrianblan.cheddar.MainActivity"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --build)    DO_BUILD=true; shift ;;
        --app-dir)  APP_DIR="$2"; shift 2 ;;
        --package)  PACKAGE="$2"; shift 2 ;;
        --activity) ACTIVITY="$2"; shift 2 ;;
        -h|--help)  grep '^#' "$0" | sed 's/^#\{1,2\} \{0,1\}//'; exit 0 ;;
        *)          echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

STARTUP_RUNS=10
DURATION_SECS=60
RESULTS_DIR="$(cd "$(dirname "$0")/.." && pwd)/results/accuracy"

mkdir -p "$RESULTS_DIR"

# ── check device connected ────────────────────────────────────────────────────
if ! adb get-state > /dev/null 2>&1; then
    echo "ERROR: No device connected via adb."
    exit 1
fi

# ── build + install the withSdk APK ──────────────────────────────────────────
APK_PATH="$APP_DIR/app/build/outputs/apk/withSdk/debug/app-withSdk-debug.apk"
if [ "$DO_BUILD" = true ]; then
    echo "=== Building withSdk debug APK ==="
    cd "$APP_DIR"
    ./gradlew ":app:assembleWithSdkDebug" --quiet
    cd - > /dev/null
fi

if [ ! -f "$APK_PATH" ]; then
    echo "APK not found at: $APK_PATH"
    echo "Pass --build to build it first."
    exit 1
fi

echo "=== Installing withSdk APK ==="
adb install -r "$APK_PATH"

# ── auto-scroll worker ────────────────────────────────────────────────────────
# Runs in background: scrolls down every 2s, taps back to top every 20s
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
# 1. STARTUP  (cold starts via /proc starttime + logcat Displayed timestamp)
#
# Measurement window matches the SDK exactly:
#   start  = Process.getStartUptimeMillis()  ≈  /proc/<pid>/stat field 22
#   end    = Choreographer vsync after first draw  ≈  ActivityTaskManager: Displayed
#
# Expected residual: ≤ 1 vsync (~16 ms) because the SDK Choreographer callback
# fires one frame after the Displayed event that logcat records.
# ═════════════════════════════════════════════════════════════════════════════

echo ""
echo "=== Startup ground truth ($STARTUP_RUNS cold starts) ==="

GT_STARTUP="$RESULTS_DIR/startup_groundtruth.csv"
echo "timestamp_s,startup_ms" > "$GT_STARTUP"

# One-time constants ──────────────────────────────────────────────────────────
# CLK_TCK: jiffies per second (almost always 100 on Android, but read it properly)
CLK_TCK=$(adb shell getconf CLK_TCK 2>/dev/null | tr -d '\r')
CLK_TCK=${CLK_TCK:-100}

# BOOT_UNIX: Unix epoch of device boot (seconds, floating point).
# Fetched atomically — both values from a single adb call to eliminate skew.
read _Dunix _UPS <<< "$(adb shell 'echo $(date +%s) $(cat /proc/uptime)' \
    | awk '{print $1, $2}' | tr -d '\r')"
BOOT_UNIX=$(echo "$_Dunix $_UPS" | awk '{printf "%.3f", $1 - $2}')

LOGCAT_TMP="/tmp/perfx_logcat_$$.txt"

for i in $(seq 1 "$STARTUP_RUNS"); do
    adb shell am force-stop "$PACKAGE" > /dev/null
    sleep 1

    # Clear logcat buffer and start streaming in background.
    adb logcat -c 2>/dev/null
    adb logcat -v epoch \
        ActivityTaskManager:I ActivityManager:I "*:S" \
        > "$LOGCAT_TMP" 2>/dev/null &
    LOGCAT_PID=$!

    # Launch the app (fire-and-forget — we do NOT wait with -W here).
    adb shell am start -n "$PACKAGE/$ACTIVITY" > /dev/null

    # Poll until the process is visible in /proc (typically < 300 ms).
    APP_PID=""
    for _try in $(seq 1 40); do
        APP_PID=$(adb shell pidof "$PACKAGE" 2>/dev/null | tr -d '\r' | awk '{print $1}')
        [ -n "$APP_PID" ] && break
        sleep 0.1
    done

    if [ -z "$APP_PID" ]; then
        echo "  Run $i: SKIP — process never appeared"
        kill "$LOGCAT_PID" 2>/dev/null
        rm -f "$LOGCAT_TMP"
        continue
    fi

    # Read process start time from /proc/<pid>/stat field 22 (jiffies since boot).
    STAT_LINE=$(adb shell cat /proc/"$APP_PID"/stat 2>/dev/null | tr -d '\r')
    STARTTIME_TICKS=$(echo "$STAT_LINE" | awk '{print $22}')

    if [ -z "$STARTTIME_TICKS" ] || [ "$STARTTIME_TICKS" = "0" ]; then
        echo "  Run $i: SKIP — could not read /proc/$APP_PID/stat"
        kill "$LOGCAT_PID" 2>/dev/null
        rm -f "$LOGCAT_TMP"
        continue
    fi

    # Convert to Unix epoch (floating point seconds).
    PROC_START_UNIX=$(echo "$BOOT_UNIX $STARTTIME_TICKS $CLK_TCK" \
        | awk '{printf "%.3f", $1 + $2/$3}')

    # Wait for ActivityTaskManager: Displayed (or ActivityManager: Displayed)
    # in the logcat stream — up to 15 seconds.
    DISPLAYED_EPOCH=""
    for _wait in $(seq 1 150); do
        DISPLAYED_EPOCH=$(grep -m1 "Displayed.*$PACKAGE" "$LOGCAT_TMP" 2>/dev/null \
            | awk '{print $1}' | tr -d '\r')
        [ -n "$DISPLAYED_EPOCH" ] && break
        sleep 0.1
    done

    kill "$LOGCAT_PID" 2>/dev/null
    rm -f "$LOGCAT_TMP"

    if [ -z "$DISPLAYED_EPOCH" ]; then
        echo "  Run $i: SKIP — Displayed event not found in logcat"
        adb shell am force-stop "$PACKAGE" > /dev/null
        sleep 1
        continue
    fi

    # startup_ms = (displayed_epoch_unix - proc_start_unix) * 1000
    TIME_MS=$(echo "$DISPLAYED_EPOCH $PROC_START_UNIX" \
        | awk '{printf "%.0f", ($1 - $2) * 1000}')

    # Use the Displayed epoch as the run timestamp (same clock as SDK's System.currentTimeMillis()).
    TS=$(echo "$DISPLAYED_EPOCH" | awk '{printf "%d", $1}')

    echo "$TS,$TIME_MS" >> "$GT_STARTUP"
    echo "  Run $i: ${TIME_MS} ms  ts=${TS}  pid=${APP_PID}  proc_start=${PROC_START_UNIX}  displayed=${DISPLAYED_EPOCH}"

    adb shell am force-stop "$PACKAGE" > /dev/null
    sleep 1
done

echo "  Saved: $GT_STARTUP"

# ═════════════════════════════════════════════════════════════════════════════
# 2. CPU + RAM  (polled every 1s via /proc)
# ═════════════════════════════════════════════════════════════════════════════

echo ""
echo "=== CPU + RAM ground truth ($DURATION_SECS seconds) ==="

adb shell am force-stop "$PACKAGE" > /dev/null
sleep 1
adb shell am start -n "$PACKAGE/$ACTIVITY" > /dev/null
sleep 4

auto_scroll "$PACKAGE" &
SCROLL_PID=$!
disown
trap 'kill $SCROLL_PID 2>/dev/null; adb shell am force-stop '"$PACKAGE"' > /dev/null' EXIT

GT_SYSTEM="$RESULTS_DIR/system_groundtruth.csv"
echo "timestamp_s,cpu_pct,pss_kb" > "$GT_SYSTEM"

# Record the start of the window so the notebook can query ClickHouse
# from the right lower bound even before the first GT row is written.
SYSTEM_BEGIN=$(adb shell date +%s | tr -d '\r')
echo "system_begin_s=$SYSTEM_BEGIN" > "$RESULTS_DIR/system_meta.txt"

for i in $(seq 1 "$DURATION_SECS"); do
    # Sample before and after sleep, stamp at the END of the 1-second window.
    # The SDK also stamps at the end of its 500ms interval (System.currentTimeMillis()
    # after delay()), so end-of-window semantics keep both on the same time reference.
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

    # Stamp after the sleep — end of the measurement window, same as SDK
    TS=$(adb shell date +%s | tr -d '\r')
    echo "$TS,$CPU,$PSS" >> "$GT_SYSTEM"
    echo "  t=${i}s  CPU=${CPU}%  PSS=${PSS}KB"
done

kill $SCROLL_PID 2>/dev/null
trap - EXIT
adb shell am force-stop "$PACKAGE" > /dev/null

echo "  Saved: $GT_SYSTEM"

# ═════════════════════════════════════════════════════════════════════════════
# 3. FRAME TIME  (gfxinfo framestats, IntendedVsync deltas)
# ═════════════════════════════════════════════════════════════════════════════

echo ""
echo "=== Frame time ground truth ($DURATION_SECS seconds) ==="

adb shell am force-stop "$PACKAGE" > /dev/null
sleep 1
adb shell am start -n "$PACKAGE/$ACTIVITY" > /dev/null
sleep 4

# Reset gfxinfo after the app has loaded to flush startup frames from the buffer.
adb shell dumpsys gfxinfo "$PACKAGE" reset > /dev/null 2>&1

# Capture BOOT_UNIX once before scrolling starts — both values fetched in a
# single adb call to eliminate host/device clock skew and round-trip race.
read DEVICE_UNIX UPTIME_S <<< "$(adb shell 'echo $(date +%s) $(cat /proc/uptime)' | awk '{print $1, $2}' | tr -d '\r')"
BOOT_UNIX=$(echo "$DEVICE_UNIX $UPTIME_S" | awk '{printf "%d", $1 - $2}')

GT_FRAMES="$RESULTS_DIR/frames_groundtruth.csv"
CHUNK_FILE="/tmp/perfx_frames_chunk.txt"
echo "timestamp_s,frame_ms" > "$GT_FRAMES"

auto_scroll "$PACKAGE" &
SCROLL_PID=$!
disown
trap 'kill $SCROLL_PID 2>/dev/null; adb shell am force-stop '"$PACKAGE"' > /dev/null; rm -f '"$CHUNK_FILE"'' EXIT

# Dump framestats every DUMP_INTERVAL seconds throughout the scroll.
# The gfxinfo buffer holds ~128 frames (~2s at 60 fps); dumping every 2s
# ensures no frames are lost. After each dump the buffer is reset immediately
# so the next chunk starts fresh with no duplicates.
DUMP_INTERVAL=2
ELAPSED=0
TOTAL_FRAMES=0

echo "  Collecting framestats every ${DUMP_INTERVAL}s for ${DURATION_SECS}s..."

while [ "$ELAPSED" -lt "$DURATION_SECS" ]; do
    sleep "$DUMP_INTERVAL"
    ELAPSED=$((ELAPSED + DUMP_INTERVAL))

    adb shell dumpsys gfxinfo "$PACKAGE" framestats > "$CHUNK_FILE" 2>/dev/null
    adb shell dumpsys gfxinfo "$PACKAGE" reset      > /dev/null    2>&1

    # Parse framestats: columns are nanosecond timestamps from SystemClock uptime.
    # Header: Flags(1),FrameTimelineVsyncId(2),IntendedVsync(3),...,FrameCompleted(17)
    # frame_ms    = interval between consecutive IntendedVsync values (matches SDK frameTime)
    # timestamp_s = BOOT_UNIX + IntendedVsync_ns / 1e9
    LINES_BEFORE=$(wc -l < "$GT_FRAMES")
    awk -v boot="$BOOT_UNIX" -F',' '
        /^---PROFILEDATA---/ { in_data=1; prev=0; next }
        /^Flags,/            { next }
        in_data && NF >= 17 && $1 == 0 {
            if (prev > 0) {
                interval_ms = ($3 - prev) / 1000000.0
                ts_s = int(boot + $3 / 1000000000.0)
                if (interval_ms > 0 && interval_ms < 2000)
                    printf "%d,%.3f\n", ts_s, interval_ms
            }
            prev = $3
        }
    ' "$CHUNK_FILE" >> "$GT_FRAMES"
    CHUNK_FRAMES=$(( $(wc -l < "$GT_FRAMES") - LINES_BEFORE ))

    TOTAL_FRAMES=$((TOTAL_FRAMES + CHUNK_FRAMES))
    echo "  t=${ELAPSED}s  +${CHUNK_FRAMES} frames  total=${TOTAL_FRAMES}"
done

kill $SCROLL_PID 2>/dev/null
trap - EXIT
rm -f "$CHUNK_FILE"

adb shell am force-stop "$PACKAGE" > /dev/null

echo "  Total frames captured: $TOTAL_FRAMES"
echo "  Saved: $GT_FRAMES"

# ═════════════════════════════════════════════════════════════════════════════
# done
# ═════════════════════════════════════════════════════════════════════════════

echo ""
echo "=== Done. Ground truth saved to $RESULTS_DIR ==="
ls -1 "$RESULTS_DIR/"
echo ""
echo "Open accuracy_analysis.ipynb, set PROJECT_ID, and run to compare against SDK data."
