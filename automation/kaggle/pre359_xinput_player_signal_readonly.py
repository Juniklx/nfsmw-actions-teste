#!/usr/bin/env python3
"""PRE359: authenticated PRE99 targeted excerpts of actual XInput state poll route.

Read-only source audit. Does not identify player ownership from name or slot.
No APK, no signing, no saves, no game guest memory access.
"""
from pathlib import Path
import hashlib,tarfile,tempfile,json,re
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre359/PRE359_XINPUT_STATE_BRIDGE.json")
SOURCES={
"workspace/nativo/sdk/src/kernel/xam/xam_input.cpp":(
 r"(?i)XamInputGetState|XamInputGetCapabilities|GetState|GetDeviceState|input_system|user_index|gamepad|X_INPUT_STATE",),
"workspace/nativo/sdk/src/input/sdl/sdl_input_driver.cpp":(
 r"(?i)SDLInputDriver::GetDeviceState|SDLInputDriver::OnControllerDeviceButtonChangedLocked|SDLInputDriver::ProcessEventLocked|SDLInputDriver::OnControllerDeviceAxisChangedLocked|X_INPUT_GAMEPAD|SDL_EVENT_GAMEPAD_BUTTON",),
"workspace/nativo/sdk/include/rex/input/input.h":(
 r"(?i)X_INPUT_GAMEPAD_BUTTON|X_INPUT_STATE|LEFT_TRIGGER|RIGHT_TRIGGER|LEFT_SHOULDER|RIGHT_SHOULDER",),
"workspace/nativo/sdk/src/input/state_merge.cpp":(
 r"(?i)ActiveDeviceTracker::Observe|MergeInto|GetActive|GetDeviceState",),
}
PATTERNS={p:[re.compile(x) for x in regexes] for p,regexes in SOURCES.items()}
WINDOW=12
MAX_CONTEXTS=18
def contexts(lines,pats):
    ixs=[]
    for i,line in enumerate(lines):
        if any(x.search(line) for x in pats) and not line.lstrip().startswith(("//","*","/*")):
            ixs.append(i)
    output=[]
    for i in ixs[:MAX_CONTEXTS]:
        lo=max(0,i-WINDOW);hi=min(len(lines),i+WINDOW+1)
        output.append({"hit_line":i+1,"lines":[{"n":j+1,"code":lines[j][:220]} for j in range(lo,hi)]})
    return {"matches":len(ixs),"windows":output}
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE359_XINPUT_PLAYER_SIGNAL_SOURCE_AUDIT","status":"FAILED",
      "owner_verified":False,"nitro_button_mapping_verified":False,"apk_built":False,"read_only":True}
    try:
        with tempfile.TemporaryDirectory(prefix="pre359_") as td:
            archive=Path(td)/"pre99.tar.gz";download(drive_client(),archive)
            sha,_,size=sha_file(archive)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 archive integrity mismatch")
            with tarfile.open(archive,"r:gz") as tf:
                members={m.name.lstrip("./"):m for m in tf if m.isfile()}
                results={}
                for path in SOURCES:
                    if path not in members or members[path].size>300_000:raise ValueError("Missing/oversized required source "+path)
                    f=tf.extractfile(members[path])
                    if f is None:raise ValueError("Missing member stream")
                    contents=f.read(); lines=contents.decode("utf-8","replace").splitlines()
                    results[path]={"sha256":hashlib.sha256(contents).hexdigest(),
                       "lines":len(lines),**contexts(lines,PATTERNS[path])}
            report.update({"status":"AUDIT_OK","pre99_sha256":sha,
                "files_verified":len(results),"results":results,
                "limitation":"Input polling/API exposed via XInput does not automatically identify player car, nor prove Nitro binding. Need validated guest-to-input mapping and runtime negative AI test before cheat."})
    except Exception as e:report["error_type"]=type(e).__name__
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE359_STATUS",report["status"])
    print("PRE359_FILES",report.get("files_verified",0))
    print("PRE359_OWNER_VERIFIED",False)
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
