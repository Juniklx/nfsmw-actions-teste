#!/usr/bin/env python3
"""PRE551: verify exact PAL ZZDATA4 sector padding and synthetic virtual resource.

This is a *file-format and virtual-read simulation*, NOT execution of the
game's PAL guest loader. Authenticate user's original PAL ZIP central
directory metadata; stream and CRC-check only original compressed
NFS/ZZDATA4.BIN within the private ephemeral CI worker. Capture just
its 341-sector reserved area for GLOBAL/ATTRIBUTES.BIN. Check original
VPAK SHA and all 512 physical padding bytes, then run PRE502 synthetic
BMW level1 resource constructor IN MEMORY. Simulate ZDIR record and
resource reads using scratch bytes + original sector tail. No game
assets, original ZZDATA4, ZIP, ISO, ZDIR or APK saved or uploaded.
No game play/save/signing access and no transaction.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,zlib
from datetime import datetime,timezone
from pathlib import Path
from pre459_pal_zip_car_catalog_readonly import inspect,session,read_range,API,FILE_ID,SIZE
from pre461_zdir_candidate_hash_names_readonly import raw_zdir,INDEX_SHA
from pre462_usa_raw_iso_attributes_readonly import NAMES
from pre502_bmw_engine_combined_level1_scratch import audit as build_scratch
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
OUT=Path("/tmp/nfsmw-pre551/report.json")
ENTRY="NFS/ZZDATA4.BIN"
ARCHIVE_SIZE=401068032
COMPRESSED=261097565
OFFSET_LOCAL_HEADER=3731333269
ZIP_CRC=0xB46A396C
RESOURCE_OFFSET=355932160
RESOURCE_ORIGINAL=697856
RESOURCE_CANDIDATE=698004
RESERVED=698368
PADDING_ORIGINAL=512
PADDING_NEW=364
ROW_INDEX=806
GLOBAL_SECTOR=890205
ARCHIVE=4
ORIG_EA=0x296AD9ED
NEW_EA=0x4D05584A
ORIG_SHA="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
NEW_SHA="d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6"
NEW_RECORD_SHA="6d0b1744073a50756dcdd296ff5c7ede7dfba35b7a9928e0de5be28f3a18fa78"
MASK=b"NFS/ZZDATA4.BIN"

def original_sector(sess):
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
    def accept(uncompressed):
        nonlocal output_at,copied,digest
        if not uncompressed:return
        old=output_at
        new=old+len(uncompressed)
        if new>ARCHIVE_SIZE:
            raise ValueError("DEFLATE emitted beyond authenticated ZZDATA4 uncompressed size")
        digest=zlib.crc32(uncompressed,digest)
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
        "original_pal_ZZDATA4_expected_CRC32_validated":True,
        "original_resource_sector_offset_bytes":RESOURCE_OFFSET,
        "original_resource_reserved_sector_bytes_captured":copied,
        "raw_original_ZZDATA4_or_ZIP_written_to_files":False
    }

def audit():
    need={
      "docs/PRE518_BMW_RAM_VPAK_ZDIR_CHECKSUM_READONLY.json":"status",
      "docs/PRE506_ORIGINAL_PAL_ZDIR_ATTRIBUTE_ALLOCATION_READONLY.json":"status",
      "docs/PRE550_CANONICAL_CONTEXT_SYNC_RESULT.json":"status"
    }
    proofs={p:json.loads(Path(p).read_text()) for p in need}
    if any(j.get("status")!="AUDIT_OK" for j in proofs.values()):
        raise ValueError("PRE518/PRE506/PRE550 authenticated preconditions absent")
    pre518=proofs["docs/PRE518_BMW_RAM_VPAK_ZDIR_CHECKSUM_READONLY.json"]
    pre506=proofs["docs/PRE506_ORIGINAL_PAL_ZDIR_ATTRIBUTE_ALLOCATION_READONLY.json"]
    sync=proofs["docs/PRE550_CANONICAL_CONTEXT_SYNC_RESULT.json"]
    if (pre518.get("synthetic_scratch_VPAK_sha256")!=NEW_SHA or
        pre518.get("synthetic_scratch_VPAK_bytes")!=RESOURCE_CANDIDATE or
        pre518.get("source_PAL_ZDIR_sha256")!=INDEX_SHA or
        pre518.get("new_engine_guest_loader_acceptance_proven") is not False or
        pre506.get("PRE502_fits_same_sector_count") is not True or
        pre506.get("PAL_padding_byte_values_verified") is not False or
        pre506.get("pal_ZDIR_records")!=1390 or
        sync.get("new_total_bytes")!=834187 or
        sync.get("new_sha256")!="33733023e743cac5cc8206fe45891455e6f8d3c951b9d7cdae835f3765f7b72d"):
        raise ValueError("Original PAL allocation/experimental candidate/canonical checkpoint changed")
    zdir=raw_zdir()
    if len(zdir)!=1390*24 or hashlib.sha256(zdir).hexdigest()!=INDEX_SHA:
        raise ValueError("Original PAL ZDIR SHA and size mismatch")
    rows=[(i,vals) for i,vals in enumerate(struct.iter_unpack("<IiIIiI",zdir))
          if vals[0]==NAMES["GLOBAL\\ATTRIBUTES.BIN"]]
    if len(rows)!=1 or rows[0][0]!=ROW_INDEX:
        raise ValueError("Original PAL ZDIR resource row is ambiguous")
    idx,(name_hash,archive,sector,total,size,checksum)=rows[0]
    if (archive,sector*2048,total,size,checksum)!=(
       ARCHIVE,RESOURCE_OFFSET,GLOBAL_SECTOR,RESOURCE_ORIGINAL,ORIG_EA):
        raise ValueError("Original PAL ZDIR resource tuple differs")
    sector_region,source_proof=original_sector(session())
    original=sector_region[:RESOURCE_ORIGINAL]
    pad=sector_region[RESOURCE_ORIGINAL:]
    if (hashlib.sha256(original).hexdigest()!=ORIG_SHA or
        ea_data_hash(original)!=ORIG_EA or
        len(pad)!=PADDING_ORIGINAL):
        raise ValueError("PAL original direct ZZDATA4 VPAK hash/EA CRC/padding identity differ")
    pad_zero=sum(b==0 for b in pad)
    if pad_zero!=PADDING_ORIGINAL:
        raise ValueError("Original PAL sector slack contains nonzero bytes (unsafe)")
    next_rows=sorted(
      x[2]*2048 for x in
      (t for t in struct.iter_unpack("<IiIIiI",zdir))
      if x[1]==ARCHIVE and x[2]*2048>RESOURCE_OFFSET
    )
    if not next_rows or next_rows[0]!=RESOURCE_OFFSET+RESERVED:
        raise ValueError("Next original PAL ZDIR resource does not start exactly at 341-sector boundary")
    def synthetic_consumer(scratch:bytes):
        if len(scratch)!=RESOURCE_CANDIDATE or hashlib.sha256(scratch).hexdigest()!=NEW_SHA:
            raise ValueError("Authenticated PRE502 RAM reconstruction differs from PRE518")
        if ea_data_hash(scratch)!=NEW_EA:
            raise ValueError("Synthetic BMW EA checksum differs from authenticated test fixture")
        # All writes are PRIVATE TO MEMORY, never to the user's archive.
        simulated_sector=bytearray(sector_region)
        simulated_sector[:len(scratch)]=scratch
        sim_zdir=bytearray(zdir)
        struct.pack_into("<i",sim_zdir,idx*24+16,len(scratch))
        struct.pack_into("<I",sim_zdir,idx*24+20,NEW_EA)
        patched_row=bytes(sim_zdir[idx*24:(idx+1)*24])
        if hashlib.sha256(patched_row).hexdigest()!=NEW_RECORD_SHA:
            raise ValueError("Synthetic 24-byte ZDIR member changed since PRE518")
        if (zdir[:idx*24]!=sim_zdir[:idx*24] or
            zdir[(idx+1)*24:]!=sim_zdir[(idx+1)*24:]):
            raise ValueError("Non-target original PAL ZDIR rows changed in memory")
        if bytes(simulated_sector[len(scratch):])!=b"\0"*PADDING_NEW:
            raise ValueError("New 364-byte padded sector remainder is not zero")
        if (bytes(simulated_sector[:len(scratch)])!=scratch or
            len(simulated_sector)!=RESERVED):
            raise ValueError("RAM virtual sector readback mismatch")
        # Resource-level ZDIR virtual read only; deliberately not actual game
        # guest loader, VLT import system, engine runtime or save writer.
        (h,a,sec,glob,sz,ck)=struct.unpack_from("<IiIIiI",sim_zdir,idx*24)
        if (h,a,sec*2048,glob,sz,ck)!=(
            name_hash,ARCHIVE,RESOURCE_OFFSET,GLOBAL_SECTOR,RESOURCE_CANDIDATE,NEW_EA):
            raise ValueError("Simulated ZDIR lookup / sector read does not resolve candidate")
        fetched=bytes(simulated_sector[:sz])
        if hashlib.sha256(fetched).hexdigest()!=NEW_SHA or ea_data_hash(fetched)!=ck:
            raise ValueError("Virtual resource CRC/readback failure")
        return {
          "original_pal_ZDIR_in_ram_resource_lookup_verified":True,
          "original_pal_ZZDATA_sector_padding_all_zero_verified":True,
          "original_pal_ZZDATA_sector_padding_zero_bytes":PADDING_ORIGINAL,
          "isolated_synthetic_RAM_resource_readback_SHA256":NEW_SHA,
          "isolated_synthetic_RAM_ZDIR_EA_hash_hex":f"{ck:08x}",
          "original_archive_target_other_sectors_unchanged_in_this_ram_model":True,
          "synthetic_ZDIR_record_sha256":hashlib.sha256(patched_row).hexdigest(),
          "synthetic_remaining_sector_padding_zero_bytes":PADDING_NEW,
          "actual_game_guest_loader_executed":False,
          "actual_game_guest_VLT_ExpN_RefSpec_accepted":False,
          "actual_game_engine_power_modified":False,
          "on_device_ISO_selection_verified":False,
          "V48_edition_branch_runtime_observed":False,
          "runtime_purchase_or_save_persistence_verified":False
        }
    rebuild=build_scratch(consume_scratch=synthetic_consumer)
    private=rebuild.pop("_private_scratch_analysis",None)
    if (rebuild.get("status")!="AUDIT_OK" or private is None or
        rebuild.get("new_engine_ExpN_RefSpec_PtrN_reparsed") is not True or
        rebuild.get("scratch_vpak_bytes")!=RESOURCE_CANDIDATE or
        rebuild.get("safe_to_enable_or_build_tuning") is not False):
        raise ValueError("PRE502 synthetic RAM rebuild gate failed")
    return {
      "stage":"PRE551_ORIGINAL_PAL_ZZDATA4_SECTOR_AND_SYNTHETIC_RAM_RESOURCE_READBACK",
      "status":"AUDIT_OK",
      "PAL_game_original_ZIP_id":FILE_ID,
      "source_pal_original_VPAK_sha256":ORIG_SHA,
      "source_pal_original_VPAK_bytes":RESOURCE_ORIGINAL,
      "source_pal_original_EA_resource_hash_hex":f"{ORIG_EA:08x}",
      "source_PAL_original_ZDIR_sha256":INDEX_SHA,
      "source_PAL_index_row":ROW_INDEX,
      "source_PAL_next_ZDIR_resource_offset_bytes":RESOURCE_OFFSET+RESERVED,
      "original_PALEdition_source_archive_sector_count":RESERVED//2048,
      "synthetic_BMW_engine_plus_five_percent_only":True,
      "synthetic_BMW_upgrade_counter_original_zero_candidate_one":True,
      "synthetic_ExpN_RefSpec_PtrN_reparsed_in_ram":True,
      **source_proof,**private,
      "no_original_game_file_written_or_changed":True,
      "modified_ZDIR_or_ZZDATA_file_written_or_published":False,
      "synthetic_VPAK_game_resource_written_or_published":False,
      "APK_built":False,"save_modified":False,"signing_material_accessed":False,
      "BMW_tuning_enabled":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    args=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as e:
        result={"stage":"PRE551_ORIGINAL_PAL_ZZDATA4_SECTOR_AND_SYNTHETIC_RAM_RESOURCE_READBACK",
                "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
                "no_original_game_file_written_or_changed":True,
                "modified_ZDIR_or_ZZDATA_file_written_or_published":False,
                "synthetic_VPAK_game_resource_written_or_published":False,
                "APK_built":False,"save_modified":False,
                "signing_material_accessed":False,"BMW_tuning_enabled":False}
    result["run_id"]=args.run_id;result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE551_STATUS",result["status"],flush=True)
    print("PRE551_COMPRESSED_ZZDATA4_VERIFIED",result.get("zip_original_ZZDATA4_compressed_bytes_read"),flush=True)
    print("PRE551_ORIGINAL_PADDING",result.get("original_pal_ZZDATA_sector_padding_zero_bytes"),flush=True)
    print("PRE551_VIRTUAL_READER",result.get("original_pal_ZDIR_in_ram_resource_lookup_verified"),flush=True)
    print("PRE551_ERROR",result.get("error_type","none"),result.get("error",""),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
