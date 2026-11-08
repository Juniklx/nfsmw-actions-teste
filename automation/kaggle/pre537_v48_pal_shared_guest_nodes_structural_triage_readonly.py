#!/usr/bin/env python3
"""PRE537: signed V48 PAL original ELF structural triage of twelve shared nodes.

Independent authenticated download of V48 original APK and PAL native ELF
through PRE535.load_lib, sha pinned. Relocation-resolved direct BL inbound
counts from all exported guest functions, one-function Capstone opcode
fingerprints, and bounded outbound guest calls for exactly twelve nodes.

This does NOT establish function purpose, live execution, guest SetPackage,
checkout, purchases, or physics. No game code/asset/ELF/APK exported.
"""
from __future__ import annotations
import argparse,hashlib,io,json,re,struct
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from elftools.elf.relocation import RelocationSection
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from pre535_signed_v48_pal_shop_two_hop_plt_graph_readonly import load_lib,APK_SHA,LIB_SHA

OUT=Path("/tmp/nfsmw-pre537/report.json")
GUEST=re.compile(r"^sub_[0-9a-fA-F]{8}$")
MAX_CODE=120_000
MAX_SCAN=45_000_000
MAX_EXAMPLE_CALLERS=20
EXPECTED={
 "sub_820E25C0","sub_82152A38","sub_8215CB08","sub_821E02C0",
 "sub_8227FD70","sub_82282A70","sub_82284CC0","sub_82284E88",
 "sub_822BCE60","sub_822CC740","sub_822FEB70","sub_823EAE40"
}

