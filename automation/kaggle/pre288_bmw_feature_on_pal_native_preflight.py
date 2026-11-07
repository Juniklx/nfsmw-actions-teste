#!/usr/bin/env python3
"""PRE288: feature-ON PAL native CMake configure and link (no APK).

Authenticated PRE99 -> disposable restore -> full V37 source replay ->
PRE283 native callback registered in PAL nativo/app CMake, feature default OFF.
Attempts to configure the ORIGINAL Android app native CMake root using the
pinned NDK; only builds a verified native target that outputs libmain.so.
No Gradle/assembleRelease, key or game save access, no APK. OAuth/signing
secrets removed from child processes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime,timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client, download
from pre107_restore_isolated import restore
from pre284_v37_full_passive_vtable_link_preflight import replay_v37,stage_logger,sha
from pre285_bmw_arm64_ndk_logger_preflight import find_ndk, arm64_elf

OUT=Path("/tmp/nfsmw-pre288/PRE288_BMW_REAL_LIBMAIN_PAL_CMAKE_LINK.json")
EXPECTED_ROOT="android/app/src/main/cpp/CMakeLists.txt"
LINK_TARGETS=("main","nfsmw","libmain.so")
CALLBACK="NFSMW_PRE283_VTABLE_TARGET_TRACE"
FEATURE="NFSMW_PRE283_VTABLE_TARGET_TRACE_ENABLE"
PAL_FILENAME="nfsmw_recomp.11.cpp"
MAX_CMAKE_FILE=300_000
MAX_BUILD_SECONDS=1380
OUTPUT_LIMIT=2600
ALLOW_TERMS=("add_library","add_subdirectory","target_link_libraries","target_sources","include(",
             "set(","set_property","project(","file(","nfsmw","main","CMAKE_SOURCE_DIR",
             "CMAKE_CURRENT","CMAKE_TOOLCHAIN","CMAKE_CXX_STANDARD","CMAKE_CXX_FLAGS")
CMAKE_FILES=[
 "android/app/src/main/cpp/CMakeLists.txt",
 "android/app/src/main/cpp/nativo/nativo.cmake",
 "nativo/app/CMakeLists.txt",
 "nativo/app/generated/default/sources.cmake",
 "nativo/sdk/CMakeLists.txt",
 "nativo/app_usa/CMakeLists.txt",
]
EXCLUDED_WORDS=("password","secret","keystore","credential","private_key","signing","token")

def short_tail(value:str,n=OUTPUT_LIMIT):
    # Do not place potentially private environment values or credentials in reports.
    for envname in ("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_SECRET","GOOGLE_CLIENT_ID"):
        secret=os.getenv(envname) or ""
        if secret: value=value.replace(secret,"[REDACTED]")
    return value[-n:]

def clean_env():
    env=dict(os.environ)
    for k in list(env):
        u=k.upper()
        if any(x in u for x in ("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_SECRET",
                                  "GOOGLE_CLIENT_ID","KEYSTORE","STORE_PASSWORD",
                                  "KEY_PASSWORD","NFSMW_SIGNING","GRADLE_")):
            env.pop(k,None)
    return env

def execute(argv,timeout=120,cwd=None,extra_env=None):
    env=clean_env()
    if extra_env:env.update(extra_env)
    try:
        p=subprocess.run([str(v) for v in argv],cwd=cwd,env=env,
            capture_output=True,text=True,errors="replace",timeout=timeout)
        return {"completed":True,"code":p.returncode,
                "ok":p.returncode==0,
                "stdout_tail":short_tail(p.stdout),
                "stderr_tail":short_tail(p.stderr)}
    except subprocess.TimeoutExpired:
        return {"completed":False,"code":None,"ok":False,"timed_out_seconds":timeout}

def static_cmake_inventory(root):
    result={}
    for path in CMAKE_FILES:
        p=root/path
        if not p.is_file():
            result[path]={"present":False}
            continue
        raw=p.read_bytes()
        if len(raw)>MAX_CMAKE_FILE:raise ValueError("Unexpected CMake file size")
        lines=raw.decode("utf-8","replace").splitlines()
        matched=[{"line":i+1,"text":x.strip()[:210]}
                 for i,x in enumerate(lines) if any(term.lower() in x.lower()
                    for term in ALLOW_TERMS) and not any(t in x.lower() for t in EXCLUDED_WORDS)]
        result[path]={"present":True,"sha256":sha(raw),"bytes":len(raw),
                       "selected_lines":matched[:70],
                       "has_add_library":any("add_library(" in x.lower() for x in lines),
                       "has_target_sources_nfsmw":any("target_sources(nfsmw" in x.lower() for x in lines)}
    return result

def validate_clang_toolchain(ndk:Path):
    tool=ndk/"build/cmake/android.toolchain.cmake"
    if not tool.exists():raise ValueError("Missing pinned NDK toolchain")
    return tool

def find_cmake(ndk_info):
    # Pin the same installed CMake used in Gradle V37 if present.
    cm=ndk_info["sdk"]/"cmake/3.31.6/bin/cmake"
    if cm.is_file():return cm, "SDK_CMAKE_3_31_6"
    other=shutil.which("cmake")
    if other:return Path(other), "SYSTEM_CMAKE"
    raise FileNotFoundError("No CMake executable")

def get_targets(build:Path,cmake:Path):
    r=execute([cmake,"--build",build,"--target","help"],timeout=90)
    if not r["ok"]:return {"checked":True,"ok":False,"diagnostic":r}
    # Output is usually short enough for target names to survive tail clipping,
    # but authoritative build.ninja is on disk and can be read without truncation.
    ninja=build/"build.ninja"
    if not ninja.exists():return {"checked":True,"ok":False,"reason":"CMake did not produce Ninja build graph"}
    text=ninja.read_text(encoding="utf-8",errors="replace")
    names=sorted(set(re.findall(r"(?m)^build ([^\n:]+):",text)))
    relevant=[s for s in names if any(t in s for t in ("libmain.so","libnfsmw","nfsmw","main.so"))]
    return {"checked":True,"ok":True,"build_ninja_sha256":sha(ninja.read_bytes()),
            "native_targets_matching_game":relevant[:75],
            "target_help_tail":r["stdout_tail"][-1100:]}

def choose_target(result,cmake_files):
    names=result.get("native_targets_matching_game",[])
    # Require a real .so output; never treat the PRE285 isolated static archive
    # or a custom substitute target as successful linking of the game.
    for name in names:
        if "libmain.so" in name and not name.endswith(".o") and ".so/" not in name:
            # The native engine uses target nfsmw with OUTPUT_NAME main,
            # not the separate xenos engine's target main.
            if "nfsmw" in names:
                return "nfsmw","libmain.so"
            if "main" in names:
                return "main","libmain.so"
            return None,None
    return None,None

def find_outputs(build:Path):
    paths=[]
    for target in build.rglob("libmain.so"):
        if target.is_file():
            paths.append(target)
    return paths[:7]

def audit(repo:Path):
    info=find_ndk()
    toolchain=validate_clang_toolchain(info["ndk"])
    cmake,cmake_provider=find_cmake(info)
    ninja=shutil.which("ninja")
    if ninja is None:raise FileNotFoundError("Ninja unavailable")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre288_") as dirname:
        temp=Path(dirname)
        archive=temp/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,size=sha_file(archive)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("Authenticated PRE99 SHA256/size mismatch")
        extracted=temp/"restore"
        extracted.mkdir()
        restore(archive,extracted)
        archive.unlink(missing_ok=True)
        root=extracted/"workspace"
        patches=replay_v37(root,repo)
        staged=stage_logger(root)
        cmake_inventory=static_cmake_inventory(root)
        report={
          "stage":"PRE288_BMW_FEATURE_ON_PAL_NATIVE_LINK_NO_APK",
          "status":"NOT_YET_CONFIGURED",
          "feature_enabled_for_temporary_native_build":True,
          "backup_sha256":digest,
          "v37_source_patch_count":len(patches),
          "v37_source_patch_checks":patches,
          "pre283_native_module":staged,
          "cmake_provider":cmake_provider,
          "ndk_revision":"28.2.13676358",
          "cmake_source_inventory":cmake_inventory,
          "apk_built":False,"signed":False,"signing_material_accessed":False,
          "saves_accessed":False,"release_approved":False,
          "bumper":[
            "No Gradle APK task, package or signing executed",
            "PRE283 is ON only in this disposable compile; BMW tuning menu remains unchanged",
            "A real game library must be found as libmain.so and contain the callback"
          ]
        }
        original=root/EXPECTED_ROOT
        if not original.is_file():
            report["status"]="BLOCKED_SOURCE_CMAKE_ENTRY_NOT_FOUND"
            return report
        build=temp/"cmake_link"
        config=execute([
            cmake,"-S",original.parent,"-B",build,"-G","Ninja",
            "-DCMAKE_TOOLCHAIN_FILE="+str(toolchain),
            "-DANDROID_ABI=arm64-v8a",
            "-DANDROID_PLATFORM=android-26",
            "-DANDROID_STL=c++_shared",
            "-DNFSMW_MOTOR=nativo",
            "-DNFSMW_NATIVO_APP=app",
            "-DNFSMW_REPO="+str(root),
            "-DNFSMW_NATIVO="+str(root/"nativo"),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_CXX_FLAGS=-D"+FEATURE+"=1",
            "-DCMAKE_CXX_STANDARD=23",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            "-DCMAKE_MAKE_PROGRAM="+str(ninja),
        ],timeout=240)
        report["cmake_configure"]={"ok":config["ok"],"completed":config["completed"],
                                    "diagnostic":config}
        if not config["ok"]:
            report["status"]="BLOCKED_PRODUCTION_CMAKE_CONFIGURE"
            return report
        # Verify the ON flag is present specifically in the actual generated PAL shard
        # compile invocation; a configured CMake flag alone is insufficient.
        commands_path=build/"compile_commands.json"
        if not commands_path.is_file():
            report["status"]="BLOCKED_MISSING_COMPILE_COMMANDS"
            return report
        commands=json.loads(commands_path.read_text(encoding="utf-8"))
        pal_commands=[entry for entry in commands
                      if Path(entry.get("file","")).name==PAL_FILENAME]
        if len(pal_commands)!=1:
            report["status"]="BLOCKED_PAL_SHARD_COMPILE_COMMAND_NOT_UNIQUE"
            report["pal_compile_command_count"]=len(pal_commands)
            return report
        args=pal_commands[0].get("arguments")
        if args is None:
            command=pal_commands[0].get("command","")
            # Exact command-line token match, not prefix match or comment.
            import shlex
            args=shlex.split(command)
        expected="-D"+FEATURE+"=1"
        enabled=expected in args
        report["pal_feature_flag"]={
            "feature":FEATURE,"expected_define":expected,
            "pal_source":PAL_FILENAME,"command_found_once":True,
            "passed_to_pal_compiler":enabled,
            "compile_commands_sha256":sha(commands_path.read_bytes())
        }
        if not enabled:
            report["status"]="BLOCKED_PAL_FEATURE_NOT_ENABLED"
            return report
        targets=get_targets(build,cmake)
        report["target_graph"]=targets
        if not targets["ok"]:
            report["status"]="BLOCKED_TARGET_DISCOVERY"
            return report
        selected,expected=choose_target(targets,cmake_inventory)
        report["selected_native_target"]=selected
        if selected is None:
            report["status"]="BLOCKED_NO_REAL_LIBMAIN_TARGET"
            return report
        built=execute([cmake,"--build",build,"--target",selected,"--parallel","2"],
                      timeout=MAX_BUILD_SECONDS)
        report["production_native_build"]={"ok":built["ok"],
                "completed":built["completed"],"return_code":built["code"],
                "stdout_tail":built.get("stdout_tail"),"stderr_tail":built.get("stderr_tail"),
                "timed_out_seconds":built.get("timed_out_seconds")}
        if not built["ok"]:
            report["status"]="BLOCKED_PRODUCTION_NATIVE_LINK"
            return report
        libraries=find_outputs(build)
        if len(libraries)!=1:raise ValueError("Expected one production PAL libmain.so output")
        library=libraries[0]
        if not arm64_elf(library):raise ValueError("Output is not ARM64 ELF")
        nm=info["ndk"]/"toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
        check=execute([nm,"-D","--defined-only",library],timeout=100)
        if not check["ok"]:
            report["status"]="BLOCKED_DSO_SYMBOL_READ"
            return report
        # Use a complete fresh symbol table for exact matching (not tail).
        s=subprocess.run([str(nm),"-D","--defined-only",str(library)],
           capture_output=True,text=True,timeout=100,env=clean_env())
        refs=re.findall(r"(?m)^\S+\s+T\s+"+CALLBACK+r"$",s.stdout)
        report["linked_library"]={
            "filename":"libmain.so","relative_path":str(library.relative_to(build)),
            "sha256":sha(library.read_bytes()),"size":library.stat().st_size,
            "arm64_elf":True,"defined_callback_count":len(refs),
            "native_target_name":selected
        }
        report["status"]="AUDIT_OK" if len(refs)==1 and report["pal_feature_flag"]["passed_to_pal_compiler"] else "LINKED_BUT_MISSING_CALLBACK"
        report["game_dso_linked"]=True
        return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    arg=ap.parse_args()
    if not arg.run_id.isdecimal():raise ValueError("Numeric run required")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE288_BMW_ACTUAL_PAL_NATIVE_LIBMAIN_LINK_NO_APK",
      "status":"FAILED","apk_built":False,"signed":False,
      "saves_accessed":False,"signing_material_accessed":False}
    try:result=audit(Path(__file__).resolve().parents[2])
    except Exception as e:
        result["status"]="FAILED"
        result["error_type"]=type(e).__name__
        result["error_message"]=short_tail(str(e),450)
    result["github_run_id"]=arg.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE288_STATUS",result["status"])
    print("PRE288_CONFIG",result.get("cmake_configure",{}).get("ok"))
    print("PRE288_TARGET",result.get("selected_native_target"))
    print("PRE288_LIBMAIN_LINKED",result.get("game_dso_linked",False))
    print("PRE288_CALLBACK_DEFINITIONS",result.get("linked_library",{}).get("defined_callback_count"))
    print("PRE288_APK_BUILT",False)
    return 0 if result["status"]!="FAILED" else 1

if __name__=="__main__":sys.exit(main())
