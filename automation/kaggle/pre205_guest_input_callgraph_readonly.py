#!/usr/bin/env python3
"""PRE205: trace direct PPC callgraph ancestors of verified XamInputGetState wrappers.
Read only SHA-verified PRE99; no game data/SDK/signing modifications.
"""
from __future__ import annotations
import argparse, collections, json, re, tarfile, tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre205")
PREFIXES={"pal":"workspace/nativo/app/generated/default/",
          "usa":"workspace/nativo/app_usa/generated/default/"}
SEEDS={
"pal":{"XamInputGetState":"sub_8262D8B0","XamInputGetKeystrokeEx":"sub_8262D910"},
"usa":{"XamInputGetState":"sub_8262D6B8","XamInputGetKeystrokeEx":"sub_8262D718"}}
DEF=re.compile(r"\bDEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
CALL=re.compile(r"\b(sub_[0-9A-Fa-f]{8})\s*\(\s*ctx\s*,\s*base\s*\)")
MACRO_CALL=re.compile(r"\bREX_(?:CALL|TAILCALL)\(\s*(sub_[0-9A-Fa-f]{8})")
def parse():
    with tempfile.TemporaryDirectory(prefix="pre205_") as folder:
        source=Path(folder)/"PRE99.tar.gz"
        download(drive_client(),source)
        digest,_,size=sha_file(source)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("PRE99 digest mismatch")
        rev={ed:collections.defaultdict(set) for ed in PREFIXES}
        defs={ed:set() for ed in PREFIXES}
        samples={ed:collections.defaultdict(list) for ed in PREFIXES}
        counts={ed:{"files":0,"bytes":0,"direct_calls":0} for ed in PREFIXES}
        with tarfile.open(source,"r:gz",errorlevel=2) as tf:
            for m in tf:
                name=m.name.lstrip("./")
                if not m.isfile() or not name.endswith(".cpp") or "nfsmw_recomp." not in name:
                    continue
                ed=next((k for k,p in PREFIXES.items() if name.startswith(p)),None)
                if ed is None:continue
                if m.size>2400000:raise ValueError("Unexpected generated source size")
                f=tf.extractfile(m)
                if f is None:raise ValueError("Missing TAR source")
                raw=f.read()
                if len(raw)!=m.size:raise ValueError("Truncated source member")
                counts[ed]["files"]+=1
                counts[ed]["bytes"]+=len(raw)
                current=None
                seeds=set(SEEDS[ed].values())
                for line_no,line in enumerate(raw.decode("utf-8","replace").splitlines(),1):
                    match=DEF.search(line)
                    if match:
                        current=match.group(1)
                        defs[ed].add(current)
                    if current is None:continue
                    called=set(CALL.findall(line))|set(MACRO_CALL.findall(line))
                    if not called:continue
                    for callee in called:
                        if callee==current:continue
                        rev[ed][callee].add(current)
                        counts[ed]["direct_calls"]+=1
                        if callee in seeds and len(samples[ed][callee])<35:
                            samples[ed][callee].append({"path":name,"line":line_no,
                                "caller":current,"callee":callee,
                                "snippet":line.strip()[:180]})
        found={}
        for ed in PREFIXES:
            found[ed]={"totals":counts[ed],"defined_functions":len(defs[ed]),
                       "targets":{}}
            for title,seed in SEEDS[ed].items():
                visited={seed}
                active={seed}
                layers=[]
                for depth in range(1,5):
                    next_nodes=set()
                    for node in active:
                        next_nodes.update(rev[ed].get(node,()))
                    next_nodes-=visited
                    visited|=next_nodes
                    layers.append({"depth":depth,"count":len(next_nodes),
                                   "functions":sorted(next_nodes)[:110],
                                   "truncated":len(next_nodes)>110})
                    active=next_nodes
                    if not active:break
                found[ed]["targets"][title]={
                    "seed_function":seed,"seed_defined":seed in defs[ed],
                    "direct_call_samples":samples[ed].get(seed,[]),
                    "reverse_callgraph":layers}
        return {
            "stage":"PRE205_INPUT_WRAPPER_REVERSE_CALLGRAPH_READONLY","status":"AUDIT_OK",
            "backup_sha256":digest,"backup_verified":True,"read_only":True,
            "apk_built":False,"source_modified":False,"signer_accessed":False,
            "saves_accessed":False,"v36_modified":False,
            "editions":found,
            "limits":[
                "Direct generated-code calls only; indirect/dynamic calls may be absent",
                "Ancestor routines are input-handling candidates, not verified nitro or Speedbreaker meters",
                "No economy/career balance trace performed",
                "PRE99 static snapshot, not an exact running-V36 trace",
                "Do not patch guessed addresses"
            ]
        }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    if not args.run_id.isdecimal():raise ValueError("Non-numeric run ID")
    OUT.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE205_INPUT_WRAPPER_REVERSE_CALLGRAPH_READONLY",
            "status":"FAILED","read_only":True,"apk_built":False,
            "source_modified":False,"signer_accessed":False}
    try:result=parse()
    except Exception as exc:result["error_type"]=type(exc).__name__
    result["run_id"]=args.run_id
    (OUT/"PRE205_REVERSE_INPUT_CALLGRAPH.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE205_STATUS",result["status"],"BACKUP",result.get("backup_verified",False))
    for ed,v in result.get("editions",{}).items():
        print("PRE205_ED",ed,"DEFS",v["defined_functions"],"CALLS",v["totals"]["direct_calls"])
        for k,t in v["targets"].items():
            print("PRE205_TARGET",ed,k,t["seed_function"],"LAYERS",
                  [(layer["depth"],layer["count"]) for layer in t["reverse_callgraph"]])
    if result["status"]!="AUDIT_OK":print("PRE205_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
