#!/usr/bin/env python3
"""PRE531: source-to-distributed V48 guest-symbol presence audit, read only.

This is not a runtime test. An original release V48 APK is downloaded from
the owner's private Drive in a temporary runner directory, verified against
the exact PRE511 SHA and size, and two ARM64 ELF files are inspected for
defined guest routines linked in their symbol tables.

If symbols are stripped, absence is reported honestly; symbol presence
cannot establish equivalence of behavior, selected PAL/USA edition in a
device session, guest SetPackage semantics or ability to buy upgrades.
No APK/ELF content published, no repack/patch/key/save interaction.
"""
from __future__ import annotations
import argparse,hashlib,io,json,tempfile,zipfile
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from pre105_read_settings_source import drive_client

OUT=Path("/tmp/nfsmw-pre531/report.json")
APK_ID="1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C"
APK_NAME="NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk"
APK_SIZE=47104233
APK_SHA="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
LIBRARY_PINS={
  "lib/arm64-v8a/libmain.so":("f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3",41768224),
  "lib/arm64-v8a/libmain_usa.so":("4f32de8f2ff10d4748aa33f208774038ef9bfa402eacc61a49dd7e70f3b1bc83",41749696)
}
# Only named PPC guest functions previously authenticated as raw generated
# source numeric identities, not a PC-to-Xbox symbol equivalence assertion.
TARGETS={
 "package_list_builder":"sub_8256F818",
 "attribute_count_lookup":"sub_823E5988",
 "attribute_validator":"sub_8214B858",
 "attribute_reader":"sub_8214EDA8",
 "ui_caller_of_builder":"sub_82582F70",
 "near_shop_candidate_A":"sub_8256CBC8",
 "near_shop_candidate_B":"sub_8256C2F0",
 "historical_offset12_writer_A":"sub_8256BFC8",
 "historical_offset12_writer_B":"sub_82564D80",
}
# No broad untrusted symbol payloads are saved; only exact name hits in fixed allowlist.
def audit():
    prev=json.loads(Path("docs/PRE529_PAL_GUEST_SHOP_NEIGHBORS_MONEY_STORES_READONLY.json").read_text())
    earlier=json.loads(Path("docs/PRE528_PAL_GUEST_UPGRADE_COUNT_CALLGRAPH_READONLY.json").read_text())
    pin=json.loads(Path("docs/PRE511_ORIGINAL_V48_APK_RUNTIME_MARKERS_READONLY.json").read_text())
    if (prev.get("status")!="AUDIT_OK" or earlier.get("status")!="AUDIT_OK"
        or earlier.get("historical_codegen_shards_scanned")!=129
        or earlier.get("historical_codegen_functions_scanned")!=56338
        or prev.get("guest_SetPackage_address_proven") is not False
        or pin.get("status")!="AUDIT_OK"
        or pin.get("V48_apk_exact_hash_verified") is not True
        or pin.get("original_apk_sha256")!=APK_SHA):
        raise ValueError("PRE511/PRE528/PRE529 source pins or limitations missing")
    client=drive_client()
    meta=client.files().get(fileId=APK_ID,fields="id,name,size,mimeType",supportsAllDrives=True).execute()
    if (meta.get("id")!=APK_ID or meta.get("name")!=APK_NAME
        or int(meta.get("size",0))!=APK_SIZE or
        meta.get("mimeType")!="application/vnd.android.package-archive"):
        raise ValueError("V48 APK metadata identity differs from PRE511")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre531_") as td:
        orig=Path(td)/"v48_original_readonly.apk"
        with orig.open("wb") as f:
            dl=MediaIoBaseDownload(f,client.files().get_media(fileId=APK_ID,supportsAllDrives=True),chunksize=4*1024*1024)
            done=False
            while not done:_,done=dl.next_chunk(num_retries=4)
        if orig.stat().st_size!=APK_SIZE:
            raise ValueError("V48 APK byte size changed")
        d=hashlib.sha256()
        with orig.open("rb") as f:
            for block in iter(lambda:f.read(4*1024*1024),b""):
                d.update(block)
        if d.hexdigest()!=APK_SHA:
            raise ValueError("V48 APK SHA256 mismatch")
        libraries=[]
        with zipfile.ZipFile(orig) as archive:
            for name,(pinned_sha,pinned_size) in LIBRARY_PINS.items():
                z=archive.getinfo(name)
                if z.file_size!=pinned_size or z.file_size>80_000_000:
                    raise ValueError("V48 library uncompressed size changed "+name)
                content=archive.read(name)
                if content[:4]!=b"\x7fELF" or hashlib.sha256(content).hexdigest()!=pinned_sha:
                    raise ValueError("V48 library SHA256 changed "+name)
                elf=ELFFile(io.BytesIO(content))
                if elf["e_machine"]!="EM_AARCH64" or elf["e_type"]!="ET_DYN":
                    raise ValueError("Original V48 library ELF machine or type unexpected")
                section_names=[s.name for s in elf.iter_sections()]
                symtab_meta=[]
                found={label:[] for label in TARGETS}
                total_func_symbols=0
                for section in elf.iter_sections():
                    if not isinstance(section,SymbolTableSection):continue
                    count=Counter()
                    exact_hits=Counter()
                    for sym in section.iter_symbols():
                        count[sym["st_info"]["type"]]+=1
                        if sym["st_info"]["type"]!="STT_FUNC":
                            continue
                        if sym["st_shndx"]=="SHN_UNDEF":
                            continue
                        total_func_symbols+=1
                        for label,target in TARGETS.items():
                            if (sym.name==target or sym.name.endswith(target) or
                                sym.name.endswith(target+"v")):
                                exact_hits[label]+=1
                                if len(found[label])<5:
                                    found[label].append({
                                      "symbol_table":section.name,
                                      "symbol_name":sym.name[:100],
                                      "st_size":int(sym["st_size"]),
                                      "st_value":int(sym["st_value"]),
                                      "type":"defined_STT_FUNC"
                                    })
                    symtab_meta.append({
                      "table":section.name,"symbol_count":section.num_symbols(),
                      "defined_function_symbols":count.get("STT_FUNC",0),
                      "identified_symbol_counts_by_label":dict(exact_hits)
                    })
                if sum(len(v) for v in found.values())>90:
                    raise ValueError("Unexpectedly broad guest symbol matches")
                libraries.append({
                  "zip_entry":name,"sha256":pinned_sha,
                  "original_elf_bytes":len(content),
                  "ELF_header":{"e_machine":elf["e_machine"],"e_type":elf["e_type"]},
                  "ELF_section_count":elf.num_sections(),
                  "symbol_table_metadata":symtab_meta,
                  "has_static_symtab":".symtab" in section_names,
                  "has_dynamic_symtab":".dynsym" in section_names,
                  "total_defined_function_symbols_scanned":total_func_symbols,
                  "guest_target_elf_symbol_matches":found,
                  "static_symbol_match_is_not_proof_of_execution_or_semantics":True
                })
        return {
          "stage":"PRE531_ORIGINAL_V48_PAL_GUEST_ELF_SYMBOL_PROVENANCE_READONLY",
          "status":"AUDIT_OK",
          "original_V48_apk_sha256":APK_SHA,
          "original_V48_apk_bytes":APK_SIZE,
          "authenticated_exact_V48_apk":True,
          "libraries":libraries,
          "symbol_search_allowlist":TARGETS,
          "all_target_symbols_linked_or_executed_proven":False,
          "historical_PRE99_to_V48_semantic_equivalence_verified":False,
          "V48_actual_PAL_library_selected_on_phone_verified":False,
          "guest_SetPackage_function_identity_verified":False,
          "guest_SetPackage_synthetic_BMW_acceptance_verified":False,
          "BMW_upgrade_purchase_or_persistence_verified":False,
          "new_APK_built":False,
          "original_game_or_APK_modified":False,
          "guest_source_or_ELF_published":False,
          "save_modified":False,
          "signing_material_accessed":False,
          "ready_to_enable_BMW_tuning":False
        }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"stage":"PRE531_ORIGINAL_V48_PAL_GUEST_ELF_SYMBOL_PROVENANCE_READONLY",
           "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
           "new_APK_built":False,"original_game_or_APK_modified":False,
           "guest_source_or_ELF_published":False,"save_modified":False,
           "signing_material_accessed":False,"ready_to_enable_BMW_tuning":False}
    r["run_id"]=args.run_id
    r["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE531_STATUS",r["status"],flush=True)
    print("PRE531_TARGETS",[(x["zip_entry"],sum(len(z) for z in x["guest_target_elf_symbol_matches"].values()))
         for x in r.get("libraries",[])],flush=True)
    print("PRE531_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
