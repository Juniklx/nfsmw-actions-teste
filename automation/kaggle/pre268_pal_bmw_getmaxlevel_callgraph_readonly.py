#!/usr/bin/env python3
"""PRE268 PAL performance UI / GetMaxLevel dataflow source audit, read-only.

Public decomp and PPC function addresses are hypotheses, not exact symbols.
Audit only exact SHA-pinned generated C++ of the PRE99 backup. Never patch.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre268/PRE268_PAL_BMW_GETMAXLEVEL_CANDIDATES.json")
PINS={
 "workspace/nativo/app/generated/default/nfsmw_recomp.39.cpp":"ac9c0f8f5d69a59c390010227263ece19ae4688ef4bc4d30d16ed622879bd0e4",
 "workspace/nativo/app/generated/default/nfsmw_recomp.34.cpp":"c972fcac927c13539fd8a536edfc1827d96353d22ab8fe88816d31ec94b3595a",
 "workspace/nativo/app/generated/default/nfsmw_recomp.90.cpp":"4c4be4548441acc9cd703917a71db84e230d522acf164450fc87e9f74fe36a01",
 "workspace/nativo/app/generated/default/nfsmw_recomp.57.cpp":"a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c",
}
FUNCTIONS={
 "sub_825767F0":"workspace/nativo/app/generated/default/nfsmw_recomp.39.cpp",
 "sub_8256D2B8":"workspace/nativo/app/generated/default/nfsmw_recomp.34.cpp",
 "sub_8256F9D8":"workspace/nativo/app/generated/default/nfsmw_recomp.90.cpp",
 "sub_8256F818":"workspace/nativo/app/generated/default/nfsmw_recomp.57.cpp",
}
REX=re.compile(r"(?:__imp__)?sub_([0-9a-fA-F]{8})\(ctx,\s*base\)")
OPTION=re.compile(r"(?:__imp__)?sub_82575370\(ctx,\s*base\)")
GEOM=("// cmplw","// cmplwi","// cmpwi","// cmpw","// beq","// bne",
      "// bge","// bgt","// ble","// blt")

def audit():
    with tempfile.TemporaryDirectory(prefix="pre268_") as d:
        tarpath=Path(d)/"pre99.tar.gz"
        download(drive_client(),tarpath)
        h,_,size=sha_file(tarpath)
        if h!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 mismatch")
        data={}
        with tarfile.open(tarpath,"r:gz",errorlevel=2) as tar:
            for m in tar:
                name=m.name.lstrip("./")
                if not m.isfile() or name not in PINS:continue
                if m.size>7_000_000:raise ValueError("Unexpected generated size")
                f=tar.extractfile(m)
                if f is None:raise ValueError("Unreadable source")
                raw=f.read()
                if len(raw)!=m.size or hashlib.sha256(raw).hexdigest()!=PINS[name]:
                    raise ValueError("Pinned source SHA mismatch")
                data[name]=raw.decode("utf-8")
        if set(data)!=set(PINS):raise ValueError("Pinned target missing")
        selected={}
        for fun,path in FUNCTIONS.items():
            body=body_for_function(data[path],fun)
            lines=body.splitlines()
            calls=[]
            for i,s in enumerate(lines):
                if REX.search(s):
                    if len(calls)<75:
                        calls.append({"line":i+1,"target":REX.search(s).group(1),
                                      "preceding_guest_instructions":[
                                         t.strip()[:140] for t in lines[max(0,i-14):i]
                                         if t.lstrip().startswith("//")][-8:]})
            loop_controls=[{"line":i+1,"opcode":s.strip()[:160]}
                for i,s in enumerate(lines)
                if s.lstrip().startswith(GEOM)]
            options=[]
            for i,s in enumerate(lines):
                if not OPTION.search(s):continue
                prev=lines[max(0,i-24):i]
                li_r7=[x.strip()[:140] for x in prev if re.search(r"//\s*li r7,\s*\d+",x)]
                options.append({"line":i+1,
                   "nearest_category_instruction":li_r7[-1:] or [],
                   "branch_window":[x.strip()[:140] for x in lines[max(0,i-11):i+1]
                      if x.strip().startswith("//")][-9:]})
            selected[fun]={
                "file":path,"sha256":PINS[path],
                "lines":len(lines),"calls":calls,
                "option_calls":len(options),
                "option_context":options[:25],
                "branches":loop_controls[:90],
                "head":lines[:18],
                "tail":lines[-20:],
            }
        candidate=selected["sub_825767F0"]
        category_5=sum(any(f"li r7,{i}" in str(x) for x in candidate["option_context"]) for i in (513,514,515,516,517,518,519))
        return {
          "stage":"PRE268_BMW_PAL_UI_AND_PERF_PACKAGE_DATAFLOW_READONLY",
          "status":"AUDIT_OK",
          "pre99_verified":h,"selected":selected,
          "setup_performance_candidate":"sub_825767F0",
          "performance_list_candidate":"sub_8256D2B8",
          "identity_proven_by_runtime":False,
          "known_actual_bmw_package_counts":False,
          "menu_categories_from_public_decomp":7,
          "option_call_count_candidate":candidate["option_calls"],
          "guest_model_type_values_read":False,
          "category_numeric_id_leads":["513","514","515","516","517","518","519"],
          "limitations":[
            "A call/argument pattern does not independently identify high-level method name",
            "Cannot infer actual GetMaxLevel( BMW, type ) from static call graph alone",
            "The seven category menu options can be emitted without any valid upgrade package",
            "Zero-option screen remains a genuine untested runtime risk",
            "No game source modified, APK built, signing accessed, or save touched",
          ],
          "patch_applied":False,"apk_built":False,"save_touched":False,
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("invalid run-id")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    r={"stage":"PRE268_BMW_PAL_UI_AND_PERF_PACKAGE_DATAFLOW_READONLY","status":"FAILED",
       "game_code_modified":False,"apk_built":False}
    try:r=audit()
    except Exception as e:r["error_type"]=type(e).__name__
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE268_STATUS",r["status"])
    print("PRE268_OPTION_CALLS",r.get("option_call_count_candidate"))
    print("PRE268_BMW_GETMAXLEVEL_KNOWN",False)
    if r["status"]!="AUDIT_OK":print("PRE268_ERROR",r.get("error_type"))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
