#!/usr/bin/env python3
"""PRE242 read-only data-flow windows for PAL Nitro / Speedbreaker floating stores.

This audits existing PPC loads and bits conversions; does not create a patch.
"""
from __future__ import annotations
import hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
OUT=Path("/tmp/nfsmw-pre242/NFSMW_PRE242_PAL_FLOAT_DATAFLOW_WINDOWS.json")
TARGETS={
"nitro":{
    "function":"sub_82424AF0",
    "file":"workspace/nativo/app/generated/default/nfsmw_recomp.66.cpp",
    "sha256":"eec9b82e51bbfcb573cd0f965e3ed7639bbbd291b285f9fc6d5a7d1e77cd735f",
    "offset":252,"expected_stores":5
},
"speedbreaker":{
    "function":"sub_8246C2F0",
    "file":"workspace/nativo/app/generated/default/nfsmw_recomp.24.cpp",
    "sha256":"e5cf7f0f0b7369615432845bbbfdcf0786f6a4646b0872dfb037fc6a6c320b71",
    "offset":132,"expected_stores":3
}}
FLOAT=re.compile(r"^\s*//\s*stfs\s+f\d+,\s*(132|252)\(r31\)\s*$",re.I)
HOST=re.compile(r"^\s*REX_STORE_U32\s*\(\s*r31\.u32\s*\+\s*(132|252)\s*,\s*temp\.u32\s*\)\s*;\s*$")
FLOAD=re.compile(r"^\s*//\s*lfs\s+f\d+,\s*(132|252)\(r31\)\s*$",re.I)
TEMP=re.compile(r"\btemp\.(?:u32|f32|f64)\b")

def scan(txt,spec):
    body=body_for_function(txt,spec["function"])
    lines=body.splitlines()
    matches=[]
    for i,line in enumerate(lines):
        m=FLOAT.match(line)
        if not m or int(m.group(1))!=spec["offset"]:continue
        if i+1>=len(lines) or not HOST.match(lines[i+1]):
            raise ValueError("Guest float store not followed by expected host write")
        # Gather existing guest loads; DO NOT insert any load.
        previous=lines[max(0,i-100):i]
        exact_loads=[{"line_relative":i-100+k if i>=100 else k,
           "text":v.strip()[:190]} for k,v in enumerate(previous)
           if FLOAD.match(v) and int(FLOAD.match(v).group(1))==spec["offset"]]
        matches.append({
            "ordinal":len(matches)+1,
            "comment_line":i+1,
            "opcode":line.strip()[:120],
            "original_host_store":lines[i+1].strip()[:180],
            "preexisting_same_field_loads":exact_loads[-12:],
            "temp_neighborhood":[{"relative_line":k+1,"text":v.strip()[:220]}
                for k,v in enumerate(lines[max(0,i-16):min(len(lines),i+5)],
                                     max(0,i-16)) if TEMP.search(v)][:15],
            "prior_window":[{"relative_line":k+1,"text":v.strip()[:240]}
                for k,v in enumerate(lines[max(0,i-35):i+2],max(0,i-35))],
            "no_extra_memory_load":True,
        })
    if len(matches)!=spec["expected_stores"]:
        raise ValueError("Expected float store count mismatch")
    return {"function":spec["function"],"field_offset":spec["offset"],
            "store_count":len(matches),"stores":matches}

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 r={"stage":"PRE242_PAL_FLOAT_DATAFLOW_READONLY","status":"FAILED",
    "phase":"START","apk_built":False,"source_modified":False,
    "signing_accessed":False,"saves_modified":False,
    "game_executed":False,"cheats_activated":False}
 try:
  with tempfile.TemporaryDirectory(prefix="nfsmw_pre242_") as t:
   r["phase"]="VERIFY_PRE99"
   p=Path(t)/"snapshot.tar.gz"
   download(drive_client(),p)
   sha,_,size=sha_file(p)
   if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("Snapshot SHA mismatch")
   r["pre99_verified"]=True
   r["phase"]="EXTRACT_READ_ONLY_WINDOWS"
   required={v["file"] for v in TARGETS.values()}
   sources={}
   with tarfile.open(p,"r:gz") as tar:
    for m in tar:
     name=m.name.lstrip("./")
     if not m.isfile() or name not in required:continue
     if m.size>3_000_000:raise ValueError("Oversized codegen")
     f=tar.extractfile(m)
     if f is None:raise ValueError("Failed read")
     b=f.read()
     digest=hashlib.sha256(b).hexdigest()
     spec=next(v for v in TARGETS.values() if v["file"]==name)
     if digest!=spec["sha256"]:raise ValueError("Source hash mismatch")
     sources[name]=b.decode("utf-8","replace")
   if len(sources)!=len(required):raise ValueError("Missing source")
   r["resources"]={}
   for kind,spec in TARGETS.items():
    res=scan(sources[spec["file"]],spec)
    res["file"]=spec["file"]
    res["sha256"]=spec["sha256"]
    r["resources"][kind]=res
   r["total_stores"]=sum(x["store_count"] for x in r["resources"].values())
   r["limitations"]=[
      "The floating-point stores are structural candidates; precise consumption semantics are not established.",
      "A prior guest lfs and host temp conversion may be used only after register dataflow review.",
      "No generated files were patched; no nondecrease float policy was injected.",
      "Do not extrapolate PAL offsets to USA addresses or assume a trainer TU1 match."
   ]
   r["phase"]="COMPLETE"
   r["status"]="AUDIT_OK" if r["total_stores"]==8 else "NEEDS_REVIEW"
 except Exception as e:
  r["failed_phase"]=r["phase"]
  r["error_type"]=type(e).__name__
  print("PRE242_ERROR",type(e).__name__,r["phase"])
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("PRE242_STATUS",r["status"])
 print("PRE242_TOTAL_STORES",r.get("total_stores",0))
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
