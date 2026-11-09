#!/usr/bin/env python3
"""PRE539 — exact original V48 PAL guest calls into sub_823EAE40, read-only.

Using SHA256-pinned release V48 APK and ELF and the authentic PLT relocation
table, inspect *all seven* callers and *all nine* static BL call sites of
sub_823EAE40. Capture bounded ARM64 instruction mnemonics/argument-register
write hints before each call and outgoing guest calls of the target.

This is structural callsite evidence, not proof of runtime calls, money
transactions, physics package installation, or identity with SetPackage.
Do not publish raw native code, ISO contents, save or signing material.
"""
from __future__ import annotations

import argparse, hashlib, io, json, re, struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from elftools.elf.relocation import RelocationSection
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from pre535_signed_v48_pal_shop_two_hop_plt_graph_readonly import load_lib, APK_SHA, LIB_SHA

OUT=Path("/tmp/nfsmw-pre539/report.json")
TARGET="sub_823EAE40"
GUEST=re.compile(r"^sub_[0-9A-Fa-f]{8}$")
CALLERS={
  "sub_8226B228":1,
  "sub_8226B4C0":1,
  "sub_8254E908":1,
  "sub_8255C1C8":1,
  "sub_82566BE8":2,
  "sub_8256CE68":2,
  "sub_82584880":1
}
EXPECTED_OUT={"sub_823EB290":1,"sub_823EB3B0":1,"sub_823E4130":1,"sub_823E4588":1}

