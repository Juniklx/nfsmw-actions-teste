#!/usr/bin/env python3
"""PRE124: inspect PAL/USA native staging and signing backup metadata.

Read-only backup plus metadata lookup only. No private signing bytes, no
source extraction to persistent storage, no APK, no Kaggle run.
"""
from __future__ import annotations
import argparse
import json
import re
import tarfile
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, EXPECTED_ENTRIES, sha_file
from pre105_read_settings_source import drive_client, download

P = "workspace/"
N = P + "nativo/"
FILES = {
    "pal_sources_cmake": N+"app/generated/default/sources.cmake",
    "usa_sources_cmake": N+"app_usa/generated/default/sources.cmake",
    "pal_shader_vulkan": N+"out/nfsmw_shaders.nfsp",
    "pal_shader_gles": N+"out/nfsmw_shaders_gles.nfsp",
    "usa_shader_vulkan": N+"out/usa/nfsmw_shaders.nfsp",
    "usa_shader_gles": N+"out/usa/nfsmw_shaders_gles.nfsp",
    "pal_edition_json": N+"out/edicion.json",
    "usa_edition_json": N+"out/usa/edicion.json",
    "pal_mobile_toml": N+"app/nfsmw_movil.toml",
    "usa_mobile_toml": N+"app_usa/nfsmw_movil.toml",
    "android_gradlew": P+"android/gradlew",
    "gradle_wrapper": P+"android/gradle/wrapper/gradle-wrapper.jar",
}
SIGNING_FILES = {
    "p12": ("1Emu7CQ6T0_jME6LyMqyzDLSaypvTR2gM","NFSMW_ASSINATURA_PERMANENTE.p12"),
    "properties": ("1FLqPk_mxvlue2Tl7NPHpnnr7AScm5cFn","NFSMW_ASSINATURA_CREDENCIAIS.properties"),
    "version_file": ("1kb76kopySxud66_1uvEvXaMFQP6o90s6","NFSMW_PROXIMO_VERSION_CODE.txt"),
    "public_info": ("1GGe3WuWluycrBAtFBXNTM2PCmzUpQ0ov","NFSMW_ASSINATURA_PERMANENTE_INFO.json"),
}

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--report",required=True)
    args=ap.parse_args()
    if not re.fullmatch(r"\d+",args.run_id):raise ValueError("Bad run id")
    dst=Path(args.report);dst.parent.mkdir(parents=True,exist_ok=True)
    r={
        "etapa":"PRE124_NATIVO_PAL_USA_AND_SIGNING_METADATA",
        "run_id":args.run_id,
        "phase":"START","status":"NAO_VALIDADO",
        "archive_verified":False,
        "signing_metadata_only":True,
        "signing_bytes_read":False,
        "credentials_read":False,
        "signed_apk_built":False,
        "original_kaggle_modified":False,
        "google_drive_modified":False,
        "patch_applied":False,
    }
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre124_") as tmp:
            archive=Path(tmp)/"pre99.tar.gz"
            r["phase"]="DRIVE_OAUTH"
            d=drive_client()
            r["phase"]="METADATA_SIGNING_BACKUP"
            matches={}
            for k,(file_id,expected) in SIGNING_FILES.items():
                md=d.files().get(fileId=file_id,fields="id,name,size,mimeType,trashed",supportsAllDrives=True).execute()
                matches[k]=bool(md.get("name")==expected and not md.get("trashed") and int(md.get("size",0))>0)
            r["signing_metadata_matches_names"]=matches
            if not all(matches.values()):raise ValueError("Signing metadata missing or mismatched")
            r["phase"]="DOWNLOAD_PRE99"
            download(d,archive)
            r["phase"]="VERIFY_SHA_PRE99"
            sha,_,sz=sha_file(archive)
            if sha!=EXPECTED_SHA256 or sz!=EXPECTED_BYTES:raise ValueError("PRE99 integrity failed")
            r["archive_verified"]=True
            r["phase"]="SCAN_NATIVE_STAGING"
            with tarfile.open(archive,"r:gz",errorlevel=2) as f:
                members=f.getmembers()
                if len(members)!=EXPECTED_ENTRIES:raise ValueError("PRE99 member count mismatch")
                names={m.name for m in members}
                if len(names)!=len(members):raise ValueError("PRE99 duplicate member")
                r["native_stage_presence"]={k:v in names for k,v in FILES.items()}
                r["native_stage_counts"]={
                    "pal_generated_cpp":sum(x.startswith(N+"app/generated/") and x.endswith(".cpp") for x in names),
                    "usa_generated_cpp":sum(x.startswith(N+"app_usa/generated/") and x.endswith(".cpp") for x in names),
                    "pal_app_cpp":sum(x.startswith(N+"app/") and x.endswith(".cpp") for x in names),
                    "usa_app_cpp":sum(x.startswith(N+"app_usa/") and x.endswith(".cpp") for x in names),
                    "pal_out_files":sum(x.startswith(N+"out/") and not x.startswith(N+"out/usa/") for x in names),
                    "usa_out_files":sum(x.startswith(N+"out/usa/") for x in names),
                    "edition_bundle_candidates":sum("ediciones" in x.lower() and x.endswith(".json") for x in names),
                    "native_prebuilt_arm64_libraries":sum(x.startswith(N) and "arm64-v8a" in x and x.endswith(".so") for x in names),
                    "native_generated_cmake_any":sum(x.startswith(N) and x.endswith("sources.cmake") for x in names),
                }
                r["pal_native_game_stage_ready"] = all(r["native_stage_presence"][key] for key in
                    ("pal_sources_cmake","pal_shader_vulkan","pal_mobile_toml"))
                r["usa_native_game_stage_ready"] = all(r["native_stage_presence"][key] for key in
                    ("usa_sources_cmake","usa_shader_vulkan"))
                r["native_mode_can_have_game"] = r["pal_native_game_stage_ready"] or r["usa_native_game_stage_ready"]
                r["v26_pal_usa_dual_edition_build_directly_proven"]=False
                r["versionCode_target"]=27
                r["versionCode_source_should_be_env_override"]=True
            r["status"]="PRE124_STAGING_E_ASSINATURA_METADATA_AUDITADOS"
            r["phase"]="COMPLETE"
    except Exception as exc:
        r["error_type"]=type(exc).__name__
        print("PRE124 failed phase",r["phase"],type(exc).__name__)
    finally:
        r["utc"]=datetime.now(timezone.utc).isoformat()
        dst.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE124:",r["status"])
    return 0 if r["status"]=="PRE124_STAGING_E_ASSINATURA_METADATA_AUDITADOS" else 1

if __name__=="__main__":
    raise SystemExit(main())
