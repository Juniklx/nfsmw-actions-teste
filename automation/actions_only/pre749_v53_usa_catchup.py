#!/usr/bin/env python3
"""PRE749 V53: USB/USA Catch-Up candidate in signed Android APK.

Follows PRE731/V52 + PRE652/V51 authenticated production chain.
Only original USA libmain_usa.so is intentionally replaced after V30 SHA
verification, with a verified SHA-pinned, real ARM64 native build. CVar
default OFF until gameplay negative-controls. Signing is ONLY the existing
permanent release certificate, verified by the original production builder.
Do not upload game APKs, binaries, signing material or source to public Actions.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path

import pre731_v52 as v52
import pre652_build_signed_v51_gpu_shader_counts_diag as release
import pre401_build_signed_v46_global_nitro_full as production
import pre434_build_signed_v47_bmw_passive_diag as v47
import pre747_usa_arm64_object as usa
import pre288_bmw_feature_on_pal_native_preflight as native

VERSION=53
APK_NAME="NFSMW_V53_PRE749_USA_CATCHUP_CARREIRA_EXPERIMENTAL_OFF.apk"
USA_LIB="lib/arm64-v8a/libmain_usa.so"
USA_BUNDLE="jniLibs/arm64-v8a/libmain_usa.so"
USA_CPP="nativo/app_usa/src/nfsmw_catchup_carreira.cpp"
USA_H="nativo/app_usa/src/nfsmw_catchup_carreira_policy.h"
USA_CMAKE="nativo/app_usa/CMakeLists.txt"
USA_GENERATED="nativo/app_usa/generated/default/nfsmw_recomp.52.cpp"
PAL_CMAKE="nativo/app/CMakeLists.txt"
DEFAULT_CVAR=b"REXCVAR_DEFINE_BOOL(nfsmw_sem_catchup_carreira, false"
EXPECTED_CERT="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
V30_SHA="4f32de8f2ff10d4748aa33f208774038ef9bfa402eacc61a49dd7e70f3b1bc83"
EVIDENCE={}

def sha(b):return hashlib.sha256(b).hexdigest()

def source_stage(root):
    previous=v52.stage(root)  # Original V51 source -> V52 touch, pinned patch.
    cmake=root/USA_CMAKE
    old=cmake.read_bytes()
    if sha(old)!=usa.CMAKE_SHA:
        raise ValueError("PRE749 USA original CMake not authenticated PRE745")
    pal_sha=sha((root/PAL_CMAKE).read_bytes())
    game=(root/USA_GENERATED).read_bytes()
    marker=b"DEFINE_REX_FUNC(sub_823328C0) {"
    if game.count(marker)!=1:raise ValueError("PRE749 USA guest target not unique")
    i=game.index(marker)+len(marker)
    j=game.find(b"\nDEFINE_REX_FUNC(",i)
    if j<0 or sha(game[i:j+1])!=usa.TARGET_SHA:
        raise ValueError("PRE749 USA codegen target SHA differs from PRE746")
    for name in usa.BLOBS:
        path=root/"nativo/app_usa/src"/name
        if path.exists():raise ValueError("PRE749 duplicate USA hook injection refused")
        path.write_bytes(usa.fetch(name))  # immutable PR8 commit + Git blob SHA
    hook=(root/USA_CPP).read_bytes()
    policy=(root/USA_H).read_bytes()
    if not (
        hook.count(b"REX_HOOK_RAW(sub_823328C0)")==1
        and hook.count(DEFAULT_CVAR)==1
        and b"REX_HOOK_RAW(sub_82332898)" not in hook
        and b"kOffsetContexto = 6700u" in policy
        and b"kRaceStatusGlobal = 0x82A2CB18u" in policy
    ):
        raise ValueError("PRE749 only accepts the OFF-by-default USA Career hook")
    anchor="    src/nfsmw_recortes_carrera.cpp\n"
    added="    src/nfsmw_catchup_carreira.cpp\n"
    cmake_text=old.decode("utf-8")
    if cmake_text.count(anchor)!=1 or added in cmake_text:
        raise ValueError("PRE749 USA CMake insertion ambiguous")
    staged=cmake_text.replace(anchor,anchor+added,1)
    if staged.replace(added,"",1)!=cmake_text:
        raise ValueError("PRE749 USA CMake insertion not exactly reversible")
    cmake.write_text(staged,encoding="utf-8")
    if sha((root/PAL_CMAKE).read_bytes())!=pal_sha:
        raise ValueError("PRE749 PAL game CMake unexpectedly changed")
    EVIDENCE.update({
        "original_USA_guest_sha256":usa.TARGET_SHA,
        "original_USA_CMake_sha256":usa.CMAKE_SHA,
        "usa_CMake_reversible":True,
        "usa_only_hook_source_sha256":sha(hook),
        "usa_only_hook_header_sha256":sha(policy),
        "usa_CVar_default_off":True,
        "pal_CMake_unchanged":True,
        "usa_generated_guest_unchanged":sha((root/USA_GENERATED).read_bytes())==sha(game),
        "v52_touch_patch_preserved":True
    })
    return {**previous,"pre749_usa_catchup_off_by_default":True}

def build_usa_native(root):
    info=native.find_ndk()
    cmake,_provider=native.find_cmake(info)
    toolchain=info["ndk"]/"build/cmake/android.toolchain.cmake"
    if not toolchain.is_file():raise ValueError("PRE749 pinned NDK toolchain missing")
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre749-usa-link-") as td:
        build=Path(td)/"build"
        cmd=[cmake,"-S",root/"android/app/src/main/cpp","-B",build,"-G","Ninja",
             "-DCMAKE_TOOLCHAIN_FILE="+str(toolchain),
             "-DANDROID_ABI=arm64-v8a","-DANDROID_PLATFORM=android-26",
             "-DANDROID_STL=c++_shared","-DNFSMW_MOTOR=nativo",
             "-DNFSMW_NATIVO_APP=app_usa",
             "-DNFSMW_REPO="+str(root),"-DNFSMW_NATIVO="+str(root/"nativo"),
             "-DCMAKE_BUILD_TYPE=Release","-DCMAKE_CXX_STANDARD=23",
             "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
             "-DCMAKE_CXX_FLAGS=-DNFSMW_PRE748_USA_LINK_ONLY=1"]
        configured=native.execute(cmd,timeout=250)
        if not configured["ok"]:
            raise ValueError("PRE749 native USA CMake configure failed: "+
                             configured.get("stderr_tail","")[-700:])
        cc=json.loads((build/"compile_commands.json").read_text())
        paths=[str(x.get("file","")) for x in cc]
        count=sum(s.endswith("/nativo/app_usa/src/nfsmw_catchup_carreira.cpp") for s in paths)
        pal=sum(s.endswith("/nativo/app/src/nfsmw_catchup_carreira.cpp") for s in paths)
        codegen=sum(s.endswith("/nativo/app_usa/generated/default/nfsmw_recomp.52.cpp") for s in paths)
        if (count,pal,codegen)!=(1,0,1):
            raise ValueError("PRE749 USA-only native compile graph mismatch")
        build_status=native.execute([cmake,"--build",build,"--target","nfsmw","--parallel","2"],
                                    timeout=4800)
        if not build_status["ok"]:
            raise ValueError("PRE749 real USA native link failed: "+
                             build_status.get("stderr_tail","")[-900:])
        libs=native.find_outputs(build)
        if len(libs)!=1 or not native.arm64_elf(libs[0]):
            raise ValueError("PRE749 actual ARM64 USA libmain.so missing/duplicated")
        data=libs[0].read_bytes()
        if b"nfsmw_sem_catchup_carreira" not in data or len(data)<1000000:
            raise ValueError("PRE749 linked USA game DSO missing feature cvar")
    EVIDENCE.update({
        "real_usa_arm64_DSO_built":True,
        "usa_guest_codegen_compiled":True,
        "usa_hook_in_native_compile_commands":1,
        "pal_hook_in_native_compile_commands":0,
        "usa_DSO_sha256":sha(data),
        "usa_DSO_bytes":len(data)
    })
    return data

def prepare_usa(root,bundle,v30):
    # Called AFTER authenticated V30 restore and AFTER source_stage.
    # Keep original integrity validation of every V30 asset intact.
    if sha(v30[USA_LIB])!=V30_SHA:
        raise ValueError("PRE749 original V30 USA bytes changed before staging")
    details=ORIGINAL_PREPARE(root,bundle,v30)
    original=(bundle/USA_BUNDLE).read_bytes()
    if sha(original)!=V30_SHA:
        raise ValueError("PRE749 V30 USA baseline not staged correctly")
    newer=build_usa_native(root)
    path=bundle/USA_BUNDLE
    path.write_bytes(newer)
    readback=sha(path.read_bytes())
    if readback!=EVIDENCE["usa_DSO_sha256"] or readback==V30_SHA:
        raise ValueError("PRE749 USA DLL replacement readback/equivalence failed")
    # V30 content and signer already validated by original builder.
    # The only intentionally changed Preserve entry is USA game code.
    if production.PRESERVE.get(USA_LIB)!=V30_SHA:
        raise ValueError("PRE749 original preservation policy unexpectedly changed")
    production.PRESERVE[USA_LIB]=readback
    EVIDENCE["original_V30_USA_library_verified_before_override"]=True
    EVIDENCE["usa_bundle_replaced_only_after_V30_authentication"]=True
    EVIDENCE["all_other_V30_preservation_hashes_untouched"]=True
    return {**details,"usa_library_preserved":False,"usa_library_compiled_from_original_PRE99":True,
            "usa_DSO_sha256":readback}

def original_apk_verify(apk,sdk,v30,progress):
    value=ORIGINAL_APK_VERIFY(apk,sdk,v30,progress)
    if not isinstance(value,dict):raise ValueError("PRE749 original APK verifier not a dict")
    if production.PRESERVE.get(USA_LIB)!=EVIDENCE.get("usa_DSO_sha256"):
        raise ValueError("PRE749 missing exact installed USA library SHA gate")
    value["usa_main_library_unchanged_from_v30"]=False
    value["usa_main_library_recompiled_from_PRE99"]=True
    value["usa_main_library_sha256"]=EVIDENCE["usa_DSO_sha256"]
    progress["pre749_expected_changed_usa_library_verified"]=True
    return value

def verify_v53(apk,sdk,v30,progress):
    prior=v52.verify(apk,sdk,v30,progress)
    with zipfile.ZipFile(apk) as z:
        if z.testzip() is not None:raise ValueError("PRE749 signed APK ZIP CRC failed")
        usalib=z.read(USA_LIB)
        if sha(usalib)!=EVIDENCE.get("usa_DSO_sha256") or sha(usalib)==V30_SHA:
            raise ValueError("PRE749 signed APK contains wrong USA game library")
        if not usalib.startswith(b"\x7fELF") or b"nfsmw_sem_catchup_carreira" not in usalib:
            raise ValueError("PRE749 signed APK lacks USA Catch-Up ELF marker")
        if b"NFSMW_PRE635_C3_TWOREQUEST_TRACE" not in z.read("lib/arm64-v8a/libmain.so"):
            raise ValueError("PRE749 PAL diagnostic not preserved")
    if progress.get("apk_v2_certificate_sha256")!=EXPECTED_CERT:
        raise ValueError("PRE749 certificate mismatch")
    progress["pre749_usa_catchup_signed_apk"]={
       "usa_arm64_sha256":sha(usalib),
       "replaced_original_V30_usa_DSO":True,
       "usa_only_hook_included":True,
       "feature_default_off":True,
       "gameplay_tested":False,"catchup_removal_proven":False,
       "usa_shaders_modified":False,"save_modified":False,
       "permanent_certificate_sha256":EXPECTED_CERT
    }
    return prior

ORIGINAL_PREPARE=production.prepare_usa_edition
ORIGINAL_APK_VERIFY=production.verify_apk
ORIGINAL_V47_VERIFY=v47.ORIGINAL_VERIFY

def main():
    opts=argparse.ArgumentParser(add_help=False)
    opts.add_argument("--report",required=True)
    o,_=opts.parse_known_args()
    if ORIGINAL_V47_VERIFY is not ORIGINAL_APK_VERIFY:
        raise ValueError("PRE749 V47 verifier capture changed; abort")
    if production.PRESERVE.get(USA_LIB)!=V30_SHA:
        raise ValueError("PRE749 old USA hash policy changed")
    saved=(release.VERSION,release.APK_NAME,release.stage_v51,
           release.verify_v51,production.prepare_usa_edition,
           production.verify_apk,v47.ORIGINAL_VERIFY)
    try:
        release.VERSION=VERSION
        release.APK_NAME=APK_NAME
        release.stage_v51=source_stage
        release.verify_v51=verify_v53
        production.prepare_usa_edition=prepare_usa
        production.verify_apk=original_apk_verify
        v47.ORIGINAL_VERIFY=original_apk_verify
        rc=release.main()
    finally:
        (release.VERSION,release.APK_NAME,release.stage_v51,
         release.verify_v51,production.prepare_usa_edition,
         production.verify_apk,v47.ORIGINAL_VERIFY)=saved
        production.PRESERVE[USA_LIB]=V30_SHA
    report=Path(o.report)
    if not report.is_file():raise ValueError("PRE749 signed APK report absent")
    j=json.loads(report.read_text())
    ok=(rc==0
        and j.get("signed_apk_verified") is True
        and j.get("permanent_certificate_verified") is True
        and j.get("apk_v2_certificate_sha256")==EXPECTED_CERT
        and j.get("pre652_target_version_code")==VERSION
        and j.get("v52_touch_dex_verified") is True
        and j.get("drive_upload_success") is True
        and j.get("pre749_usa_catchup_signed_apk",{}).get("usa_only_hook_included") is True
        and j.get("pre749_expected_changed_usa_library_verified") is True)
    j["pre749_stage"]="V53_USA_CATCHUP_EXPERIMENTAL_DEFAULT_OFF"
    j["pre749_verified"]=ok
    j["pre749_evidence"]=EVIDENCE
    j["pre749_not_runtime_tested"]=True
    j["pre749_rollout_authorized"]=False
    report.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n")
    print("PRE749_SIGNED_V53_USA_CATCHUP_GATE="+("PASS" if ok else "BLOCKED"))
    print("PRE749_NO_NEW_SIGNER_AND_NO_GAME_ASSET_CHANGE")
    if not ok:return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
