#!/usr/bin/env python3
"""PRE494 synthetic duplicate-stock BMW ENGINE RefSpec relocation, RAM ONLY.

Input: SHA-pinned original user PAL/USA-identical VPAK from Drive.
Output: metadata JSON only. Never store or export modified game binary.
Second "upgrade" reference duplicates original stock, and is NOT real tuning.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
from datetime import datetime,timezone
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA,hash32
from pre474_bmw_punto_refs_readonly import array_candidate
from pre476_pal_performance_reference_resolution_readonly import collect_rows
from pre477_pal_bmw_punto_physics_layout_compare import fixup_lookup

OUT=Path("/tmp/nfsmw-pre494/report.json")
BIN_START,BIN_SIZE,VLT_START,VLT_SIZE=128,354959,355136,342720
STOCK_ARRAY=256660
PTR_START,PTR_SIZE=212848,129872
PV_CLASS=0x4A97EC8F
CAR_HASH=hash32("bmwm3gtr")
ENGINE_HASH=hash32("engine")
def sha(x):return hashlib.sha256(x).hexdigest()
def proof(path,field):
    d=json.loads(Path(path).read_text())
    if d.get("status")!="AUDIT_OK" or d.get(field)!=EXPECTED_VPAK_SHA:
        raise ValueError("Original PAL source proof missing: "+path)
    return d
def get_field(vlt):
    rows,_=collect_rows(vlt)
    records=rows.get((PV_CLASS,CAR_HASH),[])
    if len(records)!=1:raise ValueError("BMW pvehicle CollectionLoad not unique")
    r=records[0];at=r["record_offset_vlt"]
    _,cls,_,reserve,_,count,types,_=struct.unpack_from(">IIIIIIII",vlt,at)
    if cls!=PV_CLASS or reserve!=count or 32+4*types+12*count>r["record_size"]:
        raise ValueError("Original BMW collection metadata bounds changed")
    matches=[]
    for i in range(count):
        off=at+32+4*types+i*12
        key,value,typ,flags=struct.unpack_from(">IIHH",vlt,off)
        if key==ENGINE_HASH:matches.append((off,value,typ,flags))
    if len(matches)!=1 or matches[0][1]!=0xEFFECADD:
        raise ValueError("Original BMW engine RefSpec optional field missing")
    return matches[0][0]+4
def find_ptr_record(vlt,field_off):
    ptr=vlt[PTR_START:PTR_START+PTR_SIZE]
    if len(ptr)!=PTR_SIZE or ptr[:4]!=b"PtrN" or int.from_bytes(ptr[4:8],"big")!=PTR_SIZE:
        raise ValueError("Original PtrN chunk header invalid")
    section=None;matches=[]
    for rel in range(8,len(ptr),12):
        src,kind,index,dst=struct.unpack_from(">IHHI",ptr,rel)
        if kind==2:
            if index not in (0,1):raise ValueError("Unexpected PtrN switch")
            section=index
        elif kind in (1,3,4):
            if section is None:raise ValueError("Uninitialized PtrN section")
            if section==0 and src==field_off:matches.append((rel,kind,index,dst))
        elif kind!=0:raise ValueError("Unknown PtrN record")
    if len(matches)!=1 or matches[0][1:]!=(3,1,STOCK_ARRAY):
        raise ValueError("Original BMW engine array PtrN record not unique")
    return matches[0][0]
def audit():
    identity=proof("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json","pal_target_sha256")
    if not identity.get("pal_resource_identical_to_usa_reference"):
        raise ValueError("PAL/USA identity not proved")
    refs=proof("docs/PRE474_PAL_BMW_PUNTO_PERFORMANCE_REF_ARRAYS.json","vpak_sha256")
    caps=proof("docs/PRE492_PAL_BMW_REFSPEC_CAPACITY_RELOCATION_GATES.json","source_pal_vpak_sha256")
    old_entry=refs["vehicles"]["bmwm3gtr"]["categories_with_explicit_references"]["engine"]
    if (old_entry["item_count"]!=1 or old_entry["capacity"]!=1 or
        old_entry["bin_array_offset"]!=STOCK_ARRAY or
        old_entry["pvehicle_upgrade_limit"]!=0 or
        caps["original_arrays"]["bmwm3gtr"]["categories"]["engine"]["capacity"]!=1):
        raise ValueError("Original BMW engine array capacity proof changed")
    reader,location=locate()
    original=reader.read(location["absolute_offset"],location["size"])
    if len(original)!=697856 or sha(original)!=EXPECTED_VPAK_SHA:
        raise ValueError("Authenticated original game file SHA/length differs")
    _,bn,vn,bo,vo=struct.unpack_from("<IIIII",original,16)
    if (bn,vn,bo,vo)!=(BIN_SIZE,VLT_SIZE,BIN_START,VLT_START):
        raise ValueError("VPAK source geometry changed")
    rawbin=original[bo:bo+bn]
    rawvlt=original[vo:vo+vn]
    old=array_candidate(rawbin,STOCK_ARRAY,{})
    if not old["array_header_valid"] or old["capacity"]!=1 or old["item_count"]!=1:
        raise ValueError("Original engine array not valid")
    stockref=rawbin[STOCK_ARRAY+8:STOCK_ARRAY+20]
    if stockref!=struct.pack(">III",ENGINE_HASH,CAR_HASH,0):
        raise ValueError("Original engine RefSpec points outside intended stock car")
    field_ptr=get_field(rawvlt)
    if fixup_lookup(rawvlt).get(field_ptr,[])!=[(3,1,STOCK_ARRAY)]:
        raise ValueError("Original field fixup mismatch")
    record=find_ptr_record(rawvlt,field_ptr)
    padding=original[BIN_START+BIN_SIZE:VLT_START]
    if len(padding)!=49 or any(padding):
        raise ValueError("49-byte inter-vault gap not zero-filled")
    dest=(BIN_SIZE+15)//16*16
    synthetic_array=struct.pack(">HHHH",2,2,12,0)+stockref+stockref
    if len(synthetic_array)!=32 or BIN_START+dest+32>VLT_START:
        raise ValueError("Not enough BIN/VLT space for second reference")
    scratch=bytearray(original) # Never written to disk.
    scratch[BIN_START+dest:BIN_START+dest+32]=synthetic_array
    new_len=dest+32
    struct.pack_into("<I",scratch,20,new_len)
    pointer_abs=VLT_START+PTR_START+record+8
    struct.pack_into(">I",scratch,pointer_abs,dest)
    _,bn2,vn2,bo2,vo2=struct.unpack_from("<IIIII",scratch,16)
    if (bn2,vn2,bo2,vo2)!=(new_len,VLT_SIZE,BIN_START,VLT_START):
        raise ValueError("Scratch vault geometry failed reparse")
    newbin=bytes(scratch[bo2:bo2+bn2])
    newvlt=bytes(scratch[vo2:vo2+vn2])
    new=array_candidate(newbin,dest,{})
    if not new["array_header_valid"] or new["capacity"]!=2 or new["item_count"]!=2:
        raise ValueError("New two-reference header reparse failed")
    if (any(struct.pack(">III",int(item["class_hash"],16),
        int(item["collection_hash"],16),int(item["trailing_u32"],16))!=stockref
        for item in new["items"])):
        raise ValueError("Synthetic array did not retain duplicate stock refs")
    if fixup_lookup(newvlt).get(field_ptr,[])!=[(3,1,dest)]:
        raise ValueError("New PtrN fixup not independently resolved")
    if newbin[:BIN_SIZE]!=rawbin:
        raise ValueError("Original declared BIN changed unexpectedly")
    relative=PTR_START+record+8
    if newvlt[:relative]!=rawvlt[:relative] or newvlt[relative+4:]!=rawvlt[relative+4:]:
        raise ValueError("VLT modified outside one PtrN target")
    allowed=set(range(20,24))
    allowed.update(range(BIN_START+dest,BIN_START+dest+32))
    allowed.update(range(pointer_abs,pointer_abs+4))
    diffs=[i for i,(a,b) in enumerate(zip(original,scratch)) if a!=b]
    if not diffs or any(i not in allowed for i in diffs):
        raise ValueError("Unexpected scratch write outside safe spans")
    if len(scratch)!=len(original) or scratch[BIN_START+BIN_SIZE:BIN_START+dest]!=original[BIN_START+BIN_SIZE:BIN_START+dest]:
        raise ValueError("Scratch changed total file length or earlier padding")
    return {"stage":"PRE494_BMW_ENGINE_IN_MEMORY_REFSPEC_RELOCATION",
        "status":"AUDIT_OK","source_pal_vpak_sha256":EXPECTED_VPAK_SHA,
        "original_vpak_total_bytes":len(original),
        "original_bin_length":BIN_SIZE,"scratch_bin_length":new_len,
        "vlt_absolute_offset_unchanged":VLT_START,
        "original_zero_gap_bytes":len(padding),
        "remaining_gap_bytes":VLT_START-(BIN_START+new_len),
        "original_ref_count":1,"scratch_ref_count":2,
        "scratch_array_bin_offset":dest,
        "stock_bmw_engine_ref_unchanged":True,
        "scratch_second_ref_is_duplicate_stock":True,
        "scratch_bmw_power_increase_proven":False,
        "original_bin_and_other_vlt_exactly_preserved":True,
        "scratch_pointer_reparse_ok":True,
        "scratch_modified_bytes_within_whitelist_only":True,
        "scratch_changed_bytes_count":len(diffs),
        "pal_engine_loader_acceptance_tested":False,
        "modified_game_binary_written":False,
        "game_asset_published":False,"apk_built":False,
        "save_modified":False,"feature_enabled":False,
        "range_bytes_transferred":reader.total}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);opt=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as e:result={"stage":"PRE494_BMW_ENGINE_IN_MEMORY_REFSPEC_RELOCATION",
        "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
        "modified_game_binary_written":False,"game_asset_published":False,
        "apk_built":False,"save_modified":False,"feature_enabled":False}
    result["run_id"]=opt.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PRE494_STATUS",result["status"],flush=True)
    print("PRE494_PTR_REPARSE",result.get("scratch_pointer_reparse_ok",False),flush=True)
    print("PRE494_ERROR",result.get("error_type","none"),result.get("error",""),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
