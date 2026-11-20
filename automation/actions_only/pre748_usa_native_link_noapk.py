#!/usr/bin/env python3
"""PRE748: genuine USA Android libmain.so link, Catch-Up disabled by default.

Uses authenticated original PRE99, replays V46/V49/V50/V51 native sources and
injects the reviewed PRE747 hook ONLY into app_usa in a disposable tree.
No APK, Gradle, signing key, user saves or game asset changes.
Do NOT put the generated game ELF or source in public Actions artifacts.
"""
import argparse,hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
import pre288_bmw_feature_on_pal_native_preflight as native
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre636_v49_c3_replay_noapk as v49
import pre635_c3_duplicate_request_trace_dryrun as pre635
import pre648_v50_shader_pass_counts_arm64_noapk as pre648
import pre652_build_signed_v51_gpu_shader_counts_diag as v51
from pre194_c3_guard_pal_diagnostic_patch import PATCHED_SHA as PIN_C3
import pre747_usa_arm64_object as usa

OUT=Path("/tmp/nfsmw-pre748/PRE748_USA_REAL_LIBMAIN_NOAPK.json")
PHASE="START"
EVIDENCE={}
TARGET="sub_823328C0"
CVAR=b"nfsmw_sem_catchup_carreira"
def sha(b):return hashlib.sha256(b).hexdigest()

def stage(root):
    global PHASE
    PHASE="REPLAY_V49_ON_AUTHENTICATED_V46"
    prior=v49.stage_v49_once(root)
    if prior.get("pre626_previous_PRE429_PRE447_nitro_preserved") is not True:
        raise ValueError("V49 original callback stage not verified")
    PHASE="STAGE_ORIGINAL_V50_AND_V51_PAL_DIAGNOSTICS"
    original=(root/pre648.SOURCE).read_bytes()
    if sha(original)!=PIN_C3:raise ValueError("V49 original C3 source SHA mismatch")
    v50=pre635.patch_p194(original)
    if sha(v50)!=v49.EXPECTED_PROPOSAL:
        raise ValueError("V50 original C3 diagnostic SHA mismatch")
    candidate=pre648.patch_bytes(v50)
    if sha(candidate)!=v51.SOURCE_SHA:
        raise ValueError("V51 original GPU draw diagnostic SHA mismatch")
    header=pre648.HEADER.read_bytes()
    if sha(header)!=v51.HEADER_SHA:
        raise ValueError("V51 original header checksum mismatch")
    (root/pre648.SOURCE).write_bytes(candidate)
    dst=root/pre648.DEST_HEADER
    if dst.exists():raise ValueError("Existing V51 header, double-stage refused")
    dst.write_bytes(header)
    EVIDENCE["v51_original_pal_renderer_sha"]=sha(candidate)
    PHASE="VERIFY_ORIGINAL_USA_CONTROLLER"
    guest=(root/usa.USAFUNC).read_bytes()
    marker=b"DEFINE_REX_FUNC(sub_823328C0) {"
    if guest.count(marker)!=1:raise ValueError("USA controller symbol not unique")
    i=guest.index(marker)+len(marker)
    j=guest.find(b"\nDEFINE_REX_FUNC(",i)
    if j<0 or sha(guest[i:j+1])!=usa.TARGET_SHA:
        raise ValueError("USA guest controller body not authenticated")
    if b"// cmpwi cr6,r11,2" not in guest[i:j+1]:
        raise ValueError("USA controller career branch absent")
    PHASE="STAGE_USA_HOOK_PRIVATE_NO_PAL_CHANGES"
    cmake=root/usa.USA_CMAKE if hasattr(usa,"USA_CMAKE") else root/"nativo/app_usa/CMakeLists.txt"
    # PRE747 template validates exact original file SHA and reviewed source blobs.
    base=cmake.read_bytes()
    if sha(base)!=usa.CMAKE_SHA:raise ValueError("USA CMake base SHA invalid")
    pal=root/"nativo/app/CMakeLists.txt"
    pal_sha=sha(pal.read_bytes())
    for name in usa.BLOBS:
        d=root/"nativo/app_usa/src"/name
        if d.exists():raise ValueError("Refuse duplicate USA feature")
        d.write_bytes(usa.fetch(name))
    cpp=(root/"nativo/app_usa/src/nfsmw_catchup_carreira.cpp").read_bytes()
    header=(root/"nativo/app_usa/src/nfsmw_catchup_carreira_policy.h").read_bytes()
    if (cpp.count(b"REX_HOOK_RAW(sub_823328C0)")!=1 or
        b"REX_HOOK_RAW(sub_82332898)" in cpp or
        b"REXCVAR_DEFINE_BOOL(nfsmw_sem_catchup_carreira, false" not in cpp or
        b"kRaceStatusGlobal = 0x82A2CB18u" not in header or
        b"kOffsetContexto = 6700u" not in header):
        raise ValueError("USA hook or race context not verified")
    old=base.decode()
    anchor="    src/nfsmw_recortes_carrera.cpp\n"
    insert="    src/nfsmw_catchup_carreira.cpp\n"
    if old.count(anchor)!=1 or insert in old:raise ValueError("Unsafe USA CMake patch")
    new=old.replace(anchor,anchor+insert,1)
    if new.replace(insert,"",1)!=old:raise ValueError("USA CMake insertion not reversible")
    cmake.write_text(new)
    if sha(pal.read_bytes())!=pal_sha or insert in pal.read_text():
        raise ValueError("PAL native tree accidentally modified")
    EVIDENCE.update({
      "usa_guest_original_body_sha256":usa.TARGET_SHA,
      "usa_cmake_original_sha256":sha(base),
      "usa_cmake_stage_sha256":sha(cmake.read_bytes()),
      "usa_hook_sha256":sha(cpp),
      "usa_source_code_staged_only_in_app_usa":True,
      "usa_cvar_off_by_default":True,
      "usa_cmake_reversible":True,
      "pal_cmake_preserved":True,
      "original_usa_generated_guest_unchanged":sha(guest)==sha((root/usa.USAFUNC).read_bytes()),
    })
    PHASE="STAGED_USA_NO_APK"
    return {"v51_previous_native_diagnostics_preserved":True,
            "usa_catchup_hook_default_off":True}

