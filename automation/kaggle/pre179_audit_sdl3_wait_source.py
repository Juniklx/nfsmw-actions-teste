#!/usr/bin/env python3
"""PRE179: read-only SHA-pinned PRE99 archive scan for vendored SDL event-loop sources."""
from __future__ import annotations
import hashlib, json, tarfile, tempfile, zipfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

TARGETS=("src/events/SDL_events.c","src/video/android/SDL_androidevents.c",
         "src/core/android/SDL_android.c","include/SDL3/SDL_version.h")
def main():
    out=Path("/tmp/nfsmw-pre179-sdl3-audit");out.mkdir(parents=True,exist_ok=True)
    matches=[];metadata=[];candidates=[]
    with tempfile.TemporaryDirectory(prefix="pre179_sdl3_") as d:
        arc=Path(d)/"PRE99.tar.gz"
        download(drive_client(),arc)
        sha,_,size=sha_file(arc)
        if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise RuntimeError("PRE99 snapshot mismatch")
        with tarfile.open(arc,"r:gz") as tar,zipfile.ZipFile(out/"PRE179_SDL3_READONLY_AUDIT.zip","w",zipfile.ZIP_DEFLATED) as z:
            for m in tar:
                name=m.name
                if not m.isfile():continue
                lower=name.lower()
                if "sdl" in lower and any(x in lower for x in ("/src/", "version.h", "cmake", "sdl3")) and len(candidates)<80:
                    candidates.append(name)
                if not any(name.endswith(t) for t in TARGETS):continue
                if m.size>600000:raise RuntimeError("Unexpected SDL file size: "+name)
                file=tar.extractfile(m)
                if file is None:raise RuntimeError("Could not extract: "+name)
                data=file.read()
                if len(data)!=m.size:raise RuntimeError("Short read")
                if name in matches:raise RuntimeError("duplicate")
                matches.append(name)
                digest=hashlib.sha256(data).hexdigest()
                z.writestr("matched/"+str(len(matches))+"_"+name.replace("/","_"),data)
                metadata.append({"archive_path":name,"bytes":len(data),"sha256":digest,
                                 "wait_event_timeout_ns":b"SDL_WaitEventTimeoutNS" in data,
                                 "android_pump_events":b"Android_PumpEvents" in data,
                                 "push_poll_sentinel":b"SDL_PumpEventsInternal(true)" in data})
            report={"stage":"PRE179","verified_pre99_sha256":sha,"bytes":size,
                    "source_modified":False,"matching_sources":metadata,"sample_candidate_paths":candidates,
                    "note":"No exact vendored source in PRE99 is possible; don't infer SDL implementation from upstream."}
            z.writestr("PRE179_REPORT.json",json.dumps(report,indent=2))
    print("PRE179_PRE99_AUTH_OK",sha,"SDL_TARGETS_FOUND",len(matches))
    for x in metadata:print("SDL_SOURCE",x)
    if not matches:print("PRE179_SOURCE_ABSENT_FROM_PRE99_SNAPSHOT")
if __name__=="__main__":main()
