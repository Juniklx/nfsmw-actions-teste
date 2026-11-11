#!/usr/bin/env bash
# Synthetic-only test. Never contacts a real device.
set -Eeuo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WRAPPER="$REPO_ROOT/automation/termux/nfsmw_pre694_aba_readonly.sh"
bash -n "$WRAPPER"
if grep -En '(^|[[:space:]])(su|setprop|pm install|settings put|cmd thermalservice override-status)([[:space:]]|$)' "$WRAPPER"; then
  echo PRE694_FORBIDDEN_SYSTEM_WRITE=TRUE; exit 11
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/home/storage/downloads" "$TMP/bin"
cat > "$TMP/bin/adb" <<'ADB'
#!/usr/bin/env bash
set -Eeuo pipefail
if [[ "$1" == devices ]]; then
  printf 'List of devices attached\n127.0.0.1:5555\tdevice\n'
  if [[ "${MOCK_SECOND:-0}" == 1 ]]; then printf '127.0.0.1:5556\tdevice\n'; fi
  exit 0
fi
[[ "$1" == -s && "$3" == shell ]] || exit 90
shift 3
case "$*" in
  'id -u') echo 2000;;
  'getprop ro.product.model') echo "${MOCK_MODEL:-SM-S721B}";;
  'dumpsys package io.github.nfsmwrecomp') echo "  versionCode=${MOCK_VERSION:-51}";;
  *) echo "UNEXPECTED_ADB_QUERY:$*" >&2; exit 91;;
esac
ADB
cat > "$TMP/mock_collector.sh" <<'COLLECT'
#!/usr/bin/env bash
set -Eeuo pipefail
case "$1" in
  preflight) echo PRE690_PREFLIGHT=PASS_INTERFACE_ONLY;;
  status) echo PRE690_WORKER=NOT_RUNNING;;
  arm)
    echo PRE690_ARMED=TRUE
    cat >"$NFSMW_PRE690_OUT_DIR/NFSMW_PRE690_CAPTURE_20261111_120001.status.txt" <<'STATUS'
PRE690_MATCHING_NFSMW_LAYERS=2
PRE690_ADVANCING_NFSMW_LAYERS=1
PRE690_CAPTURE=RECORDED_UNANALYZED
PRE690_NO_APK_OR_SYSTEM_SETTINGS_CHANGED=TRUE
STATUS
    {
      echo PRE690_ORDERED_SURFACEVIEW_TIMESTAMPS
      echo SAMPLES_REQUESTED=30
      echo COLLECTION_START=2026-11-11T12:00:00-0300
      echo 'LAYER=fc1e4cf SurfaceView[io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity]@0(BLAST)#19616'
      for ((i=1;i<=30;i++)); do
        printf 'SAMPLE_START %s 2026-11-11T12:00:00-0300\n' "$i"
        echo 'FRAME 1 2 3'
        printf 'SAMPLE_END %s\n' "$i"
      done
      echo COLLECTION_END=2026-11-11T12:00:30-0300
      echo NONEMPTY_SAMPLES=30
    } >"$NFSMW_PRE690_OUT_DIR/NFSMW_PRE690_ORDERED_PRESENT_20261111_120001.txt"
    ;;
  *) exit 2;;
esac
COLLECT
chmod +x "$TMP/bin/adb" "$TMP/mock_collector.sh"
export HOME="$TMP/home" NFSMW_PRE694_COLLECTOR="$TMP/mock_collector.sh" NFSMW_ADB_BIN="$TMP/bin/adb"
bash "$WRAPPER" preflight
for bad in MOCK_SECOND MOCK_MODEL MOCK_VERSION; do
  case "$bad" in
    MOCK_SECOND) export MOCK_SECOND=1;;
    MOCK_MODEL) export MOCK_MODEL=OTHER_DEVICE;;
    MOCK_VERSION) export MOCK_VERSION=52;;
  esac
  if bash "$WRAPPER" arm SAMSUNG_A1 >/dev/null 2>&1; then
    echo "PRE694_FAILURE_GATE_BROKEN=$bad"; exit 12
  fi
  unset "$bad"
done
if bash "$WRAPPER" arm UNLISTED >/dev/null 2>&1; then echo PRE694_BAD_PHASE_ACCEPTED; exit 13; fi
for phase in SAMSUNG_A1 RADV_B SAMSUNG_A2; do
  bash "$WRAPPER" arm "$phase"
  if bash "$WRAPPER" arm SAMSUNG_A2 >/dev/null 2>&1; then echo PRE694_PARALLEL_ACCEPTED; exit 14; fi
  bash "$WRAPPER" status
  bash "$WRAPPER" finish
  dir="$(find "$HOME/storage/downloads/NFSMW_PRE694_ABA" -maxdepth 1 -type d -name "${phase}_*" -print -quit)"
  [[ -n "$dir" ]] || exit 15
  grep -qx 'PRE694_CAPTURE_STRUCTURAL_VALIDATION=PASS' "$dir/PRE694_PHASE_CAPTURE_VALIDATED.txt"
  grep -qx 'PRE694_DRIVER_ACTUALLY_LOADED=UNVERIFIED_NEEDS_LOG' "$dir/PRE694_PHASE_CAPTURE_VALIDATED.txt"
  grep -qx "PHASE_LABEL=$phase" "$dir/PRE694_PHASE_MANIFEST.txt"
done
[[ ! -f "$HOME/.nfsmw_pre694_current_phase" ]] || exit 16
[[ "$(find "$HOME/storage/downloads/NFSMW_PRE694_ABA" -name PRE694_PHASE_CAPTURE_VALIDATED.txt | wc -l)" -eq 3 ]] || exit 17
echo PRE694_SYNTHETIC_THREE_PHASE_CAPTURE_ISOLATION=PASS
echo PRE694_SYNTHETIC_VERSION_MODEL_DEVICE_GUARDS=PASS
echo PRE694_SYNTHETIC_NO_CONCURRENT_CAPTURE=PASS
echo PRE694_REAL_S24FE_CAPTURE=NOT_TESTED_IN_CI
echo PRE694_GPU_DRIVER_VERIFIED=REQUIRES_REAL_LOG
