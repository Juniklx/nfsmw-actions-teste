#!/usr/bin/env python3
"""PRE572: prepare two *private* PTBR BMW synthetic patch fragments in Drive.
Never overwrite the user's translated game or APK. Source 5.4GB PTBR ZIP is
read by HTTP206, keeping only the first 341 sectors and a streaming hash.
The patch is NOT a playable ZZDATA4 archive; real guest loader remains untested.
"""
from __future__ import annotations
import argparse, hashlib, io, json, struct, zlib
from datetime import datetime, timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from pre459_pal_zip_car_catalog_readonly import session
from pre561_ptbr_zip_zdir_record_readonly import (
    FILE_ID, SIZE, API, zip_directory, member_zdir, ranged, ZDIR_SHA)
from pre502_bmw_engine_combined_level1_scratch import audit as make_scratch
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash

OUT=Path("/tmp/nfsmw-pre572/report.json")
PATCH_PARENT="1tmIzbpCbTQrNT59p0tWHiW_KdGGpHCCB"
PATCH_FOLDER="PRE572_BMW_PTBR_TESTE_EXPERIMENTAL_20261109"
ROW=805; OLD_SIZE=697856; NEW_SIZE=698004; REGION=698368
NEW_SHA="d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6"
OLD_RESOURCE_SHA="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
OLD_ARCHIVE_SHA="7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951"
NEW_CRC=0x4d05584a
ZIP_CRC=0xa038afed
ZIP_COMP=261092849
ZIP_UNCOMP=401068032
TARGET_HASH=0x9775379a
EXPECTED_ZDIR_ROW_SHA="728e02041249ed029026fcdd7a92f254b60f1669f81ebad45e57f53574481735"

def sha(b):return hashlib.sha256(b).hexdigest()
def md5(b):return hashlib.md5(b).hexdigest()

def stream_full_archive_digest(sess,entry,replacement:bytes):
    if (entry["method"]!=8 or entry["compressed"]!=ZIP_COMP
        or entry["uncompressed"]!=ZIP_UNCOMP or entry["crc32"]!=ZIP_CRC
        or entry["flags"]&1):
        raise ValueError("PTBR ZIP ZZDATA4 metadata differs from PRE563")
    h=ranged(sess,entry["offset"],30)
    if h[:4]!=b"PK\x03\x04":raise ValueError("ZZDATA4 ZIP local header missing")
    vals=struct.unpack("<IHHHHHIIIHH",h)
    _,_ver,flags,method,*_,nlen,xlen=vals
    if method!=8 or flags&1 or not 1<=nlen<=500 or not 0<=xlen<=4096:
        raise ValueError("ZZDATA4 local ZIP member invalid")
    actual=ranged(sess,entry["offset"]+30,nlen).decode("utf-8","replace")
    if actual!=entry["name"]:raise ValueError("ZZDATA4 ZIP local name mismatch")
    begin=entry["offset"]+30+nlen+xlen
    end=begin+ZIP_COMP-1
    if begin<=0 or end>=SIZE:raise ValueError("ZIP compressed archive range outside file")
    original=hashlib.sha256()
    patched=hashlib.sha256()
    original_crc=0
    modified_crc=0
    decoded=0
    received=0
    region=bytearray(REGION)
    region_written=0
    inflate=zlib.decompressobj(-15)
    def accept(data):
        nonlocal decoded,original_crc,modified_crc,region_written
        if not data:return
        start=decoded
        decoded+=len(data)
        if decoded>ZIP_UNCOMP:raise ValueError("Uncompressed member overrun")
        original.update(data)
        original_crc=zlib.crc32(data,original_crc)
        take=max(0,min(REGION,decoded)-start) if start<REGION else 0
        if take:
            region[start:start+take]=data[:take]
            region_written+=take
            patched.update(replacement[start:start+take])
            modified_crc=zlib.crc32(replacement[start:start+take],modified_crc)
        if take<len(data):
            suffix=data[take:]
            patched.update(suffix)
            modified_crc=zlib.crc32(suffix,modified_crc)
    with sess.get(API,params={"alt":"media"},headers={
         "Range":f"bytes={begin}-{end}","Accept-Encoding":"identity"},
         stream=True,timeout=(35,220),allow_redirects=False) as res:
        if(res.status_code!=206 or res.headers.get("Content-Range","").strip()
            !=f"bytes {begin}-{end}/{SIZE}" or
           res.headers.get("Content-Encoding","identity").lower() not in ("identity","")):
            raise ValueError("Strict range for original ZIP member unavailable")
        for part in res.iter_content(chunk_size=512*1024):
            if not part:continue
            received+=len(part)
            if received>ZIP_COMP:raise ValueError("Compressed member overflow")
            accept(inflate.decompress(part))
        accept(inflate.flush())
    if (received!=ZIP_COMP or decoded!=ZIP_UNCOMP or not inflate.eof or
        inflate.unused_data or inflate.unconsumed_tail or
        (original_crc&0xffffffff)!=ZIP_CRC or region_written!=REGION):
        raise ValueError("Original ZIP stream CRC/length/end-of-stream invalid")
    if original.hexdigest()!=OLD_ARCHIVE_SHA:
        raise ValueError("Original PTBR archive SHA does not match PRE563+phone")
    if sha(bytes(region[:OLD_SIZE]))!=OLD_RESOURCE_SHA or region[OLD_SIZE:]!=bytes(REGION-OLD_SIZE):
        raise ValueError("Original translated attributes/padding differ from PRE563")
    if ea_data_hash(bytes(region[:OLD_SIZE]))!=0x296ad9ed:
        raise ValueError("Original EA resource checksum mismatch")
    return {"translated_original_ZZDATA4_full_sha256":original.hexdigest(),
            "translated_full_archive_expected_modified_sha256":patched.hexdigest(),
            "translated_full_archive_expected_modified_crc32":f"{modified_crc&0xffffffff:08x}",
            "original_zip_member_fully_verified_by_stream":True,
            "translated_nontarget_archive_bytes_pass_through_unchanged":True,
            "source_sector_initial_512_padding_bytes_verified":True}

