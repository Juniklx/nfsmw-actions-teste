#!/usr/bin/env python3
"""PRE422: read-only symbol and source provenance scan of authenticated PRE99."""
import argparse, hashlib, json, re, sys, tarfile, tempfile
from pathlib import Path
from datetime import datetime, timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre422/report.json")
PAT=re.compile(r"GetPerformancePartsList|CustomizePerformance|RefreshHeader|PerformancePartsList|Option title|999[.,]?999[.,]?999",re.I)
def audit():
    with tempfile.TemporaryDirectory(prefix="pre422_") as d:
        archive=Path(d)/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,size=sha_file(archive)
        if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE99 fingerprint mismatch")
        hits=[]; scanned=0; skipped=0
        with tarfile.open(archive,"r:gz") as tar:
            for m in tar:
                if not m.isfile():continue
                name=m.name.lstrip("./")
                if not name.endswith((".cpp",".h",".hpp",".c",".md",".txt",".json",".py",".toml",".cmake",".yml",".yaml")):continue
                if m.size>7_000_000:skipped+=1;continue
                f=tar.extractfile(m)
                if f is None:continue
                scanned+=1
                data=f.read()
                if not PAT.search(data.decode("utf-8","replace")):continue
                lines=data.decode("utf-8","replace").splitlines()
                matches=[{"line":i+1,"text":line[:250]} for i,line in enumerate(lines) if PAT.search(line)]
                hits.append({"path":name,"sha256":hashlib.sha256(data).hexdigest(),"matches":matches[:35],"total_matches":len(matches)})
        hits.sort(key=lambda x:(-x["total_matches"],x["path"]))
        return {"status":"AUDIT_OK","stage":"PRE422","archive_sha256":digest,"scanned_files":scanned,"skipped_oversized":skipped,"matching_files":len(hits),"hits":hits[:65],"truncated":len(hits)>65,"source_modified":False,"apk_built":False,"save_modified":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250]}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE422_STATUS",r["status"],"FILES",r.get("scanned_files",0),"MATCHING",r.get("matching_files",0))
    print("PRE422_ERROR",r.get("error","none"))
    for h in r.get("hits",[]):
        print("PRE422_FILE",h["path"],"MATCHES",h["total_matches"],"SHA256",h["sha256"])
        for m in h["matches"][:15]:print("PRE422_MATCH",h["path"],m["line"],m["text"][:200])
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
