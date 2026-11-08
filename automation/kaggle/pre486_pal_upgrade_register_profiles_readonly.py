#!/usr/bin/env python3
"""PRE486: original PAL static-recompilation guest-code access patterns.

Read authenticated PRE99 privately to characterize expected BMW menu caller
sub_82582F70 and find field/register grouping candidates for Physics::
Upgrades::GetMaxLevel/SetLevel/SetPackage. A heuristic rank is NOT a semantic
identification. Publish metadata only, no original game source code or bytes.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre486/report.json")
ROOT="workspace/nativo/app/generated/default/"
FUNC=re.compile(r"(?m)^\s*DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
CALL=re.compile(r"__imp__(sub_[0-9A-Fa-f]{8})\s*\(\s*ctx\s*,\s*base\s*\)")
ACCESS=re.compile(r"(?m)^\s*//\s*(lwz|stw)\s+r\d+,\s*(-?\d+)\((r\d+)\)")
TARGETS=(
 "sub_82582F70", # unique PRE485 direct caller of list builder
 "sub_8256F818", # candidate option list builder already authenticated PRE456
 "sub_82582A40", # other attribute lookup caller
 "sub_82570D90", # repeated pvehicle-like offsets
 "sub_8255C790", # frequent 52-byte field accesses
 "sub_8256C2F0", # route-style helper
 "sub_8256CBC8", # route-style helper
 "sub_8256CBB8", # route-style helper
 "sub_823E5988", # verified candidate count lookup PRE456
 "sub_8236E378", # seven offset candidate (unclassified)
 "sub_82141B48", # seven offset candidate (unclassified)
 "sub_82142B38", # seven offset candidate (unclassified)
)
FIELDS={40,44,48,52,60,68,72}
SOURCE_SHA={
 "nfsmw_recomp.28.cpp":"11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad",
 "nfsmw_recomp.57.cpp":"a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c",
}

def audit():
 with tempfile.TemporaryDirectory(prefix="nfsmw_pre486_") as t:
  archive=Path(t)/"pre99.tar.gz"
  download(drive_client(),archive)
  digest,_,length=sha_file(archive)
  if (digest,length)!=(EXPECTED_SHA256,EXPECTED_BYTES):
   raise ValueError("Original PRE99 tar changed")
  ranked=[];target_info={};file_count=0;total=0;files_pinned=set()
  with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
   for member in tar:
    path=member.name.lstrip("./")
    if not (member.isfile() and path.startswith(ROOT) and
      re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",path[len(ROOT):]) and
      10<member.size<=12_000_000):continue
    stream=tar.extractfile(member)
    if stream is None:raise ValueError("Invalid generated source member")
    content=stream.read()
    if len(content)!=member.size:raise ValueError("Generated source truncated")
    filename=path[len(ROOT):];file_count+=1
    sha=hashlib.sha256(content).hexdigest()
    if filename in SOURCE_SHA:
     if sha!=SOURCE_SHA[filename]:raise ValueError("Known source sha mismatch "+filename)
     files_pinned.add(filename)
    source=content.decode("utf-8","replace")
    definitions=list(FUNC.finditer(source))
    for i,m in enumerate(definitions):
     name=m.group(1)
     body=source[m.start():definitions[i+1].start() if i+1<len(definitions) else len(source)]
     total+=1
     rows=ACCESS.findall(body)
     byreg=defaultdict(list)
     for instruction,offset,reg in rows:
      value=int(offset)
      if value in FIELDS:byreg[reg].append((instruction,value))
     byreg_count={k:sorted(set(off for _,off in v)) for k,v in byreg.items()}
     largest=max((len(v) for v in byreg_count.values()),default=0)
     best_registers=[k for k,offsets in byreg_count.items() if len(offsets)==largest and largest>0]
     calls=CALL.findall(body)
     call_counts=Counter(calls)
     repeat=max(call_counts.values(),default=0)
     if name in TARGETS:
      opcodes=re.findall(r"(?m)^\s*//\s*([a-z][a-z0-9.]*)\b",body)
      sampled_comments=[line.strip()[3:].strip()[:90] for line in body.splitlines()
        if line.lstrip().startswith("//") and any(k in line.lower() for k in
           ("cmpwi ","cmplwi ","lwz ","stw ","bne ","beq ","bl ","blr "))
       ][:95]
      target_info[name]={
       "filename":filename,"file_sha256":sha,"function_size_chars":len(body),
       "lines":len(body.splitlines()),
       "incoming_semantic_role":"Not identified; candidate only",
       "same_register_field_diversity":largest,
       "best_base_registers":best_registers,
       "per_register_fields":byreg_count,
       "outgoing_distinct_calls":len(call_counts),
       "repeated_callee_call_counts":[{"callee":k,"sites":n} for k,n in
          call_counts.most_common(18)],
       "ppc_mnemonic_histogram":dict(Counter(opcodes).most_common(20)),
       "sampled_ppc_instructions":sampled_comments
      }
     # High-confidence structural patterns are access to 5+ distinct
     # offsets through the same register, not generic offset occurrence.
     if largest>=4 or repeat>=6:
      info={
       "function":name,"filename":filename,"file_sha256":sha,
       "function_size_chars":len(body),"number_distinct_offsets_same_register":largest,
       "best_registers":best_registers[:4],
       "offsets_by_best_registers":{k:byreg_count[k] for k in best_registers[:4]},
       "max_same_callee_calls":repeat,
       "top_repeated_callees":[{"guest_function":k,"sites":n}
          for k,n in call_counts.most_common(5) if n>=3],
       "calls_total":len(calls),
       "function_line_count":len(body.splitlines()),
      }
      ranked.append(info)
  if files_pinned!=set(SOURCE_SHA):
   raise ValueError("Previously pinned PAL generated source absent")
  if file_count!=129 or total!=56338:
   raise ValueError("PRE485 source function/file coverage changed")
  if set(target_info)!=set(TARGETS):
   raise ValueError("At least one selected PRE486 source function missing")
  ranked.sort(key=lambda r:(
     -r["number_distinct_offsets_same_register"],
     -(r["max_same_callee_calls"] if r["max_same_callee_calls"]<=12 else 0),
     r["function_line_count"],
     r["function"]))
  same_register_5=sum(x["number_distinct_offsets_same_register"]>=5 for x in ranked)
  repeats6=sum(x["max_same_callee_calls"]>=6 for x in ranked)
  return {
    "stage":"PRE486_ORIGINAL_PAL_PERFORMANCE_GUEST_REGISTER_TRACE",
    "status":"AUDIT_OK",
    "pre99_sha256":digest,"source_files":file_count,
    "functions_indexed":total,"pinned_source_files_checked":len(files_pinned),
    "guest_field_offsets_hex":[hex(k) for k in sorted(FIELDS)],
    "all_heuristic_candidates":len(ranked),
    "candidates_with_five_or_more_fields_on_one_register":same_register_5,
    "candidates_with_six_or_more_calls_to_one_function":repeats6,
    "named_anchor_function_summaries":target_info,
    "structural_candidates_top_120":ranked[:120],
    "functions_SetPackage_SetLevel_GetMaxLevel_confirmed":False,
    "candidate_heuristics_do_not_prove_semantics":True,
    "source_archive_extracted":False,"original_generated_source_uploaded":False,
    "game_executed":False,"apk_built":False,"save_modified":False,
    "tuning_enabled":False
  }

def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"stage":"PRE486_ORIGINAL_PAL_PERFORMANCE_GUEST_REGISTER_TRACE",
  "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
  "source_archive_extracted":False,"original_generated_source_uploaded":False,
  "apk_built":False,"save_modified":False,"tuning_enabled":False}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("PRE486_STATUS",r["status"],flush=True)
 print("PRE486_CANDIDATES",r.get("all_heuristic_candidates","?"),flush=True)
 print("PRE486_ONE_REGISTER_FIVE",r.get("candidates_with_five_or_more_fields_on_one_register","?"),flush=True)
 print("PRE486_ERROR",r.get("error_type","none"),flush=True)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
