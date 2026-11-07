#!/usr/bin/env python3
"""PRE272 read-only PAL candidate discovery for entering car customization.

Find guest call sites that configure gCarCustomizeManager, including TuningCar
and pvehicle initialization. Candidate scores never prove method identity.
No game/signer/save writes or APK compilation.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, tarfile, tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre272/PRE272_BMW_TAKECONTROL_PAL_CANDIDATES.json")
ROOT="workspace/nativo/app/generated/default/"
DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
CALL=re.compile(r"(?m)^\s*(?:__imp__)?(sub_[0-9A-Fa-f]{8})\(ctx,\s*base\);")
GLOBAL=re.compile(r"(?m)^\s*//\s*addi\s+r\d+,r\d+,-9752\b")
LI_GLOBAL=re.compile(r"(?m)^\s*//\s*lis\s+r\d+,-32058\b")
WRITE4=re.compile(r"(?m)^\s*//\s*stw\s+r\d+,4\(r\d+\)\s*$")
WRITE0=re.compile(r"(?m)^\s*//\s*stw\s+r\d+,0\(r\d+\)\s*$")
STORE_PTR=re.compile(r"(?m)^\s*//\s*stw\s+r\d+,(?:8|12|16|20|24|28)\(r\d+\)\s*$")
MAX_SOURCE=7_000_000
MAX_RESULTS=36

def nearby(lines,word,limit=3):
    idx=[i for i,s in enumerate(lines) if word in s]
    return [{"line":i+1,"snippet":[f"{j+1}: {lines[j].strip()[:165]}"
        for j in range(max(0,i-8),min(len(lines),i+13))]}
       for i in idx[:limit]]

def candidate(body,fn,file,sha):
    gl=list(GLOBAL.finditer(body))
    names=CALL.findall(body)
    calls=[x for x in names if x.startswith("sub_8256")]
    if not gl and len(calls)<1:return None
    pc=int(fn[4:],16)
    near_ui=0x82574F00<=pc<=0x82579400
    writes4=len(WRITE4.findall(body))
    writes0=len(WRITE0.findall(body))
    phys=len(STORE_PTR.findall(body))
    score=(8 if gl else 0)+(3 if near_ui else 0)+(2 if calls else 0)
    score+=min(writes4,2)+min(writes0,2)+min(phys,4)
    if "821E02C0" in body:score+=3
    if "823E5988" in body:score+=2
    if "-9752" in body and len(calls)>=2:score+=2
    lines=body.splitlines()
    if score<9:return None
    return {"guest_function":fn,"file":file,"file_sha256":sha,"score":score,
            "ui_address_range_hint":near_ui,
            "global_manager_address_mentions":len(gl),
            "candidate_tuning_car_4_store_count":writes4,
            "candidate_pvehicle_field_stores_count":phys,
            "called_sub_8256":calls[:25],
            "direct_call_count":len(names),
            "contexts_global":nearby(lines,"-9752",2),
            "contexts_vehicle_store":nearby(lines,"// stw",1),
            "first_lines":lines[:9]}

def audit():
    with tempfile.TemporaryDirectory(prefix="pre272_") as t:
        backup=Path(t)/"pre99.tar.gz"
        download(drive_client(),backup)
        dig,_md5,size=sha_file(backup)
        if dig!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("PRE99 backup mismatch")
        candidates=[]
        nfiles=0
        sizes=0
        with tarfile.open(backup,"r:gz",errorlevel=2) as tar:
            for m in tar:
                name=m.name.lstrip("./")
                if not m.isfile() or not name.startswith(ROOT) or not name.endswith(".cpp"):
                    continue
                if m.size>MAX_SOURCE:raise ValueError("Source exceeds size bound")
                fp=tar.extractfile(m)
                if fp is None:raise ValueError("Unable to read member")
                raw=fp.read()
                if len(raw)!=m.size:raise ValueError("Short member")
                src=raw.decode("utf-8","replace")
                digest=hashlib.sha256(raw).hexdigest()
                nfiles+=1
                sizes+=len(raw)
                defs=list(DEF.finditer(src))
                if not defs:continue
                for i,d in enumerate(defs):
                    body=src[d.start():defs[i+1].start() if i+1<len(defs) else len(src)]
                    if "-9752" not in body and "sub_8256" not in body:continue
                    v=candidate(body,d.group(1),name,digest)
                    if v is not None:candidates.append(v)
        candidates.sort(key=lambda x:(-x["score"],x["guest_function"]))
        return {
          "stage":"PRE272_BMW_TAKE_CONTROL_GUEST_CANDIDATES_READONLY",
          "status":"AUDIT_OK" if nfiles>=120 else "NEEDS_REVIEW",
          "backup_sha256":dig,"generated_pal_cpp_scanned":nfiles,
          "generated_pal_bytes_scanned":sizes,
          "candidate_count":len(candidates),
          "ranked_candidate_samples":candidates[:MAX_RESULTS],
          "mapped_exact_takecontrol":False,
          "guest_model_41_runtime_levels_captured":False,
          "limitations":[
            "Manager reference/address scoring is heuristic; no symbol identity claimed",
            "A stable moment after pvehicle setup must be proven before calling GetMaxLevel",
            "Read-only search only; no guest function invocation or pointer dereference in game",
            "No APK, no runtime test, no save or signer touched"],
          "source_modified":False,"apk_built":False,"signer_accessed":False,
          "save_modified":False
        }
def main():
    a=argparse.ArgumentParser();a.add_argument("--run-id",required=True)
    opts=a.parse_args()
    if not opts.run_id.isdecimal():raise ValueError("Invalid run id")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    r={"stage":"PRE272_BMW_TAKE_CONTROL_GUEST_CANDIDATES_READONLY",
       "status":"FAILED","apk_built":False,"save_modified":False}
    try:r=audit()
    except Exception as e:r["error_type"]=type(e).__name__
    r["run_id"]=opts.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE272_STATUS",r["status"])
    print("PRE272_CANDIDATES",r.get("candidate_count"))
    print("PRE272_TOP",[(v["guest_function"],v["score"]) for v in r.get("ranked_candidate_samples",[])[:6]])
    if r["status"]!="AUDIT_OK":print("PRE272_ERROR",r.get("error_type"))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
