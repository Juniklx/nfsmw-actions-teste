#!/usr/bin/env python3
"""PRE357: targeted, source-only inventory of gamepad/keyboard event ingress and player-Nitro controls.
Uses authenticated PRE99 snapshot. Does not touch guest, APK, signing, saves.
Returns bounded code context with numbered lines only, no credential/config content.
"""
from pathlib import Path
import tarfile,tempfile,json,re,hashlib
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre357/PRE357_PLAYER_INPUT_INGRESS.json")
TERMS=[
("nitro",r"(?i)nitro|nitrous|boost"),
("gamepad_button",r"SDL_EVENT_GAMEPAD_BUTTON_(?:DOWN|UP)|SDL_GAMEPAD_BUTTON_|SDL_GamepadButton|GamepadButton"),
("joystick_button",r"SDL_EVENT_JOYSTICK_BUTTON_(?:DOWN|UP)|SDL_JoystickButton"),
("keyboard",r"SDL_EVENT_KEY_(?:DOWN|UP)|SDL_KEYDOWN|SDL_KEYUP|SDL_SCANCODE_"),
("input_callback",r"(?i)gamepad.*(?:input|event)|(?:input|event).*gamepad|process.*input|input.*process"),
]
PATTERNS=[(tag,re.compile(p)) for tag,p in TERMS]
EXCLUDE=("/generated/","/thirdparty/","/third_party/","/vendor/","/tests/","/test/","/examples/","/external/")
PREFIXES=("workspace/nativo/app/","workspace/nativo/app_usa/","workspace/android/app/src/main/cpp/","workspace/nativo/sdk/")
def candidate(name):
    n=name.lower()
    return (name.startswith(PREFIXES) and n.endswith((".cpp",".cc",".hpp",".h",".c"))
      and not any(part in n for part in EXCLUDE)
      and any(part in n for part in ("input","controller","gamepad","sdl","keyboard","button","android")))
def occurrences(lines):
    found=[]
    for i,line in enumerate(lines):
        tags=[name for name,rgx in PATTERNS if rgx.search(line)]
        if tags and not line.strip().startswith(("//","/*","*")):
            found.append((i,tags))
    return found
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE357_INPUT_NITRO_SOURCE_INGRESS","status":"FAILED","read_only":True,
      "owner_verified":False,"apk_built":False,"guest_modified":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre357_") as td:
            arc=Path(td)/"pre99.tar.gz";download(drive_client(),arc)
            digest,_,size=sha_file(arc)
            if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 archive mismatch")
            found=[];checked=0;all_lines=0;selected=0;global_hits=0
            with tarfile.open(arc,"r:gz") as tf:
                for m in tf:
                    name=m.name.lstrip("./")
                    if not m.isfile() or not candidate(name) or m.size>1_500_000:continue
                    checked+=1
                    fp=tf.extractfile(m)
                    if not fp:continue
                    data=fp.read()
                    lines=data.decode("utf-8",errors="replace").splitlines()
                    all_lines+=len(lines)
                    matches=occurrences(lines)
                    if not matches:continue
                    selected+=1;global_hits+=len(matches)
                    # Bounded excerpts only from non-generated native C++ sources, never personal data.
                    if len(found)<50:
                        hits=[]
                        for i,tags in matches[:16]:
                            lo=max(0,i-2);hi=min(len(lines),i+3)
                            hits.append({"line":i+1,"tags":tags,
                                "window":[{"line":j+1,"code":lines[j].strip()[:180]} for j in range(lo,hi)]})
                        found.append({"file":name,"sha256":hashlib.sha256(data).hexdigest(),
                          "total_matches":len(matches),"sample":hits})
            if checked<1:raise ValueError("No input sources in archive inventory")
            report.update({"status":"AUDIT_OK","pre99_sha256":digest,
              "files_checked":checked,"source_lines_checked":all_lines,
              "files_matching":selected,"total_source_hits":global_hits,
              "bounded_files":found,
              "interpretation":"Native SDL/Android ingress only. Input event names do not prove mapping to Nitro guest controls or player car owner.",
              "next_gate":"Identify exact button event and original game mapping, then separate player-input events from passive guest Nitro writes without assuming first slot is player."})
    except Exception as e:report["error_type"]=type(e).__name__
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE357_STATUS",report["status"])
    print("PRE357_FILES_CHECKED",report.get("files_checked"))
    print("PRE357_MATCHING_FILES",report.get("files_matching"))
    print("PRE357_MATCHES",report.get("total_source_hits"))
    print("PRE357_OWNER_VERIFIED",False)
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
