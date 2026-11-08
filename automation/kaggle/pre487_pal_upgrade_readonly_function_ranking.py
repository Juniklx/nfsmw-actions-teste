#!/usr/bin/env python3
"""PRE487: refine PAL Physics Upgrades function candidates by READ/WRITE
provenance on same PowerPC base register, excluding stack pointer r1.
This is structural xref classification, not proved semantic address labels.
Only temporary, hash-authenticated user's PRE99 generated code is inspected.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre487/report.json")
ROOT="workspace/nativo/app/generated/default/"
FUNC=re.compile(r"(?m)^\s*DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
ACCESS=re.compile(r"(?m)^\s*//\s*(lwz|stw)\s+r\d+,\s*(-?\d+)\((r\d+)\)")
CALL=re.compile(r"__imp__(sub_[0-9A-Fa-f]{8})\s*\(\s*ctx\s*,\s*base\s*\)")
PHYS_FIELDS={40,44,48,52,60,68,72}
PKG_OFFSETS={0,4,8,12,16,20,24}
WATCH=("sub_82582F70","sub_8256F818","sub_823E5988")

def audit():
 with tempfile.TemporaryDirectory(prefix="nfsmw_pre487_") as t:
  tarpath=Path(t)/"pre99.tar.gz"
  download(drive_client(),tarpath)
  digest,_,size=sha_file(tarpath)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):raise ValueError("PRE99 digest changed")
  candidates=[];files=0;functions=0;watch={};reads_any=0
  with tarfile.open(tarpath,"r:gz",errorlevel=2) as tf:
   for member in tf:
    path=member.name.lstrip("./")
    if not(member.isfile() and path.startswith(ROOT) and
      re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",path[len(ROOT):]) and
      10<member.size<=12_000_000):continue
    stream=tf.extractfile(member)
    if stream is None:raise ValueError("Missing source member")
    data=stream.read()
    if len(data)!=member.size:raise ValueError("Truncated source member")
    pathshort=path[len(ROOT):];fingerprint=hashlib.sha256(data).hexdigest()
    src=data.decode("utf-8","replace")
    defs=list(FUNC.finditer(src));files+=1
    for i,m in enumerate(defs):
     functions+=1
     guest=m.group(1)
     body=src[m.start():defs[i+1].start() if i+1<len(defs) else len(src)]
     reads=defaultdict(set);writes=defaultdict(set)
     pkg_reads=defaultdict(set)
     for op,offs,base in ACCESS.findall(body):
      if base=="r1":continue # explicit PowerPC stack register: not pvehicle
      off=int(offs)
      if off in PHYS_FIELDS:
       (reads if op=="lwz" else writes)[base].add(off)
      if op=="lwz" and off in PKG_OFFSETS:pkg_reads[base].add(off)
     matches=[]
     for base,fields in reads.items():
      if len(fields)<3:continue
      writes_same=writes.get(base,set())
      matches.append({"base_register":base,
        "pvehicle_counter_like_load_offsets":sorted(fields),
        "pvehicle_counter_like_store_offsets":sorted(writes_same),
        "distinct_reads":len(fields),"distinct_writes":len(writes_same)})
     calls=Counter(CALL.findall(body))
     if any(len(fields)>=5 for fields in reads.values()):reads_any+=1
     pkg_best=max((len(x) for x in pkg_reads.values()),default=0)
     if matches or pkg_best>=7 or guest in WATCH:
      high=max((x["distinct_reads"] for x in matches),default=0)
      entry={"function":guest,"generated_file":pathshort,
       "generated_file_sha256":fingerprint,
       "function_lines":len(body.splitlines()),"offset_load_profiles":matches,
       "max_distinct_package_field_reads_same_register":pkg_best,
       "call_count_total":sum(calls.values()),"calls_distinct":len(calls),
       "repeated_callees":[{"callee":k,"count":v} for k,v in calls.most_common(10) if v>=4],
       "candidate_getmaxlevel":high>=5 and all(x["distinct_writes"]<=2 for x in matches if x["distinct_reads"]==high),
       "candidate_setpackage_callpattern":pkg_best>=7 and sum(calls.values())>=1,
       "semantic_verification":"Not yet confirmed"}
      if guest in WATCH:watch[guest]=entry
      if entry["candidate_getmaxlevel"] or entry["candidate_setpackage_callpattern"]:
       candidates.append(entry)
  if (files,functions)!=(129,56338):
   raise ValueError("PRE485 indexed coverage differs from read-only PRE99")
  if len(watch)!=len(WATCH):raise ValueError("Known anchor missing from source")
  byread=sorted(candidates,key=lambda x:(
    -max((g["distinct_reads"] for g in x["offset_load_profiles"]),default=0),
    x["function_lines"],x["function"]))
  bypkg=sorted((x for x in candidates if x["candidate_setpackage_callpattern"]),
    key=lambda x:(-x["max_distinct_package_field_reads_same_register"],-x["call_count_total"],x["function"]))
  return {"stage":"PRE487_PAL_PERFORMANCE_GUEST_READONLY_FUNCTION_RANKING",
    "status":"AUDIT_OK","source_PRE99_sha256":digest,
    "files_verified":files,"functions_verified":functions,
    "read_at_least_five_phys_field_offsets_function_count":reads_any,
    "candidates_after_stack_and_store_filter":len(candidates),
    "GetMaxLevel_heuristic_top80":byread[:80],
    "SetPackage_heuristic_top60":bypkg[:60],
    "known_menu_anchors":watch,
    "semantic_SetPackage_verified":False,"semantic_SetLevel_verified":False,
    "semantic_GetMaxLevel_verified":False,
    "hypotheses_not_addresses_of_certified_functions":True,
    "game_code_executed":False,"apk_built":False,"save_modified":False,
    "game_assets_published":False,"tuning_enabled":False}

def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"stage":"PRE487_PAL_PERFORMANCE_GUEST_READONLY_FUNCTION_RANKING",
   "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:235],
   "apk_built":False,"save_modified":False,"tuning_enabled":False,
   "game_assets_published":False}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("PRE487_STATUS",r["status"])
 print("PRE487_READ_CANDIDATES",r.get("read_at_least_five_phys_field_offsets_function_count"))
 print("PRE487_POST_FILTER",r.get("candidates_after_stack_and_store_filter"))
 print("PRE487_ERROR",r.get("error_type","none"))
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
