#!/usr/bin/env python3
"""PRE533: resolve authenticated V48 ARM64 guest BL through ELF PLT relocations, read only.

Verify exact original V48 APK and PAL libmain.so against PRE511/PRE531.
Use pyelftools .dynsym to resolve original PAL numeric guest sub_XXXXXXXX
functions, and Capstone to classify BL/B/BLR call sites for 12 anchor
routines. Compare ordered direct guest targets with PRE529 source PRE99
in metadata only.

Presence/absence of BL after optimization is not semantic equivalence;
no guest function is named SetPackage without a proof. Never export or
modify game/ELF/APK/save content or access permanent signature.
"""
from __future__ import annotations
import argparse,hashlib,io,json,re,tempfile,zipfile
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseDownload
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from elftools.elf.relocation import RelocationSection
from capstone import Cs,CS_ARCH_ARM64,CS_MODE_ARM
from capstone.arm64 import ARM64_OP_IMM
from pre105_read_settings_source import drive_client

OUT=Path("/tmp/nfsmw-pre533/report.json")
APK_ID="1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C"
APK_NAME="NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk"
APK_SIZE=47104233
APK_SHA="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
PAL_LIB="lib/arm64-v8a/libmain.so"
PAL_LIB_SHA="f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3"
PAL_LIB_SIZE=41768224
GUEST_RE=re.compile(r"^sub_[0-9a-fA-F]{8}$")

def get_code(elf,original_bytes,address,size):
    if size<4 or size>64000 or address%4 or size%4:
        raise ValueError("Guest function symbol size or alignment unexpected")
    for seg in elf.iter_segments():
        if seg["p_type"]!="PT_LOAD":continue
        start=int(seg["p_vaddr"]);filelen=int(seg["p_filesz"])
        if start<=address and address+size<=start+filelen:
            offset=int(seg["p_offset"])+(address-start)
            if offset+size>len(original_bytes):
                raise ValueError("ELF load segment exceeds library bounds")
            return original_bytes[offset:offset+size]
    raise ValueError("ELF guest function has no exact executable load segment")

