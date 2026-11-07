#!/usr/bin/env python3
"""PRE273: exact PPC customization manager TakeControl candidate cross-check.
Read-only PRE99 authenticated. Does not modify source, APK, signing, or saves.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, tarfile, tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client, download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre273/PRE273_BMW_TAKECONTROL_CROSSCHECK.json")
PAL_ROOT="workspace/nativo/app/generated/default/"
CANDIDATE="sub_8256B440"
SECONDARY="sub_8256B5F8"
CANDIDATE_FILE=PAL_ROOT+"nfsmw_recomp.15.cpp"
CANDIDATE_SHA="414803e217226952833caf347a1ef61dde781a01a8a518262f77196bbc9a0d3a"
DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[a-fA-F0-9]{8})\)")
NEEDLES=(b"__imp__sub_8256B440(ctx, base)", b"__imp__sub_8256B5F8(ctx, base)")
MAX_CPP=7_000_000

def inspect(body,limit=365):
    lines=body.splitlines()
    calls=[]
    offsets=[]
    for i,row in enumerate(lines):
        m=re.search(r"__imp__(sub_[A-Fa-f0-9]{8})\(ctx, base\)",row)
        if m:
            window=lines[max(0,i-10):i+2]
            calls.append({"line":i+1,"callee":m.group(1),
                "guest_arg_setup":[x.strip()[:150] for x in window
                    if x.strip().startswith("//")][-8:]})
        st=re.search(r"(?m)^\s*//\s*st(?:w|b|h)\s+r\d+,(-?\d+)\(r\d+\)",row)
        if st:
            offsets.append({"line":i+1,"offset":int(st.group(1)),
                            "opcode":row.strip()[:110]})
    important=["mr r29,r5","stw r9,448(r31)","stb ","lwz ","g_bCustomizeManager"]
    hits={t:[i+1 for i,x in enumerate(lines) if t in x][:12] for t in important}
    return {
        "total_lines":len(lines),
        "call_count":len(calls),"call_sequence":calls[:65],
        "original_guest_memory_stores":offsets[:100],
        "key_patterns":hits,
        "source_excerpt":[f"{i+1}: {line[:220]}" for i,line in enumerate(lines[:limit])],
        "excerpt_complete":len(lines)<=limit,
        "no_writes_applied":True,
    }

def audit():
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre273_") as t:
        archive=Path(t)/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,length=sha_file(archive)
        if digest!=EXPECTED_SHA256 or length!=EXPECTED_BYTES:
            raise ValueError("Pinned PRE99 mismatch")
        candidate=None
        secondary=None
        callers=[]
        total=0
        with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
            for entry in tar:
                name=entry.name.lstrip("./")
                if not entry.isfile() or not name.startswith(PAL_ROOT) or not name.endswith(".cpp"):
                    continue
                if entry.size>MAX_CPP:raise ValueError("Oversized PAL generated member")
                fp=tar.extractfile(entry)
                if fp is None:raise ValueError("Cannot read PRE99 member")
                raw=fp.read()
                if len(raw)!=entry.size:raise ValueError("Truncated PRE99 member")
                total+=1
                is_target=name==CANDIDATE_FILE
                if is_target:
                    if hashlib.sha256(raw).hexdigest()!=CANDIDATE_SHA:
                        raise ValueError("PRE272 pinned candidate SHA changed")
                    src=raw.decode("utf-8","replace")
                    candidate=inspect(body_for_function(src,CANDIDATE))
                if not any(x in raw for x in NEEDLES) and ("DEFINE_REX_FUNC("+SECONDARY+")").encode() not in raw:
                    continue
                src=raw.decode("utf-8","replace")
                defs=list(DEF.finditer(src))
                for j,df in enumerate(defs):
                    start=df.start()
                    end=defs[j+1].start() if j+1<len(defs) else len(src)
                    body=src[start:end]
                    fn=df.group(1)
                    if fn==SECONDARY:
                        if secondary is not None:raise ValueError("Duplicate secondary definition")
                        secondary={"function":fn,"file":name,
                                   "sha256":hashlib.sha256(raw).hexdigest(),
                                   "details":inspect(body,250)}
                    for callee in (CANDIDATE,SECONDARY):
                        needle="__imp__"+callee+"(ctx, base);"
                        if needle not in body:continue
                        lines=body.splitlines()
                        for k,row in enumerate(lines):
                            if needle not in row:continue
                            callers.append({
                                "caller":fn,"callee":callee,"file":name,
                                "call_index":k+1,
                                "nearby_guest_opcodes":[v.strip()[:150] for v in
                                    lines[max(0,k-18):k+12] if v.strip().startswith("//")][-17:],
                            })
        if candidate is None or secondary is None:
            raise ValueError("Primary/secondary candidate not found")
        candidate_callers=[c for c in callers if c["callee"]==CANDIDATE]
        secondary_callers=[c for c in callers if c["callee"]==SECONDARY]
        return {
            "stage":"PRE273_BMW_TAKECONTROL_CANDIDATE_CROSSCHECK",
            "status":"AUDIT_OK" if total>=125 else "NEEDS_REVIEW",
            "pre99_sha256_verified":digest,
            "pal_cpp_count":total,
            "primary":{"function":CANDIDATE,"file":CANDIDATE_FILE,
                       "sha256":CANDIDATE_SHA,"details":candidate},
            "secondary":secondary,
            "primary_call_sites":candidate_callers[:30],
            "secondary_call_sites":secondary_callers[:35],
            "primary_caller_count":len(candidate_callers),
            "secondary_caller_count":len(secondary_callers),
            "identity_proven":False,
            "runtime_bmw_levels_measured":False,
            "limitations":[
                "PPC structure and high-level decomp can suggest TakeControl, but do not prove exact function identity",
                "Do not call Physics::GetMaxLevel in this candidate until ThePVehicle initialization is verified",
                "PRE99 is baseline, not direct V37 runtime trace",
                "No source, save, APK or credential mutation and no game invocation"
            ],
            "apk_built":False,"save_touched":False,"signer_accessed":False,
            "game_code_modified":False,
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("Run ID must be numeric")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    data={"stage":"PRE273_BMW_TAKECONTROL_CANDIDATE_CROSSCHECK",
          "status":"FAILED","apk_built":False,"game_code_modified":False}
    try:data=audit()
    except Exception as e:data["error_type"]=type(e).__name__
    data["github_run_id"]=a.run_id
    data["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE273_STATUS",data["status"])
    print("PRE273_CANDIDATE",CANDIDATE)
    print("PRE273_SOURCE_CALLS",data.get("primary",{}).get("details",{}).get("call_count"))
    print("PRE273_PRIMARY_CALLERS",data.get("primary_caller_count"))
    print("PRE273_SECONDARY_CALLERS",data.get("secondary_caller_count"))
    if data["status"]!="AUDIT_OK":print("PRE273_ERROR",data.get("error_type"))
    return 0 if data["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    sys.exit(main())
