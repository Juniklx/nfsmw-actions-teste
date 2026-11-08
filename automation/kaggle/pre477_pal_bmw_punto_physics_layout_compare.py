#!/usr/bin/env python3
"""PRE477: compare class-specific physical layout snapshots of PAL-original
BMW and Punto performance collections, read-only and SHA-authenticated.
Never interpret zero-only optional fields as equal physical performance;
the actual base layout lives in BIN and is located by PtrN fixups.
No output of raw game assets, no save or APK changes.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA
from pre474_bmw_punto_refs_readonly import KNOWN_CLASS_NAMES

OUT=Path("/tmp/nfsmw-pre477/report.json")
PROOF=Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json")
REFPROOF=Path("docs/PRE476_PAL_BMW_PUNTO_REFERENCE_RESOLUTION_READONLY.json")
EXPOFF,EXPSIZE=164848,48000
PTROFF,PTRSIZE=212848,129872
CLASS_NAMES={int(k,16):v for k,v in KNOWN_CLASS_NAMES.items()}
SIZES={"engine":0x60,"transmission":0x84,"chassis":0x74,"tires":0x50,"brakes":0x14,"induction":0x1c}
SCALAR_FLOATS={
 "engine":{"FLYWHEEL_MASS":0x50,"MAX_RPM":0x54,"RED_LINE":0x58,"IDLE":0x5c},
 "transmission":{"TORQUE_CONVERTER":0x6c,"TORQUE_SPLIT":0x70,"CLUTCH_SLIP":0x74,
                 "OPTIMAL_SHIFT":0x78,"SHIFT_SPEED":0x7c,"FINAL_GEAR":0x80},
 "chassis":{"ROLL_CENTER":0x50,"WHEEL_BASE":0x54,"SHOCK_BLOWOUT":0x58,
            "AERO_CG":0x5c,"RENDER_MOTION":0x60,"FRONT_AXLE":0x64,
            "AERO_COEFFICIENT":0x68,"FRONT_WEIGHT_BIAS":0x6c,
            "DRAG_COEFFICIENT":0x70},
 "tires":{"STEERING":0x48,"YAW_SPEED":0x4c},
 "brakes":{"EBRAKE":0x10},
 "induction":{"LOW_BOOST":0x0,"SPOOL_TIME_DOWN":0x4,"VACUUM":0x8,
              "SPOOL":0xc,"SPOOL_TIME_UP":0x10,"PSI":0x14,"HIGH_BOOST":0x18}}
HEADER_SOURCES="dbalatoni13/nfsmw generated class headers (engine, transmission, chassis, tires, brakes, induction)"
SELECT_HASHES={"bmwm3gtr":0xCD88083F,"m3gtre46careerstart":0x39DAE0F8,
                "punto_base":0xA6EE7A11,"punto_derived":0xA6F0F405,
                "default":0xEEC2271A}
def data_source():
    a=json.loads(PROOF.read_text());b=json.loads(REFPROOF.read_text())
    if a.get("status")!="AUDIT_OK" or a.get("pal_target_sha256")!=EXPECTED_VPAK_SHA or not a.get("pal_resource_identical_to_usa_reference"):
        raise ValueError("PAL identity was not proven")
    if b.get("status")!="AUDIT_OK" or b.get("source_pal_vpak_sha256")!=EXPECTED_VPAK_SHA:
        raise ValueError("PRE476 relationship proof missing")
    r,loc=locate()
    raw=r.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:
        raise ValueError("Original VPAK fingerprint mismatch")
    _,bs,vs,bo,vo=struct.unpack_from("<IIIII",raw,16)
    return r,raw[bo:bo+bs],raw[vo:vo+vs],b

def fixup_lookup(vlt):
    chunk=vlt[PTROFF:PTROFF+PTRSIZE]
    if chunk[:4]!=b"PtrN" or int.from_bytes(chunk[4:8],"big")!=PTRSIZE or len(chunk)!=PTRSIZE:
        raise ValueError("PtrN chunk differs from PRE471")
    current_section=None;result=defaultdict(list)
    for off in range(8,len(chunk),12):
        fix,typ,index,dst=struct.unpack_from(">IHHI",chunk,off)
        if typ==2:
            if index not in (0,1):raise ValueError("Invalid PtrN section switch")
            current_section=index
        elif typ in (1,3,4):
            if current_section is None:raise ValueError("Malformed PtrN order")
            if current_section==0:
                result[fix].append((typ,index,dst))
        elif typ!=0:
            raise ValueError("Unrecognized PtrN tag")
    return result

def parse_export(vlt):
    chunk=vlt[EXPOFF:EXPOFF+EXPSIZE]
    if chunk[:4]!=b"ExpN" or int.from_bytes(chunk[8:12],"big")!=2399:
        raise ValueError("ExpN source differed from PRE466")
    rows={};class_sizes={}
    for i in range(2399):
        h,typ,reserved,size,ref=struct.unpack_from(">IIIII",chunk,12+i*20)
        if reserved or ref+size>len(vlt):raise ValueError("Export row outside VLT")
        if typ==0x5E970CBC:
            if size<28:raise ValueError("Invalid ClassLoad record")
            key,reserve,defs,defptr,base_size,zero,num_base=struct.unpack_from(">IIIIIIH",vlt,ref)
            if key in CLASS_NAMES:
                class_sizes[key]={"class":CLASS_NAMES[key],"base_size_declared":base_size,
                                  "base_size_matches_reference_header":base_size==SIZES[CLASS_NAMES[key]],
                                  "field_definition_count":defs}
        if typ==0x8E112EB7:
            if size<32:raise ValueError("Invalid CollectionLoad record")
            key,cls,parent,res,unk,ne,nt,layout=struct.unpack_from(">IIIIIIII",vlt,ref)
            if cls not in CLASS_NAMES or key not in SELECT_HASHES.values():continue
            item={"vlt_record_offset":ref,"class":CLASS_NAMES[cls],"class_hash":f"{cls:08x}",
                  "collection_hash":f"{key:08x}","parent_hash":f"{parent:08x}",
                  "layout_marker":f"{layout:08x}","optional_count":ne}
            if (cls,key) in rows:raise ValueError("Duplicate class+collection")
            rows[(cls,key)]=item
    return class_sizes,rows

def floats(blob,cls):
    out={}
    for name,off in SCALAR_FLOATS[cls].items():
        if off+4>len(blob):continue
        val=struct.unpack_from(">f",blob,off)[0]
        out[name]=val if math.isfinite(val) and abs(val)<1e8 else None
    return out

def audit():
    reader,B,V,old=data_source()
    fixes=fixup_lookup(V)
    sizes,rows=parse_export(V)
    samples={}
    for cls,name in CLASS_NAMES.items():
        if name not in SIZES or name=="nos":continue
        meta=sizes.get(cls)
        if not meta:raise ValueError("Missing source class definition for "+name)
        layout_size=SIZES[name]
        per={}
        for label,key in SELECT_HASHES.items():
            item=rows.get((cls,key))
            if item is None:continue
            pointer_at=item["vlt_record_offset"]+28
            matches=[p for p in fixes.get(pointer_at,[]) if p[0]==3 and p[1]==1 and p[2]+layout_size<=len(B)]
            sample={**item,"fixup_candidates":len(matches),"has_bounded_layout":len(matches)==1}
            if len(matches)==1:
                off=matches[0][2]
                data=B[off:off+layout_size]
                sample.update({"bin_base_offset":off,"layout_bytes":len(data),
                  "sha256":hashlib.sha256(data).hexdigest(),
                  "scalar_f32_be_from_generated_pc_header":floats(data,name)})
            per[label]=sample
        compares=[]
        for a,b in (("punto_base","punto_derived"),("bmwm3gtr","punto_base"),
                    ("bmwm3gtr","m3gtre46careerstart")):
            x,y=per.get(a),per.get(b)
            if not (x and y and x.get("has_bounded_layout") and y.get("has_bounded_layout")):continue
            raw_a=B[x["bin_base_offset"]:x["bin_base_offset"]+layout_size]
            raw_b=B[y["bin_base_offset"]:y["bin_base_offset"]+layout_size]
            changed=[i for i in range(0,layout_size,4) if raw_a[i:i+4]!=raw_b[i:i+4]]
            compares.append({"left":a,"right":b,"same_layout_bytes":raw_a==raw_b,
               "different_4byte_words":len(changed),
               "different_word_offsets_hex":[f"0x{i:x}" for i in changed[:45]],
               "changed_word_offset_list_truncated":len(changed)>45})
        samples[name]={"metadata":meta,"collections":per,"comparisons":compares}
    required=[("engine","punto_base"),("engine","punto_derived"),
              ("engine","bmwm3gtr"),("transmission","punto_derived"),
              ("chassis","bmwm3gtr"),("tires","punto_derived"),
              ("brakes","punto_derived")]
    all_required=all(samples.get(c,{}).get("collections",{}).get(k,{}).get("has_bounded_layout",False)
                     for c,k in required)
    return {
      "stage":"PRE477_PAL_BMW_VS_PUNTO_PHYSICS_PROFILE_LAYOUTS_READONLY",
      "status":"AUDIT_OK","source_sha256":EXPECTED_VPAK_SHA,
      "pal_binary_identical_to_usa_from_PRE467":True,
      "class_layout_reference":HEADER_SOURCES,
      "class_models":samples,
      "all_required_bounded_layouts_found":all_required,
      "finite_scalar_numbers_are_observations_not_verified_simulation_effects":True,
      "no_source_modifications":True,"safe_to_enable_bmw_upgrade":False,
      "game_assets_published":False,"apk_built":False,"save_modified":False,
      "range_bytes":reader.total
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE477_PAL_BMW_VS_PUNTO_PHYSICS_PROFILE_LAYOUTS_READONLY",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:240],
      "game_assets_published":False,"apk_built":False,"save_modified":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE477_STATUS",r["status"],flush=True)
    print("PRE477_LAYOUTS",{name:{"expected":v["metadata"]["base_size_matches_reference_header"],
        "comparisons":v["comparisons"]} for name,v in r.get("class_models",{}).items()},flush=True)
    print("PRE477_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
