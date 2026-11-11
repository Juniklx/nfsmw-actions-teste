#!/usr/bin/env bash
# PRE691: read-only SHA256 identity of installed base.apk, no APK pull.
set -Eeuo pipefail
PKG=io.github.nfsmwrecomp
EXPECTED=207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b
ADB=adb
OUT="$HOME/storage/downloads"
[[ -d "$OUT" ]] || OUT="$HOME"
fail() { echo "$1"; exit "$2"; }
command -v "$ADB" >/dev/null || fail 'PRE691_ADB_UNAVAILABLE=TRUE' 10
DEV="$("$ADB" devices | awk 'NR>1 && $2=="device"{print $1}')"
[[ -n "$DEV" && "$DEV" != *$'\n'* ]] || fail 'PRE691_DEVICE_COUNT_INVALID_ABORT=TRUE' 11
shell() { "$ADB" -s "$DEV" shell "$@"; }
UID_REMOTE="$(shell id -u | tr -d '\r\n')"
[[ "$UID_REMOTE" == 2000 ]] || fail 'PRE691_NOT_ADB_SHELL_ABORT=TRUE' 12
MODEL="$(shell getprop ro.product.model | tr -d '\r\n')"
[[ "$MODEL" == 'SM-S721B' || "$MODEL" == *'S24 FE'* ]] || fail 'PRE691_OTHER_MODEL_ABORT=TRUE' 13
VERSION="$(shell "dumpsys package $PKG" | sed -n 's/.*versionCode=\([0-9][0-9]*\).*/\1/p' | head -n1)"
[[ "$VERSION" == 51 ]] || fail 'PRE691_NON_V51_VERSION_ABORT=TRUE' 14
BASES="$(shell "pm path $PKG" | tr -d '\r' | sed -n 's/^package:\(\/.*\/base\.apk\)$/\1/p')"
[[ -n "$BASES" && "$BASES" != *$'\n'* ]] || fail 'PRE691_BASE_APK_AMBIGUOUS_ABORT=TRUE' 15
case "$BASES" in /data/app/*/base.apk) ;; *) fail 'PRE691_BASE_APK_PATH_INVALID_ABORT=TRUE' 16 ;; esac
[[ "$BASES" != *[[:space:]]* ]] || fail 'PRE691_BASE_APK_PATH_HAS_WHITESPACE_ABORT=TRUE' 17
RAW="$(shell sha256sum "$BASES" 2>/dev/null)" || fail 'PRE691_DEVICE_APK_SHA256_NOT_READABLE=TRUE' 18
GOT="$(printf '%s\n' "$RAW" | awk '{print $1}')"
[[ "$GOT" =~ ^[0-9a-fA-F]{64}$ ]] || fail 'PRE691_DEVICE_APK_SHA256_INVALID_ABORT=TRUE' 19
GOT="$(printf '%s' "$GOT" | tr A-F a-f)"
REPORT="$OUT/NFSMW_PRE691_INSTALLED_APK_IDENTITY_$(date +%Y%m%d_%H%M%S).txt"
{
  echo PRE691_INSTALLED_APK_IDENTITY_READONLY
  echo "PACKAGE=$PKG"
  echo "DEVICE_MODEL=$MODEL"
  echo "PACKAGE_VERSION_CODE=$VERSION"
  echo "EXPECTED_BASE_APK_SHA256=$EXPECTED"
  echo "INSTALLED_BASE_APK_SHA256=$GOT"
  if [[ "$GOT" == "$EXPECTED" ]]; then
    echo 'PRE691_INSTALLED_V51_BINARY_IDENTITY=PASS'
  else
    echo 'PRE691_INSTALLED_V51_BINARY_IDENTITY=MISMATCH_ABORT'
  fi
  echo PRE691_NO_ROOT_NO_APK_PULL_NO_SETTINGS_CHANGE=TRUE
} > "$REPORT"
echo "PRE691_REPORT=$REPORT"
[[ "$GOT" == "$EXPECTED" ]] || fail 'PRE691_SHA256_MISMATCH_ABORT=TRUE' 20
echo PRE691_DEVICE_APK_IDENTITY_GATE=PASS
