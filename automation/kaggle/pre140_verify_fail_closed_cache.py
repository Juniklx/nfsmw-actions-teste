#!/usr/bin/env python3
"""PRE140 isolated security audit for split restore/audit/save cache workflow.

Only reads public repository text, no game data, signing or APK builds.
"""
from __future__ import annotations
import ast,hashlib,json
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/nfsmw-pre138-signed-v31-log-diagnostic.yml"
RELEASE=ROOT/"automation/kaggle/pre138_build_signed_v31_log_pal_usa.py"
POLICY=ROOT/"automation/kaggle/pre139_verify_dependency_cache.py"
EXPECTED_PATHS={
    "${{ runner.temp }}/nfsmw-gradle-home/caches/modules-2",
    "${{ runner.temp }}/nfsmw-gradle-home/wrapper",
}
EXPECTED_KEY="nfsmw-pre99-gradle-ef570ba95703-jdk21-v1-${{ runner.os }}"

def need(ok,message):
    if not ok: raise AssertionError("PRE140 safety audit: "+message)

def main():
    source=RELEASE.read_text(encoding="utf-8")
    policy=POLICY.read_text(encoding="utf-8")
    workflow=WF.read_text(encoding="utf-8")
    ast.parse(source)
    ast.parse(policy)
    steps=yaml.safe_load(workflow)["jobs"]["release"]["steps"]
    def one(test,label):
        found=[(i,s) for i,s in enumerate(steps) if test(s)]
        need(len(found)==1,label+" expected exactly once")
        return found[0]
    restore_i,restore=one(lambda s:s.get("id")=="gradle_deps_cache","cache restore")
    build_i,build=one(lambda s:s.get("id")=="release","release step")
    guard_i,guard=one(lambda s:s.get("id")=="deps_policy","cache guard")
    save_i,save=one(lambda s:s.get("uses")=="actions/cache/save@v4" and
        "nfsmw-gradle-home" in str(s.get("with",{}).get("path","")),"Gradle cache save")
    precheck_i,precheck=one(lambda s:s.get("name")=="PRE140 verify restored Gradle cache before build","restored cache precheck")
    need(restore.get("uses")=="actions/cache/restore@v4","restore must never auto-save")
    need(all(s.get("uses")!="actions/cache@v4" for s in steps),"generic cache with uncontrolled post-save forbidden")
    need(restore_i<precheck_i<build_i<guard_i<save_i,"cache must be checked before build and before saving")
    need(precheck.get("if")=="steps.gradle_deps_cache.outputs.cache-hit == 'true'","restored cache precheck condition")
    need("pre139_verify_dependency_cache.py" in precheck.get("run",""),"restore cache not scanned")
    need(guard.get("if")=="steps.release.outcome == 'success'","guard only after validated build")
    need("pre139_verify_dependency_cache.py" in guard.get("run",""),"save cache not scanned")
    need(build.get("continue-on-error") is True,"expected build step failure accounting changed")
    need(build.get("env",{}).get("NFSMW_GRADLE_USER_HOME")=="${{ runner.temp }}/nfsmw-gradle-home","unexpected Gradle cache home")
    def paths(c):
        return {p.strip() for p in c.get("with",{}).get("path","").splitlines() if p.strip()}
    need(paths(restore)==EXPECTED_PATHS and paths(save)==EXPECTED_PATHS,"allowlisted cache content differs")
    need(restore["with"]["key"]==EXPECTED_KEY,"pinned cache key changed")
    need(save["with"]["key"]=="${{ steps.gradle_deps_cache.outputs.cache-primary-key }}","save key not matched to restore primary key")
    condition=save.get("if","")
    for required in ("success()","steps.release.outcome == 'success'",
                     "steps.deps_policy.outcome == 'success'",
                     "steps.gradle_deps_cache.outputs.cache-hit != 'true'"):
        need(required in condition,"save conditional guard missing "+required)
    need('MISSING=()' in workflow and 'rm -rf "$p"' not in workflow,
         "SDK setup must be conditional and non-destructive")
    need("VERSION_CODE=31" in source and '"-Pnfsmw.registro=true"' in source,
         "V31 release target changed")
    need("certificate_sha256(key,secret_props)!=CERT_SHA" in source,
         "permanent certificate verification missing")
    need("propose_pre133(src.read_bytes())" in source,
         "functional Android touch patch missing")
    # PRE140: a second cache may persist ONLY the selected SDK compiler results,
    # never translated game objects; it has its own scan-before-build and seal gates.
    sdk_restore_i,sdk_restore=one(lambda x:x.get("id")=="sdk_ccache","SDK ccache restore")
    sdk_check_i,sdk_check=one(lambda x:x.get("name")==
        "PRE140 inspect restored SDK compiler cache before build","SDK cache precheck")
    sdk_policy_i,sdk_policy=one(lambda x:x.get("id")=="sdk_ccache_policy","SDK cache policy")
    sdk_save_i,sdk_save=one(lambda x:x.get("uses")=="actions/cache/save@v4" and
        "nfsmw-ccache-sdk-only" in str(x.get("with",{}).get("path","")),"SDK cache save")
    need(sdk_restore_i<sdk_check_i<build_i<sdk_policy_i<sdk_save_i,
         "SDK-only cache restore/precheck/build/audit/save order invalid")
    need(sdk_restore.get("uses")=="actions/cache/restore@v4",
         "SDK cache restore must not auto-save")
    sdk_path="${{ runner.temp }}/nfsmw-ccache-sdk-only"
    need(paths(sdk_restore)=={sdk_path} and paths(sdk_save)=={sdk_path},
         "SDK cache path scope drifted")
    need(sdk_restore.get("with",{}).get("key")==
         "nfsmw-pre99-sdkonly-ndk28-clang-ccache4-v1-${{ runner.os }}",
         "SDK cache version key changed")
    need(sdk_save.get("with",{}).get("key")==
         "${{ steps.sdk_ccache.outputs.cache-primary-key }}",
         "SDK save key mismatch")
    need(sdk_check.get("if")=="steps.sdk_ccache.outputs.cache-hit == 'true'",
         "SDK cache hit must trigger early scan")
    need("pre140_guard_sdk_only_ccache.py" in sdk_check.get("run","") and
         "--mode check" in sdk_check.get("run",""),"SDK restored cache unverified")
    need(sdk_policy.get("if")=="steps.release.outcome == 'success'",
         "SDK cache sealing must follow successful signed build")
    need("pre140_guard_sdk_only_ccache.py" in sdk_policy.get("run","") and
         "--mode seal" in sdk_policy.get("run",""),"SDK cache seal missing")
    for required in ("success()","steps.release.outcome == 'success'",
                     "steps.sdk_ccache_policy.outcome == 'success'",
                     "steps.sdk_ccache.outputs.cache-hit != 'true'"):
        need(required in sdk_save.get("if",""),"SDK cache save guard missing "+required)
    need(build.get("env",{}).get("NFSMW_PRE140_CCACHE_LAUNCHER")==
         "${{ github.workspace }}/automation/kaggle/pre140_sdk_only_ccache_launcher.sh",
         "SDK-only executable launcher missing")
    need("PRE140_CCACHE_LAUNCHER" in source and
         "c4949a0adbb788c82b621c7c39fa29baba02b4ae" in source and
         '"NFSMW_SDK_SOURCE_ROOT":str(root/"nativo/sdk")' in source,
         "release script did not pin the SDK-only compiler launcher")

    report={"stage":"PRE140_CACHE_FAIL_CLOSED_POLICY_AUDIT","status":"PASS",
        "workflow_sha256":hashlib.sha256(workflow.encode()).hexdigest(),
        "source_sha256":hashlib.sha256(source.encode()).hexdigest(),
        "restore_only":True,"scan_restored_cache":True,
        "post_build_explicit_scan":True,"save_requires_passed_build_and_guard":True,
        "cache_contents":sorted(EXPECTED_PATHS),
        "game_binary_cached":False,"signing_material_cached":False,
        "apk_built":False,"fps_tested":False}
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
