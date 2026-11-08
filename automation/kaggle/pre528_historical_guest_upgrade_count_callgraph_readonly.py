#!/usr/bin/env python3
"""PRE528: source-anchored PAL guest package-count callgraph, read-only.

Authenticate private 874,780,689-byte PRE99 archive before scanning. Inspect
generated C++ guest functions, pin exact known original files, report only
instruction-level call metadata and bounded source locations. The PPC guest
routine names are guessed NONE; use original numeric identities.
Historical source is not a runtime execution of released V48. Never mutate
archive, game, APK, save or signing material.
"""
from __future__ import annotations
import argparse,hashlib,json,re,tarfile,tempfile
from collections import Counter,defaultdict
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre528/report.json")
ROOT="workspace/nativo/app/generated/default/"
SHARDS={
 "ui_entry":("nfsmw_recomp.15.cpp","414803e217226952833caf347a1ef61dde781a01a8a518262f77196bbc9a0d3a","sub_8256B440"),
 "lookup":("nfsmw_recomp.28.cpp","11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad","sub_823E5988"),
 "category_builder":("nfsmw_recomp.57.cpp","a74e2314e878a88d197d2d8774254bf8c7fbc0e835f84a6c048f0ec86d9f455c","sub_8256F818"),
 "attribute_check":("nfsmw_recomp.50.cpp","f20ec567de4c4637756977a71a6c85f3848b63ba639f037b819868328e3f7e9d","sub_8214B858"),
 "attribute_read":("nfsmw_recomp.83.cpp","21e561eeae953888b7d645719dc6bd7077dfa040f3f06896b7bbe3ba3e7774d4","sub_8214EDA8")
}
TARGET_CALLEES={v[2] for v in SHARDS.values()}
FUNCTION_DEF=re.compile(r"(?m)^DEFINE_REX_FUNC\((sub_[0-9a-fA-F]{8})\)")
EXACT_CALL=re.compile(r"(?m)^\s*(?:__imp__)?(sub_[0-9a-fA-F]{8})\(ctx,\s*base\);\s*$")
REF_LINE=re.compile(r"(?m)^.*\b(__imp__)?sub_([0-9a-fA-F]{8})\(ctx,\s*base\);.*$")
RETURNS={
 "sub_823E5988":{"known_zero_sites":2,
                  "known_read_return_site":1,
                  "ppc_return_site_to_ui_count":"0x8256F83C"}
}
CAP_PER_TARGET=110
MAX_CODEGEN=1600

def sample_site(lines,index):
    sample=[]
    for j in range(max(0,index-4),min(len(lines),index+2)):
        stripped=lines[j].strip()
        # Codegen only, don't publish private source lines or register pointers.
        if "ctx.lr" in stripped and re.search(r"0x8[0-9a-fA-F]{7}",stripped):
            v=re.search(r"0x8[0-9a-fA-F]{7}",stripped)
            if v:sample.append({"relative_line":j-index,"guest_return_address":v.group(0)})
    return sample

