#!/usr/bin/env python3
"""PRE409 read-only BMW upgrade catalog triage from authenticated PRE99."""
import argparse, hashlib, json, re, sys, tarfile, tempfile
from pathlib import Path
from datetime import datetime, timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre409/report.json")
TARGETS={"menu_gate":("workspace/nativo/app/generated/default/nfsmw_recomp.5.cpp","26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07",["sub_82578988"]),
         "performance_setup":("workspace/nativo/app/generated/default/nfsmw_recomp.11.cpp","0208ca992595ccbddfddc1299f59a2ff586b9c4d4c73f6dc40db4e3",["sub_82582F70","sub_8256F818"])}
CALL=re.compile(r"\b(?:__imp__)?(sub_[A-Fa-f0-9]{8})\(ctx,\s*base\)")
def audit():
    with tempfile.TemporaryDirectory(prefix="pre409_") as d:
        archive=Path(d)/"pre99.tar.gz";download(drive_client(),archive)
        digest,_,size=sha_file(archive)
        if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 archive fingerprint mismatch")
        results={}
        with tarfile.open(archive,"r:gz") as tar:
            for label,(path,sha,funcs) in TARGETS.items():
                m=next((m for m in tar if m.isfile() and m.name.lstrip("./")==path),None)
                if m is None or m.size>7_000_000:raise ValueError("Missing/oversized "+path)
                f=tar.extractfile(m)
                if f is None:raise ValueError("Cannot extract "+path)
                raw=f.read()
                if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError("Source fingerprint mismatch "+path)
                source=raw.decode("utf-8","replace")
                entries={}
                for fn in funcs:
                    body=body_for_function(source,fn)
                    lines=body.splitlines()
                    calls=[{"line":i+1,"callee":c.group(1),"preceding_asm":[z.strip()[:130] for z in lines[max(0,i-5):i] if z.lstrip().startswith("//")]} for i,line in enumerate(lines) for c in CALL.finditer(line)]
                    markers=[{"line":i+1,"text":line.strip()[:180]} for i,line in enumerate(lines) if re.search(r"cmpwi|cmplwi|li\s+r\d+,20|999999999|0x3b9ac9ff|REX_CALL_INDIRECT_FUNC",line,re.I)]
                    entries[fn]={"line_count":len(lines),"direct_calls":calls[:180],"comparisons_and_indirect_calls":markers[:220],"truncated":len(calls)>180 or len(markers)>220}
                results[label]={"source":path,"sha256":sha,"functions":entries}
        return {"status":"AUDIT_OK","stage":"PRE409_BMW_UPGRADE_CATALOG_READONLY","archive_sha256":digest,"results":results,
                "interpretation":"Static callsite evidence only. Does not establish which call generates Option title, 20/20 or 999999999.",
                "apk_built":False,"save_modified":False,"signing_accessed":False,"source_modified":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],"apk_built":False}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE409_STATUS",r["status"]);print("PRE409_REPORT",OUT)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
