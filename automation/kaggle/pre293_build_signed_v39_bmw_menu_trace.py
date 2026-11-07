#!/usr/bin/env python3
"""PRE293: V39 PAL/PTBR BMW main-menu passive trace; preserve V38 instrumentation.

Preserve all previous SDL/input patches and logging; versionCode 39 with the same permanent signer.
source patches remain PRE117+PRE128+PRE131+PRE133 from exact PRE99.
Preserve the permanent original signing certificate, PAL/USA shaders/assets,
and prior V30 APK. Enforce log-file code in DEX before publication.
The diagnostic APK is NOT a proven FPS optimization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime,timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import SOURCE_NAME,SOURCE_SHA256,drive_client,download
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
from pre194_c3_guard_pal_diagnostic_patch import patch_verified as propose_pre194, BASE_SHA as PRE194_PAL_BASE_SHA, PATCHED_SHA as PRE194_PAL_PATCHED_SHA, MARKER as PRE194_C3_MARKER
from pre246_passive_money_probe_patch import apply as apply_pre246
from pre247_pal_meter_passive_probe_patch import apply as apply_pre247
from pre284_v37_full_passive_vtable_link_preflight import PAL_SOURCE, PAL_FEATURE, PAL_DECL, sha as pre289_sha
from pre292_bmw_main_menu_native_link_nosign import stage_trace as stage_menu_trace
from pre291_bmw_main_menu_passive_trace_dryrun import TRACE_FLAG as MENU_FEATURE, PROTOTYPE as MENU_DECL
from pre264_bmw_hero_menu_patch_dryrun import SOURCE as MENU_SOURCE
from pre127_apk_v2_certificate_audit import apk_v2_cert_sha256
from pre125_ephemeral_gradle_signing_preflight import (
    P12_DRIVE_ID,PROPERTIES_DRIVE_ID,P12_SHA,CERT_SHA,GRADLE_SHA,
    download_file,digest,parse_properties_safely,certificate_sha256,classify_gradle_error,
)

V30_ID="1Nl3J0gOwGHfV1Yu8FP3Gl5KdzM51gmdi"
V30_SHA="150438943b709f44b55d44a83baea5f239dd55677c3846f3508ee7a4760b2388"
V30_BYTES=47101205
VERSION_CODE=39
EXPECTED_PRE128_SHA="cf3cc930904303ec3b4a081f9987a1ced478697678fcab90b056f07ba0b4957d"
PRE131_PREFLIGHT_RUN="41868450408"
EXPECTED_PRE131_FILES={
    "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp":"9e95ab6637ec742be5d2f0d9aca94c8ce4f5f4f19f93ec94700183699b23ece7",
    "workspace/nativo/sdk/include/rex/ui/overlay/settings_overlay.h":"0b6e351358d421c7cd5122fa2baccfb3145a24921943239d53aeb023f99ca17a",
    "workspace/nativo/sdk/src/ui/imgui_drawer.cpp":"00b1dc75778f9718bd0eceeaae90c49915bebd0f0627698580a8bf8c32c91fa4",
    "workspace/nativo/sdk/include/rex/ui/imgui_drawer.h":"2d91946b4e1aff8437070e381b59ced3aecd07b7a106685da2520c565ef36543",
    "workspace/nativo/sdk/src/ui/nfsmw_modern_font.h":"b1eb3bc2d5a09e535701546ad15e16bde3960915fb3ba0eb5c7df4c7e59e3e83",
}

EXPECTED_PACKAGE="io.github.nfsmwrecomp"
DEST_FOLDER="1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh"
APK_NAME="NFSMW_V39_PRE293_BMW_MAIN_MENU_PASSIVE_TRACE.apk"
REQUIRED_LIBS=(
    "libSDL3.so", "libc++_shared.so", "libfile_redirect_hook.so",
    "libgsl_alloc_hook.so", "libhook_impl.so", "libmain.so",
    "libmain_hook.so", "libmain_usa.so", "librexgpu-xenos.so",
    "librexruntime.so",
)
PRESERVE={
    "lib/arm64-v8a/libmain_usa.so":"4f32de8f2ff10d4748aa33f208774038ef9bfa402eacc61a49dd7e70f3b1bc83",
    "assets/nativo/usa/nfsmw_shaders.nfsp":"8c49de7587c4405a37fe8904981a4902c5294f4e74472dbe3b5d9a643adfa267",
    "assets/nativo/usa/nfsmw_shaders_gles.nfsp":"8a2c9488e930df1a55b1286ee07c1b4eaf6a0cf89fd75815108ca4f0e76c0e02",
    "assets/nativo/nfsmw_shaders.nfsp":"b84602ca9bf6efd84f54ad1509297baccd57c04ffcda494c77f5780a433f95a7",
    "assets/nativo/nfsmw_shaders_gles.nfsp":"aa509b41a484b16226b98aa67f51c88d2a193278719f4123840fe689dc4ef02b",
    "assets/nativo/nfsmw.toml":"9602e9f7409eaab83b295521d00fecb95b04d629a8f7cea48911473f77a4f0d2",
}
V30_RUNTIME_SHA="4e5864fd9eee1d067eaf9f0ad9259a8603ad442d8c7839f6257a58c0f7ffc990"
V31_RUNTIME_SHA="48777767e2b669601e48779bd93c48739043a8d4327376ff1f5bdd85ce1ab560"
V32_RUNTIME_SHA="2b7f21de3b9de89945d13898ff4cce7990d345dd375a1ff03b5e8c5d9a87855c"
V33_RUNTIME_SHA="b4b2f7c99aff7ebb3384ed02a7680250b6322fad686d22d8ac4692f4103fcca2"
V34_LIBSDL3_SHA="9f779073464a307102bcb292aa2d9504a9090509ad2f56afd0f7f6a35f76b881"
PRE180_SDL_PATCHED_SHA="bdd3200a44e055168e5092cec7f5adbf5f24cabe7af0b629fceec866f567cb33"
V35_PAL_MAIN_SHA="ce33b914b113531d888010368d8570205e4acf54542e659e36963790a4dc5a7c"


def sha_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()


def sdk_root()->Path:
    for candidate in (os.environ.get("ANDROID_HOME"),os.environ.get("ANDROID_SDK_ROOT"),"/usr/local/lib/android/sdk"):
        if candidate and (Path(candidate)/"build-tools").is_dir():
            return Path(candidate).resolve()
    raise FileNotFoundError("Android SDK build tools unavailable")


def latest_tool(sdk:Path,name:str)->Path:
    for folder in sorted((sdk/"build-tools").iterdir(),reverse=True):
        p=folder/name
        if p.is_file():return p
    raise FileNotFoundError("Android build tool "+name+" missing")


def safe_gradle_error_context(content:str,props:dict)->list[str]:
    # Keep only limited failure markers. Never publish raw Gradle logs.
    lines=[]
    markers=("FAILURE: Build failed","What went wrong:","Could not resolve",
             "Could not find","Execution failed for task","CMake Error",
             "ninja: error","clang++: error","error:","SDK location not found",
             "Build failed with an exception","No matching variant","A problem occurred")
    for line in content.splitlines():
        if any(v.lower() in line.lower() for v in markers):
            s=line.strip()
            for secret in (props.get("storePassword",""),props.get("keyPassword","")):
                if secret and len(secret)>3:s=s.replace(secret,"[REDACTED]")
            s=re.sub(r"(/[^\s:]+){2,}","[path]",s)
            s=re.sub(r"(token|password|secret)\s*[:=]\s*\S+",r"\1=[REDACTED]",s,flags=re.I)
            lines.append(s[:220])
    return lines[-15:]


def verified_v30(apk:Path)->dict[str,bytes]:
    if apk.stat().st_size!=V30_BYTES or digest(apk)!=V30_SHA:
        raise ValueError("V30 baseline APK changed")
    if apk_v2_cert_sha256(apk)!=CERT_SHA:
        raise ValueError("Original V30 has unexpected APK v2 signer certificate")
    result={}
    with zipfile.ZipFile(apk,"r") as z:
        if z.testzip() is not None:raise ValueError("V30 ZIP CRC failed")
        for path,expected_sha in PRESERVE.items():
            data=z.read(path)
            if sha_bytes(data)!=expected_sha:raise ValueError("V30 asset hash mismatch")
            result[path]=data
        result["runtime"]=z.read("lib/arm64-v8a/librexruntime.so")
        if sha_bytes(result["runtime"])!=V30_RUNTIME_SHA:raise ValueError("V30 runtime hash changed")
    return result


def prepare_usa_edition(root:Path,bundle:Path,v30:dict[str,bytes])->dict:
    required=[
        root/"nativo/app/generated/default/sources.cmake",
        root/"nativo/app_usa/generated/default/sources.cmake",
        root/"nativo/out/nfsmw_shaders.nfsp",
        root/"nativo/out/nfsmw_shaders_gles.nfsp",
        root/"nativo/out/usa/edicion.json",
    ]
    if not all(p.is_file() for p in required):raise FileNotFoundError("Native PAL/USA staging incomplete")
    for name,suffix in (
        ("assets/nativo/nfsmw_shaders.nfsp","nativo/out/nfsmw_shaders.nfsp"),
        ("assets/nativo/nfsmw_shaders_gles.nfsp","nativo/out/nfsmw_shaders_gles.nfsp"),
    ):
        if digest(root/suffix)!=PRESERVE[name]:raise ValueError("PAL shader differs from V30")
    meta=json.loads((root/"nativo/out/usa/edicion.json").read_text(encoding="utf-8"))
    if not isinstance(meta,dict) or str(meta.get("id","")).lower()!="usa":
        raise ValueError("USA edition metadata id mismatch")
    # Preserve USA game library and assets from the verified V30 APK.
    # No generated game files are uploaded to GitHub source control.
    dll=bundle/"jniLibs/arm64-v8a/libmain_usa.so"
    dll.parent.mkdir(parents=True,exist_ok=True)
    dll.write_bytes(v30["lib/arm64-v8a/libmain_usa.so"])
    for name in (
        "assets/nativo/usa/nfsmw_shaders.nfsp",
        "assets/nativo/usa/nfsmw_shaders_gles.nfsp",
    ):
        dest=bundle/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(v30[name])
    (bundle/"ediciones.json").write_text(json.dumps([meta],ensure_ascii=False)+"\n",encoding="utf-8")
    return {"usa_edition_id_verified":True,
            "usa_library_preserved":True,
            "usa_shader_assets_preserved":True,
            "pal_shader_assets_match_v30":True}


def verify_apk(apk:Path,sdk:Path,v30:dict[str,bytes],progress:dict)->dict:
    progress["verification_subphase"]="APK_FILE_SIZE"
    if not apk.is_file() or apk.stat().st_size<25_000_000:
        raise ValueError("APK absent or unexpectedly small")
    progress["apk_candidate_bytes"]=apk.stat().st_size
    progress["apk_candidate_sha256"]=digest(apk)
    progress["verification_subphase"]="APK_SIGNER_CRYPTOVALIDATION"
    apksigner=latest_tool(sdk,"apksigner")
    aapt=latest_tool(sdk,"aapt")
    check=subprocess.run([str(apksigner),"verify","--verbose","--print-certs",str(apk)],
                         capture_output=True,text=True,timeout=90,check=False)
    if check.returncode!=0:raise ValueError("apksigner verify failed")
    progress["verification_subphase"]="APK_SIGNER_CERTIFICATE_FINGERPRINT"
    fingerprints=re.findall(r"Signer #1 certificate SHA-256 digest:\s*([0-9a-fA-F:]+)",check.stdout)
    cli_fingerprints=[fp.replace(":","").lower() for fp in fingerprints]
    progress["apksigner_cli_cert_fingerprints"]=cli_fingerprints
    progress["apksigner_cli_cert_count"]=len(cli_fingerprints)
    progress["verification_subphase"]="APK_V2_DER_SIGNER_CERTIFICATE"
    # Do not rely exclusively on text formatting of apksigner --print-certs.
    # apksigner verifies the cryptographic signatures above; independently
    # identify the exact DER certificate used by the v2 signer, minSdk=26.
    v2_cert_digest=apk_v2_cert_sha256(apk)
    progress["apk_v2_certificate_sha256"]=v2_cert_digest
    if v2_cert_digest!=CERT_SHA:
        raise ValueError("APK v2 permanent signing certificate mismatch")
    if cli_fingerprints and v2_cert_digest not in cli_fingerprints:
        raise ValueError("APK signer CLI certificate disagrees with APK v2 DER certificate")
    progress["verification_subphase"]="APK_SIGNING_CERTIFICATE_APPROVED"
    progress["verification_subphase"]="APK_AAPT_BADGING"
    badge=subprocess.run([str(aapt),"dump","badging",str(apk)],
                         capture_output=True,text=True,timeout=90,check=False)
    if badge.returncode!=0:raise ValueError("AAPT could not inspect APK")
    match=re.search(r"package:\s+name='([^']+)'\s+versionCode='(\d+)'",badge.stdout)
    if match is None or match.group(1)!=EXPECTED_PACKAGE or int(match.group(2))!=VERSION_CODE:
        raise ValueError("APK applicationId/versionCode mismatch")
    progress["verification_subphase"]="APK_ZIP_CRC"
    with zipfile.ZipFile(apk) as z:
        if z.testzip() is not None:raise ValueError("Generated APK ZIP CRC failed")
        present=set(z.namelist())
        progress["verification_subphase"]="APK_REQUIRED_ARM64_LIBRARIES"
        missing=[x for x in REQUIRED_LIBS if "lib/arm64-v8a/"+x not in present]
        if missing:
            progress["missing_required_arm64_libraries"]=missing
            raise ValueError("New APK missing required native library")
        kept={}
        for name,expected in PRESERVE.items():
            progress["verification_subphase"]="APK_PRESERVED_ASSET_SHA256"
            if name not in present or sha_bytes(z.read(name))!=expected:
                progress["mismatched_preserved_asset"]=name
                progress["mismatched_asset_was_present"]=name in present
                raise ValueError("V31 changed required V30 PAL/USA content")
            kept[name]=True
        progress["verification_subphase"]="APK_PRE194_C3_PAL_MAIN_BINARY_MARKER"
        main_binary=z.read("lib/arm64-v8a/libmain.so")
        if main_binary[:4]!=b"\x7fELF":
            raise ValueError("PRE194 V36 PAL main is not ELF")
        pal_main_sha=sha_bytes(main_binary)
        if pal_main_sha==V35_PAL_MAIN_SHA:
            raise ValueError("PRE194 V36 PAL libmain is identical to V35")
        if PRE194_C3_MARKER not in main_binary:
            raise ValueError("PRE194 V36 PAL libmain lacks C3 predicate marker")
        if b"referencia_distinta" not in main_binary or b"copia_duplicada" not in main_binary:
            raise ValueError("PRE194 V36 PAL binary does not contain both C3 predicate names")
        if b"NFSMW_PRE246_CHEATS_DIAG" not in main_binary:
            raise ValueError("PRE246 passive money trace marker missing from PAL libmain")
        progress["pre246_passive_money_trace_marker_verified"]=True
        if b"NFSMW_PRE247_CHEATS_DIAG" not in main_binary:
            raise ValueError("PRE247 passive float meter trace marker missing from PAL libmain")
        progress["pre247_passive_meter_trace_marker_verified"]=True
        progress["pre194_c3_pal_libmain_sha256"]=pal_main_sha
        progress["pre194_c3_marker_verified_in_pal_libmain"]=True
        progress["verification_subphase"]="APK_PRE180_ANDROID_SDL3_LINKAGE"
        sdl3_hash=sha_bytes(z.read("lib/arm64-v8a/libSDL3.so"))
        progress["libSDL3_sha256"]=sdl3_hash
        if sdl3_hash==V34_LIBSDL3_SHA:
            raise ValueError("PRE180 compiled libSDL3 identical to V34: patch not reflected")
        progress["pre180_libsdl3_distinct_from_v34"]=True
        progress["verification_subphase"]="APK_RUNTIME_LINKAGE_DIFFERENCE"
        runtime=sha_bytes(z.read("lib/arm64-v8a/librexruntime.so"))
        progress["runtime_identical_to_v30"]=(runtime==V30_RUNTIME_SHA)
        progress["runtime_identical_to_v31"]=(runtime==V31_RUNTIME_SHA)
        if runtime==V31_RUNTIME_SHA:raise ValueError("V34 runtime identical to V31")
        progress["runtime_identical_to_v32"]=(runtime==V32_RUNTIME_SHA)
        if runtime==V32_RUNTIME_SHA:raise ValueError("V34 runtime identical to V32")
        progress["runtime_identical_to_v33"]=(runtime==V33_RUNTIME_SHA)
        if runtime==V33_RUNTIME_SHA:raise ValueError("V34 runtime identical to V33 despite input pump patch")
        progress["runtime_difference_note"]="Source was hash-verified; log toggle or reproducibility may change runtime"
        progress["verification_subphase"]="APK_ANDROID_LOGGING_CODE_PRESENT"
        dex_files=[name for name in present if name.startswith("classes") and name.endswith(".dex")]
        dex=b"".join(z.read(name) for name in dex_files)
        if b"nfsmw.log" not in dex or b"--log_file=" not in dex:
            raise ValueError("Diagnostic V31 DEX lacks registered game-log path")
        progress["logging_code_in_dex_verified"]=True
        progress["verification_subphase"]="APK_ALL_GATES_PASSED"
        return {
            "signed_certificate_sha256_match":True,
            "signed_schemes_verified":True,
            "package_id":match.group(1),
            "version_code":int(match.group(2)),
            "android_arm64_required_libraries_present":True,
            "required_arm64_library_count":len(REQUIRED_LIBS),
            "pal_usa_shaders_preserved":True,
            "usa_main_library_unchanged_from_v30":True,
            "pre194_c3_pal_marker_verified":True,
            "pre194_pal_main_sha256":pal_main_sha,
            "runtime_identical_to_v30":runtime==V30_RUNTIME_SHA,
            "registration_enabled_on_gradle":True,
            "new_librexruntime_sha256":runtime,
            "new_libSDL3_sha256":sdl3_hash,
            "apk_size":apk.stat().st_size,
            "apk_sha256":digest(apk),
            "zip_entries":len(present),
        }


def upload_verified_apk(drive,apk:Path)->dict:
    from googleapiclient.http import MediaFileUpload
    media=MediaFileUpload(str(apk),mimetype="application/vnd.android.package-archive",resumable=True,chunksize=8*1024*1024)
    operation=drive.files().create(
        body={"name":APK_NAME,"parents":[DEST_FOLDER],
              "mimeType":"application/vnd.android.package-archive"},
        media_body=media,fields="id,name,mimeType,size,md5Checksum,webViewLink",
        supportsAllDrives=True,
    )
    reply=None
    while reply is None:
        _progress,reply=operation.next_chunk(num_retries=4)
    if reply.get("name")!=APK_NAME or int(reply.get("size",-1))!=apk.stat().st_size:
        raise ValueError("Drive upload size/name mismatch")
    info=drive.files().get(fileId=reply["id"],fields="id,name,size,md5Checksum,webViewLink,parents",
                           supportsAllDrives=True).execute()
    if info.get("name")!=APK_NAME or int(info.get("size",-1))!=apk.stat().st_size:
        raise ValueError("Drive upload readback size mismatch")
    if DEST_FOLDER not in info.get("parents",[]):
        raise ValueError("Drive upload is outside intended APK folder")
    md5=hashlib.md5()
    with apk.open("rb") as f:
        for block in iter(lambda:f.read(8*1024*1024),b""):md5.update(block)
    if info.get("md5Checksum","").lower()!=md5.hexdigest():
        raise ValueError("Drive upload MD5 mismatch")
    return {"id":info["id"],"file_name":info["name"],
            "url":info.get("webViewLink"),"size":int(info["size"]),
            "remote_md5_matches":True,"folder_verified":True}


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    p.add_argument("--report",required=True)
    p.add_argument("--verified-output",required=True)
    p.add_argument("--upload",action="store_true")
    args=p.parse_args()
    if not re.fullmatch(r"\d+",args.run_id):raise ValueError("Bad GitHub run ID")
    report_path=Path(args.report)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    output=Path(args.verified_output)
    report={
        "etapa":"PRE293_BUILD_V39_BMW_MAIN_MENU_PASSIVE_DIAGNOSTIC",
        "run_id":args.run_id,
        "phase":"INITIAL","status":"NAO_VALIDADO",
        "target_version_code":VERSION_CODE,
        "pre194_c3_pal_patch_applied":False,
        "pre194_c3_marker_in_libmain_verified":False,
         "pre246_passive_money_trace_marker_verified":False,
        "pre247_passive_meter_trace_marker_verified":False,
        "verified_source_pre99":False,
        "pre117_exact_patch_applied_in_runner":False,
        "pre128_exact_patch_applied_in_runner":False,
        "pre131_exact_patches_applied_in_runner":False,
        "pre133_exact_patch_applied_in_runner":False,
        "pre157_callback_move_applied":False,
        "pre165_sdl_delay2_applied":False,
        "pre165_sdl_source_sha256":None,
        "pre170_input_pump_8ms_applied":False,
        "pre170_input_cpp_sha256":None,
        "pre170_input_header_sha256":None,
        "pre180_sdl_patch_applied":False,
        "pre180_sdl_source_sha256":None,
        "pre180_libsdl3_distinct_from_v34":False,
        "pre133_arm64_preflight_verified":False,
        "pre131_native_touch_syntax_preflight_verified":False,
        "phone_touch_scroll_tested":False,
        "phone_visual_theme_tested":False,
        "permanent_certificate_verified":False,
        "v30_baseline_verified":False,
        "gradle_release_succeeded":False,
        "game_file_logging_requested":True,
        "logging_code_in_dex_verified":False,
        "game_log_created_on_phone_verified":False,
        "fps_gain_verified":False,
        "signed_apk_verified":False,
        "drive_upload_requested":bool(args.upload),
        "drive_upload_success":False,
        "original_kaggle_workspace_modified":False,
        "original_drive_apk_modified":False,
        "permanent_signing_backup_modified":False,
        "version_counter_in_drive_modified":False,
        "source_code_published_to_github":False,
        "private_credentials_in_report":False,
    }
    try:
        prelim=Path("automation/kaggle/status/pre125_gradle_signing_preflight.json")
        q=json.loads(prelim.read_text(encoding="utf-8"))
        if q.get("status")!="PRE125_CERTIFICADO_E_GRADLE_CONFIG_VALIDOS" or not q.get("signing_certificate_sha256_expected"):
            raise ValueError("PRE125 signing/Gradle gate not passed")
        verified_pre128=json.loads(Path("automation/kaggle/status/pre128_touch_theme_arm64.json").read_text(encoding="utf-8"))
        if (verified_pre128.get("run_id")!="41856230258" or
                verified_pre128.get("status")!="PRE128_ANDROID_ARM64_SYNTAX_PASSED_NOT_APPLIED_TO_RELEASE" or
                verified_pre128.get("pre128_source_sha256")!=EXPECTED_PRE128_SHA or
                verified_pre128.get("arm64_syntax_passed") is not True):
            raise ValueError("PRE128 isolated Android ARM64 source gate not proven")
        report["pre128_arm64_syntax_preflight_verified"]=True
        pre131_report=json.loads(Path("automation/kaggle/status/pre131_touch_theme_arm64.json").read_text(encoding="utf-8"))
        if (pre131_report.get("run_id")!=PRE131_PREFLIGHT_RUN or
                pre131_report.get("status")!="PRE131_ANDROID_ARM64_SYNTAX_PASSED" or
                pre131_report.get("patch_file_hashes")!=EXPECTED_PRE131_FILES or
                pre131_report.get("arm64_settings_syntax_ok") is not True or
                pre131_report.get("arm64_imgui_drawer_syntax_ok") is not True):
            raise ValueError("PRE131 ARM64 syntax and exact patch hashes not approved")
        report["pre131_native_touch_syntax_preflight_verified"]=True
        pre133_report=json.loads(Path("automation/kaggle/status/pre133_touch_theme_arm64.json").read_text(encoding="utf-8"))
        if (pre133_report.get("run_id")!="41876482785" or
                pre133_report.get("status")!="PRE133_ANDROID_ARM64_SYNTAX_PASSED" or
                pre133_report.get("pre133_sources_patched_in_isolated_runner") is not True or
                pre133_report.get("arm64_settings_syntax_ok") is not True or
                pre133_report.get("arm64_imgui_drawer_syntax_ok") is not True or
                len(pre133_report.get("pre133_source_sha256",""))!=64):
            raise ValueError("PRE133 exact ARM64 syntax gate not satisfied")
        report["pre133_arm64_preflight_verified"]=True
        sdk=sdk_root()
        if not (sdk/"ndk/28.2.13676358/source.properties").is_file():
            raise FileNotFoundError("NDK r28.2 not installed")
        if not (sdk/"cmake/3.31.6").is_dir():
            raise FileNotFoundError("CMake 3.31.6 not installed")
        base=Path(os.environ.get("RUNNER_TEMP","/tmp"))
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre170_",dir=base) as tmp:
            temp=Path(tmp)
            if shutil.disk_usage(temp).free<6*1024**3:
                raise RuntimeError("Insufficient ephemeral disk for native release")
            signing=temp/"signing"
            signing.mkdir(mode=0o700)
            key=signing/"NFSMW_ASSINATURA_PERMANENTE.p12"
            creds=signing/"NFSMW_ASSINATURA_CREDENCIAIS.properties"
            report["phase"]="VERIFY_ORIGINAL_PERMANENT_SIGNING"
            d=drive_client()
            download_file(d,P12_DRIVE_ID,key)
            download_file(d,PROPERTIES_DRIVE_ID,creds)
            key.chmod(0o600)
            creds.chmod(0o600)
            if digest(key)!=P12_SHA:raise ValueError("P12 SHA256 wrong")
            secret_props=parse_properties_safely(creds)
            if certificate_sha256(key,secret_props)!=CERT_SHA:raise ValueError("Signing certificate wrong")
            report["permanent_certificate_verified"]=True
            (signing/"NFSMW_PROXIMO_VERSION_CODE.txt").write_text(str(VERSION_CODE)+"\n")
            report["phase"]="DOWNLOAD_V30_BASELINE"
            old=temp/"v30.apk"
            download_file(d,V30_ID,old)
            old_files=verified_v30(old)
            report["v30_baseline_verified"]=True
            report["phase"]="DOWNLOAD_PRE99_SNAPSHOT"
            tar=temp/"pre99.tar.gz"
            download(d,tar)
            sha,_md5,sz=sha_file(tar)
            if sha!=EXPECTED_SHA256 or sz!=EXPECTED_BYTES:
                raise ValueError("PRE99 SHA mismatch")
            restored=temp/"restored"
            restored.mkdir()
            report["phase"]="RESTORE_VERIFIED_PRE99"
            restore(tar,restored)
            tar.unlink(missing_ok=True)
            root=restored/"workspace"
            src=root/"nativo/sdk/src/ui/overlay/settings_overlay.cpp"
            if digest(src)!=SOURCE_SHA256:raise ValueError("PRE92 source mismatch")
            if digest(root/"android/app/build.gradle.kts")!=GRADLE_SHA:
                raise ValueError("PRE99 Gradle source mismatch")
            report["verified_source_pre99"]=True
            report["phase"]="APPLY_EXACT_PRE117_EPHEMERAL_ONLY"
            modified,diff=propose(src.read_text(encoding="utf-8"))
            src.write_text(modified,encoding="utf-8")
            if digest(src)!=EXPECTED_PRE117_SHA:raise ValueError("PRE117 patch SHA mismatch")
            report["pre117_exact_patch_applied_in_runner"]=True
            report["phase"]="APPLY_EXACT_PRE128_EPHEMERAL_ONLY"
            proposed_v31=propose_pre128(modified)
            src.write_text(proposed_v31,encoding="utf-8")
            if digest(src)!=EXPECTED_PRE128_SHA:raise ValueError("PRE128 patched source SHA mismatch")
            report["pre128_exact_patch_applied_in_runner"]=True
            report["source_pre128_sha256"]=EXPECTED_PRE128_SHA
            report["phase"]="APPLY_EXACT_PRE131_EPHEMERAL_ONLY"
            source_paths={
                "drawer_cpp":root/"nativo/sdk/src/ui/imgui_drawer.cpp",
                "drawer_header":root/"nativo/sdk/include/rex/ui/imgui_drawer.h",
                "settings_header":root/"nativo/sdk/include/rex/ui/overlay/settings_overlay.h",
                "font":root/"android/app/src/main/res/font/michroma.ttf",
            }
            modifications=propose_pre131(src.read_bytes(),
                 source_paths["drawer_cpp"].read_bytes(),
                 source_paths["drawer_header"].read_bytes(),
                 source_paths["settings_header"].read_bytes(),
                 source_paths["font"].read_bytes())
            if set(modifications)!=set(EXPECTED_PRE131_FILES):
                raise ValueError("PRE131 unexpected generated patch targets")
            for rel,blob in modifications.items():
                if sha_bytes(blob)!=EXPECTED_PRE131_FILES[rel]:
                    raise ValueError("PRE131 exact source SHA changed")
                dst=restored/rel
                dst.parent.mkdir(parents=True,exist_ok=True)
                dst.write_bytes(blob)
                if digest(dst)!=EXPECTED_PRE131_FILES[rel]:
                    raise ValueError("PRE131 applied bytes mismatch")
            report["pre131_exact_patches_applied_in_runner"]=True
            report["source_pre131_sha256"]=EXPECTED_PRE131_FILES["workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp"]
            report["phase"]="APPLY_EXACT_PRE133_SDL_MOUSE_BRIDGE_EPHEMERAL_ONLY"
            patched_v31=propose_pre133(src.read_bytes())
            expected_v31_hash=pre133_report["pre133_source_sha256"]
            if (sha_bytes(patched_v31)!=expected_v31_hash or
                    pre133_report.get("patch_file_hashes",{}).get("workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp")!=expected_v31_hash):
                raise ValueError("PRE133 source differs from exact ARM64 validated patch")
            src.write_bytes(patched_v31)
            if digest(src)!=expected_v31_hash:
                raise ValueError("PRE133 patch bytes changed after application")
            report["pre133_exact_patch_applied_in_runner"]=True
            report["source_pre133_sha256"]=expected_v31_hash
            report["phase"]="APPLY_PRE157_MOVE_CALLBACK_ONLY"
            presenter_source=root/"nativo/sdk/src/ui/presenter.cpp"
            raw_presenter=presenter_source.read_bytes()
            if sha_bytes(raw_presenter)!=PRE157_BASE_SHA:
                raise ValueError("V31 base presenter.cpp mismatch; refusing optimization")
            modified_presenter=propose_pre157(raw_presenter)
            presenter_source.write_bytes(modified_presenter)
            if digest(presenter_source)!=sha_bytes(modified_presenter):
                raise ValueError("PRE157 candidate source write did not verify")
            report["pre157_callback_move_applied"]=True
            report["pre157_source_sha256"]=sha_bytes(modified_presenter)
            report["phase"]="APPLY_PRE165_SDL_WAKE_DELAY2_EXACT_SOURCE"
            sdl_source=root/"nativo/sdk/src/ui/windowed_app_context_sdl.cpp"
            original_sdl=sdl_source.read_bytes()
            if sha_bytes(original_sdl)!=PRE165_BASE_SHA:
                raise ValueError("V32 SDL base mismatch, refusing PRE165 optimization")
            modified_sdl=propose_pre165(original_sdl)
            sdl_source.write_bytes(modified_sdl)
            if digest(sdl_source)!=sha_bytes(modified_sdl):
                raise ValueError("PRE165 SDL source did not verify after patch")
            report["pre165_sdl_delay2_applied"]=True
            report["pre165_sdl_source_sha256"]=sha_bytes(modified_sdl)
            report["phase"]="APPLY_PRE170_GUARDED_ANDROID_INPUT_PUMP_8MS"
            input_cpp=root/"nativo/sdk/src/input/sdl/sdl_input_driver.cpp"
            input_header=root/"nativo/sdk/include/rex/input/sdl/sdl_input_driver.h"
            if digest(input_cpp)!=PRE170_CPP_SHA or digest(input_header)!=PRE170_HEADER_SHA:
                raise ValueError("PRE170 source digest mismatch")
            new_input_cpp,new_input_header=propose_pre170(input_cpp.read_bytes(),input_header.read_bytes())
            input_cpp.write_bytes(new_input_cpp)
            input_header.write_bytes(new_input_header)
            if digest(input_cpp)!=sha_bytes(new_input_cpp) or digest(input_header)!=sha_bytes(new_input_header):
                raise ValueError("PRE170 patch readback mismatch")
            report["pre170_input_pump_8ms_applied"]=True
            report["pre170_input_cpp_sha256"]=sha_bytes(new_input_cpp)
            report["pre170_input_header_sha256"]=sha_bytes(new_input_header)
            report["phase"]="APPLY_PRE180_ANDROID_SDL3_WAIT_SOURCE_HASH_PINNED"
            sdl3_source=root/"nativo/sdk/thirdparty/sdl3/src/events/SDL_events.c"
            if digest(sdl3_source)!=PRE180_SDL_BASE_SHA:
                raise ValueError("PRE180 SDL3 vendored source mismatch; no patch or build allowed")
            patched_sdl3=propose_pre180(sdl3_source.read_bytes())
            if sha_bytes(patched_sdl3)!=PRE180_SDL_PATCHED_SHA:
                raise ValueError("PRE180 output SHA mismatch; no patch or build allowed")
            sdl3_source.write_bytes(patched_sdl3)
            if digest(sdl3_source)!=PRE180_SDL_PATCHED_SHA:
                raise ValueError("PRE180 source readback mismatch")
            report["pre180_sdl_patch_applied"]=True
            report["pre180_sdl_source_sha256"]=PRE180_SDL_PATCHED_SHA
            report["phase"]="PRE194_APPLY_C3_GUARD_PREDICATE_LOGGING_PAL_ONLY"
            pal_c3_source=root/"nativo/app/src/nfsmw_nativo_dibujos.cpp"
            if digest(pal_c3_source)!=PRE194_PAL_BASE_SHA:
                raise ValueError("PRE194 PAL C3 exact authenticated PRE99 source mismatch")
            patched_pal_c3=propose_pre194(pal_c3_source.read_bytes())
            if sha_bytes(patched_pal_c3)!=PRE194_PAL_PATCHED_SHA:
                raise ValueError("PRE194 PAL C3 output digest mismatch")
            pal_c3_source.write_bytes(patched_pal_c3)
            if digest(pal_c3_source)!=PRE194_PAL_PATCHED_SHA:
                raise ValueError("PRE194 PAL C3 readback mismatch")
            report["pre194_c3_pal_patch_applied"]=True
            report["pre194_c3_pal_patched_sha256"]=PRE194_PAL_PATCHED_SHA
            report["phase"]="PRE246_APPLY_PASSIVE_MONEY_TRACE_PAL_ONLY"
            report["pre246_passive_trace"]=apply_pre246(root)
            if report["pre246_passive_trace"].get("money_traces")!=8:
                raise ValueError("PRE246 expected eight passive money sites")
            report["phase"]="PRE247_APPLY_PASSIVE_FLOAT_METER_TRACES_PAL_ONLY"
            report["pre247_passive_meters"]=apply_pre247(root)
            if report["pre247_passive_meters"].get("combined_money_and_meter_probe_sites") != 16:
                raise ValueError("PRE247 expected sixteen passive money/nitro/speedbreaker sites")
            report["phase"]="PRE293_STAGE_BMW_MAIN_MENU_PASSIVE_TRACES"
            stage=stage_menu_trace(root)
            if not (stage.get("menu_registered_once") and stage.get("source_patch_reversible")
                    and stage.get("original_guest_ops_unchanged")):
                raise ValueError("PRE293 menu trace staging invariant failed")
            # Preserve V38 diagnostic path unchanged; enable only passive callbacks.
            pal_shard=root/PAL_SOURCE.removeprefix("workspace/")
            patched=pal_shard.read_text(encoding="utf-8")
            if patched.count(PAL_DECL)!=1 or ("#define "+PAL_FEATURE) in patched:
                raise ValueError("PRE293 previous passive setup flag unexpected")
            patched=patched.replace(PAL_DECL,"#define "+PAL_FEATURE+" 1\n"+PAL_DECL,1)
            pal_shard.write_text(patched,encoding="utf-8")
            menu_shard=root/MENU_SOURCE.removeprefix("workspace/")
            menu_text=menu_shard.read_text(encoding="utf-8")
            if menu_text.count(MENU_DECL)!=1 or ("#define "+MENU_FEATURE) in menu_text:
                raise ValueError("PRE293 main-menu trace flag declaration unexpected")
            menu_text=menu_text.replace(MENU_DECL,"#define "+MENU_FEATURE+" 1\n"+MENU_DECL,1)
            menu_shard.write_text(menu_text,encoding="utf-8")
            if (menu_shard.read_text(encoding="utf-8").count("#define "+MENU_FEATURE+" 1")!=1
                    or pal_shard.read_text(encoding="utf-8").count("#define "+PAL_FEATURE+" 1")!=1):
                raise ValueError("PRE293 passive flags not uniquely enabled")
            report["pre293_main_menu_source_sha256"]=pre289_sha(menu_shard.read_bytes())
            report["pre293_setup_source_sha256"]=pre289_sha(pal_shard.read_bytes())
            report["pre293_menu_logger_source_sha256"]=stage["menu_logger_sha256"]
            report["pre293_both_trace_flags_enabled"]=True
            report["pre293_menu_categories_modified"]=False
            report["phase"]="STAGE_VERIFIED_USA_FROM_V30"
            bundle=temp/"editions"
            bundle.mkdir()
            report["edition_gates"]=prepare_usa_edition(root,bundle,old_files)
            report["phase"]="ANDROID_SDK_CONFIGURATION"
            android=root/"android"
            (android/"local.properties").write_text("sdk.dir="+str(sdk)+"\n",encoding="utf-8")
            child=os.environ.copy()
            child["NFSMW_SIGNING_DIR"]=str(signing)
            child["NFSMW_VERSION_CODE"]=str(VERSION_CODE)
            child["ANDROID_HOME"]=str(sdk)
            child["ANDROID_SDK_ROOT"]=str(sdk)
            child["CMAKE_BUILD_PARALLEL_LEVEL"]="2"
            # PRE139: persist ONLY Gradle downloaded dependencies / wrapper,
            # outside this ephemeral source and private signing workspace.
            external_gradle=os.environ.get("NFSMW_GRADLE_USER_HOME")
            if external_gradle:
                root_cache=Path(external_gradle).absolute()
                runner_temp=Path(os.environ.get("RUNNER_TEMP","/tmp")).resolve()
                if (root_cache.name!="nfsmw-gradle-home" or
                        runner_temp not in root_cache.parents or
                        root_cache.is_symlink() or
                        root_cache==temp or temp in root_cache.parents):
                    raise ValueError("Unsafe persistent dependency cache path")
                root_cache.mkdir(parents=True,exist_ok=True,mode=0o700)
                child["GRADLE_USER_HOME"]=str(root_cache)
                report["gradle_dependency_cache_policy"]="PRE139_DEPENDENCIES_ONLY"
            else:
                child["GRADLE_USER_HOME"]=str(temp/"gradle_cache")
                report["gradle_dependency_cache_policy"]="EPHEMERAL_FALLBACK_NO_SHARED_CACHE"
            # PRE140: optional SDK-only CMake compiler launcher. This is
            # explicitly separate from the PRE139 dependency cache. Game
            # translation C++ units under nativo/app and app_usa bypass ccache.
            requested_launcher=os.environ.get("NFSMW_PRE140_CCACHE_LAUNCHER")
            if requested_launcher:
                expected_launcher=Path(__file__).resolve().parent/"pre140_sdk_only_ccache_launcher.sh"
                launcher=Path(requested_launcher)
                if launcher.resolve()!=expected_launcher.resolve() or not expected_launcher.is_file():
                    raise ValueError("PRE140 SDK launcher path is not the pinned private script")
                blob=expected_launcher.read_bytes()
                git_blob=hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
                if git_blob!="c4949a0adbb788c82b621c7c39fa29baba02b4ae":
                    raise ValueError("PRE140 SDK-only launcher content changed; rerun policy checks")
                if not os.access(launcher,os.X_OK):
                    raise ValueError("PRE140 launcher is not executable")
                runner_temp=Path(os.environ.get("RUNNER_TEMP","/tmp")).resolve()
                cache_dir=Path(os.environ.get("CCACHE_DIR","")).absolute()
                if (cache_dir!=runner_temp/"nfsmw-ccache-sdk-only" or
                        cache_dir.is_symlink() or
                        cache_dir==temp or temp in cache_dir.parents):
                    raise ValueError("PRE140 unsafe persistent SDK ccache directory")
                ccache_bin=shutil.which("ccache")
                if not ccache_bin:
                    raise FileNotFoundError("PRE140 ccache executable unavailable")
                cache_dir.mkdir(parents=True,exist_ok=True,mode=0o700)
                child.update({
                    "NFSMW_SDK_ONLY_CCACHE_ENABLED":"1",
                    "NFSMW_SDK_SOURCE_ROOT":str(root/"nativo/sdk"),
                    "NFSMW_CCACHE_BIN":str(Path(ccache_bin).resolve()),
                    "CMAKE_C_COMPILER_LAUNCHER":str(launcher),
                    "CMAKE_CXX_COMPILER_LAUNCHER":str(launcher),
                    "CCACHE_DIR":str(cache_dir),
                    "CCACHE_BASEDIR":str(root),
                    "CCACHE_COMPILERCHECK":"content",
                    "CCACHE_MAXSIZE":"1024M",
                    "CCACHE_COMPRESS":"1",
                })
                report["pre140_sdk_only_ccache_requested"]=True
                report["pre140_launcher_pinned_blob_sha1"]=git_blob
                report["pre140_cache_contains_game_translation_objects_expected"]=False
                subprocess.run([str(ccache_bin),"--zero-stats"],env=child,check=True,
                               stdout=subprocess.DEVNULL)
            else:
                report["pre140_sdk_only_ccache_requested"]=False
            args_gradle=[
                "bash","gradlew","assembleRelease","--no-daemon","--console=plain","--max-workers=2",
                "-Pnfsmw.motor=nativo","-Pnfsmw.edicion=pal_es",
                "-Pnfsmw.registro=true",
                "-Pnfsmw.ediciones="+str(bundle),
                "-Pnfsmw.sdk="+str(root/"nativo/sdk"),
                "-Dorg.gradle.jvmargs=-Xmx3g -XX:MaxMetaspaceSize=768m",
            ]
            report["phase"]="GRADLE_ASSEMBLE_RELEASE_ARM64"
            log_path=temp/"gradle_private.log"
            try:
                with log_path.open("w",encoding="utf-8") as log:
                    finished=subprocess.run(args_gradle,cwd=android,env=child,stdout=log,
                                            stderr=subprocess.STDOUT,timeout=9000,check=False)
                report["gradle_release_exit_code"]=finished.returncode
            except subprocess.TimeoutExpired:
                report["status"]="PRE170_GRADLE_TIMEOUT"
                return 1
            log=log_path.read_text(encoding="utf-8",errors="replace")[-1000000:]
            if requested_launcher:
                # PRE140: only numeric cache measurements enter the sanitized report.
                ccache_stats=subprocess.run([ccache_bin,"--show-stats"],env=child,
                            capture_output=True,text=True,check=False)
                raw=ccache_stats.stdout if ccache_stats.returncode==0 else ""
                numbers={}
                for name in ("Cacheable calls","Hits","Misses"):
                    found=re.search(r"^\s*"+re.escape(name)+r":\s*(\d+)",raw,re.MULTILINE)
                    numbers[name.lower().replace(" ","_")]=int(found.group(1)) if found else None
                report["pre140_sdk_only_ccache_numeric_stats"]=numbers
            report["gradle_failure_categories"]=classify_gradle_error(log)
            if finished.returncode!=0:
                report["gradle_failure_context_sanitized"]=safe_gradle_error_context(log,secret_props)
                report["status"]="PRE170_GRADLE_BUILD_FALHOU"
                return 1
            report["gradle_release_succeeded"]=True
            report["phase"]="SELECT_APK_AND_VERIFY"
            outputs=list((android/"app/build/outputs/apk/release").glob("*.apk"))
            if len(outputs)!=1:raise RuntimeError("Unexpected Gradle APK outputs")
            apk=outputs[0]
            report["apk_validation"]=verify_apk(apk,sdk,old_files,report)
            with zipfile.ZipFile(apk) as pre293_zip:
                pal_bytes=pre293_zip.read("lib/arm64-v8a/libmain.so")
            if b"NFSMW_PRE283_BMW_VTABLE" not in pal_bytes:
                raise ValueError("PRE293 previous BMW setup marker missing in signed libmain")
            if b"NFSMW_PRE292_BMW_MENU" not in pal_bytes:
                raise ValueError("PRE293 BMW main-menu marker missing in signed libmain")
            report["pre293_both_trace_markers_verified_in_signed_apk"]=True
            report["pre194_c3_marker_in_libmain_verified"]=report.get("pre194_c3_marker_verified_in_pal_libmain",False)
            if not report["pre194_c3_marker_in_libmain_verified"]:
                raise ValueError("PRE194 C3 marker linkage not proven")
            report["signed_apk_verified"]=True
            output.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(apk,output)
            if digest(output)!=report["apk_validation"]["apk_sha256"]:
                raise ValueError("Verified artifact copy digest mismatch")
            if args.upload:
                report["phase"]="UPLOAD_NEW_APK_TO_PRIVATE_DRIVE"
                report["drive_upload"]=upload_verified_apk(d,output)
                report["drive_upload_success"]=True
            report["status"]="PRE293_V39_BMW_MENU_DIAGNOSTIC_SIGNED_VERIFIED_ARTIFACT"
            report["phase"]="COMPLETE"
    except Exception as exc:
        report["error_type"]=type(exc).__name__
        safe_messages={
            "APK absent or unexpectedly small",
            "apksigner verify failed",
            "APK permanent signing certificate mismatch",
            "APK v2 permanent signing certificate mismatch",
            "APK signer CLI certificate disagrees with APK v2 DER certificate",
            "AAPT could not inspect APK",
            "APK applicationId/versionCode mismatch",
            "Generated APK ZIP CRC failed",
            "New APK missing required native library",
            "V31 changed required V30 PAL/USA content",
            "Rebuilt runtime is identical to V30: PRE128 linkage not proven",
        }
        if report.get("phase")=="SELECT_APK_AND_VERIFY" and str(exc) in safe_messages:
            report["validation_failure_code"]=str(exc)
        print("PRE170 stopped at",report["phase"],type(exc).__name__,
              "validation subphase",report.get("verification_subphase","UNKNOWN"))
    finally:
        report["utc"]=datetime.now(timezone.utc).isoformat()
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE170:",report["status"],"APK verified:",report["signed_apk_verified"],
              "Drive upload:",report["drive_upload_success"])
    return 0 if report["status"]=="PRE293_V39_BMW_MENU_DIAGNOSTIC_SIGNED_VERIFIED_ARTIFACT" else 1

if __name__=="__main__":
    raise SystemExit(main())
