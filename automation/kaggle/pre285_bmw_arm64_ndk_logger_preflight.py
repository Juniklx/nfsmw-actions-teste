#!/usr/bin/env python3
"""PRE285: actual Android NDK AArch64 C++ compile + isolated CMake archive smoke.

Authenticated PRE99 restored in temp; V37 patch sequence rebuilt via PRE284;
PRE283 source/register added in temp, feature flag enabled for *syntax only*.
A real Android NDK compiler and CMake compile the native logger (real SDK
headers) into AArch64 objects and a static linkable archive, not a game binary.
The guest generated source also receives an optional NDK -fsyntax-only
attempt. No full nfsmw DSO link, no Gradle, no APK, no signing, no saves.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from datetime import datetime, timezone

from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client, download
from pre107_restore_isolated import restore
from pre284_v37_full_passive_vtable_link_preflight import (
  replay_v37, stage_logger, MODULE_REL, PAL_SOURCE, PAL_FEATURE,
  EXPECTED_PAL_CANDIDATE, sha
)

OUT=Path("/tmp/nfsmw-pre285/PRE285_AARCH64_NDK_PASSIVE_VTABLE_COMPILE.json")
NDK_VERSION="28.2.13676358"
ANDROID_ABI="arm64-v8a"
ANDROID_API=26
MAX_TEST_SECONDS=240
CALLBACK="NFSMW_PRE283_VTABLE_TARGET_TRACE"

def find_ndk():
    roots=[]
    for key in ("ANDROID_HOME","ANDROID_SDK_ROOT"):
        value=os.getenv(key)
        if value:roots.append(Path(value))
    roots.append(Path("/usr/local/lib/android/sdk"))
    for sdk in roots:
        ndk=sdk/"ndk"/NDK_VERSION
        compiler=ndk/"toolchains/llvm/prebuilt/linux-x86_64/bin"/f"aarch64-linux-android{ANDROID_API}-clang++"
        if (ndk/"source.properties").is_file() and compiler.is_file():
            text=(ndk/"source.properties").read_text(encoding="utf-8")
            if "Pkg.Revision = "+NDK_VERSION not in text:
                raise ValueError("Unexpected NDK revision")
            return {"sdk":sdk,"ndk":ndk,"compiler":compiler}
    raise FileNotFoundError("Expected Android NDK r28.2 compiler not installed")

def run_checked(args,timeout=120,cwd=None):
    p=subprocess.run([str(v) for v in args],cwd=cwd,capture_output=True,text=True,timeout=timeout)
    return {"ok":p.returncode==0,"returncode":p.returncode,
            "stdout_tail":p.stdout[-600:],
            "stderr_head":p.stderr[:1600],"stderr_tail":p.stderr[-1000:]}

def arm64_elf(path:Path):
    if not path.is_file():return False
    data=path.read_bytes()[:24]
    return len(data)>=20 and data[:4]==b"\x7fELF" and data[4]==2 and data[5]==1 and data[18:20]==b"\xb7\x00"

def get_include_paths(root:Path):
    options=[
      root/"nativo/sdk/include",
      root/"nativo/sdk/thirdparty/fmt/include",
      root/"nativo/sdk/thirdparty/spdlog/include",
      root/"nativo/sdk/thirdparty",
      root/"nativo/sdk/thirdparty/simde",
      root/"nativo/app/include",
      root/"nativo/app/src",
      root/"nativo/app/generated/default",
      root/"nativo/sdk/src",
    ]
    # Resolve SIMDe as a vendored dependency by its actual header path:
    # the include must be the directory containing the 'simde/' folder.
    vendor=root/"nativo/sdk/thirdparty"
    if vendor.is_dir():
        for header in vendor.glob("**/simde/x86/sse.h"):
            parent=header.parents[2]
            if parent.is_dir() and parent not in options:
                options.append(parent)
    return [p for p in options if p.is_dir()]

def symbol_visible(obj:Path,ndk:Path):
    nm=ndk/"toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
    if not nm.is_file():nm=Path(shutil.which("nm") or "")
    if not nm.is_file():raise FileNotFoundError("No nm available")
    p=subprocess.run([str(nm),"-g",str(obj)],capture_output=True,text=True,timeout=30)
    if p.returncode!=0:return {"ok":False,"reason":"nm could not read ARM64 object"}
    lines=[x for x in p.stdout.splitlines() if CALLBACK in x]
    # GNU/LLVM nm: '0000... T NFSMW...' or 'T NFSMW...'
    good=[x for x in lines if re.search(r"\bT\s+"+CALLBACK+r"$",x)]
    return {"ok":len(good)==1,"unmangled_defined_symbol_count":len(good),
            "symbol":CALLBACK}

def compile_real_module(root:Path,tool:dict,tmp:Path):
    clang=tool["compiler"]
    mod=root/MODULE_REL
    obj=tmp/"nfsmw_cheats_trace_pre284.ARM64.o"
    inc=get_include_paths(root)
    cmd=[clang,"-std=c++20","-DANDROID=1","-fPIC","-O1",
         "-Wno-unused-parameter","-c",mod,"-o",obj]
    for p in inc:cmd+=["-I",p]
    info=run_checked(cmd,timeout=MAX_TEST_SECONDS)
    result={"compiled":info["ok"],"real_sdk_header":True,
            "architecture":"aarch64-linux-android"+str(ANDROID_API),
            "android_ndk_version":NDK_VERSION,
            "include_dirs_used":[p.relative_to(root).as_posix() for p in inc],
            "compiler_return_code":info["returncode"]}
    if not info["ok"]:
        result["diagnostic"]=info["stderr_tail"]
        return result
    if not arm64_elf(obj):raise ValueError("NDK compiler did not output AArch64 ELF64 relocatable")
    syms=symbol_visible(obj,tool["ndk"])
    if not syms["ok"]:raise ValueError("Missing unmangled native callback from NDK object")
    result.update({"arm64_elf_verified":True,"symbol":syms,
                  "object_size":obj.stat().st_size,"object_sha256":sha(obj.read_bytes())})
    return result

def cmake_archive(root:Path,tool:dict,tmp:Path):
    cmake_bin=shutil.which("cmake")
    ninja=shutil.which("ninja")
    if not cmake_bin or not ninja:raise FileNotFoundError("CMake/Ninja missing")
    proj=tmp/"link_smoke"
    proj.mkdir()
    mod=root/MODULE_REL
    includes=get_include_paths(root)
    lines=[
     "cmake_minimum_required(VERSION 3.22)",
     "project(NFSMW_PRE285_Android_Logger_Link_Smoke LANGUAGES CXX)",
     "add_library(nfsmw_pre285_logger STATIC \""+mod.as_posix()+"\")",
     "set_target_properties(nfsmw_pre285_logger PROPERTIES POSITION_INDEPENDENT_CODE ON CXX_STANDARD 20)",
     "target_compile_definitions(nfsmw_pre285_logger PRIVATE ANDROID=1)",
    ]
    if includes:
        lines.append("target_include_directories(nfsmw_pre285_logger PRIVATE "+
                     " ".join('"'+v.as_posix()+'"' for v in includes)+")")
    (proj/"CMakeLists.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
    build=tmp/"cmake_aarch64"
    toolchain=tool["ndk"]/"build/cmake/android.toolchain.cmake"
    if not toolchain.is_file():raise ValueError("NDK CMake toolchain missing")
    config=run_checked([
     cmake_bin,"-S",proj,"-B",build,"-G","Ninja",
     "-DCMAKE_TOOLCHAIN_FILE="+str(toolchain),
     "-DANDROID_ABI="+ANDROID_ABI,
     "-DANDROID_PLATFORM=android-"+str(ANDROID_API),
     "-DCMAKE_BUILD_TYPE=Release"
    ],timeout=180)
    if not config["ok"]:
        return {"configured":False,"built":False,"diagnostic":config["stderr_tail"][-750:]}
    build_result=run_checked([cmake_bin,"--build",build,"--parallel","2"],timeout=MAX_TEST_SECONDS)
    if not build_result["ok"]:
        return {"configured":True,"built":False,
                "diagnostic":build_result["stderr_tail"][-750:]}
    outputs=list(build.glob("libnfsmw_pre285_logger.a"))
    if len(outputs)!=1:raise ValueError("Unexpected CMake static archive output")
    arch=outputs[0]
    if arch.read_bytes()[:8]!=b"!<arch>\n":raise ValueError("Invalid native static archive magic")
    nm=tool["ndk"]/"toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
    if not nm.exists():raise FileNotFoundError("NDK llvm-nm unavailable")
    nm_result=subprocess.run([str(nm),"-g",str(arch)],capture_output=True,text=True,timeout=45)
    if nm_result.returncode!=0 or len(re.findall(r"\bT\s+"+CALLBACK+r"\b",nm_result.stdout))!=1:
        raise ValueError("AArch64 archive does not expose required native symbol exactly once")
    return {
      "configured":True,"built":True,"ndk_target":"nfsmw_pre285_logger",
      "isolation":"isolated static CMake archive, NOT actual game nfsmw shared library",
      "archive_sha256":sha(arch.read_bytes()),"archive_bytes":arch.stat().st_size,
      "callback_definition_count":1,"full_game_linked":False,
    }

def guest_macro_syntax_attempt(root:Path,tool:dict):
    src=root/PAL_SOURCE.removeprefix("workspace/")
    if sha(src.read_bytes())!=EXPECTED_PAL_CANDIDATE:
        raise ValueError("Guest source PRE283 SHA changed")
    # Generated PAL uses std::byteswap from <bit> (requires C++23);
    # the standalone logger module remains independently C++20-compatible.
    flags=[tool["compiler"],"-std=c++23","-DANDROID=1",
           "-D"+PAL_FEATURE+"=1","-fsyntax-only","-Wno-unused-parameter"]
    for inc in get_include_paths(root):flags+=["-I",inc]
    flags.append(src)
    result=run_checked(flags,timeout=MAX_TEST_SECONDS)
    return {
       "attempted":True,"passed":result["ok"],
       "guest_file":"nfsmw_recomp.11.cpp","feature_enabled_for_syntax_test":True,
       "feature_enabled_in_APK":False,
       "full_build_flags_or_precompiled_header_available":False,
       "diagnostic_if_failed":(result["stderr_head"]+"\n...\n"+result["stderr_tail"]) if not result["ok"] else None
    }

def audit(repo_root:Path):
    tools=find_ndk()
    with tempfile.TemporaryDirectory(prefix="pre285_") as d:
      tmp=Path(d)
      arch=tmp/"pre99.tar.gz"
      download(drive_client(),arch)
      digest,_,size=sha_file(arch)
      if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
         raise ValueError("PRE99 checksum/size mismatch")
      restore_to=tmp/"restore";restore_to.mkdir()
      restore(arch,restore_to)
      arch.unlink(missing_ok=True)
      root=restore_to/"workspace"
      replay=replay_v37(root,repo_root)
      pre283=stage_logger(root)
      module=compile_real_module(root,tools,tmp)
      if not module["compiled"]:
        return {"stage":"PRE285_BMW_ARM64_NDK_NATIVE_LINK_TEST","status":"NDK_MODULE_COMPILE_FAILED",
             "PRE99_authenticated_sha256":digest,"v37_source_chain":replay,
             "pre283":pre283,"android_ndk_module":module,"release_approved":False,
             "full_game_linked":False,"apk_built":False,"signer_accessed":False}
      cmake=cmake_archive(root,tools,tmp)
      guest=guest_macro_syntax_attempt(root,tools)
      status="AUDIT_OK" if cmake["built"] and guest["passed"] else (
          "PARTIAL_GUEST_SOURCE_SYNTAX_UNVERIFIED" if cmake["built"] else "CMAKE_ARCHIVE_FAILED"
      )
      return {
         "stage":"PRE285_BMW_ARM64_NDK_NATIVE_LINK_TEST",
         "status":status,"PRE99_authenticated_sha256":digest,
         "v37_source_chain":replay,"pre283":pre283,
         "android_ndk_module":module,
         "isolated_cmake_archive":cmake,
         "guest_pal_source_syntax":guest,
         "release_approved":False,
         "actual_game_libmain_linked":False,
         "pre283_active_in_apk":False,
         "bmw_menu_unlocked":False,
         "bmw_upgrade_levels_known":False,
         "limits":[
           "Real NDK AArch64 compile and isolated CMake archive only, not the production nfsmw target",
           "Guest PAL source syntax may fail without the original native CMake macros, PCH or include flags",
           "Actual game libmain.so link and Android Runtime remain unverified",
           "Signing, APK, save file and private signer material are not read or changed",
           "No current V38 APK; permanent certificate must remain unchanged if later approved"
         ],
         "apk_built":False,"signed":False,"signer_accessed":False,
         "user_save_modified":False,"source_persisted":False,
      }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("run id numeric")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE285_BMW_ARM64_NDK_NATIVE_LINK_TEST",
            "status":"FAILED","apk_built":False,"signed":False,
            "signer_accessed":False,"source_persisted":False}
    try:result=audit(Path(__file__).resolve().parents[2])
    except Exception as e:
        result["error_type"]=type(e).__name__
        result["error_message"]=str(e)[:350]
    result["run_id"]=a.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE285_STATUS",result["status"])
    print("PRE285_NDK_MODULE",result.get("android_ndk_module",{}).get("compiled"))
    print("PRE285_CMAKE_ARCHIVE",result.get("isolated_cmake_archive",{}).get("built"))
    print("PRE285_PAL_SYNTAX",result.get("guest_pal_source_syntax",{}).get("passed"))
    print("PRE285_GAME_LIBMAIN_LINKED",result.get("actual_game_libmain_linked"))
    if result["status"]=="FAILED":print("PRE285_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] not in ("FAILED","NDK_MODULE_COMPILE_FAILED","CMAKE_ARCHIVE_FAILED") else 1

if __name__=="__main__":
    sys.exit(main())
