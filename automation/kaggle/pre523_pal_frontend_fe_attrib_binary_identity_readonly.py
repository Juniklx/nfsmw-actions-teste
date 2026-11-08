#!/usr/bin/env python3
"""PRE523: authenticate PAL FE_ATTRIB.BIN against USA original, READ ONLY.

The FE price catalogue parsed in PRE521/PRE522 was from a SHA-pinned USA ISO.
This audit independently reads the true PAL copy stored in user's 5.56GB
NFSMW_PAL.zip -> NFS/ZZDATA0.BIN via strict HTTP206, validates the full
ZIP member's Deflate CRC32/size and compares the FE resource SHA/EA checksum.
No archive extracted to disk; no game resource bytes ever leave runner.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,zlib
from datetime import datetime,timezone
from pathlib import Path
from pre459_pal_zip_car_catalog_readonly import session,read_range,SIZE
from pre461_zdir_candidate_hash_names_readonly import raw_zdir,INDEX_SHA,ZZDATA_SIZES
from pre462_usa_raw_iso_attributes_readonly import NAMES,SECTOR
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
OUT=Path("/tmp/nfsmw-pre523/report.json")
ZIP_ID="1sF5irZpUNfN5Z2p4L53eMVISBeh8MfRz"
LOCAL_OFFSET=2772526743
NAME=b"NFS/ZZDATA0.BIN"
COMPRESSED=225288232
UNCOMPRESSED=369948672
CRC=0x11D904BA
CHUNK_SIZE=4*1024*1024
RESOURCE="GLOBAL\\FE_ATTRIB.BIN"
TARGET_HASH=NAMES[RESOURCE]
USA_SHA="8ac09099cfc98646bbfbdb261d28b9648e3ec8b0d6bdf9d3edd6ef7bc967b528"
USA_SIZE=113856
USA_EA_CHECKSUM=0x4EC7ACF5
MAX_TARGET=1024*1024

def audit():
    source=json.loads(Path("docs/PRE521_USA_FE_ATTRIB_FRONTEND_CARPARTS_STRUCTURE_READONLY.json").read_text())
    costs=json.loads(Path("docs/PRE522_USA_FE_CARPARTS_COST_ARRAYS_READONLY.json").read_text())
    if (source.get("status")!="AUDIT_OK" or source.get("source_sha256")!=USA_SHA
        or source.get("source_original_ZDIR_checksum_hex")!=f"{USA_EA_CHECKSUM:08x}"
        or source.get("source_bytes")!=USA_SIZE
        or source.get("original_carparts_direct_children_count")!=21
        or costs.get("status")!="AUDIT_OK"
        or costs.get("original_FE_ATTRIB_sha256")!=USA_SHA
        or costs.get("children_with_valid_FECarPartInfo_array")!=21
        or costs.get("actual_BMW_shop_cost_or_purchase_verified") is not False):
        raise ValueError("PRE521/PRE522 authenticated USA frontend evidence missing")

    z=raw_zdir()
    if len(z)!=1390*24 or hashlib.sha256(z).hexdigest()!=INDEX_SHA:
        raise ValueError("Original PAL ZDIR identity mismatch")
    matches=[(i,arc,sec,glob,size,crc) for i,(h,arc,sec,glob,size,crc)
             in enumerate(struct.iter_unpack("<IiIIiI",z)) if h==TARGET_HASH]
    if len(matches)!=1:raise ValueError("PAL FE_ATTRIB ZDIR resource missing/duplicated")
    row,archive,sector,total,size,checksum=matches[0]
    if archive!=0 or not (1000<size<=MAX_TARGET) or sector*SECTOR+size>ZZDATA_SIZES[0]:
        raise ValueError("PAL FE resource is not safely in expected ZZDATA0 archive")
    want_start=sector*SECTOR
    want_end=want_start+size
    expected_total=sector # archive zero has no previous sectors
    if total!=expected_total:raise ValueError("PAL global/local sector mismatch")
    with session() as sess:
        meta=sess.get("https://www.googleapis.com/drive/v3/files/"+ZIP_ID,
              params={"fields":"id,name,size"},timeout=35).json()
        if (meta.get("id")!=ZIP_ID or int(meta.get("size",0))!=SIZE
            or meta.get("name")!="NFSMW_PAL.zip"):
            raise ValueError("PAL ZIP metadata identity or size mismatch")
        header=read_range(sess,LOCAL_OFFSET,30)
        if header[:4]!=b"PK\x03\x04":
            raise ValueError("PAL ZIP member local header not found")
        (_sig,_ver,flags,method,_tm,_dt,hcrc,hcsize,husize,nlen,xlen)=struct.unpack("<IHHHHHIIIHH",header)
        if (method!=8 or flags&1 or nlen>80 or xlen>1000
            or hcrc not in (0,CRC) or hcsize not in (0,COMPRESSED)
            or husize not in (0,UNCOMPRESSED)):
            raise ValueError("Original PAL ZZDATA0 ZIP member fields unexpected")
        if read_range(sess,LOCAL_OFFSET+30,nlen)!=NAME:
            raise ValueError("PAL ZIP target member name changed")
        start=LOCAL_OFFSET+30+nlen+xlen
        if start+COMPRESSED>SIZE:raise ValueError("PAL ZIP member compressed bounds invalid")
        inflater=zlib.decompressobj(-15)
        out=bytearray(size)
        got=0;plain_cursor=0;crc=0;cursor=0;requests=0
        while cursor<COMPRESSED:
            num=min(CHUNK_SIZE,COMPRESSED-cursor)
            first=start+cursor;last=first+num-1
            with sess.get("https://www.googleapis.com/drive/v3/files/"+ZIP_ID,
                params={"alt":"media"},headers={"Range":f"bytes={first}-{last}"},
                stream=True,timeout=(25,90),allow_redirects=False) as response:
                if response.status_code!=206:
                    raise ValueError("Strict HTTP206 ZIP range rejected "+str(response.status_code))
                if response.headers.get("Content-Range","")!=f"bytes {first}-{last}/{SIZE}":
                    raise ValueError("Original PAL ZIP content-range mismatch")
                part=response.raw.read(num+1,decode_content=False)
            if len(part)!=num:raise ValueError("Short/long compressed ZIP response")
            if inflater.eof:raise ValueError("Deflate ended before source member boundary")
            plain=inflater.decompress(part)
            crc=zlib.crc32(plain,crc)
            lo=max(want_start,plain_cursor);hi=min(want_end,plain_cursor+len(plain))
            if hi>lo:
                out[lo-want_start:hi-want_start]=plain[lo-plain_cursor:hi-plain_cursor]
                got+=hi-lo
            plain_cursor+=len(plain);cursor+=num;requests+=1
            if requests%16==0:
                print("PRE523_CHECKPOINT","compressed_read",cursor,"inflated",plain_cursor,flush=True)
        remaining=inflater.flush()
        if remaining:
            crc=zlib.crc32(remaining,crc)
            lo=max(want_start,plain_cursor);hi=min(want_end,plain_cursor+len(remaining))
            if hi>lo:
                out[lo-want_start:hi-want_start]=remaining[lo-plain_cursor:hi-plain_cursor]
                got+=hi-lo
            plain_cursor+=len(remaining)
        if (not inflater.eof or inflater.unused_data or inflater.unconsumed_tail
            or plain_cursor!=UNCOMPRESSED or got!=size or crc!=CRC):
            raise ValueError("PAL full ZIP member CRC32, size, or FE extraction range failed")
    resource=bytes(out)
    pal_sha=hashlib.sha256(resource).hexdigest()
    pal_hash=ea_data_hash(resource)
    if pal_hash!=checksum:
        raise ValueError("PAL resource checksum does not match PAL ZDIR record")
    return {
      "stage":"PRE523_ORIGINAL_PAL_FE_ATTRIB_VPAK_BINARY_IDENTITY_READONLY",
      "status":"AUDIT_OK",
      "original_PAL_ZIP_file_id":ZIP_ID,
      "original_PAL_ZZDATA0_uncompressed_size_verified":plain_cursor==UNCOMPRESSED,
      "original_PAL_ZZDATA0_crc32_verified":crc==CRC,
      "original_PAL_ZZDATA0_member_crc32_hex":f"{crc:08x}",
      "original_PAL_ZDIR_SHA256":INDEX_SHA,
      "original_PAL_FE_ZDIR_record_index":row,
      "original_PAL_FE_ZDIR_archive_index":archive,
      "original_PAL_FE_local_byte_offset":want_start,
      "original_PAL_FE_total_sector":total,
      "original_PAL_FE_resource_bytes":size,
      "original_PAL_FE_resource_sha256":pal_sha,
      "original_PAL_FE_checksum_hex":f"{checksum:08x}",
      "recomputed_PAL_FE_EA_checksum_hex":f"{pal_hash:08x}",
      "original_USA_FE_sha256":USA_SHA,
      "original_USA_FE_bytes":USA_SIZE,
      "original_USA_FE_checksum_hex":f"{USA_EA_CHECKSUM:08x}",
      "original_PAL_FE_same_bytes_as_USA_proven":size==USA_SIZE and pal_sha==USA_SHA,
      "original_PAL_FE_same_checksum_as_USA":checksum==USA_EA_CHECKSUM,
      "previous_USA_FECarPartInfo_21_arrays_verified":True,
      "PAL_FECarPartInfo_costs_usable_as_original_values":size==USA_SIZE and pal_sha==USA_SHA,
      "PAL_runtime_shop_cost_lookups_verified":False,
      "BMW_purchase_or_installed_physics_verified":False,
      "compressed_bytes_authenticated":cursor,
      "strict_original_zip_HTTP206_requests":requests,
      "asset_bytes_published":False,"PAL_zip_modified":False,
      "ZDIR_or_ZZDATA_modified":False,"APK_built":False,
      "save_modified":False,"signing_accessed":False,
      "safe_to_enable_tuning":False
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    a=ap.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"stage":"PRE523_ORIGINAL_PAL_FE_ATTRIB_VPAK_BINARY_IDENTITY_READONLY",
           "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:240],
           "asset_bytes_published":False,"PAL_zip_modified":False,
           "ZDIR_or_ZZDATA_modified":False,"APK_built":False,
           "save_modified":False,"signing_accessed":False,"safe_to_enable_tuning":False}
    r["run_id"]=a.run_id;r["timestamp_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE523_STATUS",r["status"],flush=True)
    print("PRE523_PAL_FE_IDENTITY",r.get("original_PAL_FE_same_bytes_as_USA_proven"),flush=True)
    print("PRE523_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
