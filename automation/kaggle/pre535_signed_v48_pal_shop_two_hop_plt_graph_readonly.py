#!/usr/bin/env python3
"""PRE535: authenticated signed V48 PAL ELF two-hop candidate callgraph.

Find one/two direct-guest-call hops from UI package list, related callbacks,
and historical field +12 writers. PLT references are resolved from the
ORIGINAL AArch64 ELF .rela.plt JUMP_SLOT, not guessed offsets.

The output contains bounded numeric graph metadata only. Shared reachable
functions are NOT demonstrated SetPackage, money writes, checkout, or any
executed code. Do not build APK, alter source, publish binaries or touch saves.
"""
from __future__ import annotations
import argparse,hashlib,io,json,re,struct,tempfile,zipfile
from collections import Counter,defaultdict,deque
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from elftools.elf.sections import SymbolTableSection
from pre105_read_settings_source import drive_client

OUT=Path("/tmp/nfsmw-pre535/report.json")
APK_ID="1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C"
APK_NAME="NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk"
APK_SIZE=47104233
APK_SHA="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
LIB="lib/arm64-v8a/libmain.so"
LIB_SHA="f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3"
LIB_SIZE=41768224
SOURCES={
 "ui_package_list":"sub_8256F818",
 "ui_package_related":"sub_8256CBC8",
 "ui_list_caller":"sub_82582F70",
 "historical_field12_writer_A":"sub_8256BFC8",
 "historical_field12_writer_B":"sub_82564D80",
}
GUEST=re.compile(r"^sub_[0-9a-fA-F]{8}$")
MAX_FUNCTION=100_000
MAX_NEIGHBORS=250
MAX_TOTAL_SCAN=5_000_000
MAX_LIST=75

def load_lib():
    drive=drive_client()
    meta=drive.files().get(fileId=APK_ID,fields="id,name,size,mimeType",supportsAllDrives=True).execute()
    if (meta.get("id")!=APK_ID or meta.get("name")!=APK_NAME
        or int(meta.get("size",-1))!=APK_SIZE
        or meta.get("mimeType")!="application/vnd.android.package-archive"):
        raise ValueError("Published V48 Drive metadata different from pin")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre535_") as td:
        p=Path(td)/"v48.apk"
        with p.open("wb") as f:
            downloader=MediaIoBaseDownload(f,drive.files().get_media(fileId=APK_ID,
                supportsAllDrives=True),chunksize=4*1024*1024)
            done=False
            while not done:
                _,done=downloader.next_chunk(num_retries=4)
        if p.stat().st_size!=APK_SIZE:raise ValueError("Original signed V48 APK length differs")
        h=hashlib.sha256()
        with p.open("rb") as fp:
            for part in iter(lambda:fp.read(4*1024*1024),b""):h.update(part)
        if h.hexdigest()!=APK_SHA:raise ValueError("Original signed V48 APK SHA differs")
        with zipfile.ZipFile(p) as z:
            info=z.getinfo(LIB)
            if info.file_size!=LIB_SIZE:
                raise ValueError("Original PAL libmain uncompressed size differs")
            raw=z.read(info)
    if hashlib.sha256(raw).hexdigest()!=LIB_SHA:
        raise ValueError("Original PAL libmain SHA differs")
    return raw