def drive_folder(d):
    q=("name = '"+PATCH_FOLDER+"' and '"+PATCH_PARENT+
       "' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false")
    results=d.files().list(q=q,pageSize=10,fields="files(id,name,mimeType,parents),nextPageToken").execute().get("files",[])
    if len(results)>1:raise ValueError("Duplicate experiment folders ambiguous")
    if results:return results[0]["id"],False
    result=d.files().create(body={"name":PATCH_FOLDER,"mimeType":"application/vnd.google-apps.folder",
      "parents":[PATCH_PARENT]},fields="id,name,parents").execute()
    if not result.get("id"):raise ValueError("Patch folder not created")
    return result["id"],True

def ensure_private_file(d,folder,name,data):
    q=("name = '"+name+"' and '"+folder+"' in parents and trashed = false")
    result=d.files().list(q=q,pageSize=10,fields="files(id,name,size,md5Checksum,mimeType,parents)").execute().get("files",[])
    if len(result)>1:raise ValueError("Duplicate patch binary filename")
    if result:
        info=result[0]
        if int(info.get("size",0))!=len(data) or info.get("md5Checksum")!=md5(data):
            raise ValueError("Existing Drive patch file differs; never overwrite it")
        fresh=False
    else:
        metadata={"name":name,"parents":[folder],"description":"Experimental NFSMW PTBR BMW synthetic patch fragment; not a playable full archive"}
        info=d.files().create(body=metadata,
             media_body=MediaIoBaseUpload(io.BytesIO(data),mimetype="application/octet-stream",resumable=False),
             fields="id,name,size,md5Checksum,parents").execute()
        fresh=True
    if not info.get("id") or int(info.get("size",0))!=len(data) or info.get("md5Checksum")!=md5(data):
        raise ValueError("Drive patch upload metadata mismatch")
    file_bytes=io.BytesIO()
    dl=MediaIoBaseDownload(file_bytes,d.files().get_media(fileId=info["id"]),chunksize=1024*1024)
    done=False
    while not done: _,done=dl.next_chunk(num_retries=3)
    if file_bytes.getvalue()!=data:raise ValueError("Drive readback differs from candidate")
    return {"id":info["id"],"name":name,"size":len(data),"sha256":sha(data),"fresh_upload":fresh}

