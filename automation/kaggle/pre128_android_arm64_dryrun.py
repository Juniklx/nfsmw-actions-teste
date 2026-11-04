#!/usr/bin/env python3
"""PRE128: restore PRE99 in temporary runner, apply PRE117 then PRE128, ARM64 syntax."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download,SOURCE_NAME,SOURCE_SHA256
from pre107_restore_isolated import restore
from pre117_one_scroll_android_dryrun import propose as propose_pre117
from pre128_android_touch_scroll_visual_patch import propose as propose_pre128
from pre112_cpp_syntax_isolated import get_candidate_includes,compile_syntax
from pre113b_android_arm64_syntax import locate_toolchain,NDK_REVISION,ANDROID_API
from pre118_audit_build_tree import EXPECTED_PRE117_SHA

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    p.add_argument("--report",required=True)
    a=p.parse_args()
    if not re.fullmatch(r"\d+",a.run_id):
        raise ValueError("Invalid run id")
    report_path=Path(a.report)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    status={"stage":"PRE128_ARM64_EXPERIMENTAL_TOUCH_AND_THEME",
            "run_id":a.run_id,"phase":"START","status":"NOT_VERIFIED",
            "pre99_sha256_verified":False,"pre92_settings_source_sha256_verified":False,
            "pre117_sha256_verified":False,"pre128_applied_only_ephemerally":False,
            "arm64_syntax_passed":False,
            "source_persistent_modified":False,"drive_modified":False,
            "permanent_signing_key_accessed":False,"apk_built":False,
            "phone_touch_tested":False,
            "goals":["touch drag only on passive content","root-only scrollbar",
                     "remove legacy titlebar","yellow scrollbar + dark background",
                     "desktop settings unchanged"]}
    try:
        status["phase"]="LOCATE_NDK"
        _,compiler=locate_toolchain()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre128_",dir="/tmp") as tmp:
            root=Path(tmp)
            if shutil.disk_usage(root).free<4*1024**3:
                raise RuntimeError("Runner disk below required safety margin")
            archive=root/"pre99.tar.gz"
            staging=root/"staging"
            staging.mkdir()
            status["phase"]="DOWNLOAD_PRE99"
            drive=drive_client()
            download(drive,archive)
            status["phase"]="HASH_PRE99"
            archive_sha,_md5,archive_size=sha_file(archive)
            if archive_sha!=EXPECTED_SHA256 or archive_size!=EXPECTED_BYTES:
                raise ValueError("PRE99 integrity mismatch")
            status["pre99_sha256_verified"]=True
            status["phase"]="RESTORE_EPHEMERAL"
            restored=restore(archive,staging)
            status["members_restored"]=restored["members_restored"]
            cpp=staging/SOURCE_NAME
            before=cpp.read_bytes()
            if hashlib.sha256(before).hexdigest()!=SOURCE_SHA256:
                raise ValueError("Original PRE92 source hash mismatch")
            status["pre92_settings_source_sha256_verified"]=True
            status["phase"]="APPLY_EXACT_PRE117_IN_MEMORY"
            pre117,_diff=propose_pre117(before.decode("utf-8"))
            if hashlib.sha256(pre117.encode("utf-8")).hexdigest()!=EXPECTED_PRE117_SHA:
                raise ValueError("PRE117 source hash mismatch")
            status["pre117_sha256_verified"]=True
            status["phase"]="PROPOSE_PRE128_IN_MEMORY"
            proposed=propose_pre128(pre117)
            status["pre128_source_sha256"]=hashlib.sha256(proposed.encode("utf-8")).hexdigest()
            status["pre128_applied_only_ephemerally"]=True
            cpp.write_text(proposed,encoding="utf-8")
            status["phase"]="COMPILE_ANDROID_ARM64"
            status["clang_android_api"]=ANDROID_API
            status["ndk_revision"]=NDK_REVISION
            inc=get_candidate_includes(staging)
            check=compile_syntax(str(compiler),cpp,inc,timeout=240)
            status["arm64_syntax_result"]=check
            status["arm64_syntax_passed"]=check.get("passed",False) is True
            if not status["arm64_syntax_passed"]:
                status["status"]="PRE128_ANDROID_ARM64_SYNTAX_FAILED"
            else:
                status["status"]="PRE128_ANDROID_ARM64_SYNTAX_PASSED_NOT_APPLIED_TO_RELEASE"
                status["phase"]="COMPLETE"
    except Exception as exc:
        status["error_type"]=type(exc).__name__
    finally:
        status["recorded_utc"]=datetime.now(timezone.utc).isoformat()
        report_path.write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE128:",status["status"],"phase:",status["phase"])
    return 0 if status["status"]=="PRE128_ANDROID_ARM64_SYNTAX_PASSED_NOT_APPLIED_TO_RELEASE" else 1

if __name__=="__main__":
    raise SystemExit(main())
