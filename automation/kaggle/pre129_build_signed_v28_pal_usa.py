#!/usr/bin/env python3
"""PRE129: Rebuild NFSMW V27 PAL+USA with PRE117 in a private, ephemeral runner.

Strict gates: PRE99 archive SHA, PRE92 source SHA, PRE117 target SHA,
original V27 APK SHA, USA library + shaders unchanged, permanent P12 SHA,
certificate SHA, versionCode=27 and Android package name. Only after all
gates pass may the new signed APK be uploaded as a new Drive file.

No original Kaggle session, prior APK, signing backup or version counter is
modified. Signing files remain in runner-local temporary storage only.
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
from pre118_audit_build_tree import EXPECTED_PRE117_SHA
from pre127_apk_v2_certificate_audit import apk_v2_cert_sha256
from pre125_ephemeral_gradle_signing_preflight import (
    P12_DRIVE_ID,PROPERTIES_DRIVE_ID,P12_SHA,CERT_SHA,GRADLE_SHA,
    download_file,digest,parse_properties_safely,certificate_sha256,classify_gradle_error,
)

V27_ID="1ByL6oJzu1RAcPY7OaeNk99nRq3LtgevZ"
V27_SHA="2f9e965c21c6c648f31ffe2e61f26c114546310327c89e6aee17285dd4261e65"
V27_BYTES=47068621
VERSION_CODE=28
EXPECTED_PRE128_SHA="cf3cc930904303ec3b4a081f9987a1ced478697678fcab90b056f07ba0b4957d"
EXPECTED_PACKAGE="io.github.nfsmwrecomp"
DEST_FOLDER="1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh"
APK_NAME="NFSMW_V28_PAL_USA_PRE128_TOUCH_TEMA_EXPERIMENTAL.apk"
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
V27_RUNTIME_SHA="06ec5314433b299d56f63e546f3dd4d8c0d2684ac0e60b34a54dac2864c2d04d"


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


def verified_v27(apk:Path)->dict[str,bytes]:
    if apk.stat().st_size!=V27_BYTES or digest(apk)!=V27_SHA:
        raise ValueError("V27 baseline APK changed")
    if apk_v2_cert_sha256(apk)!=CERT_SHA:
        raise ValueError("Original V27 has unexpected APK v2 signer certificate")
    result={}
    with zipfile.ZipFile(apk,"r") as z:
        if z.testzip() is not None:raise ValueError("V27 ZIP CRC failed")
        for path,expected_sha in PRESERVE.items():
            data=z.read(path)
            if sha_bytes(data)!=expected_sha:raise ValueError("V27 asset hash mismatch")
            result[path]=data
        result["runtime"]=z.read("lib/arm64-v8a/librexruntime.so")
        if sha_bytes(result["runtime"])!=V27_RUNTIME_SHA:raise ValueError("V27 runtime hash changed")
    return result


def prepare_usa_edition(root:Path,bundle:Path,v27:dict[str,bytes])->dict:
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
        if digest(root/suffix)!=PRESERVE[name]:raise ValueError("PAL shader differs from V27")
    meta=json.loads((root/"nativo/out/usa/edicion.json").read_text(encoding="utf-8"))
    if not isinstance(meta,dict) or str(meta.get("id","")).lower()!="usa":
        raise ValueError("USA edition metadata id mismatch")
    # Preserve USA game library and assets from the verified V27 APK.
    # No generated game files are uploaded to GitHub source control.
    dll=bundle/"jniLibs/arm64-v8a/libmain_usa.so"
    dll.parent.mkdir(parents=True,exist_ok=True)
    dll.write_bytes(v27["lib/arm64-v8a/libmain_usa.so"])
    for name in (
        "assets/nativo/usa/nfsmw_shaders.nfsp",
        "assets/nativo/usa/nfsmw_shaders_gles.nfsp",
    ):
        dest=bundle/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(v27[name])
    (bundle/"ediciones.json").write_text(json.dumps([meta],ensure_ascii=False)+"\n",encoding="utf-8")
    return {"usa_edition_id_verified":True,
            "usa_library_preserved":True,
            "usa_shader_assets_preserved":True,
            "pal_shader_assets_match_v27":True}


def verify_apk(apk:Path,sdk:Path,v27:dict[str,bytes],progress:dict)->dict:
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
                raise ValueError("V28 changed required V27 PAL/USA content")
            kept[name]=True
        progress["verification_subphase"]="APK_RUNTIME_LINKAGE_DIFFERENCE"
        runtime=sha_bytes(z.read("lib/arm64-v8a/librexruntime.so"))
        if runtime==V27_RUNTIME_SHA:raise ValueError("Rebuilt runtime is identical to V27: PRE128 linkage not proven")
        progress["verification_subphase"]="APK_ALL_GATES_PASSED"
        return {
            "signed_certificate_sha256_match":True,
            "signed_schemes_verified":True,
            "package_id":match.group(1),
            "version_code":int(match.group(2)),
            "android_arm64_required_libraries_present":True,
            "required_arm64_library_count":len(REQUIRED_LIBS),
            "pal_usa_shaders_preserved":True,
            "usa_main_library_unchanged_from_v27":True,
            "runtime_changed_from_v27":True,
            "new_librexruntime_sha256":runtime,
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
        "etapa":"PRE129_BUILD_V28_PAL_USA_PRE117_PRE128",
        "run_id":args.run_id,
        "phase":"INITIAL","status":"NAO_VALIDADO",
        "target_version_code":VERSION_CODE,
        "verified_source_pre99":False,
        "pre117_exact_patch_applied_in_runner":False,
        "pre128_exact_patch_applied_in_runner":False,
        "phone_touch_scroll_tested":False,
        "phone_visual_theme_tested":False,
        "permanent_certificate_verified":False,
        "v27_baseline_verified":False,
        "gradle_release_succeeded":False,
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
        sdk=sdk_root()
        if not (sdk/"ndk/28.2.13676358/source.properties").is_file():
            raise FileNotFoundError("NDK r28.2 not installed")
        if not (sdk/"cmake/3.31.6").is_dir():
            raise FileNotFoundError("CMake 3.31.6 not installed")
        base=Path(os.environ.get("RUNNER_TEMP","/tmp"))
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre129_",dir=base) as tmp:
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
            report["phase"]="DOWNLOAD_V27_BASELINE"
            old=temp/"v27.apk"
            download_file(d,V27_ID,old)
            old_files=verified_v27(old)
            report["v27_baseline_verified"]=True
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
            proposed_v28=propose_pre128(modified)
            src.write_text(proposed_v28,encoding="utf-8")
            if digest(src)!=EXPECTED_PRE128_SHA:raise ValueError("PRE128 patched source SHA mismatch")
            report["pre128_exact_patch_applied_in_runner"]=True
            report["source_pre128_sha256"]=EXPECTED_PRE128_SHA
            report["phase"]="STAGE_VERIFIED_USA_FROM_V27"
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
            child["GRADLE_USER_HOME"]=str(temp/"gradle_cache")
            args_gradle=[
                "bash","gradlew","assembleRelease","--no-daemon","--console=plain","--max-workers=2",
                "-Pnfsmw.motor=nativo","-Pnfsmw.edicion=pal_es",
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
                report["status"]="PRE129_GRADLE_TIMEOUT"
                return 1
            log=log_path.read_text(encoding="utf-8",errors="replace")[-1000000:]
            report["gradle_failure_categories"]=classify_gradle_error(log)
            if finished.returncode!=0:
                report["gradle_failure_context_sanitized"]=safe_gradle_error_context(log,secret_props)
                report["status"]="PRE129_GRADLE_BUILD_FALHOU"
                return 1
            report["gradle_release_succeeded"]=True
            report["phase"]="SELECT_APK_AND_VERIFY"
            outputs=list((android/"app/build/outputs/apk/release").glob("*.apk"))
            if len(outputs)!=1:raise RuntimeError("Unexpected Gradle APK outputs")
            apk=outputs[0]
            report["apk_validation"]=verify_apk(apk,sdk,old_files,report)
            report["signed_apk_verified"]=True
            output.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(apk,output)
            if digest(output)!=report["apk_validation"]["apk_sha256"]:
                raise ValueError("Verified artifact copy digest mismatch")
            if args.upload:
                report["phase"]="UPLOAD_NEW_APK_TO_PRIVATE_DRIVE"
                report["drive_upload"]=upload_verified_apk(d,output)
                report["drive_upload_success"]=True
            report["status"]="PRE129_V28_PAL_USA_ASSINADA_E_VERIFICADA_EM_ARTIFACT"
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
            "V28 changed required V27 PAL/USA content",
            "Rebuilt runtime is identical to V27: PRE128 linkage not proven",
        }
        if report.get("phase")=="SELECT_APK_AND_VERIFY" and str(exc) in safe_messages:
            report["validation_failure_code"]=str(exc)
        print("PRE129 stopped at",report["phase"],type(exc).__name__,
              "validation subphase",report.get("verification_subphase","UNKNOWN"))
    finally:
        report["utc"]=datetime.now(timezone.utc).isoformat()
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE129:",report["status"],"APK verified:",report["signed_apk_verified"],
              "Drive upload:",report["drive_upload_success"])
    return 0 if report["status"]=="PRE129_V28_PAL_USA_ASSINADA_E_VERIFICADA_EM_ARTIFACT" else 1

if __name__=="__main__":
    raise SystemExit(main())
