#!/usr/bin/env python3
"""PRE284: full V37 SOURCE patch-chain reproduction + PRE283 native logger preflight.

Performs no Gradle invocation, no APK build or signing. PRE99 is authenticated,
restored into a temporary directory, and the exact V37 patches are replayed.
PRE283 passive vtable-target logger is registered once in CMake and its
candidate-generated guest shard is SHA-pinned. A host C++ link mock tests the
native callback's C ABI and 12-event cap, with a clearly labeled shim
REXLOG_INFO macro; this is NOT Android/NDK compilation or a game execution.
Attempts a non-fatal syntax check using the real SDK logging header too.
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

from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download,SOURCE_SHA256
from pre107_restore_isolated import restore
from pre117_one_scroll_android_dryrun import propose
from pre128_android_touch_scroll_visual_patch import propose as propose_pre128
from pre131_native_touch_and_modern_ui_patch import proposal as propose_pre131
from pre133_mouse_bridge_swipe_patch import propose as propose_pre133
from pre118_audit_build_tree import EXPECTED_PRE117_SHA
from pre157_otimizar_refresh_callback import optimize as propose_pre157, PRE99_SHA as PRE157_BASE_SHA
from pre165_sdl_wake_sleep2 import patch_verified as propose_pre165, PRE99_SHA as PRE165_BASE_SHA
from pre170_input_pump_8ms_patch import patch_verified as propose_pre170, INPUT_SHA as PRE170_CPP_SHA, HEADER_SHA as PRE170_HEADER_SHA
from pre180_android_sdl_wait_block_patch import patch_verified as propose_pre180, SOURCE_SHA as PRE180_SDL_BASE_SHA
from pre194_c3_guard_pal_diagnostic_patch import patch_verified as propose_pre194, BASE_SHA as PRE194_PAL_BASE_SHA, PATCHED_SHA as PRE194_PAL_PATCHED_SHA
from pre246_passive_money_probe_patch import apply as apply_pre246
from pre247_pal_meter_passive_probe_patch import apply as apply_pre247
from pre246_build_signed_v37_passive_money_trace import (
    EXPECTED_PRE128_SHA,EXPECTED_PRE131_FILES,PRE180_SDL_PATCHED_SHA
)
from pre283_bmw_vtable_target_passive_dryrun import (
    SOURCE as PAL_SOURCE,PIN as PAL_PIN,FN as PAL_FUNC,
    ANCHOR as PAL_ANCHOR,INJECTION as PAL_INJECTION,
    DECL as PAL_DECL, FEATURE as PAL_FEATURE, CALLBACK,
    HOST_LOGGER_PREVIEW,patch as validate_pre283
)
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre284/PRE284_FULL_V37_SOURCE_PASSIVE_VTABLE_NATIVE_PREFLIGHT.json")
CMAKE_REL="nativo/app/CMakeLists.txt"
MODULE_REL="nativo/app/src/nfsmw_cheats_trace_pre284.cpp"
PRE247_TARGET="target_sources(nfsmw PRIVATE src/nfsmw_cheats_trace_pre247.cpp)"
PRE284_TARGET="target_sources(nfsmw PRIVATE src/nfsmw_cheats_trace_pre284.cpp)"
EXPECTED_PAL_CANDIDATE="1ce6208a0848955df6e918e7d56a28616afbf822e5a05b9747e4300e37bbaba9"
EXPECTED_PRE133_REPORT="automation/kaggle/status/pre133_touch_theme_arm64.json"

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def checked(path:Path,exp:str):
    digest=sha(path.read_bytes())
    if digest!=exp:raise ValueError("SHA mismatch "+path.name)
    return digest

def write_exact(path:Path,content:bytes,expected:str):
    if sha(content)!=expected:raise ValueError("Proposed patch digest unexpected at "+path.name)
    path.write_bytes(content)
    return checked(path,expected)

def replay_v37(root:Path,repo_root:Path):
    log={}
    # All comparisons mirror the successful PRE247/V37 build script,
    # without any signer, V30 APK, Android Gradle or credential fetch.
    src=root/"nativo/sdk/src/ui/overlay/settings_overlay.cpp"
    checked(src,SOURCE_SHA256)
    mod,_diff=propose(src.read_text(encoding="utf-8"))
    write_exact(src,mod.encode("utf-8"),EXPECTED_PRE117_SHA)
    log["PRE117_settings"]=EXPECTED_PRE117_SHA

    next_text=propose_pre128(mod)
    write_exact(src,next_text.encode("utf-8"),EXPECTED_PRE128_SHA)
    log["PRE128_settings"]=EXPECTED_PRE128_SHA

    drawer=root/"nativo/sdk/src/ui/imgui_drawer.cpp"
    header=root/"nativo/sdk/include/rex/ui/imgui_drawer.h"
    settings_h=root/"nativo/sdk/include/rex/ui/overlay/settings_overlay.h"
    font=root/"android/app/src/main/res/font/michroma.ttf"
    mods=propose_pre131(src.read_bytes(),drawer.read_bytes(),header.read_bytes(),
                        settings_h.read_bytes(),font.read_bytes())
    if set(mods)!=set(EXPECTED_PRE131_FILES):
        raise ValueError("PRE131 patch set changed")
    for relative,blob in mods.items():
        dst=root.parent/relative
        # PRE131 creates the modern-font header, missing in original PRE99.
        # The proposed contents must still match the pinned SHA256.
        dst.parent.mkdir(parents=True,exist_ok=True)
        write_exact(dst,blob,EXPECTED_PRE131_FILES[relative])
    log["PRE131_files"]=len(mods)

    report=json.loads((repo_root/EXPECTED_PRE133_REPORT).read_text(encoding="utf-8"))
    if report.get("run_id")!="41876482785" or report.get("status")!="PRE133_ANDROID_ARM64_SYNTAX_PASSED":
        raise ValueError("PRE133 original preflight record invalid")
    expect=report["pre133_source_sha256"]
    write_exact(src,propose_pre133(src.read_bytes()),expect)
    log["PRE133_settings"]=expect

    presenter=root/"nativo/sdk/src/ui/presenter.cpp"
    checked(presenter,PRE157_BASE_SHA)
    p=propose_pre157(presenter.read_bytes())
    write_exact(presenter,p,sha(p))
    log["PRE157_presenter"]=sha(p)

    sdl=root/"nativo/sdk/src/ui/windowed_app_context_sdl.cpp"
    checked(sdl,PRE165_BASE_SHA)
    p=propose_pre165(sdl.read_bytes())
    write_exact(sdl,p,sha(p))
    log["PRE165_SDL"]=sha(p)

    input_cpp=root/"nativo/sdk/src/input/sdl/sdl_input_driver.cpp"
    input_h=root/"nativo/sdk/include/rex/input/sdl/sdl_input_driver.h"
    checked(input_cpp,PRE170_CPP_SHA)
    checked(input_h,PRE170_HEADER_SHA)
    i,h=propose_pre170(input_cpp.read_bytes(),input_h.read_bytes())
    write_exact(input_cpp,i,sha(i))
    write_exact(input_h,h,sha(h))
    log["PRE170_input_cpp"]=sha(i)
    log["PRE170_input_header"]=sha(h)

    sdl3=root/"nativo/sdk/thirdparty/sdl3/src/events/SDL_events.c"
    checked(sdl3,PRE180_SDL_BASE_SHA)
    write_exact(sdl3,propose_pre180(sdl3.read_bytes()),PRE180_SDL_PATCHED_SHA)
    log["PRE180_sdl3"]=PRE180_SDL_PATCHED_SHA

    c3=root/"nativo/app/src/nfsmw_nativo_dibujos.cpp"
    checked(c3,PRE194_PAL_BASE_SHA)
    write_exact(c3,propose_pre194(c3.read_bytes()),PRE194_PAL_PATCHED_SHA)
    log["PRE194_C3"]=PRE194_PAL_PATCHED_SHA

    money=apply_pre246(root)
    meters=apply_pre247(root)
    if money.get("money_traces")!=8 or meters.get("combined_money_and_meter_probe_sites")!=16:
        raise ValueError("PRE246/247 diagnostic inventory changed")
    log["PRE246_money_sites"]=8
    log["PRE247_combined_sites"]=16
    return log

def stage_logger(root:Path):
    pal=root/PAL_SOURCE.removeprefix("workspace/")
    base=pal.read_bytes()
    if sha(base)!=PAL_PIN:raise ValueError("PRE283 PAL base changed after full V37 patches")
    reference=validate_pre283(base)
    if reference["candidate_sha256"]!=EXPECTED_PAL_CANDIDATE:
        raise ValueError("PRE283 candidate source changed")
    text=base.decode("utf-8")
    body=body_for_function(text,PAL_FUNC)
    if body.count(PAL_ANCHOR)!=1 or CALLBACK in text:
        raise ValueError("Preexisting or duplicate PRE283 site")
    revised=body.replace(PAL_ANCHOR,PAL_INJECTION+PAL_ANCHOR,1)
    text=text.replace(body,revised,1)
    m=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)",text)
    if m is None:raise ValueError("Function macro declaration missing")
    text=text[:m.start()]+PAL_DECL+text[m.start():]
    patched=text.encode("utf-8")
    if sha(patched)!=EXPECTED_PAL_CANDIDATE:raise ValueError("Nonlocal generated source change")
    pal.write_bytes(patched)
    checked(pal,EXPECTED_PAL_CANDIDATE)
    if text.replace(PAL_DECL,"",1).replace(revised,body,1)!=base.decode("utf-8"):
        raise ValueError("Cannot reverse source patch")
    module=root/MODULE_REL
    if module.exists():raise ValueError("PRE284 source already exists")
    module.write_text(HOST_LOGGER_PREVIEW,encoding="utf-8")
    cmake=root/CMAKE_REL
    original=cmake.read_text(encoding="utf-8")
    if original.count(PRE247_TARGET)!=1 or PRE284_TARGET in original:
        raise ValueError("Expected PRE247 CMake insertion exactly once")
    cmake.write_text(original.replace(PRE247_TARGET,
           PRE247_TARGET+"\n    "+PRE284_TARGET,1),encoding="utf-8")
    changed=cmake.read_text(encoding="utf-8")
    if changed.count(PRE284_TARGET)!=1 or not module.is_file():
        raise ValueError("Native CMake module registration failed")
    if changed.replace("\n    "+PRE284_TARGET,"",1)!=original:
        raise ValueError("CMake was changed beyond one additive target")
    if not HOST_LOGGER_PREVIEW.startswith("#include <atomic>"):
        raise ValueError("Native module source changed")
    return {
       "generated_pal_source":PAL_SOURCE,
       "original_sha256":PAL_PIN,
       "candidate_sha256":EXPECTED_PAL_CANDIDATE,
       "native_logger_module":MODULE_REL,
       "native_logger_sha256":sha(module.read_bytes()),
       "cmake_module_registered_once":True,
       "cmake_sha256":sha(cmake.read_bytes()),
       "feature_macro":PAL_FEATURE,
       "macro_defined_in_source":False,
       "source_exactly_reversible":True,
       "no_original_guest_memory_ops_or_calls_changed":True,
    }

def host_link_mock(root:Path):
    # Compile the *actual module source* unchanged using a minimal fake
    # rex/logging/macros.h that counts emissions instead of logging.
    # Strictly a native C ABI/symbol/saturation test, not SDK/NDK verification.
    with tempfile.TemporaryDirectory(prefix="pre284_host_") as d:
        tmp=Path(d)
        inc=tmp/"rex/logging"
        inc.mkdir(parents=True)
        (inc/"macros.h").write_text(
            "#pragma once\nvoid pre284_count_log() noexcept;\n"
            "#define REXLOG_INFO(...) pre284_count_log()\n",encoding="utf-8")
        harness=tmp/"harness.cpp"
        harness.write_text(r'''
#include <cassert>
#include <cstdint>
#include <iostream>
static unsigned g_logs=0;
void pre284_count_log() noexcept {++g_logs;}
extern "C" void NFSMW_PRE283_VTABLE_TARGET_TRACE(
    unsigned int target,unsigned int screen,unsigned int pc) noexcept;
int main() {
    for(unsigned i=0;i<200u;++i) {
        NFSMW_PRE283_VTABLE_TARGET_TRACE(0x82582A40u,0x10004000u,0x825837D4u);
    }
    assert(g_logs==12u);
    std::cout<<"PRE284_NATIVE_LINK_200_EVENTS_12_LOGS_PASS\n";
}
''',encoding="utf-8")
        compiler=shutil.which("c++")
        if compiler is None:raise ValueError("C++ compiler not found on runner")
        output=tmp/"mock"
        cmd=[compiler,"-std=c++20","-O1","-Wall","-Wextra","-Werror",
             "-pthread","-Wno-unused-parameter","-I",str(tmp),str(root/MODULE_REL),str(harness),
             "-o",str(output)]
        c=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
        if c.returncode!=0:raise ValueError("Native host logger shim compile/link failed: "+c.stderr[-400:])
        r=subprocess.run([str(output)],capture_output=True,text=True,timeout=20)
        if r.returncode!=0 or "12_LOGS_PASS" not in r.stdout:
            raise ValueError("Callback ABI/atomic limit mock failed")
        nm=subprocess.run(["nm","-g",str(output)],capture_output=True,text=True,timeout=20)
        if nm.returncode!=0 or len(re.findall(r"(?m)^[0-9a-fA-F]+ T NFSMW_PRE283_VTABLE_TARGET_TRACE$",nm.stdout))!=1:
            raise ValueError("Expected exactly one unmangled native logger symbol")
        return {"host_native_cpp_compiled":True,"host_native_cpp_linked":True,
                "abi_symbol_unmangled_verified":True,"test":r.stdout.strip(),
                "host_logging_header_is_stub":True,"real_sdk_or_android_library_compiled":False}

def real_sdk_header_syntax(root:Path):
    # Try compile with the actual logging header. Do not use its result to
    # claim a full Android link or a native ARM64 build.
    compiler=shutil.which("c++")
    include=root/"nativo/sdk/include"
    if compiler is None or not include.is_dir():
        return {"attempted":False,"passed":False,"reason":"No compiler or SDK include"}
    dirs=[
      include,
      root/"nativo/sdk/thirdparty/fmt/include",
      root/"nativo/sdk/thirdparty/spdlog/include",
      root/"nativo/sdk/thirdparty",
    ]
    cmd=[compiler,"-std=c++20","-fsyntax-only",
         "-Wno-unused-parameter"]+[arg for p in dirs if p.exists() for arg in ("-I",str(p))]
    cmd.append(str(root/MODULE_REL))
    res=subprocess.run(cmd,capture_output=True,text=True,timeout=65)
    return {"attempted":True,"passed":res.returncode==0,
            "compiler":"host C++ (not ARM64 NDK)",
            "diagnostic_if_failed":res.stderr[-700:] if res.returncode else None}

def audit(repo_root:Path):
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre284_") as d:
        tmp=Path(d)
        archive=tmp/"pre99.tar.gz"
        download(drive_client(),archive)
        dig,_,size=sha_file(archive)
        if dig!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("Authenticated PRE99 SHA/size mismatch")
        dst=tmp/"restore";dst.mkdir()
        restore(archive,dst)
        archive.unlink(missing_ok=True)
        root=dst/"workspace"
        v37=replay_v37(root,repo_root)
        vtable=stage_logger(root)
        host=host_link_mock(root)
        real=real_sdk_header_syntax(root)
        return {
         "stage":"PRE284_V37_FULL_PATCH_CHAIN_PRE283_NATIVE_LINK_PREFLIGHT",
         "status":"AUDIT_OK" if real["passed"] else "PARTIAL_SDK_HEADER_COMPILE_UNVERIFIED",
         "authenticated_pre99_sha256":dig,
         "v37_source_patch_chain":v37,
         "pre283":vtable,
         "native_host_abi_mock":host,
         "real_sdk_header_syntax":real,
         "release_approved":False,
         "compiler_used_for_full_game":False,
         "real_ndk_arm64_link_done":False,
         "vtable_target_measured_on_device":False,
         "bmw_menu_enabled":False,
         "bmw_performance_levels_measured":False,
         "limitations":[
           "Full V37 patch sequence replayed in a disposable workspace, but Android Gradle/Ninja native sources are NOT built",
           "Host ABI link test uses a substitute logging header, so it is not proof that the real SDK logger links",
           "Actual SDK header compile is host-only and not evidence of Android ARM64 linkage",
           "PRE283 feature OFF by default; real diagnostic build must explicitly enable and link it",
           "No private signing certificate, game save, V37 APK or persistent source touched"
         ],
         "apk_built":False,"signed":False,"save_touched":False,"signer_accessed":False,
         "source_persisted":False,
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    opt=p.parse_args()
    if not opt.run_id.isdecimal():raise ValueError("Run id must be decimal")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE284_V37_FULL_PATCH_CHAIN_PRE283_NATIVE_LINK_PREFLIGHT",
           "status":"FAILED","phase":"START","apk_built":False,"signer_accessed":False}
    try:report=audit(Path(__file__).resolve().parents[2])
    except Exception as err:
        report["error_type"]=type(err).__name__
        report["error_message"]=str(err)[:400]
    report["run_id"]=opt.run_id
    report["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE284_STATUS",report["status"])
    print("PRE284_V37_PATCH_KEYS",list(report.get("v37_source_patch_chain",{})))
    print("PRE284_CMAKE",report.get("pre283",{}).get("cmake_module_registered_once"))
    print("PRE284_HOST_ABI",report.get("native_host_abi_mock",{}).get("test"))
    print("PRE284_REAL_SDK_SYNTAX",report.get("real_sdk_header_syntax",{}).get("passed"))
    if report["status"]=="FAILED":print("PRE284_ERROR_TYPE",report.get("error_type"))
    return 0 if report["status"]!="FAILED" else 1

if __name__=="__main__":sys.exit(main())
