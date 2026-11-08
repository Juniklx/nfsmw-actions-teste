#!/usr/bin/env python3
"""PRE423: inspect game-owned metadata and references, excluding third-party noise."""
import argparse,hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre423/report.json")
PAT=re.compile(r"GetPerformancePartsList|CustomizePerformance|RefreshHeader|PerformancePartsList|82582F70|8256F818|82578988",re.I)
def audit():
 with tempfile.TemporaryDirectory(prefix="pre423_") as d:
  archive=Path(d)/"pre99.tar.gz";download(drive_client(),archive)
  digest,_,size=sha_file(archive)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 fingerprint mismatch")
  scanned=0;hits=[];candidates=[]
  with tarfile.open(archive,"r:gz") as tar:
   for m in tar:
    if not m.isfile() or m.size>8_000_000:continue
    name=m.name.lstrip("./")
    if "/thirdparty/" in name or "/.git/" in name:continue
    if not name.endswith((".cpp",".h",".hpp",".c",".md",".txt",".json",".py",".toml",".cmake",".yml",".yaml",".map",".sym",".csv")):continue
    scanned+=1
    if re.search(r"symbol|function|mapping|xref|reverse|recomp|patch",name,re.I):candidates.append(name)
    f=tar.extractfile(m)
    if f is None:continue
    data=f.read()
    lines=data.decode("utf-8","replace").splitlines()
    matches=[{"line":i+1,"text":line[:230]} for i,line in enumerate(lines) if PAT.search(line)]
    if matches:hits.append({"path":name,"sha256":hashlib.sha256(data).hexdigest(),"count":len(matches),"matches":matches[:12]})
  hits.sort(key=lambda h:(-h["count"],h["path"]))
  return {"status":"AUDIT_OK","scanned":scanned,"matched":len(hits),"hits":hits[:65],"candidate_metadata_paths":candidates[:70],"truncated":len(hits)>65,"source_modified":False,"apk_built":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat();OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE423_STATUS",r["status"],"SCANNED",r.get("scanned",0),"MATCHED",r.get("matched",0),"ERROR",r.get("error","none"))
 for h in r.get("hits",[]):
  print("PRE423_FILE",h["path"],"COUNT",h["count"],"SHA256",h["sha256"])
  for m in h["matches"]:print("PRE423_MATCH",m["line"],m["text"][:180])
 for path in r.get("candidate_metadata_paths",[])[:30]:print("PRE423_CANDIDATE",path)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
