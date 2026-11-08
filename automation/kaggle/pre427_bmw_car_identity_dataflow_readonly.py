#!/usr/bin/env python3
"""PRE427 read-only: inspect guest argument/owner provenance of performance list count."""
import argparse,hashlib,json,re,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
OUT=Path("/tmp/nfsmw-pre427/report.json")
ROOT="workspace/nativo/app/generated/default/"
FIXED={
 "entry":("nfsmw_recomp.15.cpp","414803e217226952833caf347a1ef61dde781a01a8a518262f77196bbc9a0d3a","sub_8256B440"),
 "helper":("nfsmw_recomp.28.cpp","11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad","sub_823E5988"),
 "builder":("nfsmw_recomp.57.cpp","a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c","sub_8256F818"),
}
CALLEE="sub_8256CB60"
def collect(lines,selection):
 return [{"line":i+1,"text":line.strip()[:220]} for i,line in enumerate(lines) if selection(i+1,line)]
def analysis():
 with tempfile.TemporaryDirectory(prefix="pre427_") as d:
  arch=Path(d)/"pre99.tar.gz";download(drive_client(),arch)
  digest,_,size=sha_file(arch)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 SHA/size mismatch")
  results={}; found_callee=[]
  with tarfile.open(arch,"r:gz") as tar:
   for m in tar:
    if not m.isfile() or not m.name.lstrip("./").startswith(ROOT):continue
    path=m.name.lstrip("./")
    if not re.fullmatch(r"nfsmw_recomp\.[0-9]+\.cpp",path[len(ROOT):]):continue
    if m.size>7_000_000:raise ValueError("Oversized generated C++ member")
    f=tar.extractfile(m)
    if f is None:continue
    raw=f.read()
    for label,(filename,expected,fn) in FIXED.items():
     if path!=ROOT+filename:continue
     actual=hashlib.sha256(raw).hexdigest()
     if actual!=expected:raise ValueError("Fixed source hash mismatch: "+label)
     lines=body_for_function(raw.decode("utf-8"),fn).splitlines()
     sel=(lambda i,line: True) if label=="helper" else (
       (lambda i,line: i<=150 or i>=220) if label=="entry" else
       (lambda i,line: i<=135 or i>=192))
     results[label]={"path":path,"source_sha256":actual,"function":fn,
      "body_length":len(lines),"body_excerpt":collect(lines,sel)}
    if ("DEFINE_REX_FUNC("+CALLEE+")").encode() in raw:
     found_callee.append((path,raw))
  if set(results)!=set(FIXED):raise ValueError("Missing pinned owner source")
  if len(found_callee)!=1:raise ValueError("Expected one callee definition, found "+str(len(found_callee)))
  path,raw=found_callee[0]
  lines=body_for_function(raw.decode("utf-8"),CALLEE).splitlines()
  results["callee"]={"path":path,"source_sha256":hashlib.sha256(raw).hexdigest(),"function":CALLEE,
                     "body_length":len(lines),"body_excerpt":collect(lines,lambda i,line: i<=260)}
  return {"status":"AUDIT_OK","stage":"PRE427_BMW_CAR_IDENTITY_DATAFLOW_READONLY",
          "archive_sha256":digest,"sources":results,
          "car_identification_proven":False,"runtime_count_measured":False,
          "notes":"Read-only PPC trace; no equivalence between guest address and selected vehicle assumed",
          "source_modified":False,"apk_built":False,"save_modified":False,"signing_accessed":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=analysis()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("PRE427_STATUS",r["status"],"ERROR",r.get("error","none"))
 for label,e in r.get("sources",{}).items():
  print("PRE427_FUNCTION",label,e["function"],"FILE",e["path"],"LINES",e["body_length"],"SHA256",e["source_sha256"])
  for row in e["body_excerpt"]:print("PRE427_BODY",label,row["line"],row["text"])
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
