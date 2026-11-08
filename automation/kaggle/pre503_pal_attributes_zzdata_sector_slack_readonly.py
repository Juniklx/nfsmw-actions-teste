#!/usr/bin/env python3
"""PRE503 original Xbox 360 XDVDFS ZZDATA attribute resource sector slack.

Check whether PRE502's fully re-parsed synthetic VPAK (698004 bytes) fits
within original GLOBAL/ATTRIBUTES.BIN archive sectors without moving later
resources, and compare the actual ZDIR CRC field against zlib CRC32 of
SHA-verified original bytes. Entire operation READ ONLY; no ISO, APK, save
or game resource bytes are written to disk or output.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,zlib
from datetime import datetime,timezone
from pathlib import Path
from pre462_usa_raw_iso_attributes_readonly import (
    PARTITION_BASE,EXPECTED_NFS_SECTOR,SECTOR,dir_entries,NAMES)
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA

OUT=Path("/tmp/nfsmw-pre503/report.json")
ORIGINAL_SIZE=697856
TARGET=NAMES["GLOBAL\\ATTRIBUTES.BIN"]
def sha(data):return hashlib.sha256(data).hexdigest()
def audit():
    prior=json.loads(Path("docs/PRE502_BMW_ENGINE_FULL_LEVEL1_COMBINED_SCRATCH.json").read_text())
    if (prior.get("status")!="AUDIT_OK" or
        prior.get("source_pal_sha256")!=EXPECTED_VPAK_SHA or
        prior.get("combined_new_engine_physical_collection_RefSpec_and_level1_in_one_VPAK") is not True or
        prior.get("safe_to_enable_or_build_tuning") is not False):
        raise ValueError("PRE502 authenticated scratch repack metadata unavailable")
    rebuilt_size=prior["scratch_vpak_bytes"]
    if rebuilt_size!=698004 or rebuilt_size<=ORIGINAL_SIZE:
        raise ValueError("PRE502 scratch total length changed unexpectedly")
    reader,entry=locate()
    if entry["size"]!=ORIGINAL_SIZE:
        raise ValueError("Original ZDIR resource size differs from PRE467")
    raw=reader.read(entry["absolute_offset"],entry["size"])
    if sha(raw)!=EXPECTED_VPAK_SHA:raise ValueError("Original PAL/USA-identical VPAK SHA mismatch")
    tree=reader.read(PARTITION_BASE+EXPECTED_NFS_SECTOR*SECTOR,2048)
    files={x["name"].upper():x for x in dir_entries(tree)}
    z=files.get("ZDIR.BIN")
    zz=files.get("ZZDATA"+str(entry["archive"])+".BIN")
    if not z or not zz or z["is_dir"] or zz["is_dir"]:
        raise ValueError("Missing XDVDFS original resource/archive entry")
    zdir=reader.read(PARTITION_BASE+z["sector"]*SECTOR,z["size"])
    if len(zdir)%24:
        raise ValueError("ZDIR record table bounds mismatch")
    recs=[]
    for i,(h,arc,sector,total,size,checksum) in enumerate(struct.iter_unpack("<IiIIiI",zdir)):
        if arc!=entry["archive"]:continue
        recs.append({"index":i,"hash":h,"archive":arc,
                     "sector":sector,"bytes_offset":sector*SECTOR,
                     "size":size,"total":total,"checksum":checksum})
    expected=[x for x in recs if x["hash"]==TARGET
              and x["bytes_offset"]==entry["offset"] and x["size"]==ORIGINAL_SIZE]
    if len(expected)!=1:raise ValueError("Original resource ZDIR tuple not unique")
    found=expected[0]
    archive_off=PARTITION_BASE+zz["sector"]*SECTOR
    if archive_off+found["bytes_offset"]!=entry["absolute_offset"]:
        raise ValueError("Absolute original resource location no longer matches ZDIR")
    sector_count=(ORIGINAL_SIZE+SECTOR-1)//SECTOR
    reserved=sector_count*SECTOR
    remainder=reserved-ORIGINAL_SIZE
    new_remainder=reserved-rebuilt_size
    if new_remainder<0:raise ValueError("Synthetic rebuilt resource exceeds existing sector allocation")
    if found["bytes_offset"]+reserved>zz["size"]:
        raise ValueError("Original resource sector padding outside ZZDATA")
    successors=[x for x in recs if x["bytes_offset"]>found["bytes_offset"]]
    successor=min(successors,key=lambda x:x["bytes_offset"]) if successors else None
    if successor and successor["bytes_offset"]<found["bytes_offset"]+reserved:
        raise ValueError("Next ZDIR record overlaps original reserved sectors")
    original_padding=reader.read(entry["absolute_offset"]+ORIGINAL_SIZE,remainder)
    if len(original_padding)!=remainder:
        raise ValueError("Archive resource padding truncated")
    padded_zero=not any(original_padding)
    checksum_calc=zlib.crc32(raw)&0xffffffff
    end_file=entry["absolute_offset"]+reserved
    return {
        "stage":"PRE503_PAL_XXDATA_ATTRIBUTE_RESOURCE_SECTOR_SLACK",
        "status":"AUDIT_OK",
        "original_vpak_source_sha256":EXPECTED_VPAK_SHA,
        "source_attribute_bytes":ORIGINAL_SIZE,
        "PRE502_scratch_rebuild_bytes":rebuilt_size,
        "candidate_resource_growth_bytes":rebuilt_size-ORIGINAL_SIZE,
        "original_sector_size_bytes":SECTOR,
        "original_sector_count":sector_count,
        "original_reserved_sector_bytes":reserved,
        "original_sector_padding_bytes":remainder,
        "scratch_remaining_sector_padding_bytes":new_remainder,
        "original_padding_all_zero":padded_zero,
        "original_data_archive_ZZDATA_number":found["archive"],
        "source_archive_file_bytes":zz["size"],
        "original_resource_archive_byte_offset":found["bytes_offset"],
        "original_resource_ZDIR_row":found["index"],
        "next_resource_in_same_archive_record_offset":successor["bytes_offset"] if successor else None,
        "next_resource_starts_after_reserved_sectors":
             successor is None or successor["bytes_offset"]>=found["bytes_offset"]+reserved,
        "candidate_within_existing_sector_allocation":rebuilt_size<=reserved,
        "original_ZDIR_resource_size_field":found["size"],
        "original_ZDIR_resource_total_field":found["total"],
        "original_ZDIR_checksum_field_hex":f"{found['checksum']:08x}",
        "crc32_original_attribute_resource_hex":f"{checksum_calc:08x}",
        "original_ZDIR_checksum_matches_zlib_crc32":checksum_calc==found["checksum"],
        "ZDIR_checksum_semantics_corroborated_by_other_resources":False,
        "ZDIR_size_and_checksum_would_require_revalidation_if_replacing":True,
        "archive_sector_storage_feasible_if_padded_zero":
            rebuilt_size<=reserved and padded_zero,
        "VPAK_loader_accepts_larger_resource_verified":False,
        "ZIP_PAL_archive_same_allocation_verified":False,
        "modded_ZDIR_written":False,
        "modded_ZZDATA_written":False,
        "modded_GAME_resource_published":False,
        "APK_generated":False,"save_modified":False,"tuning_enabled":False,
        "source_data_ranges_read":reader.total
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE503_PAL_XXDATA_ATTRIBUTE_RESOURCE_SECTOR_SLACK",
        "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:240],
        "modded_ZDIR_written":False,"modded_ZZDATA_written":False,
        "modded_GAME_resource_published":False,"APK_generated":False,
        "save_modified":False,"tuning_enabled":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE503_STATUS",r["status"],flush=True)
    print("PRE503_SECTOR_SLACK",r.get("original_sector_padding_bytes"),flush=True)
    print("PRE503_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
