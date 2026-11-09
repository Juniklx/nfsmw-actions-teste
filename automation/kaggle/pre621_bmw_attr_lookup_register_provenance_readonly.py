#!/usr/bin/env python3
"""PRE621: read-only bounded PAL guest FE attribute lookup operand/branch audit.
Downloads the exact authenticated PRE99 original from private Drive; reads only
the generated C++ shards for sub_823E5988, sub_8256F818, and two attribute
helpers; publishes metadata, NOT private game sources or a guest patch.
This gate is needed after user SHA-verified PRE607 game archives while BMW's
six performance categories still return 0 in V48 PRE447_ROUTE reason=2.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre621/report.json")
ROOT="workspace/nativo/app/generated/default/"
TARGET={
  "lookup":("nfsmw_recomp.28.cpp","11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad","sub_823E5988"),
  "builder":("nfsmw_recomp.57.cpp","a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c","sub_8256F818"),
  "attribute_check":("nfsmw_recomp.50.cpp","f20ec567de4c4637756977a71a6c85f3848b63ba639f037b819868328e3f7e9d","sub_8214B858"),
  "attribute_value":("nfsmw_recomp.83.cpp","21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4","sub_8214EDA8")
}
RETURN_LINES={"lookup":[60,126,153]}
WATCH=("ctx.r3","ctx.r4","ctx.r11","ctx.r12","ctx.r21","ctx.r31","ctx.lr")
CALL_RE=re.compile(r"__imp__(sub_[0-9A-Fa-f]{8})\s*\(\s*ctx\s*,\s*base\s*\)")
GUEST_LOADS=("REX_LOAD_U8(","REX_LOAD_U16(","REX_LOAD_U32(","REX_LOAD_U64(")
GUEST_STORES=("REX_STORE_U8(","REX_STORE_U16(","REX_STORE_U32(","REX_STORE_U64(")
def sha(raw):return hashlib.sha256(raw).hexdigest()
def audit():
  base=json.loads(Path("docs/PRE617_HANDOFF_NAME_BMW_OPTION_TITLE_SEVEN_CATEGORIES_LOG_20261109.md").read_text(encoding="utf-8").split("# PRE617",1)[-1] and "{}") if False else None
  last=Path("docs/PRE620_HANDOFF_USER_VERIFIED_PRE607_ACTIVE_HASH_BMW_CATEGORY_ZERO_20261109.md").read_text(encoding="utf-8")
  if ( "f15d5da54148e0e762f65004d534092dbf3c08d12b0f8b710d6cf599235a32e2" not in last
     or "1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146" not in last
     or "PRE607_CONFIRMED_BY_USER_SHA256" not in last):
    raise ValueError("PRE620 user supplied live hashes not checked")
  report446=Path("docs/PRE446_PRE447_BMW_ZERO_RETURN_ROTAS_20261108.md").read_text(encoding="utf-8")
  if "reason" not in report446.lower() and "raz" not in report446.lower() and "return" not in report446.lower():
    raise ValueError("Old branch provenance absent")
  with tempfile.TemporaryDirectory(prefix="nfsmw_pre621_") as tmp:
    p=Path(tmp)/"pre99.tar.gz"
    download(drive_client(),p)
    dig,_,n=sha_file(p)
    if (dig,n)!=(EXPECTED_SHA256,EXPECTED_BYTES):
      raise ValueError("Private PRE99 original hash/size differ")
    files={ROOT+v[0]:k for k,v in TARGET.items()}
    hit={}
    with tarfile.open(p,"r:gz") as tar:
      for mem in tar:
        name=mem.name.lstrip("./")
        if name not in files:continue
        if not mem.isfile() or mem.size>7000000:raise ValueError("Bad source entry")
        raw=tar.extractfile(mem).read()
        tag=files[name]; expected=TARGET[tag][1]
        if sha(raw)!=expected:raise ValueError("PRE99 C++ shard changed: "+tag)
        src=raw.decode("utf-8")
        body=body_for_function(src,TARGET[tag][2])
        lines=body.splitlines()
        hit[tag]={"path":TARGET[tag][0],"sha256":expected,"func":TARGET[tag][2],"nlines":len(lines),
          "calls_in_order":CALL_RE.findall(body),
          "guest_load_counts":{v:body.count(v) for v in GUEST_LOADS},
          "guest_store_counts":{v:body.count(v) for v in GUEST_STORES},
          "callsite_relative_lines":[{"target":m.group(1),
                   "line":body[:m.start()].count("\n")+1}
                   for m in CALL_RE.finditer(body)]}
        if tag=="lookup":
          if len(lines)!=155:raise ValueError("Expected PRE446 lookup original 155 lines")
          returns=[i+1 for i,l in enumerate(lines) if l.strip()=="return;"]
          if returns!=[60,126,153]:
            raise ValueError("Original PRE447 lookup return lines changed")
          attrreads=[i+1 for i,l in enumerate(lines)
               if "ctx.r3.u64 = REX_LOAD_U32(ctx.r11.u32 + 0);" in l]
          if len(attrreads)!=1 or len(hit[tag]["callsite_relative_lines"])!=2:
            raise ValueError("Original lookup attr return/calls changed")
          hit[tag]["return_lines"]=returns
          hit[tag]["attribute_value_return_relative_lines"]=attrreads
          hit[tag]["branch_and_register_metadata"]=[]
          for ret in returns:
            window=lines[max(0,ret-20):ret]
            filters=[{
               "relative_line":ret-len(window)+i,
               "kind": ("conditional" if l.strip().startswith("if (") else
                        "branch" if "goto loc_" in l else
                        "register" if any(k in l for k in WATCH) else
                        "return" if l.strip()=="return;" else "other"),
               "observed_registers":sorted(set(re.findall(r"ctx\.r(?:3|4|11|12|21|31)(?!\d)|ctx\.lr",l))),
               "guest_memory_op":next((op for op in GUEST_LOADS+GUEST_STORES if op in l),None),
               "guest_call":bool(CALL_RE.search(l))
             } for i,l in enumerate(window)
             if ("if (" in l or "goto loc_" in l or "ctx.r" in l or l.strip()=="return;")]
            hit[tag]["branch_and_register_metadata"].append({
                "return_line":ret,
                "last_20_source_lines_categorized":filters,
                "return_value_was_zero_or_resolved_attribute":
                  "resolved_attribute" if ret==126 else "explicit_zero",
                "new_guest_reads_needed_for_basic_extra_host_logging":False
            })
    if set(hit)!=set(TARGET):
      raise ValueError("Missing original generated source shard")
  for tag in TARGET:
    if hit[tag]["nlines"]<50:raise ValueError("Unreasonable small function")
  if hit["lookup"]["calls_in_order"]!=["sub_8214B858","sub_8214EDA8"]:
    raise ValueError("Function return route controls differ")
  return {
    "stage":"PRE621_GUEST_ATTR_LOOKUP_RETURN_REGISTERS_BRANCH_METADATA_READONLY",
    "status":"AUDIT_OK",
    "private_original_pre99_sha256":EXPECTED_SHA256,
    "private_original_pre99_bytes":EXPECTED_BYTES,
    "pinned_functions":hit,
    "PRE607_active_game_assets_sha_confirmed_by_user":True,
    "guest_PRE447_reason2_associated_with_resolved_attribute_return":True,
    "six_zero_one_nitro_three_values_from_prior_uploaded_log":True,
    "attribute_descriptor_semantic_identity_proven":False,
    "specific_RefSpec_new_engine_used_by_guest_proven":False,
    "GetMaxLevel_or_SetLevel_identified":False,
    "next_step":"Bounded reversible instrumented C++ preview for resolved attribute value and descriptor pointer; pin no new guest loads/stores, no patch release before validate",
    "guest_executed":False,"source_changed_on_disk":False,
    "game_assets_modified":False,"save_modified":False,"APK_built":False,
    "release_key_accessed":False,"original_source_published":False
  }
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"stage":"PRE621_GUEST_ATTR_LOOKUP_RETURN_REGISTERS_BRANCH_METADATA_READONLY",
    "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:290],
    "guest_executed":False,"source_changed_on_disk":False,
    "game_assets_modified":False,"save_modified":False,"APK_built":False,
    "release_key_accessed":False,"original_source_published":False}
 r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE621_STATUS",r["status"],flush=True)
 print("PRE621_PINNED_FUNCTIONS",list(r.get("pinned_functions",{})),flush=True)
 print("PRE621_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
