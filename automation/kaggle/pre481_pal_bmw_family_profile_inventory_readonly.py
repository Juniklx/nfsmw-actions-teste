#!/usr/bin/env python3
"""PRE481: inventory named BMW performance profiles in authenticated PAL VPAK.

Original game attribute data are read through a SHA-pinned, bounded read-only
source. No asset bytes, modified files, physical profiles, savegames or APKs
are written. Findings are metadata, not purchasable upgrade proof.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from datetime import datetime, timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA, hash32, get_names, chunks
from pre476_pal_performance_reference_resolution_readonly import collect_rows, parent_chain
from pre477_pal_bmw_punto_physics_layout_compare import fixup_lookup, SIZES, CLASS_NAMES, floats

OUT=Path("/tmp/nfsmw-pre481/report.json")
PROOF=Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json")
PHYSICS=Path("docs/PRE477_PAL_BMW_PUNTO_PHYSICS_LAYOUTS_READONLY.json")
PVEHICLE=0x4A97EC8F
EXP_OFF=164848
EXP_LEN=48000
BMW_BASE="bmwm3gtr"
KNOWN_VARIANTS=("bmwm3gtr","bmwm3gtre46","m3gtre46careerstart","BMWM3GTR","BMWM3GTRE46")
TARGET_CLASS_NAMES=tuple(x for x in ("engine","transmission","chassis","tires","brakes","induction") if x in SIZES)
CLASS_TO_HASH={v:k for k,v in CLASS_NAMES.items()}
HASH_TO_CLASS={**CLASS_NAMES,PVEHICLE:"pvehicle"}
def validate_source():
    proof=json.loads(PROOF.read_text())
    physics=json.loads(PHYSICS.read_text())
    if (proof.get("status")!="AUDIT_OK" or
        proof.get("pal_target_sha256")!=EXPECTED_VPAK_SHA or
        proof.get("pal_resource_identical_to_usa_reference") is not True or
        physics.get("status")!="AUDIT_OK" or
        physics.get("source_sha256")!=EXPECTED_VPAK_SHA or
        physics.get("all_required_bounded_layouts_found") is not True):
        raise ValueError("PRE467/PRE477 authenticated original data proof unavailable")
    reader,loc=locate()
    raw=reader.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:
        raise ValueError("Original PAL/USA-identical VPAK SHA mismatch")
    _,binlen,vltlen,binoff,vltoff=struct.unpack_from("<IIIII",raw,16)
    if binoff!=128 or binlen!=354959 or vltoff!=355136 or vltlen!=342720:
        raise ValueError("PRE463 source offsets no longer match")
    return reader,raw[binoff:binoff+binlen],raw[vltoff:vltoff+vltlen]

def export_index(vlt):
    part=vlt[EXP_OFF:EXP_OFF+EXP_LEN]
    if (part[:4]!=b"ExpN" or int.from_bytes(part[4:8],"big")!=EXP_LEN or
        int.from_bytes(part[8:12],"big")!=2399):
        raise ValueError("PRE466 ExpN bounds changed")
    index={}
    for i in range(2399):
        id_,kind,reserved,size,ref=struct.unpack_from(">IIIII",part,12+i*20)
        if reserved or size<20 or ref+size>len(vlt):
            raise ValueError("Invalid export record bounds")
        if kind!=0x8E112EB7:continue
        if size<32:raise ValueError("Invalid collection record size")
        name,cls,parent,cap,u,n,t,layout=struct.unpack_from(">IIIIIIII",vlt,ref)
        if cap!=n or n>1000 or t>1000 or 32+4*t+12*n>size:
            raise ValueError("Invalid collection metadata")
        pair=(cls,name)
        if pair in index:raise ValueError("Duplicate class+collection VLT export")
        index[pair]={"export_index":i, "vlt_offset":ref,"parent_hash":f"{parent:08x}",
            "optional_field_count":n,"base_layout_raw_word":f"{layout:08x}"}
    return index

def analyze():
    reader,B,V=validate_source()
    names=get_names(B,chunks(B,"BIN")[0])
    unique=sorted(set(names))
    family=sorted(x for x in unique if
        ("bmwm3" in x.lower() or "m3gtr" in x.lower()) and
        not (x.lower().endswith("_hood") or ".gin" in x.lower()))
    selected=sorted(set(KNOWN_VARIANTS).union(
        x for x in family if len(x)<70 and
        x.replace("_","").isalnum() and "exhaust" not in x.lower()))
    index=export_index(V)
    ancestors,_=collect_rows(V)
    fixups=fixup_lookup(V)
    samples={}
    for name in selected:
        key=hash32(name)
        per={}
        for cls,label in HASH_TO_CLASS.items():
            record=index.get((cls,key))
            if not record:continue
            chain,state=parent_chain(ancestors,cls,key,limit=16)
            entry={"class":label,"class_hash":f"{cls:08x}",
                   "collection_name":name,"collection_hash":f"{key:08x}",
                   "VLT_collection_exists":True,
                   "inheritance_path":[x["collection_hash"] for x in chain],
                   "inheritance_termination":state,
                   "optional_field_count":record["optional_field_count"],
                   "class_base_layout_sha256":None,
                   "layout_data_in_original_vpak":False}
            if label in SIZES:
                off=record["vlt_offset"]+28
                ptrs=[p for p in fixups.get(off,[]) if
                      p[0]==3 and p[1]==1 and p[2]+SIZES[label]<=len(B)]
                entry["bin_layout_fixup_count"]=len(ptrs)
                if len(ptrs)==1:
                    data=B[ptrs[0][2]:ptrs[0][2]+SIZES[label]]
                    entry.update({"layout_data_in_original_vpak":True,
                                  "class_base_layout_sha256":hashlib.sha256(data).hexdigest(),
                                  "original_big_endian_scalar_samples":floats(data,label)})
            per[label]=entry
        samples[name]={"lookup2_hash":f"{key:08x}","is_name_in_StrE":name in unique,
            "performance_classes":per}
    bmw=samples.get(BMW_BASE,{}).get("performance_classes",{})
    for name,record in samples.items():
        for cls,item in record["performance_classes"].items():
            if cls in bmw and cls in SIZES and
                item.get("layout_data_in_original_vpak") and
                bmw[cls].get("layout_data_in_original_vpak"):
                item["physical_layout_byte_identical_to_bmwm3gtr"]=(
                    item["class_base_layout_sha256"]==bmw[cls]["class_base_layout_sha256"])
    validated_base=sum(bool(bmw.get(c,{}).get("layout_data_in_original_vpak"))
                       for c in TARGET_CLASS_NAMES)
    return {
       "stage":"PRE481_PAL_BMW_FAMILY_ORIGINAL_PERFORMANCE_PROFILES",
       "status":"AUDIT_OK",
       "pal_vpak_sha256":EXPECTED_VPAK_SHA,
       "source_pal_identical_to_usa_proven":True,
       "bmw_names_found_in_strE":family,
       "analyzed_exact_names":selected,
       "vehicle_family_records":samples,
       "bmwm3gtr_base_physics_classes_verified":validated_base,
       "candidate_bmw_alternate_physical_profiles":[
            {"collection_name":name,"class_name":cls,"sha256":v["class_base_layout_sha256"]}
            for name,entry in samples.items() if name!=BMW_BASE
            for cls,v in entry["performance_classes"].items()
            if cls in TARGET_CLASS_NAMES and v.get("layout_data_in_original_vpak")
       ],
       "candidate_alternative_profile_is_not_verified_purchase_level":True,
       "reference_is_not_sufficient_to_install_upgrade":True,
       "custom_upgrade_physics_proven":False,
       "frontend_catalog_proven":False,
       "runtime_mod_enabled":False,"save_modified":False,
       "game_assets_published":False,"apk_built":False,
       "bytes_read_original_vpak":reader.total
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);opts=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=analyze()
    except Exception as e:r={"stage":"PRE481_PAL_BMW_FAMILY_ORIGINAL_PERFORMANCE_PROFILES",
        "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
        "runtime_mod_enabled":False,"save_modified":False,"apk_built":False}
    r["run_id"]=opts.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE481_STATUS",r["status"],flush=True)
    print("PRE481_FAMILY_NAMES",r.get("bmw_names_found_in_strE"),flush=True)
    print("PRE481_MATCH_COUNTS",{name:len(v["performance_classes"]) for name,v in r.get("vehicle_family_records",{}).items()},flush=True)
    print("PRE481_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
