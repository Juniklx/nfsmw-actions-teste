#!/usr/bin/env python3
"""PRE243: read-only survey of maintained hooks, CVAR and logging integration.

No generated file edits. No codegen rewrite, game build or Android signing.
"""
from __future__ import annotations
import hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre243/NFSMW_PRE243_HOOK_LOGGING_CVAR_INTEGRATION_AUDIT.json")
FILES={
 "workspace/nativo/sdk/include/rex/hook.h",
 "workspace/nativo/sdk/include/rex/logging/macros.h",
 "workspace/nativo/sdk/include/rex/logging/api.h",
 "workspace/nativo/app/src/nfsmw_recortes_carrera.cpp",
 "workspace/nativo/app/generated/default/nfsmw_pch.h",
 "workspace/nativo/app/generated/default/sources.cmake",
 "workspace/nativo/app/CMakeLists.txt",
}
SYMBOLS={
 "hook":["REX_HOOK_RAW","REX_EXTERN","REX_HOOK","REX_ORIGINAL"],
 "cvar":["REXCVAR_DEFINE_BOOL","REXCVAR_GET","REXCVAR_DEFINE","REXCVAR_REGISTER"],
 "logging":["REXLOG","REX_LOG","LOG_INFO","LOG_WARN","LOG_ERROR","rex::log","REX_TRACE","REX_DEBUG"],
 "memory":["REX_STORE_U32","REX_LOAD_U32","REX_PHYS_HOST_OFFSET"],
 "build":["add_library(","target_sources(","sources.cmake","DO NOT EDIT"],
}
def find_excerpt(lines,terms,span=2,limit=100):
 hits=[]
 for i,line in enumerate(lines):
  if any(t in line for t in terms):
   hits.append(i)
 keep=set()
 for i in hits[:limit]:
  keep.update(range(max(0,i-span),min(len(lines),i+span+1)))
 return {"matches":len(hits),
    "match_line_numbers":[i+1 for i in hits[:60]],
    "excerpts":[{"line":i+1,"text":lines[i][:260]} for i in sorted(keep)[:450]]}
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 r={"stage":"PRE243_MAINTAINED_INTEGRATION_READONLY",
    "status":"FAILED","phase":"START","apk_built":False,"source_modified":False,
    "signer_accessed":False,"saves_touched":False,"cheats_enabled":False}
 try:
  with tempfile.TemporaryDirectory(prefix="nfsmw_pre243_") as td:
   r["phase"]="PIN_PRE99"
   archive=Path(td)/"snapshot.tar.gz"
   download(drive_client(),archive)
   sha,_,size=sha_file(archive)
   if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 digest mismatch")
   r["verified_pre99"]=True
   r["phase"]="SCAN_REFERENCE_SOURCES"
   items={}
   codegen_names=[]
   with tarfile.open(archive,"r:gz") as tf:
    for m in tf:
     name=m.name.lstrip("./")
     if any(k in name.lower() for k in ("rexglue","codegen","recompiler")) and len(codegen_names)<60:
      codegen_names.append(name[:250])
     if not m.isfile() or name not in FILES:continue
     if m.size>3_000_000:raise ValueError("Source member exceeds limit")
     f=tf.extractfile(m)
     if f is None:raise ValueError("Cannot read source")
     raw=f.read();lines=raw.decode("utf-8","replace").splitlines()
     matching={}
     for label,terms in SYMBOLS.items():
      matching[label]=find_excerpt(lines,terms)
     items[name]={"sha256":hashlib.sha256(raw).hexdigest(),
        "lines_total":len(lines),"search":matching,
        "beginning":[{"line":i+1,"text":line[:260]} for i,line in enumerate(lines[:45])]
        if name.endswith(("logging/macros.h","logging/api.h","hook.h")) else []}
   r["files"]=items
   r["missing"]=sorted(FILES-set(items))
   r["codegen_like_names"]=codegen_names
   r["limits"]=[
    "A declared hook API does not prove per-instruction interception or nonintrusive rollback.",
    "A CVAR declaration in maintained code does not automatically control generated stores.",
    "No generated files were changed or built; any proposed integration needs a separate syntax/build test.",
    "Do not read or write guest memory outside original game operations.",
   ]
   r["phase"]="COMPLETE"
   r["status"]="AUDIT_OK" if "workspace/nativo/sdk/include/rex/hook.h" in items and "workspace/nativo/app/src/nfsmw_recortes_carrera.cpp" in items else "INCOMPLETE"
 except Exception as e:
  r["failed_phase"]=r["phase"]
  r["error_type"]=type(e).__name__
  print("PRE243_ERROR",type(e).__name__,r["phase"])
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("PRE243_STATUS",r["status"],"FILES",len(r.get("files",{})))
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
