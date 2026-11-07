#!/usr/bin/env python3
"""PRE298: isolated REAL PAL cold/warm native-cache benchmark, no APK or game cache persistence.
Replays authenticated PRE99 twice with identical patches/features in fresh temp trees,
with a shared ephemeral ccache and source/path safeguards. Does not save object cache.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, time
from pathlib import Path
from datetime import datetime, timezone
import pre288_bmw_feature_on_pal_native_preflight as native
from pre292_bmw_main_menu_native_link_nosign import stage_trace
from pre291_bmw_main_menu_passive_trace_dryrun import TRACE_FLAG, TRACE_CALLBACK
from pre264_bmw_hero_menu_patch_dryrun import SOURCE
from pre296_game_objects_cache_policy import check as cache_check

OUT=Path("/tmp/nfsmw-pre298/PRE298_REAL_PAL_COLD_WARM_NO_PERSISTENCE.json")
def verify(x,msg):
    if not x:raise ValueError(msg)
def compiler_stats(ccache,env):
    p=subprocess.run([ccache,"--show-stats"],capture_output=True,text=True,
                     check=False,timeout=30,env=env)
    verify(p.returncode==0,"ccache stats unavailable")
    vals={}
    for name in ["Cacheable calls","Hits","Misses"]:
        m=re.search(r"(?mi)^\\s*"+re.escape(name)+r"\\s*:?\\s+(\\d+)\\b",p.stdout)
        vals[name.lower().replace(" ","_")]=int(m.group(1)) if m else None
    return vals
def main():
    argp=argparse.ArgumentParser()
    argp.add_argument("--run-id",required=True)
    args=argp.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE298_REAL_GAME_ARM64_COLD_WARM_DISPOSABLE",
            "status":"FAILED","apk_built":False,"game_object_cache_persisted":False,
            "save_modified":False,"signer_accessed":False,
            "real_game_cache_approved_for_release":False}
    current="INITIAL"
    prior=(native.stage_logger,native.FEATURE,native.CALLBACK,
           native.PAL_FILENAME,native.execute)
    base_env=dict(os.environ)
    try:
        current="ENVIRONMENT"
        runner=Path(os.environ["RUNNER_TEMP"]).resolve()
        cache=runner/"nfsmw-game-objects"
        verify(not cache.exists(),"game cache must start cold and absent")
        cache.mkdir(mode=0o700)
        ccache=shutil.which("ccache")
        verify(ccache,"ccache missing")
        wrapper=Path(__file__).resolve().parent/"pre296_game_objects_cache_launcher.sh"
        verify(wrapper.is_file() and "NFSMW_CACHE_GAME_OPT_IN" in wrapper.read_text(),
               "bounded launcher missing")
        wrapper.chmod(0o755)
        os.environ.update({"CCACHE_DIR":str(cache),
                           "CCACHE_MAXSIZE":"2048M",
                           "CCACHE_COMPILERCHECK":"content",
                           "CCACHE_COMPRESS":"1",
                           "NFSMW_CACHE_GAME_OPT_IN":"1",
                           "NFSMW_GAME_CCACHE_BIN":str(Path(ccache).resolve()),
                           "NFSMW_GAME_CCACHE_DIR":str(cache)})
        subprocess.run([ccache,"--zero-stats"],check=True,
                       capture_output=True,env=os.environ,timeout=25)
        original_exec=native.execute
        def execute_with_launcher(argv,timeout=120,cwd=None,extra_env=None):
            cmd=list(argv)
            if "-S" in cmd and "-B" in cmd and "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON" in cmd:
                cmd+=["-DCMAKE_C_COMPILER_LAUNCHER="+str(wrapper),
                      "-DCMAKE_CXX_COMPILER_LAUNCHER="+str(wrapper)]
            return original_exec(cmd,timeout=timeout,cwd=cwd,extra_env=extra_env)
        def staging_with_root(root):
            os.environ["NFSMW_GAME_CACHE_SOURCE_ROOT"]=str(root)
            os.environ["CCACHE_BASEDIR"]=str(root)
            return stage_trace(root)
        native.stage_logger=staging_with_root
        native.execute=execute_with_launcher
        native.FEATURE=TRACE_FLAG
        native.CALLBACK=TRACE_CALLBACK
        native.PAL_FILENAME=Path(SOURCE).name
        entries=[]
        for iteration in (1,2):
            current="REAL_NATIVE_LINK_ITERATION_"+str(iteration)
            t=time.monotonic()
            out=native.audit(Path(__file__).resolve().parents[2])
            elapsed=time.monotonic()-t
            info=out.get("linked_library",{})
            flags=out.get("pal_feature_flag",{})
            verify(out.get("status")=="AUDIT_OK","real PAL link did not pass")
            verify(info.get("arm64_elf") and info.get("defined_callback_count")==1,
                   "unexpected linked callback/architecture")
            verify(flags.get("passed_to_pal_compiler"),"menu feature disabled")
            entries.append({"number":iteration,"elapsed_wall_seconds":round(elapsed,2),
                            "libmain_sha256":info.get("sha256"),
                            "linked_size":info.get("size"),
                            "native_target":out.get("selected_native_target"),
                            "compiler_cache":compiler_stats(ccache,os.environ)})
        current="COMPARE_AND_GUARD"
        cache_check(cache,seal=True)
        # All cached objects intentionally discarded at job end.
        report.update({"status":"AUDIT_OK",
            "iterations":entries,
            "real_pal_cmake_twice_successful":True,
            "libmain_hashes_identical":entries[0]["libmain_sha256"]==entries[1]["libmain_sha256"],
            "second_pass_cache_hits_total":entries[1]["compiler_cache"].get("hits"),
            "real_game_object_cache_used_only_in_ephemeral_runner":True,
            "game_object_cache_persisted":False,
            "game_runtime_tested":False,
            "release_gate_passed":False})
    except Exception as exc:
        report["error_type"]=type(exc).__name__
        report["failed_stage"]=current
    finally:
        native.stage_logger,native.FEATURE,native.CALLBACK,native.PAL_FILENAME,native.execute=prior
        os.environ.clear();os.environ.update(base_env)
    report["run_id"]=args.run_id
    report["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("PRE298_STATUS",report["status"])
    print("PRE298_REAL_NATIVE_TWICE",report.get("real_pal_cmake_twice_successful"))
    print("PRE298_HASH_EQUAL",report.get("libmain_hashes_identical"))
    print("PRE298_GAME_CACHE_PERSISTED",False)
    print("PRE298_FAILURE_STAGE",report.get("failed_stage"))
    print("PRE298_FAILURE_TYPE",report.get("error_type"))
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
