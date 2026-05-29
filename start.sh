#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# PerfX — start the whole system via Docker Compose
#
# Usage:
#   ./start.sh                   # build & start everything
#   ./start.sh --fresh           # wipe volumes first (fresh DB), then start
#   ./start.sh --with-detector   # also start the regression detector locally
#   ./start.sh --logs            # stream compose logs after startup
#   ./start.sh --help
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
fatal()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; exit 1; }

# ── Arguments ─────────────────────────────────────────────────────────────────

FRESH=false
WITH_DETECTOR=false
STREAM_LOGS=false

for arg in "$@"; do
  case "$arg" in
    --fresh)          FRESH=true ;;
    --with-detector)  WITH_DETECTOR=true ;;
    --logs)           STREAM_LOGS=true ;;
    --help|-h)
      sed -n '2,10p' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) fatal "Unknown argument: $arg" ;;
  esac
done

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYSIS_DIR="$REPO/Analysis"

# ── Prerequisite checks ───────────────────────────────────────────────────────

command -v docker &>/dev/null || fatal "'docker' not found."
docker info &>/dev/null       || fatal "Docker daemon is not running."

if docker compose version &>/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose &>/dev/null; then
  DC="docker-compose"
else
  fatal "Neither 'docker compose' nor 'docker-compose' found."
fi

# ── Cleanup on exit ───────────────────────────────────────────────────────────

DETECTOR_PID=""
OLD_STTY=""

restore_tty() {
  [[ -n "$OLD_STTY" ]] && stty "$OLD_STTY" 2>/dev/null || true
}

cleanup() {
  restore_tty
  echo ""
  if [[ -n "$DETECTOR_PID" ]]; then
    info "Stopping detector (PID $DETECTOR_PID)…"
    kill "$DETECTOR_PID" 2>/dev/null || true
  fi
  info "Stopping Docker services…"
  (cd "$REPO" && $DC down) 2>/dev/null || true
  success "All services stopped."
}

trap cleanup INT TERM EXIT

# ── 1. Optionally wipe volumes ────────────────────────────────────────────────

echo ""
echo -e "${BOLD}━━━ PerfX System Launcher ━━━${RESET}"
echo ""

if $FRESH; then
  warn "--fresh: removing existing Docker volumes…"
  (cd "$REPO" && $DC down -v --remove-orphans 2>/dev/null || true)
  success "Volumes cleared."
fi

# ── 2. Build & start all containers ──────────────────────────────────────────

info "Building & starting containers (Postgres, ClickHouse, Ktor, Streamlit)…"
(cd "$REPO" && $DC up --build -d)

# ── 3. Wait for backend ───────────────────────────────────────────────────────

info "Waiting for backend on :8080…"
TIMEOUT=180
ELAPSED=0
until curl -sf http://localhost:8080/health &>/dev/null; do
  if (( ELAPSED >= TIMEOUT )); then
    echo ""
    fatal "Backend did not become healthy within ${TIMEOUT}s.\n  Check logs:  $DC logs ktor-app"
  fi
  printf "."
  sleep 3
  ELAPSED=$(( ELAPSED + 3 ))
done
echo ""
success "Backend healthy."

# ── 4. Wait for frontend ──────────────────────────────────────────────────────

info "Waiting for frontend on :8501…"
ELAPSED=0
until curl -sf http://localhost:8501/_stcore/health &>/dev/null; do
  if (( ELAPSED >= TIMEOUT )); then
    echo ""
    fatal "Frontend did not become healthy within ${TIMEOUT}s.\n  Check logs:  $DC logs frontend"
  fi
  printf "."
  sleep 3
  ELAPSED=$(( ELAPSED + 3 ))
done
echo ""
success "Frontend healthy."

# ── 5. Optional: regression detector (local Python) ──────────────────────────

