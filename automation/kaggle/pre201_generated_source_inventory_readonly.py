#!/usr/bin/env python3
"""PRE201: inventory generated recompilation sources from verified PRE99.
Read-only, no builds, no patching, no key or save access.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download
OUT=Path("/tmp/nfsmw-pre201")
GENERATED_PREFIXES=("workspace/nativo/app/generated/","workspace/nativo/app_usa/generated/")
TARGET_NAMES={"sources.cmake","CMakeLists.txt","functions.h","function_map.h","imports.h","config.json","project.json","main.cpp"}
PAT=re.compile(rb"(?i)nitro|nitrous|speedbreaker|speed.break|money|cash|bankroll|career|gameprofile")
def sha(b): return hashlib.sha256(b).hexdigest()
def audit():
    result={"stage":"PRE201_RECOMPILED_GAME_SOURCES_INVENTORY",
            "status":"NOT_VALIDATED","read_only":True,"build":False,
            "source_modified":False,"key_accessed":False,
            "original_apk_preserved":True}
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre201_") as temp:
        archive=Path(temp)/"PRE99.tar.gz"
        download(drive_client(),archive)
        digest,_,count=sha_file(archive)
        if digest!=EXPECTED_SHA256 or count!=EXPECTED_BYTES:
            raise ValueError("PRE99 mismatch")
        result["backup_sha256"]=digest
        result["backup_verified"]=True
        agg={x:{"files":0,"bytes_total":0,"extensions":collections.Counter(),
                 "example_paths":[],"largest":[],"potential_symbol_files":[],
                 "content_keyword_samples":[]} for x in ("pal","usa")}
        matches_in_filenames=[]
        text_read_bytes=0
        text_read_files=0
        with tarfile.open(archive,"r:gz") as t:
            for m in t:
                if not m.isfile():continue
                name=m.name.lstrip("./")
                if not name.startswith(GENERATED_PREFIXES):continue
                edition="usa" if name.startswith(GENERATED_PREFIXES[1]) else "pal"
                section=agg[edition]
                section["files"]+=1
                section["bytes_total"]+=m.size
                section["extensions"][Path(name).suffix.lower() or "(none)"]+=1
                if len(section["example_paths"])<55:
                    section["example_paths"].append({"path":name,"size":m.size})
                if "nitro" in name.lower() or "speedbreak" in name.lower() or "cash" in name.lower():
                    matches_in_filenames.append(name)
                largest=section["largest"]
                largest.append({"name":name,"size":m.size})
                largest.sort(key=lambda x:x["size"],reverse=True)
                del largest[15:]
                is_manifest=(
                    Path(name).name in TARGET_NAMES or
                    re.search(r"symbol|function|manifest|address|map|import|recomp",Path(name).name,re.I) is not None
                )
                if is_manifest and len(section["potential_symbol_files"])<70:
                    section["potential_symbol_files"].append({"name":name,"size":m.size})
                ext=Path(name).suffix.lower()
                # Analyze only bounded text manifests and a small sample of generated code.
                read_this=is_manifest or (ext in (".cpp",".h",".c",".txt") and
                    len(section["content_keyword_samples"])<8 and
                    text_read_files<40 and m.size<350000)
                if not read_this or m.size>2000000 or text_read_bytes+m.size>34000000:
                    continue
                f=t.extractfile(m)
                if f is None:continue
                b=f.read()
                if len(b)!=m.size:raise ValueError("Truncated generated source read")
                text_read_bytes+=len(b)
                text_read_files+=1
                hits=list(PAT.finditer(b))[:8]
                if is_manifest or hits:
                    snippet={
                        "name":name,"sha256":sha(b),"bytes":len(b),
                        "has_keyword_hits":bool(hits),
                        "keyword_excerpt_offsets":[match.start() for match in hits],
                        "first_lines":[line[:170] for line in b.decode("utf-8","replace").splitlines()[:18]]
                    }
                    if len(section["content_keyword_samples"])<50:
                        section["content_keyword_samples"].append(snippet)
        result["generated"]={}
        for ed,a in agg.items():
            a["extensions"]=dict(a["extensions"])
            result["generated"][ed]=a
        result["keyword_filenames"]=matches_in_filenames[:100]
        result["bounded_text_files_read"]=text_read_files
        result["bounded_text_bytes_read"]=text_read_bytes
        result["important_limitation"]="Not exhaustive symbol search; bounded inventory and sample content only."
        result["status"]="AUDIT_OK"
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    if not args.run_id.isdecimal():
        raise ValueError("numeric run id required")
    OUT.mkdir(parents=True,exist_ok=True)
    r={"stage":"PRE201_RECOMPILED_GAME_SOURCES_INVENTORY","status":"FAILED",
       "read_only":True,"build":False,"source_modified":False,"key_accessed":False}
    try:
        r=audit()
        r["run_id"]=args.run_id
    except Exception as error:
        r["error_type"]=type(error).__name__
    (OUT/"PRE201_GENERATED_SOURCES_READONLY.json").write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE201",r["status"],"BACKUP",r.get("backup_verified"),
          "PAL",r.get("generated",{}).get("pal",{}).get("files"),
          "USA",r.get("generated",{}).get("usa",{}).get("files"),
          "READ",r.get("bounded_text_files_read"))
    if r.get("error_type"):print("PRE201_ERROR_TYPE",r["error_type"])
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
