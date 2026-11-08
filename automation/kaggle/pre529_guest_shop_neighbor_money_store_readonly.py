#!/usr/bin/env python3
"""PRE529 read-only guest call triage near shop category list and money writes.

Scan the original authenticated PRE99 PAL PPC C++ source and list only
function call relationships, registers ops and function-local sites.
Do not label guest numeric addresses as PC symbol names unless proved.
The V48 generated binary is NOT audited or edited here.
No game binary, ZIP, save, APK or signing material is changed.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre529/report.json")
ROOT="workspace/nativo/app/generated/default/"
SCAN_FN={
 "category_list":"sub_8256F818",
 "category_list_direct_caller":"sub_82582F70",
 "category_lookup":"sub_823E5988",
 "category_subroutine":"sub_8256C2F0",
 "price_or_category_neighbor_A":"sub_8256CBC8",
 "price_or_category_neighbor_B":"sub_8256CB60",
 "part_install_neighbor_A":"sub_8256BC60",
 "part_install_neighbor_B":"sub_8256D548",
 "part_install_neighbor_C":"sub_8256D5F0",
 "part_install_neighbor_D":"sub_8256D800",
 "historic_money_store_1":"sub_8256BFC8",
 "historic_money_store_2":"sub_82564D80",
}
CALL_TARGETS=set(SCAN_FN.values())
EXACT_CALL=re.compile(r"(?m)^\s*(?:__imp__)?(sub_[0-9a-fA-F]{8})\(ctx,\s*base\);\s*$")
FUNC=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9a-fA-F]{8})\)")
MAX_CALL_SITES=80
MAX_LINES=3500
def analyze_body(blob):
    lines=blob.splitlines()
    if len(lines)>MAX_LINES:raise ValueError("An audited body has unusually many lines")
    calls=list(EXACT_CALL.finditer(blob))
    direct=[]
    for m in calls:
        i=blob.count("\n",0,m.start())
        address=None
        for prev in range(max(0,i-4),i):
            p=re.search(r"\bctx\.lr\s*=\s*(0x8[0-9A-Fa-f]{7})\s*;",lines[prev])
            if p:address=p.group(1)
        direct.append({"target":m.group(1),"guest_lr_at_callsite":address,"relative_line":i+1})
    return {
        "function_lines":len(lines),
        "direct_calls_in_order":direct[:110],
        "direct_call_count":len(direct),
        "guest_read_opcode_counts":dict(Counter(re.findall(r"REX_LOAD_(U8|U16|U32|U64)\(",blob))),
        "guest_write_opcode_counts":dict(Counter(re.findall(r"REX_STORE_(U8|U16|U32|U64)\(",blob))),
        "bracketed_branch_count":len(re.findall(r"(?m)^\s*if\s*\([^\n]+\)\s*goto\s+loc_",blob)),
        "ctx_return_zero_writes":len(re.findall(r"(?m)^\s*ctx\.r3\.[a-z0-9]+\s*=\s*0\s*;",blob)),
        "money_store_offset12_U32_syntax_hits":len(re.findall(r"REX_STORE_U32\(\s*(?:ctx\.r10|ctx\.r11)\.u32\s*\+\s*12\s*,",blob))
    }
def audit():
    prev=json.loads(Path("docs/PRE528_PAL_GUEST_UPGRADE_COUNT_CALLGRAPH_READONLY.json").read_text())
    if (prev.get("status")!="AUDIT_OK" or
        prev.get("source_archive_sha256")!=EXPECTED_SHA256 or
        prev.get("known_UI_builder_has_two_calls_to_attribute_count_lookup") is not True or
        prev.get("historical_codegen_shards_scanned")!=129 or
        prev.get("guest_SetPackage_function_address_identified") is not False):
        raise ValueError("PRE528 provenance or source limits not verified")
    anchored={k:v["sha256"] for k,v in prev["pinned_guest_anchor_functions"].items()}
    callee_sites=defaultdict(list)
    matching={}
    scanned=0
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre529_") as td:
        archive=Path(td)/"pre99.tar.gz"
        download(drive_client(),archive)
        sha,_,size=sha_file(archive)
        if (sha,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("PRE99 private backup hash/size changed")
        with tarfile.open(archive,"r:gz") as tar:
            for item in tar:
                filename=item.name.lstrip("./")
                if not item.isfile() or not filename.startswith(ROOT):
                    continue
                leaf=filename[len(ROOT):]
                if re.fullmatch(r"nfsmw_recomp\.[0-9]+\.cpp",leaf) is None:continue
                scanned+=1
                if scanned>300 or item.size>7_000_000:raise ValueError("Unexpected codegen file")
                reader=tar.extractfile(item)
                if reader is None:raise ValueError("Unable to read original source")
                raw=reader.read()
                if len(raw)!=item.size:raise ValueError("Original shard short read")
                file_sha=hashlib.sha256(raw).hexdigest()
                src=raw.decode("utf-8")
                defs=list(FUNC.finditer(src))
                for fi,defn in enumerate(defs):
                    frompos=defn.start()
                    topos=defs[fi+1].start() if fi+1<len(defs) else len(src)
                    fn=defn.group(1)
                    body=src[frompos:topos]
                    if fn in CALL_TARGETS:
                        if fn in matching:raise ValueError("Duplicate guest definition "+fn)
                        matching[fn]={"filename":leaf,"source_sha256":file_sha,
                                      **analyze_body(body)}
                    for match in EXACT_CALL.finditer(body):
                        tgt=match.group(1)
                        if tgt not in CALL_TARGETS:continue
                        sites=callee_sites[tgt]
                        if len(sites)>=MAX_CALL_SITES:continue
                        rel_line=body.count("\n",0,match.start())+1
                        sites.append({"caller":fn,"caller_source":leaf,
                                      "caller_relative_line":rel_line})
    if set(matching)!=CALL_TARGETS:raise ValueError("Original guest functions missing "+repr(CALL_TARGETS-set(matching)))
    if scanned!=prev["historical_codegen_shards_scanned"]:
        raise ValueError("PRE99 codegen source count differs from PRE528")
    for label,name in SCAN_FN.items():
        if label in ("category_lookup","category_list"):
            sha_expected=prev["pinned_guest_anchor_functions"]["lookup" if label=="category_lookup" else "category_builder"]["sha256"]
            if matching[name]["source_sha256"]!=sha_expected:
                raise ValueError("PRE528 source anchor differs "+name)
    ui=matching["sub_8256F818"]
    if sum(x["target"]=="sub_823E5988" for x in ui["direct_calls_in_order"])!=2:
        raise ValueError("Original package list no longer contains two lookup calls")
    money={k:matching[SCAN_FN[k]] for k in ("historic_money_store_1","historic_money_store_2")}
    if money["historic_money_store_1"]["money_store_offset12_U32_syntax_hits"]<1:
        raise ValueError("PRE239 guest money store probe anchor not found")
    counts={k:len(v) for k,v in callee_sites.items()}
    closest=set(x["target"] for x in ui["direct_calls_in_order"])
    return {
       "stage":"PRE529_PAL_GUEST_SHOP_NEIGHBOR_AND_MONEY_WRITE_CROSSREF_READONLY",
       "status":"AUDIT_OK",
       "historical_archive_sha256":EXPECTED_SHA256,
       "historical_codegen_shard_count":scanned,
       "target_guest_function_count":len(matching),
       "target_guest_definition_metadata":matching,
       "target_guest_direct_call_counts":counts,
       "target_guest_direct_callers":dict(callee_sites),
       "UI_category_builder_direct_calls_for_crossref":sorted(closest),
       "original_money_offset12_write_candidate_count":sum(v["money_store_offset12_U32_syntax_hits"] for v in money.values()),
       "money_offset12_write_is_cash_or_charge_confirmed":False,
       "PC_CarCustomizeManager_Symbol_to_guest_function_verified":False,
       "guest_SetPackage_address_proven":False,
       "guest_checkout_charges_before_install_proven":False,
       "guest_pvehicle_bmw_level1_new_collection_loaded_proven":False,
       "live_V48_caller_equivalence_verified":False,
       "safe_to_enable_BMW_tuning":False,
       "historical_archive_or_original_sources_modified":False,
       "game_assets_or_binaries_published":False,
       "APK_built":False,"save_modified":False,"signing_material_accessed":False
    }
def main():
    a=argparse.ArgumentParser();a.add_argument("--run-id",required=True)
    args=a.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"stage":"PRE529_PAL_GUEST_SHOP_NEIGHBOR_AND_MONEY_WRITE_CROSSREF_READONLY",
        "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
        "historical_archive_or_original_sources_modified":False,"game_assets_or_binaries_published":False,
        "APK_built":False,"save_modified":False,"signing_material_accessed":False,
        "safe_to_enable_BMW_tuning":False}
    r["run_id"]=args.run_id;r["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE529_STATUS",r["status"],flush=True)
    print("PRE529_TARGETS",r.get("target_guest_function_count"),flush=True)
    print("PRE529_MONEY_STORE_CANDIDATES",r.get("original_money_offset12_write_candidate_count"),flush=True)
    print("PRE529_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
