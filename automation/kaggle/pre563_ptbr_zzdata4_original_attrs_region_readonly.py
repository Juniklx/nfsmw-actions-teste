#!/usr/bin/env python3
"""PRE563: authenticate translated PTBR ZIP ZZDATA4 full member via strict HTTP206,
then inspect its first 341 sectors as indicated by authenticated ZDIR attributes
row 805. Only SHA/CRC/numerical evidence released. Never publish assets, APK,
source game files, save, or altered data; no guest executable or loader run.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,zlib
from datetime import datetime,timezone
from pathlib import Path
from pre459_pal_zip_car_catalog_readonly import session
from pre561_ptbr_zip_zdir_record_readonly import (
 API,SIZE,ZIP_NAME,FILE_ID,zip_directory,member_zdir,ranged,ZDIR_SHA)
from pre517_original_zdir_ea_checksum_readonly import ea_data_hash
OUT=Path("/tmp/nfsmw-pre563/report.json")
PAL_VPAK_SHA="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
PHONE_ZZDATA4_SHA="7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951"
ATTRIBUTES_NAME_HASH=0x9775379a
ATTRIBUTES_BYTES=697856
RESERVED=698368
ZIP_ZZ_CRC=0xa038afed
ZIP_ZZ_UNCOMPRESSED=401068032
ZIP_ZZ_COMPRESSED=261092849
def stream_member(session_obj,entry):
 if(entry["method"]!=8 or entry["compressed"]!=ZIP_ZZ_COMPRESSED or
    entry["uncompressed"]!=ZIP_ZZ_UNCOMPRESSED or entry["crc32"]!=ZIP_ZZ_CRC or
    entry["flags"]&1):
  raise ValueError("ZIP metadata for translated ZZDATA4 changed")
 off=entry["offset"]
 header=ranged(session_obj,off,30)
 if header[:4]!=b"PK\x03\x04":raise ValueError("Missing local ZIP header")
 _,v,flags,method,tm,dt,crc,compressed,uncompressed,nlen,xlen=struct.unpack("<IHHHHHIIIHH",header)
 if method!=8 or flags&1 or not (1<=nlen<=450 and 0<=xlen<=4096):
  raise ValueError("Invalid local ZIP member header")
 actual_name=ranged(session_obj,off+30,nlen).decode("utf-8","replace")
 if actual_name!=entry["name"]:raise ValueError("ZIP local member name mismatch")
 start=off+30+nlen+xlen
 end=start+ZIP_ZZ_COMPRESSED-1
 if not (start>0 and end<SIZE):raise ValueError("ZIP compressed byte span outside source")
 sha=hashlib.sha256(); crc32=zlib.crc32(b"")
 inflate=zlib.decompressobj(-15)
 seen_compressed=0; seen_uncompressed=0
 sector=bytearray(RESERVED); covered=0
 def accept(chunk):
  nonlocal seen_uncompressed,crc32,covered
  if not chunk:return
  begin=seen_uncompressed
  seen_uncompressed+=len(chunk)
  if seen_uncompressed>ZIP_ZZ_UNCOMPRESSED:
   raise ValueError("Inflated stream beyond claimed uncompressed file size")
  sha.update(chunk);crc32=zlib.crc32(chunk,crc32)
  overlap_begin=max(0,begin)
  overlap_end=min(RESERVED,seen_uncompressed)
  if overlap_begin<overlap_end:
   sector[overlap_begin:overlap_end]=chunk[overlap_begin-begin:overlap_end-begin]
   covered+=overlap_end-overlap_begin
 with session_obj.get(API,params={"alt":"media"},headers={
     "Range":f"bytes={start}-{end}","Accept-Encoding":"identity"},
     stream=True,timeout=(35,200),allow_redirects=False) as resp:
  if(resp.status_code!=206 or resp.headers.get("Content-Range","").strip()
     !=f"bytes {start}-{end}/{SIZE}" or
     resp.headers.get("Content-Encoding","identity").lower() not in ("identity","")):
   raise ValueError("PTBR ZIP compressed member strict HTTP206 unavailable")
  for chunk in resp.iter_content(chunk_size=512*1024):
   if not chunk:continue
   seen_compressed+=len(chunk)
   if seen_compressed>ZIP_ZZ_COMPRESSED:
    raise ValueError("Compressed member overflow")
   accept(inflate.decompress(chunk))
  accept(inflate.flush())
 if (seen_compressed!=ZIP_ZZ_COMPRESSED or seen_uncompressed!=ZIP_ZZ_UNCOMPRESSED
     or crc32&0xffffffff!=ZIP_ZZ_CRC or not inflate.eof or
     inflate.unused_data or inflate.unconsumed_tail or covered!=RESERVED):
  raise ValueError("Translated ZZDATA4 incomplete or CRC32 mismatch")
 return bytes(sector),sha.hexdigest(),f"{crc32&0xffffffff:08x}"
def audit():
 prior=json.loads(Path("docs/PRE562_ORIGINAL_VS_PTBR_ZDIR_RECORD_DIFF_READONLY.json").read_text())
 src=json.loads(Path("docs/PRE561_PTBR_ZIP_ZDIR_DIRECT_RECORD_READONLY.json").read_text())
 if(prior.get("status")!="AUDIT_OK" or
    prior.get("attributes_record_translated",{}).get("sector")!=0 or
    prior.get("attributes_record_translated",{}).get("size")!=ATTRIBUTES_BYTES or
    prior.get("attributes_record_translated",{}).get("archive")!=4 or
    src.get("status")!="AUDIT_OK" or
    src.get("zzdata4_member_zip_crc32_hex")!=f"{ZIP_ZZ_CRC:08x}"):
  raise ValueError("PRE561/PRE562 translated index evidence gate failed")
 s=session();entries,central_sha=zip_directory(s)
 zs=[e for e in entries if e["name"].upper().endswith("NFS/ZDIR.BIN")]
 z4s=[e for e in entries if e["name"].upper().endswith("NFS/ZZDATA4.BIN")]
 if len(zs)!=1 or len(z4s)!=1:raise ValueError("Ambiguous PTBR NFS archive members")
 zb=member_zdir(s,zs[0])
 attrs=[(i,a,sec,total,size,ck) for i,(h,a,sec,total,size,ck)
        in enumerate(struct.iter_unpack("<IiIIiI",zb)) if h==ATTRIBUTES_NAME_HASH]
 if attrs!=[(805,4,0,0,ATTRIBUTES_BYTES,0x296ad9ed)]:
  raise ValueError("Translated ZDIR attributes target changed")
 others=sorted({sec for h,a,sec,total,size,ck in struct.iter_unpack("<IiIIiI",zb)
                if a==4 and sec>0 and size>0})
 first_next_sector=others[0] if others else None
 region,full_sha,full_crc=stream_member(s,z4s[0])
 source=region[:ATTRIBUTES_BYTES]
 pad=region[ATTRIBUTES_BYTES:]
 firstsha=hashlib.sha256(source).hexdigest()
 checksum=ea_data_hash(source)
 padzeros=sum(x==0 for x in pad)
 if full_sha!=PHONE_ZZDATA4_SHA:
  raise ValueError("PTBR ZIP ZZDATA4 does not match Shevery full-file SHA256")
 return {
  "stage":"PRE563_TRANSLATED_PAL_ZZDATA4_SOURCE_ZIP_SHA256_AND_ATTRIBUTES_FIRST_SECTORS",
  "status":"AUDIT_OK",
  "translated_zip_source_file_id":FILE_ID,
  "translated_zip_central_directory_sha256":central_sha,
  "source_ZDIR_verified_against_Shevery":True,
  "attributes_record_row":805,
  "attributes_record_archive":4,
  "attributes_record_sector":0,
  "attributes_record_resource_bytes":ATTRIBUTES_BYTES,
  "attributes_record_ZDIR_checksum_hex":"296ad9ed",
  "first_next_positive_ZZDATA4_sector_from_ZDIR":first_next_sector,
  "first_resource_bytes_SHA256":firstsha,
  "original_PAL_ATTRIBUTES_VPAK_SHA256":PAL_VPAK_SHA,
  "first_resource_identical_to_original_PAL_ATTRIBUTES_VPAK":firstsha==PAL_VPAK_SHA,
  "first_resource_EA_hash_hex":f"{checksum:08x}",
  "first_resource_EA_hash_matches_ZDIR_checksum":checksum==0x296ad9ed,
  "first_reserved_sector_region_bytes":RESERVED,
  "first_region_trailing_padding_bytes":len(pad),
  "first_region_trailing_zero_count":padzeros,
  "first_region_trailing_all_zero":padzeros==len(pad),
  "original_ZZDATA4_SHA256_from_PRE557":"8b0e6c09b9e55e78d319521b634119055ad6fb2f144aa13660f60bdea7cf05d3",
  "translated_ZZDATA4_full_uncompressed_bytes":ZIP_ZZ_UNCOMPRESSED,
  "translated_ZZDATA4_full_uncompressed_SHA256":full_sha,
  "translated_ZZDATA4_full_crc32":full_crc,
  "translated_ZZDATA4_full_file_matches_Shevery_SHA256":True,
  "full_zip_original_or_translated_asset_written_or_uploaded":False,
  "source_ZZDATA4_member_streamed_ephemerally":True,
  "guest_game_loader_executed":False,
  "guest_accepts_modified_ATTRIBUTES":False,
  "BMW_tuning_usable_or_saved":False,
  "APK_built":False,"save_modified":False,"game_assets_modified":False,
  "signing_material_accessed":False,"BMW_tuning_enabled":False
 }
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:
  r={"stage":"PRE563_TRANSLATED_PAL_ZZDATA4_SOURCE_ZIP_SHA256_AND_ATTRIBUTES_FIRST_SECTORS",
     "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
     "full_zip_original_or_translated_asset_written_or_uploaded":False,
     "guest_game_loader_executed":False,"guest_accepts_modified_ATTRIBUTES":False,
     "APK_built":False,"save_modified":False,"game_assets_modified":False,
     "signing_material_accessed":False,"BMW_tuning_enabled":False}
 r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("PRE563_STATUS",r["status"],flush=True)
 print("PRE563_NEXT_SECTOR",r.get("first_next_positive_ZZDATA4_sector_from_ZDIR"),flush=True)
 print("PRE563_VPAK_SHA_MATCH",r.get("first_resource_identical_to_original_PAL_ATTRIBUTES_VPAK"),flush=True)
 print("PRE563_CRC_MATCH",r.get("first_resource_EA_hash_matches_ZDIR_checksum"),flush=True)
 print("PRE563_PHONE_ZZDATA_SHA_MATCH",r.get("translated_ZZDATA4_full_file_matches_Shevery_SHA256"),flush=True)
 print("PRE563_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
