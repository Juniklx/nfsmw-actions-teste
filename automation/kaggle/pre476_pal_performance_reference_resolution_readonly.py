#!/usr/bin/env python3
"""PRE476: check referenced performance collections and their parent chains.
Input: SHA-verified original USA ATTRIBUTES.BIN, independently identical to
user's PAL BIN in PRE467. No repacking, binary output, APK, or save writes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import hash32, EXPECTED_VPAK_SHA
from pre474_bmw_punto_refs_readonly import KNOWN_CLASS_NAMES

OUT = Path("/tmp/nfsmw-pre476/report.json")
SOURCE_PROOF = Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json")
REFERENCE_PROOF = Path("docs/PRE474_PAL_BMW_PUNTO_PERFORMANCE_REF_ARRAYS.json")
EXP_OFF, EXP_BYTES = 164848, 48000
CLASSES = {int(h, 16): label for h, label in KNOWN_CLASS_NAMES.items()}
TARGETS = ("bmwm3gtr", "m3gtre46careerstart", "punto")
CONTRASTS = ("engine", "transmission", "chassis", "tires", "brakes", "nos", "induction")
UNRESOLVED_PUNTO = 0xA6F0F405

def read_source():
    identity = json.loads(SOURCE_PROOF.read_text())
    references = json.loads(REFERENCE_PROOF.read_text())
    if (identity.get("status") != "AUDIT_OK"
       or identity.get("pal_target_sha256") != EXPECTED_VPAK_SHA
       or not identity.get("pal_resource_identical_to_usa_reference")):
        raise ValueError("PAL/USA matching VPAK provenance missing")
    if (references.get("status") != "AUDIT_OK"
       or references.get("vpak_sha256") != EXPECTED_VPAK_SHA):
        raise ValueError("PRE474 actual reference array provenance missing")
    reader, loc = locate()
    source = reader.read(loc["absolute_offset"], loc["size"])
    if hashlib.sha256(source).hexdigest() != EXPECTED_VPAK_SHA:
        raise ValueError("Original VPAK SHA changed")
    _, binlen, vltlen, binoff, vltoff = struct.unpack_from("<IIIII", source, 16)
    if not (0 < binoff < binoff + binlen <= len(source)
            and 0 < vltoff < vltoff + vltlen <= len(source)):
        raise ValueError("Invalid source section bounds")
    vlt = source[vltoff:vltoff + vltlen]
    return reader, references, vlt

def collect_rows(vlt):
    chunk = vlt[EXP_OFF:EXP_OFF + EXP_BYTES]
    if chunk[:4] != b"ExpN" or int.from_bytes(chunk[4:8], "big") != EXP_BYTES:
        raise ValueError("PRE466 ExpN proof moved")
    if int.from_bytes(chunk[8:12], "big") != 2399:
        raise ValueError("PRE466 2399 export count changed")
    refs = defaultdict(list)
    class_counter = defaultdict(int)
    for i in range(2399):
        export_id, kind, reserved, size, position = struct.unpack_from(">IIIII", chunk, 12 + i*20)
        if reserved or position + size > len(vlt) or size < 20:
            raise ValueError("Unbounded export record index")
        if kind != 0x8E112EB7:
            continue
        if size < 32:
            raise ValueError("Unbounded collection header")
        collection, cls, parent, res, unk, count, tcount, layout = struct.unpack_from(">IIIIIIII", vlt, position)
        if count > 2048 or tcount > 2048 or count != res:
            raise ValueError("Invalid collection field count")
        row = {
           "class_hash": f"{cls:08x}",
           "collection_hash": f"{collection:08x}",
           "parent_hash": f"{parent:08x}",
           "optional_attribute_count": count,
           "field_type_count": tcount,
           "record_size": size,
           "record_offset_vlt": position,
           "export_index": i,
        }
        refs[(cls,collection)].append(row)
        class_counter[cls] += 1
    return refs, class_counter

def parent_chain(refs, class_hash, collection_hash, limit=10):
    result=[]
    seen=set()
    current=collection_hash
    for n in range(limit):
        if current in seen:
            return result, "CYCLE"
        seen.add(current)
        rows=refs.get((class_hash,current),[])
        if not rows:
            return result, "MISSING_REFERENCED_COLLECTION" if n == 0 else "MISSING_PARENT"
        if len(rows) != 1:
            return result, "DUPLICATE_CLASS_COLLECTION"
        row=rows[0]
        result.append(row)
        parent=int(row["parent_hash"],16)
        if parent==0:
            return result, "END_ZERO_PARENT"
        current=parent
    return result,"DEPTH_LIMIT"

def audit():
    reader, source_refs, vlt = read_source()
    all_rows, class_counts = collect_rows(vlt)
    results={}
    missing=0
    for variant in TARGETS:
        source_vehicle = source_refs["vehicles"][variant]
        attrs=source_vehicle["categories_with_explicit_references"]
        checked={}
        for category in CONTRASTS:
            rec=attrs.get(category)
            if rec is None:
                checked[category]={"explicit_field_found":False,
                    "note":"May be inherited; no negative existence assertion"}
                continue
            if not rec.get("array_header_valid") or not rec.get("items"):
                raise ValueError("Invalid PRE474 array for "+variant+"/"+category)
            records=[]
            for item in rec["items"]:
                cls=int(item["class_hash"],16)
                key=int(item["collection_hash"],16)
                if cls not in CLASSES or CLASSES[cls]!=category:
                    raise ValueError("PRE474 RefSpec class mismatch")
                chain,state=parent_chain(all_rows,cls,key)
                if not chain:
                    missing+=1
                records.append({
                  "array_item_index":item["index"],
                  "ref_collection_hash":item["collection_hash"],
                  "ref_class_hash":item["class_hash"],
                  "explicit_reference_exists_in_vlt":len(chain)>0,
                  "chain_termination":state,
                  "chain":chain
                })
            checked[category]={
                "explicit_field_found":True,
                "declared_array_count":rec["item_count"],
                "original_upgrade_counter":rec["pvehicle_upgrade_limit"],
                "reference_resolution":records,
            }
        results[variant]=checked
    keys=[(cls,UNRESOLVED_PUNTO) for cls in CLASSES]
    extra=[]
    for cls,key in keys:
        chain,state=parent_chain(all_rows,cls,key)
        extra.append({"class_hash":f"{cls:08x}",
                      "class_name":CLASSES[cls],
                      "record_exists":bool(chain),
                      "ancestry_state":state,"ancestry":chain})
    unresolved_extra_count=sum(x["record_exists"] for x in extra)
    return {
       "stage":"PRE476_PAL_BMW_PUNTO_REFERENCE_RESOLUTION_READONLY",
       "status":"AUDIT_OK",
       "source_pal_vpak_sha256": EXPECTED_VPAK_SHA,
       "referenced_source_proofs":["PRE467","PRE474"],
       "all_indexed_collections":sum(len(x) for x in all_rows.values()),
       "punto_second_reference_hash":"a6f0f405",
       "punto_second_reference_per_class":extra,
       "second_reference_classes_resolved":unresolved_extra_count,
       "vehicles":results,
       "missing_refspec_targets":missing,
       "reference_existence_does_not_mean_available_upgrades":True,
       "part_catalog_validated":False,
       "safe_to_enable_tuning":False,
       "source_assets_published":False,
       "save_modified":False,
       "apk_built":False,
       "ranges_transferred_bytes":reader.total,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=audit()
    except Exception as e:
        result={"stage":"PRE476_PAL_BMW_PUNTO_REFERENCE_RESOLUTION_READONLY",
                "status":"FAILED",
                "error_type":type(e).__name__,
                "error":str(e)[:245],
                "source_assets_published":False,"save_modified":False,"apk_built":False}
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PRE476_STATUS",result["status"],flush=True)
    print("PRE476_MATCHED_SECOND_REF",result.get("second_reference_classes_resolved","?"),flush=True)
    print("PRE476_MISSING_ORIGINAL_TARGETS",result.get("missing_refspec_targets","?"),flush=True)
    print("PRE476_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    raise SystemExit(main())
