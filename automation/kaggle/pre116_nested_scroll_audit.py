#!/usr/bin/env python3
"""PRE116: read-only SHA-gated audit of Settings nested scrolling and footer.

Reads exact original PRE92 C++ from full SHA256-verified PRE99 archive.
Only emits small source excerpts and structural counts, never game binaries.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download, SOURCE_NAME, SOURCE_SHA256

def excerpt(source: str, begin: int, end: int) -> list[dict]:
    lines=source.splitlines()
    return [{"line": i+1, "text": lines[i][:300]} for i in range(begin-1,min(end,len(lines)))]

def scan(source:str)->dict:
    expected={
        "root_begin":'ImGui::Begin(\n      "Settings##rex"',
        "root_flags":"ImGuiWindowFlags_NoResize);",
        "mobile_branch":"const bool mobile_layout = true;",
        "category_mobile":'ImGui::TextDisabled("CATEGORY");',
        "desktop_cats":'ImGui::BeginChild("##cats", ImVec2(panel_width, -30.0f), true);',
        "list_begin":'ImGui::BeginChild("##cvars", ImVec2(0, -30.0f), false);',
        "save_button":'mobile_layout ? ImVec2(240.0f, 52.0f) : ImVec2(0, 0)',
        "list_end_marker":"  ImGui::EndChild();\n  ImGui::PopID();\n\n  // Bottom bar: Save button.",
        "root_end":"  ImGui::End();",
    }
    markers={}
    for k,v in expected.items():
        matches=list(re.finditer(re.escape(v),source))
        if len(matches)!=1:
            raise ValueError("PRE92 unique anchor missing or repeated: "+k)
        markers[k]={"line":source.count("\n",0,matches[0].start())+1}
    windows=source.splitlines()
    root_line=markers["root_begin"]["line"]
    list_line=markers["list_begin"]["line"]
    footer_line=markers["save_button"]["line"]
    root_flags="".join(windows[root_line-1:root_line+5])
    if "ImGuiWindowFlags_NoScrollbar" in root_flags or "NoScrollWithMouse" in root_flags:
        raise ValueError("Root already configured as non-scrollable; expected PRE92")
    if not (markers["category_mobile"]["line"]<list_line<footer_line):
        raise ValueError("Unexpected list/footer source order")
    return {
        "anchor_lines":markers,
        "root_window_has_explicit_NoScrollbar":False,
        "root_window_has_explicit_NoScrollWithMouse":False,
        "mobile_also_enters_cvars_begin_child":True,
        "cvars_child_negative_height_pixels_logical":-30,
        "android_save_button_logical_height":52,
        "negative_30_reserve_smaller_than_save_button":True,
        "other_layout_overhead_measured":False,
        "nested_scroll_observed_by_user":True,
        "root_window_excerpt":excerpt(source,225,280),
        "category_and_child_excerpt":excerpt(source,375,515),
        "footer_and_end_excerpt":excerpt(source,715,765),
        "interpretation":[
            "PRE92 root window does not disable its own scrolling.",
            "PRE92 contains a CVar child with negative trailing reserve of 30 logical ImGui units.",
            "Android save button is 52 logical units high, with additional footer content.",
            "This is consistent with user-observed double scrolling in regular phone mode.",
            "Actual runtime scrolling, geometry and DeX-dependent ImGui display scaling were not measured.",
            "Suggested safest first change: one scroll owner on Android root and no CVar nested child; desktop preserved.",
        ],
        "patch_applied":False,
        "apk_built":False,
    }

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    p.add_argument("--report",required=True)
    args=p.parse_args()
    if not re.fullmatch(r"\d+",args.run_id):raise ValueError("Bad run ID")
    target=Path(args.report)
    target.parent.mkdir(parents=True,exist_ok=True)
    report={
        "etapa":"PRE116_MOBILE_NESTED_SCROLL_ROOT_CAUSE",
        "run_id":args.run_id,
        "status":"NAO_VALIDADO",
        "phase":"INITIAL",
        "pre99_archive_sha256_verified":False,
        "pre92_source_sha256_verified":False,
        "workspace_modified":False,
        "drive_modified":False,
        "apk_compiled":False,
        "signing_key_accessed":False,
    }
    try:
        report["phase"]="GOOGLE_AUTH"
        drive=drive_client()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre116_",dir="/tmp") as temp:
            archive=Path(temp)/"pre99.tar.gz"
            report["phase"]="DOWNLOAD_PRE99"
            download(drive,archive)
            digest,_md5,size=sha_file(archive)
            if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 mismatch")
            report["pre99_archive_sha256_verified"]=True
            report["phase"]="READ_VERIFIED_SOURCE"
            with tarfile.open(archive,"r:gz",errorlevel=2) as tf:
                entry=tf.getmember(SOURCE_NAME)
                if not entry.isfile() or entry.size>2_000_000:raise ValueError("Unexpected settings source metadata")
                f=tf.extractfile(entry)
                if f is None:raise ValueError("Unable to read source")
                with f: data=f.read()
            if hashlib.sha256(data).hexdigest()!=SOURCE_SHA256:raise ValueError("PRE92 source mismatch")
            report["pre92_source_sha256_verified"]=True
            report["phase"]="AUDIT_SCROLL_AND_FOOTER"
            report["findings"]=scan(data.decode("utf-8"))
            report["status"]="PRE116_NESTED_SCROLL_ESTATICO_CONFIRMADO"
            report["phase"]="COMPLETE"
    except Exception as exc:
        report["error_type"]=type(exc).__name__
        print("PRE116 incomplete:",report["phase"],type(exc).__name__)
    finally:
        report["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE116:",report["status"])
    return 0 if report["status"]=="PRE116_NESTED_SCROLL_ESTATICO_CONFIRMADO" else 1

if __name__=="__main__":
    raise SystemExit(main())
