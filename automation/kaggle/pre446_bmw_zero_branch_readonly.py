#!/usr/bin/env python3
"""PRE446 - read-only branch taxonomy for observed BMW zero / Punto positive."""
import argparse,hashlib,json,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function
OUT=Path("/tmp/nfsmw-pre446/report.json")
ROOT="workspace/nativo/app/generated/default/"
TARGETS={
 "lookup":("nfsmw_recomp.28.cpp","11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad","sub_823E5988"),
 "builder":("nfsmw_recomp.57.cpp","a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c","sub_8256F818"),
 "attribute_check":("nfsmw_recomp.50.cpp","f20ec567de4c4637756977a71a6c85f3848b63ba639f037b819868328e3f7e9d","sub_8214B858"),
 "attribute_value":("nfsmw_recomp.83.cpp","21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4","sub_8214EDA8")
}
def audit():
 with tempfile.TemporaryDirectory(prefix="pre446_readonly_") as d:
  tarpath=Path(d)/"pre99.tar.gz";download(drive_client(),tarpath)
  fingerprint,_,size=sha_file(tarpath)
  if (fingerprint,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 fingerprint mismatch")
  found={}
  with tarfile.open(tarpath,"r:gz") as tar:
   names={ROOT+v[0]:k for k,v in TARGETS.items()}
   for m in tar:
    name=m.name.lstrip("./")
    if name not in names:continue
    if not m.isfile() or m.size>7000000:raise ValueError("Invalid source entry")
    handle=tar.extractfile(m)
    if handle is None:raise ValueError("Missing source member")
    raw=handle.read();key=names[name];expected=TARGETS[key][1]
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("Pinned file hash mismatch "+key)
    body=body_for_function(raw.decode("utf-8"),TARGETS[key][2])
    found[key]={"sha256":expected,"lines":body.splitlines()}
  if set(found)!=set(TARGETS):raise ValueError("Missing expected functions")
  l=found["lookup"]["lines"];b=found["builder"]["lines"]
  def chk(a,expression):
   hits=[i+1 for i,v in enumerate(a) if expression in v]
   if not hits:raise ValueError("Missing code evidence "+expression)
   return hits
  explicit=chk(l,"ctx.r3.s64 = 0;")
  resolved=chk(l,"ctx.r3.u64 = REX_LOAD_U32(ctx.r11.u32 + 0);")
  if len(explicit)!=2 or len(resolved)!=1:raise ValueError("Return-site count changed")
  first_call=chk(b,"__imp__sub_823E5988(ctx, base);")
  if len(first_call)!=2:raise ValueError("Expected two existing calls")
  guard=chk(b,"if (!cr6.gt) goto loc_8256F990;")
  if guard[0]<first_call[0]:raise ValueError("Builder guard before helper")
  if not chk(l,"__imp__sub_8214B858(ctx, base);") or not chk(l,"__imp__sub_8214EDA8(ctx, base);"):
   raise ValueError("Missing lookup's attribute resolution")
  nested=found["attribute_check"]["lines"]
  if not chk(nested,"if (cr6.eq) goto loc_8214B8E0;"):
   raise ValueError("Attribute null short-circuit not found")
  evidence={
   "descriptor_chain_miss":{"zero_line":explicit[0],"condition":"table search reaches end without matching type"},
   "resolved_attribute_value":{"value_read_line":resolved[0],"condition":"value read from resolved attribute; may itself be zero"},
   "fallback_or_unresolved_attribute":{"zero_line":explicit[1],"condition":"one of several null / unresolved branches"},
   "builder_early_exit":{"guard_lines":guard,"condition":"candidate_count <=0 skips list allocation"}
  }
  return {"status":"AUDIT_OK","stage":"PRE446_ZERO_BRANCH_PROVENANCE_READONLY",
   "pre99_sha256":fingerprint,
   "source_signatures":{k:{"sha256":v["sha256"],"function_lines":len(v["lines"])} for k,v in found.items()},
   "source_level_return_paths":evidence,"bmw_runtime_branch_selected":False,
   "seven_category_observations_source":"PRE444 user logs; not processed in this audit",
   "guest_calls_executed":False,"source_changed":False,"apk_built":False,"save_changed":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:result=audit()
 except Exception as e:result={"status":"FAILED","error_type":type(e).__name__,
                              "reason":str(e)[:160]}
 result["run_id"]=a.run_id;result["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print("PRE446_STATUS",result["status"],"ERROR",result.get("reason","none"))
 print("PRE446_BRANCH_PATHS",result.get("source_level_return_paths"))
 print("PRE446_RUNTIME_BRANCH_IDENTIFIED",result.get("bmw_runtime_branch_selected"))
 return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
