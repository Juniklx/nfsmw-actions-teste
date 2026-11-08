#!/usr/bin/env python3
"""PRE502: combine experimental BMW engine endpoint, RefSpec and level 1 and
VPAK collection/ExpN/PtrN repack IN RAM, then re-parse independently.

Source: SHA256-authenticated PAL/USA-identical GLOBAL/ATTRIBUTES.BIN.
The cloned stock engine has only its nine torque floats changed by a
SYNTHETIC +5% test vector, not a user-selected final calibration.
No original game content, rebuilt VPAK, ISO, APK or save is ever written.
No pvehicle upgrade counter or frontend purchase metadata is altered.
PAL loader compatibility and runtime tuning remain UNPROVEN and OFF.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA,hash32,get_names,chunks
from pre476_pal_performance_reference_resolution_readonly import collect_rows
from pre494_bmw_engine_scratch_refspec_relocation import get_field,find_ptr_record
from pre497_bmw_engine_torque_endpoint_synthetic import prototype

OUT=Path("/tmp/nfsmw-pre502/report.json")
PROOFS={
 "docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json":"pal_target_sha256",
 "docs/PRE499_BMW_ENGINE_COLLECTION_REPACK_PREFLIGHT.json":"source_pal_vpak_sha256",
 "docs/PRE497_BMW_TORQUE_ENGINE_SYNTHETIC_ENDPOINT.json":"authenticated_source_pal_vpak_sha256",
 "docs/PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json":"source_sha256",
 "docs/PRE501_BMW_ENGINE_ONE_LEVEL_COUNTER_SCRATCH.json":"source_sha256",
}
CANDIDATE="bmwm3gtr_upgrade_engine_pre499"
ENGINE_CLASS=hash32("engine")
CAR_HASH=hash32("bmwm3gtr")
NEW_HASH=hash32(CANDIDATE)
NEW_EXPORT_ID=hash32("engine/"+CANDIDATE)
SOURCE_ENGINE_EXPORT_ID=hash32("engine/bmwm3gtr")
CAREER_ENGINE_EXPORT_ID=hash32("engine/m3gtre46careerstart")
COL_KIND=0x8E112EB7
BO=128
OLD_BIN_LEN=354959
OLD_VLT_OFF=355136
OLD_VLT_LEN=342720
DAT_START,DAT_LEN=64,164784
EXP_START,EXP_LEN=164848,48000
PTR_START,PTR_LEN=212848,129872
SYNTHETIC_GAIN_BP=500
def sha(data):return hashlib.sha256(data).hexdigest()
def align(v,n):return (v+n-1)//n*n
def verify_provenance():
    objs={}
    for path,key in PROOFS.items():
        d=json.loads(Path(path).read_text())
        if d.get("status")!="AUDIT_OK" or d.get(key)!=EXPECTED_VPAK_SHA:
            raise ValueError("Original PAL source integrity report missing "+path)
        objs[path]=d
    p=objs["docs/PRE499_BMW_ENGINE_COLLECTION_REPACK_PREFLIGHT.json"]
    known={r["collection_hash"]:r["export_id"] for r in p["engine_collection_records"]}
    if (known.get(f"{CAR_HASH:08x}")!=f"{SOURCE_ENGINE_EXPORT_ID:08x}"
        or known.get(f"{hash32('m3gtre46careerstart'):08x}")!=f"{CAREER_ENGINE_EXPORT_ID:08x}"
        or p.get("candidate_new_collection_hash")!=f"{NEW_HASH:08x}"
        or p.get("datn_uncovered_tail_bytes")!=0
        or p.get("original_exports")!=2399
        or p.get("original_export_ids_unique") is not True
        or p.get("ptrn_switches",[])[-1].get("section")!=0):
        raise ValueError("Collection export ID formula/DatN/PtrN preflight mismatch")
    t=objs["docs/PRE497_BMW_TORQUE_ENGINE_SYNTHETIC_ENDPOINT.json"]
    v=[x for x in t["synthetic_test_vectors"] if x["synthetic_gain_basis_points"]==SYNTHETIC_GAIN_BP]
    if len(v)!=1 or not t.get("test_vectors_not_user_selected"):
        raise ValueError("PRE497 synthetic-only test vector missing")
    p=objs["docs/PRE501_BMW_ENGINE_ONE_LEVEL_COUNTER_SCRATCH.json"]
    if (p.get("original_BMW_engine_upgrade_counter")!=0
        or p.get("synthetic_BMW_engine_upgrade_counter")!=1
        or p.get("scratch_engine_counter_bin_relative_offset")!=256488
        or p.get("BMW_original_nitro_unchanged") is not True
        or p.get("Punto_all_original_upgrade_limits_unchanged") is not True):
        raise ValueError("PRE501 specific BMW engine one-tier proof mismatch")
    return objs,v[0]

def parse_exports(vlt,at,count,declared_len):
    if (vlt[at:at+4]!=b"ExpN"
        or int.from_bytes(vlt[at+4:at+8],"big")!=declared_len
        or int.from_bytes(vlt[at+8:at+12],"big")!=count):
        raise ValueError("Export chunk header/count mismatch")
    ids=Counter();entries=[]
    for i in range(count):
        expid,kind,unused,size,pos=struct.unpack_from(">IIIII",vlt,at+12+i*20)
        if unused or size<20 or pos<72 or pos+size>at:
            raise ValueError("Export record outside DatN")
        ids[expid]+=1
        entries.append((expid,kind,unused,size,pos))
    if any(n!=1 for n in ids.values()):
        raise ValueError("Collision of original or new Export IDs")
    return entries

def lookup_ptrn(vlt,ptr_start,ptr_bytes):
    region=vlt[ptr_start:ptr_start+ptr_bytes]
    if (region[:4]!=b"PtrN" or len(region)!=ptr_bytes
        or int.from_bytes(region[4:8],"big")!=ptr_bytes
        or (ptr_bytes-8)%12):
        raise ValueError("PtrN chunk header / stride invalid")
    section=None;result={}
    for offset in range(8,len(region),12):
        source,kind,index,dst=struct.unpack_from(">IHHI",region,offset)
        if kind==2:
            if index not in (0,1):raise ValueError("Unknown PtrN section")
            section=index
        elif kind in (1,3,4):
            if section is None:raise ValueError("PtrN section not initialized")
            if section==0:
                result.setdefault(source,[]).append((kind,index,dst))
        elif kind!=0:raise ValueError("Unknown PtrN instruction")
    if section!=0:raise ValueError("New PtrN insertion group not section0")
    return result

def audit():
    proofs,test=verify_provenance()
    r,position=locate()
    raw=r.read(position["absolute_offset"],position["size"])
    if len(raw)!=697856 or sha(raw)!=EXPECTED_VPAK_SHA:
        raise ValueError("Authentic source VPAK SHA256/size mismatch")
    _,binlen,vltlen,binoff,vltoff=struct.unpack_from("<IIIII",raw,16)
    if (binlen,vltlen,binoff,vltoff)!=(OLD_BIN_LEN,OLD_VLT_LEN,BO,OLD_VLT_OFF):
        raise ValueError("Original PAL vault layout differs")
    B=raw[binoff:binoff+binlen]
    V=raw[vltoff:vltoff+vltlen]
    vlt_sections=[x["tag"] for x in chunks(V,"VLT")[0]]
    if vlt_sections!=["DepN","StrN","DatN","ExpN","PtrN"]:
        raise ValueError("VLT required section sequence changed")
    existing=parse_exports(V,EXP_START,2399,EXP_LEN)
    if SOURCE_ENGINE_EXPORT_ID not in {x[0] for x in existing} or NEW_EXPORT_ID in {x[0] for x in existing}:
        raise ValueError("Original BMW export or new export ID uniqueness failure")
    collection_rows,_=collect_rows(V)
    rows=collection_rows.get((ENGINE_CLASS,CAR_HASH),[])
    if len(rows)!=1 or rows[0]["record_size"]!=36:
        raise ValueError("Original BMW engine CollectionLoad size not 36")
    original_row=rows[0]
    original_col_offset=original_row["record_offset_vlt"]
    original_collection=V[original_col_offset:original_col_offset+36]
    expid,kind,unused,size,ref=existing[original_row["export_index"]]
    if (expid,kind,unused,size,ref)!=(SOURCE_ENGINE_EXPORT_ID,COL_KIND,0,36,original_col_offset):
        raise ValueError("Original engine Export ID formatting changed")
    if (struct.unpack_from(">IIIIIIII",original_collection,0)[0:3]
        !=(CAR_HASH,ENGINE_CLASS,hash32("default"))):
        raise ValueError("Original stock engine collection header unexpected")
    if (hash32(CANDIDATE),ENGINE_CLASS) in {(x[0],x[1]) for x in []}:
        raise ValueError("Unreachable defensive marker")
    if (ENGINE_CLASS,NEW_HASH) in collection_rows:
        raise ValueError("New engine class/name hash collides")
    original_physics=proofs["docs/PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json"]
    original_engine=original_physics["class_models"]["engine"]["collections"]["bmwm3gtr"]
    physical_at=original_engine["bin_base_offset"]
    if not original_engine.get("has_bounded_layout") or not 0<=physical_at<=OLD_BIN_LEN-96:
        raise ValueError("Stock BMW engine physical base unbounded")
    block=B[physical_at:physical_at+96]
    if sha(block)!=original_engine["sha256"]:
        raise ValueError("Original physical engine SHA mismatch")
    scale=1+SYNTHETIC_GAIN_BP/10000
    patched=bytearray(block)
    for i in range(9):
        value=struct.unpack_from(">f",block,8+4*i)[0]
        if not math.isfinite(value) or value<=0:
            raise ValueError("Original torque sample invalid")
        struct.pack_into(">f",patched,8+4*i,value*scale)
    new_motor=bytes(patched)
    if (sha(new_motor)!=test["output_engine_layout_sha256"]
        or not prototype(block,SYNTHETIC_GAIN_BP)["all_non_torque_bytes_identical"]):
        raise ValueError("PRE497 experimental BMW torque curve SHA mismatch")
    if new_motor[:8]!=block[:8] or new_motor[44:]!=block[44:]:
        raise ValueError("BMW engine non-torque bytes changed")
    if CANDIDATE in get_names(B,chunks(B,"BIN")[0]):
        raise ValueError("Candidate not absent from StrE table")
    field_at=get_field(V)
    old_ptr_record=find_ptr_record(V,field_at)
    old_ptrs=lookup_ptrn(V,PTR_START,PTR_LEN)
    if old_ptrs.get(field_at)!=[(3,1,256660)]:
        raise ValueError("BMW pvehicle original RefSpec pointer changed")
    if old_ptrs.get(original_col_offset+28)!=[(3,1,physical_at)]:
        raise ValueError("Original BMW engine physical collection PtrN changed")
    stock_ref=struct.pack(">III",ENGINE_CLASS,CAR_HASH,0)
    if B[256660+8:256660+20]!=stock_ref:
        raise ValueError("Original engine pvehicle ref changed")
    new_ref=struct.pack(">III",ENGINE_CLASS,NEW_HASH,0)
    if (struct.unpack_from(">i",B,256488)[0]!=0 or
        struct.unpack_from(">i",B,269568+40)[0]!=0 or
        struct.unpack_from(">i",B,258352+40)[0]!=4 or
        struct.unpack_from(">i",B,256448+48)[0]!=3):
        raise ValueError("Original BMW, Punto, Nitro counters unexpectedly changed")
    new_bin=bytearray(B)
    struct.pack_into(">i",new_bin,256488,1)  # exactly one BMW engine level, RAM only
    layout_at=align(len(new_bin),16)
    new_bin.extend(b"\0"*(layout_at-len(new_bin)))
    new_bin.extend(new_motor)  # 96 physical bytes
    ref_at=align(len(new_bin),16)
    new_bin.extend(b"\0"*(ref_at-len(new_bin)))
    new_bin.extend(struct.pack(">HHHH",2,2,12,0)+stock_ref+new_ref)
    if len(new_bin)!=ref_at+32:
        raise ValueError("RefSpec allocation overflow")

    # New VLT collection is copied from the authenticated BMW engine only:
    # it has a different class-qualified hashed name and own physical pointer.
    new_collection=bytearray(original_collection)
    struct.pack_into(">I",new_collection,0,NEW_HASH)
    if len(new_collection)!=36 or struct.unpack_from(">I",new_collection,4)[0]!=ENGINE_CLASS:
        raise ValueError("New engine CollectionLoad copy malformed")
    new_col_at=EXP_START
    dat=bytearray(V[:EXP_START])
    dat.extend(new_collection)
    struct.pack_into(">I",dat,DAT_START+4,DAT_LEN+36)
    new_exp_record=struct.pack(">IIIII",NEW_EXPORT_ID,COL_KIND,0,36,new_col_at)
    original_exp=V[EXP_START:PTR_START]
    if original_exp[:4]!=b"ExpN" or len(original_exp)!=EXP_LEN:
        raise ValueError("Original ExpN bytes changed")
    exp=bytearray(original_exp[:12]+original_exp[12:-8]+new_exp_record+original_exp[-8:])
    struct.pack_into(">I",exp,4,EXP_LEN+20)
    struct.pack_into(">I",exp,8,2400)
    new_exp_at=EXP_START+36
    if len(exp)!=EXP_LEN+20:raise ValueError("New ExpN size wrong")
    ptr=bytearray(V[PTR_START:])
    if ptr[:4]!=b"PtrN" or len(ptr)!=PTR_LEN:
        raise ValueError("Original PtrN slice changed")
    struct.pack_into(">I",ptr,old_ptr_record+8,ref_at)
    ptr.extend(struct.pack(">IHHI",new_col_at+28,3,1,layout_at))
    struct.pack_into(">I",ptr,4,PTR_LEN+12)
    new_ptr_at=new_exp_at+len(exp)
    if len(ptr)!=PTR_LEN+12:raise ValueError("New PtrN size wrong")
    new_vlt=bytes(dat+exp+ptr)
    new_vltlen=OLD_VLT_LEN+36+20+12
    if len(new_vlt)!=new_vltlen:raise ValueError("New VLT length wrong")
    new_vlt_offset=align(BO+len(new_bin),16)
    final=bytearray(raw[:BO])
    final.extend(new_bin)
    final.extend(b"\0"*(new_vlt_offset-len(final)))
    final.extend(new_vlt)
    struct.pack_into("<I",final,20,len(new_bin))
    struct.pack_into("<I",final,24,new_vltlen)
    struct.pack_into("<I",final,32,new_vlt_offset)
    if final[:20]!=raw[:20] or final[28:32]!=raw[28:32]:
        raise ValueError("Outer VPAK source header mutated unexpectedly")

    # Independently reparse the newly formed VPAK from its own declared
    # sections, not from stale original offsets. No file is emitted.
    _,bi,vl,bo,vo=struct.unpack_from("<IIIII",final,16)
    if (bi,vl,bo,vo)!=(len(new_bin),new_vltlen,BO,new_vlt_offset):
        raise ValueError("Outer VPAK header failed reparse")
    if not (bo+bi<=vo and vo+vl==len(final)):
        raise ValueError("Rebuilt resource sections overlap or truncate")
    b2=bytes(final[bo:bo+bi])
    v2=bytes(final[vo:vo+vl])
    tags=chunks(v2,"VLT")[0]
    if ([x["tag"] for x in tags]!=["DepN","StrN","DatN","ExpN","PtrN"] or
        [x["declared_size"] for x in tags]!=[48,16,DAT_LEN+36,EXP_LEN+20,PTR_LEN+12] or
        [x["relative_offset"] for x in tags]!=[0,48,64,new_exp_at,new_ptr_at]):
        raise ValueError("Repacked VLT chunk map invalid")
    export2=parse_exports(v2,new_exp_at,2400,EXP_LEN+20)
    if export2[:2399]!=existing or export2[-1]!=(NEW_EXPORT_ID,COL_KIND,0,36,new_col_at):
        raise ValueError("Existing exports changed or new engine export unresolvable")
    name,cls,parent,flag,unused,num,types,base=struct.unpack_from(">IIIIIIII",v2,new_col_at)
    if (name,cls,parent,flag,num,types,base)!=(NEW_HASH,ENGINE_CLASS,hash32("default"),0,0,1,0xEFFECADD):
        raise ValueError("New BMW physical collection no longer matches original schema")
    ptrs2=lookup_ptrn(v2,new_ptr_at,PTR_LEN+12)
    if (ptrs2.get(field_at)!=[(3,1,ref_at)] or
        ptrs2.get(new_col_at+28)!=[(3,1,layout_at)] or
        ptrs2.get(original_col_offset+28)!=[(3,1,physical_at)]):
        raise ValueError("New/stock engine pointers failed independent VLT reparse")
    refs=struct.unpack_from(">HHHH",b2,ref_at)
    if refs!=(2,2,12,0) or b2[ref_at+8:ref_at+20]!=stock_ref or b2[ref_at+20:ref_at+32]!=new_ref:
        raise ValueError("Repacked BMW performance two-ref source array invalid")
    expected_bin=bytearray(B)
    struct.pack_into(">i",expected_bin,256488,1)
    if (b2[layout_at:layout_at+96]!=new_motor or
        b2[:OLD_BIN_LEN]!=bytes(expected_bin)):
        raise ValueError("Combined BMW engine endpoint or only engine counter differs")
    if (struct.unpack_from(">i",b2,256488)[0]!=1 or
        struct.unpack_from(">i",b2,269568+40)[0]!=0 or
        struct.unpack_from(">i",b2,258352+40)[0]!=4 or
        struct.unpack_from(">i",b2,256448+48)[0]!=3):
        raise ValueError("Scratch changed Nitro, Punto or BMW prologue")
    if v2[:DAT_START+4]!=V[:DAT_START+4] or v2[DAT_START+8:EXP_START]!=V[DAT_START+8:EXP_START]:
        raise ValueError("Original DatN attributes changed")
    if v2[new_exp_at+12:new_exp_at+12+2399*20]!=V[EXP_START+12:EXP_START+12+2399*20]:
        raise ValueError("Original ExpN records changed")
    # Original PtRN records aside from the BMW pvehicle engine array pointer
    # are exact byte matches; one new physical-layout fixup has been added.
    original_ptr=V[PTR_START:]
    new_ptr=v2[new_ptr_at:]
    pos=old_ptr_record+8
    if new_ptr[8:pos]!=original_ptr[8:pos] or new_ptr[pos+4:PTR_LEN]!=original_ptr[pos+4:]:
        raise ValueError("Original PtrN instructions modified unexpectedly")
    if b2[physical_at:physical_at+96]!=block:
        raise ValueError("The original BMW physical engine was overwritten")
    rows2={}
    for expid,kind,unused,size,pos in export2:
        if kind!=COL_KIND:continue
        row_name,row_class=struct.unpack_from(">II",v2,pos)
        rows2.setdefault((row_class,row_name),0)
        rows2[(row_class,row_name)]+=1
    if rows2.get((ENGINE_CLASS,NEW_HASH))!=1 or rows2.get((ENGINE_CLASS,CAR_HASH))!=1:
        raise ValueError("Repacked engine class+collection index not unique")
    if len(rows2)!=2339+1:
        raise ValueError("Original collection count changed unexpectedly")
    return {
        "stage":"PRE502_BMW_ENGINE_LEVEL1_FULL_COMBINED_RAM_REPACK",
        "status":"AUDIT_OK","source_pal_sha256":EXPECTED_VPAK_SHA,
        "source_vpak_bytes":len(raw),"scratch_vpak_bytes":len(final),
        "original_export_count":2399,"scratch_export_count":2400,
        "original_collection_count":2339,"scratch_collection_count":2340,
        "original_bin_bytes":OLD_BIN_LEN,"scratch_bin_bytes":len(b2),
        "original_vlt_bytes":OLD_VLT_LEN,"scratch_vlt_bytes":len(v2),
        "new_vlt_absolute_offset":new_vlt_offset,
        "original_motor_layout_SHA256":sha(block),
        "new_motor_synthetic_SHA256":sha(new_motor),
        "engine_synthetic_gain_percent":SYNTHETIC_GAIN_BP/100,
        "engine_synthetic_gain_is_not_user_selected":True,
        "engine_stock_layout_untouched":True,
        "engine_donor_careerstart_untouched":True,
        "new_engine_collection_name":CANDIDATE,
        "new_engine_collection_hash":f"{NEW_HASH:08x}",
        "new_engine_export_id_generated_with_original_class_slash_name_formula":f"{NEW_EXPORT_ID:08x}",
        "new_engine_collection_vlt_relative_offset":new_col_at,
        "new_engine_layout_bin_relative_offset":layout_at,
        "new_two_ref_array_bin_relative_offset":ref_at,
        "original_2399_exports_bytewise_preserved":True,
        "original_BMW_physics_base_unchanged":True,
        "original_4_other_performance_categories_unchanged":True,
        "original_vlt_data_records_bytewise_preserved":True,
        "new_engine_ExpN_RefSpec_PtrN_reparsed":True,
        "new_collection_name_missing_original_StrE":True,
        "new_name_registration_requirement_in_PAL_runtime_unknown":True,
        "original_pvehicle_engine_upgrade_limit_in_source_zero":True,
        "scratch_BMW_pvehicle_engine_upgrade_limit_one":True,
        "BMW_engine_counter_bin_offset":256488,
        "combined_new_engine_physical_collection_RefSpec_and_level1_in_one_VPAK":True,
        "source_BMW_original_nitro_level_three":True,
        "source_Punto_engine_level_four":True,
        "engine_upgrade_counter_is_single_BMW_only_edit":True,
        "original_Nitro_unchanged":True,
        "new_engine_not_buyable_in_game":True,
        "PAL_game_loader_support_verified":False,
        "gameplay_motor_power_increase_verified":False,
        "safe_to_enable_or_build_tuning":False,
        "source_game_files_modified":False,
        "modified_game_resource_file_written":False,
        "rebuilt_asset_uploaded":False,
        "apk_built":False,"save_modified":False,
        "range_transfer_bytes":r.total
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as e:result={"stage":"PRE502_BMW_ENGINE_LEVEL1_FULL_COMBINED_RAM_REPACK",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:260],
      "source_game_files_modified":False,"modified_game_resource_file_written":False,
      "rebuilt_asset_uploaded":False,"apk_built":False,"save_modified":False,
      "safe_to_enable_or_build_tuning":False}
    result["run_id"]=args.run_id;result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PRE502_STATUS",result["status"],flush=True)
    print("PRE502_REPACK_EXPORTS",result.get("scratch_export_count"),flush=True)
    print("PRE502_REPACK_COLLECTIONS",result.get("scratch_collection_count"),flush=True)
    print("PRE502_ERROR",result.get("error_type","none"),result.get("error",""),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
