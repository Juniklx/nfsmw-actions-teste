#!/usr/bin/env python3
"""PRE460: inspect only 33 KB NFS/ZDIR.BIN inside user's 5.56 GB PAL ZIP.
Strict ranged reads; no game assets published, no ZZDATA extraction or repacking.
"""
import argparse, hashlib, json, re, struct, sys, zlib
from pathlib import Path
from datetime import datetime,timezone
from pre459_pal_zip_car_catalog_readonly import session, read_range, FILE_ID, SIZE

OUT=Path("/tmp/nfsmw-pre460/report.json")
NAME=b"NFS/ZDIR.BIN"
LOCAL_OFFSET=2772502468
COMPRESSED=24233
UNCOMPRESSED=33360
CRC=0x1572A136
LIMIT=262144

def inspect():
    sess=session()
    header=read_range(sess,LOCAL_OFFSET,30)
    if header[:4]!=b"PK\x03\x04":raise ValueError("ZIP local header signature mismatch")
    fields=struct.unpack_from("<IHHHHHIIIHH",header)
    (_sig,version,flags,method,mt,md,header_crc,header_csize,header_usize,nlen,xlen)=fields
    if method!=8 or (flags&1) or nlen>80 or xlen>1024:
        raise ValueError("Unsupported ZDIR compression/flags/name")
    name=read_range(sess,LOCAL_OFFSET+30,nlen)
    if name!=NAME:raise ValueError("ZIP member identity mismatch")
    if header_crc not in (0,CRC) or header_csize not in (0,COMPRESSED) or header_usize not in (0,UNCOMPRESSED):
        raise ValueError("ZDIR local header conflicts with PRE459 central dir")
    start=LOCAL_OFFSET+30+nlen+xlen
    compressed=read_range(sess,start,COMPRESSED)
    inflator=zlib.decompressobj(-15)
    plain=inflator.decompress(compressed,LIMIT)
    plain+=inflator.flush()
    if not inflator.eof or inflator.unused_data or len(plain)!=UNCOMPRESSED:
        raise ValueError("ZDIR inflate length/EOF mismatch")
    if (zlib.crc32(plain)&0xFFFFFFFF)!=CRC:
        raise ValueError("ZDIR CRC32 mismatch")
    # Metadata only: low-entropy observations for safe format recognition.
    words=[plain[i:i+4] for i in range(0,min(128,len(plain)),4)]
    asciis=[v.decode("ascii","ignore") for v in re.findall(rb"[A-Za-z0-9_./\\-]{6,80}",plain)]
    hits=[x for x in asciis if any(y in x.lower() for y in ("bmw","gtr","car","perform","upgrade","global","attrib","vlt","punto"))]
    return {
      "status":"AUDIT_OK","stage":"PRE460_PAL_ZDIR_SMALL_FORMAT_READONLY",
      "source_drive_file_id":FILE_ID,"source_zip_size":SIZE,
      "member_name":NAME.decode(),"compressed_bytes":COMPRESSED,
      "uncompressed_bytes":UNCOMPRESSED,"crc32":f"{CRC:08x}",
      "uncompressed_sha256":hashlib.sha256(plain).hexdigest(),
      "first_32_words_big_endian":[int.from_bytes(w,"big") for w in words],
      "first_32_words_little_endian":[int.from_bytes(w,"little") for w in words],
      "ascii_sequence_count":len(asciis),"ascii_strings_candidate":hits[:20],
      "null_byte_count":plain.count(b"\x00"),
      "number_of_nonzero_4byte_groups":sum(bool(int.from_bytes(w,"big")) for w in words),
      "total_bytes_requested_upper_bound":30+nlen+COMPRESSED,
      "zdir_fully_read_private_runner_only":True,
      "zzdata_contents_read":False,"assets_published":False,
      "bmw_upgrade_ids_identified":False,"bmw_mod_enabled":False,
      "apk_built":False,"save_modified":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=inspect()
    except Exception as e:r={"status":"FAILED","stage":"PRE460_PAL_ZDIR_SMALL_FORMAT_READONLY",
                            "error_type":type(e).__name__,"error":str(e)[:210],
                            "apk_built":False,"save_modified":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE460_STATUS",r["status"],flush=True)
    print("PRE460_ZDIR_SHA",r.get("uncompressed_sha256","unknown"),flush=True)
    print("PRE460_ASCII_HITS",len(r.get("ascii_strings_candidate",[])),flush=True)
    print("PRE460_ERROR",r.get("error_type","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":sys.exit(main())
