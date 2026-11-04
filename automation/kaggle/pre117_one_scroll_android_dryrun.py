#!/usr/bin/env python3
"""PRE117: one-scroll-owner Android Settings layout dry-run.

Hash-gated PRE99 -> ephemeral restore -> two strictly bounded PRE92 source edits in /tmp,
then C++23 syntax check on exact NDK r28 ARM64 API26 target. No APK, signing,
active project change, or Drive upload. No device behavior can be proved by syntax alone.
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

BEGIN_ANCHOR = """  ImGui::PushID(selected_category_.c_str());
  ImGui::BeginChild("##cvars", ImVec2(0, -30.0f), false);"""
BEGIN_REPLACEMENT = """  ImGui::PushID(selected_category_.c_str());
  // PRE117: Android uses the root Settings window as the sole scroll owner.
  // Desktop keeps the original CVar child and its existing scroll behavior.
  if (!mobile_layout) {
    ImGui::BeginChild("##cvars", ImVec2(0, -30.0f), false);
  }"""
END_ANCHOR = """  ImGui::EndChild();
  ImGui::PopID();

  // Bottom bar: Save button."""
END_REPLACEMENT = """  if (!mobile_layout) {
    ImGui::EndChild();
  }
  ImGui::PopID();

  // Bottom bar: Save button."""

def propose(original:str)->tuple[str,str]:
    if original.count(BEGIN_ANCHOR)!=1 or original.count(END_ANCHOR)!=1:
        raise ValueError("PRE92 CVar child begin/end unique anchors missing")
    if "PRE117" in original:
        raise ValueError("Existing PRE117 patch detected: refusing duplicate")
    if "ImGui::SetScrollY(0.0f)" in original:
        raise ValueError("PRE115 scroll patch unexpectedly present in PRE92")
    modified=original.replace(BEGIN_ANCHOR,BEGIN_REPLACEMENT,1)
    modified=modified.replace(END_ANCHOR,END_REPLACEMENT,1)
    if modified.count('ImGui::BeginChild("##cvars"')!=1:
        raise ValueError("Unexpected CVar child begin count")
    if modified.count("  if (!mobile_layout) {\n    ImGui::EndChild();\n  }")!=1:
        raise ValueError("CVar EndChild must be desktop-only exactly once")
    if modified.count("ImGui::PushID(selected_category_.c_str());")!=original.count("ImGui::PushID(selected_category_.c_str());"):
        raise ValueError("ImGui PushID changed")
    if modified.count("ImGui::PopID();")!=original.count("ImGui::PopID();"):
        raise ValueError("ImGui PopID changed")
    if not all(original.count(call)==modified.count(call) for call in (
        "ImGui::PushStyleColor", "ImGui::PopStyleColor",
        "ImGui::PushStyleVar", "ImGui::PopStyleVar", "ImGui::End();",
    )):
        raise ValueError("Style stack or root window structure changed")
    if not all(token in modified for token in ("Settings##rex","##mw_header",
                                               "##search","CATEGORY","SAVE SETTINGS")):
        raise ValueError("Expected menu element unexpectedly removed")
    diff="".join(difflib.unified_diff(
        original.splitlines(keepends=True), modified.splitlines(keepends=True),
        fromfile="PRE92 settings_overlay.cpp (verified SHA-256)",
        tofile="PRE117 ONE-SCROLL ANDROID PROPOSAL — NOT APPLIED", n=4
    ))
    if not 15<=len(diff.splitlines())<=65:
        raise ValueError("PRE117 unexpected unified diff size")
    return modified,diff


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
        "etapa":"PRE117_DRYRUN_ONE_SCROLL_ANDROID",
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
            report["change"]="Android root scroll only; desktop CVar child scroll maintained"
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
                report["status"]="PRE117_PROPOSTA_NAO_COMPILOU"
                return 1
            report["status"]="PRE117_SCROLL_UNICO_ARM64_VALIDADO_NAO_APLICADO"
            report["phase"]="COMPLETE"
    except Exception as exc:
        report["error_type"]=type(exc).__name__
        print("PRE115 incomplete in phase:",report["phase"],type(exc).__name__)
    finally:
        report["recorded_utc"]=datetime.now(timezone.utc).isoformat()
        dst.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE117:",report["status"])
    return 0 if report["status"]=="PRE117_SCROLL_UNICO_ARM64_VALIDADO_NAO_APLICADO" else 1

if __name__=="__main__":
    raise SystemExit(main())
