#!/usr/bin/env python3
"""PRE441: authenticated read-only guest PPC r24 category source trace.

No guest runtime invoked, no game patches, no writes to user data, no signer.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre441/report.json")
SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.11.cpp"
HASH="0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3"
TARGET="sub_82582F70"
def digest(blob):return hashlib.sha256(blob).hexdigest()
def analyze():
 with tempfile.TemporaryDirectory(prefix="nfsmw_pre441_") as d:
  arc=Path(d)/"pre99.tar.gz";download(drive_client(),arc)
  sh,_,length=sha_file(arc)
  if (sh,length)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 fingerprint mismatch")
  matched=[]
  with tarfile.open(arc,"r:gz") as tar:
   for item in tar:
    if item.name.lstrip("./")==SOURCE and item.isfile():
     if item.size>7_000_000:raise ValueError("Unexpected generated source size")
     fp=tar.extractfile(item)
     if fp is None:raise ValueError("Unextractable source")
     raw=fp.read()
     if digest(raw)!=HASH:raise ValueError("Caller source hash mismatch")
     matched.append(raw)
  if len(matched)!=1:raise ValueError("Caller file count mismatch")
  body=body_for_function(matched[0].decode("utf-8"),TARGET).splitlines()
  sites=[i+1 for i,line in enumerate(body) if "r24" in line]
  events=[]
  for i in sites:
   line=body[i-1].strip()
   events.append({"line":i,"source":line[:220]})
  assignments=[r for r in events if re.match(r"(?:r24\.(?:u64|s64|u32|s32|u8|s8)\s*=|//\s*(?:(?:mr|lwz|li|addi|rlwinm|clrlwi|subf)\s+r24\b))",r["source"])]
  if len(assignments)==0:raise ValueError("Missing category register provenance")
  windows=[]
  seen=set()
  for item in assignments:
   i=item["line"]
   for line_no in range(max(1,i-13),min(len(body),i+16)+1):
    if line_no in seen:continue
    windows.append({"line":line_no,"source":body[line_no-1].strip()[:220]});seen.add(line_no)
  # PRE441B: preserve the complete 0..6 switch and targets for exact mapping.
  for line_no in range(365,404):
   if line_no not in seen and line_no<=len(body):
    windows.append({"line":line_no,"source":body[line_no-1].strip()[:220]})
    seen.add(line_no)
  windows.sort(key=lambda x:x["line"])
  if not any("sub_8256F818(ctx, base);" in x for x in body):
   raise ValueError("Selected caller does not contain list builder")
  return {"status":"AUDIT_OK","target":TARGET,"source":SOURCE,"source_sha256":HASH,
    "function_length":len(body),"r24_occurrences":events,"r24_assignments":assignments,
    "windows":windows,"runtime_value4_source_verified":False,
    "high_level_category_name_verified":False,"source_modified":False,"apk_built":False,"save_accessed":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:report=analyze()
 except Exception as e:report={"status":"FAILED","error_type":type(e).__name__,"error":str(e)[:180]}
 report["run_id"]=a.run_id;report["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
 print("PRE441_STATUS",report["status"],"ERROR",report.get("error","none"))
 for line in report.get("r24_assignments",[]):print("PRE441_ASSIGN",line["line"],line["source"])
 for line in report.get("windows",[]):print("PRE441_CODE",line["line"],line["source"])
 return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