def audit():
    prior=json.loads(Path("docs/PRE535_V48_PAL_SHOP_TWO_HOP_PLT_GRAPH_READONLY.json").read_text())
    sync=json.loads(Path("docs/PRE536_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (prior.get("status")!="AUDIT_OK" or
        prior.get("published_original_V48_apk_sha256")!=APK_SHA or
        prior.get("published_original_V48_PAL_libmain_sha256")!=LIB_SHA or
        prior.get("guest_root_two_hop_intersection_count")!=12 or
        prior.get("guest_SetPackage_guest_address_proven") is not False or
        prior.get("BMW_tuning_enabled") is not False or
        sync.get("status")!="AUDIT_OK" or
        sync.get("new_total_bytes")!=805726 or
        sync.get("new_sha256")!="ad8ff437d106d920d20e60756a769794029ca95169e54bab4a8dd96047c44e63"):
        raise ValueError("PRE535/536 proof or canonical handoff gate changed")
    intersection=prior["guest_root_two_hop_intersection_samples"]
    names={n["numeric_function"] for n in intersection}
    if len(intersection)!=12 or names!=EXPECTED:
        raise ValueError("Unexpected PRE535 exact shared numeric function identity set")
    raw=load_lib()
    if hashlib.sha256(raw).hexdigest()!=LIB_SHA:raise ValueError("Original PAL V48 ELF hash mismatch")
    elf=ELFFile(io.BytesIO(raw))
    if elf["e_machine"]!="EM_AARCH64" or elf["e_type"]!="ET_DYN":
        raise ValueError("Original V48 PAL ELF architecture unexpected")
    dyn=elf.get_section_by_name(".dynsym")
    plt=elf.get_section_by_name(".plt")
    rela=elf.get_section_by_name(".rela.plt")
    if not isinstance(dyn,SymbolTableSection) or not isinstance(rela,RelocationSection) or plt is None:
        raise ValueError("Signed PAL ELF lacks authoritative PLT, symbols, relocations")
    n=rela.num_relocations()
    plt_base=int(plt["sh_addr"])
    if n!=17107 or int(plt["sh_size"])!=32+16*n:
        raise ValueError("PLT / AArch64 JUMP_SLOT layout changed")
    plt_slots={}
    slot_counts=Counter()
    for i,r in enumerate(rela.iter_relocations()):
        if int(r.entry.r_info_type)!=1026:raise ValueError("Non JUMP_SLOT relocation")
        label=dyn.get_symbol(int(r.entry.r_info_sym)).name
        if label.startswith("__imp__"):label=label[len("__imp__"):]
        if not GUEST.fullmatch(label):continue
        plt_slots[plt_base+32+16*i]=label
        if label in EXPECTED:slot_counts[label]+=1
    if len(plt_slots)!=15598:raise ValueError("Guest PLT original slot count changed")
    definitions={}
    for sym in dyn.iter_symbols():
        label=sym.name
        if (not GUEST.fullmatch(label)
            or sym["st_info"]["type"]!="STT_FUNC"
            or sym["st_shndx"]=="SHN_UNDEF"):continue
        if label in definitions:raise ValueError("Duplicate guest numeric definition")
        definitions[label]=(int(sym["st_value"]),int(sym["st_size"]))
    if len(definitions)!=56338:raise ValueError("Original V48 guest numeric symbol count changed")
    for k in EXPECTED:
        if k not in definitions or slot_counts.get(k,0)<1:
            raise ValueError("Original V48 shared node missing def or PLT slot: "+k)
    ranges=[]
    for seg in elf.iter_segments():
        if seg["p_type"]=="PT_LOAD" and (int(seg["p_flags"])&1):
            ranges.append((int(seg["p_vaddr"]),int(seg["p_offset"]),int(seg["p_filesz"])))
    def code_for(label):
        addr,size=definitions[label]
        if size<=0 or size>MAX_CODE or size%4!=0 or addr%4:
            return None
        for begin,offset,filesize in ranges:
            if begin<=addr and addr+size<=begin+filesize:
                pos=offset+(addr-begin)
                if pos+size<=len(raw):return addr,memoryview(raw)[pos:pos+size]
        return None

    # Complete scan of all guest function bodies that satisfy exact ELF
    # executable bounds, measuring only PLT-linked BL instructions.
    inbound={k:{"calls":0,"callers":set(),"region_counts":Counter(),
                "caller_samples":[]} for k in EXPECTED}
    scanned=0;skipped=0;bytes_total=0;all_guest_bl=0
    for name in sorted(definitions):
        selected=code_for(name)
        if selected is None:
            skipped+=1;continue
        addr,code=selected
        scanned+=1;bytes_total+=len(code)
        if bytes_total>MAX_SCAN:
            raise ValueError("Guest-wide BL scan exceeds bounded byte budget")
        touched=set()
        for ix,(word,) in enumerate(struct.iter_unpack("<I",code)):
            if word&0xFC000000!=0x94000000:continue
            imm=word&0x03ffffff
            if imm&0x02000000:imm-=0x04000000
            destination=plt_slots.get(addr+4*ix+(imm<<2))
            if destination is None:continue
            all_guest_bl+=1
            if destination not in inbound:continue
            r=inbound[destination]
            r["calls"]+=1
            touched.add(destination)
            if len(r["caller_samples"])<MAX_EXAMPLE_CALLERS:
                r["caller_samples"].append(name)
        for target in touched:
            r=inbound[target]
            r["callers"].add(name)
            region=f"0x{(int(name[4:],16)>>16):04x}"
            r["region_counts"][region]+=1
    if scanned<56000 or skipped>400:
        raise ValueError("Original PAL exported function scan incomplete")
    # These are structural metrics only: no semantic classification inferred.
    dis=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    dis.detail=False
    records=[]
    for node in intersection:
        name=node["numeric_function"]
        addr,buf=code_for(name)
        if buf is None:raise ValueError("Shared node missing executable code "+name)
        code=bytes(buf)
        opcode=Counter()
        outgoing=Counter()
        direct_bl=0
        for inst in dis.disasm(code,addr):
            opcode[inst.mnemonic]+=1
            if inst.mnemonic!="bl":continue
            direct_bl+=1
            word=struct.unpack_from("<I",code,int(inst.address)-addr)[0]
            imm=word&0x03ffffff
            if imm&0x02000000:imm-=0x04000000
            target=plt_slots.get(int(inst.address)+(imm<<2))
            if target:outgoing[target]+=1
        inc=inbound[name]
        region_counts=inc["region_counts"]
        top_regions=region_counts.most_common(12)
        caller_total=len(inc["callers"])
        local_825x=sum(cnt for region,cnt in region_counts.items()
                        if region in ("0x8255","0x8256","0x8257","0x8258"))
        records.append({
          "function":name,
          "original_V48_ELF_function_bytes":len(code),
          "original_V48_ELF_ARM64_instruction_count":sum(opcode.values()),
          "branch_and_call_opcode_counts":{k:opcode[k] for k in
             ("bl","blr","br","b","b.eq","b.ne","cbz","cbnz",
              "tbz","tbnz","ret") if opcode[k]},
          "memory_opcode_counts":{k:opcode[k] for k in
              ("ldr","ldrb","ldrh","ldrsw","ldp","str","strb","strh",
               "stp","ldur","stur") if opcode[k]},
          "direct_ARM64_BL_count":direct_bl,
          "resolved_numeric_guest_callees":dict(outgoing.most_common(25)),
          "distinct_resolved_guest_callees":len(outgoing),
          "incoming_guest_BL_callsite_count":inc["calls"],
          "incoming_distinct_guest_caller_count":caller_total,
          "incoming_distinct_guest_caller_address_regions":len(region_counts),
          "incoming_callers_from_8255_to_8258_regions":local_825x,
          "incoming_guest_caller_top_address_regions":dict(top_regions),
          "incoming_guest_caller_bounded_examples":inc["caller_samples"],
          "PRE535_menu_root_roles_reaching":node["ui_root_roles_reaching"],
          "PRE535_field_writer_root_roles_reaching":node["field_writer_root_roles_reaching"],
          "PRE535_verified_witness_paths":node["witness_paths_at_most_two_calls"],
          "semantic_identity_proven":False
        })
    records.sort(key=lambda r:(r["incoming_distinct_guest_caller_count"],r["function"]))
    return {
      "stage":"PRE537_SIGNED_V48_PAL_SHARED_GUEST_NODES_INBOUND_BREADTH_READONLY",
      "status":"AUDIT_OK",
      "original_signed_V48_APK_sha256":APK_SHA,
      "original_signed_V48_PAL_libmain_sha256":LIB_SHA,
      "ELF_PLT_relocation_count":n,
      "ELF_guest_Plt_mapping_count":len(plt_slots),
      "ELF_guest_numeric_function_count":len(definitions),
      "all_guest_exported_bodies_scanned":scanned,
      "all_guest_exported_bodies_skipped_by_bounds":skipped,
      "total_original_V48_ARM64_bytes_scanned":bytes_total,
      "all_resolved_guest_BL_calls_seen":all_guest_bl,
      "audited_PRE535_shared_numeric_function_count":len(records),
      "audited_shared_numeric_functions":records,
      "metrics_support_only_breadth_not_function_identity":True,
      "historical_field12_writes_proven_cash_debit":False,
      "candidate_SetPackage_identified":False,
      "actual_runtime_checkout_installation_or_save_verified":False,
      "original_game_or_ELF_modified":False,
      "original_APK_modified":False,
      "guest_code_or_assets_published":False,
      "APK_built":False,
      "save_modified":False,
      "signing_key_accessed":False,
      "safe_to_enable_BMW_tuning":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"stage":"PRE537_SIGNED_V48_PAL_SHARED_GUEST_NODES_INBOUND_BREADTH_READONLY",
           "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
           "original_game_or_ELF_modified":False,"original_APK_modified":False,
           "guest_code_or_assets_published":False,"APK_built":False,
           "save_modified":False,"signing_key_accessed":False,
           "safe_to_enable_BMW_tuning":False}
    r["run_id"]=a.run_id
    r["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE537_STATUS",r["status"],flush=True)
    print("PRE537_GUEST_DEFINITIONS_SCANNED",r.get("all_guest_exported_bodies_scanned"),flush=True)
    print("PRE537_SHARED_NODES",r.get("audited_PRE535_shared_numeric_function_count"),flush=True)
    print("PRE537_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
