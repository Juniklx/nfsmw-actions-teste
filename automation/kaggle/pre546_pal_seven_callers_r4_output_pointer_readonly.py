#!/usr/bin/env python3
"""PRE546 original PPC PAL seven callers: r4 outgoing result-pointer provenance.

Authenticate PRE99 archive SHA, inspect exactly the seven functions calling
sub_823EAE40. Before each call, identify the nearest PPC instruction that
explicitly sets guest r4 and whether its operand references r1 (stack)
or an already-held guest register. This is bounded static context only.

Never treat a nearest-write as complete reaching-definition analysis:
branching, implicit writes, or prior subroutine calls can invalidate it.
No code/ISO/VPAK/APK/save/signing changes or source export.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre546/report.json")
ROOT="workspace/nativo/app/generated/default/"
TARGET="sub_823EAE40"
CALLERS={
  "sub_8226B228":1,"sub_8226B4C0":1,"sub_8254E908":1,
  "sub_8255C1C8":1,"sub_82566BE8":2,"sub_8256CE68":2,
  "sub_82584880":1
}
DEFINE=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
CALL=re.compile(r"^\s*(?:__imp__)?sub_823EAE40\(ctx,\s*base\);\s*$")
COMMENT=re.compile(r"^\s*//\s*([a-z][a-z0-9_.-]{0,18})\s+(.+?)\s*$")
REG=re.compile(r"(?<!\w)r\d+(?!\w)")
# Destination-writing PPC mnemonics, not stores/compares.
DST={
 "mr","or","ori","oris","li","lis","addi","addis","add","subf","lwz","lwzx",
 "ld","ldx","lhz","lhzx","lbz","lbzx","mflr","mfctr","slwi","srwi",
 "rlwinm","rlwimi","clrlwi","extsw","extsh","extsb","cntlzw","xor","and",
 "andi.","srawi","srw","slw","mulli","mulhw","mullw","rlwnm"
}
MAX_WINDOW_SOURCE_LINES=130
def audit():
    proof=json.loads(Path("docs/PRE545_ORIGINAL_PAL_PPC_R31_FLOAT_OUTPUT_ORIGIN_READONLY.json").read_text())
    prior=json.loads(Path("docs/PRE539_ORIGINAL_V48_PAL_823EAE40_SEVEN_CALLERS_READONLY.json").read_text())
    if (proof.get("status")!="AUDIT_OK" or
        proof.get("PRE99_archive_sha256")!=EXPECTED_SHA256 or
        proof.get("r31_explicit_destination_assignment_candidates")!=[{
            "relative_original_source_line":41,"ppc_mnemonic":"mr",
            "source_registers_except_r31":["r4"],
            "destination_register":"r31",
            "operand_has_r1_stack_reference":False,
            "operand_has_r3_or_r4_argument_reference":True}] or
        proof.get("number_of_non_r1_fp_output_stores")!=18 or
        proof.get("guest_SetPackage_identified") is not False or
        prior.get("status")!="AUDIT_OK" or
        prior.get("target_incoming_distinct_guest_caller_count")!=7 or
        prior.get("target_incoming_direct_BL_callsite_count")!=9 or
        prior.get("target_is_guest_SetPackage_proven") is not False):
        raise ValueError("PRE539/545 authentic original guest PPC output-pointer gate differs")
    found={}
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre546_") as td:
        path=Path(td)/"pre99.tar.gz"
        download(drive_client(),path)
        dig,_,size=sha_file(path)
        if (dig,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("Historical PRE99 source SHA/size differs")
        nshards=0
        with tarfile.open(path,"r:gz") as tf:
            for member in tf:
                p=member.name.lstrip("./")
                if not member.isfile() or not p.startswith(ROOT):continue
                leaf=p[len(ROOT):]
                if not re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",leaf):continue
                nshards+=1
                if member.size>9_000_000:raise ValueError("Invalid guest shard member size")
                f=tf.extractfile(member)
                if f is None:raise ValueError("Cannot read original source shard")
                raw=f.read()
                if len(raw)!=member.size:raise ValueError("Truncated guest source shard")
                txt=raw.decode("utf-8",errors="strict")
                funcs=list(DEFINE.finditer(txt))
                shard_sha=hashlib.sha256(raw).hexdigest()
                for i,m in enumerate(funcs):
                    name=m.group(1)
                    if name not in CALLERS:continue
                    if name in found:raise ValueError("Duplicate original guest numeric function")
                    end=funcs[i+1].start() if i+1<len(funcs) else len(txt)
                    body=txt[m.start():end]
                    lines=body.splitlines()
                    sites=[]
                    for ln,text in enumerate(lines):
                        if not CALL.match(text):continue
                        earlier=lines[max(0,ln-MAX_WINDOW_SOURCE_LINES):ln]
                        options=[]
                        intervening_bl=0
                        for j in range(len(earlier)-1,-1,-1):
                            cm=COMMENT.match(earlier[j])
                            if not cm:continue
                            mnemonic,operand=cm.groups()
                            if mnemonic=="bl":intervening_bl+=1
                            first=operand.split(",",1)[0].strip().lower()
                            if mnemonic in DST and first=="r4":
                                regs=[x.lower() for x in REG.findall(operand)]
                                options.append({
                                  "PPC_guest_instruction_mnemonic":mnemonic,
                                  "source_guest_registers_except_r4":[x for x in regs if x!="r4"][:5],
                                  "relative_source_line":max(0,ln-MAX_WINDOW_SOURCE_LINES)+j+1,
                                  "source_lines_before_target_call":len(earlier)-j,
                                  "operand_mentions_guest_stack_r1":"r1" in regs,
                                  "operand_mentions_existing_argument_r3":"r3" in regs,
                                  "PPC_branch_call_comments_between_assignment_and_call":intervening_bl
                                })
                                if len(options)>=6:break
                        sites.append({
                          "caller_guest_function":name,
                          "target_call_function_relative_source_line":ln+1,
                          "nearest_r4_explicit_write_candidates":options,
                          "nearest_r4_write_found":bool(options),
                          "closest_r4_write_mentions_r1":options[0]["operand_mentions_guest_stack_r1"] if options else None,
                          "closest_r4_write_source_guest_registers":options[0]["source_guest_registers_except_r4"] if options else [],
                          "whole_function_register_reaching_definitions_not_proven":True
                        })
                    found[name]={"original_source_shard":leaf,"original_source_shard_sha256":shard_sha,
                                 "function_source_lines":len(lines),
                                 "guest_numeric_target_call_count":len(sites),
                                 "callsite_r4_preparation_metadata":sites}
        if nshards!=129 or set(found)!=set(CALLERS):
            raise ValueError("Original PRE99 guest shard scan incomplete")
    if any(found[x]["guest_numeric_target_call_count"]!=CALLERS[x] for x in CALLERS):
        raise ValueError("PRE99 call counts to target diverge from 9 authenticated V48 callsites")
    allsites=[z for x in found.values() for z in x["callsite_r4_preparation_metadata"]]
    if len(allsites)!=9:raise ValueError("Not all 9 original guest caller sites found")
    nearest=Counter("r1" if z["closest_r4_write_mentions_r1"] is True else
                    "not_r1" if z["closest_r4_write_mentions_r1"] is False else "unknown"
                    for z in allsites)
    return {
      "stage":"PRE546_ORIGINAL_PAL_SEVEN_CALLERS_R4_OUTPUT_POINTER_PREPARATION_READONLY",
      "status":"AUDIT_OK",
      "verified_PRE99_archive_sha256":EXPECTED_SHA256,
      "original_generated_guest_shards_scanned":nshards,
      "target_numeric_guest_name":TARGET,
      "original_guest_target_r31_comes_from_r4_proven":True,
      "caller_numeric_function_count":len(found),
      "original_guest_direct_caller_sites":len(allsites),
      "caller_r4_nearest_explicit_write_mentions_stack_r1_distribution":dict(nearest),
      "guest_original_PPC_seven_callers":found,
      "nearest_r4_instruction_does_not_establish_pointer_allocation_or_controlflow":True,
      "guest_BMW_engine_attribute_identity_proven":False,
      "guest_SetPackage_identity_proven":False,
      "APK_built":False,"original_game_or_binary_modified_or_published":False,
      "save_modified":False,"signing_material_accessed":False,"BMW_tuning_enabled":False
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"stage":"PRE546_ORIGINAL_PAL_SEVEN_CALLERS_R4_OUTPUT_POINTER_PREPARATION_READONLY",
           "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
           "APK_built":False,"original_game_or_binary_modified_or_published":False,
           "save_modified":False,"signing_material_accessed":False,"BMW_tuning_enabled":False}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE546_STATUS",r["status"])
    print("PRE546_CALLSITES",r.get("original_guest_direct_caller_sites"))
    print("PRE546_R4_STACK",r.get("caller_r4_nearest_explicit_write_mentions_stack_r1_distribution"))
    print("PRE546_ERROR",r.get("error_type","none"),r.get("error",""))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
