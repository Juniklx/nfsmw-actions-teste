#!/usr/bin/env python3
"""PRE549: pvehicle class-hash lookup guest PPC functions and callee, READ ONLY.

Reauthenticate original PRE99 PAL generated code SHA. Inspect only the
13 guest functions with exact validated pvehicle hash constructions from
PRE548 and sub_8214D958 called directly by verified released V48
sub_821E02C0. Count explicit guest memory load/store PPC mnemonics by
stack-vs-other bases and direct guest numeric calls. No function naming
by guess, no SetPackage or actual runtime state inference.

Never export code, change APK, game assets, VPAK, save or signing material.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
OUT=Path("/tmp/nfsmw-pre549/report.json")
ROOT="workspace/nativo/app/generated/default/"
CORE="sub_821E02C0"
HELPER="sub_8214D958"
FUNCTION_DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9a-fA-F]{8})\)")
CALL=re.compile(r"(?m)^\s*(?:__imp__)?(sub_[0-9a-fA-F]{8})\(ctx,\s*base\);\s*$")
COMMENT=re.compile(r"^\s*//\s*([a-z][a-z0-9_.-]{0,16})(?:\s+(.+?))?\s*$",re.I)
MEM=re.compile(r"([-+]?(?:0x[0-9a-fA-F]+|\d+))\((r\d+)\)",re.I)
MEMOPS={"lwz","stw","lhz","sth","lbz","stb","lfs","stfs","ld","std","lfd","stfd"}
WRITEOPS={"stw","sth","stb","stfs","std","stfd"}
def one_function(fn,body,source_sha,shard):
    ops=Counter();mem=Counter();calls=CALL.findall(body);guest_stores=Counter()
    ret=0
    examples=[]
    for line in body.splitlines():
        m=COMMENT.match(line)
        if not m:continue
        op=m.group(1).lower()
        ops[op]+=1
        if op in MEMOPS:
            h=MEM.search(m.group(2) or "")
            base=h.group(2).lower() if h else "unparsed"
            key=(op,base)
            mem[key]+=1
            if op in WRITEOPS:
                guest_stores["r1_stack" if base=="r1" else "other_or_unparsed"]+=1
        if op in ("blr","bclr"):ret+=1
    return {
      "guest_numeric_function":fn,
      "original_guest_shard":shard,
      "original_guest_shard_sha256":source_sha,
      "generated_guest_function_lines":len(body.splitlines()),
      "PPC_comment_opcode_counts_relevant":{k:v for k,v in ops.items() if k in MEMOPS|{"lis","ori","addi","li","mr","bl","blr","bclr","b","beq","bne"}},
      "source_direct_guest_numeric_call_count":len(calls),
      "source_direct_guest_numeric_calls_in_order":calls[:75],
      "PPC_memory_operand_mnemonic_by_base":{
         f"{m}@{base}":n for (m,base),n in sorted(mem.items())
      },
      "PPC_explicit_store_ops_stack_vs_other":dict(guest_stores),
      "PPC_return_opcode_comment_count":ret,
      "PPC_store_base_other_than_r1_does_not_prove_persistent_car_state":True
    }

def audit():
    old=json.loads(Path("docs/PRE548_ORIGINAL_PAL_GUEST_PVEHICLE_UPGRADE_FIELD_XREFS_READONLY.json").read_text())
    graph=json.loads(Path("docs/PRE537_ORIGINAL_V48_PAL_SHARED_NODES_STRUCTURAL_TRIAGE_READONLY.json").read_text())
    p535=json.loads(Path("docs/PRE535_V48_PAL_SHOP_TWO_HOP_PLT_GRAPH_READONLY.json").read_text())
    if (old.get("status")!="AUDIT_OK" or
        old.get("PRE99_archive_sha256")!=EXPECTED_SHA256 or
        old.get("original_guest_functions_scanned")!=56338 or
        old.get("guest_PhysicsUpgrades_SetPackage_address_identified") is not False or
        graph.get("status")!="AUDIT_OK" or
        p535.get("status")!="AUDIT_OK"):
        raise ValueError("PRE548 and V48 known source-to-guest crossrefs changed")
    hits=old["guest_PPC_lis_then_ori_or_addi_hash_candidate_counts"]["pvehicle"]
    names={x["guest_function"] for x in hits["samples"]}
    if hits["matches_total"]!=16 or len(names)!=13 or CORE not in names:
        raise ValueError("PRE548 exact pvehicle class hash guest function anchors changed")
    witness=next((x for x in p535["guest_root_two_hop_intersection_samples"] if x["numeric_function"]==CORE),None)
    verified=next((x for x in graph["audited_shared_numeric_functions"] if x["function"]==CORE),None)
    if (witness is None or verified is None or
        verified["resolved_numeric_guest_callees"]!={HELPER:1} or
        verified["original_V48_ELF_function_bytes"]!=352 or
        witness["ui_root_roles_reaching"]!=["ui_list_caller"] or
        witness["field_writer_root_roles_reaching"]!=["historical_field12_writer_B"]):
        raise ValueError("PRE535/537 original signed V48 pvehicle getter path anchor changed")
    wanted=names|{HELPER}
    found={}
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre549_") as td:
        archive_path=Path(td)/"pre99.tar.gz"
        download(drive_client(),archive_path)
        digest,_,size=sha_file(archive_path)
        if (digest,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("Original historical PAL source archive SHA/size changed")
        count=0
        with tarfile.open(archive_path,"r:gz") as tar:
            for member in tar:
                path=member.name.lstrip("./")
                if not member.isfile() or not path.startswith(ROOT):continue
                shard=path[len(ROOT):]
                if re.fullmatch(r"nfsmw_recomp\.\d+\.cpp",shard) is None:continue
                count+=1
                if member.size>9_000_000:raise ValueError("Generated guest shard unexpectedly large")
                fh=tar.extractfile(member)
                if fh is None:raise ValueError("Unreadable source shard")
                data=fh.read()
                if len(data)!=member.size:raise ValueError("Short authenticated source member")
                sha=hashlib.sha256(data).hexdigest()
                source=data.decode("utf-8",errors="strict")
                definitions=list(FUNCTION_DEF.finditer(source))
                for i,definition in enumerate(definitions):
                    fn=definition.group(1)
                    if fn not in wanted:continue
                    if fn in found:raise ValueError("Duplicate original PAL numeric guest function "+fn)
                    end=definitions[i+1].start() if i+1<len(definitions) else len(source)
                    found[fn]=one_function(fn,source[definition.start():end],sha,shard)
        if count!=129 or set(found)!=wanted:
            raise ValueError("Original PAL archive generated function coverage incomplete")
    core=found[CORE]
    if core["source_direct_guest_numeric_calls_in_order"]!=[HELPER]:
        raise ValueError("PRE549 PPC source pvehicle getter call list differs from signed V48 PLT")
    merged=Counter()
    for name in names:
        v=found[name]
        merged.update({"call_stores_"+k:v["PPC_explicit_store_ops_stack_vs_other"].get(k,0) for k in
                    ("r1_stack","other_or_unparsed")})
    return {
      "stage":"PRE549_ORIGINAL_PAL_GUEST_PVEHICLE_CLASS_HASH_LINKED_V48_ACCESSOR_TRIAGE_READONLY",
      "status":"AUDIT_OK",
      "original_PRE99_archive_sha256":EXPECTED_SHA256,
      "original_guest_codegen_shards_scanned":count,
      "original_guest_functions_audited":len(found),
      "pvehicle_hash_materializing_function_count":len(names),
      "pvehicle_hash_construction_site_count":hits["matches_total"],
      "original_guest_hash_function_numeric_records":{k:found[k] for k in sorted(names)},
      "class_lookup_candidate_direct_guest_callee":HELPER,
      "class_lookup_candidate_original_guest_record":core,
      "class_lookup_helper_original_guest_record":found[HELPER],
      "selected_guest_pvehicle_hash_functions_PPC_store_aggregate":dict(merged),
      "original_signed_V48_PAL_pvehicle_getter_same_guest_callee_confirmed":True,
      "original_signed_V48_PAL_getter_reachable_from_shop_and_historical_field_writer":True,
      "pvehicle_class_hash_lookup_is_not_a_package_installation":True,
      "direct_guest_SetPackage_or_checkout_identity_proven":False,
      "original_guest_source_or_game_modified_or_published":False,
      "APK_built":False,"save_modified":False,
      "signing_material_accessed":False,"BMW_tuning_enabled":False
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:res=audit()
    except Exception as e:
        res={"stage":"PRE549_ORIGINAL_PAL_GUEST_PVEHICLE_CLASS_HASH_LINKED_V48_ACCESSOR_TRIAGE_READONLY",
             "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
             "original_guest_source_or_game_modified_or_published":False,
             "APK_built":False,"save_modified":False,"signing_material_accessed":False,
             "BMW_tuning_enabled":False}
    res["run_id"]=args.run_id
    res["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n")
    print("PRE549_STATUS",res["status"])
    print("PRE549_PVEHICLE_HASH_FUNCTIONS",res.get("pvehicle_hash_materializing_function_count"))
    print("PRE549_CORE_STORES",res.get("class_lookup_candidate_original_guest_record",{}).get("PPC_explicit_store_ops_stack_vs_other"))
    print("PRE549_ERROR",res.get("error_type","none"),res.get("error",""))
    return 0 if res["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
