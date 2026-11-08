#!/usr/bin/env python3
"""PRE499 read-only survey to design independent BMW engine collection repack.

Examine authenticated original PAL/USA-identical 697856-byte VPAK with bounded
Drive requests. Characterize DatN, ExpN, PtrN, collection export ID semantics,
physical layout ownership, padding and second-endpoint hash collision risk.
No generated engine content, altered VPAK, game assets, APK or save written.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA,hash32,get_names,chunks
from pre476_pal_performance_reference_resolution_readonly import collect_rows
from pre477_pal_bmw_punto_physics_layout_compare import fixup_lookup,parse_export,SIZES
OUT=Path("/tmp/nfsmw-pre499/report.json")
CANDIDATE="bmwm3gtr_upgrade_engine_pre499"
ENGINE_HASH=hash32("engine")
ORIGINAL_ENGINE_HASH=hash32("bmwm3gtr")
DONOR_HASH=hash32("m3gtre46careerstart")
EXP_OFF=164848; EXP_LEN=48000
PTR_OFF=212848; PTR_LEN=129872
DAT_OFF=64; DAT_LEN=164784
def source():
    expected=json.loads(Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json").read_text())
    if (expected.get("status")!="AUDIT_OK"
        or expected.get("pal_target_sha256")!=EXPECTED_VPAK_SHA
        or expected.get("pal_resource_identical_to_usa_reference") is not True):
        raise ValueError("Authentic original PAL identity missing")
    r,loc=locate()
    raw=r.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA or len(raw)!=697856:
        raise ValueError("Original VPAK fingerprint changed")
    _,bl,vl,bo,vo=struct.unpack_from("<IIIII",raw,16)
    if (bl,vl,bo,vo)!=(354959,342720,128,355136):
        raise ValueError("Unexpected VPAK vault size/offset")
    return r,raw,raw[bo:bo+bl],raw[vo:vo+vl]
def survey():
    reader,raw,B,V=source()
    names=get_names(B,chunks(B,"BIN")[0])
    collection_index,_=collect_rows(V)
    class_defs, selected=parse_export(V)
    all_keys=set()
    records=[]
    ids=Counter()
    col_ids={}
    intervals=[]
    if V[EXP_OFF:EXP_OFF+4]!=b"ExpN" or int.from_bytes(V[EXP_OFF+4:EXP_OFF+8],"big")!=EXP_LEN or int.from_bytes(V[EXP_OFF+8:EXP_OFF+12],"big")!=2399:
        raise ValueError("ExpN header changed")
    for i in range(2399):
        at=EXP_OFF+12+i*20
        export_id,kind,unused,size,pos=struct.unpack_from(">IIIII",V,at)
        if unused!=0 or not (DAT_OFF+8<=pos<=DAT_OFF+DAT_LEN-size) or size<20:
            raise ValueError("Export record escapes DatN bounds")
        ids[export_id]+=1
        intervals.append((pos,pos+size))
        if kind==0x8E112EB7:
            if size<32:raise ValueError("Bad CollectionLoad size")
            name,cls,parent,optional_count,unknown,n,types,marker=struct.unpack_from(">IIIIIIII",V,pos)
            key=(cls,name)
            if key in all_keys:raise ValueError("Duplicate original collection+class")
            all_keys.add(key)
            if key in ((ENGINE_HASH,ORIGINAL_ENGINE_HASH),(ENGINE_HASH,DONOR_HASH)):
                records.append({"export_index":i,"export_id":f"{export_id:08x}",
                    "export_id_equals_collection_name_hash":export_id==name,
                    "class_hash":f"{cls:08x}","collection_hash":f"{name:08x}",
                    "parent_hash":f"{parent:08x}",
                    "optional_count":n,"field_type_count":types,
                    "record_offset_vlt":pos,"record_size":size,
                    "layout_marker":f"{marker:08x}",
                    "collection_header_32_bytes_sha256":hashlib.sha256(V[pos:pos+32]).hexdigest()})
                col_ids[name]=export_id
    intervals.sort()
    if any(a[1]>b[0] for a,b in zip(intervals,intervals[1:])):
        raise ValueError("Original VLT DatN export records overlap")
    used_end=max(x[1] for x in intervals)
    uncovered_tail=DAT_OFF+DAT_LEN-used_end
    original_engine_rows=collection_index.get((ENGINE_HASH,ORIGINAL_ENGINE_HASH),[])
    if len(original_engine_rows)!=1 or len(records)!=2:
        raise ValueError("Original BMW engine and careerstart records not found")
    if class_defs[ENGINE_HASH]["base_size_declared"]!=SIZES["engine"]:
        raise ValueError("Original engine physical size is not 96 bytes")
    fixes=fixup_lookup(V)
    original_engine=original_engine_rows[0]
    layout_src=original_engine["record_offset_vlt"]+28
    engine_fix=fixes.get(layout_src,[])
    if len(engine_fix)!=1 or engine_fix[0][0:2]!=(3,1):
        raise ValueError("Engine physical data PtrN fixup ambiguous")
    ptr=V[PTR_OFF:PTR_OFF+PTR_LEN]
    if ptr[:4]!=b"PtrN" or len(ptr)!=PTR_LEN:raise ValueError("PtrN header invalid")
    section=None; switches=[]; sections=Counter(); ptr_target_counts=Counter()
    source_refs=Counter()
    for rel in range(8,len(ptr),12):
        src,kind,index,dst=struct.unpack_from(">IHHI",ptr,rel)
        if kind==2:
            if index not in (0,1):raise ValueError("PtrN section switch invalid")
            section=index
            switches.append({"chunk_relative_offset":rel,"section":index,
                             "preceding_record_count":sum(sections.values())})
        elif kind in (1,3,4):
            if section not in (0,1):raise ValueError("Bad PtrN section")
            sections[f"section{section}_kind{kind}_dst_index{index}"]+=1
            if section==0:source_refs[src]+=1
            if kind==3 and index==1 and section==0:ptr_target_counts[dst]+=1
        elif kind!=0:raise ValueError("Unknown PtrN record type")
    if len(switches)<1 or source_refs[layout_src]!=1:
        raise ValueError("Missing unique BMW physical PtrN fixup")
    newhash=hash32(CANDIDATE)
    names_hashes={hash32(x) for x in names}
    if newhash in names_hashes or (ENGINE_HASH,newhash) in all_keys:
        raise ValueError("Proposed new BMW engine hash collides with original data")
    old_export_id_semantics=[r["export_id_equals_collection_name_hash"] for r in records]
    gap=raw[128+354959:355136]
    if len(gap)!=49 or any(gap):raise ValueError("Original BIN/VLT gap differs")
    return {
        "stage":"PRE499_PAL_BMW_ENGINE_COLLECTION_REPACK_PREFLIGHT",
        "status":"AUDIT_OK",
        "source_pal_vpak_sha256":EXPECTED_VPAK_SHA,
        "original_resource_bytes":len(raw),
        "vlt_sections_sizes":{"DatN":DAT_LEN,"ExpN":EXP_LEN,"PtrN":PTR_LEN},
        "original_exports":2399,
        "original_collection_records":sum(1 for key in all_keys),
        "original_export_ids_unique":all(count==1 for count in ids.values()),
        "engine_collection_records":records,
        "original_engine_layout_pointer_bin_offset":engine_fix[0][2],
        "original_engine_layout_size":SIZES["engine"],
        "original_engine_layout_ptrn_source_vlt_offset":layout_src,
        "datn_records_nonoverlapping":True,
        "datn_last_record_end":used_end,
        "datn_uncovered_tail_bytes":uncovered_tail,
        "ptrn_switches":switches[:12],
        "ptrn_total_switches":len(switches),
        "ptrn_section_type_counts":dict(sections),
        "engine_layout_ptrn_source_reference_count":source_refs[layout_src],
        "candidate_new_collection_name":CANDIDATE,
        "candidate_new_collection_hash":f"{newhash:08x}",
        "candidate_new_hash_not_in_original_StrE":True,
        "candidate_new_engine_class_and_collection_pair_unique":True,
        "string_table_registration_may_be_required_by_game_loader":True,
        "new_engine_layout_96_bytes_plus_RefSpec_array_32_bytes_fits_old_49_byte_gap":False,
        "moving_expN_ptrN_chunks_requires_pointer_offset_audit":True,
        "runtime_loader_acceptance_proven":False,
        "engine_upgrade_catalog_validated":False,
        "feasible_to_write_functional_GAME_MOD_NOW":False,
        "source_touched":False,
        "modified_VPAK_written":False,
        "apk_built":False,"save_modified":False,
        "runtime_tuning_enabled":False,
        "source_bytes_transferred":reader.total
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=survey()
    except Exception as e:r={
        "stage":"PRE499_PAL_BMW_ENGINE_COLLECTION_REPACK_PREFLIGHT",
        "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:240],
        "source_touched":False,"modified_VPAK_written":False,
        "apk_built":False,"save_modified":False,"runtime_tuning_enabled":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE499_STATUS",r["status"],flush=True)
    print("PRE499_EXPORTS",r.get("original_exports"),flush=True)
    print("PRE499_DATN_TAIL",r.get("datn_uncovered_tail_bytes"),flush=True)
    print("PRE499_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
