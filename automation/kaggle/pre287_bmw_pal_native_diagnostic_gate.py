#!/usr/bin/env python3
"""PRE287 BMW PAL diagnostic: fail-closed full-native link acceptance, NO APK."""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from pre286_bmw_real_pal_libmain_cmake_nosign import audit, CALLBACK

OUT = Path("/tmp/nfsmw-pre287/PRE287_BMW_PAL_NATIVE_DIAGNOSTIC_GATE.json")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",required=True)
    args=parser.parse_args()
    if not args.run_id.isdecimal():
        raise ValueError("Run ID must be numeric")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE287_BMW_PAL_DIAGNOSTIC_NATIVE_GATE",
            "run_id":args.run_id,"status":"FAILED",
            "apk_built":False,"apk_signed":False,"save_modified":False,
            "release_approved":False,
            "observed_bmw_tuning_fixed":False}
    try:
        baseline=audit(Path(__file__).resolve().parents[2])
        logger=baseline.get("pre283_native_module",{})
        linked=baseline.get("linked_library",{})
        checks={
            "pre286_internal_audit_ok":baseline.get("status")=="AUDIT_OK",
            "cmake_configured":baseline.get("cmake_configure",{}).get("ok") is True,
            "real_pal_nfsmw_target":baseline.get("selected_native_target")=="nfsmw",
            "real_arm64_libmain_linked":baseline.get("game_dso_linked") is True,
            "arm64_elf":linked.get("arm64_elf") is True,
            "callback_defined_once":linked.get("defined_callback_count")==1,
            "default_off":logger.get("macro_defined_in_source") is False,
            "logger_registered_once":logger.get("cmake_module_registered_once") is True,
            "source_reversible":logger.get("source_exactly_reversible") is True,
            "guest_operations_unchanged":logger.get("no_original_guest_memory_ops_or_calls_changed") is True,
            "no_apk":baseline.get("apk_built") is False,
            "no_signing":baseline.get("signed") is False,
            "no_save_access":baseline.get("saves_accessed") is False,
        }
        result["checks"]=checks
        result["linked_library"]={k:linked.get(k) for k in
             ("filename","sha256","size","arm64_elf","defined_callback_count")}
        result["callback"]=CALLBACK
        result["baseline_status"]=baseline.get("status")
        result["status"]="AUDIT_OK" if all(checks.values()) else "BLOCKED_INTEGRATION_GATE"
    except Exception as exc:
        result["error_type"]=type(exc).__name__
        result["error_message"]=str(exc)[:350]
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE287_STATUS",result["status"])
    for k,v in result.get("checks",{}).items():print("PRE287_CHECK",k,v)
    print("PRE287_APK_BUILT",False)
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    sys.exit(main())
