#!/usr/bin/env python3
"""PRE135: verified PRE99 source-only performance/stability hotspot inventory.

No compilation, no patch, no APK, no signing keys. Metrics are NOT produced.
This identifies code paths to measure on the current V30 phone build.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

TOKENS={
 "sdl_event_wait":r"\bSDL_WaitEvent(?:Timeout)?\s*\(",
 "sdl_delay":r"\bSDL_Delay\s*\(",
 "sdl_push":r"\bSDL_PushEvent\s*\(",
 "sdl_poll":r"\bSDL_PollEvent\s*\(",
 "ui_deferred":r"CallInUIThread(?:Deferred)?|QueueControllerUpdate",
 "vertex_copy":r"CopiarVertices|CopyVertices|memcpy\s*\(",
 "present_gpu":r"RefreshGuestOutput|vkQueuePresentKHR|PresentFrame|SwapChain|Swapchain",
 "gpu_sync":r"vkQueueWaitIdle|vkDeviceWaitIdle|WaitForFence|WaitForIdle|WaitForSingleObject",
 "diag_overhead":r"NFSMW_DIAG3[6-9]|NFSMW_PERF|wait_cpu_ms|WAKE10s|QUEUE10s",
 "frame_metrics":r"FrameTime|frame_time|GpuTime|gpu_time|SetTargetFPS|fps_limit",
}
COMPILED={key:re.compile(p) for key,p in TOKENS.items()}
PREFERRED=(
 "workspace/nativo/sdk/src/ui/windowed_app_context_sdl.cpp",
 "workspace/nativo/sdk/src/ui/windowed_app_context.cpp",
 "workspace/nativo/sdk/src/ui/window_sdl.cpp",
 "workspace/nativo/sdk/src/input/sdl/sdl_input_driver.cpp",
 "workspace/nativo/app/src/nfsmw_nativo_dibujos.cpp",
 "workspace/nativo/app_usa/src/nfsmw_nativo_dibujos.cpp",
 "workspace/android/app/src/main/cpp/nativo/nativo_android.cpp",
 "workspace/android/app/build.gradle.kts",
)
MAX_BYTES=1100000
MAX_SOURCE_FILES=48
MAX_EXCERPTS_PER_FILE=48

def meaningful(name:str)->bool:
    if not name.startswith("workspace/"): return False
    if "/thirdparty/" in name or "/out/" in name or "/generated/" in name: return False
    if "/.gradle/" in name or "/.cxx/" in name or "/build/" in name: return False
    if not name.endswith((".cpp",".cc",".c",".hpp",".h",".kt",".java",".kts")):return False
    return (name.startswith("workspace/nativo/sdk/src/") or
            name.startswith("workspace/nativo/app/src/") or
            name.startswith("workspace/nativo/app_usa/src/") or
            name.startswith("workspace/android/app/src/main/") or
            name in PREFERRED)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--run-id",required=True);a.add_argument("--report",required=True)
    opt=a.parse_args()
    if not re.fullmatch(r"\d+",opt.run_id):raise ValueError("Invalid run ID")
    result={"stage":"PRE135_V30_BASELINE_PERFORMANCE_SOURCE_AUDIT",
      "run_id":opt.run_id,"status":"NOT_VERIFIED","phase":"INIT",
      "pre99_sha256_verified":False,"v30_runtime_performance_measured":False,
      "game_running_on_device_measured":False,"source_modified":False,
      "apk_built":False,"signing_key_accessed":False,"drive_modified":False,
      "scope":"source-only verified PRE99 snapshot used to compile V30; not a profile",
      "candidates":[],"summary":{}}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre135_") as temp:
            archive=Path(temp)/"pre99.tar.gz"
            result["phase"]="DOWNLOAD_PRE99"
            download(drive_client(),archive)
            result["phase"]="VERIFY_PRE99"
            sha,_md5,size=sha_file(archive)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 backup integrity mismatch")
            result["pre99_sha256_verified"]=True
            result["phase"]="SCAN_SOURCE_READ_ONLY"
            records=[]
            total_examined=0
            with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
                for member in tar:
                    if not member.isfile() or member.size>MAX_BYTES:continue
                    if not meaningful(member.name):continue
                    source=tar.extractfile(member)
                    if source is None:continue
                    data=source.read(MAX_BYTES+1)
                    if len(data)>MAX_BYTES:continue
                    total_examined+=1
                    text=data.decode("utf-8",errors="replace")
                    lines=text.splitlines()
                    hits=[]
                    counts=Counter()
                    for ix,line in enumerate(lines):
                        categories=[label for label,rx in COMPILED.items() if rx.search(line)]
                        if categories:
                            counts.update(categories)
                            # Include limited neighboring lines to preserve the exact call context.
                            hits.append((ix,categories))
                    if not hits and member.name not in PREFERRED:continue
                    excerpts=[]
                    seen=set()
                    for ix,labels in hits:
                        for j in range(max(0,ix-2),min(len(lines),ix+3)):
                            if j not in seen and len(excerpts)<MAX_EXCERPTS_PER_FILE:
                                excerpts.append({"line":j+1,"text":lines[j][:240]})
                                seen.add(j)
                    records.append({"path":member.name,
                        "sha256":hashlib.sha256(data).hexdigest(),
                        "source_lines":len(lines),"occurrences":dict(counts),
                        "excerpts":sorted(excerpts,key=lambda x:x["line"])})
            records.sort(key=lambda x:(x["path"] not in PREFERRED,
                                       -sum(x["occurrences"].values()),x["path"]))
            result["sources_scanned"]=total_examined
            result["matching_sources"]=len(records)
            result["candidates"]=records[:MAX_SOURCE_FILES]
            summary=Counter()
            for record in records:summary.update(record["occurrences"])
            result["summary"]={"token_occurrences_by_category":dict(summary),
               "source_paths_present":[p for p in PREFERRED if any(q["path"]==p for q in records)],
               "truncated_to_top_n":MAX_SOURCE_FILES}
            if not result["candidates"]:raise ValueError("No audited source paths")
            result["phase"]="COMPLETE"
            result["status"]="PRE135_SOURCE_HOTPATHS_AUDITED_NO_RUNTIME_METRICS"
    except Exception as exc:
        result["error_type"]=type(exc).__name__
    finally:
        result["recorded_utc"]=datetime.now(timezone.utc).isoformat()
        dst=Path(opt.report);dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE135 status",result["status"],"phase",result["phase"],
              "scanned",result.get("sources_scanned",0),
              "candidates",len(result["candidates"]))
    return 0 if result["status"]=="PRE135_SOURCE_HOTPATHS_AUDITED_NO_RUNTIME_METRICS" else 1

if __name__=="__main__":
    raise SystemExit(main())
