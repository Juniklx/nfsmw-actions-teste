#!/usr/bin/env python3
"""PRE554: read-only metadata audit. Never infer Android runtime from static evidence."""
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
APK_SHA="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
OUT=Path("/tmp/nfsmw-pre554/report.json")

def verify():
    paths=[
        "docs/PRE511_ORIGINAL_V48_APK_RUNTIME_MARKERS_READONLY.json",
        "docs/PRE515_V48_DEX_GAME_ROOT_METHOD_REFS_READONLY.json",
        "docs/PRE551_PAL_ORIGINAL_ZZDATA4_PADDING_AND_VIRTUAL_RESOURCE_READONLY.json",
        "docs/PRE553_CANONICAL_CONTEXT_SYNC_RESULT.json",
    ]
    a,b,c,d=[json.loads(Path(p).read_text()) for p in paths]
    if not all(x.get("status")=="AUDIT_OK" for x in (a,b,c,d)):
        raise ValueError("One authenticated predecessor is not AUDIT_OK")
    if a.get("original_apk_sha256")!=APK_SHA or b.get("v48_apk_sha256")!=APK_SHA:
        raise ValueError("Original signed V48 identity mismatch")
    if not a.get("V48_apk_exact_hash_verified") or not b.get("exact_apk_hash_verified_again"):
        raise ValueError("V48 static hash verification absent")
    markers=a.get("historical_runtime_diagnostic_markers_present",{})
    if not markers.get("history_runtime_image_root") or not markers.get("history_runtime_absent_root"):
        raise ValueError("Native VFS markers absent from original V48")
    getters=[x for x in b.get("method_level_source_reference_evidence",[])
             if x.get("class")=="GameActivity" and x.get("method")=="getLibraries"]
    if len(getters)!=1 or not any("Ediciones$Edicion;->libreria" in x.get("field","")
             for x in getters[0].get("referenced_safe_fields",[])):
        raise ValueError("Compiled edition->library mapping absent")
    if c.get("actual_game_guest_loader_executed") is not False or c.get("BMW_tuning_enabled") is not False:
        raise ValueError("PRE551 was not an executed guest loader")
    if c.get("isolated_synthetic_RAM_resource_readback_SHA256")!="d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6":
        raise ValueError("Synthetic in-RAM fixture differs")
    if not d.get("prior_history_bytewise_preserved") or not d.get("postupdate_readback_bytewise_verified") or d.get("new_total_bytes")!=844481:
        raise ValueError("PRE553 context checkpoint changed")
    return {
        "stage":"PRE554_V48_ANDROID_EDITION_AND_VFS_PASSIVE_EVIDENCE_GATE",
        "status":"AUDIT_OK",
        "source_original_signed_V48_sha256":APK_SHA,
        "pre511_vfs_static_markers_verified":True,
        "pre515_compiled_edition_lib_selection_verified":True,
        "pre551_only_virtual_in_ram_readback":True,
        "pre553_context_history_preserved":True,
        "phone_versionCode_48_independently_observed":False,
        "device_session_guest_edition":"UNKNOWN",
        "device_session_library_maps_observed":False,
        "device_session_vfs_mount_branch_proven":False,
        "device_session_vfs_mount_source_proven":False,
        "actual_game_guest_loader_executed":False,
        "synthetic_BMW_engine_accepted_in_game":False,
        "actual_BMW_tuning_bought_or_persistent":False,
        "next_gate":"COLLECT_REDACTED_DEVICE_SESSION_PROBE",
        "APK_built":False,"game_assets_modified":False,
        "save_modified":False,"signing_material_accessed":False,
        "BMW_tuning_enabled":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try: result=verify()
    except Exception as e:
        result={"stage":"PRE554_V48_ANDROID_EDITION_AND_VFS_PASSIVE_EVIDENCE_GATE",
                "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:220],
                "APK_built":False,"game_assets_modified":False,"save_modified":False,
                "signing_material_accessed":False,"BMW_tuning_enabled":False}
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PRE554_STATUS",result["status"],flush=True)
    print("PRE554_EDITION",result.get("device_session_guest_edition","UNKNOWN"),flush=True)
    print("PRE554_VFS_RUNTIME_PROVEN",result.get("device_session_vfs_mount_branch_proven",False),flush=True)
    print("PRE554_NEXT",result.get("next_gate","FAIL"),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__": raise SystemExit(main())
