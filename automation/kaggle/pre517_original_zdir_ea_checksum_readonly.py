#!/usr/bin/env python3
"""PRE517: verify original ZDIR global-sector offset and length-extended EA CRC.

Algorithm reference (public, pinned blob):
Ekey/NFS.BIN.Tool, NFS.Packer/FileSystem/Package/BinHash.cs
GitHub blob 7d47c9019f7f58981085c5e0d632fdc7362bbc03.
And BinPack.cs blob a6e1c2307c52bd16238bb5f4a8e1451b136d0e5f.

Compare *independently* with authenticated USA ISO VPAK and both original
USA/PAL ZDIR indices. Read-only; do not modify ZIP, ZDIR, ZZDATA, VPAK,
APK, saved profile, or signing key. Results do not establish PAL loader
acceptance of a rebuilt game resource.
"""
from __future__ import annotations
import argparse,hashlib,json,struct
from datetime import datetime,timezone
from pathlib import Path
from pre461_zdir_candidate_hash_names_readonly import raw_zdir,INDEX_SHA,ZZDATA_SIZES
from pre463_usa_vpak_attribute_metadata_readonly import locate
from pre462_usa_raw_iso_attributes_readonly import (
    PARTITION_BASE,EXPECTED_NFS_SECTOR,SECTOR,dir_entries,NAMES
)
from pre465_usa_bmw_vpak_inner_schema_readonly import EXPECTED_VPAK_SHA
OUT=Path("/tmp/nfsmw-pre517/report.json")
POLYNOMIAL=0x04C11DB7
UINT32=0xFFFFFFFF
TARGET_HASH=NAMES["GLOBAL\\ATTRIBUTES.BIN"]
TARGET_SIZE=697856
EXPECTED_CHECKSUM=0x296AD9ED
SOURCE_HASH_BLOB="7d47c9019f7f58981085c5e0d632fdc7362bbc03"
SOURCE_PACK_BLOB="a6e1c2307c52bd16238bb5f4a8e1451b136d0e5f"

def make_crc_table():
    result=[]
    for i in range(256):
        c=(i<<24)&UINT32
        for _ in range(8):
            c=(((c<<1)^POLYNOMIAL) if c&0x80000000 else (c<<1))&UINT32
        result.append(c)
    if result[:4]!=[0x0,0x04C11DB7,0x09823B6E,0x0D4326D9]:
        raise ValueError("Generated data-hash polynomial table differs from public source")
    return result
TABLE=make_crc_table()

def ea_data_hash(raw:bytes):
    crc=UINT32
    for val in raw:
        crc=(TABLE[(val ^ (crc>>24))&0xff] ^ (crc<<8))&UINT32
    length=len(raw)
    # The public packer hashes the integer file length as a succession of
    # little-endian bytes. It uses do/while, so zero length still adds one byte.
    while True:
        crc=(TABLE[(length ^ (crc>>24))&0xff] ^ (crc<<8))&UINT32
        length >>=8
        if not length:break
    return (~crc)&UINT32

def records(blob):
    if len(blob)%24:raise ValueError("Invalid ZDIR record size")
    return [{"index":i,"hash":h,"archive":arc,"sector":sector,
             "total":total,"size":size,"checksum":checksum}
            for i,(h,arc,sector,total,size,checksum)
            in enumerate(struct.iter_unpack("<IiIIiI",blob))]

