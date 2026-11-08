#!/usr/bin/env python3
"""PRE473: reconstruct original PAL/USA pvehicle base upgrade counters (read-only).
The PAL and USA VPAK are byte-identical (PRE467); this reads only the
authenticated USA raw ISO byte ranges, using no saves, keys or APK builds.
Field layout is referenced to the original pvehicle generated header, never
used for writes. Unknown parents and malformed pointers fail closed.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import hash32,get_names,chunks,EXPECTED_VPAK_SHA

OUT=Path("/tmp/nfsmw-pre473/report.json")
PROOF=Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json")
VLT_OFFSET=355136
VLT_SIZE=342720
PTR_OFFSET=212848
PTR_SIZE=129872
EXP_OFFSET=164848
EXP_SIZE=48000
PVEHICLE_HASH=0x4A97EC8F
LAYOUT_SOURCE="dbalatoni13/nfsmw/src/Speed/Indep/Src/Generated/AttribSys/Classes/pvehicle.h"
LAYOUT_SOURCE_GIT_BLOB="9689104544d2ab9f273db4ef25996adead073b81"
FIELDS=(
  ("engine_upgrades",0x28),
  ("transmission_upgrades",0x2c),
  ("nos_upgrades",0x30),
  ("brakes_upgrades",0x34),
  ("tires_upgrades",0x3c),
  ("induction_upgrades",0x44),
  ("chassis_upgrades",0x48),
)
CONTROL_NAMES=("bmwm3gtr","m3gtre46careerstart","racers","default")

def parse_fixups(vlt,bin_size):
    block=vlt[PTR_OFFSET:PTR_OFFSET+PTR_SIZE]
    if len(block)!=PTR_SIZE or block[:4]!=b"PtrN" or int.from_bytes(block[4:8],"big")!=PTR_SIZE:
        raise ValueError("Pinned PtrN bounds mismatch")
    if (len(block)-8)%12:raise ValueError("PtrN not 12-byte aligned")
    target=None;fixups=defaultdict(list);stats=Counter()
    for i in range(8,len(block),12):
        offset,kind,index,dst=struct.unpack_from(">IHHI",block,i)
        stats[kind]+=1
        if kind==2:
            if index not in (0,1):raise ValueError("Unknown fixup target section")
            target="VLT" if index==0 else "BIN"
        elif kind in (1,3,4):
            if target is None:raise ValueError("Fixup preceding target header")
            if target=="VLT" and offset+4<=len(vlt):
                fixups[offset].append({"kind":kind,"index":index,
                      "destination_offset":dst,"source_fixup_section":"VLT"})
        elif kind==0: pass
        else:raise ValueError("Invalid PtrN fixup kind")
    return fixups,dict(stats)

def extract():
    proof=json.loads(PROOF.read_text())
    if not proof.get("pal_resource_identical_to_usa_reference") or proof.get("pal_target_sha256")!=EXPECTED_VPAK_SHA:
        raise ValueError("PAL bytewise identity proof unavailable")
    reader,location=locate()
    raw=reader.read(location["absolute_offset"],location["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:
        raise ValueError("VPAK SHA mismatch")
    _,bin_len,vlt_len,bin_off,vlt_off=struct.unpack_from("<IIIII",raw,16)
    if vlt_len!=VLT_SIZE or vlt_off!=VLT_OFFSET:
        raise ValueError("VLT section moved")
    binary=raw[bin_off:bin_off+bin_len]
    vlt=raw[vlt_off:vlt_off+vlt_len]
    if binary[:4]!=b"StrE":raise ValueError("Missing BIN strings")
    names=get_names(binary,chunks(binary,"BIN")[0])
    by_hash=defaultdict(list)
    for name in names:
        h=hash32(name)
        if name not in by_hash[h]:by_hash[h].append(name)
    fixups,stats=parse_fixups(vlt,len(binary))
    export=vlt[EXP_OFFSET:EXP_OFFSET+EXP_SIZE]
    if export[:4]!=b"ExpN" or int.from_bytes(export[4:8],"big")!=EXP_SIZE or int.from_bytes(export[8:12],"big")!=2399:
        raise ValueError("PRE466 export metadata mismatch")
    rows=[]
    all_pvehicle=0
    selected_control_hashes={hash32(s) for s in CONTROL_NAMES}
    for i in range(2399):
        e_id,kind,reserved,record_size,ref=struct.unpack_from(">IIIII",export,12+i*20)
        if reserved or ref+record_size>len(vlt):raise ValueError("Export record out of bounds")
        if kind!=0x8E112EB7:continue
        if record_size<32:raise ValueError("Collection record short")
        key,cls,parent,reserve,unknown,nentry,ntypes,layout=struct.unpack_from(">IIIIIIII",vlt,ref)
        if cls!=PVEHICLE_HASH:continue
        all_pvehicle+=1
        name=by_hash.get(key,[])
        is_punto=any("punto" in x.casefold() for x in name)
        if key not in selected_control_hashes and not is_punto:continue
        ptr=fixups.get(ref+28,[])
        candidates=[p for p in ptr if p["kind"]==3 and p["index"]==1
                    and p["destination_offset"]+0x4C<=len(binary)]
        counters=None;layout_ptr=None
        if len(candidates)==1:
            layout_ptr=candidates[0]["destination_offset"]
            counters={name:int.from_bytes(binary[layout_ptr+off:layout_ptr+off+4],"big",signed=True)
                      for name,off in FIELDS}
        rows.append({
          "export_index":i,"record_key_hash":f"{key:08x}","candidate_names":name,
          "parent_hash":f"{parent:08x}","parent_names":by_hash.get(parent,[]),
          "vlt_record_offset":ref,"layout_field_value_u32":f"{layout:08x}",
          "layout_field_raw_is_sentinel":layout==0xEFFECADD,
          "fixup_at_vlt_offset":ref+28,
          "ptrn_matches":ptr,
          "valid_single_bin_layout_fixup":len(candidates)==1,
          "bin_layout_offset":layout_ptr,
          "upgrade_counters_original_signed_i32":counters
        })
    bmw=[r for r in rows if r["candidate_names"] and any(x=="bmwm3gtr" for x in r["candidate_names"])]
    career=[r for r in rows if "m3gtre46careerstart" in r["candidate_names"]]
    if len(bmw)!=1 or len(career)!=1:
        raise ValueError("Expected unique BMW and careerstart pvehicle records")
    return {
      "status":"AUDIT_OK","stage":"PRE473_ORIGINAL_PAL_PVEHICLE_PERFORMANCE_UPGRADE_COUNTERS",
      "vpak_sha256":EXPECTED_VPAK_SHA,
      "pal_us_bytewise_identical_proof":"PRE467",
      "pc_generated_header_used_only_as_layout_reference":LAYOUT_SOURCE,
      "pc_generated_header_git_blob_sha":LAYOUT_SOURCE_GIT_BLOB,
      "binary_endian":"big","int_type":"signed_32bit",
      "pvehicle_class_hash":f"{PVEHICLE_HASH:08x}",
      "pvehicle_collection_count":all_pvehicle,
      "pvehicle_name_candidates_in_StrE":len(by_hash),
      "pointer_kind_histogram":stats,
      "field_offsets":dict(FIELDS),
      "selected_variants_and_control_records":rows,
      "all_selected_layouts_authenticated":all(x["valid_single_bin_layout_fixup"] for x in rows),
      "save_modified":False,"apk_built":False,"game_assets_exported":False,
      "force_positive_upgrade_counts":False,"upgrade_parts_installed":False,
      "upgrades_purchase_safe":False,
      "range_transferred_bytes":reader.total
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=extract()
    except Exception as e:r={"status":"FAILED",
      "stage":"PRE473_ORIGINAL_PAL_PVEHICLE_PERFORMANCE_UPGRADE_COUNTERS",
      "error_type":type(e).__name__,"error":str(e)[:250],
      "save_modified":False,"apk_built":False}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE473_STATUS",r["status"],flush=True)
    print("PRE473_PVEHICLE_COUNT",r.get("pvehicle_collection_count"),flush=True)
    print("PRE473_SELECTED_VALUES",[{"names":x["candidate_names"],
       "parent":x["parent_names"],"counters":x["upgrade_counters_original_signed_i32"],
       "layout_valid":x["valid_single_bin_layout_fixup"]}
        for x in r.get("selected_variants_and_control_records",[])],flush=True)
    print("PRE473_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
