#!/usr/bin/env python3
"""PRE410: locate BMW performance helper across authenticated PRE99 generated files; read only."""
import argparse,hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
OUT=Path("/tmp/nfsmw-pre410/report.json")
TARGET="sub_8256F818"
NEEDLE=("DEFINE_REX_FUNC("+TARGET+")").encode()
CALL=re.compile(r"\b(?:__imp__)?(sub_[0-9A-Fa-f]{8})\(ctx,\s*base\)")
def audit():
 with tempfile.TemporaryDirectory(prefix="pre410_") as d:
  arc=Path(d)/"pre99.tar.gz";download(drive_client(),arc)
  digest,_,size=sha_file(arc)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("Authenticated PRE99 archive mismatch")
  files=0;matches=[];references=[]
  with tarfile.open(arc,"r:gz") as tar:
   for m in tar:
    path=m.name.lstrip("./")
    if not m.isfile() or not path.startswith("workspace/nativo/app/generated/default/") or not path.endswith(".cpp"):continue
    if m.size>7_000_000:raise ValueError("Oversized generated source")
    f=tar.extractfile(m)
    if f is None:raise ValueError("Unreadable generated source")
    raw=f.read()
    if len(raw)!=m.size:raise ValueError("Truncated generated source")
    files+=1
    if TARGET.encode() not in raw:continue
    sha=hashlib.sha256(raw).hexdigest()
    src=raw.decode("utf-8","replace")
    if NEEDLE in raw:
     body=body_for_function(src,TARGET)
     lines=body.splitlines()
     calls=[{"line":i+1,"callee":match.group(1)} for i,line in enumerate(lines) for match in CALL.finditer(line)]
     cmp=[{"line":i+1,"instruction":line.strip()[:140]} for i,line in enumerate(lines) if re.search(r"//\s*(?:cmpwi|cmplwi|beq|bne|blt|bgt)|REX_CALL_INDIRECT_FUNC",line,re.I)]
     matches.append({"path":path,"sha256":sha,"lines":len(lines),"direct_calls":calls[:120],"comparisons":cmp[:120],"truncated":len(calls)>120 or len(cmp)>120})
    else:
     references.append({"path":path,"sha256":sha,"occurrences":raw.count(TARGET.encode())})
  return {"stage":"PRE410_BMW_HELPER_LOCATION","status":"FOUND" if matches else "NOT_FOUND","archive_sha256":digest,"files_scanned":files,"definitions":matches,"reference_files":references[:50],"read_only":True,"apk_built":False,"save_modified":False,"signer_accessed":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"stage":"PRE410_BMW_HELPER_LOCATION","status":"FAILED","error_type":type(e).__name__,"error":str(e)[:180]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE410_STATUS",r["status"],"FILES",r.get("files_scanned",0),"DEFINITIONS",len(r.get("definitions",[])),"REFERENCES",len(r.get("reference_files",[])))
 for x in r.get("definitions",[]):print("PRE410_FOUND",x["path"],x["sha256"],"LINES",x["lines"],"CALLS",len(x["direct_calls"]))
 if r["status"]=="FAILED":print("PRE410_ERROR",r.get("error_type"),r.get("error"))
 return 1 if r["status"]=="FAILED" else 0
if __name__=="__main__":sys.exit(main())