def validate_total_fields(recs,archive_sizes):
    for key,value in archive_sizes.items():
        if value<0 or value%SECTOR:
            raise ValueError("Unaligned archive byte size")
    count=0;invalid=0;outside=0
    by_archive={}
    for rec in recs:
        arc=rec["archive"]
        if arc not in archive_sizes or rec["sector"]<0 or rec["size"]<0:
            outside+=1;continue
        expected=sum(archive_sizes[j]//SECTOR for j in range(arc))+rec["sector"]
        by_archive.setdefault(str(arc),{"rows":0,"matches":0,"mismatches":0})
        by_archive[str(arc)]["rows"]+=1
        if expected==rec["total"]:
            count+=1;by_archive[str(arc)]["matches"]+=1
        else:
            invalid+=1;by_archive[str(arc)]["mismatches"]+=1
    return {"rows":len(recs),"matching_total_sector_offsets":count,
            "mismatches":invalid,"invalid_archive_rows":outside,
            "all_valid_rows_match":invalid==0 and outside==0,
            "by_archive":by_archive}

def audit():
    previous=json.loads(Path("docs/PRE506_ORIGINAL_PAL_ZDIR_ATTRIBUTE_ALLOCATION_READONLY.json").read_text())
    source=json.loads(Path("docs/PRE503_XBOX_ZZDATA_ATTRIBUTE_SECTOR_SLACK_READONLY.json").read_text())
    if (previous.get("status")!="AUDIT_OK" or
        previous.get("pal_attribute_resource_size",None) not in (None,TARGET_SIZE) or
        previous.get("pal_original_resource_size")!=TARGET_SIZE or
        previous.get("pal_resource_ZDIR_checksum_hex")!="296ad9ed" or
        source.get("status")!="AUDIT_OK" or
        source.get("original_ZDIR_checksum_field_hex")!="296ad9ed"):
        raise ValueError("PRE503/506 source evidence gate failed")

    pal_bytes=raw_zdir()
    if hashlib.sha256(pal_bytes).hexdigest()!=INDEX_SHA:
        raise ValueError("Original PAL ZDIR hash diverged")
    pal=records(pal_bytes)
    if len(pal)!=1390:raise ValueError("Unexpected original PAL record count")
    if any(x not in ZZDATA_SIZES for x in range(10)):
        raise ValueError("Missing original PAL ZZDATA sizes")
    pal_totals=validate_total_fields(pal,ZZDATA_SIZES)
    p=[r for r in pal if r["hash"]==TARGET_HASH]
    if len(p)!=1:raise ValueError("PAL target record ambiguous")
    pt=p[0]
    if (pt["archive"],pt["sector"]*SECTOR,pt["size"],pt["checksum"])!=(4,355932160,TARGET_SIZE,EXPECTED_CHECKSUM):
        raise ValueError("PAL original target tuple changed")

    reader,entry=locate()
    if entry["size"]!=TARGET_SIZE:raise ValueError("USA resource size differs")
    original=reader.read(entry["absolute_offset"],entry["size"])
    sha=hashlib.sha256(original).hexdigest()
    if sha!=EXPECTED_VPAK_SHA:
        raise ValueError("USA reference VPAK does not match PAL authenticated SHA")
    result_hash=ea_data_hash(original)

    tree=reader.read(PARTITION_BASE+EXPECTED_NFS_SECTOR*SECTOR,2048)
    dirs={x["name"].upper():x for x in dir_entries(tree)}
    zz={i:dirs["ZZDATA"+str(i)+".BIN"] for i in range(10)}
    usa_sizes={i:zz[i]["size"] for i in range(10)}
    zdir=dirs["ZDIR.BIN"]
    usa_raw=reader.read(PARTITION_BASE+zdir["sector"]*SECTOR,zdir["size"])
    usa=records(usa_raw)
    usa_totals=validate_total_fields(usa,usa_sizes)
    u=[r for r in usa if r["hash"]==TARGET_HASH]
    if len(u)!=1:raise ValueError("USA target record ambiguous")
    ut=u[0]
    if ut["size"]!=TARGET_SIZE or ut["checksum"]!=EXPECTED_CHECKSUM:
        raise ValueError("Original USA VPAK ZDIR checksum differs from PRE503")
    if ut["sector"]*SECTOR!=entry["offset"] or ut["archive"]!=entry["archive"]:
        raise ValueError("Original USA target sector location mismatch")

    # Sample small, independent resources to distinguish the hash algorithm
    # from a one-off coincidence for ATTRIBUTES.BIN.
    selected=[];covered=set()
    for row in sorted(usa,key=lambda x:(x["size"],x["archive"],x["hash"])):
        arc=row["archive"];size=row["size"]
        if arc not in zz or arc in covered or not (32<=size<=8192):
            continue
        if row["sector"]*SECTOR+size>zz[arc]["size"]:continue
        selected.append(row);covered.add(arc)
        if len(selected)>=5:break
    samples=[]
    for row in selected:
        off=PARTITION_BASE+zz[row["archive"]]["sector"]*SECTOR+row["sector"]*SECTOR
        raw=reader.read(off,row["size"])
        check=ea_data_hash(raw)
        samples.append({"archive":row["archive"],"resource_size":row["size"],
                        "name_hash":f"{row['hash']:08x}",
                        "original_ZDIR_checksum":f"{row['checksum']:08x}",
                        "calculated_length_extended_crc":f"{check:08x}",
                        "matches":check==row["checksum"]})

    pal_total=sum(ZZDATA_SIZES[k]//SECTOR for k in range(4))+pt["sector"]
    usa_total=sum(usa_sizes[k]//SECTOR for k in range(4))+ut["sector"]
    return {
      "stage":"PRE517_ORIGINAL_PAL_USA_ZDIR_TOTAL_SECTOR_AND_EA_DATA_HASH_READONLY",
      "status":"AUDIT_OK",
      "public_reference_repository":"Ekey/NFS.BIN.Tool",
      "public_reference_commit":"ebf30eaa7ee37862254f37b2542107eafd29f7f6",
      "packer_hash_source_git_blob":SOURCE_HASH_BLOB,
      "packer_index_source_git_blob":SOURCE_PACK_BLOB,
      "reference_algorithm":"MSB-first CRC poly 04C11DB7, init FFFFFFFF, append bytewise file length least-significant first, final bitwise NOT",
      "crc_table_generated_from_public_polynomial":True,
      "original_source_vpak_sha256":sha,
      "original_source_vpak_identical_PAL_USA_SHA":True,
      "source_vpak_byte_size":len(original),
      "original_target_checksum_hex":f"{EXPECTED_CHECKSUM:08x}",
      "candidate_data_hash_calculated_hex":f"{result_hash:08x}",
      "candidate_checksum_matches_original_target":result_hash==EXPECTED_CHECKSUM,
      "pal_original_zdir_sha256":INDEX_SHA,
      "pal_original_target_sector_offset":pt["sector"],
      "pal_original_target_total_sector_offset":pt["total"],
      "pal_calculated_total_sector_offset":pal_total,
      "pal_target_total_field_matches_cumulative_sector_formula":pal_total==pt["total"],
      "usa_original_target_sector_offset":ut["sector"],
      "usa_original_target_total_sector_offset":ut["total"],
      "usa_calculated_total_sector_offset":usa_total,
      "usa_target_total_field_matches_cumulative_sector_formula":usa_total==ut["total"],
      "original_pal_ZDIR_offset_field_validation":pal_totals,
      "original_usa_ZDIR_offset_field_validation":usa_totals,
      "small_independent_original_resource_samples":samples,
      "all_samples_match_candidate_hash":bool(samples) and all(x["matches"] for x in samples),
      "original_game_bytes_uploaded":False,
      "game_archive_modified":False,"game_resource_modified":False,
      "ZDIR_modified":False,"APK_built":False,"save_modified":False,
      "signing_key_accessed":False,
      "new_modified_VPAK_loader_acceptance_proven":False,
      "safe_to_build_tuning_APK":False,
      "tuning_enabled":False,
      "original_range_bytes_read":reader.total,
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    a=ap.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as e:
        result={"stage":"PRE517_ORIGINAL_PAL_USA_ZDIR_TOTAL_SECTOR_AND_EA_DATA_HASH_READONLY",
                "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
                "original_game_bytes_uploaded":False,"game_archive_modified":False,
                "game_resource_modified":False,"ZDIR_modified":False,
                "APK_built":False,"save_modified":False,"signing_key_accessed":False,
                "safe_to_build_tuning_APK":False,"tuning_enabled":False}
    result["run_id"]=a.run_id
    result["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE517_STATUS",result["status"],flush=True)
    print("PRE517_DATAHASH_MATCH",result.get("candidate_checksum_matches_original_target"),flush=True)
    print("PRE517_PAL_TOTAL",result.get("pal_target_total_field_matches_cumulative_sector_formula"),flush=True)
    print("PRE517_USA_TOTAL",result.get("usa_target_total_field_matches_cumulative_sector_formula"),flush=True)
    print("PRE517_SMALL_HASH_CONTROLS",len(result.get("small_independent_original_resource_samples",[])),flush=True)
    print("PRE517_ERROR",result.get("error_type","none"),result.get("error",""),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    raise SystemExit(main())
