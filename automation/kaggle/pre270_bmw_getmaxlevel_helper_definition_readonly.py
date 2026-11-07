#!/usr/bin/env python3
"""PRE270: inspect exact PAL package-level helper behind BMW tuning menu.

Read-only authenticated PRE99 scan; no writes to game sources, save or APK.
Matches generated PPC control flow without assuming BMW-level values.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, tarfile, tempfile
from datetime import datetime, timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre270/PRE270_BMW_GETMAXLEVEL_GUEST_HELPER_AUDIT.json")
ROOT="workspace/nativo/app/generated/default/"
OWNER="sub_8256F818"
OWNER_FILE=ROOT+"nfsmw_recomp.57.cpp"
OWNER_SHA="a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c"
TARGETS=("sub_823E5988","sub_8256CB60")
FUNC_RE=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
MAX_FILE=7_000_000

def windows(lines,query,before=16,after=24):
    found=[i for i,v in enumerate(lines) if query in v]
    return [{"line":i+1,"context":[f"{j+1}: {lines[j].strip()[:200]}"
             for j in range(max(0,i-before),min(len(lines),i+after+1))]}
            for i in found[:5]]

def describe_function(src,name,file,sha):
    body=body_for_function(src,name)
    lines=body.splitlines()
    if len(lines)>5000:raise ValueError("Guest helper unexpectedly large")
    calls=[{"line":i+1,"text":line.strip()[:200]}
           for i,line in enumerate(lines) if re.search(r"(?m)(?:__imp__)?sub_[A-Fa-f0-9]{8}\(ctx,\s*base\)",line)]
    op=[{"line":i+1,"asm":line.strip()[:200]}
         for i,line in enumerate(lines) if re.search(r"^\s*//\s*(?:cmpwi|cmplwi|cmpw|cmplw|lwz|lbz|rlwinm|slwi)\b",line)]
    return {
        "function":name,"file":file,"file_sha256":sha,
        "lines":len(lines),"return_register":"r3 (ABI, not semantic proof)",
        "call_sites":calls[:80],"candidate_attribute_instructions":op[:110],
        "source_excerpt":body[:25000],
        "source_excerpt_truncated":len(body)>25000,
        "contains_hardcoded_model41":bool(re.search(r"(?:cmpwi|cmplwi)\s+cr\d+,r\d+,41",body)),
    }

def synthetic(root):
    cpp=root/"pre270_zero_policy_mock.cpp"
    cpp.write_text(r"""
