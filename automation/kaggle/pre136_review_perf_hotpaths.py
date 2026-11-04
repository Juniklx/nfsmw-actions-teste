#!/usr/bin/env python3
"""PRE136 targeted full-context, read-only source review for V30 performance.

Never applies performance patches. Confirms PRE99 SHA and reproduces PRE135
source hashes before collecting code ranges for engineering review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

TARGETS={
"workspace/nativo/sdk/src/ui/windowed_app_context_sdl.cpp":[(75,255),(255,335)],
"workspace/nativo/sdk/src/ui/windowed_app_context.cpp":[(25,120)],
"workspace/nativo/sdk/src/input/sdl/sdl_input_driver.cpp":[(810,880)],
"workspace/nativo/sdk/src/ui/window_sdl.cpp":[(410,465)],
"workspace/nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp":[(95,330)],
"workspace/nativo/sdk/src/graphics/vulkan/command_processor.cpp":[(2415,2460)]
}
MAX_FILE_BYTES=4_000_000

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",required=True)
    parser.add_argument("--report",required=True)
    args=parser.parse_args()
    if not re.fullmatch(r"\d+",args.run_id):
        raise ValueError("Invalid run ID")
    report={"stage":"PRE136_V30_PRE99_EXACT_SDL_GPU_PATH_REVIEW",
      "run_id":args.run_id,"status":"NOT_VERIFIED","phase":"INIT",
      "pre99_verified":False,"source_only":True,"apk_built":False,
      "source_modified":False,"signing_key_accessed":False,
      "google_drive_modified":False,"phone_performance_measured":False,
      "target_sources":[],"target_count":len(TARGETS)}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre136_") as tmp:
            archive=Path(tmp)/"source.tar.gz"
            report["phase"]="DOWNLOAD_PRE99"
            download(drive_client(),archive)
            report["phase"]="VERIFY_PRE99"
            sha,_md5,size=sha_file(archive)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 integrity mismatch")
            report["pre99_verified"]=True
            report["phase"]="EXTRACT_EXACT_CODE_WINDOWS_READ_ONLY"
            selected={}
            with tarfile.open(archive,"r:gz",errorlevel=2) as t:
                for m in t:
                    if m.name not in TARGETS:continue
                    if not m.isfile() or m.size>MAX_FILE_BYTES:
                        raise ValueError("Target source invalid or too large")
                    f=t.extractfile(m)
                    if f is None: raise ValueError("Target source unreadable")
                    content=f.read(MAX_FILE_BYTES+1)
                    if len(content)>MAX_FILE_BYTES:raise ValueError("Target size overflow")
                    lines=content.decode("utf-8",errors="replace").splitlines()
                    windows=[]
                    for lo,hi in TARGETS[m.name]:
                        windows.append({"first_line":lo,"last_line":min(hi,len(lines)),
                            "lines":[{"line":i+1,"text":lines[i][:320]}
                                      for i in range(lo-1,min(hi,len(lines)))]})
                    selected[m.name]={"path":m.name,
                        "sha256":hashlib.sha256(content).hexdigest(),
                        "line_count":len(lines),"code_windows":windows}
            if set(selected)!=set(TARGETS):
                report["missing_targets"]=sorted(set(TARGETS)-set(selected))
                raise ValueError("Expected source paths missing")
            report["target_sources"]=[selected[k] for k in TARGETS]
            report["status"]="PRE136_PRE99_SDL_GPU_SOURCE_REVIEW_COMPLETE"
            report["phase"]="COMPLETE"
    except Exception as exc:
        report["error_type"]=type(exc).__name__
    finally:
        report["utc"]=datetime.now(timezone.utc).isoformat()
        p=Path(args.report);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        print("PRE136:",report["status"],report["phase"],
              "read_only_targets",len(report["target_sources"]))
    return 0 if report["status"]=="PRE136_PRE99_SDL_GPU_SOURCE_REVIEW_COMPLETE" else 1

if __name__=="__main__":
    raise SystemExit(main())
