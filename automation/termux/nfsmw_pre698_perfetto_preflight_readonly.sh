#!/usr/bin/env bash
# PRE698: NFSMW V51 / Galaxy S24 FE — non-invasive Perfetto feasibility preflight.
# Reads shell/device/runtime metadata only; does not start tracing or modify system.
set -Eeuo pipefail

PKG='io.github.nfsmwrecomp'
ADB="${NFSMW_ADB_BIN:-adb}"

say() { printf '%s\n' "$*"; }
abort() { say "$1" >&2; exit "${2:-20}"; }

preflight() {
  command -v "$ADB" >/dev/null 2>&1 || abort 'PRE698_ADB_UNAVAILABLE' 10

  local -a devices=()
  local serial uid model version package_info perfetto_version
  local query='' query_ok='false' frame_hint='UNVERIFIED'
  local sf_data='' period='' sf_hint='UNVERIFIED'

  mapfile -t devices < <("$ADB" devices | awk 'NR>1 && $2=="device" {print $1}')
  ((${#devices[@]}==1)) || abort "PRE698_DEVICE_COUNT_${#devices[@]}_ABORT" 11
  serial="${devices[0]}"

  uid="$("$ADB" -s "$serial" shell id -u | tr -d '\r\n')" ||
    abort 'PRE698_SHELL_ID_UNAVAILABLE' 12
  [[ "$uid" == '2000' ]] || abort "PRE698_SHELL_UID_${uid:-UNKNOWN}_ABORT" 13

  model="$("$ADB" -s "$serial" shell getprop ro.product.model | tr -d '\r\n')" ||
    abort 'PRE698_MODEL_UNAVAILABLE' 14
  [[ "$model" == 'SM-S721B' || "$model" == *'S24 FE'* ]] ||
    abort 'PRE698_UNEXPECTED_MODEL_ABORT' 15

  package_info="$("$ADB" -s "$serial" shell "dumpsys package $PKG")" ||
    abort 'PRE698_PACKAGE_UNAVAILABLE' 16
  version="$(printf '%s\n' "$package_info" |
    sed -n 's/.*versionCode=\([0-9][0-9]*\).*/\1/p' | head -n 1)"
  [[ "$version" == '51' ]] || abort "PRE698_UNEXPECTED_VERSION_${version:-NONE}_ABORT" 17

  if perfetto_version="$("$ADB" -s "$serial" shell perfetto --version 2>/dev/null)"; then
    say 'PRE698_PERFETTO_BINARY=RESPONDING'
  else
    say 'PRE698_PERFETTO_BINARY=UNVERIFIED'
  fi

  # --query is documented as non-recording service-state interrogation.
  # It does not guarantee that FrameTimeline will report NFSMW SurfaceView frames.
  if query="$("$ADB" -s "$serial" shell perfetto --query --long 2>/dev/null)"; then
    query_ok='true'
    if printf '%s\n' "$query" | grep -Fq 'android.surfaceflinger.frametimeline'; then
      frame_hint='ADVERTISED_NOT_RUNTIME_VALIDATED'
    else
      frame_hint='NOT_LISTED_NOT_PROVEN_UNSUPPORTED'
    fi
  fi

  # --latency with no layer is inspected ONLY for the refresh-period first line.
  # No SurfaceFlinger layer name or other-app information is printed.
  if sf_data="$("$ADB" -s "$serial" shell dumpsys SurfaceFlinger --latency 2>/dev/null)"; then
    period="${sf_data%%$'\n'*}"
    period="${period%$'\r'}"
    if [[ "$period" =~ ^[0-9]+$ ]] && (( period>=3000000 && period<=50000000 )); then
      sf_hint='PERIOD_READABLE'
    fi
  fi

  say 'PRE698_PREFLIGHT=PASS_READONLY_NO_TRACE'
  say "PRE698_MODEL=$model"
  say 'PRE698_PACKAGE=io.github.nfsmwrecomp'
  say 'PRE698_VERSION_CODE=51'
  say 'PRE698_ADB_UID=2000'
  say "PRE698_PERFETTO_QUERY_COMPLETED=$query_ok"
  say "PRE698_FRAME_TIMELINE_SOURCE=$frame_hint"
  say "PRE698_SURFACEFLINGER_LATENCY=$sf_hint"
  if [[ "$sf_hint" == 'PERIOD_READABLE' ]]; then
    say "PRE698_DISPLAY_PERIOD_NS=$period"
  fi
  say 'PRE698_REAL_FRAME_TIMELINE_DATA=NOT_CAPTURED'
  say 'PRE698_APP_TO_SURFACE_FRAME_MAPPING=UNVERIFIED'
  say 'PRE698_GPU_QUEUE_AND_FENCE_TIMESTAMPS=NOT_MEASURED'
  say 'PRE698_APK_OR_DEVICE_SETTINGS_MODIFIED=FALSE'
  say 'PRE698_FPS_GAIN_PROVEN=FALSE'
}

case "${1:-}" in
  preflight) preflight ;;
  *) say 'Uso: bash nfsmw_pre698_perfetto_preflight_readonly.sh preflight'; exit 2 ;;
esac