def audit():
    previous=json.loads(Path("docs/PRE533_ORIGINAL_V48_PAL_GUEST_RELOCATED_PLT_CALLGRAPH_READONLY.json").read_text())
    original=json.loads(Path("docs/PRE529_PAL_GUEST_SHOP_NEIGHBORS_MONEY_STORES_READONLY.json").read_text())
    handoff=json.loads(Path("docs/PRE534_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (previous.get("status")!="AUDIT_OK" or
        previous.get("original_PAL_libmain_sha256")!=LIB_SHA or
        previous.get("exact_published_V48_apk_sha256")!=APK_SHA or
        previous.get("original_PAL_ELF_PLT_canonical_layout_verified") is not True or
        previous.get("original_PAL_ELF_rela_PLT_record_count")!=17107 or
        previous.get("original_PAL_ELF_guest_PLT_relocation_name_count")!=15598 or
        previous.get("source_matched_guest_calls_total")!=164 or
        previous.get("guest_Xbox_360_SetPackage_address_identified") is not False or
        original.get("status")!="AUDIT_OK" or
        original.get("original_money_offset12_write_candidate_count")!=8 or
        handoff.get("status")!="AUDIT_OK" or
        handoff.get("new_total_bytes")!=800575):
        raise ValueError("PRE533/PRE529/PRE534 authenticated evidence boundary changed")
    raw=load_lib()
    elf=ELFFile(io.BytesIO(raw))
    if elf["e_machine"]!="EM_AARCH64" or elf["e_type"]!="ET_DYN":
        raise ValueError("Published original PAL ELF type/arch unexpected")
    symtab=elf.get_section_by_name(".dynsym")
    plt=elf.get_section_by_name(".plt")
    rela=elf.get_section_by_name(".rela.plt")
    if not isinstance(symtab,SymbolTableSection) or not isinstance(rela,RelocationSection) or plt is None:
        raise ValueError("Missing original PAL dynamic relocation tables")
    plt_n=rela.num_relocations()
    plt_start=int(plt["sh_addr"])
    if (plt_n!=17107 or int(plt["sh_size"])!=32+16*plt_n or plt_start%4):
        raise ValueError("AArch64 PLT index layout not authenticated")
    reloc_guest={}
    reloc_type_counts=Counter()
    for i,rel in enumerate(rela.iter_relocations()):
        kind=int(rel.entry.r_info_type)
        reloc_type_counts[kind]+=1
        if kind!=1026:raise ValueError("Unexpected AArch64 .rela.plt record type")
        name=symtab.get_symbol(int(rel.entry.r_info_sym)).name
        if name.startswith("__imp__"):name=name[len("__imp__"):]
        if GUEST.fullmatch(name):
            reloc_guest[plt_start+32+16*i]=name
    if len(reloc_guest)!=15598:
        raise ValueError("Original PAL guest relocation count changed")
    defs={}
    for sym in symtab.iter_symbols():
        name=sym.name
        if (not GUEST.fullmatch(name) or
            sym["st_info"]["type"]!="STT_FUNC" or
            sym["st_shndx"]=="SHN_UNDEF"):continue
        v=int(sym["st_value"]);size=int(sym["st_size"])
        if size>0 and v%4==0 and size%4==0:
            if name in defs:raise ValueError("Duplicate original guest export: "+name)
            defs[name]=(v,size)
    if len(defs)!=56338:raise ValueError("Original V48 PAL numeric guest symbol count changed")
    segments=[]
    for seg in elf.iter_segments():
        if seg["p_type"]=="PT_LOAD" and seg["p_flags"]&1:
            segments.append((int(seg["p_vaddr"]),int(seg["p_offset"]),int(seg["p_filesz"])))
    def get_code(name):
        if name not in defs:raise ValueError("No authenticated PAL guest function "+name)
        addr,size=defs[name]
        if not 4<=size<=MAX_FUNCTION:
            raise ValueError("Original guest function size out of bounded range")
        for start,offset,length in segments:
            if start<=addr and addr+size<=start+length:
                pos=offset+addr-start
                return addr,raw[pos:pos+size]
        raise ValueError("Guest function not contained in original executable segment")

    # Extract only BL immediate instructions; any BL to PLT is linked via
    # RELA metadata, not by assuming an offset-to-name proximity.
    inspected={}
    bytes_examined=0
    for name in sorted(set(SOURCES.values())):
        if name not in original["target_guest_definition_metadata"]:
            raise ValueError("PRE529 source anchor not present in audit "+name)
    def inspect(name):
        nonlocal bytes_examined
        if name in inspected:return inspected[name]
        addr,code=get_code(name)
        bytes_examined+=len(code)
        if bytes_examined>MAX_TOTAL_SCAN:raise ValueError("Exceeded bounded ARM64 instruction scan budget")
        guest_calls=[]
        unknown_bl=0
        direct_bl=0
        for i,(w,) in enumerate(struct.iter_unpack("<I",code)):
            if w&0xFC000000!=0x94000000:continue
            direct_bl+=1
            imm=w&0x03ffffff
            if imm&0x02000000:imm-=0x04000000
            target=addr+4*i+(imm<<2)
            fn=reloc_guest.get(target)
            if fn:
                guest_calls.append(fn)
            else:
                unknown_bl+=1
        x={"fn":name,"size":len(code),"direct_BL":direct_bl,
           "resolved_guest_BL":len(guest_calls),
           "non_guest_or_unresolved_BL":unknown_bl,
           "guest_calls_in_order":guest_calls}
        inspected[name]=x
        return x

    direct={}
    for role,root in SOURCES.items():
        direct[role]=inspect(root)["guest_calls_in_order"]
    neighbor_names=set()
    for targets in direct.values():neighbor_names.update(targets)
    if len(neighbor_names)>MAX_NEIGHBORS:
        raise ValueError("Unusually broad first-hop neighborhood; adjust audit scope")
    for name in sorted(neighbor_names):
        inspect(name)
    # Verify all source anchors against PRE533's direct BL guest names.
    prec={v["guest_numeric_function"]:v for v in previous["target_native_ARM64_guest_call_comparisons"]}
    for name in SOURCES.values():
        if name not in prec:
            raise ValueError("Missing PRE533 original guest call comparison "+name)
        if inspected[name]["guest_calls_in_order"]!=prec[name]["direct_BL_guest_callees_in_order"]:
            raise ValueError("Raw ARM64 decode disagrees with independent PRE533 capstone "+name)

    paths={}
    for role,root in SOURCES.items():
        candidates=defaultdict(list)
        for callee in inspected[root]["guest_calls_in_order"]:
            candidates[callee].append([root,callee])
            for grandchild in inspected[callee]["guest_calls_in_order"]:
                candidates[grandchild].append([root,callee,grandchild])
        paths[role]=dict(candidates)
    # No guest SetPackage labels are inferred from graph intersection.
    ui_roles=("ui_package_list","ui_package_related","ui_list_caller")
    money_roles=("historical_field12_writer_A","historical_field12_writer_B")
    ui=set().union(*(paths[k].keys() for k in ui_roles))
    money=set().union(*(paths[k].keys() for k in money_roles))
    cross=sorted(ui&money)
    # Exclude seeds from intersection so the paths are not tautologies.
    cross=[n for n in cross if n not in SOURCES.values()]
    summaries={}
    for role,root in SOURCES.items():
        call_list=inspected[root]["guest_calls_in_order"]
        summaries[role]={
          "numeric_root":root,"direct_BL":inspected[root]["direct_BL"],
          "guest_BL_resolved":len(call_list),
          "unique_direct_guest_callees":len(set(call_list)),
          "unique_reachable_guest_callees_within_two_hops":len(paths[role]),
          "first_hop_numeric_guest_targets":sorted(set(call_list))[:MAX_LIST]
        }
    intersections=[]
    for fn in cross[:MAX_LIST]:
        u=[k for k in ui_roles if fn in paths[k]]
        m=[k for k in money_roles if fn in paths[k]]
        samples={}
        for role in u[:2]+m[:2]:
            seqs=paths[role][fn]
            samples[role]=min(seqs,key=len)
        intersections.append({"numeric_function":fn,
          "ui_root_roles_reaching":u,"field_writer_root_roles_reaching":m,
          "witness_paths_at_most_two_calls":samples,
          "does_NOT_identify_checkout_SetPackage_or_cash":True})
    return {
      "stage":"PRE535_SIGNED_V48_PAL_SHOP_AND_FIELD_WRITER_TWO_HOP_PLT_GRAPH_READONLY",
      "status":"AUDIT_OK",
      "published_original_V48_apk_sha256":APK_SHA,
      "published_original_V48_PAL_libmain_sha256":LIB_SHA,
      "original_elf_numeric_guest_function_count":len(defs),
      "original_elf_PLT_jump_slot_count":plt_n,
      "original_elf_guest_PLT_relocation_count":len(reloc_guest),
      "original_elf_relocation_types":{str(k):v for k,v in reloc_type_counts.items()},
      "target_root_count":len(SOURCES),
      "first_hop_neighbor_functions_inspected":len(neighbor_names),
      "total_distinct_functions_inspected":len(inspected),
      "total_ARM64_function_bytes_scanned":bytes_examined,
      "root_graph_summaries":summaries,
      "guest_root_two_hop_intersection_count":len(cross),
      "guest_root_two_hop_intersection_samples":intersections,
      "all_intersections_are_static_and_not_symbol_semantics":True,
      "graph_static_only_NOT_guest_runtime":True,
      "guest_SetPackage_guest_address_proven":False,
      "guest_checkout_transaction_path_proven":False,
      "guest_BMW_engine_refspec_accepted":False,
      "game_data_or_elf_written_or_uploaded":False,
      "APK_built":False,"save_modified":False,
      "signing_material_accessed":False,
      "BMW_tuning_enabled":False
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",required=True)
    a=parser.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try: result=audit()
    except Exception as e:
        result={"stage":"PRE535_SIGNED_V48_PAL_SHOP_AND_FIELD_WRITER_TWO_HOP_PLT_GRAPH_READONLY",
          "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
          "game_data_or_elf_written_or_uploaded":False,"APK_built":False,
          "save_modified":False,"signing_material_accessed":False,
          "BMW_tuning_enabled":False}
    result["run_id"]=a.run_id
    result["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE535_STATUS",result["status"],flush=True)
    print("PRE535_GUEST_NEIGHBORS",result.get("first_hop_neighbor_functions_inspected"),flush=True)
    print("PRE535_TWO_HOP_INTERSECTIONS",result.get("guest_root_two_hop_intersection_count"),flush=True)
    print("PRE535_ERROR",result.get("error_type","none"),result.get("error",""),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    raise SystemExit(main())
