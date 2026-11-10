#!/usr/bin/env python3
"""PRE637: compile real ARM64 libmain.so with PRE635 diagnostic C3 on V49 replay.
PRE636 source verification mandatory; all work in temporary PRE99 restore.
No APK, Gradle, signing material, saves, or game assets modified.
"""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
import pre288_bmw_feature_on_pal_native_preflight as native
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre636_v49_c3_replay_noapk as p636
import pre635_c3_duplicate_request_trace_dryrun as p635
import pre447_bmw_lookup_route_probe_dryrun as p447
import pre622_bmw_attr_host_value_probe_ram_only as p622
from pre194_c3_guard_pal_diagnostic_patch import PATCHED_SHA as PRE194_SHA
from pre285_bmw_arm64_ndk_logger_preflight import find_ndk

OUT=Path("/tmp/nfsmw-pre637/PRE637_V49_C3_ARM64_NOAPK.json")
EXPECTED_PROPOSAL=p636.EXPECTED_PROPOSAL
EVIDENCE={}
PHASE="START"
def sha(b):return hashlib.sha256(b).hexdigest()

def source_stage(root):
    global PHASE,EVIDENCE
    PHASE="V49_SOURCE_REPLAY"
    v49=p636.stage_v49_once(root)
    if (v49.get("pre434_two_guest_shards_feature_on") is not True
       or v49.get("pre452_passive_route_staged") is not True
       or v49.get("pre626_previous_PRE429_PRE447_nitro_preserved") is not True):
        raise ValueError("V49 full inherited callback stages missing")
    path=root/p636.C3_PATH
    original=path.read_bytes()
    if sha(original)!=PRE194_SHA:
        raise ValueError("V49 C3 preflight source hash differs")
    PHASE="PRE635_SHA_PINNED_C3_PATCH"
    proposed=p635.patch_p194(original)
    if sha(proposed)!=EXPECTED_PROPOSAL:
        raise ValueError("PRE635 candidate SHA differs")
    if proposed.replace(p635.NEW.encode(),p635.OLD.encode(),1)!=original:
        raise ValueError("PRE635 reversibility not established")
    path.write_bytes(proposed)
    if sha(path.read_bytes())!=EXPECTED_PROPOSAL:
        raise ValueError("PRE635 writeback of disposable C3 source differs")
    EVIDENCE.update({
      "pre194_original_sha256":sha(original),
      "pre635_candidate_source_sha256":sha(proposed),
      "pre635_exact_reversal_verified":True,
      "v49_bmw_callbacks_replayed":True,
      "pre398_nitro_preserved":True,
      "pre635_only_c3_file_changed_by_new_stage":True,
      "diagnostic_inside_safe_guard_only":True
    })
    PHASE="PRE635_NATIVE_STAGE_READY"
    return {**v49,"pre637_pre635_c3_applied_in_temp_tree":True,
             "pre637_c3_source_sha256":sha(proposed)}

def check_output(build,original_find):
    global PHASE,EVIDENCE
    PHASE="VERIFY_LINKED_ARM64_LIBMAIN"
    outputs=original_find(build)
    if len(outputs)!=1 or not native.arm64_elf(outputs[0]):
        raise ValueError("Expected exactly one actual ARM64 libmain.so")
    binary=outputs[0].read_bytes()
    for tag in (b"NFSMW_PRE635_C3_TWOREQUEST_TRACE",
       b"NFSMW_PRE194_C3",b"NFSMW_PRE398_GLOBAL_NITRO_FULL",
       b"NFSMW_PRE429_ENTRY",b"NFSMW_PRE429_LEVEL",
       b"NFSMW_PRE447_ROUTE",b"NFSMW_PRE622_ATTR_VALUE"):
        if tag not in binary:
            raise ValueError("Native ARM64 libmain missing required diagnostics/Nitro")
    ndk=find_ndk()["ndk"]
    nm=ndk/"toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
    run=subprocess.run([str(nm),"-D","--defined-only",str(outputs[0])],
         capture_output=True,text=True,timeout=100,env=native.clean_env())
    if run.returncode:
        raise ValueError("Cannot inspect native dynamic callback table")
    required=("NFSMW_PRE429_TRACE_ENTRY","NFSMW_PRE429_TRACE_LEVEL",
      "NFSMW_PRE447_ROUTE","NFSMW_PRE622_ATTR_VALUE")
    counts={}
    for symbol in required:
        count=len(re.findall(r"(?m)^[0-9A-Fa-f]+\s+[Tt]\s+"+re.escape(symbol)+r"$",run.stdout))
        if count!=1:
            raise ValueError("Expected exactly one callback export: "+symbol)
        counts[symbol]=count
    EVIDENCE.update({
        "arm64_elf_sha256":sha(binary),
        "arm64_elf_size":len(binary),
        "all_4_bmw_callbacks_exported_once":True,
        "callback_counts":counts,
        "pre635_marker_linked_in_actual_elf":True,
        "pre194_fallback_marker_present":True,
        "pre398_nitro_marker_present":True,
    })
    PHASE="ARM64_NATIVE_LINK_AND_SYMBOLS_PASS"
    return outputs

