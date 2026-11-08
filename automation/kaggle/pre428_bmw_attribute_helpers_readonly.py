#!/usr/bin/env python3
"""PRE428: read-only attribute helper calls underneath BMW performance list."""
import argparse,hashlib,json,re,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
OUT=Path("/tmp/nfsmw-pre428/report.json")
ROOT="workspace/nativo/app/generated/default/"
FUNCS=("sub_8214B858","sub_8214EDA8")
MAX_LINES=340
def audit():
 with tempfile.TemporaryDirectory(prefix="pre428_") as d:
  archive=Path(d)/"pre99.tar.gz";download(drive_client(),archive)
  digest,_,size=sha_file(archive)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 fingerprint mismatch")
  result={};scanned=0
  with tarfile.open(archive,"r:gz") as tar:
   for m in tar:
    path=m.name.lstrip("./")
    if not m.isfile() or not path.startswith(ROOT) or not re.fullmatch(r"nfsmw_recomp\.[0-9]+\.cpp",path[len(ROOT):]):continue
    if m.size>7_000_000:raise ValueError("oversized codegen file")
    f=tar.extractfile(m)
    if f is None:continue
    data=f.read();scanned+=1
    for fn in FUNCS:
     if ("DEFINE_REX_FUNC("+fn+")").encode() not in data:continue
     if fn in result:raise ValueError("duplicate function "+fn)
     lines=body_for_function(data.decode("utf-8"),fn).splitlines()
     calls=[{"line":i+1,"source":line.strip()[:170]} for i,line in enumerate(lines)
            if re.search(r"^\s*(?:__imp__)?sub_[0-9A-Fa-f]{8}\(ctx,\s*base\);",line)]
     snapshots=[{"line":i+1,"text":line.strip()[:200]} for i,line in enumerate(lines[:MAX_LINES])]
     result[fn]={"file":path,"sha256":hashlib.sha256(data).hexdigest(),"lines":len(lines),
                 "calls":calls[:100],"body_excerpt":snapshots,"truncated":len(lines)>MAX_LINES}
  if set(result)!=set(FUNCS):raise ValueError("missing targets "+repr(set(FUNCS)-set(result)))
  return {"status":"AUDIT_OK","archive_sha256":digest,"scanned_cpp":scanned,"functions":result,
    "classification":"Code inspection only; attribute call semantics and selected vehicle correlation not proven",
    "source_modified":False,"apk_built":False,"save_modified":False,"signing_accessed":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:240]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE428_STATUS",r["status"],"ERROR",r.get("error","none"))
 for fn,entry in r.get("functions",{}).items():
  print("PRE428_FUNCTION",fn,"PATH",entry["file"],"SHA256",entry["sha256"],"LINES",entry["lines"],"TRUNCATED",entry["truncated"])
  for call in entry["calls"]:print("PRE428_CALL",fn,call["line"],call["source"])
  for line in entry["body_excerpt"]:print("PRE428_BODY",fn,line["line"],line["text"])
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
