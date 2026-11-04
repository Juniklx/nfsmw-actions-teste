#!/usr/bin/env python3
"""NFSMW PRE114 — read-only root-scroll/header clipping audit of verified PRE99.

Check full SHA256 before inspecting exact C++ source members. Report the
ordering of header and search input, absence/presence of scroll-reset calls,
and ImGui font/clip/window flow. Do not mutate source, Drive or APK.
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
from pre105_read_settings_source import drive_client, download

SOURCE_HASHES = {
    "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp":
        "5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034",
    "workspace/nativo/sdk/src/ui/imgui_drawer.cpp":
        "1a62d13e81af3aac4837af06e90281b64bd282c78e6e5ce079d6ca930e8a5c24",
    "workspace/nativo/sdk/src/ui/imgui_dialog.cpp":
        "9dcc8cb03768bbabf20ac925363017cd56aa6221d501c2554db2b98246690ef3",
}

SEARCH = {
    "scroll_reads": r"\b(?:GetScrollY|GetScrollMaxY|GetScrollX)\s*\(",
    "scroll_writes": r"\b(?:SetScrollY|SetScrollX|SetScrollHereY|SetScrollHereX|SetNextWindowScroll|SetScrollFromPosY)\s*\(",
    "clip": r"\b(?:PushClipRect|PopClipRect|GetWindowDrawList|ClipRect|Scissor)\b",
    "font_scale": r"\b(?:FontGlobalScale|SetWindowFontScale|GetFontSize|FontDefault|DisplayFramebufferScale|FontAtlas|Fonts->|ImFont)\b",
    "draw_frame": r"\b(?:NewFrame|Render|GetDrawData|ImGuiDialog::Draw|OnDraw)\s*\(",
    "window": r"\b(?:SetNextWindowSize|SetNextWindowPos|BeginChild|EndChild|Begin|End|NoScrollbar)\b",
}

HEADER_TOKENS = {
    "root_window_begin": 'ImGui::Begin(\n      "Settings##rex"',
    "root_window_early_return": "if (!settings_visible)",
    "header_child": '"##mw_header", ImVec2(0.0f, 70.0f)',
    "header_title": '"NEED FOR SPEED / MOST WANTED"',
    "header_subtitle": '"SETTINGS  /  ANDROID"',
    "header_end": "ImGui::EndChild();",
    "search_input": 'ImGui::InputText("##search"',
    "category_label": 'ImGui::TextDisabled("CATEGORY")',
}

def occurrences(source: str, expression: str) -> list[int]:
    matches = re.finditer(expression, source, re.M)
    return [source.count("\n", 0, m.start()) + 1 for m in matches]


def excerpt(source: str, sections: list[tuple[int,int]], max_lines: int) -> list[dict]:
    lines = source.splitlines()
    wanted = set()
    for begin, end in sections:
        wanted.update(range(max(0,begin-1), min(len(lines),end)))
    return [{"line": i+1, "text": lines[i][:360]}
            for i in sorted(wanted)[:max_lines]]


def analyse(source: dict[str,str]) -> dict:
    settings_path = "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp"
    settings = source[settings_path]
    ordered = {}
    for key, token in HEADER_TOKENS.items():
        pos = settings.find(token)
        if pos < 0:
            raise ValueError("Unexpected PRE92 settings source, missing " + key)
        ordered[key] = {"byte_offset": pos, "line": settings.count("\n",0,pos)+1}
    keys = ["root_window_begin", "header_child", "header_title",
            "header_subtitle", "header_end", "search_input", "category_label"]
    if not all(ordered[a]["byte_offset"] < ordered[b]["byte_offset"]
               for a,b in zip(keys,keys[1:])):
        raise ValueError("Header/search/category ordering differs from PRE92")
    inspections = {}
    for name, body in source.items():
        inspect = {}
        for key, regex in SEARCH.items():
            at = occurrences(body,regex)
            inspect[key] = {"count":len(at),"lines":at[:35]}
        inspections[name] = {
            "line_count":len(body.splitlines()),
            "patterns":inspect,
            "source_sha256":hashlib.sha256(body.encode("utf-8")).hexdigest(),
        }
    settings_lines = settings.splitlines()
    return {
        "source_item_order": ordered,
        "header_comes_before_search": True,
        "root_settings_scroll_reset_calls_found": inspections[settings_path]["patterns"]["scroll_writes"]["count"],
        "root_scroll_current_value_known": False,
        "device_actual_imgui_scroll_value_known": False,
        "device_actual_clip_rectangle_known": False,
        "device_font_scale_known": False,
        "source_patterns": inspections,
        "settings_window_and_header_lines": excerpt(settings,[(222,280),(336,386),(748,765)],135),
        "drawer_render_frame_lines": excerpt(source[
          "workspace/nativo/sdk/src/ui/imgui_drawer.cpp"], [(429,485)],65),
        "dialog_draw_lines": excerpt(source[
          "workspace/nativo/sdk/src/ui/imgui_dialog.cpp"],[(31,53)],26),
        "interpretation": [
            "The verified C++ draws the mobile header before the search input.",
            "An absent scroll reset is only a possible explanation of a missing header, not proof that the window was scrolled.",
            "No Android runtime scroll, clip rectangle, font size or framebuffer scaling were measured in this source audit.",
            "The next diagnostic should record GetScrollY, GetScrollMaxY, ImGui::GetWindowPos and the header child rect in a controlled device test.",
        ],
        "patch_applied": False,
        "apk_built": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id",required=True)
    parser.add_argument("--report",required=True)
    args=parser.parse_args()
    if not re.fullmatch(r"\d+",args.run_id):
        raise ValueError("run id must be numeric")
    output=Path(args.report)
    output.parent.mkdir(parents=True,exist_ok=True)
    report={
        "etapa":"PRE114_HEADER_IMGUI_SCROLL_CLIP_AUDIT",
        "run_id":args.run_id,
        "status":"NAO_VALIDADO",
        "phase":"INITIAL",
        "pre99_sha256_confirmed":False,
        "all_source_sha256_confirmed":False,
        "original_workspace_modified":False,
        "google_drive_modified":False,
        "apk_built":False,
        "signing_key_accessed":False,
    }
    try:
        report["phase"]="OAUTH"
        drive=drive_client()
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre114_",dir="/tmp") as temp:
            archive=Path(temp)/"pre99.tar.gz"
            report["phase"]="DOWNLOAD_PRE99"
            download(drive,archive)
            report["phase"]="VERIFY_SHA256"
            digest,_md5,size=sha_file(archive)
            if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 archive SHA/size differs")
            report["pre99_sha256_confirmed"]=True
            report["phase"]="READ_SOURCE_MEMBERS"
            source={}
            with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
                for member in tar:
                    if member.name not in SOURCE_HASHES:
                        continue
                    if not member.isfile() or member.size>1_000_000:
                        raise ValueError("Unexpected C++ member metadata")
                    fp=tar.extractfile(member)
                    if fp is None:raise ValueError("Unable to read source")
                    with fp: blob=fp.read()
                    if hashlib.sha256(blob).hexdigest()!=SOURCE_HASHES[member.name]:
                        raise ValueError("Previously verified source SHA changed")
                    if member.name in source:
                        raise ValueError("Duplicate C++ source member")
                    source[member.name]=blob.decode("utf-8")
            if set(source)!=set(SOURCE_HASHES):
                raise ValueError("One or more C++ source members missing")
            report["all_source_sha256_confirmed"]=True
            report["phase"]="STATIC_HEADER_SCROLL_ANALYSIS"
            report["audit"]=analyse(source)
            report["status"]="HEADER_SCROLL_CLIP_ESTATICO_AUDITADO"
            report["phase"]="COMPLETE"
    except Exception as exc:
        report["error_type"]=type(exc).__name__
        print("PRE114 not complete in phase:",report["phase"],
              "type:",type(exc).__name__)
    finally:
        report["recorded_utc"]=datetime.now(timezone.utc).isoformat()
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE114 status:",report["status"])
    return 0 if report["status"]=="HEADER_SCROLL_CLIP_ESTATICO_AUDITADO" else 1

if __name__=="__main__":
    raise SystemExit(main())
