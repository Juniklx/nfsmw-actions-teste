#!/usr/bin/env python3
"""PRE115: Android-only scroll-to-top-on-appearance diagnostic patch dry-run.

Hash-gated PRE99 -> ephemeral restore -> one small PRE92 source change in /tmp,
then C++23 syntax check on exact NDK r28 ARM64 API26 target. No APK, signing,
active project change, or Drive upload. This cannot prove cause on device.
"""
from __future__ import annotations
import argparse
import difflib
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
from pre112_cpp_syntax_isolated import compile_syntax,get_candidate_includes
from pre113b_android_arm64_syntax import locate_toolchain,NDK_REVISION,ANDROID_API

ANCHOR = """  if (!settings_visible) {
    ImGui::End();
    return;
  }

  // NFSMW PRE86:"""
REPLACEMENT = """  if (!settings_visible) {
    ImGui::End();
    return;
  }

  // PRE115 diagnostic proposal: reset only when the Android window appears.
  // Does not block user scrolling after the opening frame.
  if (mobile_layout && ImGui::IsWindowAppearing()) {
    ImGui::SetScrollY(0.0f);
  }

  // NFSMW PRE86:"""

def propose(original:str)->tuple[str,str]:
    if original.count(ANCHOR)!=1:
        raise ValueError("Expected PRE92 window visibility anchor missing/duplicated")
    if "ImGui::SetScrollY" in original or "ImGui::IsWindowAppearing" in original:
        raise ValueError("Scroll handling differs from verified PRE92")
    proposed=original.replace(ANCHOR,REPLACEMENT,1)
    if proposed.count("ImGui::SetScrollY(0.0f)")!=1:
        raise ValueError("Scroll reset not inserted once")
    if (original.count("ImGui::PushStyleColor")!=proposed.count("ImGui::PushStyleColor")
        or original.count("ImGui::PopStyleColor")!=proposed.count("ImGui::PopStyleColor")
        or original.count("ImGui::PushStyleVar")!=proposed.count("ImGui::PushStyleVar")
        or original.count("ImGui::PopStyleVar")!=proposed.count("ImGui::PopStyleVar")):
        raise ValueError("Unexpected ImGui style-stack change")
    diff="".join(difflib.unified_diff(original.splitlines(keepends=True),
         proposed.splitlines(keepends=True),
         fromfile="PRE92 settings_overlay.cpp SHA verified",
         tofile="PRE115 scroll reset proposal NOT APPLIED",n=4))
    if not 10<=len(diff.splitlines())<=25:
        raise ValueError("Unexpected diff scope")
    return proposed,diff


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--report",required=True)
    args=ap.parse_args()
    if not re.fullmatch(r"\d+",args.run_id):
        raise ValueError("Bad run ID")
    dst=Path(args.report)
    dst.parent.mkdir(parents=True,exist_ok=True)
    report={
        "etapa":"PRE115_DRYRUN_HEADER_SCROLL_ON_OPEN",
        "run_id":args.run_id,
        "status":"NAO_VALIDADO",
        "phase":"INITIAL",
        "ndk_revision":NDK_REVISION,
        "android_target":f"aarch64-linux-android{ANDROID_API}",
        "ndk_found":False,
        "backup_full_sha256_verified":False,
        "pre92_cpp_sha256_verified":False,
        "original_cpp_arm64_passed":False,
        "proposed_cpp_arm64_passed":False,
        "source_changed_only_in_temporary_runner":False,
        "active_workspace_modified":False,
        "apk_built":False,
        "signing_key_accessed":False,
        "device_rendering_tested":False,
        "cause_of_header_absence_confirmed":False,
    }
    try:
        report["phase"]="NDK_CHECK"
        _root,compiler=locate_toolchain()
        report["ndk_found"]=True
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre115_",dir="/tmp") as temp:
            root=Path(temp)
            if shutil.disk_usage(root).free<4*1024**3:
                raise RuntimeError("Insufficient runner disk")
            archive=root/"pre99.tar.gz"
            extract=root/"restore_test"
            extract.mkdir()
            report["phase"]="DOWNLOAD_PRE99"
            drive=drive_client()
            download(drive,archive)
            report["phase"]="VERIFY_TAR"
            sha,_md5,size=sha_file(archive)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 digest mismatch")
            report["backup_full_sha256_verified"]=True
            report["phase"]="EXTRACT_EPHEMERAL"
            restored=restore(archive,extract)
            report["restored_count"]=restored["members_restored"]
            source=extract/SOURCE_NAME
            original_bytes=source.read_bytes()
            if hashlib.sha256(original_bytes).hexdigest()!=SOURCE_SHA256:
                raise ValueError("PRE92 source hash mismatch")
            report["pre92_cpp_sha256_verified"]=True
            original=original_bytes.decode("utf-8")
            report["phase"]="GENERATE_ONE_CHANGE_DIFF"
            modified,diff=propose(original)
            report["source_sha256_before"]=SOURCE_SHA256
            report["proposed_source_sha256"]=hashlib.sha256(modified.encode()).hexdigest()
            report["diff_lines"]=len(diff.splitlines())
            report["unified_diff"]=diff
            report["change"]="Android-only, ImGui::IsWindowAppearing() then ImGui::SetScrollY(0.0f)"
            report["phase"]="COMPILE_ANDROID_ARM64_BASELINE"
            inc=get_candidate_includes(extract)
            base=compile_syntax(str(compiler),source,inc,timeout=150)
            report["original_cpp_arm64"]=base
            report["original_cpp_arm64_passed"]=base.get("passed") is True
            if not base.get("passed"):
                report["status"]="NDK_FONTE_BASE_NAO_COMPILOU"
                return 1
            report["phase"]="COMPILE_ANDROID_ARM64_PROPOSAL"
            source.write_text(modified,encoding="utf-8")
            report["source_changed_only_in_temporary_runner"]=True
            if hashlib.sha256(source.read_bytes()).hexdigest()!=report["proposed_source_sha256"]:
                raise ValueError("Ephemeral patched source mismatch")
            new=compile_syntax(str(compiler),source,inc,timeout=150)
            report["proposed_cpp_arm64"]=new
            report["proposed_cpp_arm64_passed"]=new.get("passed") is True
            if not new.get("passed"):
                report["status"]="PRE115_PROPOSTA_NAO_COMPILOU"
                return 1
            report["status"]="PRE115_PROPOSTA_SCROLL_ARM64_VALIDADA_NAO_APLICADA"
            report["phase"]="COMPLETE"
    except Exception as exc:
        report["error_type"]=type(exc).__name__
        print("PRE115 incomplete in phase:",report["phase"],type(exc).__name__)
    finally:
        report["recorded_utc"]=datetime.now(timezone.utc).isoformat()
        dst.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE115:",report["status"])
    return 0 if report["status"]=="PRE115_PROPOSTA_SCROLL_ARM64_VALIDADA_NAO_APLICADA" else 1

if __name__=="__main__":
    raise SystemExit(main())
