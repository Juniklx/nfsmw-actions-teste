#!/usr/bin/env bash
# NFSMW PRE688: opt-in, read-only SurfaceFlinger collection over paired wireless ADB.
# No Shizuku/Shevery calls. Never changes APK, graphics, thermal policy, or refresh mode.
set -Eeuo pipefail
APP='io.github.nfsmwrecomp'
ADB_BIN="${NFSMW_ADB_BIN:-adb}"
OUT_DIR="${NFSMW_PRE688_OUT_DIR:-$HOME/storage/downloads}"
[[ -d "$OUT_DIR" ]] || OUT_DIR="$HOME"
STATE="$HOME/.nfsmw_pre688_worker.pid"
SELF="$(realpath "$0")"
say() { printf '%s\n' "$*"; }
help_text() {
  say 'Uso: bash nfsmw_pre688_adb_surfaceflinger.sh preflight | arm 110 90 | status | abort'
  say 'Requer ADB sem fio pareado e conectado ao proprio telefone, sem Shevery.'
  say 'A coleta e passiva; o start limpa apenas contadores diagnosticos do SurfaceFlinger.'
}
connected_serial() {
  command -v "$ADB_BIN" >/dev/null 2>&1 || { say 'PRE688_ADB_NOT_INSTALLED=TRUE' >&2; return 10; }
  local devices=()
  mapfile -t devices < <("$ADB_BIN" devices | awk 'NR>1 && $2=="device" {print $1}')
  if (( ${#devices[@]} != 1 )); then
    say "PRE688_CONNECTED_ADB_DEVICE_COUNT=${#devices[@]}" >&2
    say 'PRE688_REQUIRE_EXACTLY_ONE_CONNECTED_ADB_DEVICE=TRUE' >&2
    return 11
  fi
  printf '%s\n' "${devices[0]}"
}
run_shell() {
  local serial="$1"; shift
  "$ADB_BIN" -s "$serial" shell "$@"
}
preflight() {
  local serial model uid
  serial="$(connected_serial)" || return $?
  uid="$(run_shell "$serial" id -u | tr -d '\r\n')" || return 12
  model="$(run_shell "$serial" getprop ro.product.model | tr -d '\r\n')" || return 13
  [[ "$uid" == 2000 ]] || { say "PRE688_UNEXPECTED_ADB_UID=$uid" >&2; return 14; }
  say "PRE688_ADB_SHELL_UID=$uid"
  say "PRE688_DEVICE_MODEL=$model"
  if [[ "$model" != *'SM-S721B'* && "$model" != *'S24 FE'* ]]; then
    say 'PRE688_WARNING_DEVICE_IDENTITY_NOT_S24FE=TRUE' >&2
  fi
  say 'PRE688_ADB_PREFLIGHT=PASS'
}
filter_private_layer() {
  awk -v app="$APP" '
    { sub(/\r$/, "") }
    /^displayRefreshRate = / { last_refresh=$0; next }
    /^renderRate = / { last_render=$0; next }
    /^layerName = / {
      active=(index($0, "SurfaceView[" app "/")>0)
      pending=0
      if (active) {
        count++
        print "--- NFSMW_SURFACEVIEW_LAYER ---"
        if (last_refresh != "") print last_refresh
        if (last_render != "") print last_render
        print
      }
      next
    }
    active && /^(totalFrames|droppedFrames|lateAcquireFrames|badDesiredPresentFrames|averageFPS|frameRate) = / {print;next}
    active && (/^present2present histogram is as below:/ || /^presentToPresent histogram is as below:/) {
      print
      pending=1
      next
    }
    active && pending && /^[[:space:]]*[0-9]+ms=/ {
      print
      hist++
      pending=0
      next
    }
    END {
      print "PRE688_NFSMW_SURFACEVIEW_LAYERS=" (count+0)
      print "PRE688_LABELED_PRESENT_HISTOGRAMS=" (hist+0)
      if (count!=1 || hist!=1) exit 6
    }
  '
}
WORKER_SERIAL=""
WORKER_ARMED=0
WORKER_TEMPORARY=""
worker_cleanup() {
  local oldcode=$?
  if (( WORKER_ARMED == 1 )) && [[ -n "$WORKER_SERIAL" ]]; then
    run_shell "$WORKER_SERIAL" dumpsys SurfaceFlinger --timestats -disable >/dev/null 2>&1 || true
  fi
  rm -f "$STATE"
  [[ -z "$WORKER_TEMPORARY" ]] || rm -f "$WORKER_TEMPORARY"
  if (( oldcode != 0 )); then say "PRE688_WORKER_EXIT_CODE=$oldcode"; fi
}
worker() {
  local delay="$1" duration="$2" stamp="$3"
  local result="$OUT_DIR/NFSMW_PRE688_PRESENT2PRESENT_${stamp}.txt"
  WORKER_TEMPORARY="${result}.tmp"
  trap worker_cleanup EXIT
  say "PRE688_STAGE=WAIT_BEFORE_GAMEPLAY delay_seconds=$delay"
  sleep "$delay"
  WORKER_SERIAL="$(connected_serial)" || return $?
  local model
  model="$(run_shell "$WORKER_SERIAL" getprop ro.product.model | tr -d '\r\n')" || return $?
  say "PRE688_DEVICE_MODEL=$model"
  say 'PRE688_STAGE=CAPTURING'
  run_shell "$WORKER_SERIAL" dumpsys SurfaceFlinger --timestats -clear -enable >/dev/null
  WORKER_ARMED=1
  local began ended
  began="$(date '+%Y-%m-%dT%H:%M:%S%z')"
  sleep "$duration"
  ended="$(date '+%Y-%m-%dT%H:%M:%S%z')"
  {
    printf 'PRE688_NFSMW_PRESENT_PACING\n'
    printf 'PACKAGE=%s\n' "$APP"
    printf 'COLLECTION_START=%s\n' "$began"
    printf 'COLLECTION_END=%s\n' "$ended"
    printf 'REQUESTED_DURATION_SECONDS=%s\n' "$duration"
    printf 'SOURCE=Android SurfaceFlinger --timestats over wireless ADB\n'
    printf 'LIMIT=Aggregate histogram has no frame order or optical panel timestamps\n'
    run_shell "$WORKER_SERIAL" dumpsys SurfaceFlinger --timestats -dump | filter_private_layer
  } > "$WORKER_TEMPORARY" || {
    say 'PRE688_CAPTURE_VALIDATION=FAILED_OR_MULTIPLE_LAYERS' >&2
    say 'PRE688_UNFILTERED_DUMP_PRESERVED=FALSE' >&2
    return 20
  }
  mv "$WORKER_TEMPORARY" "$result"
  WORKER_TEMPORARY=""
  say "PRE688_CAPTURE_OUTPUT=$result"
  say 'PRE688_CAPTURE_VALIDATION=PASS_SINGLE_SURFACEVIEW_LAYER'
  say 'PRE688_NO_SHEVERY_APP_INVOCATION=TRUE'
}
case "${1:-}" in
  preflight) preflight ;;
  arm)
    delay="${2:-110}"; duration="${3:-90}"
    [[ "$delay" =~ ^[0-9]+$ && "$duration" =~ ^[0-9]+$ ]] || { say 'PRE688_BAD_TIME_VALUE'; exit 2; }
    (( delay>=10 && delay<=600 && duration>=20 && duration<=600 )) || { say 'PRE688_TIME_OUT_OF_BOUNDS'; exit 2; }
    preflight
    if [[ -f "$STATE" ]] && kill -0 "$(cat "$STATE")" 2>/dev/null; then
      say 'PRE688_ALREADY_RUNNING=TRUE'; exit 3
    fi
    stamp="$(date '+%Y%m%d_%H%M%S')"
    nohup bash "$SELF" worker "$delay" "$duration" "$stamp" >"$OUT_DIR/NFSMW_PRE688_CAPTURE_${stamp}.status.txt" 2>&1 </dev/null &
    printf '%s\n' "$!" >"$STATE"
    say "PRE688_BACKGROUND_PID=$!"
    say "PRE688_PRE_GAMEPLAY_DELAY_SECONDS=$delay"
    say "PRE688_CAPTURE_DURATION_SECONDS=$duration"
    say 'PRE688_ARMED=TRUE'
    say 'Abra o jogo e mantenha-o em primeiro plano durante a coleta.'
    ;;
  status)
    if [[ -f "$STATE" ]] && kill -0 "$(cat "$STATE")" 2>/dev/null; then
      say 'PRE688_WORKER=RUNNING'
    else
      say 'PRE688_WORKER=NOT_RUNNING'
    fi
    say "PRE688_OUTPUT_FOLDER=$OUT_DIR"
    ;;
  abort)
    if [[ -f "$STATE" ]]; then kill "$(cat "$STATE")" 2>/dev/null || true; fi
    serial="$(connected_serial)" || exit $?
    run_shell "$serial" dumpsys SurfaceFlinger --timestats -disable >/dev/null
    rm -f "$STATE"
    say 'PRE688_ABORTED_COUNTERS_DISABLED=TRUE'
    ;;
  worker) worker "${2:?}" "${3:?}" "${4:?}" ;;
  *) help_text; exit 2 ;;
esac
