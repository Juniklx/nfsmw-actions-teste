#!/usr/bin/env python3
"""PRE282: disposable V37 PAL probes + PRE264/PRE281 guarded integration.

NO RELEASE: restores authenticated PRE99 temporarily; applies the two
existing V37 money/meter source probes; introduces two feature-gated patches
in separate source shards; verifies both patches are byte-reversible.
Fails closed on duplicate application, unexpected SHA, or non-local edits.
No compiled guest code, Android APK, signing keys or user game saves.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download
from pre107_restore_isolated import restore
from pre246_passive_money_probe_patch import apply as add_money
from pre247_pal_meter_passive_probe_patch import apply as add_meter
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre264_bmw_hero_menu_patch_dryrun import (
  SOURCE as MENU_SOURCE, SOURCE_SHA as MENU_SHA, FUNCTION as MENU_FUNCTION,
  MODEL_CMP, ANCHORS, INJECTION as MENU_INJECTION,
  patch_memory_only as preview_menu
)
from pre281_bmw_null_header_guard_dryrun import (
  SOURCE as HEADER_SOURCE, PIN as HEADER_SHA, TARGET as HEADER_FUNCTION,
  ANCHOR as HEADER_ANCHOR, LATER_DEREF, EPILOGUE,
  INJECTION as HEADER_INJECTION, patch_in_memory as preview_header
)

OUT=Path("/tmp/nfsmw-pre282/PRE282_BMW_MENU_HEADER_DISPOSABLE_PREFLIGHT.json")
PINS={
   MENU_SOURCE:(MENU_SHA,"1dc5745263d68e186e66545f8795b2a11fffc8d5011aec74f3ce8a9256afe11c"),
   HEADER_SOURCE:(HEADER_SHA,"b71f40a1fd1770fba249192ef03c78a641f575e8a6bca9511efedf75dad54a7e"),
}
GUEST_MEM=("REX_LOAD_U8(", "REX_LOAD_U16(", "REX_LOAD_U32(", "REX_LOAD_U64(",
           "REX_STORE_U8(", "REX_STORE_U16(", "REX_STORE_U32(", "REX_STORE_U64(")

def sha(value:bytes)->str:
    return hashlib.sha256(value).hexdigest()

def compare_no_impact(before:str,after:str)->None:
    for needle in GUEST_MEM+("REX_CALL_INDIRECT_FUNC(", "DEFINE_REX_FUNC(",
                              "__imp__sub_82575370(ctx, base);"):
        if before.count(needle)!=after.count(needle):
            raise ValueError("Unexpected guest call or memory expression change: "+needle)

def stage_file(root:Path,source:str,oldsha:str,newsha:str,oldbody:str,newbody:str,marker:str)->dict:
    local=root/source.removeprefix("workspace/")
    old=local.read_bytes()
    if sha(old)!=oldsha:
        raise ValueError("Authenticated source digest mismatch: "+source)
    original=old.decode("utf-8")
    if marker in original:raise ValueError("Duplicate patch marker present")
    if original.count(oldbody)!=1:raise ValueError("Original function not unique")
    new=original.replace(oldbody,newbody,1)
    compare_no_impact(original,new)
    if new.replace(newbody,oldbody,1)!=original:
        raise ValueError("Stage not reversible")
    if sha(new.encode("utf-8"))!=newsha:
        raise ValueError("Candidate digest mismatch against earlier PRE264/PRE281")
    local.write_bytes(new.encode("utf-8"))
    if sha(local.read_bytes())!=newsha or local.read_text(encoding="utf-8").count(marker)!=1:
        raise ValueError("Staged source readback mismatch")
    return {
      "relative_source":source,"base_sha256":oldsha,
      "candidate_sha256":newsha,
      "unique_marker":marker,
      "reversible_exactly":True,"guest_call_and_access_counts_unchanged":True,
      "staged_in_temporary_restore":True,
    }

def menu_patch(root:Path)->dict:
    p=root/MENU_SOURCE.removeprefix("workspace/")
    old=p.read_bytes()
    result=preview_menu(old)
    if result["dryrun_candidate_sha256"]!=PINS[MENU_SOURCE][1]:
        raise ValueError("PRE264 SHA-invariant regression")
    source=old.decode("utf-8")
    body=body_for_function(source,MENU_FUNCTION)
    if body.count(MODEL_CMP)!=1 or any(body.count(a)!=1 for a in ANCHORS):
        raise ValueError("PRE264 anchors changed")
    after=body.replace(MODEL_CMP,MODEL_CMP+MENU_INJECTION,1)
    if after.replace(MENU_INJECTION,"",1)!=body:raise ValueError("Menu change not local")
    return stage_file(root,MENU_SOURCE,*PINS[MENU_SOURCE],body,after,"NFSMW_PRE264_BMW_MENU_LOCAL")

def header_patch(root:Path)->dict:
    p=root/HEADER_SOURCE.removeprefix("workspace/")
    old=p.read_bytes()
    result=preview_header(old)
    if result["candidate_source_sha256"]!=PINS[HEADER_SOURCE][1]:
        raise ValueError("PRE281 SHA-invariant regression")
    source=old.decode("utf-8")
    body=body_for_function(source,HEADER_FUNCTION)
    if any(body.count(a)!=1 for a in (HEADER_ANCHOR,LATER_DEREF,EPILOGUE)):
        raise ValueError("PRE281 anchors changed")
    if not body.index(HEADER_ANCHOR)<body.index(LATER_DEREF)<body.index(EPILOGUE):
        raise ValueError("PRE281 guard outside verified first-deref window")
    newbody=body.replace(HEADER_ANCHOR,HEADER_ANCHOR+HEADER_INJECTION,1)
    if newbody.replace(HEADER_INJECTION,"",1)!=body:
        raise ValueError("PRE281 not locally reversible")
    return stage_file(root,HEADER_SOURCE,*PINS[HEADER_SOURCE],body,newbody,
                      "NFSMW_PRE281: optional null-selection guard")

def negative_tests(root:Path)->dict:
    # Exact current bytes are only in this temporary restore, not a user file.
    tests={}
    for label,fn,source in (("menu",menu_patch,MENU_SOURCE),
                            ("header",header_patch,HEADER_SOURCE)):
        try:
            fn(root)
            tests[label+"_duplicate_rejected"]=False
        except ValueError:
            tests[label+"_duplicate_rejected"]=True
        path=root/source.removeprefix("workspace/")
        unchanged=path.read_bytes()
        # Do NOT write a modified candidate even to the temporary tree:
        # preview rejects tampered data passed in memory.
        if label=="menu":
            preview=preview_menu
        else:
            preview=preview_header
        altered=bytearray(unchanged)
        altered[-100]^=1
        try:
            preview(bytes(altered))
            tests[label+"_unrecognized_sha_rejected"]=False
        except ValueError:
            tests[label+"_unrecognized_sha_rejected"]=True
        if path.read_bytes()!=unchanged:
            raise ValueError("Negative tests mutated staged source")
    return tests

def audit():
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre282_") as temp:
        top=Path(temp)
        archive=top/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,length=sha_file(archive)
        if digest!=EXPECTED_SHA256 or length!=EXPECTED_BYTES:
            raise ValueError("PRE99 backup fingerprint mismatch")
        extraction=top/"restore"
        extraction.mkdir()
        restore(archive,extraction)
        archive.unlink(missing_ok=True)
        root=extraction/"workspace"

        # PRE266 workflow already checked the order of these two V37 probes.
        money=add_money(root)
        if money.get("money_traces")!=8:raise ValueError("Expected V37 money probes=8")
        meters=add_meter(root)
        if meters.get("combined_money_and_meter_probe_sites")!=16:
            raise ValueError("Expected combined V37 passive probes=16")

        menu=menu_patch(root)
        header=header_patch(root)
        if menu["relative_source"]==header["relative_source"]:
            raise ValueError("Menu and header unexpectedly share shard")

        # These two #if toggles are not defined/enabled in this workflow.
        sources=[(root/s.removeprefix("workspace/")).read_text(encoding="utf-8")
                 for s in PINS]
        toggles=("NFSMW_PRE264_BMW_MENU_ENABLE",
                 "NFSMW_PRE281_BMW_EMPTY_HEADER_GUARD_ENABLE")
        for source,flag in zip(sources,toggles):
            if "#if defined("+flag+") && "+flag not in source:
                raise ValueError("BMW guard condition changed")
            if "#define "+flag+" 1" in source or "#define "+flag+"\t1" in source:
                raise ValueError("A guard has been enabled unexpectedly")
        negatives=negative_tests(root)
        if not all(negatives.values()):
            raise ValueError("Fail-closed negative test regression")
        return {
            "stage":"PRE282_BMW_V37_DISPOSABLE_MENU_PLUS_HEADER_GUARDS",
            "status":"AUDIT_OK",
            "authenticated_pre99_sha256":digest,
            "v37_passive_money_trace_sites":8,
            "v37_combined_money_and_float_trace_sites":16,
            "menu_patch":menu,
            "empty_selection_guard":header,
            "feature_macros":list(toggles),
            "macros_enabled":False,
            "negative_tests":negatives,
            "vtable_plus12_actual_target_proven":False,
            "BMW_specific_car_ownership_guard_proven":False,
            "actual_BMW_upgrade_package_counts":None,
            "integrated_full_V37_Android_SDL_graphics_and_C3":False,
            "release_approved":False,
            "limitations":[
               "Both changes are staged only in disposable restored source shards; the source of truth is unchanged",
               "This combines only V37's generated money/meter probes; it is NOT a full V37 SDL/Android/C3/game build tree",
               "The actual virtual method at vtable+12 is still unproven; PRE281 candidate remains hypothesis",
               "PRE264 scoped main-menu change treats BMW type 41 regardless of ownership; a career-only guard is not proven",
               "Preventing a null dereference does not ensure a valid zero-packages UI or car upgrades",
               "No guest execution or native compile; no APK build/signing, no Android test, no save changes"
            ],
            "game_source_persisted":False,"apk_built":False,
            "signed":False,"signing_material_accessed":False,
            "game_saves_accessed":False,
        }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    if not args.run_id.isdecimal():raise ValueError("Numeric run ID required")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    r={"stage":"PRE282_BMW_V37_DISPOSABLE_MENU_PLUS_HEADER_GUARDS",
       "status":"FAILED","phase":"AUTHENTICATED_DISPOSABLE_SOURCE_PREFLIGHT",
       "apk_built":False,"game_source_persisted":False}
    try:r=audit()
    except Exception as err:r["error_type"]=type(err).__name__
    r["github_run_id"]=args.run_id
    r["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE282_STATUS",r["status"])
    print("PRE282_V37_PASSIVE_SITES",r.get("v37_combined_money_and_float_trace_sites"))
    print("PRE282_MENU_SHA",r.get("menu_patch",{}).get("candidate_sha256"))
    print("PRE282_HEADER_SHA",r.get("empty_selection_guard",{}).get("candidate_sha256"))
    print("PRE282_FAIL_CLOSED",r.get("negative_tests"))
    print("PRE282_RELEASE_APPROVED",r.get("release_approved"))
    if r["status"]!="AUDIT_OK":print("PRE282_ERROR",r.get("error_type"))
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    sys.exit(main())