def audit(run_id):
    global PHASE
    evidence_file=Path("docs/PRE625_BMW_HOST_ATTR_ARM64_NATIVE_LINK_RESULT.json")
    old=json.loads(evidence_file.read_text(encoding="utf-8"))
    if (old.get("status")!="AUDIT_OK" or old.get("native_build_ok") is not True
        or old.get("native_arm64_elf") is not True
        or old.get("APK_built") is not False
        or old.get("signing_material_accessed") is not False):
        raise ValueError("PRE625 earlier native baseline gate not verified")
    original=(native.replay_v37,native.stage_logger,native.find_outputs,
              native.FEATURE,native.CALLBACK,native.PAL_FILENAME)
    orig_finder=native.find_outputs
    try:
        native.replay_v37=v46.replay_v46_sources
        native.stage_logger=source_stage
        native.find_outputs=lambda build:check_output(build,orig_finder)
        native.FEATURE=p447.FLAG
        native.CALLBACK=p622.SYMBOL
        native.PAL_FILENAME=p447.FILES["lookup"][0]
        PHASE="FULL_NATIVE_REBUILD"
        result=native.audit(Path(__file__).resolve().parents[2])
    finally:
        (native.replay_v37,native.stage_logger,native.find_outputs,
         native.FEATURE,native.CALLBACK,native.PAL_FILENAME)=original
    ok=(result.get("status")=="AUDIT_OK"
        and result.get("cmake_configure",{}).get("ok") is True
        and result.get("production_native_build",{}).get("ok") is True
        and result.get("linked_library",{}).get("arm64_elf") is True
        and EVIDENCE.get("pre635_marker_linked_in_actual_elf") is True
        and EVIDENCE.get("all_4_bmw_callbacks_exported_once") is True)
    return {
      "stage":"PRE637_V49_PRE635_ARM64_NATIVE_NO_APK",
      "status":"AUDIT_OK" if ok else "NOT_APPROVED",
      "phase":PHASE,
      "run_id":run_id,
      "PRE99_sha256":result.get("backup_sha256"),
      "native_cmake_ok":result.get("cmake_configure",{}).get("ok"),
      "native_build_ok":result.get("production_native_build",{}).get("ok"),
      "native_arm64_elf":result.get("linked_library",{}).get("arm64_elf"),
      "real_linked_library_sha256":result.get("linked_library",{}).get("sha256"),
      "evidence":EVIDENCE,
      "source_replay_not_binary_equivalence_to_signed_V49":True,
      "APK_built":False,"signed":False,"signing_material_accessed":False,
      "save_modified":False,"game_assets_modified":False,
      "guest_runtime_executed":False,"FPS_gain_proven":False,
    }

def main():
    a=argparse.ArgumentParser();a.add_argument("--run-id",required=True)
    args=a.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:
        if not args.run_id.isdecimal():raise ValueError("Non-numeric workflow ID")
        result=audit(args.run_id)
    except Exception as e:
        result={"stage":"PRE637_V49_PRE635_ARM64_NATIVE_NO_APK",
            "status":"FAILED","phase":PHASE,"error_type":type(e).__name__,
            "error_summary":str(e)[:190] if isinstance(e,ValueError) else "Native gate exception",
            "APK_built":False,"signed":False,"signing_material_accessed":False}
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE637_STATUS="+result["status"])
    print("PRE637_PHASE="+str(result.get("phase","none")))
    print("PRE637_NATIVE_BUILD_OK="+str(result.get("native_build_ok",False)))
    print("PRE637_PRE635_LINKED="+str(result.get("evidence",{}).get("pre635_marker_linked_in_actual_elf",False)))
    print("PRE637_APK_BUILT=false")
    print("PRE637_SIGNING_ACCESSED=false")
    print("PRE637_ERROR_TYPE="+str(result.get("error_type","none")))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
