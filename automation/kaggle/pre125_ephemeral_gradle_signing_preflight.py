#!/usr/bin/env python3
"""PRE125 — ephemeral PRE99 restore, PRE117 exact application, permanent signing
certificate identity preflight and Gradle configuration probe only.

Runs on private GitHub Actions runner; uses temporary directories and deletes
signing bytes on completion. No APK build, no uploads, no Kaggle writes.
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
from datetime import datetime, timezone
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import SOURCE_NAME, SOURCE_SHA256, drive_client, download
from pre107_restore_isolated import restore
from pre117_one_scroll_android_dryrun import propose
from pre118_audit_build_tree import EXPECTED_PRE117_SHA

P12_DRIVE_ID="1Emu7CQ6T0_jME6LyMqyzDLSaypvTR2gM"
PROPERTIES_DRIVE_ID="1FLqPk_mxvlue2Tl7NPHpnnr7AScm5cFn"
P12_SHA="407815601cd41ab6a56a44d0d2eb130a9e0439bf00692d46d43cfba316b5334d"
CERT_SHA="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
GRADLE_SHA="ef570ba95703cb54df3c0e503fec6bce11aaa0f640e907208bdfb22bd8711230"
TARGET_CODE=27


def digest(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):h.update(chunk)
    return h.hexdigest()


def download_file(d, file_id:str, path:Path)->None:
    from googleapiclient.http import MediaIoBaseDownload
    media=d.files().get_media(fileId=file_id,supportsAllDrives=True)
    with path.open("xb") as f:
        dl=MediaIoBaseDownload(f,media,chunksize=4*1024*1024)
        done=False
        while not done:
            _status,done=dl.next_chunk(num_retries=4)


def parse_properties_safely(path:Path)->dict[str,str]:
    if path.stat().st_size>8192:raise ValueError("Unexpected signing properties size")
    raw=path.read_text(encoding="utf-8")
    result={}
    for line in raw.splitlines():
        s=line.strip()
        if not s or s.startswith(("#","!")):continue
        if "=" not in s:raise ValueError("Unsupported credential syntax")
        key,value=s.split("=",1)
        key=key.strip()
        if key not in ("storePassword","keyPassword","keyAlias") or key in result:
            raise ValueError("Unsupported or duplicate property")
        result[key]=value.strip()
    if set(result)!= {"storePassword","keyPassword","keyAlias"} or not all(result.values()):
        raise ValueError("Missing signing credential label")
    return result


def certificate_sha256(p12:Path, props:dict[str,str])->str:
    # Store password is passed via child process env, never CLI arguments.
    env=os.environ.copy()
    env["NFSMW_P12_STOREPASS_LOCAL"]=props["storePassword"]
    try:
        cmd=["keytool","-list","-v","-storetype","PKCS12",
             "-keystore",str(p12),"-alias",props["keyAlias"],
             "-storepass:env","NFSMW_P12_STOREPASS_LOCAL"]
        proc=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                            text=True,timeout=35,check=False)
    finally:
        env.pop("NFSMW_P12_STOREPASS_LOCAL",None)
    if proc.returncode!=0:raise RuntimeError("Keytool certificate read failed")
    fingerprints=re.findall(r"SHA256:\s*([0-9A-Fa-f:]{60,100})",proc.stdout)
    matches=[x.replace(":","").lower() for x in fingerprints]
    if not matches:raise ValueError("No certificate SHA256 parsed from keytool")
    return matches[0]


def classify_gradle_error(text:str)->dict[str,bool]:
    return {
        "gradle_build_successful":bool(re.search(r"\bBUILD SUCCESSFUL\b",text)),
        "gradle_build_failed":bool(re.search(r"\bBUILD FAILED\b",text)),
        "gradle_plugin_resolution_issue":bool(re.search(r"Plugin .+ was not found|plugin .*not found|Could not resolve.*plugin",text,re.I)),
        "gradle_sdk_issue":bool(re.search(r"SDK location not found|sdk.dir|Android SDK not found",text,re.I)),
        "gradle_ndk_issue":bool(re.search(r"NDK .*not found|ndkVersion|No version of NDK",text,re.I)),
        "gradle_cmake_issue":bool(re.search(r"CMake .*not found|cmake.dir|Could not find.*CMake",text,re.I)),
        "gradle_signing_config_issue":bool(re.search(r"Backup da assinatura NFSMW ausente|storeFile|signingConfig|nfsmwPermanente",text,re.I)),
        "gradle_network_issue":bool(re.search(r"Temporary failure in name resolution|ConnectException|Read timed out|Connection refused",text,re.I)),
        "gradle_kotlin_script_issue":bool(re.search(r"Script compilation errors|build.gradle.kts.*line|Unresolved reference",text,re.I)),
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--report",required=True)
    a=ap.parse_args()
    if not re.fullmatch(r"\d+",a.run_id):raise ValueError("Invalid run id")
    report_path=Path(a.report)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    r={
        "etapa":"PRE125_RESTORE_PATCH_CERT_GRADLE_PREFLIGHT",
        "run_id":a.run_id,"phase":"INITIAL","status":"NAO_VALIDADO",
        "pre99_archive_integrity_verified":False,
        "ephemeral_restore_completed":False,
        "pre117_applied_only_in_ephemeral_runner":False,
        "pre117_candidate_sha256_verified":False,
        "signing_keystore_sha256_verified":False,
        "signing_certificate_sha256_expected":False,
        "credentials_not_logged":True,
        "gradle_help_succeeded":False,
        "version_code_env_override":TARGET_CODE,
        "original_kaggle_workspace_modified":False,
        "google_drive_modified":False,
        "existing_apks_modified":False,
        "signed_apk_built":False,
    }
    try:
        root=Path(os.environ.get("RUNNER_TEMP","/tmp"))
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre125_",dir=root) as tmp:
            base=Path(tmp)
            signing=base/"signing"
            signing.mkdir(mode=0o700)
            work=base/"restored"
            work.mkdir()
            if shutil.disk_usage(base).free<5*1024**3:
                raise RuntimeError("Insufficient ephemeral runner disk")
            r["phase"]="AUTH_DOWNLOAD_SIGNING_EPHEMERAL"
            d=drive_client()
            key=signing/"NFSMW_ASSINATURA_PERMANENTE.p12"
            props_path=signing/"NFSMW_ASSINATURA_CREDENCIAIS.properties"
            download_file(d,P12_DRIVE_ID,key)
            download_file(d,PROPERTIES_DRIVE_ID,props_path)
            key.chmod(0o600)
            props_path.chmod(0o600)
            if digest(key)!=P12_SHA:raise ValueError("Permanent keystore SHA mismatch")
            r["signing_keystore_sha256_verified"]=True
            props=parse_properties_safely(props_path)
            certificate=certificate_sha256(key,props)
            if certificate!=CERT_SHA:raise ValueError("Permanent signing certificate differs")
            r["signing_certificate_sha256_expected"]=True
            # The original Drive version counter is untouched. Gradle's env override
            # supplies code 27; this temp file merely satisfies required existence.
            (signing/"NFSMW_PROXIMO_VERSION_CODE.txt").write_text(str(TARGET_CODE)+"\n")
            r["phase"]="DOWNLOAD_PRE99"
            tar=base/"pre99.tar.gz"
            download(d,tar)
            sha,_,size=sha_file(tar)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 archive drift")
            r["pre99_archive_integrity_verified"]=True
            r["phase"]="EXTRACT_PRE99_EPHEMERAL"
            stats=restore(tar,work)
            r["ephemeral_restore_completed"]=True
            r["restored_members"]=stats["members_restored"]
            source=work/SOURCE_NAME
            if digest(source)!=SOURCE_SHA256:raise ValueError("PRE92 Settings file hash mismatch")
            gradle=work/"workspace/android/app/build.gradle.kts"
            if digest(gradle)!=GRADLE_SHA:raise ValueError("PRE99 Gradle hash mismatch")
            r["phase"]="APPLY_PRE117_TO_EPHEMERAL_COPY"
            patched,_=propose(source.read_text(encoding="utf-8"))
            source.write_text(patched,encoding="utf-8")
            r["pre117_applied_only_in_ephemeral_runner"]=True
            if digest(source)!=EXPECTED_PRE117_SHA:raise ValueError("PRE117 target hash mismatch")
            r["pre117_candidate_sha256_verified"]=True
            r["phase"]="GRADLE_CONFIG_HELP"
            sdk=Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or "/usr/local/lib/android/sdk")
            if not sdk.is_dir():raise FileNotFoundError("Android SDK not available")
            project=work/"workspace"
            android=project/"android"
            local=android/"local.properties"
            local.write_text("sdk.dir="+str(sdk.resolve()).replace("\\","\\\\").replace(":","\\:")+"\n")
            child_env=os.environ.copy()
            child_env["NFSMW_SIGNING_DIR"]=str(signing)
            child_env["NFSMW_VERSION_CODE"]=str(TARGET_CODE)
            child_env["ANDROID_HOME"]=str(sdk)
            child_env["ANDROID_SDK_ROOT"]=str(sdk)
            cmd=["bash","gradlew","help","--no-daemon","--console=plain",
                 "-Pnfsmw.motor=nativo","-Pnfsmw.edicion=pal_es",
                 "-Pnfsmw.sdk="+str(project/"nativo/sdk")]
            try:
                done=subprocess.run(cmd,cwd=android,env=child_env,stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,text=True,errors="replace",timeout=1050,check=False)
                out=done.stdout[-200000:]
                r["gradle_exit_code"]=done.returncode
                r["gradle_error_flags"]=classify_gradle_error(out)
                r["gradle_help_succeeded"]=done.returncode==0 and r["gradle_error_flags"]["gradle_build_successful"]
                if not r["gradle_help_succeeded"]:
                    r["status"]="PRE125_GRADLE_CONFIG_BLOQUEADA"
                    return 1
            except subprocess.TimeoutExpired:
                r["status"]="PRE125_GRADLE_CONFIG_TIMEOUT"
                return 1
            r["status"]="PRE125_CERTIFICADO_E_GRADLE_CONFIG_VALIDOS"
            r["phase"]="COMPLETE"
    except Exception as exc:
        r["error_type"]=type(exc).__name__
        print("PRE125 stopped at:",r["phase"],type(exc).__name__)
    finally:
        r["utc"]=datetime.now(timezone.utc).isoformat()
        report_path.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE125:",r["status"],"certificate verified:",r["signing_certificate_sha256_expected"])
    return 0 if r["status"]=="PRE125_CERTIFICADO_E_GRADLE_CONFIG_VALIDOS" else 1

if __name__=="__main__":
    raise SystemExit(main())
