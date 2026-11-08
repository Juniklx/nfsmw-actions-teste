#!/usr/bin/env python3
"""PRE417: locate BMW performance helper across authenticated PRE99 generated files; read only."""
import argparse,hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
OUT=Path("/tmp/nfsmw-pre417/report.json")
TARGETS=("sub_8256D220","sub_8256D5F0","sub_8256D800","sub_8256C2F0")
PINNED_HELPER_SHA="40223de7eae9db7ecedfb2150959282736a82f42cafadc8cc8c506d9ac2c63be"
PINNED_CALLERS={"sub_8256D5F0":"3703d9cae96852c014bdb5df54cf5e72c2cfc145100664ca331eb481a1537e6f","sub_8256D800":"ddd1e461ac8c463d9edfdd1705500033fc69416eac5dd4ff0ce3cedc356b4c84","sub_8256C2F0":"5c07eae92a5583a52b88c5cd90e2d259f26ac402fe451b668768e048dac29bea"}
CALL=re.compile(r"\b(?:__imp__)?(sub_[0-9A-Fa-f]{8})\(ctx,\s*base\)")
def audit():
 with tempfile.TemporaryDirectory(prefix="pre417_") as d:
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
    if not any(t.encode() in raw for t in TARGETS):continue
    sha=hashlib.sha256(raw).hexdigest()
    src=raw.decode("utf-8","replace")
    for target in TARGETS:
     needle=("DEFINE_REX_FUNC("+target+")").encode()
     if needle in raw:
      if target in PINNED_CALLERS and sha!=PINNED_CALLERS[target]:raise ValueError("PRE412 verified caller fingerprint mismatch: "+target)
      if target=="sub_8256D220" and sha!=PINNED_HELPER_SHA:raise ValueError("PRE413 verified helper fingerprint mismatch")
      body=body_for_function(src,target)
      lines=body.splitlines()
      calls=[{"line":i+1,"callee":match.group(1)} for i,line in enumerate(lines) for match in CALL.finditer(line)]
      cmp=[{"line":i+1,"instruction":line.strip()[:140]} for i,line in enumerate(lines) if re.search(r"//\s*(?:cmpwi|cmplwi|beq|bne|blt|bgt)|REX_CALL_INDIRECT_FUNC",line,re.I)]
      windows=[{"line":x["line"],"excerpt":[f"{k+1}: {lines[k].strip()[:170]}" for k in range(max(0,x["line"]-6),min(len(lines),x["line"]+6))]} for x in calls[:30]]
      focus=[i for i,line in enumerate(lines) if "sub_8256D220(ctx, base)" in line]
      focus_windows=[{"line":i+1,"excerpt":[f"{k+1}: {lines[k].strip()[:190]}" for k in range(max(0,i-12),min(len(lines),i+14))]} for i in focus[:12]]
      return_sites=[{"line":i+1,"value":(re.search(r"ctx\.r3\.(?:s64|u64)\s*=\s*(-?\d+)",lines[i-2]).group(1) if i>1 and re.search(r"ctx\.r3\.(?:s64|u64)\s*=\s*(-?\d+)",lines[i-2]) else None),"context":[f"{k+1}: {lines[k].strip()[:180]}" for k in range(max(0,i-5),min(len(lines),i+2))]} for i,line in enumerate(lines) if line.strip()=="return;"]
      matches.append({"return_sites":return_sites,"focus_windows":focus_windows,"body_excerpt":lines[:160] if target=="sub_8256D220" else [],"function":target,"path":path,"sha256":sha,"lines":len(lines),"direct_calls":calls[:120],"comparisons":cmp[:120],"call_windows":windows,"truncated":len(calls)>120 or len(cmp)>120})
     elif target.encode() in raw:
      references.append({"function":target,"path":path,"sha256":sha,"occurrences":raw.count(target.encode())})
  return {"stage":"PRE417_BMW_HELPER_LOCATION","status":"COMPLETE" if set(x["function"] for x in matches)==set(TARGETS) else "PARTIAL" if matches else "NOT_FOUND","archive_sha256":digest,"files_scanned":files,"targets":list(TARGETS),"missing":[t for t in TARGETS if t not in {x["function"] for x in matches}],"definitions":matches,"reference_files":references[:50],"read_only":True,"apk_built":False,"save_modified":False,"signer_accessed":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"stage":"PRE417_BMW_HELPER_LOCATION","status":"FAILED","error_type":type(e).__name__,"error":str(e)[:180]}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE417_STATUS",r["status"],"FILES",r.get("files_scanned",0),"DEFINITIONS",len(r.get("definitions",[])),"REFERENCES",len(r.get("reference_files",[])))
 for x in r.get("definitions",[]):
  print("PRE417_FOUND",x["function"],x["path"],x["sha256"],"LINES",x["lines"],"CALLS",len(x["direct_calls"]))
  print("PRE417_CALLEES",x["function"],",".join(c["callee"] for c in x["direct_calls"][:35]))
  print("PRE417_FOCUS_CALLS",x["function"],len(x["focus_windows"]))
  print("PRE417_COMPARISONS",x["function"]," | ".join(z["instruction"] for z in x["comparisons"][:30])[:1800])
  if x["function"]!="sub_8256D220":
   for window in x["focus_windows"][:8]:print("PRE417_CALL_CONTEXT",x["function"],window["line"]," | ".join(window["excerpt"])[:3500])
  if x["function"]=="sub_8256D220":
   for site in x["return_sites"]:print("PRE417_RETURN",site["line"],site["value"]," | ".join(site["context"]))
   for line in x["body_excerpt"][:100]:print("PRE417_HELPER_LINE",line.strip()[:170])
 print("PRE417_MISSING",",".join(r.get("missing",[])))
 if r["status"]=="FAILED":print("PRE417_ERROR",r.get("error_type"),r.get("error"))
 return 1 if r["status"]=="FAILED" else 0
if __name__=="__main__":sys.exit(main())
