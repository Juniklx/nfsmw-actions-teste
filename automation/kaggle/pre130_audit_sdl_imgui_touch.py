#!/usr/bin/env python3
"""PRE130: read-only exact PRE99 SDL/ImGui Android touch event routing audit.

Private sanitized source excerpts only; no keys, game binaries, build, or APK.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download, SOURCE_NAME, SOURCE_SHA256

TOKENS = (
    "ImGui_ImplSDL", "ProcessEvent", "SDL_EVENT_FINGER", "SDL_FINGER",
    "SDL_EVENT_MOUSE", "SDL_MOUSE", "SDL_Touch", "SDL_GetMouse", "FingerMotion",
    "MouseDelta", "MouseDown", "MousePos", "AddMouse", "IsMouseDragging",
    "io.WantCaptureMouse", "WantCaptureMouse", "ImGui_Impl", "ImGui::NewFrame",
    "SDL_GetTouch", "SDL_PollEvent", "SDL_WaitEvent",
    "SDL_PushEvent", "SDL_Event", "touch", "Touch", "finger",
    "MOUSEMOTION", "SDL_MOUSEMOTION", "SDL_MOUSEBUTTON",
)
RELEVANT_PATHS = (
    "workspace/nativo/sdk/src/ui/imgui_drawer.cpp",
    "workspace/nativo/sdk/src/ui/rex_app.cpp",
    "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp",
    "workspace/nativo/sdk/src/ui/overlay/settings_overlay.h",
)
MAX_FILE=1_500_000
MAX_RESULT_FILES=50
MAX_LINES=155

def preview(data:bytes,name:str):
    text=data.decode("utf-8",errors="replace").splitlines()
    found=[]
    indices=set()
    for i,line in enumerate(text):
        if any(k in line for k in TOKENS):
            found.append(i+1)
            for j in range(max(0,i-4),min(len(text),i+5)):indices.add(j)
    if name.endswith("/ui/overlay/settings_overlay.cpp"):
        for j in range(220,min(280,len(text))):indices.add(j)
        for j in range(725,min(765,len(text))):indices.add(j)
    return {"path":name,"source_sha256":hashlib.sha256(data).hexdigest(),
            "total_lines":len(text),"total_matching_lines":len(found),
            "matched_line_numbers":found[:160],
            "excerpts":[{"line":i+1,"text":text[i][:260]} for i in sorted(indices)[:MAX_LINES]]}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--run-id",required=True); a.add_argument("--report",required=True)
    opt=a.parse_args()
    if not re.fullmatch(r"\d+",opt.run_id):raise ValueError("Run ID must be numeric")
    report={"stage":"PRE130_ANDROID_IMGUI_SDL_TOUCH_AUDIT","run_id":opt.run_id,
            "phase":"INIT","status":"NOT_VERIFIED","original_pre99_sha256_verified":False,
            "settings_source_sha256_verified":False,"source_modified":False,
            "private_keys_accessed":False,"apk_built":False,"android_touch_runtime_tested":False,
            "files":[]}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre130_") as tmp:
            p=Path(tmp)/"pre99.tar.gz"
            report["phase"]="DOWNLOAD_PRE99"
            download(drive_client(),p)
            report["phase"]="VERIFY_PRE99_SHA256"
            sha,_md5,sz=sha_file(p)
            if sha!=EXPECTED_SHA256 or sz!=EXPECTED_BYTES:
                raise ValueError("Full PRE99 backup digest mismatch")
            report["original_pre99_sha256_verified"]=True
            report["phase"]="AUDIT_UI_AND_SDL_SOURCE"
            with tarfile.open(p,"r:gz",errorlevel=2) as tf:
                collected=[]
                for member in tf:
                    if not member.isfile() or member.size>MAX_FILE:
                        continue
                    name=member.name
                    is_ui=name.startswith("workspace/nativo/sdk/src/ui/") or name.startswith("workspace/nativo/sdk/include/rex/ui/")
                    is_input=("/sdl" in name.lower() or "/input/" in name.lower() or "/imgui" in name.lower()) and name.startswith("workspace/nativo/")
                    is_android=name.startswith("workspace/android/") and name.endswith((".java",".kt",".cpp"))
                    if not (is_ui or is_input or is_android or name in RELEVANT_PATHS):
                        continue
                    if not name.endswith((".cpp",".cc",".c",".h",".hpp",".java",".kt")):continue
                    if len(collected)>=MAX_RESULT_FILES and name not in RELEVANT_PATHS:continue
                    file=tf.extractfile(member)
                    if file is None:continue
                    data=file.read(MAX_FILE+1)
                    if len(data)>MAX_FILE:continue
                    if name==SOURCE_NAME:
                        if hashlib.sha256(data).hexdigest()!=SOURCE_SHA256:
                            raise ValueError("Original Settings source unexpectedly changed")
                        report["settings_source_sha256_verified"]=True
                    found=sum(data.count(t.encode()) for t in TOKENS)
                    if found>=2 or name in RELEVANT_PATHS:
                        collected.append((found,preview(data,name)))
                collected.sort(key=lambda p:(p[1]["path"] not in RELEVANT_PATHS,-p[0]))
                report["files"]=[x[1] for x in collected[:MAX_RESULT_FILES]]
                report["files_discovered"]=len(collected)
                report["source_paths"]=[x["path"] for x in report["files"]]
            if not report["settings_source_sha256_verified"]:
                raise ValueError("Settings source was not audited")
        report["status"]="SOURCE_PATHS_AND_EVENTS_AUDITED"
        report["phase"]="COMPLETE"
    except Exception as exc:
        report["error_type"]=type(exc).__name__
    finally:
        report["recorded_utc"]=datetime.now(timezone.utc).isoformat()
        Path(opt.report).parent.mkdir(parents=True,exist_ok=True)
        Path(opt.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE130:",report["status"],report["phase"],"files",len(report["files"]))
    return 0 if report["status"]=="SOURCE_PATHS_AND_EVENTS_AUDITED" else 1

if __name__=="__main__":raise SystemExit(main())
