#!/usr/bin/env bash
# PRE687: passive and time-scoped SurfaceFlinger present2present measurement.
# Arm before launching NFSMW; the monitor starts after delay then records.
# Only selected NFSMW layer and optional global refresh-rate distribution saved.
set -euo pipefail

APP='io.github.nfsmwrecomp'
RISH="${NFSMW_RISH_PATH:-$HOME/rish}"
OUT_DIR="${NFSMW_PRE687_OUTPUT_DIR:-$HOME/storage/downloads}"
[[ -d "$OUT_DIR" ]] || OUT_DIR="$HOME"
STATE="$HOME/.nfsmw_pre687_worker.pid"
SELF="$(realpath "$0")"

run_rish() {
  [[ -f "$RISH" ]] || { echo "PRE687_RISH_NOT_FOUND=$RISH" >&2; return 3; }
  sh "$RISH" -c "$1"
}

worker() {
  local delay="$1" duration="$2" stamp="$3"
  local output="$OUT_DIR/NFSMW_PRE687_PRESENT2PRESENT_${stamp}.txt"
  local log="$OUT_DIR/NFSMW_PRE687_CAPTURE_${stamp}.status.txt"
  # Keep global timing counters from staying enabled if the worker is interrupted.
  trap 'run_rish "dumpsys SurfaceFlinger --timestats -disable" >/dev/null 2>&1 || true; rm -f "$STATE"' EXIT
  echo "PRE687_STAGE=WAIT_BEFORE_GAMEPLAY delay_seconds=$delay"
  sleep "$delay"
  run_rish 'dumpsys SurfaceFlinger --timestats -clear -enable' >/dev/null
  local started
  started="$(date '+%Y-%m-%dT%H:%M:%S%z')"
  echo "PRE687_STAGE=CAPTURING duration_seconds=$duration"
  sleep "$duration"
  local dump ended
  dump="$(run_rish 'dumpsys SurfaceFlinger --timestats -dump')"
  ended="$(date '+%Y-%m-%dT%H:%M:%S%z')"
  # Do not save the unfiltered system dump. It contains other applications.
  local selected
  selected="$(printf '%s\n' "$dump" | awk -v app="$APP" '
    /^layerName = / {
      active = index($0, "SurfaceView[" app "/") > 0;
      if (active) { print; selected++ }
      histogram_next = 0;
      next;
    }
    active && /^totalFrames = / { print; next }
    active && /^averageFPS = / { print; next }
    active && (/^present2present histogram is as below:/ || /^presentToPresent histogram is as below:/) {
      print; histogram_next=1; next
    }
    active && histogram_next && /^[[:space:]]*[0-9]+ms=/ { print; histogram_next=0; found++; next }
    END { if (selected<1 || found<1) exit 5 }
  ')" || {
    echo 'PRE687_NO_LABELED_PRESENT_TO_PRESENT_HISTOGRAM=TRUE' >&2
    return 5
  }
  {
    echo 'PRE687_NFSMW_SURFACEFLINGER_TIMESTATS'
    echo "PACKAGE=$APP"
    echo "CAPTURE_START=$started"
    echo "CAPTURE_END=$ended"
    echo "DURATION_REQUESTED_S=$duration"
    echo 'NOTE=Global counters were enabled only during the requested observation window.'
    echo 'NOTE=Timestamp histogram is for the SurfaceView layer; no physical-panel optical proof.'
    echo 'NOTE=The device may switch display refresh dynamically; global stats are not layer-specific.'
    # Include only refresh aggregation, not other application layer names.
    printf '%s\n' "$dump" | awk '/^displayConfigStats is as below:/ {print; getline;print;exit}'
    printf '%s\n' "$selected"
  } > "$output"
  echo "PRE687_CAPTURE_OUTPUT=$output"
  echo "PRE687_CAPTURE_SUCCESS=UNVERIFIED_DATA"
}

case "${1:-}" in
  arm)
    delay="${2:-110}"; duration="${3:-90}"
    [[ "$delay" =~ ^[0-9]+$ && "$duration" =~ ^[0-9]+$ ]] || { echo 'PRE687_BAD_DURATION'; exit 2; }
    (( delay >= 10 && delay <= 600 && duration >= 20 && duration <= 600 )) || { echo 'PRE687_DURATION_OUT_OF_BOUNDS'; exit 2; }
    if [[ -f "$STATE" ]] && kill -0 "$(cat "$STATE")" 2>/dev/null; then
      echo 'PRE687_ALREADY_RUNNING=TRUE'; exit 3
    fi
    run_rish 'id' >/dev/null
    stamp="$(date '+%Y%m%d_%H%M%S')"
    nohup bash "$SELF" worker "$delay" "$duration" "$stamp" >"$OUT_DIR/NFSMW_PRE687_CAPTURE_${stamp}.status.txt" 2>&1 </dev/null &
    pid="$!"
    echo "$pid" > "$STATE"
    echo "PRE687_ARMED_WORKER_PID=$pid"
    echo "PRE687_START_AFTER_SECONDS=$delay"
    echo "PRE687_CAPTURE_FOR_SECONDS=$duration"
    echo 'Start the game now. This script waits first, then records without switching apps during gameplay.'
    ;;
  status)
    if [[ -f "$STATE" ]] && kill -0 "$(cat "$STATE")" 2>/dev/null; then
      echo 'PRE687_CAPTURE_PROCESS=RUNNING'
    else
      echo 'PRE687_CAPTURE_PROCESS=NOT_RUNNING'
      echo "PRE687_RESULTS_DIR=$OUT_DIR"
    fi
    ;;
  abort)
    if [[ -f "$STATE" ]]; then kill "$(cat "$STATE")" 2>/dev/null || true; fi
    run_rish 'dumpsys SurfaceFlinger --timestats -disable' >/dev/null || true
    rm -f "$STATE"
    echo 'PRE687_CAPTURE_ABORTED=TRUE'
    ;;
  worker)
    worker "${2:?}" "${3:?}" "${4:?}"
    ;;
  *) echo 'Use: bash script.sh arm [delay_sec=110] [capture_sec=90] | status | abort'; exit 2 ;;
esac
