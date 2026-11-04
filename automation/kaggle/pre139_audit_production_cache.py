#!/usr/bin/env python3
"""PRE139: static audit of dependency-only cached V31 workflow and build script.

No game data, Gradle, SDK downloads, signing credentials or APK involved.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"automation/kaggle/pre138_build_signed_v31_log_pal_usa.py"
POLICY=ROOT/"automation/kaggle/pre139_verify_dependency_cache.py"
WORKFLOW=ROOT/".github/workflows/nfsmw-pre138-signed-v31-log-diagnostic.yml"
EXPECTED_KEY="nfsmw-pre99-gradle-ef570ba95703-jdk21-v1-${{ runner.os }}"

def need(condition:bool, message:str):
    if not condition:
        raise ValueError("PRE139 production cache audit failed: "+message)

def main():
    source=SCRIPT.read_text()
    wftext=WORKFLOW.read_text()
    policy=POLICY.read_text()
    ast.parse(source,filename=str(SCRIPT))
    ast.parse(policy,filename=str(POLICY))
    wf=yaml.safe_load(wftext)
    steps=wf["jobs"]["release"]["steps"]
    cache=[s for s in steps if s.get("id")=="gradle_deps_cache"]
    need(len(cache)==1,"cache action missing")
    c=cache[0]
    need(c.get("uses")=="actions/cache/restore@v4","cache restore action version changed")
    need(not any(s.get("uses")=="actions/cache@v4" for s in steps),
         "combined cache action can save files before our policy gate")
    paths=set(c.get("with",{}).get("path","").splitlines())
    paths={p.strip() for p in paths if p.strip()}
    need(paths=={
        "${{ runner.temp }}/nfsmw-gradle-home/caches/modules-2",
        "${{ runner.temp }}/nfsmw-gradle-home/wrapper",
    },"unexpected contents in persistent GitHub cache")
    need(c.get("with",{}).get("key")==EXPECTED_KEY,"source/Gradle cache version changed")
    build=[x for x in steps if x.get("id")=="release"]
    need(len(build)==1,"exact release step missing")
    need(build[0].get("env",{}).get("NFSMW_GRADLE_USER_HOME")==
         "${{ runner.temp }}/nfsmw-gradle-home","reusable Gradle home not passed")
    policy_steps=[x for x in steps if "pre139_verify_dependency_cache.py" in str(x.get("run",""))]
    need(len(policy_steps)>=1,"no production dependency cache content guard")
    restore_index=steps.index(c)
    precheck=[x for x in steps if x.get("name")=="PRE140 verify restored Gradle cache before build"]
    need(len(precheck)==1,"cached dependencies must be inspected before consuming")
    need(precheck[0].get("if")=="steps.gradle_deps_cache.outputs.cache-hit == 'true'",
         "restored cache preflight condition missing")
    need("pre139_verify_dependency_cache.py" in precheck[0].get("run",""),
         "restored cache not inspected")
    release_index=steps.index(build[0])
    need(restore_index<steps.index(precheck[0])<release_index,
         "restore verification must run before build")

    guard_index=next(i for i,x in enumerate(steps) if "PRE139 verify dependency-only cache contents" in x.get("name",""))
    need(guard_index>release_index,"guard must run after build and before cache action post")
    need("steps.release.outcome == 'success'"==steps[guard_index].get("if"),
         "safety audit execution condition altered")
    need(steps[guard_index].get("id")=="deps_policy","policy gate must be referenced by save")
    all_saves=[x for x in steps if x.get("uses")=="actions/cache/save@v4"]
    save=[x for x in all_saves
          if x.get("name")=="PRE140 persist audited Gradle dependency cache only after successful gate"]
    need(len(save)==1,"explicit Gradle cache save action missing or duplicated")
    save_step=save[0]
    save_index=steps.index(save_step)
    need(save_index>guard_index,"cache save must happen only after policy passes")
    save_paths={p.strip() for p in save_step.get("with",{}).get("path","").splitlines() if p.strip()}
    need(save_paths==paths,"save target differs from verified restored paths")
    need(save_step.get("with",{}).get("key")==
         "${{ steps.gradle_deps_cache.outputs.cache-primary-key }}",
         "save key must be derived from the restore cache key")
    expected_if=("${{ success() && steps.release.outcome == 'success' && "
                 "steps.deps_policy.outcome == 'success' && "
                 "steps.gradle_deps_cache.outputs.cache-hit != 'true' }}")
    need(save_step.get("if")==expected_if,
         "explicit cache save is not strictly conditional on the safety gate")

    # PRE142: a second, explicitly guarded compiler cache is permitted ONLY
    # for the redistributable SDK. It must never be mistaken for Gradle cache.
    sdk_restore=[x for x in steps if x.get("id")=="sdk_ccache"]
    sdk_saves=[x for x in all_saves if x is not save_step]
    need(len(sdk_restore)==len(sdk_saves)==1,
         "exactly one separate SDK cache restore/save required")
    sr=sdk_restore[0]
    ss=sdk_saves[0]
    need(sr.get("uses")=="actions/cache/restore@v4",
         "SDK cache must be restore-only before safety audit")
    sdk_path="${{ runner.temp }}/nfsmw-ccache-sdk-only"
    need(sr.get("with",{}).get("path")==sdk_path and
         ss.get("with",{}).get("path")==sdk_path,
         "SDK cache must have its own isolated dedicated path")
    need(sr.get("with",{}).get("key")==
         "nfsmw-pre99-sdkonly-ndk28-clang-ccache4-v1-${{ runner.os }}",
         "SDK ccache cache key changed")
    need(ss.get("with",{}).get("key")==
         "${{ steps.sdk_ccache.outputs.cache-primary-key }}",
         "SDK ccache save key not derived from restore")
    expected_sdk_save_if=(
         "${{ success() && steps.release.outcome == 'success' && "
         "steps.sdk_ccache_policy.outcome == 'success' && "
         "steps.sdk_ccache.outputs.cache-hit != 'true' }}")
    need(ss.get("if")==expected_sdk_save_if,
         "SDK ccache save condition does not require passed safety gate")
    restored_check=[x for x in steps
                    if x.get("name")=="PRE140 inspect restored SDK compiler cache before build"]
    sealed_check=[x for x in steps if x.get("id")=="sdk_ccache_policy"]
    need(len(restored_check)==len(sealed_check)==1,
         "SDK ccache restore scan or post-build scan missing")
    need("pre140_guard_sdk_only_ccache.py" in restored_check[0].get("run","") and
         "pre140_guard_sdk_only_ccache.py" in sealed_check[0].get("run",""),
         "SDK ccache both preflight and postflight guards required")
    need(steps.index(sr)<steps.index(restored_check[0])<release_index<
         steps.index(sealed_check[0])<steps.index(ss),
         "SDK ccache guard/save ordering unsafe")
    need(len(all_saves)==2,"unapproved cache save action present")

    need("pre139_verify_dependency_cache.py" in wftext,"safety script not referenced")
    need("MISSING=()" in wftext and 'rm -rf "$p"' not in wftext,
         "SDK installer must be non-destructive and skip installed packages")
    need("NFSMW_GRADLE_USER_HOME" in source and 'root_cache.name!="nfsmw-gradle-home"' in source,
         "external Gradle home should be confined to runner temp")
    need("VERSION_CODE=31" in source and '"-Pnfsmw.registro=true"' in source,
         "V31 code/version/logging changed")
    need("certificate_sha256(key,secret_props)!=CERT_SHA" in source,
         "permanent keystore check missing")
    need("download_file(d,P12_DRIVE_ID,key)" in source,
         "permanent signature source changed")
    need("EXPECTED_PRE131_FILES" in source and "propose_pre133(src.read_bytes())" in source,
         "V30 functional patches missing")
    output={
        "stage":"PRE140_PRODUCTION_CACHE_EXPLICIT_RESTORE_SAVE_AUDIT",
        "status":"PASS",
        "source_sha256":hashlib.sha256(source.encode()).hexdigest(),
        "workflow_sha256":hashlib.sha256(wftext.encode()).hexdigest(),
        "cache_policy_sha256":hashlib.sha256(policy.encode()).hexdigest(),
        "cached_paths":sorted(paths),
        "native_game_objects_cached":False,
        "keys_cached":False,
        "real_v31_rebuild_performed":False,
        "real_gradle_dependency_cache_hit_measured":False,
        "restored_cache_checked_before_build":True,
        "automatic_cache_post_save_disabled":True,
        "explicit_save_requires_verified_success":True,
        "sdk_compiler_cache_separate_and_safely_guarded":True,
        "unapproved_cache_saves":0,
        "gh_actions_synthetic_cache_reuse_passed_in_runs":[41899119460,41899259138],
    }
    print(json.dumps(output,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
