#!/usr/bin/env python3
"""PRE266: disposable V37-stage sources + guarded BMW category patch integration.

NEVER builds game/APK or touches signer. A guarded, default-OFF patch is
applied to the same disposable restore as PRE246 and PRE247. Do not confuse
source preflight with runtime availability of actual BMW upgrade packages.
"""
from __future__ import annotations
import argparse,hashlib,json,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre107_restore_isolated import restore
from pre246_passive_money_probe_patch import apply as add_money
from pre247_pal_meter_passive_probe_patch import apply as add_meters
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre264_bmw_hero_menu_patch_dryrun import (
  SOURCE,SOURCE_SHA,FUNCTION,MODEL_CMP,ANCHORS,INJECTION,
  patch_memory_only,
)

OUT=Path("/tmp/nfsmw-pre266/PRE266_BMW_MENU_V38_DISPOSABLE_PREFLIGHT.json")
PRE264_CANDIDATE_SHA="1dc5745263d68e186e66545f8795b2a11fffc8d5011aec74f3ce8a9256afe11c"
MARKER="NFSMW_PRE264_BMW_MENU_LOCAL"

def sha(blob):return hashlib.sha256(blob).hexdigest()

def stage(root):
    pal=root/SOURCE.removeprefix("workspace/")
    # root is /.../restore/workspace
    old=pal.read_bytes()
    if sha(old)!=SOURCE_SHA:raise ValueError("Unexpected PAL .5 source after V37 passive probes")
    expected=patch_memory_only(old)
    if expected["dryrun_candidate_sha256"]!=PRE264_CANDIDATE_SHA:
        raise ValueError("Candidate SHA changed from approved PRE264")
    text=old.decode("utf-8")
    body=body_for_function(text,FUNCTION)
    if body.count(MODEL_CMP)!=1:raise ValueError("Unexpected HeroCar compare count")
    if any(body.count(a)!=1 for a in ANCHORS):raise ValueError("Missing PPC branch anchors")
    if MARKER in text:raise ValueError("BMW patch already applied: refuse duplicate")
    if INJECTION.strip().count("#if")!=1 or INJECTION.count("#endif")!=1:
        raise ValueError("Not a guarded patch")
    modified=body.replace(MODEL_CMP,MODEL_CMP+INJECTION,1)
    staged=text.replace(body,modified,1).encode("utf-8")
    if sha(staged)!=PRE264_CANDIDATE_SHA:raise ValueError("Nonlocal BMW patch detected")
    pal.write_bytes(staged)
    if sha(pal.read_bytes())!=PRE264_CANDIDATE_SHA:
        raise ValueError("BMW patch write did not verify")
    if staged.count(MARKER.encode())!=1:raise ValueError("Duplicate BMW patch marker")
    if staged.replace(INJECTION.encode(),b"",1)!=old:
        raise ValueError("BMW patch exact reversal mismatch")
    if staged.count(b"REX_LOAD_U32(")!=old.count(b"REX_LOAD_U32("):
        raise ValueError("Guest load count changed")
    if staged.count(b"REX_STORE_U32(")!=old.count(b"REX_STORE_U32("):
        raise ValueError("Guest store count changed")
    return {"path":SOURCE,"pre_sha256":SOURCE_SHA,
            "candidate_sha256":sha(staged),"marker":MARKER,
            "feature_macro":"NFSMW_PRE264_BMW_MENU_ENABLE",
            "macro_explicitly_defined":False,
            "no_original_guest_mem_calls_changed":True,
            "exact_reversible":True,"applied_to_disposable_files":True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    if not args.run_id.isdecimal():raise ValueError("Invalid run-id")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE266_V38_BMW_CATEGORY_PATCH_INTEGRATION_PREFLIGHT",
            "phase":"INIT","status":"FAILED","apk_built":False,"release_signed":False,
            "signer_touched":False,"original_save_touched":False,
            "gameplay_tested":False,"source_persisted":False,
            "feature_enabled":False,"feature_validated_in_game":False}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre266_") as d:
            tmp=Path(d)
            archive=tmp/"pre99.tar.gz"
            result["phase"]="FETCH_AUTHENTICATED_PRE99"
            download(drive_client(),archive)
            digest,_,size=sha_file(archive)
            if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 digest mismatch")
            result["pre99_verified_sha256"]=digest
            result["phase"]="RESTORE_DISPOSABLE_SNAPSHOT"
            extracted=tmp/"restore";extracted.mkdir()
            restore(archive,extracted)
            archive.unlink(missing_ok=True)
            root=extracted/"workspace"
            result["phase"]="APPLY_V37_MONEY_TRACE"
            money=add_money(root)
            if money.get("money_traces")!=8:raise ValueError("Money probe count changed")
            result["money_trace_sites"]=8
            result["phase"]="APPLY_V37_FLOAT_METER_TRACE"
            meters=add_meters(root)
            if meters.get("combined_money_and_meter_probe_sites")!=16:
                raise ValueError("V37 resource probe count changed")
            result["total_v37_passive_sites"]=16
            result["phase"]="INSERT_PRE264_GUARDED_BMW_CODE"
            result["bmw_patch"]=stage(root)
            result["phase"]="VERIFY_SOURCE_ONLY_GATES"
            source_text=(root/SOURCE.removeprefix("workspace/")).read_text(encoding="utf-8")
            if source_text.count(MARKER)!=1 or source_text.count(INJECTION)!=1:
                raise ValueError("BMW marker/guard mismatch")
            result["status"]="AUDIT_OK"
            result["phase"]="COMPLETE"
            result["meaningful_limitations"]=[
              "Does NOT include all V37 SDL/Android input/UI/C3 patches; only passive generated game source layer",
              "Does NOT measure BMW package levels or guarantee performance upgrades",
              "Does NOT build C++ game DLL, APK, sign, or test runtime",
              "The preprocessor flag is OFF unless explicitly enabled in future build",
              "No release decision until GetMaxLevel/invalid zero-package screen behavior is proven safe",
              "Only PAL game generated source changed in disposable runner; USA library unchanged",
            ]
    except Exception as error:
        result["error_type"]=type(error).__name__
        result["failed_phase"]=result["phase"]
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE266_STATUS",result["status"])
    print("PRE266_PHASE",result["phase"])
    print("PRE266_16_PASSIVE_V37_SITES",result.get("total_v37_passive_sites",0))
    print("PRE266_GUARD_DISABLED",not result["feature_enabled"])
    if result["status"]!="AUDIT_OK":
        print("PRE266_FAILURE",result.get("error_type"),result.get("failed_phase"))
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":sys.exit(main())