def audit():
    p564=json.loads(Path("docs/PRE564_PTBR_BMW_SYNTHETIC_RAM_RESOURCE_LOOKUP_READONLY.json").read_text())
    p566=json.loads(Path("docs/PRE566_PTBR_BMW_TEMP_FILE_BACKED_READBACK_READONLY.json").read_text())
    p571=json.loads(Path("docs/PRE571_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (any(p.get("status")!="AUDIT_OK" for p in (p564,p566,p571))
        or p564.get("translated_virtual_synthetic_resource_SHA256")!=NEW_SHA
        or p564.get("translated_virtual_EA_crc_hex")!=f"{NEW_CRC:08x}"
        or p566.get("file_backed_scratch_resource_readback") is not True
        or p571.get("new_handoff_readback_verified") is not True):
        raise ValueError("Prior experimental and context evidence not authenticated")
    s=session()
    entries,cd=zip_directory(s)
    z=[e for e in entries if e["name"].upper().endswith("NFS/ZDIR.BIN")]
    zz=[e for e in entries if e["name"].upper().endswith("NFS/ZZDATA4.BIN")]
    if len(z)!=1 or len(zz)!=1:raise ValueError("PTBR ZIP archive index is ambiguous")
    zdir=member_zdir(s,z[0])
    if sha(zdir)!=ZDIR_SHA:raise ValueError("Translated ZDIR source fingerprint differs")
    orig_record=struct.unpack_from("<IiIIiI",zdir,ROW*24)
    if orig_record!=(TARGET_HASH,4,0,0,OLD_SIZE,0x296ad9ed):
        raise ValueError("Translated ZDIR index row 805 differs")
    def consume(scratch):
        if len(scratch)!=NEW_SIZE or sha(scratch)!=NEW_SHA or ea_data_hash(scratch)!=NEW_CRC:
            raise ValueError("PRE502 BMW prototype identity does not match PRE564")
        patch=scratch+bytes(REGION-NEW_SIZE)
        if len(patch)!=REGION or patch[NEW_SIZE:]!=bytes(364):
            raise ValueError("Unexpected 341-sector BMW synthetic fragment")
        new_zdir=bytearray(zdir)
        struct.pack_into("<iI",new_zdir,ROW*24+16,NEW_SIZE,NEW_CRC)
        new_zdir=bytes(new_zdir)
        if (sha(new_zdir[ROW*24:(ROW+1)*24])!=EXPECTED_ZDIR_ROW_SHA or
            new_zdir[:ROW*24]!=zdir[:ROW*24] or
            new_zdir[(ROW+1)*24:]!=zdir[(ROW+1)*24:]):
            raise ValueError("Unrelated ZDIR records changed")
        summary=stream_full_archive_digest(s,zz[0],patch)
        # Keep the source ZIP and game folder unchanged. Only create new private
        # test fragments, which require a separate, verified device-side patch.
        from pre105_read_settings_source import drive_client
        d=drive_client()
        folder,created=drive_folder(d)
        index_file=ensure_private_file(d,folder,"PRE572_ZDIR_PTBR_BMW_TESTE_FRAGMENT.bin",new_zdir)
        sector_file=ensure_private_file(d,folder,"PRE572_ZZDATA4_PRIMEIROS_341_SETORES_BMW_TESTE.bin",patch)
        return {"patch_folder_id":folder,"patch_folder_newly_created":created,
            "patch_index":index_file,"patch_first_341_sectors":sector_file,
            "patch_bundle_total_bytes":len(patch)+len(new_zdir),
            "patch_sector_region_size":REGION,"patched_index_row":ROW,
            "patched_resource_size":NEW_SIZE,"patched_EA_crc32":f"{NEW_CRC:08x}",
            "patched_resource_sha256":NEW_SHA,
            "next_sector_zero_padding_bytes":REGION-NEW_SIZE,
            "standalone_GLOBAL_ATTRIBUTES_zip_member_count":sum(
                e["name"].upper().endswith("GLOBAL/ATTRIBUTES.BIN") for e in entries),
            **summary}
    r=make_scratch(consume_scratch=consume)
    detail=r.pop("_private_scratch_analysis",None)
    if r.get("status")!="AUDIT_OK" or not detail or r.get("safe_to_enable_or_build_tuning") is not False:
        raise ValueError("Original PRE502 synthetic builder returned invalid result")
    return {
       "stage":"PRE572_PRIVATE_PTBR_BMW_TEST_FRAGMENT_PREPARATION",
       "status":"AUDIT_OK",**detail,
       "original_ptbr_zip_modified":False,
       "original_ptbr_phone_folder_modified":False,
       "experimental_artifacts_private_drive_only":True,
       "full_modified_archive_built_or_exported":False,
       "guest_loader_executed":False,"BMW_tuning_enabled":False,
       "APK_built":False,"save_modified":False,"signing_accessed":False,
       "save_isolation_requirement_waived_by_user":True,
       "safe_to_overwrite_game_assets_without_backup":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args();OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as exc:
        r={"stage":"PRE572_PRIVATE_PTBR_BMW_TEST_FRAGMENT_PREPARATION","status":"FAILED",
           "error_type":type(exc).__name__,"error":str(exc)[:230],
           "original_ptbr_zip_modified":False,"original_ptbr_phone_folder_modified":False,
           "APK_built":False,"save_modified":False,"signing_accessed":False,
           "guest_loader_executed":False,"BMW_tuning_enabled":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE572_STATUS",r["status"],flush=True)
    print("PRE572_PATCH_READY",r.get("patch_bundle_total_bytes",0),flush=True)
    print("PRE572_ORIGINAL_UNTOUCHED",r.get("original_ptbr_zip_modified",False) is False,flush=True)
    print("PRE572_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
