#!/usr/bin/env python3
"""PRE521: authenticated, read-only discovery of original FE_ATTRIB.BIN vault.

The public original-code reference describes:
  GameFlow::LoadFrontEndVault -> GLOBAL\\FE_ATTRIB.BIN -> frontend vault
  UnlockSystem::LookupFEPartInfo -> frontend class carparts descendants
  FECarPartInfo: Level:i32, Rep:f32, Cost:f32
Here we independently inspect actual USA Xbox 360 resource metadata,
byte hashes, VPAK/BIN/VLT chunks and frontend collection records.
Reference source is not automatic proof of PAL guest runtime equivalence.
No game asset exports, APK builds, saves, or signing-key access.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,re
from datetime import datetime,timezone
from pathlib import Path
from pre462_usa_raw_iso_attributes_readonly import (
    Reader,PARTITION_BASE,EXPECTED_NFS_SECTOR,SECTOR,dir_entries,NAMES
)
from pre465_usa_bmw_vpak_inner_schema_readonly import chunks,get_names,hash32
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
OUT=Path("/tmp/nfsmw-pre521/report.json")
TARGET="GLOBAL\\FE_ATTRIB.BIN"
TARGET_HASH=NAMES[TARGET]
EXPECTED_ARCHIVE=0
EXPECTED_OFFSET=162392064
EXPECTED_SIZE=113856
FRONTEND_CLASS_HASH=0x85885722
COLLECTION_KIND=0x8E112EB7
CATEGORY_NAMES=["carparts","engine","transmission","chassis","brakes","tires","induction","nos",
                "p_engine_1","p_engine_2","p_engine_3","p_engine_4"]
SOURCE_REF={
 "source_repository":"dbalatoni13/nfsmw",
 "source_commit":"80993f35224c61d2f1b135beba76c6f8234c7940",
 "lookup_source":"src/Speed/Indep/Src/Frontend/Careers/UnlockSystem.cpp",
 "vault_loading_source":"src/Speed/Indep/Src/Misc/GameFlow.cpp",
 "schema_source":"src/Speed/Indep/Src/Frontend/FEReflected.hpp",
 "frontend_class_source":"src/Speed/Indep/Src/Generated/AttribSys/Classes/frontend.h",
 "reference_platform":"PC reconstructed source; Xbox 360 guest compatibility not proven"
}

def audit():
    pre462=json.loads(Path("docs/PRE462_USA_REFERENCE_CATALOG_RESOURCE_METADATA.json").read_text())
    pre517=json.loads(Path("docs/PRE517_ORIGINAL_ZDIR_EA_DATA_HASH_AND_TOTAL_OFFSETS_READONLY.json").read_text())
    if (pre462.get("status")!="AUDIT_OK" or
        pre517.get("status")!="AUDIT_OK" or
        not pre517.get("candidate_checksum_matches_original_target") or
        not pre517.get("all_samples_match_candidate_hash")):
        raise ValueError("Missing authenticated source index / hashing proof")
    known=pre462.get("resource_candidates",{}).get(TARGET,{})
    if known.get("entries")!=1 or known.get("locations")!=[
        {"archive":EXPECTED_ARCHIVE,"offset":EXPECTED_OFFSET,"size":EXPECTED_SIZE}
    ]:
        raise ValueError("FE_ATTRIB target resource metadata changed")

    r=Reader()
    tree=r.read(PARTITION_BASE+EXPECTED_NFS_SECTOR*SECTOR,2048)
    filemap={x["name"].upper():x for x in dir_entries(tree)}
    zz=filemap.get("ZZDATA0.BIN")
    zi=filemap.get("ZDIR.BIN")
    if not zz or not zi or zz["is_dir"] or zi["is_dir"]:
        raise ValueError("Missing original USA FE data archive/ZDIR")
    zdir=r.read(PARTITION_BASE+zi["sector"]*SECTOR,zi["size"])
    if len(zdir)!=1390*24:
        raise ValueError("Unexpected original FE ZDIR table length")
    matching=[]
    for i,(h,arc,sector,total,size,checksum) in enumerate(struct.iter_unpack("<IiIIiI",zdir)):
        if h==TARGET_HASH:matching.append((i,arc,sector,total,size,checksum))
    if len(matching)!=1:raise ValueError("Original FE_ATTRIB entry not unique")
    index,arc,sector,total,size,checksum=matching[0]
    if ((arc,sector*SECTOR,size)!=(EXPECTED_ARCHIVE,EXPECTED_OFFSET,EXPECTED_SIZE)
        or size+sector*SECTOR>zz["size"]):
        raise ValueError("FE_ATTRIB original archive bounds unexpected")
    absolute=PARTITION_BASE+zz["sector"]*SECTOR+sector*SECTOR
    source=r.read(absolute,size)
    if len(source)!=EXPECTED_SIZE or source[:4]!=b"VPAK":
        raise ValueError("Original FE_ATTRIB is not expected VPAK")
    sha=hashlib.sha256(source).hexdigest()
    actual_checksum=ea_data_hash(source)
    if actual_checksum!=checksum:
        raise ValueError("Actual FE_ATTRIB data checksum disagrees with original ZDIR")

    n,vnames,vlen=struct.unpack_from("<III",source,4)
    if not (1<=n<=8 and 16+20*n<=len(source) and
            vnames>=16+20*n and 0<vlen<=4096 and vnames+vlen<=len(source)):
        raise ValueError("FE_ATTRIB VPAK header or string table bounds invalid")
    vaults=[]
    frontend_rows=[]
    for i in range(n):
        nameptr,binlen,vltlen,binoff,vltoff=struct.unpack_from("<IIIII",source,16+i*20)
        ns=vnames+nameptr
        if not vnames<=ns<vnames+vlen:
            raise ValueError("Original FE VPAK vault name pointer invalid")
        end=source.find(b"\0",ns,vnames+vlen)
        if end<=ns or end-ns>72:raise ValueError("Vault name missing/invalid")
        name=source[ns:end].decode("ascii","replace")
        if (binoff+binlen>len(source) or vltoff+vltlen>len(source)
            or binlen<16 or vltlen<30 or binoff>=vltoff):
            raise ValueError("Original FE vault section bounds invalid")
        binn=source[binoff:binoff+binlen]
        vltn=source[vltoff:vltoff+vltlen]
        bchunks,btail=chunks(binn,"FE BIN")
        vchunks,vtail=chunks(vltn,"FE VLT")
        if not bchunks or bchunks[0]["tag"]!="StrE" or not vchunks or vchunks[0]["tag"]!="DepN":
            raise ValueError("Original frontend vault section tags unexpected")
        names=get_names(binn,bchunks)
        related=[a for a in names if re.search(r"(carparts|engine|performance|brake|transmission|chassis|tire|induction|nos|upgrade)",a,re.I)]
        ex=[c for c in vchunks if c["tag"]=="ExpN"]
        if len(ex)!=1:raise ValueError("FE ExpN export table missing or repeated")
        start=ex[0]["relative_offset"]
        count=struct.unpack_from(">I",vltn,start+8)[0]
        if not (1<=count<=25000 and start+12+20*count<=start+ex[0]["declared_size"]):
            raise ValueError("FE VLT ExpN table bounds invalid")
        kinds={}
        classcounts={}
        front_col=[]
        for j in range(count):
            expid,kind,unused,record_size,pos=struct.unpack_from(">IIIII",vltn,start+12+j*20)
            k=f"{kind:08x}"
            kinds[k]=kinds.get(k,0)+1
            if kind!=COLLECTION_KIND:continue
            if (record_size<28 or record_size>1024 or
                pos+record_size>start or pos+12>len(vltn)):
                raise ValueError("Malformed FE VLT collection export")
            colhash,cls,parent=struct.unpack_from(">III",vltn,pos)
            classcounts[f"{cls:08x}"]=classcounts.get(f"{cls:08x}",0)+1
            if cls==FRONTEND_CLASS_HASH:
                front_col.append({
                  "name_hash":f"{colhash:08x}","parent_hash":f"{parent:08x}",
                  "record_offset":pos,"record_size":record_size,
                  "matches_carparts_name_hash":colhash==hash32("carparts"),
                  "parent_is_carparts":parent==hash32("carparts")
                })
        frontend_rows.extend(front_col)
        vaults.append({
          "vault_name":name,"BIN_bytes":binlen,"VLT_bytes":vltlen,
          "BIN_sha256":hashlib.sha256(binn).hexdigest(),
          "VLT_sha256":hashlib.sha256(vltn).hexdigest(),
          "BIN_chunks":[x["tag"] for x in bchunks],
          "VLT_chunks":[x["tag"] for x in vchunks],
          "BIN_StrE_distinct_strings":len(names),
          "related_StrE_name_samples":related[:75],
          "ExpN_export_count":count,
          "export_kind_counts":kinds,
          "collection_counts_by_class_hash":classcounts,
          "frontend_class_collection_count":len(front_col)
        })
    if not frontend_rows:
        raise ValueError("No frontend class 0x85885722 collection was resolved")
    if not any(c["matches_carparts_name_hash"] for c in frontend_rows):
        raise ValueError("No carparts parent collection in original FE vault")
    parts=[x for x in frontend_rows if x["parent_is_carparts"]]
    return {
      "stage":"PRE521_ORIGINAL_USA_FE_ATTRIB_VPAK_FRONTEND_CARPARTS_STRUCTURE_READONLY",
      "status":"AUDIT_OK",
      "public_code_reference":SOURCE_REF,
      "user_original_USA_iso_sha_provenance":"PRE462/PRE517 authentic strict HTTP 206",
      "USA_FE_ATTRIB_from_original_zzdata":True,
      "USA_only_PAL_equivalence_NOT_verified":True,
      "source_resource":TARGET,
      "source_resource_name_hash":f"{TARGET_HASH:08x}",
      "source_ZDIR_row":index,
      "source_archive_index":arc,
      "source_local_offset_bytes":sector*SECTOR,
      "source_bytes":len(source),
      "source_sha256":sha,
      "source_original_ZDIR_checksum_hex":f"{checksum:08x}",
      "EA_data_hash_recalculated_hex":f"{actual_checksum:08x}",
      "EA_data_hash_matches":True,
      "vault_count":n,
      "vaults":vaults,
      "original_frontend_collection_count":len(frontend_rows),
      "original_carparts_root_count":sum(x["matches_carparts_name_hash"] for x in frontend_rows),
      "original_carparts_direct_children_count":len(parts),
      "carparts_name_hash":f"{hash32('carparts'):08x}",
      "carparts_child_name_hashes":[x["name_hash"] for x in parts[:140]],
      "carparts_child_physical_record_offsets":[x["record_offset"] for x in parts[:140]],
      "FECarPartInfo_Level_Rep_Cost_source_schema_known":True,
      "actual_FECarPartInfo_arrays_decoded":False,
      "original_PAL_frontend_resource_equality_verified":False,
      "guest_LOADER_and_shop_cost_runtime_confirmed":False,
      "BMW_purchase_or_install_verified":False,
      "original_game_asset_exported":False,
      "original_game_asset_modified":False,
      "APK_built":False,"save_modified":False,
      "signing_material_accessed":False,
      "safe_to_enable_BMW_tuning":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:res=audit()
    except Exception as exc:
        res={"stage":"PRE521_ORIGINAL_USA_FE_ATTRIB_VPAK_FRONTEND_CARPARTS_STRUCTURE_READONLY",
             "status":"FAILED","error_type":type(exc).__name__,"error":str(exc)[:250],
             "original_game_asset_exported":False,"original_game_asset_modified":False,
             "APK_built":False,"save_modified":False,"signing_material_accessed":False,
             "safe_to_enable_BMW_tuning":False}
    res["run_id"]=a.run_id;res["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(res,indent=2,ensure_ascii=False)+"\n")
    print("PRE521_STATUS",res["status"],flush=True)
    print("PRE521_FRONTEND_COLLECTIONS",res.get("original_frontend_collection_count"),flush=True)
    print("PRE521_CARPARTS_CHILDREN",res.get("original_carparts_direct_children_count"),flush=True)
    print("PRE521_ERROR",res.get("error_type","none"),res.get("error",""),flush=True)
    return 0 if res["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
