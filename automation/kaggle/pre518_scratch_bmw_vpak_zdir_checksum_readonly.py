#!/usr/bin/env python3
"""PRE518: fully reparse the synthetic BMW VPAK and test its ZDIR record in RAM.

PRE502's SHA-authenticated reconstruction is consumed only through an opt-in
RAM callback. Compute the original game's verified EA length-extended CRC32
and produce a hypothetical 24-byte index record (size/checksum only changed)
IN MEMORY, then prove all remaining original PAL index entries unchanged.
Never publish rebuilt game bytes, write game assets, alter ZDIR on disk,
rebuild an APK or change any save/signing material.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
from pre502_bmw_engine_combined_level1_scratch import audit as rebuild_bmw
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
from pre461_zdir_candidate_hash_names_readonly import raw_zdir, INDEX_SHA, ZZDATA_SIZES
from pre462_usa_raw_iso_attributes_readonly import NAMES,SECTOR
OUT=Path("/tmp/nfsmw-pre518/report.json")
SIZE_ORIG=697856
SIZE_NEW=698004
SECTOR_COUNT=341
ARCHIVE=4
PAL_LOCAL_OFFSET=355932160
PAL_TOTAL=890205
CHECKSUM_OLD=0x296AD9ED
TARGET_HASH=NAMES["GLOBAL\\ATTRIBUTES.BIN"]
VPAK_SHA="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
REPORTS=[
 ("docs/PRE502_BMW_ENGINE_FULL_LEVEL1_COMBINED_SCRATCH.json","status"),
 ("docs/PRE506_ORIGINAL_PAL_ZDIR_ATTRIBUTE_ALLOCATION_READONLY.json","status"),
 ("docs/PRE517_ORIGINAL_ZDIR_EA_DATA_HASH_AND_TOTAL_OFFSETS_READONLY.json","status")
]
def audit():
    previous={}
    for f,_ in REPORTS:
        d=json.loads(Path(f).read_text())
        if d.get("status")!="AUDIT_OK":raise ValueError("Required previous source proof missing: "+f)
        previous[f]=d
    p502=previous[REPORTS[0][0]]
    p506=previous[REPORTS[1][0]]
    p517=previous[REPORTS[2][0]]
    if (p502.get("source_pal_sha256")!=VPAK_SHA or
        p502.get("scratch_vpak_bytes")!=SIZE_NEW or
        p502.get("safe_to_enable_or_build_tuning") is not False or
        p506.get("pal_original_resource_size")!=SIZE_ORIG or
        p506.get("PRE502_fits_same_sector_count") is not True or
        p506.get("PAL_padding_byte_values_verified") is not False or
        p517.get("original_source_vpak_sha256")!=VPAK_SHA or
        p517.get("candidate_checksum_matches_original_target") is not True or
        p517.get("all_samples_match_candidate_hash") is not True or
        p517["original_pal_ZDIR_offset_field_validation"].get("all_valid_rows_match") is not True or
        p517["original_usa_ZDIR_offset_field_validation"].get("all_valid_rows_match") is not True):
        raise ValueError("Original PAL/USA and PRE502 proof boundary changed")

    zdir=raw_zdir()
    if hashlib.sha256(zdir).hexdigest()!=INDEX_SHA or len(zdir)!=1390*24:
        raise ValueError("Original PAL index hash/record count unexpected")
    matches=[]
    for i,(h,arc,sector,total,size,hash_value) in enumerate(struct.iter_unpack("<IiIIiI",zdir)):
        if h==TARGET_HASH:matches.append((i,h,arc,sector,total,size,hash_value))
    if len(matches)!=1:raise ValueError("PAL target ZDIR record ambiguous")
    i,h,arc,sector,total,size,old_hash=matches[0]
    if (i,arc,sector*SECTOR,total,size,old_hash)!=(
        806,ARCHIVE,PAL_LOCAL_OFFSET,PAL_TOTAL,SIZE_ORIG,CHECKSUM_OLD):
        raise ValueError("Original PAL ATTRIBUTES.BIN ZDIR tuple differs")
    reserved=SECTOR_COUNT*SECTOR
    if reserved!=698368 or SIZE_ORIG>reserved or SIZE_NEW>reserved:
        raise ValueError("Synthetic VPAK does not fit existing sector allocation")
    if (sum(ZZDATA_SIZES[k]//SECTOR for k in range(ARCHIVE))+sector)!=total:
        raise ValueError("PAL total sector offset formula mismatch")

    def ram_only_consumer(scratch:bytes)->dict:
        if len(scratch)!=SIZE_NEW or scratch[:4]!=b"VPAK":
            raise ValueError("Unrecognized synthetic BMW VPAK RAM bytes")
        custom_hash=ea_data_hash(scratch)
        scratch_sha=hashlib.sha256(scratch).hexdigest()
        # Build a new index record only as a Python bytearray (never exported).
        simulated=bytearray(zdir)
        off=i*24
        original_record=zdir[off:off+24]
        struct.pack_into("<i",simulated,off+16,SIZE_NEW)
        struct.pack_into("<I",simulated,off+20,custom_hash)
        new_record=bytes(simulated[off:off+24])
        head_old=struct.unpack("<IiIIiI",original_record)
        head_new=struct.unpack("<IiIIiI",new_record)
        if head_old[:4]!=head_new[:4] or head_old[4]!=SIZE_ORIG or head_new[4]!=SIZE_NEW:
            raise ValueError("Hypothetical ZDIR changed identity, archive or sector location")
        if head_new[5]!=custom_hash or head_old[5]!=CHECKSUM_OLD:
            raise ValueError("Candidate EA checksum placement inconsistent")
        differing=[n for n,(a,b) in enumerate(zip(zdir,simulated)) if a!=b]
        allowed=set(range(off+16,off+24))
        if not differing or not set(differing)<=allowed:
            raise ValueError("Candidate ZDIR changed unrelated original bytes")
        if zdir[:off]!=simulated[:off] or zdir[off+24:]!=simulated[off+24:]:
            raise ValueError("Other original PAL ZDIR entries changed")
        if len(simulated)!=len(zdir):
            raise ValueError("ZDIR layout grew unexpectedly")
        if custom_hash==CHECKSUM_OLD:
            # Unlikely but would require independent explanation.
            raise ValueError("Synthetic VPAK generated unchanged checksum unexpectedly")
        return {
          "synthetic_scratch_VPAK_sha256":scratch_sha,
          "synthetic_scratch_VPAK_bytes":len(scratch),
          "synthetic_scratch_EA_data_hash_hex":f"{custom_hash:08x}",
          "candidate_ZDIR_record_sha256":hashlib.sha256(new_record).hexdigest(),
          "original_ZDIR_record_sha256":hashlib.sha256(original_record).hexdigest(),
          "candidate_ZDIR_size_field":head_new[4],
          "candidate_ZDIR_checksum_field_hex":f"{head_new[5]:08x}",
          "unchanged_ZDIR_fields":["name_hash","archive_id","local_sector","global_sector"],
          "all_other_original_PAL_ZDIR_entries_bytewise_unchanged":True,
          "other_ZDIR_bytes_unchanged":len(zdir)-len(allowed),
          "changed_candidate_byte_positions_relative_to_ZDIR_record":[n-off for n in differing],
          "original_sector_capacity_bytes":reserved,
          "synthetic_remaining_sector_bytes":reserved-len(scratch),
          "synthetic_VPAK_not_exported":True,
          "hypothetical_ZDIR_not_exported":True
        }
    reconstructed=rebuild_bmw(consume_scratch=ram_only_consumer)
    scratch_meta=reconstructed.pop("_private_scratch_analysis",None)
    if (reconstructed.get("status")!="AUDIT_OK" or scratch_meta is None or
        reconstructed.get("scratch_vpak_bytes")!=SIZE_NEW or
        reconstructed.get("new_engine_ExpN_RefSpec_PtrN_reparsed") is not True or
        reconstructed.get("source_pal_sha256")!=VPAK_SHA or
        reconstructed.get("safe_to_enable_or_build_tuning") is not False):
        raise ValueError("PRE502 repeated scratch reconstruction not authenticated")
    if reconstructed.get("engine_synthetic_gain_percent")!=5.0:
        raise ValueError("PRE502 only synthetic vector unexpectedly changed")
    return {
      "stage":"PRE518_BMW_ENGINE_LEVEL1_RAM_VPAK_ZDIR_NEW_EA_CHECKSUM",
      "status":"AUDIT_OK",
      "original_source_pal_sha256":VPAK_SHA,
      "source_PAL_ZDIR_sha256":INDEX_SHA,
      "source_PAL_archive_number":ARCHIVE,
      "source_PAL_resource_ZDIR_row_index":i,
      "source_PAL_resource_offset_bytes":PAL_LOCAL_OFFSET,
      "source_PAL_global_sector_field":total,
      "source_PAL_VPAK_size":SIZE_ORIG,
      "source_PAL_checksum_field_hex":f"{CHECKSUM_OLD:08x}",
      "original_PAL_ZDIR_total_semantics_reverified":True,
      "PAL_and_USA_ZDIR_offset_semantics_pre517_verified":True,
      "new_engine_is_synthetic_only_not_user_calibration":True,
      "new_engine_guest_loader_acceptance_proven":False,
      "new_engine_price_catalog_FEPartInfo_proven":False,
      "BMW_runtime_purchase_and_persistence_proven":False,
      "ZDIR_checksum_update_mechanics_proven_in_ram":True,
      "source_PAL_ZZDATA4_padding_bytes_proven_zero":False,
      "original_ZZDATA4_contents_accessed":False,
      "game_data_published":False,
      "game_data_modified":False,
      "ZDIR_file_written":False,
      "ZZDATA_file_written":False,
      "APK_built":False,"save_modified":False,
      "signing_material_accessed":False,
      "safe_to_build_tuning_APK":False,
      "tuning_enabled":False,
      **scratch_meta
    }

def main():
    a=argparse.ArgumentParser();a.add_argument("--run-id",required=True)
    args=a.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as exc:
        result={"stage":"PRE518_BMW_ENGINE_LEVEL1_RAM_VPAK_ZDIR_NEW_EA_CHECKSUM",
           "status":"FAILED","error_type":type(exc).__name__,
           "error":str(exc)[:220],
           "game_data_published":False,"game_data_modified":False,
           "ZDIR_file_written":False,"ZZDATA_file_written":False,
           "APK_built":False,"save_modified":False,
           "signing_material_accessed":False,
           "safe_to_build_tuning_APK":False,"tuning_enabled":False}
    result["run_id"]=args.run_id
    result["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PRE518_STATUS",result["status"],flush=True)
    print("PRE518_SYNTHETIC_EA_CHECKSUM",result.get("synthetic_scratch_EA_data_hash_hex"),flush=True)
    print("PRE518_NEW_SECTOR_PADDING",result.get("synthetic_remaining_sector_bytes"),flush=True)
    print("PRE518_ERROR",result.get("error_type","none"),result.get("error",""),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":
    raise SystemExit(main())
