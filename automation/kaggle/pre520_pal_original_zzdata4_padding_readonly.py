#!/usr/bin/env python3
"""PRE520: verify ACTUAL PAL ZZDATA4 sector padding immediately after ATTRIBUTES.BIN.

Reuses PRE467's authenticated strict-HTTP206 ZIP member stream and full-member
CRC. Collects ONLY the 697,856-byte original resource + 512-byte sector slack
in transient memory, never stores or publishes raw bytes.
No ISO, ZIP, ZDIR, ZZDATA, APK or saved profile is modified.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
from pre459_pal_zip_car_catalog_readonly import session,read_range,SIZE
from pre467_pal_zip4_attributes_vpak_authenticated import (
    LOCAL_OFFSET,ZNAME,COMPRESSED,UNCOMPRESSED,CRC,TARGET_START,
    TARGET_LENGTH,EXPECTED_USA_SHA,read_streamed_member
)
from pre461_zdir_candidate_hash_names_readonly import INDEX_SHA
OUT=Path("/tmp/nfsmw-pre520/report.json")
SECTOR=2048
SECTOR_COUNT=341
RESERVED=SECTOR*SECTOR_COUNT
PADDING=RESERVED-TARGET_LENGTH
PAL_ZDIR_RECORD_INDEX=806
SOURCE_ARCHIVE=4
EXPECTED_NEXT_ENTRY=356630528

def audit():
    earlier=json.loads(Path("docs/PRE506_ORIGINAL_PAL_ZDIR_ATTRIBUTE_ALLOCATION_READONLY.json").read_text())
    parent=json.loads(Path("docs/PRE467_PAL_BMW_ATTRIBUTES_BINARY_IDENTITY.json").read_text())
    zdir_proof=json.loads(Path("docs/PRE518_BMW_RAM_VPAK_ZDIR_CHECKSUM_READONLY.json").read_text())
    if (earlier.get("status")!="AUDIT_OK"
        or earlier.get("pal_zdir_sha256")!=INDEX_SHA
        or earlier.get("pal_ZDIR_records")!=1390
        or earlier.get("pal_attribute_ZDIR_row_index")!=PAL_ZDIR_RECORD_INDEX
        or earlier.get("pal_attribute_archive_number")!=SOURCE_ARCHIVE
        or earlier.get("pal_attribute_byte_offset")!=TARGET_START
        or earlier.get("pal_original_resource_size")!=TARGET_LENGTH
        or earlier.get("next_ZDIR_resource_offset")!=EXPECTED_NEXT_ENTRY
        or earlier.get("PAL_padding_byte_values_verified") is not False
        or parent.get("status")!="AUDIT_OK"
        or parent.get("pal_target_sha256")!=EXPECTED_USA_SHA
        or parent.get("pal_resource_identical_to_usa_reference") is not True
        or zdir_proof.get("status")!="AUDIT_OK"
        or zdir_proof.get("source_PAL_resource_ZDIR_row_index")!=PAL_ZDIR_RECORD_INDEX
        or zdir_proof.get("candidate_ZDIR_size_field")!=698004
        or zdir_proof.get("safe_to_build_tuning_APK") is not False
        or PADDING!=512
        or TARGET_START+RESERVED!=EXPECTED_NEXT_ENTRY):
        raise ValueError("PRE467/506/518 source provenance or exact sector bounds changed")

    sess=session()
    metadata=sess.get("https://www.googleapis.com/drive/v3/files/1sF5irZpUNfN5Z2p4L53eMVISBeh8MfRz",
        params={"fields":"id,size,name"},timeout=35).json()
    if (metadata.get("id")!="1sF5irZpUNfN5Z2p4L53eMVISBeh8MfRz"
        or int(metadata.get("size",0))!=SIZE or metadata.get("name")!="NFSMW_PAL.zip"):
        raise ValueError("PAL ZIP identity/size changed")

    h=read_range(sess,LOCAL_OFFSET,30)
    if len(h)!=30 or h[:4]!=b"PK\x03\x04":
        raise ValueError("PAL ZIP member local header mismatch")
    (_sig,_ver,flags,method,_tm,_date,crc,csize,usize,nlen,xlen)=struct.unpack("<IHHHHHIIIHH",h)
    if (method!=8 or flags&1 or nlen>80 or xlen>1000
        or crc not in (0,CRC) or csize not in (0,COMPRESSED)
        or usize not in (0,UNCOMPRESSED)):
        raise ValueError("PAL ZZDATA4 compressed member metadata mismatch")
    if read_range(sess,LOCAL_OFFSET+30,nlen)!=ZNAME:
        raise ValueError("ZIP local file name differs")
    offset=LOCAL_OFFSET+30+nlen+xlen
    padded,stats=read_streamed_member(sess,offset,target_length=RESERVED)
    if len(padded)!=RESERVED:
        raise ValueError("PAL reserved sector region not exactly collected")
    original=padded[:TARGET_LENGTH]
    pad=padded[TARGET_LENGTH:]
    source_hash=hashlib.sha256(original).hexdigest()
    if (source_hash!=EXPECTED_USA_SHA or original[:4]!=b"VPAK"
        or stats.get("zzdata_member_crc32")!=f"{CRC:08x}"
        or stats.get("total_deflated_bytes")!=UNCOMPRESSED):
        raise ValueError("PAL source VPAK checksum / ZIP full-member CRC mismatch")
    observed_padding_sha256=hashlib.sha256(pad).hexdigest()
    zero_bytes=pad.count(0)
    true_zero=zero_bytes==PADDING
    return {
        "stage":"PRE520_ORIGINAL_PAL_ZZDATA4_BMW_VPAK_512_BYTE_PADDING_READONLY",
        "status":"AUDIT_OK",
        "source_zip_drive_id":"1sF5irZpUNfN5Z2p4L53eMVISBeh8MfRz",
        "original_zip_size":SIZE,
        "original_zip_member":"NFS/ZZDATA4.BIN",
        "full_member_crc32_verified":True,
        "full_member_uncompressed_size_verified":True,
        "original_PAL_ZZDATA4_member_bytes":UNCOMPRESSED,
        "original_PAL_ZZDATA4_member_CRC32":f"{CRC:08x}",
        "original_PAL_resource_ZDIR_index":PAL_ZDIR_RECORD_INDEX,
        "original_PAL_resource_archive":SOURCE_ARCHIVE,
        "original_PAL_resource_byte_offset":TARGET_START,
        "original_PAL_VPAK_bytes":len(original),
        "original_PAL_VPAK_sha256":source_hash,
        "sector_bytes":SECTOR,
        "reserved_sector_bytes":RESERVED,
        "original_padding_bytes":len(pad),
        "original_padding_zero_byte_count":zero_bytes,
        "original_padding_all_zero":true_zero,
        "original_padding_sha256":observed_padding_sha256,
        "candidate_synthetic_vpak_bytes":698004,
        "candidate_remaining_bytes":RESERVED-698004,
        "hypothetical_in_place_sector_allocation_feasible":true_zero,
        "ranged_zip_requests":stats.get("http_range_calls"),
        "compressed_bytes_authenticated":stats.get("compressed_bytes_read"),
        "raw_game_asset_written":False,"original_zip_or_ZZDATA_modified":False,
        "original_ZDIR_modified":False,"VPAK_overlay_created":False,
        "APK_built":False,"save_modified":False,"signing_accessed":False,
        "original_loader_acceptance_proven":False,
        "FE_shop_purchase_catalog_verified":False,
        "ready_to_modify_original_game":False,
        "BMW_tuning_enabled":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try: report=audit()
    except Exception as exc:
        report={"stage":"PRE520_ORIGINAL_PAL_ZZDATA4_BMW_VPAK_512_BYTE_PADDING_READONLY",
                "status":"FAILED","error_type":type(exc).__name__,
                "error":str(exc)[:240],"raw_game_asset_written":False,
                "original_zip_or_ZZDATA_modified":False,"original_ZDIR_modified":False,
                "VPAK_overlay_created":False,"APK_built":False,"save_modified":False,
                "signing_accessed":False,"ready_to_modify_original_game":False,
                "BMW_tuning_enabled":False}
    report["run_id"]=args.run_id
    report["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print("PRE520_STATUS",report["status"],flush=True)
    print("PRE520_PAL_PADDING_ALL_ZERO",report.get("original_padding_all_zero"),flush=True)
    print("PRE520_CANDIDATE_PAL_SECTOR_FEASIBLE",report.get("hypothetical_in_place_sector_allocation_feasible"),flush=True)
    print("PRE520_ERROR",report.get("error_type","none"),report.get("error",""),flush=True)
    return 0 if report["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
