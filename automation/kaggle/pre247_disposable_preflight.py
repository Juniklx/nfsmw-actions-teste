#!/usr/bin/env python3
"""PRE247: authenticated PRE99 disposable money + meter probe preflight.

No Android build, signer, save, gameplay activation or Drive mutation.
"""
from __future__ import annotations
import json
import sys
import tempfile
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client, download
from pre107_restore_isolated import restore
from pre246_passive_money_probe_patch import apply as add_money
from pre247_pal_meter_passive_probe_patch import apply as add_meters

OUT = Path("/tmp/nfsmw-pre247/NFSMW_PRE247_PAL_CHEATS_PASSIVE_INTEGRATION_PREFLIGHT.json")

def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "stage": "PRE247_PAL_PASSIVE_ALL_RESOURCES_PREFLIGHT",
        "status": "FAILED", "phase": "START",
        "apk_built": False, "android_build": False, "signer_accessed": False,
        "save_files_changed": False, "drive_files_changed": False,
        "cheats_enabled": False, "game_executed": False,
        "source_tree_persistent_changes": False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre247_") as td:
            archive = Path(td) / "pre99.tar.gz"
            result["phase"] = "VERIFY_PRE99"
            download(drive_client(), archive)
            digest, _, size = sha_file(archive)
            if digest != EXPECTED_SHA256 or size != EXPECTED_BYTES:
                raise ValueError("PRE247: authenticated PRE99 digest/size mismatch")
            result["pre99_authenticated"] = True
            tmp = Path(td) / "restore"
            tmp.mkdir()
            result["phase"] = "DISPOSABLE_RESTORE"
            restore(archive, tmp)
            game_root = tmp / "workspace"
            result["phase"] = "DISPOSABLE_MONEY_PROBE"
            result["money"] = add_money(game_root)
            if result["money"]["money_traces"] != 8:
                raise ValueError("PRE247: money site count changed")
            result["phase"] = "DISPOSABLE_METER_PROBES"
            result["meters"] = add_meters(game_root)
            if result["meters"]["passive_float_probes"] != 8:
                raise ValueError("PRE247: meter site count changed")
            result["total_passive_sites"] = 16
            result["phase"] = "COMPLETE"
            result["status"] = "AUDIT_OK"
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["failed_phase"] = result["phase"]
        if isinstance(exc, ValueError) and str(exc).startswith("PRE247:"):
            result["safe_error"] = str(exc)[:150]
        print("PRE247_PREFLIGHT_ERROR", type(exc).__name__, result["phase"])
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print("PRE247_PREFLIGHT_STATUS", result["status"])
    print("PRE247_PASSIVE_SITES", result.get("total_passive_sites", 0))
    return 0 if result["status"] == "AUDIT_OK" else 1

if __name__ == "__main__":
    sys.exit(main())
