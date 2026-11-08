#!/usr/bin/env python3
"""PRE468: decode 2339 Legacy AttribSys CollectionLoad headers in USA VLT.
Use authenticated original VPAK, 20-byte ExpN records verified by PRE466,
cross-check name hashes via StrE and Jenkins lookup2. No mutations or assets.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import hash32,get_names,chunks,EXPECTED_VPAK_SHA
from pre466_usa_vlt_exports_readonly import TYPE_IDS,EXPORT_OFFSET,EXPORT_CHUNK_SIZE,VLT_OFFSET,VLT_LEN

OUT=Path("/tmp/nfsmw-pre468/report.json")
KEYWORDS=("BMW","M3GTR","UPGRADE","SPECS","JUNKMAN","PART","TUNING","ENGINE","SUSPENSION")
EXACT=("BMWM3GTR","BMWM3GTRE46","m3gtre46careerstart","bmwm3gtr",
  "bmwm3gtre46","UpgradeSpecs","eFEPartUpgradeLevels","JunkmanMod")

def parse():
    reader,loc=locate()
    raw=reader.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:raise ValueError("PRE463 source SHA mismatch")
    _,binlen,vltlen,binoff,vltoff=struct.unpack_from("<IIIII",raw,16)
    if vltlen!=VLT_LEN or vltoff!=VLT_OFFSET:raise ValueError("PRE463 VLT section bounds changed")
    bin=raw[binoff:binoff+binlen];vlt=raw[vltoff:vltoff+vltlen]
    bin_chunks,_=chunks(bin,"BIN")
    names=get_names(bin,bin_chunks)
    hash_names=defaultdict(list)
    for name in names:
        if name not in hash_names[hash32(name)]:hash_names[hash32(name)].append(name)
    source=vlt[EXPORT_OFFSET:EXPORT_OFFSET+EXPORT_CHUNK_SIZE]
    if source[:4]!=b"ExpN" or int.from_bytes(source[4:8],"big")!=EXPORT_CHUNK_SIZE:
        raise ValueError("PRE466 export chunk mismatch")
    n=int.from_bytes(source[8:12],"big")
    if n!=2399:raise ValueError("PRE466 export count changed")
    rows=[];classes=[];sample_bmw=[];class_frequency=Counter()
    for i in range(n):
        id_,typ,reserved,size,ref=struct.unpack_from(">IIIII",vlt,EXPORT_OFFSET+12+20*i)
        if reserved or ref+size>len(vlt) or size<24:raise ValueError("Invalid legacy ExpN row")
        if typ==0x8E112EB7:
            if size<32:raise ValueError("Collection header truncated")
            key,cls,parent,table_reserve,unknown,num_entries,num_types,layout=struct.unpack_from(">IIIIIIII",vlt,ref)
            if num_entries>2048 or num_types>2048:raise ValueError("Unreasonable collection count")
            label=hash_names.get(key,[])
            clabel=hash_names.get(cls,[])
            plabel=hash_names.get(parent,[])
            item={"export_index":i,"record_offset":ref,"record_bytes":size,
                 "collection_hash":f"{key:08x}","collection_name_candidates":label[:3],
                 "class_hash":f"{cls:08x}","class_name_candidates":clabel[:3],
                 "parent_hash":f"{parent:08x}","parent_name_candidates":plabel[:3],
                 "num_optional_entries":num_entries,"num_types":num_types,
                 "reserve_matches_optional_count":table_reserve==num_entries,
                 "unknown_word_zero":unknown==0}
            rows.append(item)
            class_frequency[(clabel[0] if clabel else f"0x{cls:08x}")]+=1
        elif typ==0x5E970CBC:
            if size<28:raise ValueError("Class header truncated")
            classhash,reserve,defs,ptr,base,_zero,required=struct.unpack_from(">IIIIIIH",vlt,ref)
            classes.append({"class_hash":f"{classhash:08x}",
               "class_name_candidates":hash_names.get(classhash,[])[:3],
               "definitions":defs,"collection_reserve":reserve,
               "required_count":required,"definitions_pointer_raw":f"{ptr:08x}",
               "record_offset":ref})
        elif typ!=0xCBBC628F:
            raise ValueError("Unexpected export kind "+hex(typ))
    if len(rows)!=2339 or len(classes)!=59:raise ValueError("PRE466 export type counts changed")
    target_hashes={s:hash32(s) for s in EXACT}
    target_rows={}
    for name,h in target_hashes.items():
        target_rows[name]=[r for r in rows if r["collection_hash"]==f"{h:08x}"
                                      or r["class_hash"]==f"{h:08x}"][:120]
    target_clues=[r for r in rows if
        any(k in n.upper() for n in r["collection_name_candidates"]
            for k in KEYWORDS) or
        any(k in n.upper() for n in r["class_name_candidates"]
            for k in ("UPGRADE","JUNKMAN","PART"))]
    reserve_matches=sum(r["reserve_matches_optional_count"] for r in rows)
    null_parent=sum(r["parent_hash"]=="00000000" for r in rows)
    known_key=sum(bool(r["collection_name_candidates"]) for r in rows)
    known_class=sum(bool(r["class_name_candidates"]) for r in rows)
    return {"stage":"PRE468_USA_BMW_LEGACY_COLLECTION_HEADERS_READONLY",
      "status":"AUDIT_OK",
      "source_vpak_sha256":EXPECTED_VPAK_SHA,"edition":"USA only, PAL not proven equivalent",
      "recovered_collection_count":len(rows),"recovered_class_count":len(classes),
      "collection_name_hashes_resolved_to_StrE":known_key,
      "class_name_hashes_resolved_to_StrE":known_class,
      "collection_reserve_counts_consistent":reserve_matches,
      "collection_null_parent_count":null_parent,
      "total_known_unique_strings":len(set(names)),
      "top_class_names":class_frequency.most_common(65),
      "named_class_headers":classes[:59],
      "target_hashes":{k:f"{v:08x}" for k,v in target_hashes.items()},
      "target_rows":target_rows,
      "tuning_and_bmw_name_candidate_rows":target_clues[:150],
      "target_rows_are_unresolved_raw_headers_not_installed_parts":True,
      "performance_mod_ready":False,
      "source_assets_exported":False,"save_modified":False,
      "signed_apk_built":False,"transferred_range_bytes":reader.total}

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=parse()
    except Exception as e:r={"stage":"PRE468_USA_BMW_LEGACY_COLLECTION_HEADERS_READONLY",
     "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:220],
     "source_assets_exported":False,"save_modified":False,"signed_apk_built":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE468_STATUS",r["status"],flush=True)
    print("PRE468_COLLECTIONS",r.get("recovered_collection_count"),flush=True)
    print("PRE468_TARGET_COUNTS",{k:len(v) for k,v in r.get("target_rows",{}).items()},flush=True)
    print("PRE468_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
