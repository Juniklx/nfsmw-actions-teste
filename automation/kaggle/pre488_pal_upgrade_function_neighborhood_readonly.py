#!/usr/bin/env python3
"""PRE488: trace code neighborhood around verified PAL upgrade-count resolver.

Identify candidate guest subroutines adjacent to sub_823E5988 and whether
they read, write, or delegate attribute resolution. No semantic labels of
GetMaxLevel/SetLevel/SetPackage until corroborated. Metadata only.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre488/report.json")
PREFIX="workspace/nativo/app/generated/default/"
DEF=re.compile(r"(?m)^\s*DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
CALL=re.compile(r"__imp__(sub_[0-9A-Fa-f]{8})\s*\(\s*ctx\s*,\s*base\s*\)")
COMMENT=re.compile(r"(?m)^\s*//\s*([a-z][a-z0-9.]*)\b(.*)$")
STORE=re.compile(r"REX_STORE_U(8|16|32|64)\(([^,;]+),\s*([^;]+)\)")
TARGETS=(
 "sub_823E3A20","sub_823E4130","sub_823E41C0","sub_823E4600",
 "sub_823E4850","sub_823E5128","sub_823E56B0","sub_823E5988",
 "sub_823E5AA0","sub_823E5B08","sub_823E6560","sub_823E67E8",
 "sub_8256F818","sub_82582F70")
ATTR="sub_823E5988"
def audit():
 with tempfile.TemporaryDirectory(prefix="pre488_pal_") as scratch:
  archive=Path(scratch)/"pre99.tar.gz"
  download(drive_client(),archive)
  digest,_,size=sha_file(archive)
  if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
   raise ValueError("Authenticated PRE99 digest mismatch")
  matches={};callers=defaultdict(set);processed=0;function_count=0
  with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
   for m in tar:
    path=m.name.lstrip("./")
    if not (m.isfile() and path.startswith(PREFIX)
       and re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",path[len(PREFIX):])
       and m.size<=12_000_000):continue
    handle=tar.extractfile(m)
    if handle is None:raise ValueError("Unreadable C++ generated member")
    data=handle.read()
    if len(data)!=m.size:raise ValueError("Source member truncated")
    sha=hashlib.sha256(data).hexdigest()
    src=data.decode("utf-8","replace")
    definitions=list(DEF.finditer(src));processed+=1
    for i,d in enumerate(definitions):
     guest=d.group(1);function_count+=1
     body=src[d.start():definitions[i+1].start() if i+1<len(definitions) else len(src)]
     allcalls=CALL.findall(body)
     for callee in set(allcalls):
      if callee in TARGETS:callers[callee].add(guest)
     if guest not in TARGETS:continue
     lines=body.splitlines()
     mnemonics=Counter(m.group(1) for m in COMMENT.finditer(body))
     stores=STORE.findall(body)
     gueststores=[{"width_bits":int(w),
                   "address_is_obvious_stack_expression":("ctx.r1.u32" in adr or "ctx.r1.s32" in adr)}
                  for w,adr,value in stores]
     important=[]
     for i,line in enumerate(lines):
      comment=COMMENT.match(line)
      if comment is None:continue
      op,operand=comment.groups()
      if op not in ("bl","bctrl","blr","cmpwi","cmplwi","lwz","stw","lbz","stb","lhz","sth"):
       continue
      if op in ("lwz","stw") or op=="bl":
       if len(important)<100:
        important.append({"line":i+1,"ppc_mnemonic":op,
                          "ppc_operands":operand.strip()[:100]})
     callsites=Counter(allcalls)
     target_calls=[{"callee":callee,"count":n}
        for callee,n in sorted(callsites.items())]
     matches[guest]={
      "guest_function":guest,
      "generated_file":path[len(PREFIX):],
      "generated_file_sha256":sha,
      "function_lines":len(lines),
      "ppc_mnemonic_counts":dict(mnemonics.most_common(22)),
      "calls_to_sub_823E5988":callsites[ATTR],
      "callsite_counts":target_calls[:80],
      "return_instructions":mnemonics["blr"],
      "original_rex_store_count":len(stores),
      "stores_with_explicit_non_stack_address_count":
         sum(not x["address_is_obvious_stack_expression"] for x in gueststores),
      "selected_ppc_comments_only":important,
      "does_not_confirm_semantic_role":True
     }
  if (processed,function_count)!=(129,56338):
   raise ValueError("PRE485/PRE486 PAL original code coverage changed")
  if set(matches)!=set(TARGETS):
   raise ValueError("Missing targeted candidate function(s)")
  for name,record in matches.items():
   parents=sorted(callers.get(name,set()))
   record["direct_callers_found_in_source"]=len(parents)
   record["direct_caller_guest_ids"]=parents[:70]
   record["direct_caller_list_truncated"]=len(parents)>70
  return {
    "stage":"PRE488_PAL_UPGRADES_ATTR_RESOLVER_FUNCTION_NEIGHBORHOOD",
    "status":"AUDIT_OK",
    "source_pre99_sha256":digest,"generated_files_scanned":processed,
    "generated_guest_functions_indexed":function_count,
    "lookup_anchor":ATTR,
    "suspected_frontend_and_attribute_function_metadata":matches,
    "GetMaxLevel_address_confirmed":False,
    "SetLevel_address_confirmed":False,
    "SetPackage_address_confirmed":False,
    "emitted_only_bounded_opcode_metadata":True,
    "original_source_extracted":False,"game_executed":False,
    "apk_built":False,"save_modified":False,"tuning_enabled":False}
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as ex:r={
  "stage":"PRE488_PAL_UPGRADES_ATTR_RESOLVER_FUNCTION_NEIGHBORHOOD",
  "status":"FAILED","error_type":type(ex).__name__,"error":str(ex)[:230],
  "original_source_extracted":False,"apk_built":False,
  "save_modified":False,"tuning_enabled":False}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("PRE488_STATUS",r["status"],flush=True)
 print("PRE488_GUEST_METADATA",len(r.get("suspected_frontend_and_attribute_function_metadata",{})),flush=True)
 print("PRE488_ERROR",r.get("error_type","none"),flush=True)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
