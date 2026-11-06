#!/usr/bin/env python3
"""PRE204: authenticated PRE99 generated-code input/import and hook crossrefs.
READ-ONLY: no build, source changes, save changes, or signing-key access.
"""
from __future__ import annotations
import argparse, hashlib, json, re, tarfile, tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

OUT=Path("/tmp/nfsmw-pre204-xrefs")
PFX=("workspace/nativo/app/generated/default/", "workspace/nativo/app_usa/generated/default/")
HOOKS={
"pal": {"sub_8243FF30","sub_82216600","sub_8243C6E0","sub_824E63D8"},
"usa": {"sub_8243FDC8","sub_82216600","sub_8243C578","sub_824E6220"}}
FUNC=re.compile(r"\bDEFINE_REX_FUNC\((sub_[0-9a-fA-F]{8})\)")
SYMBOL=re.compile(r"\bsub_[0-9a-fA-F]{8}\b")
IMPORT=re.compile(r"XamInput|XInput|InputGetState|GetGamepadState|XamUser|__imp__", re.I)
INPUT=re.compile(r"XamInputGetState|XInputGetState|GetGamepadState|XamInput",re.I)

def audit():
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre204_") as temp:
        path=Path(temp)/"PRE99.tar.gz"
        download(drive_client(),path)
        digest,_,size=sha_file(path)
        if size!=EXPECTED_BYTES or digest!=EXPECTED_SHA256:
            raise ValueError("PRE99 size/hash mismatch")
        eds={}
        for ed in ("pal","usa"):
            eds[ed]={"files_scanned":0,"bytes_scanned":0,"functions":0,
                "import_mentions":0,"input_mentions":0,
                "import_examples":[],"input_examples":[],"registration":{},
                "hook_refs":{s:{"mentions":0,"definitions":0,"examples":[]} for s in sorted(HOOKS[ed])}}
        with tarfile.open(path,"r:gz",errorlevel=2) as tar:
            for m in tar:
                n=m.name.lstrip("./")
                if not m.isfile() or not n.startswith(PFX):
                    continue
                if Path(n).suffix.lower() not in (".cpp",".h") or m.size>2500000:
                    continue
                f=tar.extractfile(m)
                if f is None:raise ValueError("Missing TAR member")
                data=f.read()
                if len(data)!=m.size:raise ValueError("Short TAR read")
                ed="usa" if n.startswith(PFX[1]) else "pal"
                e=eds[ed]
                e["files_scanned"]+=1
                e["bytes_scanned"]+=len(data)
                lines=data.decode("utf-8","replace").splitlines()
                current=None
                for i,line in enumerate(lines,1):
                    function=FUNC.search(line)
                    if function:
                        current=function.group(1)
                        e["functions"]+=1
                    for name,rx,limit in (("import",IMPORT,50),("input",INPUT,90)):
                        if not rx.search(line):continue
                        e[name+"_mentions"]+=1
                        if len(e[name+"_examples"])<limit:
                            e[name+"_examples"].append({"path":n,"line":i,"function":current,"text":line.strip()[:170]})
                    for sym in (set(SYMBOL.findall(line))&HOOKS[ed]):
                        entry=e["hook_refs"][sym]
                        entry["mentions"]+=1
                        if function and function.group(1)==sym:
                            entry["definitions"]+=1
                        elif len(entry["examples"])<45:
                            entry["examples"].append({"path":n,"line":i,"function":current,"text":line.strip()[:170]})
                if Path(n).name in {"nfsmw_register.cpp","nfsmw_init.cpp"}:
                    e["registration"][n]={"sha256":hashlib.sha256(data).hexdigest(),
                        "first_20_lines":lines[:20],
                        "input_mentions":[{"line":i,"text":s[:170]} for i,s in enumerate(lines,1) if INPUT.search(s)][:30]}
        return {"stage":"PRE204_INPUT_IMPORT_HOOK_XREFS_READONLY","status":"AUDIT_OK",
            "pre99_sha256":digest,"backup_verified":True,
            "read_only":True,"source_modified":False,"apk_built":False,"signer_accessed":False,"saves_accessed":False,
            "editions":eds,"limitations":["No gameplay resource state or address inferred from graphics hooks",
              "PRE99 source baseline is not a verbatim snapshot of V36",
              "Imported functions may be bound indirectly; text search is not behavioral proof"]}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",required=True)
    args=parser.parse_args()
    if not args.run_id.isdecimal():raise ValueError("Invalid run ID")
    OUT.mkdir(parents=True,exist_ok=True)
    r={"stage":"PRE204_INPUT_IMPORT_HOOK_XREFS_READONLY","status":"FAILED","run_id":args.run_id,
       "read_only":True,"apk_built":False,"signer_accessed":False,"source_modified":False}
    try:
        r=audit()
        r["run_id"]=args.run_id
    except Exception as e:
        r["error_type"]=type(e).__name__
    (OUT/"PRE204_XREFS_READONLY.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE204_STATUS",r["status"])
    print("PRE204_BACKUP_VALID",r.get("backup_verified",False))
    for ed,v in r.get("editions",{}).items():
        print("PRE204_ED",ed,"FILES",v["files_scanned"],"DEFS",v["functions"],
              "INPUT",v["input_mentions"],"HOOKS",{k:z["mentions"] for k,z in v["hook_refs"].items()})
    if r["status"]!="AUDIT_OK":print("PRE204_ERROR_TYPE",r.get("error_type"))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
