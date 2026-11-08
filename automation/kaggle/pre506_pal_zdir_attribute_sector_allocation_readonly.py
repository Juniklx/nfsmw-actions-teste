#!/usr/bin/env python3
"""PRE506: read-only PAL ZDIR/ZZDATA4 allocation metadata vs reference USA.

Uses authenticated PRE460 small ZDIR from user's PAL ZIP and PRE467 verified
PAL ATTRIBUTES.BIN position/SHA. Does not fetch PAL ZZDATA game bytes, cannot
prove contents of padding; never modifies archives, APK, saves, or signing.
"""
from __future__ import annotations
import argparse,json,struct
from datetime import datetime,timezone
from pathlib import Path
from pre461_zdir_candidate_hash_names_readonly import raw_zdir,INDEX_SHA,ZZDATA_SIZES
from pre462_usa_raw_iso_attributes_readonly import NAMES,SECTOR

OUT=Path("/tmp/nfsmw-pre506/report.json")
EXPECTED_OFFSET=355932160
EXPECTED_SIZE=697856
def audit():
    prior=json.loads(Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json").read_text())
    usa=json.loads(Path("docs/PRE503_XBOX_ZZDATA_ATTRIBUTE_SECTOR_SLACK_READONLY.json").read_text())
    scratch=json.loads(Path("docs/PRE502_BMW_ENGINE_FULL_LEVEL1_COMBINED_SCRATCH.json").read_text())
    if (prior.get("status")!="AUDIT_OK"
       or prior.get("pal_resource_identical_to_usa_reference") is not True
       or prior.get("pal_target_size_bytes")!=EXPECTED_SIZE
       or usa.get("status")!="AUDIT_OK"
       or scratch.get("status")!="AUDIT_OK"
       or scratch.get("scratch_vpak_bytes")!=698004
       or scratch.get("safe_to_enable_or_build_tuning") is not False):
        raise ValueError("PRE467/502/503 source evidence mismatch")
    data=raw_zdir()
    import hashlib
    if hashlib.sha256(data).hexdigest()!=INDEX_SHA or len(data)%24:
        raise ValueError("PAL ZDIR original hash/record length mismatch")
    records=[(i,*row) for i,row in enumerate(struct.iter_unpack("<IiIIiI",data))]
    matches=[r for r in records if r[1]==NAMES["GLOBAL\\ATTRIBUTES.BIN"]]
    if len(matches)!=1:raise ValueError("PAL ZDIR ATTRIBUTES.BIN identity ambiguous")
    i,h,archive,sector,total,size,checksum=matches[0]
    offset=sector*SECTOR
    if (archive,offset,size)!=(4,EXPECTED_OFFSET,EXPECTED_SIZE):
        raise ValueError("PAL Attributes entry differs from authenticated PRE467")
    reserved=((size+SECTOR-1)//SECTOR)*SECTOR
    upgrade_size=scratch["scratch_vpak_bytes"]
    successors=[r for r in records if r[2]==archive and r[3]*SECTOR>offset]
    next_start=min((r[3]*SECTOR for r in successors),default=None)
    within_archive=offset+reserved<=ZZDATA_SIZES[archive]
    next_nonoverlap=next_start is None or next_start>=offset+reserved
    if not within_archive or not next_nonoverlap:
        raise ValueError("PAL resource sector allocation overlaps another ZDIR entry")
    return {
       "stage":"PRE506_ORIGINAL_PAL_ZDIR_BMW_ATTRIBUTES_ARCHIVE_ALLOCATION",
       "status":"AUDIT_OK","pal_zdir_sha256":INDEX_SHA,
       "pal_ZDIR_records":len(records),
       "pal_attribute_resource_name_hash":f"{h:08x}",
       "pal_attribute_ZDIR_row_index":i,
       "pal_attribute_archive_number":archive,
       "pal_attribute_byte_offset":offset,
       "pal_original_resource_size":size,
       "pal_resource_ZDIR_total_field":total,
       "pal_resource_ZDIR_checksum_hex":f"{checksum:08x}",
       "usa_reference_ZDIR_checksum_hex":usa.get("original_ZDIR_checksum_field_hex"),
       "PAL_USA_same_target_resource_SHA":True,
       "PAL_USA_ZDIR_checksum_equal":f"{checksum:08x}"==usa.get("original_ZDIR_checksum_field_hex"),
       "pal_ZZDATA4_total_bytes":ZZDATA_SIZES[archive],
       "sector_size":SECTOR,
       "reserved_sector_bytes":reserved,
       "unused_allocated_sector_bytes":reserved-size,
       "PRE502_candidate_size":upgrade_size,
       "PRE502_fits_same_sector_count":upgrade_size<=reserved,
       "candidate_remaining_sector_bytes":reserved-upgrade_size,
       "next_ZDIR_resource_offset":next_start,
       "next_resource_nonoverlapping":next_nonoverlap,
       "PAL_padding_byte_values_verified":False,
       "PAL_Loader_acceptance_or_checksum_algorithm_verified":False,
       "original_ZDIR_size_checksum_modification_approved":False,
       "PAL_ZZDATA_bytes_read":False,"modified_ZDIR_written":False,
       "modified_ZZDATA_written":False,"game_asset_uploaded":False,
       "APK_built":False,"save_modified":False,"signing_accessed":False,
       "tuning_enabled":False
    }
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    args=ap.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as exc:
        r={"stage":"PRE506_ORIGINAL_PAL_ZDIR_BMW_ATTRIBUTES_ARCHIVE_ALLOCATION",
           "status":"FAILED","error_type":type(exc).__name__,"error":str(exc)[:240],
           "PAL_ZZDATA_bytes_read":False,"modified_ZDIR_written":False,
           "modified_ZZDATA_written":False,"APK_built":False,
           "save_modified":False,"signing_accessed":False,"tuning_enabled":False}
    r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE506_STATUS",r["status"],flush=True)
    print("PRE506_PAL_SECTOR_SLACK",r.get("unused_allocated_sector_bytes"),flush=True)
    print("PRE506_PAL_USA_CHECKSUM_EQUAL",r.get("PAL_USA_ZDIR_checksum_equal"),flush=True)
    print("PRE506_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
