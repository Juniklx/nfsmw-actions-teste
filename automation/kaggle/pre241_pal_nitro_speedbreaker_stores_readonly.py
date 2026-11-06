#!/usr/bin/env python3
"""PRE241: locate PAL generated float stores related to nitro/speedbreaker.

Read-only structural candidates. Float offsets alone are not semantic proof.
"""
from __future__ import annotations
import hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre241/NFSMW_PRE241_PAL_NITRO_SPEEDBREAKER_FLOAT_STORES.json")
FILE=re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.\d+\.cpp$")
DEF=re.compile(r"\bDEFINE_REX_FUNC\((sub_[A-Fa-f0-9]{8})\)")
FLOAT_STORE=re.compile(r"^\s*//\s*stfs\s+f\d+,\s*(132|252)\(r31\)\s*$",re.I)
HOST_STORE=re.compile(r"\bREX_STORE_(?:F32|U32)\s*\(")
FLOAT_LOAD=re.compile(r"^\s*//\s*lfs\s+f\d+,\s*(132|252)\(r31\)\s*$",re.I)
NITRO_NAMED="sub_82424AF0"
MAX_BYTES=3_000_000

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 report={"stage":"PRE241_PAL_NITRO_SPEEDBREAKER_CANDIDATES",
         "status":"FAILED","phase":"START","apk_built":False,"source_modified":False,
         "saves_modified":False,"signing_accessed":False,"cheat_activated":False,
         "game_not_executed":True}
 try:
  with tempfile.TemporaryDirectory(prefix="nfsmw_pre241_") as td:
   report["phase"]="VERIFY_PINNED_PRE99"
   archive=Path(td)/"pre99.tar.gz"
   download(drive_client(),archive)
   sha,_,size=sha_file(archive)
   if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("Snapshot fingerprint mismatch")
   report["pre99_verified"]=True
   report["phase"]="SCAN_PAL_CPP"
   shards=0; definitions=0; candidates=[]
   with tarfile.open(archive,"r:gz") as tf:
    for m in tf:
     name=m.name.lstrip("./")
     if not m.isfile() or not FILE.fullmatch(name):continue
     shards+=1
     if m.size>MAX_BYTES:raise ValueError("Unexpected generated shard size")
     f=tf.extractfile(m)
     if f is None:raise ValueError("Cannot read generated shard")
     b=f.read()
     s=b.decode("utf-8","replace")
     funcs=list(DEF.finditer(s));definitions+=len(funcs)
     for i,fn in enumerate(funcs):
      function=fn.group(1)
      body=s[fn.start():funcs[i+1].start() if i+1<len(funcs) else len(s)]
      if "stfs" not in body or ("132(r31)" not in body and "252(r31)" not in body):continue
      lines=body.splitlines()
      selected=[]
      for ix,line in enumerate(lines):
       hit=FLOAT_STORE.match(line)
       if not hit:continue
       window=lines[max(0,ix-8):min(len(lines),ix+7)]
       preceding_load=[x.strip()[:180] for x in lines[max(0,ix-30):ix] if FLOAT_LOAD.match(x)]
       following_macro=[x.strip()[:220] for x in lines[ix+1:min(len(lines),ix+5)] if HOST_STORE.search(x)]
       selected.append({"field_offset":int(hit.group(1)),
                        "function_line":ix+1,
                        "guest_opcode":line.strip()[:100],
                        "existing_float_loads":preceding_load[-6:],
                        "host_store":following_macro[:2],
                        "excerpt":[x.strip()[:200] for x in window]})
      if selected:
       candidates.append({"function":function,
                         "file":name,
                         "file_sha256":hashlib.sha256(b).hexdigest(),
                         "store_sites":selected[:18],
                         "truncated":len(selected)>18})
   report["pal_cpp_shards"]=shards
   report["pal_function_definitions"]=definitions
   report["candidates_total"]=len(candidates)
   report["field_252_candidates"]=sum(any(z["field_offset"]==252 for z in c["store_sites"]) for c in candidates)
   report["field_132_candidates"]=sum(any(z["field_offset"]==132 for z in c["store_sites"]) for c in candidates)
   report["known_nitro_function_found"]=any(c["function"]==NITRO_NAMED for c in candidates)
   # Prioritize known numeric function but never assign other results semantic labels.
   candidates.sort(key=lambda c:(c["function"]!=NITRO_NAMED,
                  -sum(v["field_offset"]==252 for v in c["store_sites"]),
                  -sum(v["field_offset"]==132 for v in c["store_sites"]),c["function"]))
   report["candidates"]=candidates[:50]
   report["candidate_list_truncated"]=len(candidates)>50
   report["limits"]=[
      "Field offset 252 is consistent with the USA nitro candidate, and 132 with USA Speedbreaker; this is not a PAL identification proof.",
      "The PAL functions need control-flow/data-flow correlation with the USA verified paths and runtime game tests.",
      "No patch, memory modification, signing, saves, APK or trainer execution was performed.",
   ]
   report["phase"]="COMPLETE"
   report["status"]="AUDIT_OK" if shards>=100 and report["field_132_candidates"] and report["field_252_candidates"] else "NEEDS_REVIEW"
 except Exception as exc:
  report["exception_type"]=type(exc).__name__
  report["failed_phase"]=report["phase"]
  print("PRE241_ERROR",type(exc).__name__,report["phase"])
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("PRE241_STATUS",report["status"])
 print("PRE241_SHARDS",report.get("pal_cpp_shards",0),"CANDIDATES",report.get("candidates_total",0))
 print("PRE241_252",report.get("field_252_candidates",0),"PRE241_132",report.get("field_132_candidates",0))
 return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
