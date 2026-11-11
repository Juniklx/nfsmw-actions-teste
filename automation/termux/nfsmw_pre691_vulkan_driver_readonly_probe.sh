#!/usr/bin/env bash
# PRE691: READ ONLY Galaxy S24 FE Vulkan environment audit.
# This cannot prove which ICD the app loaded; it only records device/package
# properties and vendor driver module names. No root or setprop.
set -Eeuo pipefail
PKG=io.github.nfsmwrecomp
ADB="${NFSMW_ADB_BIN:-adb}"
OUT="${NFSMW_PRE691_OUT_DIR:-$HOME/storage/downloads}"
[[ -d "$OUT" ]] || OUT="$HOME"
emit() { printf '%s\n' "$*"; }
command -v "$ADB" >/dev/null || { emit 'PRE691_ADB_NOT_FOUND=TRUE'; exit 10; }
mapfile -t devices < <("$ADB" devices | awk 'NR>1&&$2=="device"{print $1}')
((${#devices[@]}==1)) || { emit "PRE691_DEVICE_COUNT=${#devices[@]}"; exit 11; }
dev="${devices[0]}"
shell() { "$ADB" -s "$dev" shell "$@"; }
uid="$(shell id -u | tr -d '\r\n')"
[[ "$uid" == 2000 ]] || { emit "PRE691_UNEXPECTED_SHELL_UID=$uid"; exit 12; }
model="$(shell getprop ro.product.model | tr -d '\r\n')"
[[ "$model" == SM-S721B || "$model" == *'S24 FE'* ]] || {
  emit "PRE691_UNEXPECTED_MODEL=$model"; exit 13;
}
paths="$(shell "pm path $PKG" | tr -d '\r')" || { emit 'PRE691_PACKAGE_LOOKUP_FAILED=TRUE'; exit 14; }
[[ "$paths" == *"package:"* ]] || { emit 'PRE691_PACKAGE_NOT_INSTALLED=TRUE'; exit 15; }
vers="$(shell "dumpsys package $PKG" | sed -n 's/.*versionCode=\([0-9][0-9]*\).*/\1/p' | head -n1)"
[[ "$vers" =~ ^[0-9]+$ ]] || { emit 'PRE691_VERSION_NOT_READABLE=TRUE'; exit 16; }
stamp="$(date '+%Y%m%d_%H%M%S')"
dest="$OUT/NFSMW_PRE691_VULKAN_ENV_${stamp}.txt"
{
  emit 'PRE691_VULKAN_ENV_READONLY'
  emit "PACKAGE=$PKG"
  emit "DEVICE_MODEL=$model"
  emit "PACKAGE_VERSION_CODE=$vers"
  emit "ANDROID_SDK=$(shell getprop ro.build.version.sdk | tr -d '\r\n')"
  for prop in ro.hardware.vulkan ro.hardware.egl ro.board.platform ro.gfx.driver.0; do
    value="$(shell "getprop $prop" | tr -d '\r\n')"
    [[ -n "$value" ]] || value='UNSET'
    emit "PROP_${prop}=$value"
  done
  # Vendor file names can be evidence of installed modules but NOT of app ICD selection.
  modules="$(shell 'ls /vendor/lib64/hw/vulkan.*.so 2>/dev/null || true' | tr -d '\r')"
  [[ -n "$modules" ]] || modules=NOT_LISTED
  emit 'VENDOR_VULKAN_MODULE_FILENAMES_BEGIN'
  printf '%s\n' "$modules"
  emit 'VENDOR_VULKAN_MODULE_FILENAMES_END'
  emit 'GAME_PID_CHECK=OMITTED_NOT_NEEDED'
  emit 'CUSTOM_DRIVER_LOADED=NOT_DETERMINABLE_BY_THIS_PROBE'
  emit 'PRE691_NO_ROOT_NO_SET_PROP_NO_APK_MODIFICATION=TRUE'
} > "$dest"
emit "PRE691_OUTPUT=$dest"
emit 'PRE691_ENV_CAPTURE=PASS_READONLY'
