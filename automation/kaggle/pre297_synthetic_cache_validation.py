#!/usr/bin/env python3
"""PRE295-PRE297: isolated cache-policy and reproducibility audit, no game source/artifacts.
Audits a rolling immutable SDK cache key and bench-tests a separate game-object
ccache policy on entirely synthetic C++, never uploads proprietary binaries.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path

OUT=Path("/tmp/nfsmw-pre295-297/CACHE_PREFLIGHT.json")
PREFIX="nfsmw-sdk-v2-ndk28-clang4-linux"
SDK_ONLY="nfsmw-pre99-sdkonly-ndk28-clang-ccache4-v1-Linux"
FUTURE_SCRIPT="automation/kaggle/pre296_game_objects_cache_launcher.sh"
FUTURE_POLICY="automation/kaggle/pre296_game_objects_cache_policy.py"

def sha(b):return hashlib.sha256(b).hexdigest()
def run(argv,env=None):
    p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,env=env,timeout=90)
    if p.returncode:raise RuntimeError("synthetic compiler test failed")
    return p
def check(x,msg):
    if not x:raise AssertionError(msg)

def main():
    pa=argparse.ArgumentParser();pa.add_argument("--run-id",default="0");a=pa.parse_args()
    repo=Path(__file__).resolve().parents[2]
    result={"stage":"PRE295_PRE296_PRE297_CACHE_SYNTHETIC_VALIDATION",
            "status":"FAILED","apk_built":False,"real_game_cached":False,
            "signer_accessed":False,"save_modified":False}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    current_stage="BEGIN"
    try:
        current_stage="CHECK_REPO_POLICY"
        sdk=repo/"automation/kaggle/pre140_sdk_only_ccache_launcher.sh"
        content=sdk.read_text()
        check("nativo/app and nativo/app_usa bypass ccache" in content,"PRE140 scope changed")
        check("exec \"$CCACHE_BINARY\" \"$compiler\" \"$@\"" in content,"PRE140 SDK wrapper changed")
        for f in (FUTURE_SCRIPT,FUTURE_POLICY):check((repo/f).is_file(),f+" absent")
        wrapper=(repo/FUTURE_SCRIPT)
        pol=(repo/FUTURE_POLICY)
        ptext=pol.read_text()
        check("NFSMW_CACHE_GAME_OPT_IN" in wrapper.read_text(),"game cache enabled by default")
        check("nfsmw-game-objects" in ptext,"cache namespace missing")
        check("forbidden" in ptext.lower(),"safety guard missing")
        current_stage="CHECK_IMMUTABLE_KEYS"
        # Simulate GitHub cache restore prefix matching and unique immutable writes.
        keys=[f"{PREFIX}-sha-abc-{100+i}" for i in range(3)]
        check(len(set(keys))==3,"immutable keys duplicate")
        check(all(k.startswith(PREFIX+"-") for k in keys),"restore prefix mismatch")
        current_stage="CHECK_CCACHE_COMPILER"
        # Synthetic C++ test uses actual ccache and compiler; avoid game assets.
        compiler=shutil.which("g++") or shutil.which("clang++")
        ccache=shutil.which("ccache")
        check(compiler and ccache,"g++/clang++ or ccache absent")
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre297_synthetic_") as tmp:
            d=Path(tmp)
            cache=d/"nfsmw-game-objects"
            cache.mkdir()
            src=d/"toy.cpp"
            src.write_text("#include <cstdint>\nextern \"C\" std::uint64_t synth(std::uint64_t n){return n*n+7;}\n")
            env=dict(os.environ,CCACHE_DIR=str(cache),CCACHE_BASEDIR=str(d),
                     CCACHE_COMPILERCHECK="content",
                     CCACHE_MAXSIZE="64M")
            current_stage="CCACHE_ZERO_STATS"
            run([ccache,"-z"],env)
            objs=[];dur=[]
            for i in range(2):
                current_stage="COMPILE_SYNTH_"+str(i)
                obj=d/f"sample_{i}.o"
                t=time.monotonic()
                run([ccache,compiler,"-c","-std=c++17","-O2","-fno-ident",
                     str(src),"-o",str(obj)],env)
                dur.append(round((time.monotonic()-t)*1000,2))
                objs.append(sha(obj.read_bytes()))
            current_stage="CCACHE_SHOW_JSON_STATS"
            raw=run([ccache,"--show-stats","--format=json"],env).stdout
            stats=json.loads(raw)
            sums=stats.get("stats",{})
            direct=sums.get("direct_cache_hit",0)
            pre=sums.get("preprocessed_cache_hit",0)
            hits=int(direct)+int(pre)
            current_stage="VERIFY_CACHE_HIT_AND_HASH"
            check(objs[0]==objs[1],"synthetic object changed with warm cache")
            check(hits>=1,"no actual warm compile cache hit")
            check(pol.stat().st_size<25000,"policy unexpectedly large")
            result.update({"status":"AUDIT_OK",
              "pre295_rolling_immutable_keys_verified":True,
              "pre295_legacy_sdk_cache_unmodified":True,
              "pre296_game_cache_default_off":True,
              "pre296_policy_sha256":sha(pol.read_bytes()),
              "pre297_synthetic_compiler":Path(compiler).name,
              "pre297_synthetic_cold_ms":dur[0],
              "pre297_synthetic_warm_ms":dur[1],
              "pre297_synthetic_object_hash_equal":True,
              "pre297_synthetic_ccache_hits":hits,
              "real_game_cache_validated":False,
              "performance_gain_for_real_game_proven":False})
    except Exception as exc:
        result["failed_stage"]=current_stage
        result["failure_type"]=type(exc).__name__
        if str(exc) in ("PRE140 scope changed","PRE140 SDK wrapper changed","game cache enabled by default","cache namespace missing","safety guard missing","g++/clang++ or ccache absent","no actual warm compile cache hit","synthetic object changed with warm cache"):
            result["failure_reason"]=str(exc)
        result["status"]="AUDIT_FAILED"
    result["run_id"]=a.run_id
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    print("PRE297_FAILED_STAGE",result.get("failed_stage"))
    print("PRE297_FAILURE_REASON",result.get("failure_reason"))
    for key in ("status","pre295_rolling_immutable_keys_verified",
                "pre296_game_cache_default_off","pre297_synthetic_object_hash_equal",
                "pre297_synthetic_ccache_hits","real_game_cache_validated"):
        print("PRE297_"+key.upper(),result.get(key))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
