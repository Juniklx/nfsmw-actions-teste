#!/usr/bin/env python3
"""PRE544: inspect original PAL guest PPC lfs/stfs loads/stores and base registers.

Read only from the SHA256-pinned PRE99 archive. Parse numeric instruction
comments (not generated source bodies) for guest float access base registers,
offsets and stack r1 versus non-r1 access.
No source/game/APK/save content modified or published. No inferred SetPackage.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre544/report.json")
ROOT="workspace/nativo/app/generated/default/"
NAMES=("sub_823EAE40","sub_823E4130","sub_823E5988","sub_823EB290","sub_823EB3B0","sub_823E4588")
DEFINE=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9a-fA-F]{8})\)")
COMMENT=re.compile(r"^\s*//\s*([a-z][a-z0-9_.-]{0,15})\s+(.+?)\s*$")
MEMOPS={"lfs","stfs","lwz","stw","lhz","sth","lbz","stb","ld","std","lfd","stfd"}
FP_MEMOPS={"lfs","stfs","lfd","stfd"}
OFFSET=re.compile(r"(?<![A-Za-z0-9_])([+-]?(?:0x[0-9A-Fa-f]+|\d+))\((r\d+)\)")
def mem_audit(body):
    by_op=Counter();by_base=Counter();miss=Counter();stack=Counter();other=Counter();sites=[];offsets=Counter()
    for ix,line in enumerate(body.splitlines()):
        m=COMMENT.match(line)
        if not m or m.group(1) not in MEMOPS:continue
        op=m.group(1)
        by_op[op]+=1
        p=OFFSET.search(m.group(2))
        if not p:miss[op]+=1;continue
        token,base=p.groups()
        off=int(token,16) if "0x" in token.lower() else int(token)
        by_base[(op,base)]+=1
        (stack if base=="r1" else other)[op]+=1
        if abs(off)<=65535:offsets[(op,base,off)]+=1
        if op in FP_MEMOPS and len(sites)<180:
            sites.append({"ppc_opcode":op,"base_guest_register":base,"signed_offset_bytes":off,
                          "function_relative_source_line":ix+1,"r1_stack_relative":base=="r1"})
    return {"PPC_memory_instruction_counts":dict(by_op),
            "unparsed_PPC_memory_operand_count_by_opcode":dict(miss),
            "PPC_memory_op_and_base_register_counts":{f"{op}@{base}":n for (op,base),n in by_base.items()},
            "PPC_fp_memory_access_sites":sites,
            "PPC_r1_stack_memory_instruction_counts":dict(stack),
            "PPC_non_r1_memory_instruction_counts":dict(other),
            "top_PPC_memory_op_base_offset_counts":[{"opcode":op,"base":base,"signed_offset":off,"count":n}
                    for (op,base,off),n in offsets.most_common(25)],
            "PPC_comment_offsets_are_not_executed_dataflow":True}
def audit():
    a=json.loads(Path("docs/PRE541_PAL_GUEST_823EAE40_FOUR_DEPS_PPC_READONLY.json").read_text())
    b=json.loads(Path("docs/PRE542_ORIGINAL_V48_PAL_FLOAT_ATTRIBUTE_COUNT_PATH_READONLY.json").read_text())
    c=json.loads(Path("docs/PRE543_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (a.get("status")!="AUDIT_OK" or b.get("status")!="AUDIT_OK" or c.get("status")!="AUDIT_OK" or
        a.get("PRE99_verified_source_archive_sha256")!=EXPECTED_SHA256 or
        b.get("signed_V48_guest_numeric_two_hop_attribute_count_path_proven") is not True or
        b.get("guest_SetPackage_identity_verified") is not False or
        c.get("new_total_bytes")!=821569 or
        c.get("new_sha256")!="02e3d896f43de7ecf65f28d69f9612e4a16fbc42a637a24517599d22e028ac20"):
        raise ValueError("PRE541/542/543 authenticated source/provenance changed")
    pins=a["target_and_four_guest_callees_original_PPC_records"]
    if set(pins)!=set(NAMES):raise ValueError("PRE541 six sources changed")
    found={}
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre544_") as td:
        path=Path(td)/"pre99.tar.gz"
        download(drive_client(),path)
        digest,_,size=sha_file(path)
        if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE99 historical source SHA/size mismatch")
        numshards=0
        with tarfile.open(path,"r:gz") as tf:
            for m in tf:
                name=m.name.lstrip("./")
                if not m.isfile() or not name.startswith(ROOT):continue
                leaf=name[len(ROOT):]
                if not re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",leaf):continue
                numshards+=1
                candidates=[nm for nm in NAMES if pins[nm]["original_guest_source_shard"]==leaf]
                if not candidates:continue
                if m.size>9_000_000:raise ValueError("Invalid generated shard size")
                reader=tf.extractfile(m)
                if reader is None:raise ValueError("Missing generated member")
                raw=reader.read()
                if len(raw)!=m.size:raise ValueError("Incomplete guest source read")
                sha=hashlib.sha256(raw).hexdigest()
                if any(pins[x]["original_guest_source_sha256"]!=sha for x in candidates):
                    raise ValueError("Pinned source shard SHA mismatch")
                text=raw.decode("utf-8",errors="strict")
                defs=list(DEFINE.finditer(text))
                for i,fn in enumerate(defs):
                    nm=fn.group(1)
                    if nm not in candidates:continue
                    if nm in found:raise ValueError("Duplicate guest source function")
                    end=defs[i+1].start() if i+1<len(defs) else len(text)
                    body=text[fn.start():end]
                    if len(body.splitlines())!=pins[nm]["original_guest_body_line_count"]:
                        raise ValueError("Pinned guest source line count mismatch")
                    x=mem_audit(body)
                    for op,count in x["PPC_memory_instruction_counts"].items():
                        old=pins[nm]["PPC_generated_instruction_comment_mnemonics_top"].get(op)
                        if old is not None and old!=count:
                            raise ValueError("PRE541 mnemonic count mismatch for "+nm+" "+op)
                    found[nm]={"numeric_guest_function":nm,"source_shard_sha256":sha,**x}
        if numshards!=129 or set(found)!=set(NAMES):
            raise ValueError("Historical guest scan incomplete")
    target=found["sub_823EAE40"]["PPC_memory_instruction_counts"]
    if target.get("lfs")!=32 or target.get("stfs")!=24:
        raise ValueError("PPC target original lfs/stfs count changed")
    return {"stage":"PRE544_ORIGINAL_PAL_PPC_FLOAT_MEMORY_BASE_REGISTER_CLASSIFICATION_READONLY",
            "status":"AUDIT_OK",
            "original_PRE99_archive_sha256":EXPECTED_SHA256,
            "original_PRE99_archive_bytes":EXPECTED_BYTES,
            "guest_codegen_shards_seen":numshards,
            "guest_functions_audited":len(found),
            "original_guest_memory_operand_metadata":found,
            "target_original_lfs":32,"target_original_stfs":24,
            "guest_motor_specific_field_name_proven":False,
            "guest_SetPackage_identity_proven":False,
            "guest_synthetic_engine_VPAK_acceptance_proven":False,
            "game_source_assets_or_APK_modified_or_published":False,
            "APK_built":False,"save_modified":False,"signing_material_accessed":False,
            "BMW_tuning_enabled":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as e:
        result={"stage":"PRE544_ORIGINAL_PAL_PPC_FLOAT_MEMORY_BASE_REGISTER_CLASSIFICATION_READONLY",
                "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
                "game_source_assets_or_APK_modified_or_published":False,
                "APK_built":False,"save_modified":False,"signing_material_accessed":False,
                "BMW_tuning_enabled":False}
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE544_STATUS",result["status"])
    x=result.get("original_guest_memory_operand_metadata",{}).get("sub_823EAE40",{})
    print("PRE544_STACK",x.get("PPC_r1_stack_memory_instruction_counts"))
    print("PRE544_NONSTACK",x.get("PPC_non_r1_memory_instruction_counts"))
    print("PRE544_ERROR",result.get("error_type","none"),result.get("error",""))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
