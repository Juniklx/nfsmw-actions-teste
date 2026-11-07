#!/usr/bin/env python3
"""PRE267: find guest functions that construct the BMW performance category menu.

Safe static scan on authenticated PRE99. No game patch, build, save, signer.
The decompilation says CustomizeSub::SetupPerformance adds 7 categories in
front room and 7 in back room; match by call multiplicity and structure, not
by guesses about arbitrary source name or any hardcoded save offsets.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre267/PRE267_BMW_SEVEN_PERFORMANCE_CATEGORIES_AUDIT.json")
PFX="workspace/nativo/app/generated/default/"
DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9a-fA-F]{8})\)")
CALL_OPTION=re.compile(r"(?m)^\s*__imp__sub_82575370\(ctx,\s*base\);")
MODEL41=re.compile(r"(?i)\b(?:cmpwi|cmplwi)\s+cr\d+,r\d+,41\b")
MAX_FILE=7_000_000

def scan():
    with tempfile.TemporaryDirectory(prefix="pre267_") as d:
        p=Path(d)/"pre99.tar.gz"
        download(drive_client(),p)
        digest,_md5,size=sha_file(p)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("PRE99 integrity mismatch")
        found=[]
        nfiles=0
        calls_total=0
        arity=Counter()
        with tarfile.open(p,"r:gz",errorlevel=2) as tar:
            for m in tar:
                name=m.name.lstrip("./")
                if not m.isfile() or not name.startswith(PFX) or not name.endswith(".cpp"):continue
                if m.size>MAX_FILE:raise ValueError("oversized PAL generated file")
                stream=tar.extractfile(m)
                if stream is None:raise ValueError("missing member")
                blob=stream.read()
                if len(blob)!=m.size:raise ValueError("truncated member")
                nfiles+=1
                if b"__imp__sub_82575370(ctx, base)" not in blob:continue
                text=blob.decode("utf-8","replace")
                defs=list(DEF.finditer(text))
                for j,ddef in enumerate(defs):
                    a=ddef.start()
                    b=defs[j+1].start() if j+1<len(defs) else len(text)
                    body=text[a:b]
                    calls=list(CALL_OPTION.finditer(body))
                    if not calls:continue
                    count=len(calls); calls_total+=count;arity[count]+=1
                    lines=body.splitlines()
                    if count<6:continue
                    call_lines=[i for i,v in enumerate(lines) if CALL_OPTION.search(v)]
                    samples=[]
                    for k in call_lines[:min(len(call_lines),16)]:
                        win=lines[max(0,k-10):k]
                        samples.append({"call_line":k+1,
                                        "preceding_guest_ops":[x.strip()[:130] for x in win if x.strip().startswith("//")][-6:]})
                    found.append({
                        "function":ddef.group(1),"file":name,
                        "file_sha256":hashlib.sha256(blob).hexdigest(),
                        "call_count":count,"body_lines":len(lines),
                        "model41_comparisons":len(MODEL41.findall(body)),
                        "room_conditional_candidates":[
                          {"line":i+1,"statement":x.strip()[:130]}
                          for i,x in enumerate(lines)
                          if re.search(r"(?i)//\s*(?:lbz|lwz)\s+r\d+,|//\s*cmplwi.*\b0\b",x)
                        ][:22],
                        "menu_calls":samples,
                        "direct_named_callees":re.findall(r"(?:__imp__)?sub_[0-9a-fA-F]{8}\(ctx, base\)",body)[:50]
                    })
        found.sort(key=lambda x:(-x["call_count"],x["function"]))
        strong=[x for x in found if x["call_count"]==14]
        return {
          "stage":"PRE267_BMW_PERFORMANCE_CATEGORY_SETUP_PAL_READONLY",
          "status":"AUDIT_OK" if nfiles>=120 else "NEEDS_REVIEW",
          "pre99_authenticated":True,"pre99_sha256":digest,
          "pal_generated_files_examined":nfiles,
          "menu_addoption_call_count_total":calls_total,
          "multiplicity_distribution":dict(arity),
          "functions_with_6plus_calls":found[:40],
          "exactly_14_call_candidates":[x["function"] for x in strong],
          "mapping_status":"HYPOTHESIS_UNLESS_FURTHER_STRUCTURAL_EVIDENCE",
          "game_code_patched":False,"apk_built":False,
          "signing_accessed":False,"save_accessed":False,
          "limits":[
             "14 calls could be inlined or optimized; no match does not disprove SetupPerformance",
             "Matching call arity alone is insufficient to authorize a patch",
             "Does not retrieve BMW GetMaxLevel runtime values",
             "May be other frontend menus using the same helper",
             "No game execution, no APK, no installed save touched"
          ]
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("Invalid run id")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"status":"FAILED","phase":"START","apk_built":False}
    try:result=scan()
    except Exception as e:result["error_type"]=type(e).__name__
    result["run_id"]=a.run_id
    result["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE267_STATUS",result["status"])
    print("PRE267_MENU_COUNT_DIST",result.get("multiplicity_distribution"))
    print("PRE267_EXACT14",result.get("exactly_14_call_candidates"))
    if result["status"]!="AUDIT_OK":print("PRE267_ERROR",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    sys.exit(main())