def audit():
    prev=json.loads(Path("docs/PRE526_PC_SHOP_CHECKOUT_PHYSICS_SAFETY_READONLY.json").read_text())
    if (prev.get("status")!="AUDIT_OK" or
        prev.get("guest_V48_GetMaxLevel_or_SetPackage_behavior_verified") is not False or
        prev.get("PhysicsUpgrades_cpp_public_reference_body_bytes")!=0 or
        prev.get("safe_to_build_BMW_tuning_APK") is not False):
        raise ValueError("PRE526 safety and PC-source limitation gate absent")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre528_") as td:
        source_path=Path(td)/"authenticated_pre99.tar.gz"
        download(drive_client(),source_path)
        sha,_,size=sha_file(source_path)
        if (sha,size)!=(EXPECTED_SHA256,EXPECTED_BYTES):
            raise ValueError("Historical PRE99 private archive SHA256 and size changed")
        expected={ROOT+v[0]:k for k,v in SHARDS.items()}
        targets={}
        all_calls=defaultdict(list)
        matches_count=Counter()
        scanned_files=0
        unique_functions=0
        total_code_bytes=0
        with tarfile.open(source_path,"r:gz") as archive:
            for member in archive:
                path=member.name.lstrip("./")
                if not member.isfile() or not path.startswith(ROOT):
                    continue
                leaf=path[len(ROOT):]
                if re.fullmatch(r"nfsmw_recomp\.[0-9]+\.cpp",leaf) is None:
                    continue
                scanned_files+=1
                if scanned_files>MAX_CODEGEN or member.size>7_000_000 or member.size<100:
                    raise ValueError("Unexpected codegen file count or size: "+leaf)
                fh=archive.extractfile(member)
                if fh is None:raise ValueError("Unreadable authenticated generated shard "+leaf)
                data=fh.read()
                if len(data)!=member.size:raise ValueError("Codegen archive member short")
                total_code_bytes+=len(data)
                fp=hashlib.sha256(data).hexdigest()
                if path in expected:
                    key=expected[path]
                    if fp!=SHARDS[key][1]:raise ValueError("Pinned original guest shard changed "+key)
                    targets[key]={"path":path,"sha256":fp,"source_bytes":len(data),
                                  "fn":SHARDS[key][2],"source":data.decode("utf-8")}
                text=data.decode("utf-8",errors="strict")
                defs=list(FUNCTION_DEF.finditer(text))
                unique_functions+=len(defs)
                for i,func in enumerate(defs):
                    start=func.start()
                    end=defs[i+1].start() if i+1<len(defs) else len(text)
                    block=text[start:end]
                    # Calls are recognized only as stand-alone executable lines.
                    for m in EXACT_CALL.finditer(block):
                        callee=m.group(1)
                        if callee not in TARGET_CALLEES:continue
                        matches_count[callee]+=1
                        if len(all_calls[callee])>=CAP_PER_TARGET:continue
                        line=block.count("\n",0,m.start())
                        local=block.splitlines()
                        all_calls[callee].append({
                            "caller_function":func.group(1),
                            "caller_source_shard":leaf,
                            "source_shard_sha256":fp,
                            "caller_relative_line":line+1,
                            "nearest_guest_return_PC":sample_site(local,line)
                        })
        if set(targets)!=set(SHARDS):
            raise ValueError("Original guest anchor shards missing: "+repr(set(SHARDS)-set(targets)))
        if scanned_files<80 or unique_functions<10000:
            raise ValueError("Historical generated guest scan incomplete")
        described={}
        for label,anchor in targets.items():
            body=body_for_function(anchor.pop("source"),anchor["fn"])
            ls=body.splitlines()
            calls=[m.group(1) for m in EXACT_CALL.finditer(body)]
            stores=Counter(re.findall(r"REX_STORE_(U8|U16|U32|U64)\(",body))
            reads=Counter(re.findall(r"REX_LOAD_(U8|U16|U32|U64)\(",body))
            zero_returns=sum(x.strip()=="ctx.r3.s64 = 0;" for x in ls)
            got_read=sum(x.strip()=="ctx.r3.u64 = REX_LOAD_U32(ctx.r11.u32 + 0);" for x in ls)
            described[label]={**anchor,
                "original_implementation_lines":len(ls),
                "calls_in_order":calls[:85],
                "calls_total":len(calls),
                "guest_load_opcode_counts":dict(reads),
                "guest_store_opcode_counts":dict(stores),
                "r3_zero_return_assignments":zero_returns,
                "r3_attribute_value_return_assignments":got_read,
                "possible_counter_limit_needs_live_branch_proof":True}
        lookup=described["lookup"]
        build=described["category_builder"]
        if (lookup["r3_zero_return_assignments"]!=2 or
            lookup["r3_attribute_value_return_assignments"]!=1 or
            lookup["calls_in_order"].count("sub_8214B858")<1 or
            lookup["calls_in_order"].count("sub_8214EDA8")<1 or
            build["calls_in_order"].count("sub_823E5988")!=2):
            raise ValueError("Known PRE446/447 original guest helper or UI-list anchors differ")
        # The V48 build derivation was already pinned in PRE452; this audit
        # studies original PRE99 functions, not exact post-patch V48 compiled C++.
        return {
          "stage":"PRE528_PAL_GUEST_UPGRADE_COUNT_CALLGRAPH_ORIGINAL_PRE99_READONLY",
          "status":"AUDIT_OK",
          "source_archive_sha256":sha,
          "source_archive_bytes":size,
          "historical_codegen_shards_scanned":scanned_files,
          "historical_codegen_functions_scanned":unique_functions,
          "historical_codegen_source_bytes_scanned":total_code_bytes,
          "pinned_guest_anchor_functions":described,
          "target_callee_static_call_counts":dict(matches_count),
          "target_callee_callsite_metadata":dict(all_calls),
          "known_UI_builder_has_two_calls_to_attribute_count_lookup":True,
          "historical_lookup_has_two_zero_and_one_attribute_read_return_path":True,
          "public_PC_function_name_equivalence_proven":False,
          "actual_V48_linked_guest_implementation_equivalence_proven":False,
          "actual_bmw_runtime_branch_reason_observed":False,
          "guest_SetPackage_function_address_identified":False,
          "guest_SetPackage_accepts_synthetic_BMW_collection_proven":False,
          "guest_BMW_shop_charge_refund_safety_proven":False,
          "original_PAL_archive_or_source_modified":False,
          "game_assets_or_recompiled_binary_published":False,
          "APK_built":False,"save_modified":False,
          "signing_material_accessed":False,
          "ready_to_enable_BMW_tuning":False
        }

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run-id",required=True)
    a=parser.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as exc:
        r={"stage":"PRE528_PAL_GUEST_UPGRADE_COUNT_CALLGRAPH_ORIGINAL_PRE99_READONLY",
           "status":"FAILED","error_type":type(exc).__name__,"error":str(exc)[:240],
           "original_PAL_archive_or_source_modified":False,
           "game_assets_or_recompiled_binary_published":False,
           "APK_built":False,"save_modified":False,"signing_material_accessed":False,
           "ready_to_enable_BMW_tuning":False}
    r["run_id"]=a.run_id
    r["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE528_STATUS",r["status"],flush=True)
    print("PRE528_GUEST_SHARDS",r.get("historical_codegen_shards_scanned"),flush=True)
    print("PRE528_GUEST_FUNCTIONS",r.get("historical_codegen_functions_scanned"),flush=True)
    print("PRE528_TARGET_CALLERS",r.get("target_callee_static_call_counts"),flush=True)
    print("PRE528_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    raise SystemExit(main())
