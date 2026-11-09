#!/usr/bin/env python3
"""PRE542: verify attribute-count -> floating arithmetic path in released V48 PAL.

On SHA-pinned original signed V48 PAL ELF, decode exactly six guest numeric
functions from PRE541, resolve direct BL destinations through genuine
R_AARCH64_JUMP_SLOT relocations, and count AArch64 float instructions.
Proves only static numeric call connectivity and FP instruction presence.
Does NOT prove upgraded power, guest SetPackage, purchase or save persistence.
"""
from __future__ import annotations
import argparse,hashlib,io,json,struct,re
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from elftools.elf.relocation import RelocationSection
from pre535_signed_v48_pal_shop_two_hop_plt_graph_readonly import load_lib,APK_SHA,LIB_SHA
OUT=Path("/tmp/nfsmw-pre542/report.json")
NAMES=("sub_823EAE40","sub_823EB290","sub_823EB3B0","sub_823E4130","sub_823E4588","sub_823E5988")
NUMERIC=re.compile(r"^sub_[0-9A-Fa-f]{8}$")
FLOAT_PREFIX=("fadd","fsub","fmul","fmadd","fmsub","fnmadd","fnmsub","fdiv",
              "fmov","fcmp","fcmpe","fcvt","fneg","fabs","fmin","fmax","fsqrt",
              "fmla","fmls","frint","scvtf","ucvtf")
