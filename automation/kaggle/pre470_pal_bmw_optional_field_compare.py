#!/usr/bin/env python3
"""PRE470: decode optional AttribEntry header keys for BMW variants from
PAL-confirmed VPAK (USA byte-identical). Compare against VaultLib Legacy format.
No guessed value types, no part insertion, no game/save modification.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import hash32,EXPECTED_VPAK_SHA
from pre466_usa_vlt_exports_readonly import EXPORT_OFFSET,EXPORT_CHUNK_SIZE,VLT_OFFSET,VLT_LEN

OUT=Path("/tmp/nfsmw-pre470/report.json")
CLASS_OF_INTEREST="4a97ec8f"
VARIANTS=("bmwm3gtr","m3gtre46careerstart")
KEY_NAMES=("UpgradeSpecs","eFEPartUpgradeLevels","JunkmanMod")
PRE468=Path("docs/PRE468_USA_BMW_VLT_COLLECTION_RELATIONSHIPS_READONLY.json")
PRE467=Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json")
def get_source():
    u=json.loads(PRE467.read_text())
    if u.get("status")!="AUDIT_OK" or not u.get("pal_resource_identical_to_usa_reference"):
        raise ValueError("PRE467 PAL byte identity proof unavailable")
    a=json.loads(PRE468.read_text())
    if a.get("status")!="AUDIT_OK" or a.get("source_vpak_sha256")!=EXPECTED_VPAK_SHA:
        raise ValueError("PRE468 collection source proof unavailable")
    reader,loc=locate()
    raw=reader.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:
        raise ValueError("VPAK SHA mismatch")
    _,binlen,vltlen,binoff,vltoff=struct.unpack_from("<IIIII",raw,16)
    if vltlen!=VLT_LEN or vltoff!=VLT_OFFSET:raise ValueError("VLT bounds changed")
    bin=raw[binoff:binoff+binlen]
    vlt=raw[vltoff:vltoff+vltlen]
    strings={}
    for m in re.finditer(rb"[A-Za-z_][A-Za-z0-9_./\\:\-]{2,110}\x00",bin):
        s=m.group()[:-1].decode("ascii","replace")
        h=hash32(s)
        if h not in strings:strings[h]=s
    return reader,a,vlt,strings

def optional_fields(vlt,ref,size):
    if ref<0 or ref+size>len(vlt) or size<32:raise ValueError("Collection span invalid")
    key,cls,parent,reserve,unknown,nent,ntypes,layout=struct.unpack_from(">IIIIIIII",vlt,ref)
    minsize=32+ntypes*4+nent*12
    if reserve!=nent or ntypes>200 or nent>200 or minsize>size:
        raise ValueError("Collection AttribEntry layout invalid")
    trailing=vlt[ref+minsize:ref+size]
    types=[struct.unpack_from(">I",vlt,ref+32+4*i)[0] for i in range(ntypes)]
    entries=[]
    for j in range(nent):
        off=ref+32+ntypes*4+j*12
        fkey,value,type_index,flags=struct.unpack_from(">IIHH",vlt,off)
        entries.append({"field_hash":f"{fkey:08x}","data_u32_raw":f"{value:08x}",
           "type_index":type_index,"type_hash":f"{types[type_index]:08x}" if type_index<ntypes else None,
           "node_flags":f"{flags:04x}","type_index_valid":type_index<ntypes,
           "vlt_offset":off})
    return {"collection_hash":f"{key:08x}","class_hash":f"{cls:08x}",
      "parent_hash":f"{parent:08x}","num_entries":nent,"num_types":ntypes,
      "record_bytes":size,"minimum_record_bytes":minsize,
      "trailing_bytes":len(trailing),"trailing_all_zero":not any(trailing),
      "optional_fields":entries}

def audit():
    reader,old,vlt,strings=get_source()
    findings={}
    per_type=Counter();flags=Counter();bad=0;count=0
    for i in range(2399):
        export_id,typ,reserve,size,ref=struct.unpack_from(">IIIII",vlt,EXPORT_OFFSET+12+i*20)
        if reserve:raise ValueError("Export reserved nonzero")
        if typ!=0x8E112EB7:continue
        row=optional_fields(vlt,ref,size)
        count+=1
        for field in row["optional_fields"]:
            h=int(field["field_hash"],16)
            per_type[h]+=1
            flags[field["node_flags"]]+=1
            if not field["type_index_valid"]:bad+=1
    for name in VARIANTS:
        matches=[r for r in old["target_rows"][name] if r["class_hash"]==CLASS_OF_INTEREST]
        if len(matches)!=1:raise ValueError("Unique target class/variant record expected "+name)
        r=matches[0]
        val=optional_fields(vlt,r["record_offset"],r["record_bytes"])
        if val["collection_hash"]!=r["collection_hash"] or val["class_hash"]!=CLASS_OF_INTEREST:
            raise ValueError("Target row changed from PRE468 "+name)
        for field in val["optional_fields"]:
            field["full_BIN_field_name_candidate"]=strings.get(int(field["field_hash"],16))
        findings[name]=val
    by_variant={name:{f["field_hash"]:f for f in x["optional_fields"]} for name,x in findings.items()}
    left,right=(by_variant[v] for v in VARIANTS)
    shared=sorted(left.keys() & right.keys())
    only_left=sorted(left.keys()-right.keys())
    only_right=sorted(right.keys()-left.keys())
    differences=[{"field_hash":h,"field_name":left[h]["full_BIN_field_name_candidate"],
      "bmw_raw":left[h]["data_u32_raw"],"career_raw":right[h]["data_u32_raw"],
      "bmw_type":left[h]["type_hash"],"career_type":right[h]["type_hash"]}
      for h in shared if left[h]["data_u32_raw"]!=right[h]["data_u32_raw"]]
    interesting={n:{"field_hash":f"{hash32(n):08x}",
      "occurrence_in_optional_key_entries":per_type[hash32(n)],
      "present_in_bmw_target":f"{hash32(n):08x}" in left,
      "present_in_careerstart_target":f"{hash32(n):08x}" in right} for n in KEY_NAMES}
    return {"stage":"PRE470_PAL_VERIFIED_BMW_OPTIONAL_FIELDS_READONLY",
      "status":"AUDIT_OK","pal_vpak_sha256":EXPECTED_VPAK_SHA,
      "pal_and_usa_proven_identical_in_PRE467":True,
      "collection_headers_checked":count,"optional_entries_type_index_invalid":bad,
      "optional_fields_total":sum(per_type.values()),
      "node_flag_histogram":dict(flags),
      "named_field_key_histogram":[{"key":f"{k:08x}",
           "name":strings.get(k),"count":n}
            for k,n in per_type.most_common(90)],
      "bmw_variant_class":CLASS_OF_INTEREST,
      "bmw_variant_optional_fields":findings,
      "shared_optional_field_count":len(shared),
      "shared_raw_values_differ":differences,
      "only_bmwm3gtr_field_hashes":only_left,
      "only_careerstart_field_hashes":only_right,
      "known_upgrade_key_presence":interesting,
      "raw_values_are_not_typed_or_resolved":True,
      "valid_bmw_part_ids_proven":False,"safe_to_apply_tuning":False,
      "game_assets_published":False,"apk_built":False,
      "save_modified":False,"ranged_bytes":reader.total}

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE470_PAL_VERIFIED_BMW_OPTIONAL_FIELDS_READONLY",
     "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
     "game_assets_published":False,"apk_built":False,"save_modified":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE470_STATUS",r["status"])
    print("PRE470_OPTIONAL_CHECKED",r.get("optional_fields_total"),flush=True)
    print("PRE470_BMW_KNOWN_UPGRADE",r.get("known_upgrade_key_presence"),flush=True)
    print("PRE470_BMW_DIFFS",r.get("shared_raw_values_differ"),flush=True)
    print("PRE470_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
