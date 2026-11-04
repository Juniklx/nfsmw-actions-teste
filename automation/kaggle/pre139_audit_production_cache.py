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
    need(c.get("uses")=="actions/cache@v4","cache action version changed")
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
    release_index=steps.index(build[0])
    guard_index=next(i for i,x in enumerate(steps) if "PRE139 verify dependency-only cache contents"==x.get("name"))
    need(guard_index>release_index,"guard must run after build and before cache action post")
    need("steps.release.outcome == 'success'"==steps[guard_index].get("if"),"safety audit execution condition altered")
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
        "stage":"PRE139_PRODUCTION_CACHE_POLICY_STATIC_AUDIT",
        "status":"PASS",
        "source_sha256":hashlib.sha256(source.encode()).hexdigest(),
        "workflow_sha256":hashlib.sha256(wftext.encode()).hexdigest(),
        "cache_policy_sha256":hashlib.sha256(policy.encode()).hexdigest(),
        "cached_paths":sorted(paths),
        "native_game_objects_cached":False,
        "keys_cached":False,
        "real_v31_rebuild_performed":False,
        "real_gradle_dependency_cache_hit_measured":False,
        "gh_actions_synthetic_cache_reuse_passed_in_runs":[41899119460,41899259138],
    }
    print(json.dumps(output,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