def audit():
    prior=json.loads(Path("docs/PRE537_ORIGINAL_V48_PAL_SHARED_NODES_STRUCTURAL_TRIAGE_READONLY.json").read_text())
    handoff=json.loads(Path("docs/PRE538_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (prior.get("status")!="AUDIT_OK" or
        prior.get("original_signed_V48_APK_sha256")!=APK_SHA or
        prior.get("original_signed_V48_PAL_libmain_sha256")!=LIB_SHA or
        prior.get("ELF_PLT_relocation_count")!=17107 or
        prior.get("ELF_guest_Plt_mapping_count")!=15598 or
        prior.get("all_guest_exported_bodies_scanned")!=56338 or
        prior.get("safe_to_enable_BMW_tuning") is not False or
        handoff.get("status")!="AUDIT_OK" or
        handoff.get("new_total_bytes")!=810448 or
        handoff.get("new_sha256")!="713edd5815bb4f107c24bf283a53072ebdd41e826dfcf575b0b31c586bb47c7b"):
        raise ValueError("PRE537/538 original signed binary and canonical context bounds changed")
    target_report=next((v for v in prior["audited_shared_numeric_functions"]
                     if v["function"]==TARGET),None)
    if (not target_report or
        target_report.get("incoming_distinct_guest_caller_count")!=7 or
        target_report.get("incoming_guest_BL_callsite_count")!=9 or
        target_report.get("original_V48_ELF_function_bytes")!=2964 or
        target_report.get("resolved_numeric_guest_callees")!=EXPECTED_OUT):
        raise ValueError("Original PRE537 guest target function does not match pinned evidence")

    raw=load_lib()
    if hashlib.sha256(raw).hexdigest()!=LIB_SHA:
        raise ValueError("Original V48 PAL ELF SHA changed")
    elf=ELFFile(io.BytesIO(raw))
    if elf["e_machine"]!="EM_AARCH64" or elf["e_type"]!="ET_DYN":
        raise ValueError("Unexpected original PAL ELF machine/type")
    dyn=elf.get_section_by_name(".dynsym")
    plt=elf.get_section_by_name(".plt")
    rela=elf.get_section_by_name(".rela.plt")
    if not isinstance(dyn,SymbolTableSection) or not isinstance(rela,RelocationSection) or plt is None:
        raise ValueError("Missing original PAL ELF link structures")
    n=rela.num_relocations()
    base=int(plt["sh_addr"])
    if n!=17107 or int(plt["sh_size"])!=32+16*n:
        raise ValueError("Noncanonical original AArch64 PLT layout")
    plt_map={}
    for i,rel in enumerate(rela.iter_relocations()):
        if int(rel.entry.r_info_type)!=1026:
            raise ValueError("Unsupported original PLT relocation")
        name=dyn.get_symbol(int(rel.entry.r_info_sym)).name
        if name.startswith("__imp__"):name=name[7:]
        if GUEST.fullmatch(name):
            plt_map[base+32+16*i]=name
    if len(plt_map)!=15598:raise ValueError("Different number of original guest PLT entries")

    defs={}
    for sym in dyn.iter_symbols():
        name=sym.name
        if not GUEST.fullmatch(name) or sym["st_info"]["type"]!="STT_FUNC" or sym["st_shndx"]=="SHN_UNDEF":
            continue
        if name in defs:raise ValueError("Duplicated original guest definition")
        defs[name]=(int(sym["st_value"]),int(sym["st_size"]))
    if len(defs)!=56338:raise ValueError("Original guest function count changed")
    ranges=[]
    for seg in elf.iter_segments():
        if seg["p_type"]=="PT_LOAD" and int(seg["p_flags"])&1:
            ranges.append((int(seg["p_vaddr"]),int(seg["p_offset"]),int(seg["p_filesz"])))

    def read_func(name):
        address,size=defs[name]
        if not 4<=size<=120000 or size%4 or address%4:
            raise ValueError("Invalid guest function code size/alignment")
        for start,offset,length in ranges:
            if start<=address and address+size<=start+length:
                pos=offset+address-start
                if pos+size<=len(raw):return address,raw[pos:pos+size]
        raise ValueError("Guest function outside executable segment")

    decoder=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    def calls_from(name):
        address,code=read_func(name)
        ins=list(decoder.disasm(code,address))
        if len(ins)*4!=len(code):raise ValueError("Disassembly incomplete for "+name)
        ret=[]
        for i,x in enumerate(ins):
            if x.mnemonic!="bl":continue
            word=struct.unpack_from("<I",code,int(x.address-address))[0]
            if (word&0xFC000000)!=0x94000000:
                raise ValueError("Capstone BL mismatch")
            imm=word&0x03ffffff
            if imm&0x02000000:imm-=0x04000000
            actual=plt_map.get(int(x.address)+(imm<<2))
            previous=ins[max(0,i-12):i]
            subsequent=ins[i+1:i+5]
            argwrites=[]
            for y in previous:
                op=y.op_str.split(",",1)[0].strip()
                if re.fullmatch(r"[wx][0-7]",op) and y.mnemonic not in ("cmp","cmn","tst"):
                    argwrites.append({"arg_register":op,"prior_instruction_offset":int(y.address-x.address)})
            ret.append({
              "relative_BL_offset_bytes":int(x.address-address),
              "resolved_guest_target":actual,
              "preceding_12_mnemonics":[z.mnemonic for z in previous],
              "following_4_mnemonics":[z.mnemonic for z in subsequent],
              "previous_arg_register_write_candidates":argwrites[-12:],
              "branch_mnemonics_in_previous_12":[z.mnemonic for z in previous if
                z.mnemonic.startswith(("b.","cb","tb")) or z.mnemonic in ("b","bl","br","blr")],
              "not_a_data_flow_or_condition_proof":True
            })
        return {"name":name,"function_ARM64_bytes":len(code),
                "instruction_count":len(ins),
                "all_BL_count":len(ret),"resolved_guest_BL_count":sum(x["resolved_guest_target"] is not None for x in ret),
                "return_instruction_count":sum(x.mnemonic=="ret" for x in ins),
                "guest_BL_calls":ret}

    inspected={name:calls_from(name) for name in [TARGET]+sorted(CALLERS)}
    if inspected[TARGET]["function_ARM64_bytes"]!=2964:
        raise ValueError("PRE537 target ELF body length differs")
    target_out=dict(Counter(x["resolved_guest_target"] for x in inspected[TARGET]["guest_BL_calls"]
                            if x["resolved_guest_target"] is not None))
    if target_out!=EXPECTED_OUT:
        raise ValueError("Re-resolved target guest calls disagree with PRE537")

    summaries=[]
    for name in sorted(CALLERS):
        obj=inspected[name]
        sites=[x for x in obj["guest_BL_calls"] if x["resolved_guest_target"]==TARGET]
        if len(sites)!=CALLERS[name]:raise ValueError("Original target incoming callsite count changed "+name)
        others=Counter(x["resolved_guest_target"] for x in obj["guest_BL_calls"]
                       if x["resolved_guest_target"] is not None and x["resolved_guest_target"]!=TARGET)
        summaries.append({
          "guest_caller":name,
          "function_ARM64_bytes":obj["function_ARM64_bytes"],
          "total_native_BL":obj["all_BL_count"],
          "resolved_numeric_guest_BL_count":obj["resolved_guest_BL_count"],
          "other_resolved_numeric_guest_callee_names":dict(others.most_common(30)),
          "target_callsite_count":len(sites),
          "target_callsite_contexts":sites,
          "semantics_of_call_and_registers_proven":False
        })
    if sum(x["target_callsite_count"] for x in summaries)!=9:
        raise ValueError("Original target must have exactly 9 incoming BL sites")
    paths={
      "shop_menu_to_target":["sub_82582F70","sub_8256CE68",TARGET],
      "historical_field12_writer_to_target":["sub_82564D80","sub_8254E908",TARGET]
    }
    if not all(x in CALLERS for x in (paths["shop_menu_to_target"][1],
                                    paths["historical_field12_writer_to_target"][1])):
        raise ValueError("Expected numeric path not covered")

    return {
      "stage":"PRE539_SIGNED_V48_PAL_SEVEN_GUEST_CALLERS_TO_823EAE40_READONLY",
      "status":"AUDIT_OK",
      "original_signed_V48_APK_sha256":APK_SHA,
      "original_signed_V48_PAL_libmain_sha256":LIB_SHA,
      "original_ELF_guest_function_count":len(defs),
      "original_ELF_Plt_guest_relocation_count":len(plt_map),
      "exact_target_numeric_guest_name":TARGET,
      "exact_target_ARM64_bytes":inspected[TARGET]["function_ARM64_bytes"],
      "target_outgoing_resolved_guest_calls":target_out,
      "target_incoming_distinct_guest_caller_count":len(summaries),
      "target_incoming_direct_BL_callsite_count":sum(x["target_callsite_count"] for x in summaries),
      "all_seven_caller_direct_BL_and_bounded_argument_contexts":summaries,
      "cross_root_witness_paths_already_in_PRE535":paths,
      "ARM64_instruction_register_write_hints_are_not_verified_argument_values":True,
      "target_is_guest_SetPackage_proven":False,
      "target_is_shop_checkout_or_purchase_proven":False,
      "target_is_related_to_physical_tuning_proven":False,
      "guest_actual_V48_execution_or_bmw_save_roundtrip_proven":False,
      "APK_built":False,
      "original_game_or_APK_modified":False,
      "original_native_binary_published":False,
      "save_modified":False,
      "signing_material_accessed":False,
      "BMW_tuning_enabled":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    a=ap.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:report=audit()
    except Exception as exc:
        report={"stage":"PRE539_SIGNED_V48_PAL_SEVEN_GUEST_CALLERS_TO_823EAE40_READONLY",
           "status":"FAILED","error_type":type(exc).__name__,"error":str(exc)[:240],
           "APK_built":False,"original_game_or_APK_modified":False,
           "original_native_binary_published":False,"save_modified":False,
           "signing_material_accessed":False,"BMW_tuning_enabled":False}
    report["run_id"]=a.run_id
    report["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("PRE539_STATUS",report["status"],flush=True)
    print("PRE539_CALLERS",report.get("target_incoming_distinct_guest_caller_count"),flush=True)
    print("PRE539_SITES",report.get("target_incoming_direct_BL_callsite_count"),flush=True)
    print("PRE539_ERROR",report.get("error_type","none"),report.get("error",""),flush=True)
    return 0 if report["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
