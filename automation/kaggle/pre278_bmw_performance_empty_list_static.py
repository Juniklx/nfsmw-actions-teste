#!/usr/bin/env python3
"""PRE278: PAL CustomizePerformance Setup->RefreshHeader empty-list audit.

Read-only, authenticated PRE99. Inspect the performance screen Setup candidate
and its trailing calls/virtual call sites. No guest execution, save, build,
signer, UI unlock, or runtime BMW claims.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, tarfile, tempfile
from datetime import datetime, timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre278/PRE278_BMW_PERFORMANCE_EMPTY_LIST_STATIC.json")
SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.11.cpp"
SOURCE_SHA="0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3"
SETUP_CANDIDATE="sub_82582F70"
PARTS_LIST_FUNC="sub_8256F818"
REX=re.compile(r"\b(?:__imp__)?(sub_[A-Fa-f0-9]{8})\(ctx,\s*base\);")
INDIRECT=re.compile(r"\bREX_CALL_INDIRECT_FUNC\b|//\s*bctrl\b")
PTR_COMP=re.compile(r"^\s*//\s*(?:cmpwi|cmplwi)\s+cr\d+,r\d+,0\b",re.I)
MAX_SIZE=7_000_000
MAX_LINES=18000

def snippet(lines,center,pre=16,post=14):
    return [f"{i+1}: {lines[i].strip()[:190]}"
            for i in range(max(0,center-pre),min(len(lines),center+post+1))]

def audit():
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre278_") as d:
        archive=Path(d)/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,size=sha_file(archive)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("Authenticated PRE99 fingerprint mismatch")
        raw=None
        with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
            for m in tar:
                if not m.isfile() or m.name.lstrip("./")!=SOURCE:continue
                if m.size>MAX_SIZE:raise ValueError("Source too large")
                f=tar.extractfile(m)
                if f is None:raise ValueError("Cannot extract source")
                raw=f.read()
                if len(raw)!=m.size:raise ValueError("Truncated source")
                break
        if raw is None or hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
            raise ValueError("Exact PAL source hash mismatch or missing")
        body=body_for_function(raw.decode("utf-8","replace"),SETUP_CANDIDATE)
        lines=body.splitlines()
        if len(lines)>MAX_LINES:raise ValueError("Setup candidate unusually large")
        calls=[]
        indirect=[]
        part_list=[]
        null_guards=[]
        for i,l in enumerate(lines):
            for m in REX.finditer(l):
                calls.append({"line":i+1,"callee":m.group(1),
                  "guest_call_asm":[v.strip()[:135] for v in lines[max(0,i-4):i]
                           if v.lstrip().startswith("//")],
                  "nearby":snippet(lines,i,7,7)})
                if m.group(1)==PARTS_LIST_FUNC:
                    part_list.append({"line":i+1,"context":snippet(lines,i,15,16)})
            if INDIRECT.search(l):
                indirect.append({"line":i+1,"context":snippet(lines,i,10,10)})
            if PTR_COMP.match(l):
                null_guards.append({"line":i+1,"context":snippet(lines,i,4,6)})
        return {
          "stage":"PRE278_BMW_PERFORMANCE_EMPTY_LIST_PAL_STATIC",
          "status":"AUDIT_OK",
          "source_authenticated_sha256":digest,
          "source_file":SOURCE,"source_sha256":SOURCE_SHA,
          "setup_candidate":SETUP_CANDIDATE,
          "setup_candidate_line_count":len(lines),
          "direct_guest_call_count":len(calls),
          "direct_calls":calls[:135],
          "last_direct_calls":calls[-20:],
          "performance_part_list_calls":part_list,
          "indirect_calls":indirect[:60],
          "null_pointer_comparisons_in_setup":null_guards[:60],
          "final_guest_instructions":[f"{i+1}: {lines[i].strip()[:180]}"
                for i in range(max(0,len(lines)-205),len(lines))],
          "public_source_observation":{
             "file":"src/Speed/Indep/Src/Frontend/MenuScreens/Safehouse/customize/CarCustomize.cpp",
             "setup":"CustomizePerformance::Setup calls GetPerformancePartsList, SetInitialOption, then RefreshHeader unconditionally",
             "header":"CustomizePerformance::RefreshHeader uses GetSelectedPart()->GetPhysicsType() without an explicit null guard",
             "status":"PUBLIC_DECOMP_REFERENCE_NOT_V37_RUNTIME_PROOF"
          },
          "refresh_header_guest_function_proven":False,
          "zero_package_handling_in_android_proven":False,
          "menu_unlocked":False,"apk_built":False,"game_source_modified":False,
          "save_modified":False,"signer_accessed":False,
          "limitations":[
             "Guest generated code may optimize or inline high-level methods",
             "Call position alone is not sufficient to prove RefreshHeader identity",
             "No actual BMW GetMaxLevel() result was read",
             "No safe null-guard patch is implemented by this read-only audit",
             "No APK, signing, save change or Android gameplay test"
          ],
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("run id numeric")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE278_BMW_PERFORMANCE_EMPTY_LIST_PAL_STATIC",
            "status":"FAILED","apk_built":False,"game_source_modified":False}
    try:result=audit()
    except Exception as e:result["error_type"]=type(e).__name__
    result["run_id"]=a.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE278_STATUS",result["status"])
    print("PRE278_CALLS",result.get("direct_guest_call_count"))
    print("PRE278_PARTS_LIST_SITES",len(result.get("performance_part_list_calls",[])))
    print("PRE278_LAST_CALLEES",[x["callee"] for x in result.get("last_direct_calls",[])[-10:]])
    print("PRE278_REFRESH_FUNCTION_PROVEN",result.get("refresh_header_guest_function_proven"))
    if result["status"]!="AUDIT_OK":print("PRE278_ERROR",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":sys.exit(main())
