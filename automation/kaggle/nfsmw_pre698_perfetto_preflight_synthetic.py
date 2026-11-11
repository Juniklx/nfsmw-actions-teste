#!/usr/bin/env python3
"""PRE698: mocked ADB-only tests; never touches an Android device."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
import tempfile

SCRIPT = Path(__file__).resolve().parents[1] / 'termux' / 'nfsmw_pre698_perfetto_preflight_readonly.sh'
MOCK = r'''#!/usr/bin/env bash
set -eu
case "$*" in
  devices)
    if [ "${MOCK_NODEVICE:-0}" = 1 ]; then printf 'List of devices attached\n';
    else printf 'List of devices attached\nXDEVICE\tdevice\n'; fi ;;
  '-s XDEVICE shell id -u') echo "${MOCK_UID:-2000}" ;;
  '-s XDEVICE shell getprop ro.product.model') echo "${MOCK_MODEL:-SM-S721B}" ;;
  '-s XDEVICE shell dumpsys package io.github.nfsmwrecomp')
    echo "versionCode=${MOCK_VERSION:-51} minSdk=23 targetSdk=35" ;;
  '-s XDEVICE shell perfetto --version') echo 'perfetto vX' ;;
  '-s XDEVICE shell perfetto --query --long')
    if [ "${MOCK_NOQUERY:-0}" = 1 ]; then exit 1; fi
    if [ "${MOCK_NOFT:-0}" != 1 ]; then
      echo 'android.surfaceflinger.frametimeline'
    fi ;;
  '-s XDEVICE shell dumpsys SurfaceFlinger --latency')
    if [ "${MOCK_BADLAT:-0}" = 1 ]; then echo unknown;
    else printf '8333333\n100000 110000 105000\n'; fi ;;
  *) exit 40 ;;
esac
'''


def run() -> int:
    if not SCRIPT.is_file():
        print('PRE698_SYNTHETIC_MISSING_SCRIPT', file=sys.stderr)
        return 2
    subprocess.run(['bash', '-n', str(SCRIPT)], check=True)
    with tempfile.TemporaryDirectory(prefix='nfsmw_pre698_synthetic_') as tmp:
        adb = Path(tmp) / 'mock-adb'
        adb.write_text(MOCK, encoding='utf-8')
        adb.chmod(0o700)
        cases = [
            ('BASELINE', {}, 0, 'PRE698_FRAME_TIMELINE_SOURCE=ADVERTISED_NOT_RUNTIME_VALIDATED'),
            ('FT_NOT_LISTED', {'MOCK_NOFT': '1'}, 0, 'PRE698_FRAME_TIMELINE_SOURCE=NOT_LISTED_NOT_PROVEN_UNSUPPORTED'),
            ('QUERY_UNAVAILABLE', {'MOCK_NOQUERY': '1'}, 0, 'PRE698_PERFETTO_QUERY_COMPLETED=false'),
            ('LATENCY_UNAVAILABLE', {'MOCK_BADLAT': '1'}, 0, 'PRE698_SURFACEFLINGER_LATENCY=UNVERIFIED'),
            ('WRONG_VERSION', {'MOCK_VERSION': '52'}, 17, 'PRE698_UNEXPECTED_VERSION_52_ABORT'),
            ('WRONG_MODEL', {'MOCK_MODEL': 'OTHER'}, 15, 'PRE698_UNEXPECTED_MODEL_ABORT'),
            ('WRONG_UID', {'MOCK_UID': '0'}, 13, 'PRE698_SHELL_UID_0_ABORT'),
            ('NO_DEVICE', {'MOCK_NODEVICE': '1'}, 11, 'PRE698_DEVICE_COUNT_0_ABORT'),
        ]
        for name, flags, code, phrase in cases:
            env = {**os.environ, 'NFSMW_ADB_BIN': str(adb), **flags}
            completed = subprocess.run(['bash', str(SCRIPT), 'preflight'],
                                       capture_output=True, text=True, env=env)
            if completed.returncode != code or phrase not in (completed.stdout + completed.stderr):
                print(f'PRE698_TEST_{name}=FAIL', file=sys.stderr)
                return 1
            print(f'PRE698_TEST_{name}=PASS')
    print('PRE698_SYNTHETIC_NO_REAL_DEVICE=TRUE')
    return 0


if __name__ == '__main__':
    raise SystemExit(run())
