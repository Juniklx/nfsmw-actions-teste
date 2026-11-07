#!/usr/bin/env python3
"""PRE280: SHA-pinned PAL potential CustomizePerformance::RefreshHeader audit.

Read-only static guest function analysis: find the first selected-option access,
null guards, vtable calls and PreviewPerfPkg candidate in sub_82582A40.
This script does not prove vtable linkage or patch the game.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre280/PRE280_BMW_REFRESHHEADER_CANDIDATE_NULL_AUDIT.json")
SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.83.cpp"
PIN="21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4"
FUNCTION="sub_82582A40"
PREVIEW_CANDIDATE="sub_823E4370"
CALL=re.compile(r"(?:__imp__)?(sub_[0-9A-Fa-f]{8})\(ctx,\s*base\);")
INDIRECT=re.compile(r"REX_CALL_INDIRECT_FUNC\(ctr\.u32\)")
NULL_CHECK=re.compile(r"^\s*//\s*(?:cmpwi|cmplwi)\s+cr\d+,r\d+,0\b")
GUEST_LOAD=re.compile(r"\bREX_LOAD_U(?:8|16|32|64)\(")

def context(lines,i,before=13,after=13):
    return [f"{j+1}: {lines[j].strip()[:195]}"
        for j in range(max(0,i-before),min(len(lines),i+after+1))]

def audit():
    with tempfile.TemporaryDirectory(prefix="pre280_") as d:
        p=Path(d)/"pre99.tar.gz"
        download(drive_client(),p)
        dig,_,size=sha_file(p)
        if dig!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("PRE99 fingerprint mismatch")
        raw=None
        with tarfile.open(p,"r:gz",errorlevel=2) as tar:
          for m in tar:
            if not m.isfile() or m.name.lstrip("./")!=SOURCE:continue
            if m.size>7_000_000:raise ValueError("Unexpected C++ file size")
            f=tar.extractfile(m)
            if f is None:raise ValueError("Unreadable source")
            raw=f.read()
            if len(raw)!=m.size:raise ValueError("Truncated source")
            break
        if raw is None or hashlib.sha256(raw).hexdigest()!=PIN:
            raise ValueError("PIN mismatch")
        body=body_for_function(raw.decode("utf-8","replace"),FUNCTION)
        lines=body.splitlines()
        if not 300<=len(lines)<=1800:raise ValueError("Unexpected candidate length")
        direct=[];indirect=[];guards=[];loads=[]
        for i,l in enumerate(lines):
          if INDIRECT.search(l): indirect.append({"line":i+1,"context":context(lines,i,17,15)})
          for m in CALL.finditer(l):
            direct.append({"line":i+1,"callee":m.group(1),
                           "context":context(lines,i,9,9)})
          if NULL_CHECK.search(l):
            guards.append({"line":i+1,"op":l.strip(),"context":context(lines,i,4,8)})
          if GUEST_LOAD.search(l):
            loads.append({"line":i+1,"code":l.strip()[:185]})
        preview=[x for x in direct if x["callee"]==PREVIEW_CANDIDATE]
        if len(preview)!=1:raise ValueError("Preview candidate call count not one")
        first=preview[0]["line"]
        return {
          "stage":"PRE280_BMW_REFRESHHEADER_NULL_SELECTION_STATIC",
          "status":"AUDIT_OK",
          "pre99_sha256_verified":dig,
          "candidate":{"name":FUNCTION,"file":SOURCE,"file_sha256":PIN,
                       "lines":len(lines)},
          "direct_guest_calls":direct[:95],
          "first_direct_callees":[x["callee"] for x in direct[:12]],
          "indirect_guest_calls":indirect[:35],
          "zero_comparisons":guards[:85],
          "preview_candidate":PREVIEW_CANDIDATE,
          "preview_candidate_first_call_line":first,
          "pre_preview_guest_loads":[l for l in loads if l["line"]<first][-35:],
          "pre_preview_zero_guards":[l for l in guards if l["line"]<first],
          "candidate_body_head":[f"{i+1}: {x}" for i,x in enumerate(lines[:230])],
          "candidate_body_tail":[f"{len(lines)-100+i+1}: {x}" for i,x in enumerate(lines[-100:])],
          "guest_vtable_plus12_target_proven":False,
          "null_getselectedpart_guard_proven":False,
          "null_guard_patch_applied":False,
          "limitations":[
             "Caller vtable+12 target not recovered from immutable guest data",
             "PreviewPerfPkg is based on call/ordering hypothesis and must be cross-checked",
             "A zero comparison can guard other values, not necessarily selected part",
             "No safe early-return patch can be approved until full ownership and control flow are identified",
             "No runtime BMW counts, device test, APK build, source or save mutation"
          ],
          "apk_built":False,"game_source_modified":False,
          "save_modified":False,"signer_accessed":False,
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("Numeric run ID required")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE280_BMW_REFRESHHEADER_NULL_SELECTION_STATIC",
            "status":"FAILED","apk_built":False,"game_source_modified":False}
    try:result=audit()
    except Exception as e:result["error_type"]=type(e).__name__
    result["run_id"]=a.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE280_STATUS",result["status"])
    print("PRE280_CANDIDATE",result.get("candidate"))
    print("PRE280_PREVIEW_LINE",result.get("preview_candidate_first_call_line"))
    print("PRE280_GUARD_BEFORE_PREVIEW",len(result.get("pre_preview_zero_guards",[])))
    print("PRE280_VTABLE_IDENTITY_PROVEN",result.get("guest_vtable_plus12_target_proven"))
    if result["status"]!="AUDIT_OK":print("PRE280_ERROR",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":sys.exit(main())
