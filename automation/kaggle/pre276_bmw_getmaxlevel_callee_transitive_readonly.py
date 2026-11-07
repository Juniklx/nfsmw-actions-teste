#!/usr/bin/env python3
"""PRE276: read-only PRE99 PAL attribute callee audit to depth two.

Audit the four direct callees discovered by PRE275. Report every direct guest
write and immediate call; do not infer purity from zero direct writes.
No PPC invocation, source patches, APK builds, saves or signing access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tarfile
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre276/PRE276_BMW_ATTRIBUTE_CALLEE_TRANSITIVE_AUDIT.json")
PREFIX="workspace/nativo/app/generated/default/"
TARGETS={
 "sub_82148718":"from_sub_8214B858",
 "sub_8214E9E0":"from_sub_8214B858",
 "sub_82145428":"from_sub_8214EDA8",
 "sub_82145C50":"from_sub_8214EDA8",
}
SAVED=[
 "sub_823E5988","sub_8214B858","sub_8214EDA8"
]
DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
ST=re.compile(r"(REX_STORE_U(?:8|16|32|64))\(\s*([^,]+?)\s*,")
LD=re.compile(r"REX_LOAD_U(?:8|16|32|64)\(")
CALL=re.compile(r"(?:__imp__)?(sub_[0-9A-Fa-f]{8})\(ctx,\s*base\);")
CALL_IND=re.compile(r"\b(?:REX_CALL_INDIRECT_FUNC|REX_CALL_INDIRECT)\b|//\s*bctrl\b")
MAX_SOURCE=7_000_000

def context(lines,index,pre=8,post=8):
  return [f"{j+1}: {lines[j].strip()[:200]}"
          for j in range(max(0,index-pre),min(len(lines),index+post+1))]

def analyze(source,fn,path,digest):
  body=body_for_function(source,fn)
  lines=body.splitlines()
  if len(lines)>25000:raise ValueError("Unexpectedly large guest helper")
  stores=[]
  loads=0
  calls=[]
  for i,line in enumerate(lines):
    w=ST.search(line)
    if w:
      address=w.group(2).strip()
      # Do not promote 'ea' to stack just because stwu r1 occurs near the entry.
      scope=("DIRECT_STACK" if address.startswith("ctx.r1.")
             else "AMBIGUOUS_OR_NONSTACK")
      stores.append({"line":i+1,"opcode":w.group(1),"address":address,
         "scope":scope,"nearby":context(lines,i,6,5)})
    loads+=len(LD.findall(line))
    for c in CALL.finditer(line):
      calls.append({"line":i+1,"callee":c.group(1),
        "nearby":context(lines,i,4,5)})
  return {"function":fn,"branch_from":TARGETS[fn],"file":path,
      "file_sha256":digest,"line_count":len(lines),
      "guest_load_count":loads,
      "guest_store_count":len(stores),
      "guest_stores":stores[:140],
      "direct_stack_stores":sum(x["scope"]=="DIRECT_STACK" for x in stores),
      "nonstack_or_ambiguous_stores":sum(x["scope"]!="DIRECT_STACK" for x in stores),
      "direct_callees":calls[:120],
      "indirect_call_detected":bool(CALL_IND.search(body)),
      "first_lines":lines[:18],
      "last_lines":lines[-14:],
      "complete_output":len(stores)<=140 and len(calls)<=120}

def audit():
  with tempfile.TemporaryDirectory(prefix="nfsmw_pre276_") as dirname:
    archive=Path(dirname)/"pre99.tar.gz"
    download(drive_client(),archive)
    digest,_,size=sha_file(archive)
    if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
      raise ValueError("Authenticated PRE99 checksum mismatch")
    found={}
    scanned=0
    with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
      for member in tar:
        path=member.name.lstrip("./")
        if not member.isfile() or not path.startswith(PREFIX) or not path.endswith(".cpp"):
          continue
        if member.size>MAX_SOURCE:raise ValueError("Generated shard too large")
        f=tar.extractfile(member)
        if f is None:raise ValueError("Unable to read a source member")
        raw=f.read()
        if len(raw)!=member.size:raise ValueError("Truncated source member")
        scanned+=1
        if not any(("DEFINE_REX_FUNC("+fn+")").encode() in raw for fn in TARGETS):
          continue
        source=raw.decode("utf-8","replace")
        sha=hashlib.sha256(raw).hexdigest()
        for fn in TARGETS:
          if ("DEFINE_REX_FUNC("+fn+")").encode() not in raw:continue
          if fn in found:raise ValueError("Duplicate definition for "+fn)
          found[fn]=analyze(source,fn,path,sha)
    if scanned<120 or set(found)!=set(TARGETS):
      raise ValueError("Missing PAL sources or direct helper functions")
    risk={}
    for fn,s in found.items():
      risk[fn]={
        "source_file":s["file"],
        "direct_writes":s["guest_store_count"],
        "outside_or_ambiguous_guest_writes":s["nonstack_or_ambiguous_stores"],
        "direct_callees":[v["callee"] for v in s["direct_callees"]],
        "indirect_calls":s["indirect_call_detected"],
        "proven_pure":False
      }
    return {
      "stage":"PRE276_BMW_ATTRIBUTES_SECOND_DEPTH_SIDE_EFFECT_AUDIT",
      "status":"AUDIT_OK",
      "pre99_authenticated_sha256":digest,
      "pal_cpp_files_scanned":scanned,
      "parent_calls_from_PRE275":{
        "sub_8214B858":["sub_82148718","sub_8214E9E0"],
        "sub_8214EDA8":["sub_82145428","sub_82145C50"]
      },
      "helper_bodies":found,
      "helper_risk":risk,
      "refcount_lifecycle_balanced":False,
      "proven_no_side_effects":False,
      "extra_BMW_GetMaxLevel_queries_approved":False,
      "runtime_BMW_upgrade_counts_observed":False,
      "next_step":"Inspect calls/caches/attribute record layout or observe natural runtime calls",
      "limitations":[
        "This static analysis stops at direct callees of the four listed helpers",
        "Even zero direct stores cannot prove pure behavior if callees mutate state",
        "Reference-count pairing depends on actual control flow and object identity",
        "No additional guest function call, patch, APK build or Android runtime test",
        "No game save or permanent signing key accessed"
      ],
      "game_code_modified":False,"apk_built":False,"signed":False,
      "save_modified":False,"signer_accessed":False
    }

def main():
  ap=argparse.ArgumentParser()
  ap.add_argument("--run-id",required=True)
  args=ap.parse_args()
  if not args.run_id.isdecimal():raise ValueError("Invalid GitHub run id")
  OUT.parent.mkdir(parents=True,exist_ok=True)
  result={"stage":"PRE276_BMW_ATTRIBUTES_SECOND_DEPTH_SIDE_EFFECT_AUDIT",
          "status":"FAILED","apk_built":False,"game_code_modified":False}
  try:result=audit()
  except Exception as e:
    result["error_type"]=type(e).__name__
    result["phase"]="AUTHENTICATED_PAL_FUNCTION_SCAN"
  result["github_run_id"]=args.run_id
  result["utc"]=datetime.now(timezone.utc).isoformat()
  OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  print("PRE276_STATUS",result["status"])
  print("PRE276_HELPER_RISK",result.get("helper_risk"))
  print("PRE276_EXTRA_LEVEL_CALLS_APPROVED",result.get("extra_BMW_GetMaxLevel_queries_approved"))
  if result["status"]!="AUDIT_OK":print("PRE276_ERROR",result.get("error_type"))
  return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
  sys.exit(main())
