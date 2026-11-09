#!/usr/bin/env python3
"""PRE557: SHA-256 the full uncompressed original PAL ZZDATA4.BIN in a private
streaming runner. Byte-authenticate original ZIP central directory/member and
CRC32, capture no asset to disk; retain only digest and safe source metadata.
This is NOT a SHA of the user's translated folder, and not a loader test.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,zlib
from datetime import datetime,timezone
from pathlib import Path
from pre551_pal_ZZDATA4_sector_ram_loader_preflight_readonly import (
    inspect,session,read_range,API,FILE_ID,SIZE,ENTRY,ARCHIVE_SIZE,COMPRESSED,
    OFFSET_LOCAL_HEADER,ZIP_CRC,RESOURCE_OFFSET,RESOURCE_ORIGINAL,RESERVED,
    PADDING_ORIGINAL,ROW_INDEX,GLOBAL_SECTOR,ARCHIVE,ORIG_EA,ORIG_SHA,MASK)
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
OUT=Path("/tmp/nfsmw-pre557/report.json")

def authenticated_member_with_sha256(sess):
    catalog=inspect(sess)
    members=[x for x in catalog["entries"] if x["name"]==ENTRY]
    if (catalog["source_file_id"]!=FILE_ID or
        catalog["cd_sha256"]!="a74f69e40ec0cc84ff58fcbf9fcccdd7353996c75592779ec63f09cf7dfdc7d6" or
        len(members)!=1 or
        members[0]["uncompressed_bytes"]!=ARCHIVE_SIZE or
        members[0]["compressed_bytes"]!=COMPRESSED or
        members[0]["local_header_offset"]!=OFFSET_LOCAL_HEADER or
        members[0]["method"]!=8 or
        int(members[0]["crc32"],16)!=ZIP_CRC or
        members[0]["flags"]&1):
        raise ValueError("Original PAL ZIP/ZZDATA4 central directory changed")
    off=members[0]["local_header_offset"]
    head=read_range(sess,off,30)
    if len(head)!=30 or head[:4]!=b"PK\x03\x04":
        raise ValueError("Original PAL ZZDATA4 local ZIP header missing")
    fields=struct.unpack("<IHHHHHIIIHH",head)
    _,version,flags,method,mtime,mdate,crc,comp_size,uncomp_size,nlen,xlen=fields
    if (method!=8 or flags&1 or not 1<=nlen<=80 or not 0<=xlen<=4096
        or crc not in (0,ZIP_CRC)
        or comp_size not in (0,COMPRESSED)
        or uncomp_size not in (0,ARCHIVE_SIZE)):
        raise ValueError("Local ZIP member differs from authenticated central directory")
    name=read_range(sess,off+30,nlen)
    if name!=MASK:
        raise ValueError("Local ZIP path not expected ZZDATA4 file")
    compressed_start=off+30+nlen+xlen
    end=compressed_start+COMPRESSED-1
    if compressed_start<=0 or end>=SIZE:
        raise ValueError("Invalid absolute ZIP compressed stream range")
    captured=bytearray(RESERVED)
    received=0
    output_at=0
    copied=0
    digest=zlib.crc32(b"")
    full_sha=hashlib.sha256()
    def accept(uncompressed):
        nonlocal output_at,copied,digest
        if not uncompressed:return
        old=output_at
        new=old+len(uncompressed)
        if new>ARCHIVE_SIZE:
            raise ValueError("DEFLATE emitted beyond authenticated ZZDATA4 uncompressed size")
        digest=zlib.crc32(uncompressed,digest)
        full_sha.update(uncompressed)
        wanted_start=max(old,RESOURCE_OFFSET)
        wanted_end=min(new,RESOURCE_OFFSET+RESERVED)
        if wanted_start<wanted_end:
            n=wanted_end-wanted_start
            captured[wanted_start-RESOURCE_OFFSET:wanted_end-RESOURCE_OFFSET]=(
                uncompressed[wanted_start-old:wanted_end-old]
            )
            copied+=n
        output_at=new

    resp=sess.get(API,params={"alt":"media"},headers={
        "Range":f"bytes={compressed_start}-{end}","Accept-Encoding":"identity"},
        stream=True,timeout=(35,180),allow_redirects=False)
    with resp:
        if resp.status_code!=206:
            raise ValueError("Original ZIP compressed member request requires HTTP 206, got "+str(resp.status_code))
        if resp.headers.get("Content-Range","").strip()!=f"bytes {compressed_start}-{end}/{SIZE}":
            raise ValueError("Original ZZDATA4 compressed byte range Content-Range mismatch")
        if resp.headers.get("Content-Encoding","identity").lower() not in ("identity",""):
            raise ValueError("Unexpected HTTP content decoding while processing ZIP DEFLATE bytes")
        inflater=zlib.decompressobj(-15)
        for chunk in resp.iter_content(chunk_size=512*1024):
            if not chunk:continue
            received+=len(chunk)
            if received>COMPRESSED:
                raise ValueError("Compressed ZIP member overrun")
            # Typical compressed/uncompressed ratio ~0.65; bounded chunk
            # keeps original data ephemeral and never stores ZZDATA archive.
            uncompressed=inflater.decompress(chunk)
            accept(uncompressed)
            if inflater.unconsumed_tail:
                raise ValueError("Unexpected unconsumed raw DEFLATE input")
        if received!=COMPRESSED:
            raise ValueError("Original ZIP compressed member shortened")
        accept(inflater.flush())
        if not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
            raise ValueError("Original DEFLATE not at expected clean EOF")
    if output_at!=ARCHIVE_SIZE or copied!=RESERVED or digest&0xffffffff!=ZIP_CRC:
        raise ValueError("Original PAL ZZDATA4 CRC, size, or reserved resource capture failed")
    return bytes(captured),{
        "authenticated_zip_central_directory_sha256":catalog["cd_sha256"],
        "zip_original_ZZDATA4_uncompressed_bytes":output_at,
        "zip_original_ZZDATA4_compressed_bytes_read":received,
        "zip_original_ZZDATA4_CRC32_hex":f"{digest&0xffffffff:08x}",
        "zip_original_ZZDATA4_full_SHA256":full_sha.hexdigest(),
        "original_pal_ZZDATA4_expected_CRC32_validated":True,
        "original_resource_sector_offset_bytes":RESOURCE_OFFSET,
        "original_resource_reserved_sector_bytes_captured":copied,
        "raw_original_ZZDATA4_or_ZIP_written_to_files":False
    }


def audit():
    baseline=json.loads(Path("docs/PRE551_PAL_ORIGINAL_ZZDATA4_PADDING_AND_VIRTUAL_RESOURCE_READONLY.json").read_text())
    pre555=json.loads(Path("docs/PRE555_PAL_EXTRACTED_FOLDER_HOSTPATH_VFS_READONLY.json").read_text())
    if (baseline.get("status")!="AUDIT_OK" or
        baseline.get("zip_original_ZZDATA4_uncompressed_bytes")!=ARCHIVE_SIZE or
        baseline.get("zip_original_ZZDATA4_CRC32_hex")!=f"{ZIP_CRC:08x}" or
        baseline.get("source_PAL_original_ZDIR_sha256")!="7f37d29f958454ec73d5dbd30068a6acb23cf92d5056fa2d944ca5c87c6637ee" or
        pre555.get("status")!="AUDIT_OK" or
        pre555.get("user_reported_current_game_source")!="EXTRACTED_FOLDER_NOT_ISO" or
        pre555.get("translation_extracted_folder_bytes_match_original_PAL_ZIP_proven") is not False):
        raise ValueError("PRE551/PRE555 original PAL source provenance does not match")
    reserved,auth=authenticated_member_with_sha256(session())
    if (len(reserved)!=RESERVED or
        hashlib.sha256(reserved[:RESOURCE_ORIGINAL]).hexdigest()!=ORIG_SHA or
        ea_data_hash(reserved[:RESOURCE_ORIGINAL])!=ORIG_EA or
        reserved[RESOURCE_ORIGINAL:]!=b"\0"*PADDING_ORIGINAL or
        auth["zip_original_ZZDATA4_uncompressed_bytes"]!=ARCHIVE_SIZE or
        auth["zip_original_ZZDATA4_CRC32_hex"]!=baseline["zip_original_ZZDATA4_CRC32_hex"]):
        raise ValueError("Original resource SHA/hash/slack/CRC is not consistent")
    return {
        "stage":"PRE557_ORIGINAL_PAL_ZZDATA4_FULL_SHA256_FOR_EXTRACTED_FOLDER_PARITY",
        "status":"AUDIT_OK",
        "original_pal_source_member":"NFS/ZZDATA4.BIN",
        "original_pal_uncompressed_member_bytes":ARCHIVE_SIZE,
        "original_pal_uncompressed_member_zip_crc32_hex":auth["zip_original_ZZDATA4_CRC32_hex"],
        "original_pal_uncompressed_member_sha256":auth["zip_original_ZZDATA4_full_SHA256"],
        "original_pal_ZDIR_sha256":"7f37d29f958454ec73d5dbd30068a6acb23cf92d5056fa2d944ca5c87c6637ee",
        "original_pal_ATTRIBUTES_vpak_SHA256":ORIG_SHA,
        "original_pal_ATTRIBUTES_reserved_sector_bytes":RESERVED,
        "original_pal_ATTRIBUTES_original_padding_zero_count":PADDING_ORIGINAL,
        "source_authenticated_full_stream_CRC32_and_SHA256":True,
        "source_zip_or_game_assets_published":False,
        "user_translation_file_bytes_checked":False,
        "actual_v48_runtime_VFS_verified":False,
        "guest_new_BMW_ExpN_accepted":False,
        "APK_built":False,
        "game_assets_modified":False,
        "save_modified":False,
        "signing_material_accessed":False,
        "BMW_tuning_enabled":False,
        "next_gate":"COMPARE_ONLY_HASHES_OF_EXTRACTED_NFS_ZDIR_AND_ZZDATA4_ON_S24FE"
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"stage":"PRE557_ORIGINAL_PAL_ZZDATA4_FULL_SHA256_FOR_EXTRACTED_FOLDER_PARITY",
           "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:200],
           "source_zip_or_game_assets_published":False,"APK_built":False,
           "game_assets_modified":False,"save_modified":False,
           "signing_material_accessed":False,"BMW_tuning_enabled":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE557_STATUS",r["status"],flush=True)
    print("PRE557_ORIGINAL_ZZDATA4_SHA256",r.get("original_pal_uncompressed_member_sha256","UNAVAILABLE"),flush=True)
    print("PRE557_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
