#!/usr/bin/env python3
"""PRE269: investigate BMW performance package count call chain in pinned PAL code.
Read-only: sources are taken from PRE99 authenticated snapshot. No APK or saves.
All addresses are static candidates until call signatures are proven.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, tarfile, tempfile
from datetime import datetime, timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre269/PRE269_BMW_PERFORMANCE_PACKAGE_COUNT_DATAFLOW.json")
PIN={
  "workspace/nativo/app/generated/default/nfsmw_recomp.11.cpp":
    "0208ca992595ccbddfddc1299f59a2ff586b9c726ad4a3c4d4c73f6dc40db4e3",
  "workspace/nativo/app/generated/default/nfsmw_recomp.34.cpp":
    "c972fcac927c13539fd8a536edfc1827d96353d22ab8fe88816d31ec94b3595a",
  "workspace/nativo/app/generated/default/nfsmw_recomp.90.cpp":
    "4c4be4548441acc9cd703917a71db84e230d522acf164450fc87e9f74fe36a01",
  "workspace/nativo/app/generated/default/nfsmw_recomp.57.cpp":
    "a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c",
}
TARGETS={
  "sub_82582F70":"workspace/nativo/app/generated/default/nfsmw_recomp.11.cpp",
  "sub_8256D2B8":"workspace/nativo/app/generated/default/nfsmw_recomp.34.cpp",
  "sub_8256F9D8":"workspace/nativo/app/generated/default/nfsmw_recomp.90.cpp",
  "sub_8256F818":"workspace/nativo/app/generated/default/nfsmw_recomp.57.cpp",
}
CALL_RE=re.compile(r"(?m)^\s*(?:__imp__)?(sub_[A-Fa-f0-9]{8})\(ctx,\s*base\);")
GUEST_CALL=re.compile(r"(?m)^\s*//\s*(?:bl|bctrl)\b")
COMP=re.compile(r"(?m)^\s*//\s*(?:cmpwi|cmplwi|cmpw|cmplw)\b")
LINE_MAX=420

def short_context(lines, center, before=16, after=24):
    lo=max(0,center-before);hi=min(len(lines),center+after+1)
    return [f"{i+1}: {lines[i].strip()[:205]}" for i in range(lo,hi)]

def analyze(src,func, max_extract):
    body=body_for_function(src,func)
    lines=body.splitlines()
    if len(lines)>2000: raise ValueError("Unexpectedly huge candidate body")
    calls=[]
    for j,line in enumerate(lines):
        c=CALL_RE.search(line)
        if c:
            calls.append({"line":j+1,"function":c.group(1),
                "context":short_context(lines,j,12,20)})
    comparisons=[]
    for j,line in enumerate(lines):
        if COMP.match(line):
            comparisons.append({"line":j+1,"opcode":line.strip()[:120],
                                 "around":short_context(lines,j,4,7)})
    return {"function":func, "line_count":len(lines),
            "calls":calls[:45],"call_count":len(calls),
            "comparisons":comparisons[:45],"comparison_count":len(comparisons),
            "first_lines":[x.strip()[:200] for x in lines[:24]],
            "last_lines":[x.strip()[:200] for x in lines[-24:]],
            "body_excerpt_lines":[f"{i+1}: {line}" for i,line in enumerate(lines[:max_extract])],
            "body_is_complete":len(lines)<=max_extract,
            "return_register_pattern":"PPC ABI r3 return; candidate only"}
def audit():
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre269_") as d:
        arch=Path(d)/"pre99.tar.gz"
        download(drive_client(),arch)
        digest,_md5,n=sha_file(arch)
        if digest!=EXPECTED_SHA256 or n!=EXPECTED_BYTES:raise ValueError("PRE99 fingerprint mismatch")
        sources={}
        with tarfile.open(arch,"r:gz",errorlevel=2) as t:
            for m in t:
                name=m.name.lstrip("./")
                if not m.isfile() or name not in PIN:continue
                if m.size>7_000_000:raise ValueError("Unexpected source size")
                stream=t.extractfile(m)
                if stream is None:raise ValueError("Unreadable source")
                raw=stream.read()
                if len(raw)!=m.size or hashlib.sha256(raw).hexdigest()!=PIN[name]:
                    raise ValueError("Source SHA mismatch")
                sources[name]=raw.decode("utf-8")
        if set(sources)!=set(PIN):raise ValueError("Missing source members")
        funcs={}
        for fn,srcfile in TARGETS.items():
            funcs[fn]=analyze(sources[srcfile],fn, 520 if fn=="sub_8256D2B8" else (170 if fn=="sub_8256F9D8" else 24))
            funcs[fn]["file"]=srcfile
            funcs[fn]["file_sha256"]=PIN[srcfile]
        d2=funcs["sub_8256D2B8"]
        if d2["body_is_complete"] is not True:raise ValueError("Expected complete sub_8256D2B8 source")
        calls=[v["function"] for v in d2["calls"]]
        return {"stage":"PRE269_BMW_PAL_PERFORMANCE_GETMAXLEVEL_DATAFLOW_READONLY",
                "status":"AUDIT_OK",
                "pre99_sha256_authenticated":digest,
                "targets":funcs,
                "caller_to_candidate_hints":{
                    "main_setup_calls_to_sub_8256D2B8":
                        sum(v["function"]=="sub_8256D2B8" for v in funcs["sub_82582F70"]["calls"]),
                    "d2b8_calls_sub_8256F9D8":calls.count("sub_8256F9D8"),
                    "d2b8_other_direct_calls":[x for x in calls if x!="sub_8256F9D8"],
                },
                "model_bmw_runtime_level_counts":None,
                "mapped_exact_getmaxlevel_function":False,
                "status_limits":[
                    "Call graph alone cannot validate actual BMW performance packages",
                    "No executable source modification or in-game code was run",
                    "PPC r3 returns can represent booleans, levels, handles or pointers",
                    "No safe runtime instrumentation point is approved until arguments and ownership are proved",
                    "Do not enable BMW menu before GetMaxLevel=0 has a safe handling path"],
                "source_modified":False,"apk_compiled":False,
                "save_modified":False,"signing_accessed":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("run-id must be decimal")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    out={"stage":"PRE269_BMW_PAL_PERFORMANCE_GETMAXLEVEL_DATAFLOW_READONLY",
         "status":"FAILED","apk_compiled":False,"source_modified":False}
    try:out=audit()
    except Exception as e:
        out["error_type"]=type(e).__name__
        out["phase"]="AUTHENTICATED_SOURCE_READ_OR_SCAN"
    out["run_id"]=a.run_id
    out["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE269_STATUS",out["status"])
    print("PRE269_D2B8_CALLS",out.get("caller_to_candidate_hints"))
    print("PRE269_GETMAXLEVEL_PROVEN",out.get("mapped_exact_getmaxlevel_function"))
    if out["status"]!="AUDIT_OK":print("PRE269_ERROR",out.get("error_type"))
    return 0 if out["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    sys.exit(main())
