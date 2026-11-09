#!/usr/bin/env python3
"""PRE599: authenticated PRE99 PPC guest function local counter access provenance.

Extracts only bounded numerical PPC metadata around pvehicle-like offsets and
known front-end/attribute lookup anchors from *private* original recompilation
source, never publishes or patches raw source code. The test asks whether the
candidate GetMaxLevel path actually has engine+other counter read evidence.
No semantic identity is claimed without complete dataflow or runtime tracing.
"""
from __future__ import annotations
import argparse, hashlib, json, re, tarfile, tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256, EXPECTED_BYTES, sha_file
from pre105_read_settings_source import drive_client, download

OUT=Path("/tmp/nfsmw-pre599/report.json")
PREFIX="workspace/nativo/app/generated/default/"
FUNC=re.compile(r"(?m)^\s*DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
PPC=re.compile(r"^\s*//\s*([a-zA-Z][a-zA-Z0-9.]*)\b(.*)$")
LOAD=re.compile(r"^\s*(r\d+),\s*(-?\d+)\((r\d+)\)")
CALL=re.compile(r"__imp__(sub_[0-9A-Fa-f]{8})\s*\(\s*ctx\s*,\s*base\s*\)")
OFFSETS=(40,44,48,52,60,68,72)
TARGETS={
 "sub_82203AB8":"maxlevel_heuristic_7_pvehicle_like_fields",
 "sub_82752E10":"maxlevel_heuristic_7_pvehicle_like_fields",
 "sub_82582F70":"frontend_package_list_caller",
 "sub_8256F818":"frontend_package_list_builder",
 "sub_823E5988":"attribute_lookup_anchor",
 "sub_823E5B08":"attribute_lookup_complex_caller",
 "sub_823E6560":"attribute_numeric_candidate",
 "sub_823E67E8":"attribute_numeric_candidate",
}
FILES={
 "sub_82203AB8":"nfsmw_recomp.59.cpp",
 "sub_82752E10":"nfsmw_recomp.98.cpp",
 "sub_82582F70":"nfsmw_recomp.11.cpp",
 "sub_8256F818":"nfsmw_recomp.57.cpp",
 "sub_823E5988":"nfsmw_recomp.28.cpp",
 "sub_823E5B08":"nfsmw_recomp.48.cpp",
 "sub_823E6560":"nfsmw_recomp.81.cpp",
 "sub_823E67E8":"nfsmw_recomp.15.cpp",
}
def sha(data):return hashlib.sha256(data).hexdigest()
def summarize(body,filename,source_sha):
    lines=body.splitlines()
    comments=[]
    for line_no,line in enumerate(lines,1):
        hit=PPC.match(line)
        if hit:comments.append({"line":line_no,"opcode":hit.group(1).lower(),
                                "args":hit.group(2).strip()})
    details=[]
    load_by_base={}
    for i,p in enumerate(comments):
        if p["opcode"] not in ("lwz","stw"):continue
        m=LOAD.match(p["args"])
        if not m:continue
        reg,off,base=m.group(1),int(m.group(2)),m.group(3)
        if off not in OFFSETS:continue
        load_by_base.setdefault(base,set()).add(off)
        prev=comments[max(0,i-5):i]
        after=comments[i+1:i+7]
        details.append({"line":p["line"],"memory_operation":p["opcode"],
            "offset_decimal":off,"destination_or_source_reg":reg,"base_register":base,
            "previous_opcodes":[x["opcode"] for x in prev[-5:]],
            "following_opcodes":[x["opcode"] for x in after[:6]],
            "following_comparisons":[{"mnemonic":x["opcode"],"operand_signature":x["args"][:70]}
                for x in after if x["opcode"].startswith(("cmp","cmpl"))][:2],
            "next_conditional_branch_within_6_PPC":any(
              x["opcode"] in ("beq","bne","bgt","blt","bge","ble","bdnz")
              for x in after),
            "next_guest_call_within_6_PPC":any(x["opcode"]=="bl" for x in after)})
    # Bounded report; do not publish complete generated source.
    if len(details)>70:raise ValueError("unexpectedly large counter sites, narrow before publishing")
    return {"filename":filename,"source_file_sha256":source_sha,
      "source_function_bytes":len(body.encode("utf-8")),
      "ppc_comment_instruction_count":len(comments),
      "guest_calls_total":len(CALL.findall(body)),
      "guest_call_targets":sorted(set(CALL.findall(body)))[:35],
      "field_40_load_store_sites":details,
      "pvehicle_like_fields_per_base_register":{k:sorted(v) for k,v in load_by_base.items()},
      "comparison_mnemonics":dict(Counter(p["opcode"] for p in comments if p["opcode"].startswith(("cmp","cmpl")))),
      "blr_count":sum(x["opcode"]=="blr" for x in comments),
      "potential_common_base_fields_are_syntactic_not_proven_pvehicle":True,
      "semantic_GetMaxLevel_identity_verified":False}

def audit():
    prior=json.loads(Path("docs/PRE596_BMW_COUNTER_ONE_BYTE_GUEST_SEMANTICS_READONLY.json").read_text())
    candidate=json.loads(Path("docs/PRE487_PAL_PHYSICS_UPGRADE_READ_WRITE_CANDIDATES.json").read_text())
    anchor=json.loads(Path("docs/PRE490_PAL_FUNCTION_ARGS_RETURNS_READONLY.json").read_text())
    if (prior.get("status")!="AUDIT_OK" or prior.get("single_byte_delta_PRE591_vs_PRE502")!=[256619]
        or prior.get("game_runtime_GetMaxLevel_semantics_proven") is not False
        or candidate.get("status")!="AUDIT_OK"
        or candidate.get("semantic_GetMaxLevel_verified") is not False
        or anchor.get("source_PRE99_sha256")!=EXPECTED_SHA256
        or anchor.get("status")!="AUDIT_OK"):
        raise ValueError("PRE596/487/490 authenticated runtime semantics gate absent")
    top={x["function"]:x for x in candidate.get("GetMaxLevel_heuristic_top80",[])}
    for func in ("sub_82203AB8","sub_82752E10"):
        if func not in top:raise ValueError("Original PRE487 maxlevel candidate absent "+func)
        if top[func]["generated_file"]!=FILES[func]:
            raise ValueError("Original candidate generated source filename differs")
    matched={}
    parsed_files=0; parsed_funcs=0
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre599_") as td:
        archive=Path(td)/"original_pre99.tar.gz"
        download(drive_client(),archive)
        source_sha,_,bytecount=sha_file(archive)
        if (source_sha,bytecount)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE99 file SHA/size mismatch; do not parse")
        with tarfile.open(archive,"r:gz",errorlevel=2) as tf:
            for member in tf:
                path=member.name.lstrip("./")
                if not(member.isfile() and path.startswith(PREFIX)
                       and re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",path[len(PREFIX):])
                       and member.size<=12_000_000):
                    continue
                raw=tf.extractfile(member).read()
                if len(raw)!=member.size:raise ValueError("Generated PPC source member truncated")
                filename=path[len(PREFIX):]
                digest=sha(raw)
                content=raw.decode("utf-8","replace")
                starts=list(FUNC.finditer(content))
                parsed_files+=1;parsed_funcs+=len(starts)
                for i,start in enumerate(starts):
                    name=start.group(1)
                    if name not in TARGETS:continue
                    if name in matched:raise ValueError("Duplicate PPC source function")
                    if filename!=FILES[name]:raise ValueError("Candidate relocated into unexpected source file")
                    if name in top and digest!=top[name]["generated_file_sha256"]:
                        raise ValueError("PRE487 candidate source SHA changed")
                    if name in anchor.get("target_functions",{}) and digest!=anchor["target_functions"][name]["generated_file_sha256"]:
                        raise ValueError("PRE490 related source SHA differs")
                    body=content[start.start():starts[i+1].start() if i+1<len(starts) else len(content)]
                    matched[name]=summarize(body,filename,digest)
    if (parsed_files,parsed_funcs)!=(129,56338):raise ValueError("Generated file/function totals changed")
    if set(matched)!=set(TARGETS):raise ValueError("Missing one or more pinned guest functions")
    for f in ("sub_82203AB8","sub_82752E10"):
        loads=[x for x in matched[f]["field_40_load_store_sites"] if x["memory_operation"]=="lwz"]
        if set(x["offset_decimal"] for x in loads)!=set(OFFSETS):
            raise ValueError("Candidate must explicitly load all 7 pvehicle-like offsets")
    return {"stage":"PRE599_GUEST_BMW_LEVEL_COUNTER_AND_ATTR_LOOKUP_PPC_PROVENANCE",
        "status":"AUDIT_OK","source_archive_sha256":source_sha,
        "source_archive_bytes":bytecount,
        "guest_generated_file_count":parsed_files,
        "guest_function_count":parsed_funcs,
        "guest_functions":matched,
        "BMW_engine_counter_binary_offset":256616,
        "counter_read_offset_in_pvehicle_layout":40,
        "exact_GetMaxLevel_identity_proven":False,
        "actual_pvehicle_object_proven_for_pinned_functions":False,
        "exact_SetLevel_identity_proven":False,
        "second_engine_ref_lookup_runtime_proven":False,
        "no_dynamic_guest_exec":True,
        "no_generated_source_published":True,
        "no_game_assets_modified":True,
        "no_APK_built":True,
        "no_save_modified":True,
        "no_signing_access":True}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as exc:r={"stage":"PRE599_GUEST_BMW_LEVEL_COUNTER_AND_ATTR_LOOKUP_PPC_PROVENANCE",
      "status":"FAILED","error_type":type(exc).__name__,"error":str(exc)[:280],
      "no_dynamic_guest_exec":True,"no_generated_source_published":True,
      "no_game_assets_modified":True,"no_APK_built":True,
      "no_save_modified":True,"no_signing_access":True}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE599_STATUS",r["status"],flush=True)
    print("PRE599_PPC_GUEST_FUNCTIONS",len(r.get("guest_functions",{})),flush=True)
    print("PRE599_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
