#!/usr/bin/env python3
"""PRE474: inspect original BMW/Punto pvehicle RefSpec configuration arrays.
Read only SHA-pinned PAL-identical USA VPAK and metadata from previous audits.
No writes, no valid part assumptions, no save access, no APK build.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from collections import defaultdict,Counter
from pathlib import Path
from datetime import datetime,timezone
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import hash32,get_names,chunks,EXPECTED_VPAK_SHA

OUT=Path("/tmp/nfsmw-pre474/report.json")
PRE467=Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json")
PRE473=Path("docs/PRE473_PAL_PVEHICLE_BMW_UPGRADE_COUNTERS_READONLY.json")
PVCLASS=0x4A97EC8F
BIN_INDEX=1
PTR_START=212848
PTR_SIZE=129872
EXPORT=164848
EXPORT_SIZE=48000
CATEGORIES=("engine","transmission","chassis","nos","tires","brakes","induction")
VEHICLES=("bmwm3gtr","m3gtre46careerstart","punto")
KNOWN_CLASS_NAMES={"f1f5fbc7":"engine","07a7a3e5":"transmission","afa210f0":"chassis",
 "b1669f64":"nos","bd38d1ca":"tires","36350867":"brakes","c92a0142":"induction"}
def array_candidate(bin_data,start,fields):
    if not 0<=start<=len(bin_data)-8:
        return {"array_header_valid":False,"reason":"out_of_bounds"}
    cap,num,elsize,unknown=struct.unpack_from(">HHHH",bin_data,start)
    ok=(0<cap<=80 and 0<=num<=cap and elsize==12 and start+8+cap*12<=len(bin_data))
    result={"capacity":cap,"item_count":num,"element_size":elsize,
            "flags":f"{unknown:04x}","array_header_valid":ok}
    if not ok:return result
    refs=[]
    for i in range(num):
        c,r,third=struct.unpack_from(">III",bin_data,start+8+i*12)
        refs.append({"index":i,"class_hash":f"{c:08x}",
                     "class_name":KNOWN_CLASS_NAMES.get(f"{c:08x}"),
                     "collection_hash":f"{r:08x}",
                     "collection_name_candidates":fields.get(r,[])[:4],
                     "trailing_u32":f"{third:08x}"})
    result["items"]=refs
    return result

def audit():
    proof=json.loads(PRE467.read_text())
    orig=json.loads(PRE473.read_text())
    if proof.get("pal_target_sha256")!=EXPECTED_VPAK_SHA or not proof.get("pal_resource_identical_to_usa_reference"):
        raise ValueError("PAL VPAK identity proof missing")
    if orig.get("status")!="AUDIT_OK" or orig.get("vpak_sha256")!=EXPECTED_VPAK_SHA:
        raise ValueError("PRE473 counters not verified")
    reader,loc=locate()
    raw=reader.read(loc["absolute_offset"],loc["size"])
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_VPAK_SHA:raise ValueError("VPAK fingerprint changed")
    _,binlen,vltlen,binoff,vltoff=struct.unpack_from("<IIIII",raw,16)
    B=raw[binoff:binoff+binlen]
    V=raw[vltoff:vltoff+vltlen]
    nmap=defaultdict(list)
    for s in get_names(B,chunks(B,"BIN")[0]):
        h=hash32(s)
        if s not in nmap[h]:nmap[h].append(s)
    ptr=V[PTR_START:PTR_START+PTR_SIZE]
    if ptr[:4]!=b"PtrN" or int.from_bytes(ptr[4:8],"big")!=PTR_SIZE:raise ValueError("PtrN source mismatch")
    fixups=defaultdict(list);target=None
    for i in range(8,len(ptr),12):
        off,kind,index,dst=struct.unpack_from(">IHHI",ptr,i)
        if kind==2:
            if index not in (0,1):raise ValueError("Unknown PtrN section")
            target=index
        elif kind in (1,3,4) and target==0 and off+4<=len(V):
            fixups[off].append((kind,index,dst))
    chunk=V[EXPORT:EXPORT+EXPORT_SIZE]
    if chunk[:4]!=b"ExpN" or int.from_bytes(chunk[8:12],"big")!=2399:
        raise ValueError("Export header changed")
    found={}
    for i in range(2399):
        eid,typ,res,size,offset=struct.unpack_from(">IIIII",chunk,12+i*20)
        if res or offset+size>len(V):raise ValueError("Invalid export")
        if typ!=0x8E112EB7 or size<32:continue
        key,cls,parent,reserve,unused,ne,nt,lp=struct.unpack_from(">IIIIIIII",V,offset)
        if cls!=PVCLASS:continue
        if key not in {hash32(x) for x in VEHICLES}:continue
        name=[x for x in VEHICLES if hash32(x)==key][0]
        if name in found:raise ValueError("Duplicate pvehicle vehicle "+name)
        if reserve!=ne or nt>128 or ne>128 or 32+4*nt+12*ne>size:
            raise ValueError("Invalid optional array field offsets")
        attributes={}
        for j in range(ne):
            off=offset+32+4*nt+j*12
            fieldhash,value,typidx,flags=struct.unpack_from(">IIHH",V,off)
            for cat in CATEGORIES:
                if fieldhash!=hash32(cat):continue
                if cat in attributes:raise ValueError("Duplicate optional category field")
                fixes=[x for x in fixups.get(off+4,[]) if x[0]==3 and x[1]==1 and x[2]<len(B)]
                record={"field_name":cat,"field_hash":f"{fieldhash:08x}",
                  "nodeflags_be":f"{flags:04x}","type_index":typidx,
                  "sentinel_vlt_value":f"{value:08x}",
                  "pointer_fixups_count":len(fixes),"bin_array_offset":fixes[0][2] if len(fixes)==1 else None}
                if len(fixes)==1:record.update(array_candidate(B,fixes[0][2],nmap))
                attributes[cat]=record
        found[name]={"collection_name":name,"collection_hash":f"{key:08x}",
          "parent_hash":f"{parent:08x}","parent_name_candidates":nmap.get(parent,[]),
          "optional_entry_count":ne,"categories_with_explicit_references":attributes}
    if set(found)!=set(VEHICLES):raise ValueError("Missing named BMW/Punto pvehicle")
    original_map={r["candidate_names"][0]:r["upgrade_counters_original_signed_i32"]
        for r in orig["selected_variants_and_control_records"]
        if r["candidate_names"] and r["candidate_names"][0] in VEHICLES}
    counters={"engine":"engine_upgrades","transmission":"transmission_upgrades",
      "chassis":"chassis_upgrades","nos":"nos_upgrades","tires":"tires_upgrades",
      "brakes":"brakes_upgrades","induction":"induction_upgrades"}
    for name,data in found.items():
        if name not in original_map:raise ValueError("PRE473 count control unavailable")
        for cat in CATEGORIES:
            if cat in data["categories_with_explicit_references"]:
                data["categories_with_explicit_references"][cat]["pvehicle_upgrade_limit"]=original_map[name][counters[cat]]
        data["pvehicle_original_all_upgrade_limits"]=original_map[name]
    return {
      "stage":"PRE474_PAL_ORIGINAL_BMW_REAL_REF_ARRAY_INVENTORY",
      "status":"AUDIT_OK","vpak_sha256":EXPECTED_VPAK_SHA,
      "pal_binary_identical_to_usa_from_PRE467":True,
      "reference_array_item_size_bytes":12,"refspec_has_class_collection_and_reserved":True,
      "vehicles":found,
      "candidate_refspec_array_does_not_prove_purchasable_upgrade_part":True,
      "part_catalog_validated":False,"safe_to_enable_mod":False,
      "apk_built":False,"save_accessed":False,
      "assets_published":False,"ranges_transferred_bytes":reader.total
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE474_PAL_ORIGINAL_BMW_REAL_REF_ARRAY_INVENTORY",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:230],
      "apk_built":False,"save_accessed":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE474_STATUS",r["status"],flush=True)
    for name,info in r.get("vehicles",{}).items():
        print("PRE474_VEHICLE",name,"UPGRADE_LIMITS",info["pvehicle_original_all_upgrade_limits"],flush=True)
        for cat,rec in info["categories_with_explicit_references"].items():
            print("PRE474_REF",name,cat,"HEADER_VALID",rec.get("array_header_valid"),
                 "ITEMS",rec.get("item_count"),"CAPACITY",rec.get("capacity"),flush=True)
    print("PRE474_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
