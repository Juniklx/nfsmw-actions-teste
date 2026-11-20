#!/usr/bin/env python3
"""PRE752 V54: PAL-specific, gated Catch-Up candidate based on signed V52.

Only original authenticated PRE99 PAL codegen and source replay (V52).
No USA code/library replacement, no changes to game assets, saves, gamepad,
graphics, shaders, or physics. Experimental CVar OFF by default.
Production signing is delegated unmodified to the existing permanent signer,
and every certificate/package/version/asset check must pass.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

import pre731_v52 as v52
import pre652_build_signed_v51_gpu_shader_counts_diag as release

VERSION=54
APK_NAME="NFSMW_V54_PRE752_PAL_CATCHUP_EXPERIMENTAL_OFF.apk"
PAL_LIB="lib/arm64-v8a/libmain.so"
USA_LIB="lib/arm64-v8a/libmain_usa.so"
PAL_GUEST=Path("nativo/app/generated/default/nfsmw_recomp.52.cpp")
PAL_CMAKE=Path("nativo/app/CMakeLists.txt")
USA_CMAKE=Path("nativo/app_usa/CMakeLists.txt")
PAL_SRC=Path("nativo/app/src")
PAL_MARKER=b"nfsmw_sem_catchup_carreira"
CERT="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
PACKAGE="io.github.nfsmwrecomp"
ORIGINAL_USA_DSO_SHA="4f32de8f2ff10d4748aa33f208774038ef9bfa402eacc61a49dd7e70f3b1bc83"
PRE743_PAL_TARGET_SHA="b5522d1118e577f0b349d1eeaf727c67eaf234730631be2f60d17a7990ec06e2"
COMMIT="f3642c5a44ddccdf7dca8689859e01ba737e4375"
RAW="https://raw.githubusercontent.com/Juniklx/NFSMW-Recompiled-Mobile/"+COMMIT+"/nativo/experimental/pal_catchup/"
BLOBS={"nfsmw_catchup_carreira.cpp":"70ab71b76a862b6f720c69f0d5e3ca833ed0dfab",
       "nfsmw_catchup_carreira_policy.h":"5093fae500f9d32e4a54b95672475284cc503fed"}
EVIDENCE={}

def sha(b):return hashlib.sha256(b).hexdigest()

def load_reviewed_source(name):
    if name not in BLOBS:raise ValueError("PRE752 unexpected PAL source")
    with urllib.request.urlopen(RAW+name,timeout=40) as r:
        b=r.read(16000)
    if not b or len(b)>12000:
        raise ValueError("PRE752 reviewed PAL source invalid length")
    gitsha=hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()
    if gitsha!=BLOBS[name]:
        raise ValueError("PRE752 reviewed PAL Git blob differs")
    return b

def stage(root):
    previous=v52.stage(root)  # retains entire V51 + V52 signed release chain
    pal=root/PAL_CMAKE
    usa=root/USA_CMAKE
    before=pal.read_bytes()
    usa_before=sha(usa.read_bytes())
    if b"nfsmw_bmw_trace_pre431.cpp" not in before or b"nfsmw_bmw_attr_value_pre625.cpp" not in before:
        raise ValueError("PRE752 original PAL diagnostic source chain absent")
    guest=(root/PAL_GUEST).read_bytes()
    marker=b"DEFINE_REX_FUNC(sub_82332898) {"
    if guest.count(marker)!=1:
        raise ValueError("PRE752 wrong PAL controller guest function")
    i=guest.index(marker)+len(marker)
    j=guest.find(b"\nDEFINE_REX_FUNC(",i)
    if j<0 or sha(guest[i:j+1])!=PRE743_PAL_TARGET_SHA:
        raise ValueError("PRE752 PAL function not byte-identical to authenticated PRE743B")
    for instruction in (b"// lwz r11,6700(r31)",b"// cmpwi cr6,r11,2",
                        b"// stfs f9,0(r25)",b"// stfs f0,0(r24)"):
        if instruction not in guest[i:j+1]:
            raise ValueError("PRE752 PAL controller semantics changed")
    for name in BLOBS:
        target=root/PAL_SRC/name
        if target.exists():
            raise ValueError("PRE752 refuse repeated PAL hook staging")
        target.write_bytes(load_reviewed_source(name))
    cpp=(root/PAL_SRC/"nfsmw_catchup_carreira.cpp").read_bytes()
    policy=(root/PAL_SRC/"nfsmw_catchup_carreira_policy.h").read_bytes()
    for token in (b"REX_HOOK_RAW(sub_82332898)",
                  b"REX_EXTERN(__imp__sub_82332898);",
                  b"__imp__sub_82332898(ctx, base);",
                  b"REXCVAR_DEFINE_BOOL(nfsmw_sem_catchup_carreira, false"):
        if cpp.count(token)!=1:
            raise ValueError("PRE752 PAL hook guard/source altered")
    if b"sub_823328C0" in cpp:
        raise ValueError("PRE752 must not contain USA hook address")
    for token in (b"kRaceStatusGlobal = 0x82A2CB18u",
                  b"kOffsetContexto = 6700u",
                  b"kContextoCarreira = 2u"):
        if token not in policy:raise ValueError("PRE752 PAL race-context gate mismatch")
    pal_ctx=(root/"nativo/app/src/nfsmw_recortes_carrera.cpp").read_bytes()
    if b"g_nfsmw_android_contexto[11]" not in pal_ctx or b"0x82A2CB18" not in pal_ctx:
        raise ValueError("PRE752 original PAL singleton anchor missing")
    anchor="    src/nfsmw_recortes_carrera.cpp\n"
    entry="    src/nfsmw_catchup_carreira.cpp\n"
    cmake=before.decode()
    if cmake.count(anchor)!=1 or entry in cmake:
        raise ValueError("PRE752 unexpected PAL CMake registration")
    patched=cmake.replace(anchor,anchor+entry,1)
    if patched.replace(entry,"",1)!=cmake:
        raise ValueError("PRE752 PAL CMake patch is not reversible")
    pal.write_text(patched)
    if sha(usa.read_bytes())!=usa_before or entry in usa.read_text():
        raise ValueError("PRE752 USA CMake unexpectedly modified")
    if sha((root/PAL_GUEST).read_bytes())!=sha(guest):
        raise ValueError("PRE752 original PAL game code modified")
    EVIDENCE.update({
      "pal_cmake_before_sha256":sha(before),
      "pal_cmake_after_sha256":sha(pal.read_bytes()),
      "usa_cmake_unchanged":True,
      "pal_cmake_reversible":True,
      "pal_function_original_sha256":PRE743_PAL_TARGET_SHA,
      "pal_hook_sha256":sha(cpp),
      "pal_header_sha256":sha(policy),
      "original_generated_guest_unchanged":True,
      "cvar_off_by_default":True,
      "v52_touch_changes_preserved":True,
      "same_unmodified_release_builder_signer":True,
    })
    return {**previous,"pre752_pal_hook_staged":True,"pre752_cvar_off_by_default":True}

def verify(apk,sdk,v30,progress):
    previous=v52.verify(apk,sdk,v30,progress)
    if progress.get("apk_v2_certificate_sha256")!=CERT:
        raise ValueError("PRE752 permanent certificate mismatch")
    with zipfile.ZipFile(apk,"r") as z:
        if z.testzip() is not None:raise ValueError("PRE752 ZIP entry CRC failed")
        pal=z.read(PAL_LIB)
        usa=z.read(USA_LIB)
        if sha(usa)!=ORIGINAL_USA_DSO_SHA:
            raise ValueError("PRE752 USA game library should be identical to V30")
        if not pal.startswith(b"\x7fELF") or PAL_MARKER not in pal or b"[PRE751]" not in pal:
            raise ValueError("PRE752 PAL dynamic Catch-Up hook is absent from signed APK")
        for legacy in (b"PRE648 GPU_SHADER10s",
                       b"NFSMW_PRE635_C3_TWOREQUEST_TRACE",
                       b"NFSMW_PRE194_C3",
                       b"NFSMW_PRE398_GLOBAL_NITRO_FULL"):
            if legacy not in pal:
                raise ValueError("PRE752 previous PAL feature missing: "+legacy.decode())
    progress["pre752_pal_catchup_signed_apk"]={
        "pal_library_sha256":sha(pal),
        "original_usa_library_sha256":sha(usa),
        "only_pal_hook_staged":True,
        "cvar_off_by_default":True,
        "career_catchup_disabled_on_device_proven":False,
        "gameplay_tested":False,
        "graphics_shaders_physics_reduced":False,
        "save_modified":False,
        "permanent_certificate_sha256":CERT,
    }
    return previous

def main():
    ap=argparse.ArgumentParser(add_help=False)
    ap.add_argument("--report",required=True)
    options,_=ap.parse_known_args()
    if VERSION<=52 or release.EXPECTED_CERT!=CERT or release.EXPECTED_PACKAGE!=PACKAGE:
        raise ValueError("PRE752 package/signature/version policy mismatch")
    release.VERSION=VERSION
    release.APK_NAME=APK_NAME
    release.stage_v51=stage
    release.verify_v51=verify
    rc=release.main()
    report=Path(options.report)
    if not report.is_file():raise ValueError("PRE752 original release report absent")
    j=json.loads(report.read_text())
    proof=j.get("pre752_pal_catchup_signed_apk",{})
    ok=(rc==0
        and j.get("status")=="PRE652_V51_GPU_DIAGNOSTIC_SIGNED_VERIFIED"
        and j.get("signed_apk_verified") is True
        and j.get("permanent_certificate_verified") is True
        and j.get("apk_v2_certificate_sha256")==CERT
        and j.get("pre652_target_version_code")==VERSION
        and j.get("v52_touch_dex_verified") is True
        and j.get("drive_upload_success") is True
        and proof.get("only_pal_hook_staged") is True
        and proof.get("cvar_off_by_default") is True)
    j["pre752_gate_ok"]=bool(ok)
    j["pre752_evidence"]=EVIDENCE
    j["pre752_release_for_gameplay_unproven"]=True
    report.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n")
    print("PRE752_SIGNED_V54_PAL_CATCHUP_GATE="+("PASS" if ok else "BLOCKED"))
    print("PRE752_CVAR_DEFAULT_OFF=true")
    print("PRE752_PERMANENT_SIGNER_ONLY=true")
    return 0 if ok else 1

if __name__=="__main__":
    sys.exit(main())
