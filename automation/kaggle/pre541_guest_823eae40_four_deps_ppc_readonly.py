#!/usr/bin/env python3
"""PRE541: verified original PAL PPC guest-source role evidence, no patch.

On the SHA-pinned PRE99 backup, inspect exactly six numeric functions:
sub_823EAE40, its four direct callees, and sub_823E5988 control.
Extract generated C++ call structure, PPC mnemonic histogram, read/write
opcode counts and literal bounds for hints of general attribute operations.
Compare PRE539 source-independent V48 relocated PLT evidence.

It does not attribute PC class names or label guest SetPackage as verified,
nor modify game binaries/APK/saves or publish source bytes.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre541/report.json")
SRC_ROOT="workspace/nativo/app/generated/default/"
TARGETS=[
 "sub_823EAE40","sub_823EB290","sub_823EB3B0",
 "sub_823E4130","sub_823E4588","sub_823E5988"
]
FUNCS=set(TARGETS)
DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9a-fA-F]{8})\)")
CALL=re.compile(r"(?m)^\s*(?:__imp__)?(sub_[0-9a-fA-F]{8})\(ctx,\s*base\);\s*$")
PPC_COMMENT=re.compile(r"(?m)^\s*//\s*([a-z][a-z0-9_.-]{1,15})(?:\s+|$)")
PPC_PC=re.compile(r"(?m)^\s*//\s*(0x8[0-9A-Fa-f]{7})")
GUEST_LITERAL=re.compile(r"(?<!\w)(0x[0-9a-fA-F]{4,8})(?!\w)")
PTR_TOKEN=re.compile(r"\b(?:REX_(?:STORE|LOAD)_(?:U8|U16|U32|U64)|ctx\.r3\.)")
MAX_SHARD=9_000_000

def audit():
    earlier=json.loads(Path("docs/PRE539_ORIGINAL_V48_PAL_823EAE40_SEVEN_CALLERS_READONLY.json").read_text())
    srcprev=json.loads(Path("docs/PRE528_PAL_GUEST_UPGRADE_COUNT_CALLGRAPH_READONLY.json").read_text())
    if (earlier.get("status")!="AUDIT_OK" or
        earlier.get("exact_target_numeric_guest_name")!="sub_823EAE40" or
        earlier.get("target_incoming_direct_BL_callsite_count")!=9 or
        earlier.get("target_outgoing_resolved_guest_calls")!={x:1 for x in TARGETS[1:5]} or
        earlier.get("target_is_guest_SetPackage_proven") is not False or
        srcprev.get("status")!="AUDIT_OK" or
        srcprev.get("source_archive_sha256")!=EXPECTED_SHA256):
        raise ValueError("PRE528/PRE539 reference provenance or role-proof boundary changed")
    found={}
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre541_") as tmp:
        archive=Path(tmp)/"pre99.tar.gz"
        download(drive_client(),archive)
        digest,_,size=sha_file(archive)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("Historical guest source archive SHA256/size mismatch")
        with tarfile.open(archive,"r:gz") as tar:
            count=0
            for member in tar:
                path=member.name.lstrip("./")
                if not member.isfile() or not path.startswith(SRC_ROOT):
                    continue
                leaf=path[len(SRC_ROOT):]
                if not re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",leaf):
                    continue
                count+=1
                if member.size>MAX_SHARD:
                    raise ValueError("Unexpected guest code generator file size")
                fin=tar.extractfile(member)
                if fin is None:raise ValueError("Unreadable guest shard")
                raw=fin.read()
                if len(raw)!=member.size:raise ValueError("Partial guest source read")
                txt=raw.decode("utf-8",errors="strict")
                defs=list(DEF.finditer(txt))
                if not defs:raise ValueError("Guest shard without guest function definitions")
                file_sha=hashlib.sha256(raw).hexdigest()
                for idx,d in enumerate(defs):
                    name=d.group(1)
                    if name not in FUNCS:continue
                    if name in found:raise ValueError("Duplicate guest function "+name)
                    body=txt[d.start():defs[idx+1].start() if idx+1<len(defs) else len(txt)]
                    ops=Counter(PPC_COMMENT.findall(body))
                    direct=CALL.findall(body)
                    loads=Counter(re.findall(r"REX_LOAD_(U8|U16|U32|U64)\(",body))
                    stores=Counter(re.findall(r"REX_STORE_(U8|U16|U32|U64)\(",body))
                    offsets=Counter()
                    for v in GUEST_LITERAL.findall(body):
                        # Limited to instruction constants, never publish raw
                        # source expressions or game binary bytes.
                        n=int(v,16)
                        if n<=4096:
                            offsets[n]+=1
                    found[name]={
                     "numeric_guest_name":name,
                     "original_guest_source_shard":leaf,
                     "original_guest_source_sha256":file_sha,
                     "original_guest_body_line_count":len(body.splitlines()),
                     "direct_guest_callees_in_order":direct[:60],
                     "total_direct_guest_calls":len(direct),
                     "PPC_generated_instruction_comment_mnemonics_top":dict(ops.most_common(45)),
                     "PPC_comment_instruction_total":sum(ops.values()),
                     "REX_load_opcode_counts":dict(loads),
                     "REX_store_opcode_counts":dict(stores),
                     "return_ctx_r3_mentions":len(re.findall(r"\bctx\.r3\.",body)),
                     "guest_small_integer_literal_references":dict(offsets.most_common(24)),
                     "branch_label_count":len(re.findall(r"(?m)^\s*loc_[0-9A-Fa-f]{8}:",body)),
                     "generated_source_not_executed_on_phone":True
                    }
        if count!=129:raise ValueError("PRE99 generator shard count changed")
        if set(found)!=FUNCS:raise ValueError("Guest target/dependency source functions missing "+str(sorted(FUNCS-set(found))))
    observed=found["sub_823EAE40"]["direct_guest_callees_in_order"]
    if observed!=TARGETS[1:5]:
        raise ValueError("PRE99 source outbound order differs from V48 candidate set; inspect before inferring")
    if len(found["sub_823E5988"]["direct_guest_callees_in_order"])!=2:
        raise ValueError("Known attribute-level read helper expected exactly two source calls")
    return {
      "stage":"PRE541_PAL_GUEST_823EAE40_FOUR_DEPENDENCIES_ORIGINAL_PPC_READONLY",
      "status":"AUDIT_OK",
      "PRE99_verified_source_archive_sha256":EXPECTED_SHA256,
      "PRE99_original_guest_codegen_shards_scanned":count,
      "target_and_four_guest_callees_original_PPC_records":found,
      "source_outbound_matches_V48_PAL_function_names":True,
      "is_source_level_static_audit_only":True,
      "guest_823EAE40_semantic_role_proven":False,
      "guest_Phy_Upgrades_SetPackage_proven":False,
      "guest_engine_bmwm3gtr_new_collection_acceptance_proven":False,
      "compiled_V48_execution_verified":False,
      "APK_built":False,"game_binary_or_assets_modified":False,
      "original_guest_source_published":False,"save_modified":False,
      "signing_key_accessed":False,"tuning_enabled":False
    }

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run-id",required=True)
    args=parser.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:res=audit()
    except Exception as e:
        res={"stage":"PRE541_PAL_GUEST_823EAE40_FOUR_DEPENDENCIES_ORIGINAL_PPC_READONLY",
            "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
            "APK_built":False,"game_binary_or_assets_modified":False,
            "original_guest_source_published":False,"save_modified":False,
            "signing_key_accessed":False,"tuning_enabled":False}
    res["run_id"]=args.run_id
    res["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(res,indent=2,ensure_ascii=False)+"\n")
    print("PRE541_STATUS",res["status"],flush=True)
    print("PRE541_FUNCTIONS",len(res.get("target_and_four_guest_callees_original_PPC_records",{})),flush=True)
    print("PRE541_ERROR",res.get("error_type","none"),res.get("error",""),flush=True)
    return 0 if res["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
