#!/usr/bin/env python3
"""PRE472: infer/read real UpgradeSpecs array headers at BMW pointers.
PAL ATTRIBUTES.BIN authenticated byte-for-byte in PRE467.
No source edits, no gameplay, no APK/save operations, and no asset bytes export.
Source layout informed by VaultLib UpgradeSpecs (RefSpec + level) and VLTArrayType.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA,hash32

OUT=Path("/tmp/nfsmw-pre472/report.json")
SOURCE_REPORT=Path("docs/PRE471_BMW_PAL_UPGRADESPECS_PTRN_READONLY.json")
PRE467=Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json")
def evaluate(blob,off,section,endian,hash_names):
    if off<0 or off+8>len(blob):return None
    cap,count,sz,flag=struct.unpack_from(("<" if endian=="little" else ">")+"HHHH",blob,off)
    plausible=0<cap<=128 and count<=cap and sz==16 and off+8+16*cap<=len(blob)
    x={"section":section,"header_endian":endian,"capacity":cap,
       "actual_count":count,"element_bytes":sz,
       "unknown_flags":f"{flag:04x}","array_bounds_valid":plausible}
    if not plausible:return x
    items=[]
    for i in range(min(count,20)):
        a,b,zero,level=struct.unpack_from(">IIII",blob,off+8+i*16)
        items.append({"item_index":i,"reference_class_hash":f"{a:08x}",
          "reference_class_name_candidates":hash_names.get(a,[])[:3],
          "reference_collection_hash":f"{b:08x}",
          "reference_collection_name_candidates":hash_names.get(b,[])[:3],
          "reference_opaque_u32":f"{zero:08x}","upgrade_level_raw":level})
    x["items"]=items
    x["all_recorded_items_read"]=count<=20
    return x

def audit():
    proof=json.loads(PRE467.read_text())
    links=json.loads(SOURCE_REPORT.read_text())
    if not proof.get("pal_resource_identical_to_usa_reference") or links.get("status")!="AUDIT_OK":
        raise ValueError("PAL identity/PtrN source proof absent")
    reader,loc=locate()
    raw=reader.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:raise ValueError("Source fingerprint mismatch")
    _,binlen,vltlen,binoff,vltoff=struct.unpack_from("<IIIII",raw,16)
    BIN=raw[binoff:binoff+binlen];VLT=raw[vltoff:vltoff+vltlen]
    words=[]
    import re
    for m in re.finditer(rb"[A-Za-z_][A-Za-z0-9_./\\:\-]{2,110}\x00",BIN):
        words.append(m.group()[:-1].decode("ascii","replace"))
    names=defaultdict(list)
    for word in words:
        h=hash32(word)
        if word not in names[h]:names[h].append(word)
    results=[]
    for field in links["bmw_upgrade_field_pointer_lookup"]:
        ptr=field["ptr_fixup"]
        if not ptr or ptr["ptr_type"]!=3:
            raise ValueError("BMW UpgradeSpecs pointer not verified")
        offset=ptr["target_offset"]
        candidates=[evaluate(section_data,offset,section,endian,names)
                    for section,section_data in (("BIN",BIN),("VLT",VLT))
                    for endian in ("big","little")]
        plausible=[x for x in candidates if x and x["array_bounds_valid"]]
        results.append({"variant":field["car"],"field_hash":field["field_hash"],
          "pointer_target_offset":offset,"candidates":candidates,
          "plausible_upgrade_arrays":plausible})
    return {"stage":"PRE472_BMW_UPGRADESPECS_ARRAY_METADATA_READONLY",
      "status":"AUDIT_OK","source_pal_vpak_sha256":EXPECTED_VPAK_SHA,
      "upgradespec_element_layout_bytes_from_VaultLib":16,
      "upgradespec_array_header_bytes_from_VaultLib":8,
      "bmw_upgrade_fields_inspected":len(results),
      "bmw_pointer_array_candidates":results,
      "unique_plausible_array_for_each_field":len(results)==4 and all(
        len(r["plausible_upgrade_arrays"])==1 for r in results),
      "references_are_not_proven_purchasable_car_parts":True,
      "safe_to_enable_tuning":False,
      "game_assets_uploaded":False,"apk_built":False,"save_modified":False,
      "range_bytes":reader.total}

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE472_BMW_UPGRADESPECS_ARRAY_METADATA_READONLY",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
      "game_assets_uploaded":False,"apk_built":False,"save_modified":False}
    r["utc"]=datetime.now(timezone.utc).isoformat();r["run_id"]=a.run_id
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE472_STATUS",r["status"],flush=True)
    print("PRE472_ARRAY_MATCHES",[[(x["section"],x["header_endian"],x["capacity"],x["actual_count"],x["element_bytes"]) for x in r2["plausible_upgrade_arrays"]] for r2 in r.get("bmw_pointer_array_candidates",[])],flush=True)
    print("PRE472_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
