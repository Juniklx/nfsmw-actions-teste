#!/usr/bin/env python3
"""PRE424 BMW call-path inspection. Read-only on SHA-verified PRE99 sources."""
import argparse,hashlib,json,re,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre424/report.json")
FILES={
 "caller":("workspace/nativo/app/generated/default/nfsmw_recomp.91.cpp","89c4ac57c8443f8e2bd08e482d769705218544b885e5cff34db567257b4f4f83","sub_82582F70"),
 "setup":("workspace/nativo/app/generated/default/nfsmw_recomp.11.cpp","0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3","sub_8256F818"),
}
FUNC=re.compile(r"DEFINE_REX_FUNC\((sub_[A-Fa-f0-9]{8})\)")
CALL=re.compile(r"\b(?:__imp__)?(sub_[A-Fa-f0-9]{8})\(ctx,\s*base\)")

def audit():
 with tempfile.TemporaryDirectory(prefix="pre424_") as d:
  archive=Path(d)/"pre99.tar.gz"
  download(drive_client(),archive)
  digest,_,size=sha_file(archive)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 archive fingerprint mismatch")
  results={}
  with tarfile.open(archive,"r:gz") as tar:
   for label,(path,sha,callee) in FILES.items():
    member=next((m for m in tar if m.isfile() and m.name.lstrip("./")==path),None)
    if member is None or member.size>7_000_000:raise ValueError("Missing or oversized "+path)
    f=tar.extractfile(member)
    if f is None:raise ValueError("Cannot extract "+path)
    data=f.read()
    if hashlib.sha256(data).hexdigest()!=sha:raise ValueError("Source fingerprint mismatch "+path)
    source=data.decode("utf-8","replace")
    sites=[]
    for match in re.finditer(r"\b(?:__imp__)?"+re.escape(callee)+r"\(ctx,\s*base\)",source):
     funcs=list(FUNC.finditer(source,0,match.start()))
     if not funcs:raise ValueError("Enclosing function missing "+path)
     fn=funcs[-1].group(1)
     body=body_for_function(source,fn)
     lines=body.splitlines()
     idx=next((i for i,line in enumerate(lines) if re.search(r"\b(?:__imp__)?"+re.escape(callee)+r"\(ctx,\s*base\)",line)),None)
     if idx is None:raise ValueError("Call not in function body "+fn)
     start=max(0,idx-105);end=min(len(lines),idx+105)
     window=[{"line":i+1,"text":lines[i].strip()[:230]} for i in range(start,end)]
     calls=[{"line":i+1,"target":c.group(1)} for i,line in enumerate(lines) for c in CALL.finditer(line)]
     sites.append({"enclosing_function":fn,"body_lines":len(lines),"call_line":idx+1,"direct_calls":calls[:100],"window":window})
    results[label]={"path":path,"sha256":sha,"target":callee,"sites":sites,"site_count":len(sites)}
  return {"status":"AUDIT_OK" if all(x["site_count"]>0 for x in results.values()) else "PARTIAL",
    "stage":"PRE424_BMW_SETUP_CALLER_READONLY","archive_sha256":digest,"results":results,
    "interpretation":"Call chain only; no verified BMW-specific restriction or upgrade catalog pointer",
    "source_modified":False,"apk_built":False,"save_modified":False,"signing_accessed":False}

def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE424_STATUS",r["status"],"ERROR",r.get("error","none"))
 for label,entry in r.get("results",{}).items():
  print("PRE424_FILE",label,entry["path"],"SITES",entry["site_count"])
  for site in entry["sites"]:
   print("PRE424_CALLER",label,site["enclosing_function"],"LINES",site["body_lines"],"TARGET_LINE",site["call_line"])
   for c in site["direct_calls"]:print("PRE424_DIRECT",label,c["line"],c["target"])
   for w in site["window"]:print("PRE424_BODY",label,site["enclosing_function"],w["line"],w["text"])
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
