#!/usr/bin/env python3
"""PRE545: trace PPC source register r31 origin for 18 float stores, read only.

Reauthenticate historical PAL PRE99 tar and exact nfsmw_recomp.85.cpp
SHA256. Extract only structural PPC metadata for writes into r31 and
how r31 is initialized from input registers/stack. No binary/game/source
content exported, no APK build, no save access.

A register copied from r3/r4 could be an argument-derived pointer but
this scan does not prove the pointed-to allocation or engine attribute.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre545/report.json")
MEMBER="workspace/nativo/app/generated/default/nfsmw_recomp.85.cpp"
SHARD_SHA="e8c85788d811c0cb9390c35705ea4e60bb7dbd4210ce73d19d6d03358e5cfbf3"
TARGET="sub_823EAE40"
DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9A-Fa-f]{8})\)")
COMMENT=re.compile(r"^\s*//\s*([a-z][a-z0-9_.-]{0,16})\s+(.+?)\s*$")
REG=re.compile(r"(?<![a-z0-9_])(r(?:1|3|4|5|25|28|29|30|31))(?![0-9])",re.I)
STFS=re.compile(r"^\s*//\s*stfs\s+[^,]+,\s*([+-]?(?:\d+|0x[0-9a-fA-F]+))\((r\d+)\)\s*$",re.I)
# Instructions writing the first register operand; exclude store and compare.
WRITE_DEST_OPS={
 "mr","or","ori","oris","li","lis","addi","addis","add","subf","lwz","lwzx",
 "ld","ldx","lhz","lhzx","lbz","lbzx","mflr","mfctr","slwi","srwi",
 "rlwinm","rlwimi","clrlwi","extsw","extsh","extsb","cntlzw","xor","and","andi.",
 "srawi","srw","slw","mulli","mulhw","mullw"
}
def audit():
    p544=json.loads(Path("docs/PRE544_ORIGINAL_PAL_PPC_FLOAT_MEMORY_OFFSETS_READONLY.json").read_text())
    if (p544.get("status")!="AUDIT_OK" or
        p544.get("original_PRE99_archive_sha256")!=EXPECTED_SHA256 or
        p544.get("target_original_stfs")!=24 or
        p544.get("guest_SetPackage_identity_proven") is not False or
        p544.get("BMW_tuning_enabled") is not False):
        raise ValueError("PRE544 source provenance or safety boundary changed")
    rec=p544["original_guest_memory_operand_metadata"][TARGET]
    if (rec["PPC_memory_op_and_base_register_counts"].get("stfs@r31")!=18 or
        rec["PPC_memory_op_and_base_register_counts"].get("stfs@r1")!=6):
        raise ValueError("PRE544 original PPC float output access count changed")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre545_") as td:
        file=Path(td)/"pre99.tar.gz"
        download(drive_client(),file)
        digest,_,size=sha_file(file)
        if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("Original historical PRE99 archive hash/size changed")
        with tarfile.open(file,"r:gz") as tf:
            candidates=[m for m in tf if m.isfile() and m.name.lstrip("./")==MEMBER]
            if len(candidates)!=1 or candidates[0].size>9_000_000:
                raise ValueError("Exact authenticated source shard missing")
            f=tf.extractfile(candidates[0])
            if f is None:raise ValueError("Unable to read original guest source")
            raw=f.read()
            if len(raw)!=candidates[0].size or hashlib.sha256(raw).hexdigest()!=SHARD_SHA:
                raise ValueError("Exact PAL guest source shard SHA mismatch")
            source=raw.decode("utf-8",errors="strict")
        defs=list(DEF.finditer(source))
        index=[i for i,v in enumerate(defs) if v.group(1)==TARGET]
        if len(index)!=1:raise ValueError("Original function not uniquely defined")
        i=index[0]
        body=source[defs[i].start():defs[i+1].start() if i+1<len(defs) else len(source)]
    if len(body.splitlines())!=493:raise ValueError("Original PPC function body length changed")
    assignments=[]
    stores=[]
    instructions=0
    selected=0
    for ix,line in enumerate(body.splitlines()):
        m=COMMENT.match(line)
        if not m:continue
        mnemonic=m.group(1).lower()
        operands=m.group(2).strip()
        instructions+=1
        regs=REG.findall(operands)
        if "r31" in [z.lower() for z in regs]:
            selected+=1
        # Writes to r31 are restricted to ALU/load/move destinations.
        # Some PPC implicit/update-address instructions could still change
        # registers and must remain an explicit analysis limitation.
        first=operands.split(",",1)[0].strip().lower()
        if (mnemonic in WRITE_DEST_OPS and first=="r31" and len(assignments)<60):
            assignments.append({"relative_original_source_line":ix+1,
                "ppc_mnemonic":mnemonic,
                "source_registers_except_r31":[r.lower() for r in regs if r.lower()!="r31"][:5],
                "destination_register":"r31",
                "operand_has_r1_stack_reference":"r1" in [r.lower() for r in regs],
                "operand_has_r3_or_r4_argument_reference":any(r.lower() in ("r3","r4") for r in regs)})
        f=STFS.match(line)
        if f and f.group(2).lower()=="r31":
            token=f.group(1)
            offset=int(token,16) if "0x" in token.lower() else int(token)
            stores.append({"relative_original_source_line":ix+1,
                           "r31_relative_output_offset":offset})
    if len(stores)!=18:
        raise ValueError("Exact original PPC stfs-to-r31 count changed")
    return {
     "stage":"PRE545_ORIGINAL_PAL_PPC_FLOAT_OUTPUT_R31_REGISTER_ORIGIN_READONLY",
     "status":"AUDIT_OK",
     "PRE99_archive_sha256":EXPECTED_SHA256,
     "PRE99_shard_name":"nfsmw_recomp.85.cpp",
     "PRE99_shard_sha256":SHARD_SHA,
     "guest_target_numeric_function":TARGET,
     "original_source_instruction_comments_examined":instructions,
     "PPC_comments_referencing_r31":selected,
     "r31_explicit_destination_assignment_candidates":assignments,
     "stfs_r31_stores_in_code_order":stores,
     "stfs_r31_store_offset_histogram":dict(Counter(str(x["r31_relative_output_offset"]) for x in stores)),
     "number_of_non_r1_fp_output_stores":len(stores),
     "register_origin_only_checked_using_recognized_explicit_destinations":True,
     "any_r31_stack_alias_requires_full_pointer_provenance":True,
     "guest_engine_attr_or_power_change_proven":False,
     "guest_SetPackage_identified":False,
     "APK_built":False,"original_game_source_or_assets_modified_or_published":False,
     "save_modified":False,"signing_material_accessed":False,
     "BMW_tuning_enabled":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as exc:
        r={"stage":"PRE545_ORIGINAL_PAL_PPC_FLOAT_OUTPUT_R31_REGISTER_ORIGIN_READONLY",
           "status":"FAILED","error_type":type(exc).__name__,"error":str(exc)[:230],
           "APK_built":False,"original_game_source_or_assets_modified_or_published":False,
           "save_modified":False,"signing_material_accessed":False,"BMW_tuning_enabled":False}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE545_STATUS",r["status"])
    print("PRE545_R31_WRITES",r.get("r31_explicit_destination_assignment_candidates"))
    print("PRE545_R31_STORES",r.get("stfs_r31_store_offset_histogram"))
    print("PRE545_ERROR",r.get("error_type","none"),r.get("error",""))
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
