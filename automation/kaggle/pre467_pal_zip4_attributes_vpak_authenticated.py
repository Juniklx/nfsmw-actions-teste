#!/usr/bin/env python3
"""PRE467: authenticated PAL ATTRIBUTES.BIN from ZIP member using streaming Deflate.
Read user's PAL ZZDATA4 member in bounded HTTP206 ranges, check full member CRC
and total uncompressed length, keep only private 697856-byte VPAK in memory.
No data uploaded, APK created, or save touched. ZIP archive is never modified.
"""
from __future__ import annotations
import argparse,hashlib,json,os,struct,zlib
from datetime import datetime,timezone
from pathlib import Path
from pre459_pal_zip_car_catalog_readonly import session,read_range,API,SIZE

OUT=Path("/tmp/nfsmw-pre467/report.json")
LOCAL_OFFSET=3731333269
ZNAME=b"NFS/ZZDATA4.BIN"
COMPRESSED=261097565
UNCOMPRESSED=401068032
CRC=0xB46A396C
TARGET_START=355932160
TARGET_LENGTH=697856
EXPECTED_USA_SHA="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad"
CHUNK_BYTES=4*1024*1024
MINUTES_LIMIT="GitHub ephemeral runner: bounded file read"
CHECK_NAMES=("BMWM3GTR","BMWM3GTRE46","m3gtre46careerstart",
             "UpgradeSpecs","eFEPartUpgradeLevels","JunkmanMod")
def read_streamed_member(s,data_start):
    end_data=data_start+COMPRESSED
    if end_data>SIZE:raise ValueError("ZIP member extends beyond archive")
    cursor=0;plain_cursor=0;crc=0
    inflater=zlib.decompressobj(-15)
    target=bytearray(TARGET_LENGTH)
    collected=0;calls=0
    while cursor<COMPRESSED:
        count=min(CHUNK_BYTES,COMPRESSED-cursor)
        begin=data_start+cursor
        stop=begin+count-1
        with s.get(API,params={"alt":"media"},
           headers={"Range":f"bytes={begin}-{stop}"},
           stream=True,timeout=(25,90),allow_redirects=False) as response:
            if response.status_code!=206:
                raise ValueError("Nonpartial range response "+str(response.status_code))
            if response.headers.get("Content-Range","").strip()!=f"bytes {begin}-{stop}/{SIZE}":
                raise ValueError("ZIP streaming Range Content-Range mismatch")
            compressed=response.raw.read(count+1,decode_content=False)
        if len(compressed)!=count:raise ValueError("ZIP member ranged bytes length mismatch")
        if inflater.eof:raise ValueError("Unexpected early Deflate EOS")
        expanded=inflater.decompress(compressed)
        crc=zlib.crc32(expanded,crc)
        lo=max(TARGET_START,plain_cursor)
        hi=min(TARGET_START+TARGET_LENGTH,plain_cursor+len(expanded))
        if hi>lo:
            target[lo-TARGET_START:hi-TARGET_START]=expanded[lo-plain_cursor:hi-plain_cursor]
            collected+=hi-lo
        plain_cursor+=len(expanded)
        cursor+=count;calls+=1
        if calls%12==0:
            print("PRE467_CHECKPOINT","read_compressed",cursor,"inflated",plain_cursor,flush=True)
    final=inflater.flush()
    if final:
        crc=zlib.crc32(final,crc)
        lo=max(TARGET_START,plain_cursor)
        hi=min(TARGET_START+TARGET_LENGTH,plain_cursor+len(final))
        if hi>lo:
            target[lo-TARGET_START:hi-TARGET_START]=final[lo-plain_cursor:hi-plain_cursor]
            collected+=hi-lo
        plain_cursor+=len(final)
    if not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
        raise ValueError("Deflate stream did not end cleanly")
    if plain_cursor!=UNCOMPRESSED or (crc&0xffffffff)!=CRC or collected!=TARGET_LENGTH:
        raise ValueError("ZIP CRC, full length or targeted byte range mismatch")
    return bytes(target),{"http_range_calls":calls,
       "compressed_bytes_read":cursor,"total_deflated_bytes":plain_cursor,
       "zzdata_member_crc32":f"{crc:08x}","target_bytes_collected":collected}
