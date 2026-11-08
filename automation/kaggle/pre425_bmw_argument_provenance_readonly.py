#!/usr/bin/env python3
"""PRE425 — bounded, read-only argument provenance for BMW level instrumentation."""
import argparse,hashlib,json,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
OUT=Path("/tmp/nfsmw-pre425/report.json")
ROOT="workspace/nativo/app/generated/default/"
FILES={
 "entry":("nfsmw_recomp.15.cpp","414803e217226952833caf347a1ef61dde781a01a8a518262f77196bbc9a0d3a","sub_8256B440"),
 "level_helper":("nfsmw_recomp.28.cpp","11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad","sub_823E5988"),
 "list_builder":("nfsmw_recomp.57.cpp","a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c","sub_8256F818"),
 "setup":("nfsmw_recomp.11.cpp","0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3","sub_82582F70"),
}
TARGETS={
 "entry":["REX_STORE_U32(r31.u32 + 8, ctx.r11.u32)","REX_STORE_U32(r31.u32 + 4, r29.u32)"],
 "level_helper":["REX_FUNC_PROLOGUE()","return;"],
 "list_builder":["sub_823E5988(ctx, base)","sub_8256CB60(ctx, base)","REX_STORE_U32(r31.u32 + 32, r27.u32)"],
 "setup":["sub_8256F818(ctx, base)","REX_LOAD_U32(ctx.r1.u32 + 96)"],
}
def window(lines,index,before=14,after=12):
 return [{"line":i+1,"text":lines[i].strip()[:220]} for i in range(max(0,index-before),min(len(lines),index+after+1))]
def audit():
 with tempfile.TemporaryDirectory(prefix="pre425_") as temp:
  archive=Path(temp)/"pre99.tar.gz";download(drive_client(),archive)
  digest,_,size=sha_file(archive)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 fingerprint mismatch")
  found={}
  with tarfile.open(archive,"r:gz") as tar:
   for label,(filename,sha,function) in FILES.items():
    path=ROOT+filename
    member=next((m for m in tar if m.isfile() and m.name.lstrip("./")==path),None)
    if member is None or member.size>7_000_000:raise ValueError("Missing or oversized "+path)
    f=tar.extractfile(member)
    if f is None:raise ValueError("Cannot extract "+path)
    data=f.read()
    if hashlib.sha256(data).hexdigest()!=sha:raise ValueError("Source hash mismatch "+path)
    lines=body_for_function(data.decode("utf-8"),function).splitlines()
    matches={}
    for target in TARGETS[label]:
     locations=[i for i,line in enumerate(lines) if target in line]
     matches[target]=[{"relative_line":i+1,"window":window(lines,i)} for i in locations[:5]]
    found[label]={"source":path,"sha256":sha,"function":function,"body_lines":len(lines),"matches":matches}
  callcount=len(found["list_builder"]["matches"]["sub_823E5988(ctx, base)"])
  setupcount=len(found["setup"]["matches"]["sub_8256F818(ctx, base)"])
  entrycount=len(found["entry"]["matches"]["REX_STORE_U32(r31.u32 + 8, ctx.r11.u32)"])
  valid=callcount==2 and setupcount==1 and entrycount==1
  return {"stage":"PRE425_BMW_ARGUMENT_PROVENANCE_READONLY",
   "status":"AUDIT_OK" if valid else "NEEDS_REVIEW",
   "pre99_sha256":digest,"getmaxlevel_candidate_calls":callcount,
   "list_builder_call_from_setup":setupcount,"entry_pvehicle_store":entrycount,
   "source_windows":found,
   "proven_tuning_entry_vehicle_argument_equals_level_helper_r3":False,
   "proven_bmw_model_at_level_helper":False,
   "caution":"PRE271/PRE274 host mock does not establish runtime guest pointer equality. Compare exact r3/r4 preparation at each callsite.",
   "apk_built":False,"source_modified":False,"save_modified":False,"signing_accessed":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE425_STATUS",r["status"],"ERROR",r.get("error","none"))
 print("PRE425_CALL_COUNTS",r.get("getmaxlevel_candidate_calls"),r.get("list_builder_call_from_setup"),r.get("entry_pvehicle_store"))
 for label,entry in r.get("source_windows",{}).items():
  print("PRE425_FUNCTION",label,entry["function"],"LINES",entry["body_lines"],"SHA256",entry["sha256"])
  for term,sites in entry["matches"].items():
   print("PRE425_TARGET",label,term,"HITS",len(sites))
   for site in sites:
    print("PRE425_SITE",label,term,"LINE",site["relative_line"])
    for ln in site["window"]:
     print("PRE425_LINE",label,ln["line"],ln["text"])
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
