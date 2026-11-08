#!/usr/bin/env python3
"""PRE471: validate PAL-identical VPAK PtrN pointer fixups and BMW UpgradeSpecs.
Read-only schema research. No applying pointer fixups to any game source,
no creating modified VPAK, no APK, no save mutation or publishing assets.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA

OUT=Path("/tmp/nfsmw-pre471/report.json")
PRE470=Path("docs/PRE470_PAL_BMW_OPTIONAL_FIELDS_COMPARISON_READONLY.json")
PRE467=Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json")
PTR_OFFSET=212848;PTR_SIZE=129872;VLT_OFF=355136;VLT_LEN=342720
def parse_raw():
    a=json.loads(PRE467.read_text())
    b=json.loads(PRE470.read_text())
    if a.get("status")!="AUDIT_OK" or not a.get("pal_resource_identical_to_usa_reference"):
        raise ValueError("PAL identity proof failed")
    if b.get("status")!="AUDIT_OK" or b.get("pal_vpak_sha256")!=EXPECTED_VPAK_SHA:
        raise ValueError("PRE470 source unavailable")
    reader,loc=locate()
    raw=reader.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:
        raise ValueError("VPAK SHA mismatch")
    _,binsize,vsize,binoff,vltoff=struct.unpack_from("<IIIII",raw,16)
    if vsize!=VLT_LEN or vltoff!=VLT_OFF:raise ValueError("VLT source bounds differ")
    bin=raw[binoff:binoff+binsize]
    vlt=raw[vltoff:vltoff+vsize]
    block=vlt[PTR_OFFSET:PTR_OFFSET+PTR_SIZE]
    if block[:4]!=b"PtrN" or int.from_bytes(block[4:8],"big")!=PTR_SIZE:
        raise ValueError("PRE465 PtrN chunk mismatch")
    if (len(block)-8)%12:raise ValueError("Pointer record count not integral")
    return reader,b,bin,vlt,block

def parse_type_layout(block,endian):
    counter=Counter()
    suspicious=0;switches=0
    for i in range(8,len(block),12):
        typ=int.from_bytes(block[i+4:i+6],endian)
        idx=int.from_bytes(block[i+6:i+8],endian)
        counter[typ]+=1
        if typ>4:suspicious+=1
        if typ==2 and idx<=1:switches+=1
    return {"endian":endian,"invalid_ptr_types":suspicious,"valid_target_switches":switches,
            "types":dict(counter)}

def audit():
    reader,old,bin,vlt,block=parse_raw()
    candidates=[parse_type_layout(block,x) for x in ("big","little")]
    winner=[x for x in candidates if x["invalid_ptr_types"]==0 and x["valid_target_switches"]>=2]
    if len(winner)!=1:
        raise ValueError("Cannot select safe PtrN 16-bit field byte order")
    endian=winner[0]["endian"]
    allstats=Counter();fixups={};mode=None;invalid_bounds=0
    for i in range(8,len(block),12):
        off=int.from_bytes(block[i:i+4],"big")
        typ=int.from_bytes(block[i+4:i+6],endian)
        index=int.from_bytes(block[i+6:i+8],endian)
        dest=int.from_bytes(block[i+8:i+12],"big")
        allstats[typ]+=1
        if typ==2:
            if index not in (0,1):raise ValueError("Unknown target pointer switch")
            mode="VLT" if index==0 else "BIN"
        elif typ in (1,3,4):
            if mode not in ("VLT","BIN"):raise ValueError("Fixup record before target mode")
            current_len=len(vlt) if mode=="VLT" else len(bin)
            if off+4>current_len:invalid_bounds+=1
            if typ==3 and dest>current_len:invalid_bounds+=1
            if mode=="VLT" and typ in (1,3,4):
                if off in fixups:raise ValueError("Duplicate VLT fixup")
                fixups[off]={"ptr_type":typ,"ptr_index":index,
                             "target_section":mode,"target_offset":dest,
                             "fixup_offset":off}
        elif typ==0:
            pass
        else:raise ValueError("Unexpected pointer kind")
    wanted=[]
    for car,data in old["bmw_variant_optional_fields"].items():
        for field in data["optional_fields"]:
            if field["type_hash"]!="5fde6463":continue
            off=field["vlt_offset"]+4
            mapping=fixups.get(off)
            wanted.append({"car":car,"field_hash":field["field_hash"],
                           "optional_field_value_offset":off,
                           "value_raw_u32":field["data_u32_raw"],
                           "flags_u16_from_PRE470":field["node_flags"],
                           "ptr_fixup":mapping,
                           "has_vlt_fixup":mapping is not None})
    return {"stage":"PRE471_PAL_VERIFIED_UPGRADESPECS_POINTER_FIXUPS_READONLY",
      "status":"AUDIT_OK","source_vpak_sha256":EXPECTED_VPAK_SHA,
      "pal_equals_usa_source_verified":True,
      "ptrn_size":PTR_SIZE,"total_pointer_records":(len(block)-8)//12,
      "u16_endian_candidates":candidates,"selected_u16_endian":endian,
      "type_counts":dict(allstats),"invalid_fixed_pointer_bounds":invalid_bounds,
      "vlt_fixup_count":len(fixups),
      "bmw_upgrade_field_pointer_lookup":wanted,
      "all_four_bmw_upgrade_fields_have_fixups":len(wanted)==4 and all(x["has_vlt_fixup"] for x in wanted),
      "resolved_pointer_is_not_installed_upgrade":True,
      "bmw_part_ids_verified":False,"safe_to_enable_mod":False,
      "game_assets_exported":False,"apk_built":False,"save_modified":False,
      "bytes_transferred":reader.total}

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE471_PAL_VERIFIED_UPGRADESPECS_POINTER_FIXUPS_READONLY",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
      "game_assets_exported":False,"apk_built":False,"save_modified":False}
    r["utc"]=datetime.now(timezone.utc).isoformat();r["run_id"]=a.run_id
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE471_STATUS",r["status"],flush=True)
    print("PRE471_FIXED",r.get("vlt_fixup_count"),"BMW_PTRS",r.get("bmw_upgrade_field_pointer_lookup"),flush=True)
    print("PRE471_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