if $WITH_DETECTOR; then
  command -v python3 &>/dev/null || fatal "'python3' not found (needed for detector)."
  info "Installing detector dependencies…"
  python3 -m pip install -q -r "$ANALYSIS_DIR/requirements.txt"

  mkdir -p "$REPO/logs"
  info "Starting regression detector…"
  python3 "$ANALYSIS_DIR/regression_detector.py" > "$REPO/logs/detector.log" 2>&1 &
  DETECTOR_PID=$!
  sleep 2
  if ! kill -0 "$DETECTOR_PID" 2>/dev/null; then
    warn "Detector crashed immediately. See $REPO/logs/detector.log"
    DETECTOR_PID=""
  else
    success "Detector running (PID $DETECTOR_PID) → $REPO/logs/detector.log"
  fi
fi

# ── 6. Summary ────────────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}━━━ All services are up ━━━${RESET}"
echo ""
echo -e "  ${GREEN}●${RESET} Dashboard    →  ${CYAN}http://localhost:8501${RESET}"
echo -e "  ${GREEN}●${RESET} Backend API  →  ${CYAN}http://localhost:8080${RESET}"
echo -e "  ${GREEN}●${RESET} ClickHouse   →  ${CYAN}http://localhost:8123${RESET}"
echo -e "  ${GREEN}●${RESET} Postgres     →  ${CYAN}localhost:5432${RESET}  (perfx / perfx_user / perfx_pass)"
[[ -n "$DETECTOR_PID" ]] && \
  echo -e "  ${GREEN}●${RESET} Detector     →  log: ${CYAN}$REPO/logs/detector.log${RESET}"
echo ""
echo -e "  Useful commands:"
echo -e "    ${YELLOW}$DC logs -f${RESET}           # all container logs"
echo -e "    ${YELLOW}$DC logs -f frontend${RESET}  # frontend only"
echo -e "    ${YELLOW}$DC ps${RESET}                # container status"
echo ""

# ── 7. Interactive key loop (or plain log stream) ─────────────────────────────

if $STREAM_LOGS; then
  echo -e "  Press ${BOLD}Ctrl-C${RESET} to stop everything."
  echo ""
  (cd "$REPO" && $DC logs -f)

elif [[ -t 0 ]]; then
  # stdin is a terminal — enable single-keypress hotkeys
  OLD_STTY=$(stty -g)
  stty -echo -icanon min 0 time 0   # raw mode, non-blocking

  echo -e "  Hotkeys:  ${BOLD}[f]${RESET} rebuild+restart frontend  ${BOLD}[b]${RESET} rebuild+restart backend" \
          "  ${BOLD}[r]${RESET} rebuild+restart detector  ${BOLD}[l]${RESET} stream logs  ${BOLD}[q]${RESET} quit"
  echo ""

  while true; do
    key=""
    IFS= read -r -t 2 -n 1 key 2>/dev/null || true

    case "$key" in
      f|F)
        restore_tty
        echo ""
        info "Rebuilding & restarting frontend…"
        (cd "$REPO" && $DC up --build -d frontend)
        success "Frontend rebuilt and restarted."
        stty -echo -icanon min 0 time 0
        ;;
      b|B)
        restore_tty
        echo ""
        info "Rebuilding & restarting backend…"
        (cd "$REPO" && $DC up --build -d ktor-app)
        success "Backend rebuilt and restarted."
        stty -echo -icanon min 0 time 0
        ;;
      r|R)
        restore_tty
        echo ""
        info "Rebuilding & restarting detector…"
        (cd "$REPO" && $DC up --build -d detector)
        success "Detector rebuilt and restarted."
        stty -echo -icanon min 0 time 0
        ;;
      l|L)
        restore_tty
        echo ""
        info "Streaming logs — press Ctrl-C to return to hotkey mode…"
        (cd "$REPO" && $DC logs -f) || true
        OLD_STTY=$(stty -g)
        stty -echo -icanon min 0 time 0
        ;;
      q|Q)
        break
        ;;
    esac
  done

else
  # Non-interactive (pipe / CI) — just keep alive
  echo -e "  Press ${BOLD}Ctrl-C${RESET} to stop everything."
  echo ""
  while true; do sleep 60; done
fi