def audit():
    p541=json.loads(Path("docs/PRE541_PAL_GUEST_823EAE40_FOUR_DEPS_PPC_READONLY.json").read_text())
    p539=json.loads(Path("docs/PRE539_ORIGINAL_V48_PAL_823EAE40_SEVEN_CALLERS_READONLY.json").read_text())
    if (p541.get("status")!="AUDIT_OK" or
        p541.get("source_outbound_matches_V48_PAL_function_names") is not True or
        p541.get("guest_Phy_Upgrades_SetPackage_proven") is not False or
        p539.get("status")!="AUDIT_OK" or
        p539.get("original_signed_V48_APK_sha256")!=APK_SHA or
        p539.get("original_signed_V48_PAL_libmain_sha256")!=LIB_SHA or
        p539.get("target_is_guest_SetPackage_proven") is not False):
        raise ValueError("PRE539/541 authenticated guest evidence changed")
    src=p541["target_and_four_guest_callees_original_PPC_records"]
    if set(src)!=set(NAMES) or src["sub_823EAE40"]["original_guest_body_line_count"]!=493:
        raise ValueError("PRE541 source function identities changed")
    raw=load_lib()
    if hashlib.sha256(raw).hexdigest()!=LIB_SHA:raise ValueError("Original V48 PAL library SHA changed")
    elf=ELFFile(io.BytesIO(raw))
    dyn=elf.get_section_by_name(".dynsym")
    plt=elf.get_section_by_name(".plt")
    rela=elf.get_section_by_name(".rela.plt")
    if not isinstance(dyn,SymbolTableSection) or not isinstance(rela,RelocationSection) or plt is None:
        raise ValueError("Original V48 ARM64 PLT relocation metadata missing")
    n=rela.num_relocations();base=int(plt["sh_addr"])
    if n!=17107 or int(plt["sh_size"])!=32+16*n:raise ValueError("Original AArch64 PLT canonical mapping changed")
    destinations={}
    for i,rel in enumerate(rela.iter_relocations()):
        if int(rel.entry.r_info_type)!=1026:raise ValueError("Non JUMP_SLOT relocation")
        nm=dyn.get_symbol(int(rel.entry.r_info_sym)).name
        if nm.startswith("__imp__"):nm=nm[7:]
        if NUMERIC.fullmatch(nm):destinations[base+32+16*i]=nm
    if len(destinations)!=15598:raise ValueError("Original V48 PAL numeric relocated calls changed")
    symbols={}
    for x in dyn.iter_symbols():
        nm=x.name
        if nm not in NAMES or x["st_info"]["type"]!="STT_FUNC" or x["st_shndx"]=="SHN_UNDEF":continue
        symbols[nm]=(int(x["st_value"]),int(x["st_size"]))
    if len(symbols)!=len(NAMES):raise ValueError("Original PAL guest numeric symbols missing")
    executable=[(int(x["p_vaddr"]),int(x["p_offset"]),int(x["p_filesz"])) for x in elf.iter_segments()
                if x["p_type"]=="PT_LOAD" and int(x["p_flags"])&1]
    def extract(nm):
        a,l=symbols[nm]
        if not 4<=l<=100000 or l%4 or a%4:raise ValueError("Guest function size invalid "+nm)
        for start,offset,length in executable:
            if start<=a and a+l<=start+length:
                ix=offset+a-start
                if ix+l<=len(raw):return a,raw[ix:ix+l]
        raise ValueError("Guest function outside executable source "+nm)
    dis=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    proof={}
    for nm in NAMES:
        address,code=extract(nm)
        instructions=list(dis.disasm(code,address))
        if len(instructions)*4!=len(code):raise ValueError("AArch64 decode incomplete "+nm)
        floatop=Counter()
        bl=[]
        for inst in instructions:
            if inst.mnemonic.startswith(FLOAT_PREFIX):floatop[inst.mnemonic]+=1
            if inst.mnemonic!="bl":continue
            (w,)=struct.unpack_from("<I",code,int(inst.address-address))
            imm=w&0x03FFFFFF
            if imm&0x02000000:imm-=0x04000000
            bl.append(destinations.get(int(inst.address)+(imm<<2)))
        resolved=[x for x in bl if x]
        src_calls=src[nm]["direct_guest_callees_in_order"]
        proof[nm]={
          "v48_native_ARM64_function_bytes":len(code),
          "v48_native_AArch64_instruction_count":len(instructions),
          "v48_float_related_mnemonic_counts":dict(floatop.most_common()),
          "v48_float_related_instruction_total":sum(floatop.values()),
          "v48_bl_count":len(bl),
          "v48_numeric_guest_BL_in_order":resolved,
          "v48_unresolved_native_BL_count":len(bl)-len(resolved),
          "historical_PRE99_numeric_guest_call_list":src_calls,
          "source_and_original_V48_numeric_guest_call_multisets_match":Counter(resolved)==Counter(src_calls),
          "no_function_semantics_inferred_from_float_opcodes":True
        }
    target=proof["sub_823EAE40"]
    intermediate=proof["sub_823E4130"]
    edge1="sub_823E4130" in target["v48_numeric_guest_BL_in_order"]
    edge2="sub_823E5988" in intermediate["v48_numeric_guest_BL_in_order"]
    if not edge1 or not edge2:raise ValueError("Expected signed V48 attribute-count 2-edge chain absent")
    if target["v48_float_related_instruction_total"]<30:
        raise ValueError("Original V48 guest target lacks expected float instruction density")
    return {
      "stage":"PRE542_SIGNED_V48_PAL_GUEST_FLOAT_ATTRIBUTE_TWO_EDGE_PATH_READONLY",
      "status":"AUDIT_OK",
      "original_signed_V48_APK_sha256":APK_SHA,
      "original_signed_V48_PAL_libmain_sha256":LIB_SHA,
      "original_AArch64_PLT_guest_relocations":len(destinations),
      "six_original_guest_function_records":proof,
      "signed_V48_direct_guest_edge_823EAE40_to_823E4130":edge1,
      "signed_V48_direct_guest_edge_823E4130_to_823E5988":edge2,
      "signed_V48_guest_numeric_two_hop_attribute_count_path_proven":True,
      "signed_V48_target_float_related_instruction_count":target["v48_float_related_instruction_total"],
      "float_instruction_counts_do_not_prove_vehicle_physics_or_SetPackage":True,
      "actual_BMW_motor_data_loaded_or_power_modified":False,
      "guest_SetPackage_identity_verified":False,
      "guest_BMW_purchase_or_save_roundtrip_verified":False,
      "game_data_or_binary_modified_or_published":False,
      "APK_built":False,"save_modified":False,
      "signing_material_accessed":False,"tuning_enabled":False
    }
def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run-id",required=True)
    args=parser.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as exc:
        r={"stage":"PRE542_SIGNED_V48_PAL_GUEST_FLOAT_ATTRIBUTE_TWO_EDGE_PATH_READONLY",
           "status":"FAILED","error_type":type(exc).__name__,"error":str(exc)[:240],
           "game_data_or_binary_modified_or_published":False,"APK_built":False,
           "save_modified":False,"signing_material_accessed":False,"tuning_enabled":False}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE542_STATUS",r["status"],flush=True)
    print("PRE542_FLOAT_OPS",r.get("signed_V48_target_float_related_instruction_count"),flush=True)
    print("PRE542_PATH",r.get("signed_V48_guest_numeric_two_hop_attribute_count_path_proven"),flush=True)
    print("PRE542_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
