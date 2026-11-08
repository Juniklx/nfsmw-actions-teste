#!/usr/bin/env python3
"""PRE461: parse original small ZDIR index; match hashes to public candidate names.
No executable/game asset extraction, no new APK, no save writes.
"""
import argparse, hashlib, json, re, struct, urllib.request, zlib
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from pre459_pal_zip_car_catalog_readonly import session,read_range
OUT=Path("/tmp/nfsmw-pre461/report.json")
ZIP_OFFSET=2772502468; COMPRESSED=24233; UNCOMPRESSED=33360; CRC=0x1572A136
INDEX_SHA="7f37d29f958454ec73d5dbd30068a6acb23cf92d5056fa2d944ca5c87c6637ee"
NAMES_URL="https://raw.githubusercontent.com/Ekey/NFS.BIN.Tool/main/NFS.Unpacker/NFS.Unpacker/Projects/FileNames.list"
NAMES_GIT_BLOB="da86cf16a04f5a42b85bfdc4ee792e6f18dcfe34"
ZZDATA_SIZES={0:369948672,1:349106176,2:400523264,3:347629568,4:401068032,
              5:194918400,6:481814528,7:653262848,8:200359936,9:338206720}
def raw_zdir():
    s=session()
    hdr=read_range(s,ZIP_OFFSET,30)
    if hdr[:4]!=b"PK\x03\x04":raise ValueError("Local ZIP header signature mismatch")
    fields=struct.unpack("<IHHHHHIIIHH",hdr)
    _sig,ver,flags,method,mtime,mdate,hcrc,hcsize,husize,nlen,xlen=fields
    if method!=8 or flags&1 or nlen>90 or xlen>1000:raise ValueError("Unexpected ZIP member")
    if read_range(s,ZIP_OFFSET+30,nlen)!=b"NFS/ZDIR.BIN":
        raise ValueError("Unexpected member path")
    if hcrc not in (0,CRC) or hcsize not in (0,COMPRESSED) or husize not in (0,UNCOMPRESSED):
        raise ValueError("ZIP local/member header differs from PRE459")
    compressed=read_range(s,ZIP_OFFSET+30+nlen+xlen,COMPRESSED)
    data=zlib.decompress(compressed,-15)
    if len(data)!=UNCOMPRESSED or zlib.crc32(data)&0xffffffff!=CRC:
        raise ValueError("ZDIR inflate or CRC failed")
    if hashlib.sha256(data).hexdigest()!=INDEX_SHA:
        raise ValueError("ZDIR SHA mismatch from PRE460")
    return data

def public_names():
    req=urllib.request.Request(NAMES_URL,headers={"User-Agent":"nfsmw-readonly-pre461"})
    with urllib.request.urlopen(req,timeout=50) as f:
        raw=f.read(2_000_001)
    if len(raw)>2_000_000 or len(raw)<500_000:
        raise ValueError("Unexpected public filename list size")
    blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
    if blob!=NAMES_GIT_BLOB:
        raise ValueError("Public filename list Git blob SHA mismatch")
    lines=raw.decode("utf-8-sig",errors="replace").splitlines()
    if len(lines)<20000:raise ValueError("Too few source hash candidates")
    return lines,blob

def hname(name):
    v=0xffffffff
    for c in name.upper():v=(33*v+ord(c))&0xffffffff
    return v

def audit():
    data=raw_zdir()
    if len(data)%24!=0:raise ValueError("ZDIR length not divisible by 24")
    entries=[]
    for i,(h,archive,sector,total,size,checksum) in enumerate(struct.iter_unpack("<IiIIiI",data)):
        actual_offset=sector*2048
        valid=archive in ZZDATA_SIZES and size>=0 and actual_offset+size<=ZZDATA_SIZES.get(archive,0)
        entries.append({"index":i,"name_hash":f"{h:08x}","archive_id":archive,
                        "offset":actual_offset,"size":size,"location_valid":valid})
    if len(entries)!=1390:raise ValueError("Unexpected record count")
    valid=sum(e["location_valid"] for e in entries)
    names,blob=public_names()
    lookup={}
    for name in names:
        if not name or len(name)>300:continue
        lookup.setdefault(hname(name),[]).append(name)
    matched=[]
    for e in entries:
        matches=lookup.get(int(e["name_hash"],16),[])
        if matches:
            matched.append({**e,"public_name_candidates":matches[:3]})
    rx=re.compile(r"(bmw|m3gtr|performance|upgrad|attrib|vlt|global|carpart|vehicle|physics|punto)",re.I)
    targets=[e for e in matched if any(rx.search(x) for x in e["public_name_candidates"])]
    return {
      "status":"AUDIT_OK","stage":"PRE461_BMW_INDEX_HASH_NAMES_READONLY",
      "zdir_sha256":INDEX_SHA,"zdir_records":len(entries),
      "record_size_bytes":24,"record_locations_valid":valid,
      "record_locations_invalid":len(entries)-valid,
      "archive_id_histogram":dict(Counter(str(e["archive_id"]) for e in entries)),
      "public_filename_list_git_blob_sha1":blob,"public_name_lines":len(names),
      "hash_matches_from_public_candidates":len(matched),
      "name_samples":matched[:80],"bmw_related_candidates":targets[:120],
      "candidate_names_not_confirmed_by_resource_content":True,
      "performance_upgrade_data_verified":False,"safe_to_enable_mod":False,
      "zzdata_bytes_downloaded":False,"no_files_repacked":True,
      "game_assets_uploaded":False,"save_modified":False,"apk_built":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"status":"FAILED","stage":"PRE461_BMW_INDEX_HASH_NAMES_READONLY",
                            "error_type":type(e).__name__,"error":str(e)[:220],
                            "save_modified":False,"apk_built":False}
    r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE461_STATUS",r["status"],flush=True)
    print("PRE461_VALID_INDEX_RECORDS",r.get("record_locations_valid","?"),flush=True)
    print("PRE461_MATCHED_NAMES",r.get("hash_matches_from_public_candidates","?"),flush=True)
    print("PRE461_ERROR",r.get("error_type","none"),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1

if __name__=="__main__":raise SystemExit(main())
