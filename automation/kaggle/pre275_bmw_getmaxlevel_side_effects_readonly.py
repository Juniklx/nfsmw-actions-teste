#!/usr/bin/env python3
"""PRE275: side-effect static audit of PAL performance level helper call tree.
Authenticated source read only. Does not execute/invoke PPC functions.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys,tarfile,tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre275/PRE275_BMW_GETMAXLEVEL_CALLEE_SIDE_EFFECTS.json")
PAL_ROOT="workspace/nativo/app/generated/default/"
TARGET=("sub_823E5988","sub_8214B858","sub_8214EDA8")
KNOWN={"sub_823E5988":("workspace/nativo/app/generated/default/nfsmw_recomp.28.cpp",
 "11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad")}
DEF_RE=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[a-fA-F0-9]{8})\)")
CALL_RE=re.compile(r"(?m)^\s*(?:__imp__)?(sub_[A-Fa-f0-9]{8})\(ctx,\s*base\);")
STORE_RE=re.compile(r"REX_STORE_U(?:8|16|32|64)\((.+?)\);")
LOAD_RE=re.compile(r"REX_LOAD_U(?:8|16|32|64)\((.+?)\)")
MAX_FILE=7_000_000

def inspect_function(body:str,func:str,path:str,digest:str):
    lines=body.splitlines()
    writes=[]
    reads=[]
    calls=[]
    for i,row in enumerate(lines):
        w=STORE_RE.search(row)
        if w:
            expr=w.group(1).split(",")[0].strip()
            # Only 'ctx.r1' is syntactically direct guest-stack addressing.
            # 'ea' or another PPC register is unknown without dataflow.
            writes.append({"line":i+1,"op":re.search(r"REX_STORE_U(?:8|16|32|64)",row).group(0),
                "addr":expr[:130],
                "direct_stack_address":"ctx.r1." in expr,
                "preceding_asm":[x.strip()[:120] for x in
                    lines[max(0,i-2):i] if x.strip().startswith("//")]})
        r=LOAD_RE.search(row)
        if r:reads.append({"line":i+1,"address_expr":r.group(1)[:120]})
        c=CALL_RE.search(row)
        if c:calls.append({"line":i+1,"callee":c.group(1)})
    non_stack=[x for x in writes if not x["direct_stack_address"]]
    return {
        "function":func,"path":path,"source_sha256":digest,
        "body_line_count":len(lines),
        "guest_read_count":len(reads),
        "guest_store_count":len(writes),
        "direct_guest_stack_stores":len(writes)-len(non_stack),
        "other_or_unknown_address_stores":len(non_stack),
        "stores":writes[:90],
        "reads":reads[:80],
        "direct_callees":calls[:90],
        "has_indirect_calls":bool(re.search(r"REX_CALL_INDIRECT_FUNC|bctrl",body)),
        "entry_and_body_excerpt":body[:28000],
        "excerpt_truncated":len(body)>28000,
        "must_not_assume_pure":True
    }

def audit():
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre275_") as t:
        arch=Path(t)/"pre99.tar.gz"
        download(drive_client(),arch)
        digest,_,size=sha_file(arch)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("Authenticated PRE99 snapshot mismatch")
        found={}
        nfiles=0
        with tarfile.open(arch,"r:gz",errorlevel=2) as tar:
            for m in tar:
                name=m.name.lstrip("./")
                if not m.isfile() or not name.startswith(PAL_ROOT) or not name.endswith(".cpp"):
                    continue
                if m.size>MAX_FILE:raise ValueError("Unexpected oversized PAL source")
                fp=tar.extractfile(m)
                if fp is None:raise ValueError("Source stream missing")
                raw=fp.read()
                if len(raw)!=m.size:raise ValueError("Source truncation")
                nfiles+=1
                present=[x for x in TARGET if ("DEFINE_REX_FUNC("+x+")").encode() in raw]
                if not present:continue
                filehash=hashlib.sha256(raw).hexdigest()
                source=raw.decode("utf-8","replace")
                for func in present:
                    if func in found:raise ValueError("Duplicate guest function")
                    if func in KNOWN and (name,filehash)!=KNOWN[func]:
                        raise ValueError("PRE270 exact helper source fingerprint changed")
                    body=body_for_function(source,func)
                    found[func]=inspect_function(body,func,name,filehash)
        if set(found)!=set(TARGET):
            raise ValueError("Some direct helper functions were not found")
        # PRE270 shows two U16 writes at ctx.r11+18 on distinct paths.
        # They touch a non-stack guest object; no extra calls are approved.
        owner=found["sub_823E5988"]
        u16=[store for store in owner["stores"]
             if store["op"]=="REX_STORE_U16"
             and store["addr"]=="ctx.r11.u32 + 18"
             and not store["direct_stack_address"]]
        if len(u16)!=2:
            raise ValueError("PRE275 expected two external U16 guest writes")
        calls=[x["callee"] for x in owner["direct_callees"]]
        if calls.count("sub_8214B858")!=1 or calls.count("sub_8214EDA8")!=1:
            raise ValueError("PRE275 attribute call chain changed")
        # Inspect no deeper than direct callees; each must be checked if executing
        # GetMaxLevel outside the original game pathway is ever contemplated.
        return {
            "nonstack_u16_18_writes_confirmed":len(u16),
            "nonstack_u16_18_context":u16,
            "reference_count_decrement_is_hypothesis_not_proof":True,
            "decision":"DO_NOT_ADD_SEVEN_EXTRA_GETMAXLEVEL_CALLS",
            "stage":"PRE275_BMW_GETMAXLEVEL_CALLEE_SIDE_EFFECTS_READONLY",
            "status":"AUDIT_OK" if nfiles>=125 else "NEEDS_REVIEW",
            "pre99_sha256_authenticated":digest,
            "pal_files_scanned":nfiles,
            "functions":found,
            "extra_calls_safe_to_inject":False,
            "approved_to_activate_menu":False,
            "guest_code_executed":False,
            "limitations":[
                "A direct guest stack address is not proof of no persistent state changes in callees",
                "Callees and indirect calls beyond first depth require separate dataflow analysis",
                "Source is PRE99 static; runtime objects and BMW model-specific values were not observed",
                "No user save, game source, APK or signing material modified",
                "No seven-category explicit runtime query is approved on this evidence alone"
            ],
            "apk_built":False,"save_modified":False,
            "source_modified":False,"signer_accessed":False
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args()
    if not args.run_id.isdecimal():raise ValueError("Run ID must be numeric")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE275_BMW_GETMAXLEVEL_CALLEE_SIDE_EFFECTS_READONLY",
            "status":"FAILED","apk_built":False,"save_modified":False}
    try:result=audit()
    except Exception as e:result["error_type"]=type(e).__name__
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE275_STATUS",result["status"])
    print("PRE275_BODY_COUNTS",{k:(v["guest_store_count"],v["other_or_unknown_address_stores"],len(v["direct_callees"])) for k,v in result.get("functions",{}).items()})
    print("PRE275_UNSAFE_TO_ASSUME_PURITY",not result.get("extra_calls_safe_to_inject"))
    if result["status"]!="AUDIT_OK":print("PRE275_ERROR",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    sys.exit(main())
