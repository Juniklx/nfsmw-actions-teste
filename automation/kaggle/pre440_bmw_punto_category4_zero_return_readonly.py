#!/usr/bin/env python3
"""PRE440: SHA-pinned read-only PPC trace of observed category=4/count=0 route.

Extract only relevant function windows from authenticated PRE99 archive. Never
call guest code, inspect user saves, change APK, create patches or sign.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
OUT=Path("/tmp/nfsmw-pre440/report.json")
ROOT="workspace/nativo/app/generated/default/"
TARGETS={
 "list_caller":("nfsmw_recomp.11.cpp","0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3","sub_82582F70"),
 "list_builder":("nfsmw_recomp.57.cpp","a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c","sub_8256F818"),
 "attr_lookup":("nfsmw_recomp.28.cpp","11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad","sub_823E5988"),
 "category_bounds":("nfsmw_recomp.101.cpp","4ca7b1a401ab9a0ea4e07f57e011a8750461b289aa4031f5b9d3801bb227086c","sub_8256CB60"),
 "perf_menu":("nfsmw_recomp.39.cpp","ac9c0f8f5d69a59c390010227263ece19ae4688ef4bc4d30d16ed622879bd0e4","sub_825767F0"),
}
MAX_EXCERPTS=330
def sha(data):return hashlib.sha256(data).hexdigest()
def clip(lines,lo,hi):
 return [{"n":i+1,"s":lines[i].strip()[:240]} for i in range(max(0,lo-1),min(len(lines),hi))]
def function(src,fn):
 body=body_for_function(src,fn)
 if not body.startswith("DEFINE_REX_FUNC("+fn+") {"):raise ValueError("function parser mismatch")
 return body.splitlines()
def extract(lines,label):
 if label in ("attr_lookup","list_builder","category_bounds"):
  return clip(lines,1,len(lines))
 if label=="list_caller":
  sites=[i+1 for i,s in enumerate(lines) if "sub_8256F818(ctx, base);" in s]
  if len(sites)!=1:raise ValueError("Expected unique builder call in caller")
  idx=sites[0]
  selected=clip(lines,1,115)+clip(lines,idx-100,idx+105)
  seen=set();out=[]
  for x in selected:
   if x["n"] not in seen:out.append(x);seen.add(x["n"])
  return out
 if label=="perf_menu":
  focus=[i+1 for i,s in enumerate(lines) if any(k in s for k in
         ("__imp__sub_82575370(ctx, base)", "sub_8256F9D8(ctx, base)",
          "ctx.r7.s64 = 513","ctx.r7.s64 = 514","ctx.r7.s64 = 515",
          "ctx.r7.s64 = 516","ctx.r7.s64 = 517","ctx.r7.s64 = 518"))]
  indices=set()
  for n in focus:
   for i in range(max(1,n-6),min(len(lines),n+8)+1):indices.add(i)
  return [{"n":i,"s":lines[i-1].strip()[:240]} for i in sorted(indices)][:MAX_EXCERPTS]
 raise ValueError("Unknown label")
def audit():
 with tempfile.TemporaryDirectory(prefix="nfsmw_pre440_") as d:
  tarpath=Path(d)/"pre99.tar.gz";download(drive_client(),tarpath)
  arc_sha,_,arc_len=sha_file(tarpath)
  if (arc_sha,arc_len)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 SHA/size mismatch")
  found={}
  with tarfile.open(tarpath,"r:gz") as arc:
   for member in arc:
    name=member.name.lstrip("./")
    if not member.isfile() or not name.startswith(ROOT):continue
    if not re.fullmatch(r"nfsmw_recomp\.[0-9]+\.cpp",name[len(ROOT):]):continue
    matching=[(k,v) for k,v in TARGETS.items() if ROOT+v[0]==name]
    if not matching:continue
    if member.size>7_000_000:raise ValueError("Oversized source")
    fp=arc.extractfile(member)
    if fp is None:raise ValueError("Unreadable source")
    raw=fp.read();digest=sha(raw)
    for label,(filename,expected,fn) in matching:
     if digest!=expected:raise ValueError("PRE99 source digest mismatch: "+label)
     lines=function(raw.decode("utf-8"),fn)
     view=extract(lines,label)
     found[label]={"path":name,"function":fn,"sha256":digest,
                  "function_lines":len(lines),"windows":view}
  if set(found)!=set(TARGETS):raise ValueError("Missing pinned sources")
  a=found["attr_lookup"]["windows"];b=found["list_builder"]["windows"]
  # These facts are local to code. Do not assert C++ symbol names for high-level APIs.
  if sum("ctx.r3.s64 = 0;" in row["s"] for row in a)<2:
   raise ValueError("Cannot establish helper has multiple zero-return branches")
  if sum("sub_823E5988(ctx, base);" in row["s"] for row in b)!=2:
   raise ValueError("Builder call count unexpected")
  lines=found["list_caller"]["windows"]
  if sum("sub_8256F818(ctx, base);" in row["s"] for row in lines)!=1:
   raise ValueError("Caller callsite missing in window")
  return {"status":"AUDIT_OK","stage":"PRE440_BMW_PUNTO_ZERO_RETURN_PAL_READONLY",
          "pre99_sha256":arc_sha,"sources":found,
          "user_runtime_observations":{"category":4,"punto_candidate":4,"bmw_candidate":0,
           "source":"PRE438; this workflow does not reread user logs"},
          "conclusion_proven":False,"category4_equates_engine_proven":False,
          "any_guest_code_executed":False,"any_source_written":False,
          "apk_built":False,"signer_accessed":False,"save_accessed":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:220]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("PRE440_STATUS",r["status"],"ERROR",r.get("error","none"))
 for k,v in r.get("sources",{}).items():
  print("PRE440_FN",k,v["function"],"SOURCE_SHA",v["sha256"],"LINES",v["function_lines"])
  for row in v["windows"]:print("PRE440_CODE",k,row["n"],row["s"])
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