#include <cassert>
#include <iostream>
static bool can_render_first_selection(int available_packages) noexcept {
    return available_packages > 0;
}
int main() {
    unsigned n=0;
    for(int count=-10;count<=15;++count) {
        const bool first=can_render_first_selection(count);
        assert(first==(count>0));
        if(count<=0)assert(!first);
        ++n;
    }
    std::cout<<"PRE270_ZERO_PACKAGE_GUARD "<<n<<" CASES_OK\n";
}
""",encoding="utf-8")
    exe=root/"pre270_mock"
    c=subprocess.run(["g++","-std=c++17","-O1","-Wall","-Wextra","-Werror",
                      str(cpp),"-o",str(exe)],capture_output=True,text=True,timeout=30)
    if c.returncode:return {"passed":False,"compile_returncode":c.returncode}
    p=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
    return {"passed":p.returncode==0,"report":p.stdout.strip(),"cases":26,
            "game_code_executed":False}

def audit():
    with tempfile.TemporaryDirectory(prefix="pre270_") as td:
        root=Path(td)
        arch=root/"pre99.tar.gz"
        download(drive_client(),arch)
        digest,_,size=sha_file(arch)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("Authenticated PRE99 fingerprint mismatch")
        owner=None
        found={}
        scanned=0
        with tarfile.open(arch,"r:gz",errorlevel=2) as tar:
            for m in tar:
                path=m.name.lstrip("./")
                if not m.isfile() or not path.startswith(ROOT) or not path.endswith(".cpp"):
                    continue
                if m.size>MAX_FILE:raise ValueError("Source size exceeds bound")
                f=tar.extractfile(m)
                if f is None:raise ValueError("Unreadable member")
                blob=f.read()
                if len(blob)!=m.size:raise ValueError("Short member read")
                scanned+=1
                if path==OWNER_FILE:
                    if hashlib.sha256(blob).hexdigest()!=OWNER_SHA:
                        raise ValueError("Owner SHA mismatch")
                    owner=blob.decode("utf-8")
                if not any(("DEFINE_REX_FUNC("+t+")").encode() in blob for t in TARGETS):
                    continue
                src=blob.decode("utf-8")
                filehash=hashlib.sha256(blob).hexdigest()
                for name in TARGETS:
                    if "DEFINE_REX_FUNC("+name+")" not in src:continue
                    if name in found:raise ValueError("Duplicate target definition")
                    found[name]=describe_function(src,name,path,filehash)
        if owner is None or len(found)!=len(TARGETS):
            raise ValueError("Missing required source or helper")
        owner_body=body_for_function(owner,OWNER)
        call="__imp__sub_823E5988(ctx, base);"
        if owner_body.count(call)!=2:
            raise ValueError("GetMaxLevel helper call count not two")
        if owner_body.count("sub_8256CB60(ctx, base);")!=1:
            raise ValueError("Maximum-package lookup call count changed")
        lines=owner_body.splitlines()
        first=windows(lines,call,18,19)
        guard=windows(lines,"// cmpwi cr6,r21,0",4,8)
        if len(first)!=2 or len(guard)!=1 or "ble cr6" not in "\n".join(guard[0]["context"]):
            raise ValueError("No fail-closed list-length branch at owner")
        mock=synthetic(root)
        return {
          "stage":"PRE270_BMW_GUEST_GETMAXLEVEL_HELPER_READONLY",
          "status":"AUDIT_OK" if mock["passed"] else "NEEDS_REVIEW",
          "authenticated_backup_sha256":digest,
          "pal_files_scanned":scanned,
          "performance_list_owner":{
             "function":OWNER,"file":OWNER_FILE,"file_sha256":OWNER_SHA,
             "getmaxlevel_candidate_call_sites":first,
             "zero_or_negative_count_prevents_creating_parts":True,
             "zero_count_guard_context":guard,
             "other_max_pkg_call_count":1,
          },
          "helper_definitions":found,
          "host_only_zero_guard_mock":mock,
          "observed_bmw_model_runtime_values":False,
          "confirmed_helper_identity_from_public_decomp":False,
          "release_approved":False,
          "important_limits":[
             "Two calls inside list building are strong GetMaxLevel mapping evidence, not runtime values",
             "Zero-count guard exists in list builder, but performance detail may still dereference empty selected item",
             "No BMW-specific upgrade maximum count measured",
             "No safe activation of BMW performance menu until detail-screen empty-list handling proven",
             "No APK build or guest patch; no signer or save access",
          ],
          "apk_built":False,"signed":False,"source_changed":False,
          "save_changed":False,"password_accessed":False,
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("run id must be decimal")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE270_BMW_GUEST_GETMAXLEVEL_HELPER_READONLY",
            "status":"FAILED","apk_built":False,"source_changed":False}
    try:result=audit()
    except Exception as e:result["error_type"]=type(e).__name__
    result["github_run_id"]=a.run_id
    result["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE270_STATUS",result["status"])
    print("PRE270_HELPERS_FOUND",sorted(result.get("helper_definitions",{})))
    print("PRE270_PAL_FILES",result.get("pal_files_scanned"))
    print("PRE270_BMW_UPGRADE_VALUES_KNOWN",result.get("observed_bmw_model_runtime_values"))
    if result["status"]!="AUDIT_OK":print("PRE270_ERROR",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    sys.exit(main())