def run_native():
    global PHASE
    prior=(native.replay_v37,native.stage_logger,native.execute,
           native.find_outputs,native.PAL_FILENAME,native.FEATURE,native.CALLBACK,
           native.MAX_BUILD_SECONDS)
    old_execute=native.execute
    old_find=native.find_outputs

    def intercept(argv,*args,**kwargs):
        global PHASE
        values=[str(x) for x in argv]
        if "-DNFSMW_NATIVO_APP=app" in values:
            values[values.index("-DNFSMW_NATIVO_APP=app")]="-DNFSMW_NATIVO_APP=app_usa"
        result=old_execute(values,*args,**kwargs)
        if result["ok"] and "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON" in values:
            b=Path(values[values.index("-B")+1])
            commands=json.loads((b/"compile_commands.json").read_text())
            paths=[str(x.get("file","")) for x in commands]
            hook=[p for p in paths if p.endswith("/nativo/app_usa/src/nfsmw_catchup_carreira.cpp")]
            wrong=[p for p in paths if p.endswith("/nativo/app/src/nfsmw_catchup_carreira.cpp")]
            guest=[p for p in paths if p.endswith("/nativo/app_usa/generated/default/nfsmw_recomp.52.cpp")]
            if len(hook)!=1 or wrong or len(guest)!=1:
                raise ValueError("USA-only hook/USA guest compile graph mismatch")
            EVIDENCE["USA_HOOK_COMPILE_COUNT"]=1
            EVIDENCE["PAL_HOOK_COMPILE_COUNT"]=0
            EVIDENCE["USA_GUEST_SHARD_COMPILE_COUNT"]=1
            PHASE="USA_ONLY_CMAKE_GRAPH_VALIDATED"
        return result

    def inspect_link(build):
        global PHASE
        libs=old_find(build)
        if len(libs)!=1 or not native.arm64_elf(libs[0]):
            raise ValueError("One genuine ARM64 libmain.so expected")
        data=libs[0].read_bytes()
        if CVAR not in data:
            raise ValueError("Linked USA DSO missing Catch-Up cvar marker")
        EVIDENCE.update({
            "real_game_DSO_arm64_linked":True,
            "real_game_DSO_sha256":sha(data),
            "real_game_DSO_bytes":len(data),
            "cvar_marker_linked":True,
        })
        PHASE="LINKED_USA_LIBMAIN_AARCH64"
        return libs

    try:
        native.replay_v37=v46.replay_v46_sources
        native.stage_logger=stage
        native.execute=intercept
        native.find_outputs=inspect_link
        native.PAL_FILENAME="nfsmw_recomp.52.cpp"
        native.FEATURE="NFSMW_PRE748_USA_LINK_ONLY"
        native.CALLBACK=TARGET
        native.MAX_BUILD_SECONDS=4800
        PHASE="RUN_ORIGINAL_NDK_CMAKE_GUEST_BUILD"
        report=native.audit(Path(__file__).resolve().parents[2])
    finally:
        (native.replay_v37,native.stage_logger,native.execute,
         native.find_outputs,native.PAL_FILENAME,native.FEATURE,native.CALLBACK,
         native.MAX_BUILD_SECONDS)=prior
    verified=(
      report.get("cmake_configure",{}).get("ok") is True
      and report.get("production_native_build",{}).get("ok") is True
      and report.get("linked_library",{}).get("arm64_elf") is True
      and report.get("pal_feature_flag",{}).get("passed_to_pal_compiler") is True
      and EVIDENCE.get("real_game_DSO_arm64_linked") is True
      and EVIDENCE.get("USA_HOOK_COMPILE_COUNT")==1
      and EVIDENCE.get("PAL_HOOK_COMPILE_COUNT")==0)
    if not verified:
        raise ValueError("Full native USA link gate failed: "+
                         str(report.get("status"))+" - "+
                         str(report.get("production_native_build",{}).get("stderr_tail",""))[-750:])
    PHASE="REAL_USA_NATIVE_BUILD_LINK_APPROVED"
    return {
      "stage":"PRE748_ACTUAL_USA_CAREER_CATCHUP_ARM64_DSO_NOAPK",
      "status":"AUDIT_OK_REAL_USA_LIBMAIN_LINK",
      "source_archive_sha256":report.get("backup_sha256"),
      "arm64_cmake_ok":True,
      "native_build_real_link":True,
      "original_builder_native_status":report.get("status"),
      "evidence":EVIDENCE,
      "apk_built":False,"signer_accessed":False,
      "gameplay_on_device_tested":False,"catchup_effect_proven":False,
      "saves_modified":False,"shaders_or_physics_modified_by_feature":False,
    }

