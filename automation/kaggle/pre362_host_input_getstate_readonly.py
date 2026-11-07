#!/usr/bin/env python3
"""PRE362: locate XInput InputSystem::GetState host implementation in authenticated PRE99.
Read-only, bounded excerpts, no guest read or modification.
"""
from pathlib import Path
import json,tarfile,tempfile,re,hashlib
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre362/PRE362_HOST_INPUT_GETSTATE.json")
MATCH=re.compile(r"\b(?:InputSystem::GetState|GetState\s*\(|GetDeviceState\s*\(|X_INPUT_STATE\b|XINPUT_FLAG_ANY_USER)\b")
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE362_HOST_INPUT_GETSTATE_AUDIT","status":"FAILED",
      "owner_verified":False,"nitro_binding_verified":False,"apk_built":False,"read_only":True}
    try:
        with tempfile.TemporaryDirectory(prefix="pre362_") as td:
            archive=Path(td)/"pre99.tar.gz";download(drive_client(),archive)
            sha,_,size=sha_file(archive)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 archive mismatch")
            hits=[];input_sources=0
            with tarfile.open(archive,"r:gz") as tf:
                for m in tf:
                    p=m.name.lstrip("./")
                    if not m.isfile() or m.size>200000:continue
                    if not p.startswith("workspace/nativo/sdk/"):continue
                    if "/input/" not in p or not p.endswith((".cpp",".hpp",".h")):continue
                    if any(x in p for x in ("/thirdparty/","/test/","/examples/")):continue
                    input_sources+=1
                    f=tf.extractfile(m)
                    if f is None:continue
                    b=f.read();rows=b.decode("utf-8","replace").splitlines()
                    matched=[i for i,x in enumerate(rows) if MATCH.search(x) and not x.strip().startswith(("//","*"))]
                    if not matched:continue
                    excerpts=[]
                    for i in matched[:18]:
                        lo=max(0,i-7);hi=min(len(rows),i+24)
                        excerpts.append({"line":i+1,"window":[{"line":j+1,"code":rows[j][:220]} for j in range(lo,hi)]})
                    if len(hits)<35:hits.append({"path":p,"sha256":hashlib.sha256(b).hexdigest(),
                        "matches":len(matched),"excerpts":excerpts})
            if input_sources<5:raise ValueError("Unexpectedly few SDK input sources")
            result.update({"status":"AUDIT_OK","pre99_sha256":sha,
              "input_sources_checked":input_sources,"matching_sources":len(hits),"matches":hits,
              "limitation":"Host state route can be logged without reading guest memory only if source shows a native state before ppc_ptr copy; a button press is not by itself proof of Nitro player ownership."})
    except Exception as e:result["error_type"]=type(e).__name__
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE362_STATUS",result["status"])
    print("PRE362_INPUT_SOURCES",result.get("input_sources_checked"))
    print("PRE362_HITS",result.get("matching_sources"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
