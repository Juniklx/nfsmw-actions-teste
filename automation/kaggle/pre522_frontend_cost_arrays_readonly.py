#!/usr/bin/env python3
"""PRE522: recover typed FECarPartInfo purchase levels/costs from authentic USA FE vault.

Uses signed Level + float Rep + float Cost (12 bytes), per the public
original source FEReflected.hpp, and matches frontend.class carparts descendants
using the exact VLT CollectionLoad/AttribEntry and PtrN records. Fail closed
for unsupported pointer semantics; never fabricate costs or modify a save.
Does not yet prove the PAL frontend resource is identical or runtime prices.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,math,re
from datetime import datetime,timezone
from pathlib import Path
from collections import Counter
from pre462_usa_raw_iso_attributes_readonly import Reader,PARTITION_BASE,EXPECTED_NFS_SECTOR,SECTOR,dir_entries,NAMES
from pre465_usa_bmw_vpak_inner_schema_readonly import chunks,get_names,hash32
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
from pre502_bmw_engine_combined_level1_scratch import lookup_ptrn
OUT=Path("/tmp/nfsmw-pre522/report.json")
FE_SHA="8ac09099cfc98646bbfbdb261d28b9648e3ec8b0d6bdf9d3edd6ef7bc967b528"
RESOURCE="GLOBAL\\FE_ATTRIB.BIN"
RES_HASH=NAMES[RESOURCE]
BASE_SIZE=113856
CLASS=0x85885722
COL_KIND=0x8E112EB7
CARPARTS=hash32("carparts")
KEY_INFO=hash32("feCarPartInfo")
KEY_NAME=hash32("feCarPartName")
KEY_COST=hash32("Cost")
ENUM={4:"tires",5:"brakes",6:"chassis",7:"transmission",8:"engine",9:"induction",10:"nos"}
EXPECTED_BROKEN_OR_UNKNOWN_FIELD_NAMES_ALLOWED=True
REF_SOURCE="dbalatoni13/nfsmw@80993f35224c61d2f1b135beba76c6f8234c7940/FEReflected.hpp"

def read_original():
    reader=Reader()
    tree=reader.read(PARTITION_BASE+EXPECTED_NFS_SECTOR*SECTOR,2048)
    entries={x["name"].upper():x for x in dir_entries(tree)}
    index=entries["ZDIR.BIN"]
    archive=entries["ZZDATA0.BIN"]
    raw=reader.read(PARTITION_BASE+index["sector"]*SECTOR,index["size"])
    matches=[(i,arc,sec,tot,size,crc) for i,(h,arc,sec,tot,size,crc)
             in enumerate(struct.iter_unpack("<IiIIiI",raw)) if h==RES_HASH]
    if len(matches)!=1:raise ValueError("Original USA FE resource ZDIR row ambiguous")
    i,arc,sec,tot,size,crc=matches[0]
    if (arc,sec*SECTOR,size)!=(0,162392064,BASE_SIZE) or sec*SECTOR+size>archive["size"]:
        raise ValueError("USA FE resource original archive location invalid")
    blob=reader.read(PARTITION_BASE+archive["sector"]*SECTOR+sec*SECTOR,size)
    if hashlib.sha256(blob).hexdigest()!=FE_SHA or ea_data_hash(blob)!=crc:
        raise ValueError("USA FE original resource checksum or pinned SHA changed")
    return blob,reader.total

def audit():
    prior=json.loads(Path("docs/PRE521_USA_FE_ATTRIB_FRONTEND_CARPARTS_STRUCTURE_READONLY.json").read_text())
    if (prior.get("status")!="AUDIT_OK" or
        prior.get("source_sha256")!=FE_SHA or
        prior.get("source_bytes")!=BASE_SIZE or
        prior.get("original_frontend_collection_count")!=414 or
        prior.get("original_carparts_direct_children_count")!=21 or
        prior.get("guest_LOADER_and_shop_cost_runtime_confirmed") is not False):
        raise ValueError("PRE521 source/frontend inventory proof missing")
    data,transferred=read_original()
    n,sbase,slen=struct.unpack_from("<III",data,4)
    if n!=1:raise ValueError("Unexpected frontend VPAK vault count")
    _name,binlen,vltlen,binoff,vltoff=struct.unpack_from("<IIIII",data,16)
    BIN=data[binoff:binoff+binlen]
    VLT=data[vltoff:vltoff+vltlen]
    if binlen!=53071 or vltlen!=60576:
        raise ValueError("Source FE vault section lengths changed")
    vchunks,rem=chunks(VLT,"FE VLT")
    bchunks,brem=chunks(BIN,"FE BIN")
    exp=next(x for x in vchunks if x["tag"]=="ExpN")
    ptr=next(x for x in vchunks if x["tag"]=="PtrN")
    start=exp["relative_offset"]
    ct=struct.unpack_from(">I",VLT,start+8)[0]
    if ct!=414 or [x["tag"] for x in vchunks]!=["DepN","StrN","DatN","ExpN","PtrN"]:
        raise ValueError("Source FE VLT section sequence changed")
    ptr_offsets=lookup_ptrn(VLT,ptr["relative_offset"],ptr["declared_size"])
    strings=get_names(BIN,bchunks)
    labels={hash32(x):x for x in strings}
    fields_count=Counter()
    all_children=[]
    for j in range(ct):
        expid,kind,unused,sz,pos=struct.unpack_from(">IIIII",VLT,start+12+j*20)
        if kind!=COL_KIND or unused!=0:raise ValueError("Unknown FE VLT export type")
        if not (32<=sz<=1024 and pos+sz<=start):
            raise ValueError("Malformed frontend CollectionLoad span")
        key,cl,parent,reserve,unk,nent,ntypes,base=struct.unpack_from(">IIIIIIII",VLT,pos)
        if cl!=CLASS or reserve!=nent or nent>100 or ntypes>100 or 32+4*ntypes+12*nent>sz:
            raise ValueError("Malformed frontend optional attribute header")
        if parent!=CARPARTS:continue
        types=[struct.unpack_from(">I",VLT,pos+32+4*t)[0] for t in range(ntypes)]
        fields={}
        for k in range(nent):
            src=pos+32+4*ntypes+12*k
            h,val,tix,flag=struct.unpack_from(">IIHH",VLT,src)
            if tix>=ntypes:raise ValueError("Invalid frontend optional type index")
            fields_count[f"{h:08x}"]+=1
            fields[h]={"keyhash":f"{h:08x}","source_offset":src,"raw_value":val,
                       "typehash":f"{types[tix]:08x}","flags":flag,
                       "pointer_fixups":ptr_offsets.get(src+4,[])}
        info=fields.get(KEY_INFO)
        name=fields.get(KEY_NAME)
        results=[]
        candidate_header=[]
        if info:
            for kind,section,offset in info["pointer_fixups"]:
                if kind!=3:continue
                blob=BIN if section==1 else VLT if section==0 else None
                if blob is None or offset<0 or offset+8>len(blob):continue
                cap,num,elem,flag=struct.unpack_from(">HHHH",blob,offset)
                plausible=0<cap<=60 and num<=cap and elem==12 and offset+8+12*cap<=len(blob)
                candidate_header.append({"section":section,"offset":offset,"capacity":cap,
                    "count":num,"elem_bytes":elem,"header_flags":flag,"bounds_valid":plausible})
                if not plausible:continue
                rows=[]
                for k in range(num):
                    level,rep,cost=struct.unpack_from(">iff",blob,offset+8+12*k)
                    if level not in range(-1,8) or not math.isfinite(rep) or not math.isfinite(cost):
                        plausible=False;break
                    if cost<0 or cost>1e8 or rep<0 or rep>1e8:
                        plausible=False;break
                    rows.append({"level":level,"rep":round(rep,5),"cost":round(cost,5)})
                if plausible and len({row["level"] for row in rows})==len(rows):
                    results.append({"section":section,"offset":offset,"array_elements":rows,
                                    "array_count":num,"all_costs_nonnegative":True})
        # The field may be in the base or optional storage, hence a value
        # outside enum is treated as unproven, never "corrected".
        raw_cat=name["raw_value"] if name else None
        cat=ENUM.get(raw_cat)
        all_children.append({
            "collection_hash":f"{key:08x}",
            "collection_name":labels.get(key),
            "parent_is_carparts":True,
            "optional_field_count":nent,
            "feCarPartName_optional_field_present":name is not None,
            "feCarPartName_raw_value":raw_cat,
            "FE_purchase_category":cat,
            "feCarPartInfo_optional_field_present":info is not None,
            "feCarPartInfo_pointer_candidates":candidate_header[:5],
            "validated_FECarPartInfo_arrays":results[:3],
            "known_requested_field_hashes":{
                "feCarPartName":f"{KEY_NAME:08x}",
                "feCarPartInfo":f"{KEY_INFO:08x}"
            }
        })
    if len(all_children)!=21:raise ValueError("Original 21 direct carparts descendants changed")
    usable=[x for x in all_children if x["validated_FECarPartInfo_arrays"]]
    mapped=[x for x in all_children if x["FE_purchase_category"]]
    return {
        "stage":"PRE522_ORIGINAL_USA_FECarPartInfo_ARRAY_AND_COST_ENUM_READONLY",
        "status":"AUDIT_OK",
        "original_FE_ATTRIB_sha256":FE_SHA,
        "source_PC_generated_layout_reference":REF_SOURCE,
        "frontend_class_hash":"85885722",
        "carparts_hash":f"{CARPARTS:08x}",
        "feCarPartInfo_field_hash":f"{KEY_INFO:08x}",
        "feCarPartName_field_hash":f"{KEY_NAME:08x}",
        "original_carparts_children_examined":len(all_children),
        "optional_key_occurrences":dict(fields_count),
        "children_with_category_enum_decoded":len(mapped),
        "children_with_valid_FECarPartInfo_array":len(usable),
        "per_collection_reference_and_typed_metadata":all_children,
        "actual_original_USA_prices_decoded":len(usable)>0,
        "original_PAL_FE_ATTRIB_binary_identity_verified":False,
        "actual_BMW_shop_cost_or_purchase_verified":False,
        "original_loader_acceptance_verified":False,
        "original_game_bytes_written_or_published":False,
        "APK_built":False,"save_modified":False,"signing_material_accessed":False,
        "BMW_tuning_enabled":False,
        "iso_bytes_transferred":transferred
    }

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run-id",required=True)
    args=parser.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as exc:
        r={"stage":"PRE522_ORIGINAL_USA_FECarPartInfo_ARRAY_AND_COST_ENUM_READONLY",
           "status":"FAILED","error_type":type(exc).__name__,"error":str(exc)[:230],
           "original_game_bytes_written_or_published":False,"APK_built":False,
           "save_modified":False,"signing_material_accessed":False,"BMW_tuning_enabled":False}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE522_STATUS",r["status"],flush=True)
    print("PRE522_CATEGORIES",r.get("children_with_category_enum_decoded"),flush=True)
    print("PRE522_COST_ARRAYS",r.get("children_with_valid_FECarPartInfo_array"),flush=True)
    print("PRE522_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