def main():
    global PHASE
    parser=argparse.ArgumentParser();parser.add_argument("--run-id",required=True)
    opts=parser.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:
        if not opts.run_id.isdecimal():raise ValueError("Invalid run ID")
        result=run_native()
    except Exception as exc:
        result={"stage":"PRE748_ACTUAL_USA_CAREER_CATCHUP_ARM64_DSO_NOAPK",
                "status":"FAILED","phase":PHASE,"error_type":type(exc).__name__,
                "error_summary":str(exc)[-1100:] if isinstance(exc,ValueError) else "Native build exception",
                "evidence":EVIDENCE,"apk_built":False,"signer_accessed":False}
    result["utc"]=datetime.now(timezone.utc).isoformat()
    result["run_id"]=opts.run_id
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE748_STATUS="+result["status"])
    print("PRE748_PHASE="+PHASE)
    print("PRE748_REAL_USA_LIBMAIN_ARM64="+str(EVIDENCE.get("real_game_DSO_arm64_linked",False)))
    print("PRE748_NO_APK_NO_SIGNING")
    if result["status"]=="FAILED":
        print("PRE748_ERROR_TYPE="+result.get("error_type","unknown"))
        print("PRE748_ERROR_HINT="+result.get("error_summary","")[-350:])
    return 0 if result["status"]=="AUDIT_OK_REAL_USA_LIBMAIN_LINK" else 1
if __name__=="__main__":
    sys.exit(main())
