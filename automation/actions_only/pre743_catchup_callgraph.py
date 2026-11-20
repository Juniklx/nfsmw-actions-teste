#!/usr/bin/env python3
"""PRE743: private read-only guest PPC caller analysis for real CatchUp instructions.

Evidence from PRE742: immediate pair 4315/1254 builds 0x10DB04E6.
Known candidate functions are scanned for exact definitions, callsites and code.
No host APK, game asset, signing key or gameplay code is modified.
"""
import argparse
import json
import re
import tarfile
import tempfile
from collections import Counter
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from pre104_verify_backup_tar import BACKUP_ID,EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

FOLDER="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
SOURCES=re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.[0-9]+\.cpp$")
FUNC=re.compile(rb"(?m)^DEFINE_REX_FUNC\((sub_82[0-9A-F]{6})\)\s*\{")
TARGETS={
"catchup_flag_bool":"sub_82338A68",
"catchup_flag_pointer":"sub_82327438",
"catchup_flag_writer":"sub_8233BC58",
"catchup_copy":"sub_822C4FC0",
"catchup_controller_candidate":"sub_82332898",
"catchup_controller_setup":"sub_82331CE0",
"catchup_controller_defaults":"sub_82332BB0",
"catchup_controller_setup_parent":"sub_82332BF0",
"race_context_pointer":"sub_820E5E28",
}
MAX_SCAN=400*1024*1024
MAX_BODY=40000
MAX_CALLERS=90

def inspect(path):
    findings={
      "stage":"PRE743B_X360_GUEST_CATCHUP_CALL_GRAPH_PRIVATE",
      "pre99_sha256_verified":True,
      "files_scanned":0,"functions_scanned":0,"bytes_scanned":0,
      "targets":{k:{"symbol":sym,"definitions":[],"direct_callers":[]} for k,sym in TARGETS.items()},
      "source_tree_modified":False,"runtime_hook_validated":False,"apk_built":False,"signing_accessed":False,
    }
    refs={k:re.compile(rb"(?<![A-Za-z0-9_])(?:__imp__)?"+v.encode()+rb"\s*\(") for k,v in TARGETS.items()}
    with tarfile.open(path,"r:gz",errorlevel=2) as tar:
        for member in tar:
            if not member.isfile() or not SOURCES.match(member.name):continue
            if not 0<member.size<=24*1024*1024:raise ValueError("Guest source size out of bounds")
            findings["bytes_scanned"]+=member.size
            if findings["bytes_scanned"]>MAX_SCAN:raise ValueError("Guest source scan budget exceeded")
            f=tar.extractfile(member)
            if f is None:raise ValueError("Guest source unreadable")
            with f:data=f.read()
            findings["files_scanned"]+=1
            headers=list(FUNC.finditer(data))
            for i,h in enumerate(headers):
                fn=h.group(1).decode()
                body=data[h.end():headers[i+1].start() if i+1<len(headers) else len(data)]
                findings["functions_scanned"]+=1
                for target,needle in TARGETS.items():
                    entry=findings["targets"][target]
                    if fn==needle:
                        if entry["definitions"]:raise ValueError("Duplicate target definition: "+needle)
                        entry["definitions"].append({"member":member.name,
                            "length_bytes":len(body),
                            "text":body[:MAX_BODY].decode("utf-8","replace"),
                            "text_truncated":len(body)>MAX_BODY})
                    if fn==needle:continue
                    matches=list(refs[target].finditer(body))
                    if not matches:continue
                    if len(entry["direct_callers"])>=MAX_CALLERS:continue
                    entry["direct_callers"].append({
                        "function":fn,"member":member.name,"count":len(matches),
                        "call_sites":[body[max(0,m.start()-450):min(len(body),m.end()+750)].decode("utf-8","replace")
                           for m in matches[:3]]
                    })
    return findings

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,required=True)
    o=p.parse_args()
    drive=drive_client()
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre743-") as temp:
        archive=Path(temp)/"pre99.tar.gz"
        info=drive.files().get(fileId=BACKUP_ID,fields="id,size").execute()
        if info.get("id")!=BACKUP_ID or int(info.get("size",0))!=EXPECTED_BYTES:
            raise ValueError("Backup source identity invalid")
        download(drive,archive)
        sha,_md5,size=sha_file(archive)
        if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("Backup SHA changed")
        report=inspect(archive)
    o.report.parent.mkdir(parents=True,exist_ok=True)
    o.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    summary={k:{"definitions":len(v["definitions"]),"direct_callers":len(v["direct_callers"])}
             for k,v in report["targets"].items()}
    print("PRE743_EXACT_CALL_GRAPH="+json.dumps(summary,sort_keys=True))
    print("PRE743_GUEST_FUNCTIONS="+str(report["functions_scanned"]))
    name="NFSMW_PRE743B_CATCHUP_GUEST_X360_CALL_GRAPH_PRIVATE.json"
    up=drive.files().create(body={"name":name,"parents":[FOLDER],"mimeType":"application/json"},
         media_body=MediaFileUpload(str(o.report),mimetype="application/json"),
         fields="id,name,parents").execute()
    if up.get("name")!=name or FOLDER not in up.get("parents",[]):
        raise ValueError("Private report Drive identity mismatch")
    print("PRE743_REPORT_DRIVE_ID="+up["id"])
    print("PRE743_NO_GAMEPLAY_PATCH_NO_APK_NO_SIGNING")
if __name__=="__main__":
    main()