def audit():
    s=session()
    meta=s.get("https://www.googleapis.com/drive/v3/files/1sF5irZpUNfN5Z2p4L53eMVISBeh8MfRz",
        params={"fields":"id,size,name"},timeout=30).json()
    if meta.get("id")!="1sF5irZpUNfN5Z2p4L53eMVISBeh8MfRz" or int(meta.get("size",0))!=SIZE:
        raise ValueError("PAL source identity/size mismatch")
    header=read_range(s,LOCAL_OFFSET,30)
    if header[:4]!=b"PK\x03\x04":raise ValueError("Local ZIP header not found")
    v=struct.unpack("<IHHHHHIIIHH",header)
    _sig,_ver,flags,method,_tm,_dt,crc,csize,usize,nlen,xlen=v
    if method!=8 or flags&1 or nlen>80 or xlen>1000:raise ValueError("Invalid ZIP member flags")
    if read_range(s,LOCAL_OFFSET+30,nlen)!=ZNAME:raise ValueError("Unexpected ZIP member name")
    if crc not in (0,CRC) or csize not in (0,COMPRESSED) or usize not in (0,UNCOMPRESSED):
        raise ValueError("Local ZIP/member metadata differs from verified central dir")
    data_start=LOCAL_OFFSET+30+nlen+xlen
    target,stats=read_streamed_member(s,data_start)
    sha=hashlib.sha256(target).hexdigest()
    if target[:4]!=b"VPAK":raise ValueError("PAL extracted resource not VPAK")
    count,strings_off,strings_size=struct.unpack_from("<III",target,4)
    if count!=1:raise ValueError("Unrecognized PAL VPAK vault count")
    nameoff,binsize,vltsize,binoff,vltoff=struct.unpack_from("<IIIII",target,16)
    if not (0<binoff<binoff+binsize<=len(target) and
            0<vltoff<vltoff+vltsize<=len(target)):
        raise ValueError("PAL VPAK section offsets outside file")
    b=target[binoff:binoff+binsize]
    v=target[vltoff:vltoff+vltsize]
    if b[:4]!=b"StrE" or v[:4]!=b"DepN":
        raise ValueError("PAL BIN/VLT section signatures mismatch")
    first_size=int.from_bytes(b[4:8],"big")
    if not (8<=first_size<=len(b)):raise ValueError("PAL BIN StrE chunk bounds")
    names=[x.decode("ascii") for x in b[8:first_size].split(b"\x00")
           if 0<len(x)<120 and all(32<=y<=126 for y in x)]
    targets={s:{"bin_name_present":s in names,
                "bin_text_occurrences":b.count(s.encode("ascii")),
                "vlt_text_occurrences":v.count(s.encode("ascii"))} for s in CHECK_NAMES}
    return {"stage":"PRE467_PAL_BMW_ATTRIBUTE_VPAK_AUTHENTICATED",
      "status":"AUDIT_OK","original_zip_size":SIZE,
      "source_archive_member":ZNAME.decode(),
      "source_member_deflate_crc32_verified":True,
      "source_member_full_uncompressed_bytes":UNCOMPRESSED,
      "pal_target_resource":"GLOBAL\\ATTRIBUTES.BIN",
      "pal_target_size_bytes":TARGET_LENGTH,
      "pal_target_sha256":sha,
      "usa_reference_sha256":EXPECTED_USA_SHA,
      "pal_resource_identical_to_usa_reference":sha==EXPECTED_USA_SHA,
      "vpak_name_count":count,"vpak_bin_size":binsize,"vpak_vlt_size":vltsize,
      "pal_bin_string_candidate_count":len(names),
      "pal_target_identifiers":targets,
      "transfer_stats":stats,
      "raw_game_assets_published":False,
      "game_archive_modified":False,"signed_apk_built":False,
      "save_modified":False,"bmw_usable_upgrades_proven":False}

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"stage":"PRE467_PAL_BMW_ATTRIBUTE_VPAK_AUTHENTICATED",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:260],
      "signed_apk_built":False,"save_modified":False,
      "game_archive_modified":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE467_STATUS",r["status"],flush=True)
    print("PRE467_PAL_SHA",r.get("pal_target_sha256","unknown"),flush=True)
    print("PRE467_MATCH_USA",r.get("pal_resource_identical_to_usa_reference","unknown"),flush=True)
    print("PRE467_ERROR",r.get("error","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
