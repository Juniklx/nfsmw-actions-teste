#!/usr/bin/env python3
"""PRE249: inspect real pinned Rex SDK logging ABI and compile tiny callbacks.

No game build, no APK, no credentials for signing, and no persistent game writes.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client, download
from pre107_restore_isolated import restore
from pre246_passive_money_probe_patch import CPP_TEXT as MONEY
from pre247_pal_meter_passive_probe_patch import CPP_TEXT as METERS

OUT=Path("/tmp/nfsmw-pre249/NFSMW_PRE249_REAL_REX_LOGGER_HEADER_PROBE.json")
HEADER="nativo/sdk/include/rex/logging/macros.h"

def main()->int:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE249_REX_LOGGING_HEADER_HOST_SYNTAX",
            "status":"FAILED","phase":"START",
            "game_compiled":False,"apk_built":False,
            "signer_accessed":False,"saves_changed":False,
            "cheats_enabled":False,"drive_files_modified":False}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre249_") as t:
            root=Path(t)
            bundle=root/"pre99.tar.gz"
            report["phase"]="DOWNLOAD_AUTHENTICATED_PRE99"
            download(drive_client(),bundle)
            digest,_,size=sha_file(bundle)
            if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE249: PRE99 hash mismatch")
            report["pre99_authenticated"]=True
            report["phase"]="RESTORE_EPHEMERAL_REFERENCE_SDK"
            restored=root/"isolate"
            restored.mkdir()
            restore(bundle,restored)
            work=restored/"workspace"
            header=work/HEADER
            if not header.is_file():
                raise ValueError("PRE249: Rex logging macro header missing")
            text=header.read_text(encoding="utf-8")
            report["real_header_sha256"]=hashlib.sha256(header.read_bytes()).hexdigest()
            report["real_header_path"]=HEADER
            matches=[(i+1,line.strip()[:220]) for i,line in enumerate(text.splitlines())
                    if "REXLOG_INFO" in line]
            report["rexlog_info_matches"]=[{"line":i,"text":s} for i,s in matches[:12]]
            report["header_mentions_rexlog_info"]=bool(matches)
            if not matches:
                raise ValueError("PRE249: REXLOG_INFO absent from real SDK header")
            report["phase"]="REAL_SDK_HOST_CPP_SYNTAX_ONLY"
            local=root/"isolated"
            local.mkdir()
            (local/"money.cpp").write_text(MONEY,encoding="utf-8")
            (local/"meters.cpp").write_text(METERS,encoding="utf-8")
            cmd=["g++","-std=c++20","-fsyntax-only","-Wall","-Wextra",
                 "-I",str(work/"nativo/sdk/include"),
                 str(local/"money.cpp"),str(local/"meters.cpp")]
            res=subprocess.run(cmd,capture_output=True,text=True,timeout=35)
            report["real_sdk_host_syntax_ok"]=res.returncode==0
            report["host_compiler_rc"]=res.returncode
            if res.returncode:
                report["safe_compiler_error_tail"]=(res.stderr or "")[-1300:]
                report["status"]="NEEDS_TOOLCHAIN_OR_LOGGING_REVIEW"
            else:
                report["status"]="AUDIT_OK"
            report["limits"]=[
                "A host compiler syntax check is not an Android NDK compile or link.",
                "The trace modules do not modify the guest stores or read guest memory.",
                "Even AUDIT_OK does not activate any cheat or prove gameplay behavior.",
            ]
            report["phase"]="COMPLETE"
    except Exception as e:
        report["error_type"]=type(e).__name__
        report["failed_phase"]=report["phase"]
        print("PRE249_ERROR",type(e).__name__,report["phase"])
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE249_STATUS",report["status"],"HOST_REAL_REX_SYNTAX",report.get("real_sdk_host_syntax_ok"))
    return 0 if report["status"] in ("AUDIT_OK","NEEDS_TOOLCHAIN_OR_LOGGING_REVIEW") else 1
if __name__=="__main__":sys.exit(main())
