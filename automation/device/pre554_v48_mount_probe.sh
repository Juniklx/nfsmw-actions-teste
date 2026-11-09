#!/system/bin/sh
# PRE554: read-only; start V48 before invoking in ADB shell.
# Six low-sensitivity, allowlisted values only; no raw paths or logs emitted.
PKG=io.github.nfsmwrecomp
echo "PRE554_PACKAGE=$PKG"
VC="$(dumpsys package "$PKG" 2>/dev/null | sed -n 's/.*versionCode=\([0-9][0-9]*\).*/\1/p' | head -n 1)"
case "$VC" in ''|*[!0-9]*) VC=0;; esac
echo "PRE554_VERSION_CODE=$VC"
PID="$(pidof "$PKG" 2>/dev/null | awk '{print $1}')"
case "$PID" in ''|*[!0-9]*)
 echo PRE554_PROCESS_RUNNING=NO
 echo PRE554_MAPS_ACCESS=NOT_RUNNING
 echo PRE554_EDITION_LIB=NOT_RUNNING
 echo PRE554_MOUNT_HINT=UNAVAILABLE
 exit 0;;
esac
echo PRE554_PROCESS_RUNNING=YES
if [ ! -r "/proc/$PID/maps" ]; then
 echo PRE554_MAPS_ACCESS=DENIED
 echo PRE554_EDITION_LIB=UNKNOWN
else
 echo PRE554_MAPS_ACCESS=GRANTED
 PAL=0; USA=0
 if grep -Eq '(^|[/!])libmain\.so([[:space:]]|$)' "/proc/$PID/maps" 2>/dev/null; then PAL=1; fi
 if grep -Eq '(^|[/!])libmain_usa\.so([[:space:]]|$)' "/proc/$PID/maps" 2>/dev/null; then USA=1; fi
 if [ "$PAL" -eq 1 ] && [ "$USA" -eq 0 ]; then E=PAL
 elif [ "$USA" -eq 1 ] && [ "$PAL" -eq 0 ]; then E=USA
 elif [ "$PAL" -eq 1 ] && [ "$USA" -eq 1 ]; then E=BOTH
 else E=UNKNOWN; fi
 echo "PRE554_EDITION_LIB=$E"
fi
HINT=NONE
if ! command -v logcat >/dev/null 2>&1; then HINT=UNAVAILABLE
elif logcat -d --pid="$PID" -t 4000 2>/dev/null | grep -Fq 'game_data_root es una imagen de disco'; then HINT=IMAGE_ROOT_LOG
elif logcat -d --pid="$PID" -t 4000 2>/dev/null | grep -Fq 'game_data_root does not exist'; then HINT=MISSING_ROOT_LOG
elif logcat -d --pid="$PID" -t 4000 2>/dev/null | grep -Eq 'Failed to initialize game data device|Failed to register host path device'; then HINT=DEVICE_ERROR_LOG
fi
echo "PRE554_MOUNT_HINT=$HINT"
