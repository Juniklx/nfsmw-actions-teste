#!/usr/bin/env python3
"""PRE636: authenticated PRE99 -> V46 -> V47 -> V48 -> V49 source replay.
No APK, no NDK build, no signing or user save access. PRE635 tested in memory.
Replaying the same staging functions is not byte proof of a signed V49 ELF.
"""
from __future__ import annotations
import hashlib,json,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre107_restore_isolated import restore
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre434_build_signed_v47_bmw_passive_diag as p434
import pre626_build_signed_v49_bmw_attr_diag as p626
import pre635_c3_duplicate_request_trace_dryrun as p635
from pre194_c3_guard_pal_diagnostic_patch import PATCHED_SHA as C3_SHA

REPORT=Path("/tmp/nfsmw-pre636/PRE636_V49_C3_REPLAY.json")
C3_PATH="nativo/app/src/nfsmw_nativo_dibujos.cpp"
CMAKE_PATH="nativo/app/CMakeLists.txt"
EXPECTED_PROPOSAL="1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
def sha(b):return hashlib.sha256(b).hexdigest()

def stage_v49_once(root):
    # PRE431 replay_v46_sources already invokes the actual PRE292 menu stage.
    # PRE434 normally invokes that menu stage again; skip ONLY that duplicate.
    # This is disposable source replay, not a replacement for a V49 release build.
    prev=p434.ORIGINAL_STAGE
    def verified_previous_menu(r):
        cmake=(r/CMAKE_PATH).read_text(encoding="utf-8")
        if cmake.count(v46.PRE292_REGISTER)!=1:
            raise ValueError("PRE292 registration not unique before V47")
        return {"menu_registered_once":True}
    try:
        p434.ORIGINAL_STAGE=verified_previous_menu
        return p626.stage_v49(root)
    finally:
        p434.ORIGINAL_STAGE=prev

def audit():
    report={"stage":"PRE636_V49_C3_REPLAY", "status":"FAIL_CLOSED",
      "utc":datetime.now(timezone.utc).isoformat(), "source_archive_verified":False,
      "exact_signed_v49_elf_equivalence_verified":False,
      "release_signing_material_accessed":False, "APK_built":False,
      "ARM64_compiled":False, "original_drive_modified":False,
      "user_save_modified":False,"temporary_sources_only":True}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre636_") as t:
            d=Path(t);arc=d/"pre99.tar.gz"
            download(drive_client(),arc)
            digest,_,size=sha_file(arc)
            report["pre99_sha256"]=digest;report["pre99_bytes"]=size
            if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
                raise ValueError("PRE99 SHA/size mismatch")
            report["source_archive_verified"]=True
            dest=d/"restored";dest.mkdir()
            restore(arc,dest);arc.unlink(missing_ok=True)
            root=dest/"workspace"
            stages=v46.replay_v46_sources(root,Path(__file__).resolve().parents[2])
            if stages["PRE398"]["cheat_enabled"] is not True:
                raise ValueError("PRE398 Nitro source not preserved")
            v49=stage_v49_once(root)
            if (v49.get("pre434_two_guest_shards_feature_on") is not True
              or v49.get("pre452_passive_route_staged") is not True
              or v49.get("pre626_previous_PRE429_PRE447_nitro_preserved") is not True):
                raise ValueError("V47/V48/V49 staging invariants failed")
            c3=(root/C3_PATH).read_bytes()
            report["v49_replayed_c3_sha256"]=sha(c3)
            if sha(c3)!=C3_SHA:
                raise ValueError("V49 replay C3 does not equal authenticated PRE194")
            candidate=p635.patch_p194(c3)
            if sha(candidate)!=EXPECTED_PROPOSAL:
                raise ValueError("PRE635 dry-run output differs from audited prototype")
            if candidate.replace(p635.NEW.encode(),p635.OLD.encode(),1)!=c3:
                raise ValueError("PRE635 exact reverse failure")
            try:p635.patch_p194(candidate)
            except ValueError:pass
            else:raise ValueError("PRE635 double patch not rejected")
            cmake=(root/CMAKE_PATH).read_text()
            expected_regs=(
                "nfsmw_bmw_trace_pre431.cpp",
                "nfsmw_bmw_route_pre448.cpp",
                "nfsmw_bmw_attr_value_pre625.cpp",
            )
            for fn in expected_regs:
                if cmake.count(fn)!=1:
                    raise ValueError("Expected V49 native callback registration missing")
            report.update({
                "status":"AUDIT_OK_V49_SOURCE_REPLAY",
                "v46_stage_names":list(stages.keys()),
                "c3_source_authenticated_p194":True,
                "pre635_candidate_sha256":sha(candidate),
                "pre635_exact_reverse_verified":True,
                "pre635_double_application_rejected":True,
                "pre635_bytes_added":len(candidate)-len(c3),
                "pre398_nitro_preserved":True,
                "pre434_dual_trace_preserved":True,
                "pre452_route_preserved":True,
                "pre626_attr_value_preserved":True,
                "v49_stage_checks":{k:v for k,v in v49.items()
                  if k.startswith("pre626_") and isinstance(v,(bool,int,str))},
                "source_provenance":"PRE99 SHA pinned + V46/V47/V48/V49 staging replay",
                "next_gate":"ARM64 compile/link in disposable tree only",
            })
    except Exception as e:
        report["error_type"]=type(e).__name__
        report["error_phase_hint"]=str(e)[:180] if isinstance(e,ValueError) else "audit exception"
    finally:
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
        print("PRE636_STATUS="+report["status"])
        print("PRE636_PRE99_VERIFIED="+str(report["source_archive_verified"]))
        print("PRE636_C3_SHA="+str(report.get("v49_replayed_c3_sha256","not available")))
        print("PRE636_PRE635_SHA="+str(report.get("pre635_candidate_sha256","not available")))
        print("PRE636_APK_BUILT=false")
        print("PRE636_ARM64_COMPILED=false")
        print("PRE636_ERROR_TYPE="+str(report.get("error_type","none")))
    return 0 if report["status"]=="AUDIT_OK_V49_SOURCE_REPLAY" else 1
if __name__=="__main__":sys.exit(audit())
