#!/usr/bin/env bash
# PRE694: read-only session isolation wrapper for PRE690 SurfaceFlinger collector.
# DOES NOT switch GPU drivers or edit game settings. User must select manually.
set -Eeuo pipefail
COLLECTOR="${NFSMW_PRE694_COLLECTOR:-$HOME/nfsmw_pre690_ordered_latency_adb.sh}"
ADB="${NFSMW_ADB_BIN:-adb}"
ROOT="${NFSMW_PRE694_ROOT:-$HOME/storage/downloads/NFSMW_PRE694_ABA}"
CURRENT="$HOME/.nfsmw_pre694_current_phase"
PKG='io.github.nfsmwrecomp'
msg(){ printf '%s\n' "$*"; }
fail(){ msg "$1" >&2; exit "${2:-20}"; }
require_collector(){
  [[ -f "$COLLECTOR" ]] || fail 'PRE694_PRE690_COLLECTOR_MISSING' 10
  bash -n "$COLLECTOR" || fail 'PRE694_PRE690_SYNTAX_FAILED' 11
}
version_gate(){
  command -v "$ADB" >/dev/null || fail 'PRE694_ADB_MISSING' 12
  local ds=() d uid model version
  mapfile -t ds < <("$ADB" devices | awk 'NR>1 && $2=="device" {print $1}')
  (( ${#ds[@]} == 1 )) || fail "PRE694_ADB_DEVICE_COUNT_${#ds[@]}_ABORT" 13
  d="${ds[0]}"
  uid="$("$ADB" -s "$d" shell id -u | tr -d '\r\n')"
  [[ "$uid" == '2000' ]] || fail 'PRE694_ADB_NOT_SHELL_ABORT' 14
  model="$("$ADB" -s "$d" shell getprop ro.product.model | tr -d '\r\n')"
  [[ "$model" == 'SM-S721B' || "$model" == *'S24 FE'* ]] || fail 'PRE694_OTHER_MODEL_ABORT' 15
  version="$("$ADB" -s "$d" shell "dumpsys package $PKG" | sed -n 's/.*versionCode=\([0-9][0-9]*\).*/\1/p' | head -n 1)"
  [[ "$version" == '51' ]] || fail "PRE694_UNEXPECTED_APK_VERSION_${version:-NONE}_ABORT" 16
  msg 'PRE694_DEVICE_AND_INSTALLED_V51=PASS'
  msg "PRE694_MODEL=$model"
  msg 'PRE694_V51_SHA_PREVIOUSLY_VERIFIED_NOT_RECHECKED=TRUE'
}
preflight(){
  require_collector
  version_gate
  NFSMW_ADB_BIN="$ADB" bash "$COLLECTOR" preflight
  msg 'PRE694_PREFLIGHT=PASS_READONLY'
}
arm(){
  local stage="${1:-}" dir stamp
  case "$stage" in
    SAMSUNG_A1|RADV_B|SAMSUNG_A2) ;;
    *) fail 'PRE694_INVALID_PHASE_EXPECT_SAMSUNG_A1_RADV_B_SAMSUNG_A2' 17 ;;
  esac
  [[ ! -f "$CURRENT" ]] || fail 'PRE694_EXISTING_PHASE_FINISH_OR_ARCHIVE_FIRST' 18
  preflight
  mkdir -p "$ROOT"
  stamp="$(date +%Y%m%d_%H%M%S)"
  dir="$ROOT/${stage}_${stamp}"
  mkdir "$dir" || fail 'PRE694_CANNOT_CREATE_UNIQUE_PHASE_DIRECTORY' 19
  {
    msg 'PRE694_A_B_A_CAPTURE_SESSION'
    msg "PHASE_LABEL=$stage"
    msg 'DRIVER_LABEL_IS_INTENT_NOT_VERIFIED=TRUE'
    msg "DEVICE=SM-S721B"
    msg "PACKAGE=$PKG"
    msg 'VERSION_CODE=51'
    msg "ARMED_AT=$(date -Iseconds)"
    msg 'INTERNAL_RESOLUTION_REQUIRED=1920x1080'
    msg 'FPS_CAP_REQUIRED=60'
    msg 'EFFECTS_UNCHANGED_REQUIRED=TRUE'
    msg 'SCREEN_SCENE_EQUIVALENCE=USER_TO_VERIFY'
    msg 'GPU_DRIVER_SELECTION=MANUAL_IN_GAME_MENU'
    msg 'GPU_DRIVER_VERIFICATION=NEEDS_SAME_SESSION_NFSMW_LOG'
    msg 'THERMAL_STATE_EQUIVALENCE=UNVERIFIED'
    msg 'NO_NEW_APK_OR_SYSTEM_CHANGE=TRUE'
  } > "$dir/PRE694_PHASE_MANIFEST.txt"
  # PRE690 reads OUT from environment; the background worker inherits it.
  if ! NFSMW_ADB_BIN="$ADB" NFSMW_PRE690_OUT_DIR="$dir" bash "$COLLECTOR" arm 110 30; then
    msg 'PRE694_COLLECTOR_ARM_FAILED_PRESERVE_MANIFEST'
    exit 21
  fi
  printf '%s\n' "$dir" > "$CURRENT"
  msg "PRE694_PHASE_DIR=$dir"
  msg "PRE694_PHASE=$stage"
  msg 'PRE694_ARMED=TRUE'
  msg 'PRE694_DO_NOT_SWITCH_DRIVER_DURING_SESSION=TRUE'
}
status(){
  require_collector
  [[ -s "$CURRENT" ]] || { msg 'PRE694_NO_ACTIVE_PHASE=TRUE'; exit 0; }
  local dir
  dir="$(cat "$CURRENT")"
  [[ -d "$dir" && "$dir" == "$ROOT/"* ]] || fail 'PRE694_PHASE_PATH_INVALID_ABORT' 22
  msg "PRE694_PHASE_DIR=$dir"
  NFSMW_PRE690_OUT_DIR="$dir" bash "$COLLECTOR" status
  for f in "$dir"/NFSMW_PRE690_CAPTURE_*.status.txt; do
    [[ -f "$f" ]] || continue
    if grep -q '^PRE690_CAPTURE=RECORDED_UNANALYZED$' "$f"; then
      msg 'PRE694_CAPTURE_WORKER_COMPLETED=TRUE'
    else
      msg 'PRE694_CAPTURE_WORKER_COMPLETED=FALSE'
    fi
  done
}
finish(){
  [[ -s "$CURRENT" ]] || fail 'PRE694_NO_ACTIVE_PHASE_ABORT' 23
  local dir statuses=() captures=() s c samples nonempty
  dir="$(cat "$CURRENT")"
  [[ -d "$dir" && "$dir" == "$ROOT/"* ]] || fail 'PRE694_PHASE_PATH_INVALID_ABORT' 22
  shopt -s nullglob
  statuses=("$dir"/NFSMW_PRE690_CAPTURE_*.status.txt)
  captures=("$dir"/NFSMW_PRE690_ORDERED_PRESENT_*.txt)
  shopt -u nullglob
  (( ${#statuses[@]} == 1 && ${#captures[@]} == 1 )) || fail 'PRE694_MISSING_OR_AMBIGUOUS_CAPTURE_FILES_ABORT' 24
  s="${statuses[0]}"; c="${captures[0]}"
  grep -qx 'PRE690_CAPTURE=RECORDED_UNANALYZED' "$s" || fail 'PRE694_CAPTURE_NOT_COMPLETED_ABORT' 25
  grep -qx 'PRE690_ADVANCING_NFSMW_LAYERS=1' "$s" || fail 'PRE694_ACTIVE_SURFACE_NOT_UNIQUE_ABORT' 26
  grep -qx 'SAMPLES_REQUESTED=30' "$c" || fail 'PRE694_REQUESTED_30_SAMPLES_MISSING_ABORT' 27
  samples="$(grep -c '^SAMPLE_START ' "$c")"
  [[ "$samples" == 30 ]] || fail "PRE694_ONLY_${samples}_SAMPLE_STARTS_ABORT" 28
  [[ "$(grep -c '^SAMPLE_END ' "$c")" == 30 ]] || fail 'PRE694_SAMPLE_END_COUNT_ABORT' 29
  nonempty="$(sed -n 's/^NONEMPTY_SAMPLES=\([0-9][0-9]*\)$/\1/p' "$c")"
  [[ "$nonempty" =~ ^[0-9]+$ ]] && ((nonempty>=15)) || fail 'PRE694_TOO_FEW_NONEMPTY_SAMPLES_ABORT' 30
  grep -q '^COLLECTION_END=' "$c" || fail 'PRE694_NO_COLLECTION_END_ABORT' 31
  {
    msg 'PRE694_CAPTURE_STRUCTURAL_VALIDATION=PASS'
    msg 'PRE694_DRIVER_ACTUALLY_LOADED=UNVERIFIED_NEEDS_LOG'
    msg 'PRE694_GAMEPLAY_AND_WATCHDOG_UNVERIFIED_NEEDS_LOG'
    msg "PRE694_VALIDATED_AT=$(date -Iseconds)"
    msg "PRE694_NONEMPTY_SAMPLES=$nonempty"
    sha256sum "$s" "$c" "$dir/PRE694_PHASE_MANIFEST.txt"
  } > "$dir/PRE694_PHASE_CAPTURE_VALIDATED.txt"
  rm -f "$CURRENT"
  msg 'PRE694_PHASE_CAPTURE=PASS_STRUCTURAL_ONLY'
  msg 'PRE694_DRIVER_CAUSALITY_AND_FPS_GAIN=UNPROVEN'
  msg "PRE694_PHASE_DIR=$dir"
  msg 'PRE694_SEND_PHASE_DIRECTORY_FILES_AND_SAME_SESSION_NFSMW_LOG=TRUE'
}
case "${1:-}" in
  preflight) preflight ;;
  arm) arm "${2:-}" ;;
  status) status ;;
  finish) finish ;;
  *) msg 'Uso: bash nfsmw_pre694_aba_readonly.sh preflight | arm SAMSUNG_A1|RADV_B|SAMSUNG_A2 | status | finish'; exit 2 ;;
esac
