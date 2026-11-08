#!/usr/bin/env python3
"""PRE495 — use an EXISTING second BMW original engine profile in a RAM-only
two-reference candidate; compare all original torque samples. Do NOT infer
that prologue calibration is a useful upgrade or that PAL runtime applies it.
Never write patched game bytes, APK, or user saves.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,math
from pathlib import Path
from datetime import datetime,timezone
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA,hash32
from pre474_bmw_punto_refs_readonly import array_candidate
from pre476_pal_performance_reference_resolution_readonly import collect_rows,parent_chain
from pre477_pal_bmw_punto_physics_layout_compare import parse_export,fixup_lookup,SIZES
from pre494_bmw_engine_scratch_refspec_relocation import (
    get_field,find_ptr_record,BIN_START,BIN_SIZE,VLT_START,VLT_SIZE,STOCK_ARRAY,
    PTR_START,PTR_SIZE,ENGINE_HASH,CAR_HASH,sha,proof)

OUT=Path("/tmp/nfsmw-pre495/report.json")
DONOR="m3gtre46careerstart"
DONOR_HASH=hash32(DONOR)
ENGINE_SIZE=SIZES["engine"]
def physical(vlt,bin_data,cls,key,expected_sha):
    classes,rows=parse_export(vlt)
    meta=classes.get(cls)
    row=rows.get((cls,key))
    if meta is None or row is None or meta["base_size_declared"]!=ENGINE_SIZE:
        raise ValueError("Original engine class/collection metadata missing")
    fix=fixup_lookup(vlt).get(row["vlt_record_offset"]+28,[])
    matches=[x for x in fix if x[0]==3 and x[1]==1 and x[2]+ENGINE_SIZE<=len(bin_data)]
    if len(matches)!=1:raise ValueError("No unique original engine physical layout")
    offset=matches[0][2]
    blob=bin_data[offset:offset+ENGINE_SIZE]
    if sha(blob)!=expected_sha:raise ValueError("PRE477 original engine collection SHA mismatch")
    capacity,count,element_size,flags=struct.unpack_from(">HHHH",blob,0)
    if (not 1<=count<=capacity<=9 or element_size!=4
        or 8+capacity*4>ENGINE_SIZE):
        raise ValueError("Unrecognized original engine TORQUE float array header")
    values=struct.unpack_from(">"+str(count)+"f",blob,8)
    if any(not math.isfinite(x) or abs(x)>20000 for x in values):
        raise ValueError("Non-finite torque curve in original engine")
    return {"bin_offset":offset,"sha256":expected_sha,"samples":values,
            "count":count,"max":max(values),"min":min(values),
            "peak_sample_index":values.index(max(values))}
def audit():
    identity=proof("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json","pal_target_sha256")
    if not identity.get("pal_resource_identical_to_usa_reference"):
        raise ValueError("PAL and USA resource identity not verified")
    refs=proof("docs/PRE474_PAL_BMW_PUNTO_PERFORMANCE_REF_ARRAYS.json","vpak_sha256")
    physics=proof("docs/PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json","source_sha256")
    previous=json.loads(Path("docs/PRE494_BMW_ENGINE_IN_MEMORY_REFSPEC_RELOCATION.json").read_text())
    if previous.get("status")!="AUDIT_OK" or previous.get("scratch_pointer_reparse_ok") is not True:
        raise ValueError("PRE494 scratch offset proof unavailable")
    original_ref=refs["vehicles"]["bmwm3gtr"]["categories_with_explicit_references"]["engine"]
    if original_ref["capacity"]!=1 or original_ref["item_count"]!=1:
        raise ValueError("BMW original one-reference layout changed")
    reader,position=locate()
    raw=reader.read(position["absolute_offset"],position["size"])
    if len(raw)!=697856 or sha(raw)!=EXPECTED_VPAK_SHA:
        raise ValueError("User's original PAL-equivalent VPAK SHA changed")
    _,length,vl,bo,vo=struct.unpack_from("<IIIII",raw,16)
    if (length,vl,bo,vo)!=(BIN_SIZE,VLT_SIZE,BIN_START,VLT_START):
        raise ValueError("Original resource geometry changed")
    bin_data=raw[bo:bo+length]
    vlt=raw[vo:vo+vl]
    engine_expected=physics["class_models"]["engine"]["collections"]
    bmw=physical(vlt,bin_data,ENGINE_HASH,CAR_HASH,
                 engine_expected["bmwm3gtr"]["sha256"])
    donor=physical(vlt,bin_data,ENGINE_HASH,DONOR_HASH,
                   engine_expected[DONOR]["sha256"])
    if len(bmw["samples"])!=len(donor["samples"]):
        raise ValueError("BMW engine profiles have incompatible sample counts")
    chain,index=collect_rows(vlt)
    c0,state0=parent_chain(chain,ENGINE_HASH,CAR_HASH)
    c1,state1=parent_chain(chain,ENGINE_HASH,DONOR_HASH)
    if not c0 or not c1 or state0!="END_ZERO_PARENT" or state1!="END_ZERO_PARENT":
        raise ValueError("Engine collection parent chain not fully resolved")
    stock=bin_data[STOCK_ARRAY+8:STOCK_ARRAY+20]
    if stock!=struct.pack(">III",ENGINE_HASH,CAR_HASH,0):
        raise ValueError("Stock BMW engine RefSpec wrong")
    newref=struct.pack(">III",ENGINE_HASH,DONOR_HASH,0)
    field=get_field(vlt)
    ptr=find_ptr_record(vlt,field)
    if fixup_lookup(vlt).get(field,[])!=[(3,1,STOCK_ARRAY)]:
        raise ValueError("Original engine fixup differs from PRE494")
    gap=raw[BIN_START+BIN_SIZE:VLT_START]
    dest=(BIN_SIZE+15)//16*16
    refarray=struct.pack(">HHHH",2,2,12,0)+stock+newref
    if len(gap)!=49 or any(gap) or len(refarray)!=32 or BIN_START+dest+32>VLT_START:
        raise ValueError("No unoccupied original BIN/VLT padding")
    scratch=bytearray(raw) # RAM ONLY
    scratch[BIN_START+dest:BIN_START+dest+32]=refarray
    struct.pack_into("<I",scratch,20,dest+32)
    ptrabs=VLT_START+PTR_START+ptr+8
    struct.pack_into(">I",scratch,ptrabs,dest)
    _,length2,vl2,bo2,vo2=struct.unpack_from("<IIIII",scratch,16)
    if (length2,vl2,bo2,vo2)!=(dest+32,VLT_SIZE,BIN_START,VLT_START):
        raise ValueError("Scratch section header incorrect")
    rebuilt_bin=bytes(scratch[bo2:bo2+length2])
    rebuilt_vlt=bytes(scratch[vo2:vo2+vl2])
    new=array_candidate(rebuilt_bin,dest,{})
    if (not new["array_header_valid"] or new["capacity"]!=2 or
        new["item_count"]!=2 or
        [i["collection_hash"] for i in new["items"]]!=
         [f"{CAR_HASH:08x}",f"{DONOR_HASH:08x}"]):
        raise ValueError("Original BMW donor pairing failed array reparse")
    if fixup_lookup(rebuilt_vlt).get(field,[])!=[(3,1,dest)]:
        raise ValueError("New BMW donor RefSpec pointer no longer resolves")
    if rebuilt_bin[:BIN_SIZE]!=bin_data or len(scratch)!=len(raw):
        raise ValueError("User's original game data changed in source regions")
    pre=PTR_START+ptr+8
    if rebuilt_vlt[:pre]!=vlt[:pre] or rebuilt_vlt[pre+4:]!=vlt[pre+4:]:
        raise ValueError("Source VLT changed outside intended engine PtrN")
    allowed=set(range(20,24))
    allowed.update(range(BIN_START+dest,BIN_START+dest+32))
    allowed.update(range(ptrabs,ptrabs+4))
    changed=[i for i,(a,b) in enumerate(zip(raw,scratch)) if a!=b]
    if not changed or any(i not in allowed for i in changed):
        raise ValueError("Scratch modified unapproved bytes")
    diffs=[b-a for a,b in zip(bmw["samples"],donor["samples"])]
    higher=sum(v>1e-6 for v in diffs)
    lower=sum(v< -1e-6 for v in diffs)
    equal=len(diffs)-higher-lower
    return {"stage":"PRE495_PAL_BMW_ENGINE_SECOND_ORIGINAL_PROFILE_RAM_ONLY",
      "status":"AUDIT_OK","pal_vpak_sha256":EXPECTED_VPAK_SHA,
      "original_engine_collection":"bmwm3gtr",
      "candidate_second_engine_collection":DONOR,
      "first_collection_hash":f"{CAR_HASH:08x}",
      "second_collection_hash":f"{DONOR_HASH:08x}",
      "both_existing_original_engine_collections_resolved":True,
      "original_BMW_engine_ref_count":1,
      "scratch_engine_ref_count":2,
      "scratch_refspec_pointer_reparse_ok":True,
      "original_data_regions_unchanged":True,
      "scratch_total_resource_length_unchanged":True,
      "scratch_modified_regions_all_explicitly_whitelisted":True,
      "donor_is_original_careerstart_not_new_custom_upgrade":True,
      "stock_engine_layout_sha256":bmw["sha256"],
      "second_engine_layout_sha256":donor["sha256"],
      "original_torque_samples_stock":list(bmw["samples"]),
      "original_torque_samples_donor":list(donor["samples"]),
      "original_torque_sample_count":bmw["count"],
      "torque_samples_donor_above_stock":higher,
      "torque_samples_donor_below_stock":lower,
      "torque_samples_equal":equal,
      "donor_original_peak_torque":donor["max"],
      "stock_original_peak_torque":bmw["max"],
      "donor_is_uniformly_stronger_by_torque_samples":lower==0 and higher>0,
      "donor_candidate_valid_as_user_desired_power_upgrade_proven":False,
      "PAL_upgrade_interpolator_executed":False,
      "original_upgrade_counters_changed":False,
      "asset_bytes_emitted":False,"asset_files_written":False,
      "apk_built":False,"save_modified":False,"feature_enabled":False,
      "strict_ranges_read":reader.total}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True);a=ap.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:d=audit()
    except Exception as e:d={"stage":"PRE495_PAL_BMW_ENGINE_SECOND_ORIGINAL_PROFILE_RAM_ONLY",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
      "asset_files_written":False,"apk_built":False,
      "save_modified":False,"feature_enabled":False}
    d["run_id"]=a.run_id
    d["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
    print("PRE495_STATUS",d["status"])
    print("PRE495_TORQUE_DELTA",d.get("torque_samples_donor_above_stock"),d.get("torque_samples_donor_below_stock"))
    print("PRE495_ERROR",d.get("error_type","none"),d.get("error",""))
    return 0 if d["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
