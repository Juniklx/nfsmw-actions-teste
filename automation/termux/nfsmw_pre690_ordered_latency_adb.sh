#!/usr/bin/env bash
# PRE690: ordered SurfaceFlinger timestamps for NFSMW's SurfaceView, using paired ADB.
# No Shevery, Shizuku, root, graphics/thermal changes, or APK modifications.
set -Eeuo pipefail
PKG='io.github.nfsmwrecomp'
ADB="${NFSMW_ADB_BIN:-adb}"
OUT="${NFSMW_PRE690_OUT_DIR:-$HOME/storage/downloads}"
[[ -d "$OUT" ]] || OUT="$HOME"
SELF="$(realpath "$0")"
STATE="$HOME/.nfsmw_pre690_worker.pid"
notice() { printf '%s\n' "$*"; }
device() {
  command -v "$ADB" >/dev/null || { notice 'PRE690_ADB_NOT_INSTALLED=TRUE' >&2; return 10; }
  local ds=()
  mapfile -t ds < <("$ADB" devices | awk 'NR>1 && $2=="device"{print $1}')
  (( ${#ds[@]}==1 )) || { notice "PRE690_ADB_CONNECTED_COUNT=${#ds[@]}" >&2; return 11; }
  printf '%s\n' "${ds[0]}"
}
shelladb() { local d="$1"; shift; "$ADB" -s "$d" shell "$@"; }
quote_remote() {
  local input="${1//\'/\'\\\'\'}"
  printf "'%s'" "$input"
}
layer_cmd() {
  local d="$1" op="$2" layer="$3"
  shelladb "$d" "dumpsys SurfaceFlinger $op $(quote_remote "$layer")"
}
preflight() {
  local d uid model hdr period
  d="$(device)" || return $?
  uid="$(shelladb "$d" id -u | tr -d '\r\n')" || return 12
  [[ "$uid" == 2000 ]] || { notice "PRE690_ADB_UID_UNEXPECTED=$uid" >&2; return 13; }
  model="$(shelladb "$d" getprop ro.product.model | tr -d '\r\n')"
  [[ "$model" == 'SM-S721B' || "$model" == *'S24 FE'* ]] || {
    notice 'PRE690_OTHER_DEVICE_STOP=TRUE' >&2; return 14;
  }
  hdr="$(shelladb "$d" dumpsys SurfaceFlinger --latency)" || return 15
  period="${hdr%%$'\n'*}"; period="${period%$'\r'}"
  [[ "$period" =~ ^[0-9]+$ ]] || {
    notice 'PRE690_LATENCY_INTERFACE_UNAVAILABLE=TRUE' >&2; return 16;
  }
  notice 'PRE690_PREFLIGHT=PASS_INTERFACE_ONLY'
  notice "PRE690_DEVICE_MODEL=$model"
  notice "PRE690_REFRESH_PERIOD_NS=$period"
  notice 'PRE690_GAME_LAYER_AND_TIMESTAMPS=NOT_YET_TESTED'
}
latest_present_ns() {
  # Extract latest *actual presentation* timestamp from this exact layer.
  # No other-app names or raw SurfaceFlinger dumps are saved.
  local d="$1" layer="$2" raw
  raw="$(layer_cmd "$d" --latency "$layer")" || return 21
  printf '%s\n' "$raw" | awk '
    {sub(/\r$/, "")}
    NR==1 {if ($0 !~ /^[0-9]+$/) {bad=1; exit 21}; next}
    NF==3 && $2 ~ /^[0-9]+$/ && $2!="0" && $2!="-1" && $2!="9223372036854775807" {
      if (top=="" || $2+0>top+0) top=$2
      next
    }
    NF==0 {next}
    NF==3 {next}
    {bad=1; exit 22}
    END {if(bad) exit 23; print top=="" ? "0" : top}
  '
}
select_layer() {
  local d="$1" line index moving=0 selected="" before_ns after_ns
  local matches=() before=()
  while IFS= read -r line; do
    line="${line%$'\r'}"
    [[ "$line" == *"SurfaceView[$PKG/"* ]] && matches+=("$line")
  done < <(shelladb "$d" dumpsys SurfaceFlinger --list)
  notice "PRE690_MATCHING_NFSMW_LAYERS=${#matches[@]}" >&2
  ((${#matches[@]}>0)) || return 20

  # Older SurfaceViews can coexist with the actual presenting layer.
  # Measure progress twice, not lexicographic layer ID or list order.
  for ((index=0; index<${#matches[@]}; index++)); do
    before_ns="$(latest_present_ns "$d" "${matches[index]}")" || {
      notice "PRE690_LAYER_PROBE_ERROR_INDEX=$((index+1))" >&2
      return 21
    }
    [[ "$before_ns" =~ ^[0-9]+$ ]] || return 21
    notice "PRE690_LAYER_$((index+1))_BEFORE_ACTUAL_NS=$before_ns" >&2
    before+=("$before_ns")
  done
  sleep 2
  for ((index=0; index<${#matches[@]}; index++)); do
    after_ns="$(latest_present_ns "$d" "${matches[index]}")" || {
      notice "PRE690_LAYER_PROBE_ERROR_INDEX=$((index+1))" >&2
      return 21
    }
    [[ "$after_ns" =~ ^[0-9]+$ ]] || return 21
    notice "PRE690_LAYER_$((index+1))_AFTER_ACTUAL_NS=$after_ns" >&2
    if (( after_ns > before[index] )); then
      notice "PRE690_LAYER_$((index+1))_ADVANCING=TRUE" >&2
      moving=$((moving+1))
      selected="${matches[index]}"
    else
      notice "PRE690_LAYER_$((index+1))_ADVANCING=FALSE" >&2
    fi
  done
  notice "PRE690_ADVANCING_NFSMW_LAYERS=$moving" >&2
  if (( moving!=1 )); then
    notice 'PRE690_LAYER_AMBIGUOUS_OR_INACTIVE_ABORT=TRUE' >&2
    return 20
  fi
  printf '%s\n' "$selected"
}
parse_dump() {
  # Large nanosecond timestamp arithmetic is deliberately deferred to Python.
  awk '
    {sub(/\r$/,"")}
    NR==1 { if ($0 !~ /^[0-9]+$/ || $0+0<3000000 || $0+0>50000000) exit 21;
            print "PERIOD_NS " $0; next }
    NF==3 && $1~/^-?[0-9]+$/ && $2~/^-?[0-9]+$/ && $3~/^-?[0-9]+$/ {
      print "FRAME " $1 " " $2 " " $3; n++;
      if ($2!="0" && $2!="9223372036854775807" && $2!="-1") valid++;
      next
    }
    NF==0 {next}
    {exit 22}
    END {print "FRAME_ROWS " n+0; print "VALID_PRESENT_ROWS " valid+0}
  '
}
TMP=''
cleanup() {
  local rc=$?
  [[ -z "$TMP" ]] || rm -f "$TMP"
  rm -f "$STATE"
  ((rc==0)) || notice "PRE690_WORKER_EXIT_CODE=$rc"
}
worker() {
  local delay="$1" seconds="$2" stamp="$3" dest d layer now raw parsed rows
  dest="$OUT/NFSMW_PRE690_ORDERED_PRESENT_${stamp}.txt"
  TMP="${dest}.tmp"; trap cleanup EXIT
  notice "PRE690_STAGE=WAIT delay_s=$delay"
  sleep "$delay"
  d="$(device)" || return $?
  layer="$(select_layer "$d")" || return $?
  layer_cmd "$d" --latency-clear "$layer" >/dev/null || return 24
  {
    printf 'PRE690_ORDERED_SURFACEVIEW_TIMESTAMPS\nPACKAGE=%s\n' "$PKG"
    printf 'LAYER=%s\n' "$layer"
    printf 'COLLECTION_START=%s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')"
    printf 'SAMPLES_REQUESTED=%s\n' "$seconds"
    printf 'COLUMNS=desired_ns actual_present_ns frame_ready_ns\n'
    printf 'SAMPLING=one_query_per_second_exact_NFSMW_SurfaceView\n'
  } > "$TMP"
  local nonempty=0
  for ((i=1;i<=seconds;i++)); do
    now="$(date '+%Y-%m-%dT%H:%M:%S%z')"
    raw="$(layer_cmd "$d" --latency "$layer")" || return 25
    parsed="$(printf '%s\n' "$raw" | parse_dump)" || {
      notice "PRE690_SAMPLE_SCHEMA_ERROR_INDEX=$i" >&2; return 26;
    }
    rows="$(printf '%s\n' "$parsed" | awk '$1=="VALID_PRESENT_ROWS"{print $2}')"
    if ((rows>0)); then nonempty=$((nonempty+1)); fi
    printf 'SAMPLE_START %d %s\n%s\nSAMPLE_END %d\n' "$i" "$now" "$parsed" "$i" >> "$TMP"
    sleep 1
  done
  printf 'COLLECTION_END=%s\nNONEMPTY_SAMPLES=%d\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$nonempty" >> "$TMP"
  ((nonempty>=seconds/2)) || { notice 'PRE690_INSUFFICIENT_GAME_FRAMES=TRUE' >&2; return 27; }
  mv "$TMP" "$dest"; TMP=''
  notice "PRE690_CAPTURE_OUTPUT=$dest"
  notice 'PRE690_CAPTURE=RECORDED_UNANALYZED'
  notice 'PRE690_NO_APK_OR_SYSTEM_SETTINGS_CHANGED=TRUE'
}
case "${1:-}" in
  preflight) preflight ;;
  arm)
    delay="${2:-110}"; seconds="${3:-60}"
    [[ "$delay" =~ ^[0-9]+$ && "$seconds" =~ ^[0-9]+$ ]] || exit 2
    ((delay>=10 && delay<=600 && seconds>=20 && seconds<=120)) || exit 2
    preflight
    if [[ -f "$STATE" ]] && kill -0 "$(cat "$STATE")" 2>/dev/null; then
      notice 'PRE690_WORKER_ALREADY_RUNNING=TRUE'; exit 3
    fi
    stamp="$(date '+%Y%m%d_%H%M%S')"
    nohup bash "$SELF" worker "$delay" "$seconds" "$stamp" >"$OUT/NFSMW_PRE690_CAPTURE_${stamp}.status.txt" 2>&1 </dev/null &
    printf '%s\n' "$!" > "$STATE"
    notice "PRE690_WORKER_PID=$!"
    notice 'PRE690_ARMED=TRUE'
    notice 'Abra o jogo e mantenha o carro parado durante a captura.'
    ;;
  status)
    if [[ -f "$STATE" ]] && kill -0 "$(cat "$STATE")" 2>/dev/null; then
      notice 'PRE690_WORKER=RUNNING'
    else notice 'PRE690_WORKER=NOT_RUNNING'; fi
    notice "PRE690_OUTPUT_DIR=$OUT"
    ;;
  abort)
    if [[ -f "$STATE" ]]; then kill -TERM "$(cat "$STATE")" 2>/dev/null || true; fi
    notice 'PRE690_ABORT_REQUESTED=TRUE'
    ;;
  worker) worker "${2:?}" "${3:?}" "${4:?}" ;;
  *) notice 'Uso: bash nfsmw_pre690_ordered_latency_adb.sh preflight | arm 110 60 | status | abort'; exit 2 ;;
esac
