#!/usr/bin/env python3
"""PRE279: PAL CustomizePerformance::RefreshHeader virtual-call investigation.

Static only. Confirms a vtable+12 indirect call in Setup, searches nearby
generated functions for plausible RefreshHeader bodies, inventories any
relevant data sections without exporting copyrighted bytes. Candidate ranks
are NOT addresses proven to be in the CustomizePerformance vtable.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, tarfile, tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre279/PRE279_BMW_REFRESHHEADER_VTABLE_CANDIDATES.json")
PAL="workspace/nativo/app/generated/default/"
SETUP_SOURCE=PAL+"nfsmw_recomp.11.cpp"
SETUP_SHA="0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3"
SETUP="sub_82582F70"
DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
DIRECT_CALL=re.compile(r"(?:__imp__)?(sub_[0-9A-Fa-f]{8})\(ctx,\s*base\);")
INDIRECT=re.compile(r"\bREX_CALL_INDIRECT_FUNC\(ctr\.u32\)")
NEAR_LOW=0x82580000
NEAR_HIGH=0x82587000
MAX_SRC=7_000_000

def around(a,i,b=12,c=12):
    return [f"{j+1}: {a[j].strip()[:185]}" for j in range(max(0,i-b),min(len(a),i+c+1))]

def verify_setup(source):
    body=body_for_function(source,SETUP)
    lines=body.splitlines()
    callsites=[i for i,l in enumerate(lines) if INDIRECT.search(l)]
    matches=[]
    for i in callsites:
        nearby="\n".join(lines[max(0,i-10):i])
        if "REX_LOAD_U32(ctx.r9.u32 + 12)" in nearby and "REX_LOAD_U32(r29.u32 + 0)" in nearby:
            matches.append(i)
    if len(matches)!=1:raise ValueError("Expected exactly one vtable+12 r29 Setup call")
    i=matches[0]
    tail="\n".join(lines[i:i+14])
    if "__imp__sub_82587498(ctx, base);" not in tail:
        raise ValueError("Setup virtual call is not followed by list teardown")
    # Keep the previous virtual call's vtable+60 as a distinct dispatch.
    first=[k for k in callsites if "REX_LOAD_U32(ctx.r11.u32 + 60)" in "\n".join(lines[max(0,k-14):k])]
    if not first:raise ValueError("Missing vtable+60 for initial-option choice")
    return {
       "guest_function":SETUP,"owner_source":SETUP_SOURCE,
       "function_lines":len(lines),"indirect_dispatches":len(callsites),
       "vtable_slot_plus12_call_at_line":i+1,
       "vtable_plus12_context":around(lines,i,12,13),
       "initial_option_vtable_plus60_sites":[j+1 for j in first[-3:]],
       "vtable_plus12_address_not_resolved":True,
       "vtable_pointer_dereference":"r29->vtable + 12",
       "derived_high_level_hint":"virtual RefreshHeader after SetInitialOption",
       "high_level_identity_proved":False,
    }

def score_candidate(fn,body,file,hashname):
    lines=body.splitlines()
    calls=DIRECT_CALL.findall(body)
    vcall=len(INDIRECT.findall(body))
    ptr_access=sum("REX_LOAD_U32" in x for x in lines)
    if len(lines)<55 or len(lines)>1800:return None
    if not (len(calls)>=4 or vcall>=2):return None
    frequent=Counter(calls)
    score=0
    score+=(4 if 0x82581500<=int(fn[4:],16)<0x82584000 else 1)
    score+=min(vcall,7)
    score+=min(len(calls)//3,7)
    score+=(3 if any("ctx.f" in x and "f64" in x for x in lines) else 0)
    score+=(2 if any("REX_STORE_U32" in x for x in lines) else 0)
    score+=(3 if any(c.startswith("sub_8256") for c in calls) else 0)
    score+=(3 if any(c=="sub_823E5988" for c in calls) else 0)
    score+=(3 if any("+ 8)" in x for x in lines) else 0)
    score+=(5 if len(lines)>=160 else 0)
    matching=[{"line":i+1,"guest":" "+lines[i].strip()[:175]}
      for i in range(len(lines)) if INDIRECT.search(lines[i])]
    return {
      "function":fn,"source_file":file,"source_sha256":hashname,
      "lines":len(lines),"score_hint":score,
      "direct_calls":len(calls),"indirect_calls":vcall,
      "guest_load_instructions":ptr_access,
      "called_unique_functions":list(dict.fromkeys(calls))[:60],
      "indirect_call_locations":matching[:14],
      "head":[s[:190] for s in lines[:10]],
      "found_at_vtable_address":False
    }

def audit():
    with tempfile.TemporaryDirectory(prefix="pre279_") as tmp:
      archive=Path(tmp)/"pre99.tar.gz"
      download(drive_client(),archive)
      dig,_,size=sha_file(archive)
      if dig!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 hash mismatch")
      cpp_count=0
      setup=None
      cand=[]
      data_names=[]
      with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
        for m in tar:
          name=m.name.lstrip("./")
          if not m.isfile():continue
          if name.startswith("workspace/nativo/app/") and not name.endswith((".cpp",".hpp",".h",".cc",".c",".txt",".md")):
            # Metadata only. Do not export copyrighted data or source contents.
            if any(t in name.lower() for t in ("generated","recomp","xex","data","rdata")) and len(data_names)<100:
              data_names.append({"path":name,"size":m.size})
          if not name.startswith(PAL) or not name.endswith(".cpp"):continue
          if m.size>MAX_SRC:raise ValueError("Unexpected generated shard size")
          f=tar.extractfile(m)
          if f is None:raise ValueError("Missing source stream")
          raw=f.read()
          if len(raw)!=m.size:raise ValueError("Truncated source shard")
          cpp_count+=1
          filehash=hashlib.sha256(raw).hexdigest()
          if name==SETUP_SOURCE:
            if filehash!=SETUP_SHA:raise ValueError("PRE278 SHA-pinned source mismatch")
            setup=verify_setup(raw.decode("utf-8","replace"))
          if b"DEFINE_REX_FUNC(sub_8258" not in raw:continue
          src=raw.decode("utf-8","replace")
          defs=list(DEF.finditer(src))
          for i,defn in enumerate(defs):
            addr=int(defn.group(1)[4:],16)
            if addr<NEAR_LOW or addr>=NEAR_HIGH:continue
            body=src[defn.start():defs[i+1].start() if i+1<len(defs) else len(src)]
            q=score_candidate(defn.group(1),body,name,filehash)
            if q is not None:cand.append(q)
      if setup is None or cpp_count<120:raise ValueError("Source inventory or setup missing")
      cand.sort(key=lambda x:(-x["score_hint"],-x["indirect_calls"],x["function"]))
      return {
        "stage":"PRE279_BMW_PAL_REFRESHHEADER_VTABLE_TARGET_READONLY",
        "status":"AUDIT_OK",
        "backup_sha256_verified":dig,
        "pal_source_files_examined":cpp_count,
        "setup_vtable_call":setup,
        "nearby_guest_candidate_count":len(cand),
        "ranked_candidates":cand[:60],
        "data_metadata_candidates":data_names[:70],
        "vtable_target_proven":False,
        "null_selection_guard_applied":False,
        "read_only":True,
        "limits":[
          "The vtable+12 slot of the performance screen is identified but its target address is not recovered by the code-only scan",
          "Scores are heuristics; cannot be used for a binary patch",
          "Public decomp source does not prove equivalence with every PAL/USA runtime instruction",
          "Zero-package behavior and actual BMW package levels have not been tested",
          "No game source mutation, signing, saves, or Android build"
        ],
        "apk_built":False,"save_changed":False,"source_changed":False,
        "signer_accessed":False,
      }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("Invalid run ID")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE279_BMW_PAL_REFRESHHEADER_VTABLE_TARGET_READONLY",
           "status":"FAILED","apk_built":False,"source_changed":False}
    try:result=audit()
    except Exception as e:result["error_type"]=type(e).__name__
    result["run_id"]=a.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE279_STATUS",result["status"])
    print("PRE279_VTABLE_SLOT_PLUS12",result.get("setup_vtable_call",{}).get("vtable_slot_plus12_call_at_line"))
    print("PRE279_METHOD_TARGET_PROVEN",result.get("vtable_target_proven"))
    print("PRE279_TOP_CANDIDATES",[(v["function"],v["score_hint"]) for v in result.get("ranked_candidates",[])[:12]])
    print("PRE279_DATA_FILES_FOUND",len(result.get("data_metadata_candidates",[])))
    if result["status"]!="AUDIT_OK":print("PRE279_ERROR",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":sys.exit(main())
