#!/usr/bin/env python3
"""PRE466: diagnostic decoding of USA ExpN export index, no data patching.
Compare Xbox-big-endian 16 vs 20-byte structures to historical VaultLib;
validate actual record bounds before interpreting refs or class names.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import hash32,EXPECTED_VPAK_SHA

OUT=Path("/tmp/nfsmw-pre466/report.json")
EXPORT_OFFSET=164848
EXPORT_CHUNK_SIZE=48000
VLT_OFFSET=355136
VLT_LEN=342720
TYPE_IDS={0x5E970CBC:"ClassLoadData",0xCBBC628F:"DatabaseLoadData",0x8E112EB7:"CollectionLoadData"}
NAMES=("BMWM3GTR","BMWM3GTRE46","m3gtre46careerstart","UpgradeSpecs",
       "eFEPartUpgradeLevels","JunkmanMod")
def load():
    reader, loc=locate()
    raw=reader.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:raise ValueError("PRE463 SHA mismatch")
    return reader,raw[VLT_OFFSET:VLT_OFFSET+VLT_LEN]

def evaluate(blob,count,stride):
    payload_start=EXPORT_OFFSET+12
    available=EXPORT_CHUNK_SIZE-12
    if count<=0 or count>5000 or count*stride>available:
        return {"stride_bytes":stride,"possible":False,"reason":"count_overflow"}
    trailing=blob[payload_start+count*stride:EXPORT_OFFSET+EXPORT_CHUNK_SIZE]
    if len(trailing)>16 or any(trailing):
        return {"stride_bytes":stride,"possible":False,
                "reason":"nonzero_or_large_padding","padding_len":len(trailing)}
    rows=[];types=Counter();zeros=0;valid=0
    for i in range(count):
        off=payload_start+i*stride
        vals=struct.unpack_from(">"+"I"*(stride//4),blob,off)
        if stride==16:
            id_,typ,size,ref=vals
            reserved_ok=True
        else:
            id_,typ,reserved,size,ref=vals
            reserved_ok=reserved==0
        plausible=(ref+size<=len(blob) and size<=len(blob) and reserved_ok)
        if plausible:valid+=1
        if stride==20 and not reserved_ok:zeros+=1
        types[f"{typ:08x}"]+=1
        if i<12 or id_ in (hash32(x) for x in NAMES):
            if len(rows)<90:
                rows.append({"index":i,"id_hash":f"{id_:08x}",
                             "type_hash":f"{typ:08x}","known_type":TYPE_IDS.get(typ),
                             "size":size,"vlt_offset":ref,"bounds_valid":plausible,
                             "reserved_zero":reserved_ok})
    seen={x:[] for x in NAMES}
    for row in rows:
        for name in NAMES:
            if row["id_hash"]==f"{hash32(name):08x}":seen[name].append(row)
    return {"stride_bytes":stride,"possible":True,
            "reported_count":count,"padding_len":len(trailing),
            "all_entries_within_vlt_and_reserved_ok":valid==count,
            "valid_entry_count":valid,"reserved_violations":zeros,
            "type_hash_histogram":dict(types),
            "sample_and_named_rows":rows,
            "matched_named_export_rows":seen}

def audit():
    reader,vlt=load()
    chunk=vlt[EXPORT_OFFSET:EXPORT_OFFSET+EXPORT_CHUNK_SIZE]
    if chunk[:4]!=b"ExpN" or int.from_bytes(chunk[4:8],"big")!=EXPORT_CHUNK_SIZE:
        raise ValueError("PRE465 export chunk moved")
    head=[int.from_bytes(chunk[i:i+4],"big") for i in range(8,min(68,len(chunk)),4)]
    n=int.from_bytes(chunk[8:12],"big")
    candidates=[evaluate(vlt,n,s) for s in (16,20)]
    return {
      "stage":"PRE466_USA_VLT_EXPN_EXPORT_SCHEMA_READONLY","status":"AUDIT_OK",
      "edition":"USA reference only (not authenticated PAL runtime)",
      "vpak_sha256":EXPECTED_VPAK_SHA,"chunk_tag":"ExpN",
      "chunk_offset":EXPORT_OFFSET,"chunk_bytes":EXPORT_CHUNK_SIZE,
      "declared_export_count":n,"first_15_payload_u32_be":head,
      "entry_layout_candidates":candidates,
      "schema_confirmed":sum(c["possible"] and c.get("all_entries_within_vlt_and_reserved_ok",False) for c in candidates)==1,
      "matching_export_does_not_prove_upgrade_application":True,
      "bmw_upgrade_purchase_safe":False,
      "game_assets_exported":False,"apk_built":False,"save_modified":False,
      "range_bytes":reader.total
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE466_USA_VLT_EXPN_EXPORT_SCHEMA_READONLY",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
      "game_assets_exported":False,"apk_built":False,"save_modified":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE466_STATUS",r["status"],flush=True)
    print("PRE466_EXPORT_COUNT",r.get("declared_export_count","?"),flush=True)
    print("PRE466_CANDIDATES",[(x["stride_bytes"],x["possible"],x.get("valid_entry_count")) for x in r.get("entry_layout_candidates",[])],flush=True)
    print("PRE466_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
