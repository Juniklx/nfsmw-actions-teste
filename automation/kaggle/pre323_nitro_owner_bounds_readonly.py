#!/usr/bin/env python3
"""PRE323: Nitro PAL original function context for f28/f30 and owner r31.
Authenticated PRE99 read-only, no patches, no game build or key exposure.
"""
from pathlib import Path
import json,hashlib,tarfile,tempfile,sys,re
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre242_pal_float_dataflow_readonly import TARGETS
OUT=Path("/tmp/nfsmw-pre323/NFSMW_PRE323_NITRO_OWNER_BOUNDS.json")
def need(ok,msg):
 if not ok:raise ValueError(msg)
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 result={"stage":"PRE323_NITRO_OWNER_AND_LIMITS","status":"FAILED","apk_built":False,"source_changed":False,"cheats_enabled":False}
 try:
  with tempfile.TemporaryDirectory(prefix="nfsmw_pre323_") as td:
   arc=Path(td)/"pre99.tar.gz"
   download(drive_client(),arc)
   h,_,n=sha_file(arc)
   need(h==EXPECTED_SHA256 and n==EXPECTED_BYTES,"PRE99 mismatch")
   spec=TARGETS["nitro"]
   with tarfile.open(arc,"r:gz") as z:
    member=next((m for m in z if m.isfile() and m.name.lstrip("./")==spec["file"]),None)
    need(member is not None and member.size<8_000_000,"PAL source missing/oversized")
    stream=z.extractfile(member)
    need(stream is not None,"PAL unreadable")
    raw=stream.read()
   need(hashlib.sha256(raw).hexdigest()==spec["sha256"],"PAL fingerprint changed")
   body=body_for_function(raw.decode("utf8"),spec["function"])
   lines=body.splitlines()
   need(len(lines)>525,"Nitro function too short")
   region=lines[:550]
   # Observe all assignments to f28/f30 and to r31 (including dataflow from guest registers)
   needles=[
    r"(?<![A-Za-z0-9_])f28\.(?:f64|f32)\s*=",
    r"(?<![A-Za-z0-9_])f30\.(?:f64|f32)\s*=",
    r"(?<![A-Za-z0-9_])r31\.(?:u64|u32|s32)\s*=",
    r"\b(ctx\.r31|r31)\b.*(REX_LOAD|REX_STORE)",
    r"(?<![A-Za-z0-9_])f28\.(?:f64|f32)\b",
    r"(?<![A-Za-z0-9_])f30\.(?:f64|f32)\b",
   ]
   evidence={}
   for label,pat in zip(["f28_writes","f30_writes","r31_writes","r31_accesses","f28_uses","f30_uses"],needles):
    matches=[i for i,t in enumerate(region) if re.search(pat,t)]
    evidence[label]=[{"line":i+1,"text":region[i].strip()[:220],
       "window":[{"line":j+1,"text":region[j].strip()[:180]}
           for j in range(max(0,i-4),min(len(region),i+5))]} for i in matches[:38]]
    evidence[label+"_total"]=len(matches)
   evidence["function_entry"]=[{"line":i+1,"text":lines[i].strip()[:180]} for i in range(min(105,len(lines)))]
   evidence["branch_around_consumption"]=[{"line":i+1,"text":lines[i].strip()[:180]} for i in range(364,424)]
   evidence["branch_around_refill"]=[{"line":i+1,"text":lines[i].strip()[:180]} for i in range(487,538)]
   result.update({"status":"AUDIT_OK","source_file":spec["file"],"source_sha256":spec["sha256"],
    "function":spec["function"],"line_count":len(lines),"evidence":evidence,
    "limitation":"Assignments and offsets do not prove player ownership, safe writes, or absolute max; no code injection performed."})
 except Exception as e:
  result["error_type"]=type(e).__name__
 OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
 print("PRE323_STATUS",result["status"])
 for k in ["f28_writes","f30_writes","r31_writes","f28_uses","f30_uses"]:
  if "evidence" in result:
   print("PRE323",k,"count",result["evidence"].get(k+"_total"),
     "lines",[v["line"] for v in result["evidence"][k]])
 print("PRE323_ERROR_TYPE",result.get("error_type"))
 return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
