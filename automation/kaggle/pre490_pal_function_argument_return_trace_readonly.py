#!/usr/bin/env python3
"""PRE490 — PAL guest function call/return register evidence, strictly read-only.

Pulls authenticated private PRE99 in a temporary runner and examines source
provenance, branch/return and argument-register context around a fixed
candidate set. Does not infer semantic identities from raw call proximity.
Original generated source is never committed, copied, or published.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre490/report.json")
PROOF=Path("docs/PRE488_PAL_UPGRADE_FUNCTION_NEIGHBORHOOD_READONLY.json")
PREFIX="workspace/nativo/app/generated/default/"
DEF=re.compile(r"(?m)^\s*DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
CALL=re.compile(r"__imp__(sub_[0-9A-Fa-f]{8})\s*\(\s*ctx\s*,\s*base\s*\)")
PPC=re.compile(r"^\s*//\s*([a-zA-Z][a-zA-Z0-9.]*)\b(.*)$")
REX_STORE=re.compile(r"\bREX_STORE_U(8|16|32|64)\s*\(\s*([^,;]+),\s*([^;]+)\)")
REGISTER_ASSIGN=re.compile(r"\bctx\.(r(?:3|4|5|6))(?:\.[a-z0-9]+)?\s*=")
TARGETS=(
 "sub_823E5B08","sub_823E6560","sub_823E67E8",
 "sub_823E5988","sub_823E5AA0","sub_823E4600",
 "sub_823E41C0","sub_823E4130","sub_823E5128",
 "sub_82582F70","sub_8256F818",
 "sub_8256CBB8","sub_8256CBC8"
)
MAX_SITES=32

def ppc_comments(lines):
    return [(i+1,m.group(1).lower(),m.group(2).strip()) for i,l in enumerate(lines)
            if (m:=PPC.match(l)) is not None]

def nearby_ppc(items,line,window=9,direction=-1):
    if direction<0:
        return [{"line":i,"op":op,"args":ops[:100]}
                for i,op,ops in items if i<line][-window:]
    return [{"line":i,"op":op,"args":ops[:100]}
            for i,op,ops in items if i>line][:window]

def local_arguments(lines,line):
    # This is a bounded syntactic trace (NOT live register data flow).
    result={}
    for index in range(max(0,line-25),line):
        source=lines[index]
        match=REGISTER_ASSIGN.search(source)
        if not match:continue
        reg=match.group(1)
        rhs=source.split("=",1)[1].strip()[:110]
        result[reg]={"line":index+1,"assignment_syntax":rhs}
    return result

def inspect_body(body,filename,sha,name):
    lines=body.splitlines()
    comments=ppc_comments(lines)
    counts=Counter(op for _,op,_ in comments)
    callsites=[]
    for idx,line in enumerate(lines):
        match=CALL.search(line)
        if not match:continue
        if len(callsites)<MAX_SITES:
            callsites.append({
                "generated_source_line":idx+1,
                "callee":match.group(1),
                "recent_ppc_ops":nearby_ppc(comments,idx+1,7),
                "guest_register_argument_assignments_syntactic":local_arguments(lines,idx),
                "next_ppc_ops":nearby_ppc(comments,idx+1,3,1),
            })
    allcalls=CALL.findall(body)
    return_sites=[]
    for i,op,args in comments:
        if op!="blr":continue
        if len(return_sites)<18:
            recent=nearby_ppc(comments,i,12)
            # Keep a return-site syntactic snapshot rather than invent r3
            # result certainty across branches.
            assign=local_arguments(lines,i-1)
            return_sites.append({
                "generated_source_line":i,
                "recent_ppc_ops":recent,
                "r3_assignment_syntactic":assign.get("r3"),
            })
    stores=[]
    for idx,line in enumerate(lines):
        m=REX_STORE.search(line)
        if m is None:continue
        addr=m.group(2).strip()
        is_stack="ctx.r1." in addr
        if len(stores)<60:
            stores.append({
                "line":idx+1,"bits":int(m.group(1)),
                "stack_address_explicit":is_stack,
                "address_expr_bounded":addr[:125],
                "value_expr_bounded":m.group(3).strip()[:125],
                "previous_ppc_op":nearby_ppc(comments,idx+1,2)
            })
    return {
        "function":name,
        "generated_file":filename,
        "generated_file_sha256":sha,
        "generated_lines":len(lines),
        "ppc_opcode_counts":dict(counts.most_common(35)),
        "guest_calls_total":len(allcalls),
        "guest_calls_unique":len(set(allcalls)),
        "guest_callsite_samples":callsites,
        "guest_callsite_samples_truncated":len(allcalls)>MAX_SITES,
        "guest_return_count_from_comments":counts["blr"],
        "guest_return_samples":return_sites,
        "guest_return_samples_truncated":counts["blr"]>18,
        "guest_rex_store_occurrences":len(list(REX_STORE.finditer(body))),
        "guest_rex_store_samples":stores,
        "syntax_trace_not_dynamic_proof":True,
        "function_semantic_role_verified":False
    }

def audit():
    p=json.loads(PROOF.read_text())
    if (p.get("status")!="AUDIT_OK" or
        p.get("source_pre99_sha256")!=EXPECTED_SHA256 or
        p.get("GetMaxLevel_address_confirmed") is not False or
        p.get("SetPackage_address_confirmed") is not False):
        raise ValueError("PRE488 provenance/semantic safety proof missing")
    prior=p["suspected_frontend_and_attribute_function_metadata"]
    with tempfile.TemporaryDirectory(prefix="pre490_") as scratch:
        archive=Path(scratch)/"pre99.tar.gz"
        download(drive_client(),archive)
        source_sha,_,source_size=sha_file(archive)
        if (source_sha,source_size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE99 archive not SHA256-and-size authenticated")
        matched={}
        generated_files=0
        guest_functions=0
        with tarfile.open(archive,"r:gz",errorlevel=2) as tar:
            for m in tar:
                path=m.name.lstrip("./")
                if not(m.isfile() and path.startswith(PREFIX) and
                    re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",path[len(PREFIX):]) and
                    m.size<=12_000_000):
                    continue
                source=tar.extractfile(m)
                if source is None:raise ValueError("Missing original generated code member")
                raw=source.read()
                if len(raw)!=m.size:raise ValueError("Original generated code member truncated")
                digest=hashlib.sha256(raw).hexdigest()
                filename=path[len(PREFIX):]
                content=raw.decode("utf-8","replace")
                definitions=list(DEF.finditer(content))
                generated_files+=1
                guest_functions+=len(definitions)
                for i,fn in enumerate(definitions):
                    name=fn.group(1)
                    if name not in TARGETS:continue
                    if name in matched:raise ValueError("Duplicate original PPC guest function")
                    if name in prior:
                        verified=prior[name]
                        if (verified.get("generated_file")!=filename or
                            verified.get("generated_file_sha256")!=digest):
                            raise ValueError("Original PRE488 function signature changed")
                    body=content[fn.start():definitions[i+1].start() if i+1<len(definitions) else len(content)]
                    matched[name]=inspect_body(body,filename,digest,name)
        if (generated_files,guest_functions)!=(129,56338):
            raise ValueError("PRE485/PRE488 original PAL function count mismatch")
        if set(matched)!=set(TARGETS):
            raise ValueError("Expected guest functions absent from authenticated PRE99")
        return {
            "stage":"PRE490_PAL_UPGRADE_GUEST_CALL_RETURN_ARGS_READONLY",
            "status":"AUDIT_OK",
            "source_PRE99_sha256":source_sha,
            "source_archive_bytes":source_size,
            "generated_files_audited":generated_files,
            "guest_functions_audited":guest_functions,
            "target_functions":matched,
            "semantic_GetMaxLevel_proven":False,
            "semantic_SetLevel_proven":False,
            "semantic_SetPackage_proven":False,
            "unresolved":"Guest function roles require ABI/dataflow or runtime corroboration",
            "feature_enabled":False,
            "apk_built":False,
            "save_modified":False,
            "user_game_assets_modified":False,
            "raw_generated_source_published":False
        }
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:doc=audit()
    except Exception as exc:
        doc={"stage":"PRE490_PAL_UPGRADE_GUEST_CALL_RETURN_ARGS_READONLY",
            "status":"FAILED","error_type":type(exc).__name__,
            "error":str(exc)[:280],"feature_enabled":False,"apk_built":False,
            "save_modified":False,"user_game_assets_modified":False,
            "raw_generated_source_published":False}
    doc["run_id"]=args.run_id
    doc["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n")
    print("PRE490_STATUS",doc["status"],flush=True)
    print("PRE490_FUNCTIONS",len(doc.get("target_functions",{})),flush=True)
    print("PRE490_ERROR",doc.get("error_type","none"),flush=True)
    return 0 if doc["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    raise SystemExit(main())