def audit():
    prior_bl=json.loads(Path("docs/PRE532_AUTHENTIC_V48_PAL_GUEST_ARM64_CALLGRAPH_READONLY.json").read_text())
    if (prior_bl.get("status")!="AUDIT_OK" or
        prior_bl.get("aggregate_direct_BL_in_targets")!=189 or
        prior_bl.get("source_matched_guest_calls_total")!=0 or
        prior_bl.get("original_PAL_libmain_sha256")!=PAL_LIB_SHA):
        raise ValueError("PRE532 authentic direct branch and unresolved-PLT evidence missing")
    pre529=json.loads(Path("docs/PRE529_PAL_GUEST_SHOP_NEIGHBORS_MONEY_STORES_READONLY.json").read_text())
    pre531=json.loads(Path("docs/PRE531_ORIGINAL_V48_PAL_GUEST_ELF_SYMBOLS_READONLY.json").read_text())
    if (pre529.get("status")!="AUDIT_OK" or
        pre529.get("target_guest_function_count")!=12 or
        pre529.get("guest_SetPackage_address_proven") is not False or
        pre531.get("status")!="AUDIT_OK" or
        pre531.get("original_V48_apk_sha256")!=APK_SHA or
        pre531.get("authenticated_exact_V48_apk") is not True or
        pre531.get("guest_SetPackage_function_identity_verified") is not False):
        raise ValueError("PRE529/531 provenance and guest analysis boundaries missing")
    candidates=pre529["target_guest_definition_metadata"]
    if len(candidates)!=12 or not all(GUEST_RE.fullmatch(n) for n in candidates):
        raise ValueError("Unexpected PRE529 original guest anchor set")
    cli=drive_client()
    meta=cli.files().get(fileId=APK_ID,
           fields="id,name,size,mimeType",supportsAllDrives=True).execute()
    if (meta.get("id")!=APK_ID or meta.get("name")!=APK_NAME
        or int(meta.get("size",0))!=APK_SIZE
        or meta.get("mimeType")!="application/vnd.android.package-archive"):
        raise ValueError("V48 original Drive metadata diverged")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre533_") as td:
        target=Path(td)/"v48.apk"
        with target.open("wb") as fp:
            dl=MediaIoBaseDownload(fp,cli.files().get_media(fileId=APK_ID,supportsAllDrives=True),chunksize=4*1024*1024)
            done=False
            while not done:
                _,done=dl.next_chunk(num_retries=4)
        if target.stat().st_size!=APK_SIZE:
            raise ValueError("V48 original APK size diverged")
        h=hashlib.sha256()
        with target.open("rb") as fp:
            for chunk in iter(lambda:fp.read(4*1024*1024),b""):
                h.update(chunk)
        if h.hexdigest()!=APK_SHA:
            raise ValueError("V48 original APK SHA256 diverged")
        with zipfile.ZipFile(target) as zipf:
            member=zipf.getinfo(PAL_LIB)
            if member.file_size!=PAL_LIB_SIZE:
                raise ValueError("V48 PAL original ELF expected size changed")
            raw=zipf.read(member)
        if hashlib.sha256(raw).hexdigest()!=PAL_LIB_SHA:
            raise ValueError("V48 PAL original ELF SHA256 changed")
        elf=ELFFile(io.BytesIO(raw))
        if elf["e_machine"]!="EM_AARCH64":
            raise ValueError("Not V48 ARM64 PAL code")
        symtab=elf.get_section_by_name(".dynsym")
        if not isinstance(symtab,SymbolTableSection):
            raise ValueError("Authentic PAL binary has no .dynsym")
        addr_map={}
        name_map={}
        for sym in symtab.iter_symbols():
            name=sym.name
            if (not GUEST_RE.fullmatch(name) or
                sym["st_info"]["type"]!="STT_FUNC" or
                sym["st_shndx"]=="SHN_UNDEF"):
                continue
            vaddr=int(sym["st_value"]);size=int(sym["st_size"])
            if vaddr<0 or size<1:continue
            if vaddr in addr_map and addr_map[vaddr]!=name:
                raise ValueError("Two distinct guest functions alias same symbol address")
            addr_map[vaddr]=name
            if name in name_map:raise ValueError("Duplicate distinct symbol name "+name)
            name_map[name]=(vaddr,size)
        if len(addr_map)<40000:
            raise ValueError("Unexpectedly low exported guest function count; cannot map")
        # AArch64 ELF code may dispatch guest calls through PLT entries
        # (symbol interposition), so BL's immediate is not the guest symbol.
        # Decode the authoritative .rela.plt JUMP_SLOT order and require
        # the canonical AArch64 PLT0 32B + 16B per relocation table size.
        plt=elf.get_section_by_name(".plt")
        rela=elf.get_section_by_name(".rela.plt")
        plt_reloc_count=None
        plt_bytes=None
        plt_index={}
        plt_layout_verified=False
        plt_decode_limit_reason=None
        plt_guest_reloc_symbol_count=0
        relocation_kinds=Counter()
        if (plt is not None and isinstance(rela,RelocationSection)):
            plt_bytes=int(plt["sh_size"])
            plt_start=int(plt["sh_addr"])
            plt_reloc_count=rela.num_relocations()
            if (plt_reloc_count>0 and plt_bytes==32+16*plt_reloc_count
                and plt_start%4==0 and int(plt["sh_entsize"]) in (0,16)):
                for i,rel in enumerate(rela.iter_relocations()):
                    rtype=int(rel.entry.r_info_type)
                    relocation_kinds[str(rtype)]+=1
                    if rtype!=1026: # R_AARCH64_JUMP_SLOT
                        plt_decode_limit_reason="unexpected relocation type in .rela.plt"
                        break
                    sym=symtab.get_symbol(int(rel.entry.r_info_sym))
                    nm=sym.name
                    if nm.startswith("__imp__"):
                        nm=nm[len("__imp__"):]
                    if not GUEST_RE.fullmatch(nm):
                        continue
                    target=plt_start+32+16*i
                    if target in plt_index and plt_index[target]!=nm:
                        raise ValueError("Conflicting dynamic guest PLT slot")
                    plt_index[target]=nm
                    plt_guest_reloc_symbol_count+=1
                else:
                    plt_layout_verified=True
            else:
                plt_decode_limit_reason="actual ELF PLT size not canonical 32+16*N layout"
        else:
            plt_decode_limit_reason="actual original ELF .plt or .rela.plt not both present"
        if not plt_layout_verified:
            plt_index={}
        decoder=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
        decoder.detail=True
        mapped=[]
        total_direct=0
        total_agreed=0
        for name in sorted(candidates):
            if name not in name_map:
                raise ValueError("PRE529 PAL candidate missing in original signed V48 ELF "+name)
            addr,size=name_map[name]
            code=get_code(elf,raw,addr,size)
            direct=[]; branch=[]; indirect=Counter()
            count=0
            for ins in decoder.disasm(code,addr):
                count+=1
                if count>18000:raise ValueError("Excessive guest function instructions")
                if ins.mnemonic not in ("bl","b","blr","br"):
                    continue
                if ins.mnemonic in ("blr","br"):
                    indirect[ins.mnemonic]+=1
                    continue
                if (not ins.operands or ins.operands[0].type!=ARM64_OP_IMM):
                    continue
                target_address=int(ins.operands[0].imm)
                dest=addr_map.get(target_address) or plt_index.get(target_address)
                rec={"instruction_offset_bytes":int(ins.address-addr),
                     "mapped_numeric_guest_target":dest,
                     "target_is_known_guest_numeric_symbol":dest is not None}
                if ins.mnemonic=="bl":
                    direct.append(rec)
                    total_direct+=1
                else:
                    branch.append(rec)
            src_order=[x["target"] for x in candidates[name]["direct_calls_in_order"]]
            elf_guest_order=[x["mapped_numeric_guest_target"] for x in direct
                           if x["mapped_numeric_guest_target"]]
            source_counts=Counter(src_order);binary_counts=Counter(elf_guest_order)
            exact_identical=src_order==elf_guest_order
            overlap={key:min(val,binary_counts.get(key,0)) for key,val in source_counts.items()
                     if binary_counts.get(key,0)>0}
            total_agreed+=sum(overlap.values())
            mapped.append({
              "guest_numeric_function":name,
              "original_V48_elf_symbol_address":addr,
              "original_V48_elf_symbol_size":size,
              "ARM64_instructions_disassembled":count,
              "ARM64_bytes_disassembled":count*4,
              "all_source_calls_PRE99":len(src_order),
              "all_direct_ARM64_BL_in_V48":len(direct),
              "direct_BL_resolving_to_defined_guest_functions":len(elf_guest_order),
              "direct_BL_guest_callees_in_order":elf_guest_order[:250],
              "BL_source_PRE99_callee_list_exactly_equal_to_V48":exact_identical,
              "source_guest_call_counts":dict(source_counts),
              "V48_guest_BL_call_counts":dict(binary_counts),
              "overlap_source_and_ELF_direct_guest_call_count":sum(overlap.values()),
              "direct_unresolved_BL_count":len(direct)-len(elf_guest_order),
              "direct_BL_calls_resolved_through_relocated_PLT":sum(1 for rec in direct if rec["mapped_numeric_guest_target"]),
              "ARM64_indirect_branch_instruction_counts":dict(indirect),
              "direct_B_guest_tail_branches":sum(x["target_is_known_guest_numeric_symbol"] for x in branch)
            })
        return {
          "stage":"PRE533_SIGNED_V48_PAL_ARM64_GUEST_RELOCATED_PLT_CALLGRAPH_READONLY",
          "status":"AUDIT_OK",
          "exact_published_V48_apk_sha256":APK_SHA,
          "original_PAL_libmain_sha256":PAL_LIB_SHA,
          "apk_and_pal_lib_sha256_verified":True,
          "elf_numeric_guest_exported_function_count":len(addr_map),
          "target_pre529_numeric_function_count":len(mapped),
          "target_native_ARM64_guest_call_comparisons":mapped,
          "aggregate_direct_BL_in_targets":total_direct,
          "source_matched_guest_calls_total":total_agreed,
          "original_PAL_ELF_PLT_bytes":plt_bytes,
          "original_PAL_ELF_rela_PLT_record_count":plt_reloc_count,
          "original_PAL_ELF_rela_PLT_types":dict(relocation_kinds),
          "original_PAL_ELF_PLT_canonical_layout_verified":plt_layout_verified,
          "original_PAL_ELF_PLT_mapping_limitation":plt_decode_limit_reason,
          "original_PAL_ELF_guest_PLT_relocation_name_count":plt_guest_reloc_symbol_count,
          "PLT_relocations_used_only_when_layout_verified":True,
          "source_PPC_function_to_ARM64_symbol_identity_confirmed":True,
          "similar_guest_direct_call_targets_not_semantic_equivalence":True,
          "guest_Xbox_360_SetPackage_address_identified":False,
          "guest_Xbox_360_SetPackage_accepts_new_BMW_profile":False,
          "actual_V48_guest_execution_on_phone_verified":False,
          "guest_checkout_price_or_payment_function_identified":False,
          "safe_to_patch_or_buy_BMW":False,
          "original_APK_or_game_modified":False,
          "native_binary_or_guest_code_uploaded":False,
          "APK_built":False,
          "save_modified":False,
          "signing_key_touched":False
        }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    args=ap.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:report=audit()
    except Exception as e:
        report={
          "stage":"PRE533_SIGNED_V48_PAL_ARM64_GUEST_BL_CALLGRAPH_METADATA_READONLY",
          "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
          "original_APK_or_game_modified":False,"native_binary_or_guest_code_uploaded":False,
          "APK_built":False,"save_modified":False,
          "signing_key_touched":False,"safe_to_patch_or_buy_BMW":False
        }
    report["run_id"]=args.run_id
    report["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE533_STATUS",report["status"],flush=True)
    print("PRE533_GUEST_SYMBOLS",report.get("elf_numeric_guest_exported_function_count"),flush=True)
    print("PRE533_OVERLAPPING_SOURCE_CALLS",report.get("source_matched_guest_calls_total"),flush=True)
    print("PRE533_ERROR",report.get("error_type","none"),report.get("error",""),flush=True)
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    raise SystemExit(main())
