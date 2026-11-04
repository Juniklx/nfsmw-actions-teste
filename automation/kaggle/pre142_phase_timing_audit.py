#!/usr/bin/env python3
"""PRE142: standalone static/synthetic audit of sanitized build phase timing.

No key, APK, game asset, Drive download or Gradle invocation is required.
"""
from __future__ import annotations
import ast
import json
import re
import textwrap
from pathlib import Path

SRC=Path(__file__).with_name("pre138_build_signed_v31_log_pal_usa.py")
EXPECTED=[
 "VERIFY_ORIGINAL_PERMANENT_SIGNING",
 "DOWNLOAD_V30_BASELINE",
 "DOWNLOAD_PRE99_SNAPSHOT",
 "RESTORE_VERIFIED_PRE99",
 "APPLY_EXACT_PRE117_EPHEMERAL_ONLY",
 "APPLY_EXACT_PRE128_EPHEMERAL_ONLY",
 "APPLY_EXACT_PRE131_EPHEMERAL_ONLY",
 "APPLY_EXACT_PRE133_SDL_MOUSE_BRIDGE_EPHEMERAL_ONLY",
 "STAGE_VERIFIED_USA_FROM_V30",
 "ANDROID_SDK_CONFIGURATION",
 "GRADLE_ASSEMBLE_RELEASE_ARM64",
 "SELECT_APK_AND_VERIFY",
 "UPLOAD_NEW_APK_TO_PRIVATE_DRIVE",
 "COMPLETE",
]
def check(cond,why):
    if not cond:
        raise RuntimeError("PRE142 audit failed: "+why)

def main():
    source=SRC.read_text(encoding="utf-8")
    tree=ast.parse(source,str(SRC))
    compile(tree,str(SRC),"exec")
    entry=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="main"]
    check(len(entry)==1,"main missing")
    main_fn=entry[0]
    calls=[x for x in ast.walk(main_fn)
           if isinstance(x,ast.Call) and isinstance(x.func,ast.Name)
           and x.func.id=="pre142_advance_stage"]
    stages=[]
    for call in sorted(calls,key=lambda x:x.lineno):
        check(len(call.args)==1 and isinstance(call.args[0],ast.Constant)
              and isinstance(call.args[0].value,str),"dynamic/unknown stage name")
        stages.append(call.args[0].value)
    check(stages==EXPECTED,"phase markers/order changed")
    setters=re.findall(r'report\["phase"\]\s*=\s*',source)
    check(len(setters)==1,"direct phase assignments bypass monotonic timer")
    check('report["phase"]=next_stage' in source,"phase assignment not centralized")
    check('report["pre142_timing"]={' in source,"private report missing telemetry")
    check('"clock":"time.perf_counter"' in source,"clock marker changed")
    check('"gradle_phase_contains_cmake_ninja_and_packaging":True' in source,
          "Gradle/CMake aggregation disclaimer missing")
    check('"native_compile_exclusive_seconds_measured":False' in source,
          "exclusive native compile disclaimer missing")
    check('"timing_proves_cache_speedup":False' in source,
          "no-cache-speedup disclaimer missing")
    check('certificate_sha256(key,secret_props)!=CERT_SHA' in source,
          "permanent signing gate changed")
    check('VERSION_CODE=31' in source,"V31 version unchanged")
    nested=[x for x in main_fn.body if isinstance(x,ast.FunctionDef)
            and x.name=="pre142_advance_stage"]
    check(len(nested)==1,"embedded timing function absent")
    # Execute the actual nested function body with a deterministic fake monotonic clock,
    # no imports or user data from the build script.
    function_code=ast.unparse(nested[0])
    test_code="""def run_test():
    report={"phase":"INITIAL"}
    pre142_stage_started=0.0
    pre142_stage_name="INITIAL"
    pre142_stage_samples=[]
    class FakeTime:
        values=iter([1.25,4.0])
        def perf_counter(self):
            return next(self.values)
    time=FakeTime()
"""+textwrap.indent(function_code,"    ")+"""
    pre142_advance_stage("DOWNLOAD_PRE99_SNAPSHOT")
    pre142_advance_stage("GRADLE_ASSEMBLE_RELEASE_ARM64")
    return report,pre142_stage_name,pre142_stage_samples
"""
    scope={}
    exec(compile(test_code,"<pre142-mock>", "exec"),scope,scope)
    test_report,last,samples=scope["run_test"]()
    check(test_report["phase"]==last=="GRADLE_ASSEMBLE_RELEASE_ARM64",
          "monotonic stage update not applied")
    check(len(samples)==2 and samples[0]["elapsed_seconds"]==1.25 and
          samples[1]["elapsed_seconds"]==2.75,
          "synthetic elapsed times inaccurate")
    result={
        "stage":"PRE142_PHASE_TIMER_STATIC_AND_SYNTHETIC",
        "status":"PASS",
        "build_script_syntax_ok":True,
        "phase_count":len(stages),
        "simulated_stage_durations_seconds":[x["elapsed_seconds"] for x in samples],
        "stores_only_fixed_phase_labels_and_elapsed_seconds":True,
        "production_rebuild_performed":False,
        "actual_gradle_cache_savings_measured":False,
        "permanent_signing_gate_preserved":True,
    }
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
