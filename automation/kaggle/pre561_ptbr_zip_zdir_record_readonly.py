#!/usr/bin/env python3
"""PRE561: bounded read-only ZIP64 central directory + translated ZDIR member.

Do not download the full archive, ZZDATA4, executable, assets or save.
Read only ZIP metadata and the small ZDIR member via HTTP206.
Never publish original ZDIR bytes or absolute device paths.
"""
from __future__ import annotations
import argparse, hashlib, json, struct, zlib
from datetime import datetime, timezone
from pathlib import Path
from pre459_pal_zip_car_catalog_readonly import session
FILE_ID="1M95wS9iqrMI-p328Wual7TreqfaPgdL0"
SIZE=5416276032
ZIP_NAME="NFSMW_PT-BR.zip"
ZDIR_SIZE=33312
ZDIR_SHA="832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf"
ZZDATA4_SIZE=401068032
API="https://www.googleapis.com/drive/v3/files/"+FILE_ID
OUT=Path("/tmp/nfsmw-pre561/report.json")
NAMES={
 "GLOBAL_ATTRIBUTES":"9775379a",
 "GLOBAL_FE_ATTRIB":"80be7b63",
 "GLOBAL_GLOBALB_LZC":"4c939b36",
 "GLOBAL_GLOBALB_BUN":"4c937012",
 "GLOBAL_GLOBALA_BUN":"4c815791"
}
def ranged(s,start,length):
 if not (0<length<=1024*1024 and 0<=start and start+length<=SIZE):
  raise ValueError("Read outside permitted range")
 end=start+length-1
 with s.get(API,params={"alt":"media"},
     headers={"Range":f"bytes={start}-{end}","Accept-Encoding":"identity"},
     stream=True,timeout=(30,90),allow_redirects=False) as resp:
  if resp.status_code!=206 or resp.headers.get("Content-Range","").strip()!=f"bytes {start}-{end}/{SIZE}":
   raise ValueError("Strict Drive HTTP206 range unavailable")
  if resp.headers.get("Content-Encoding","identity").lower() not in ("identity",""):
   raise ValueError("Unexpected Content-Encoding")
  data=resp.raw.read(length+1,decode_content=False)
  if len(data)!=length:raise ValueError("Ranged read wrong size")
  return data
def zip_directory(s):
 metadata=s.get(API,params={"fields":"id,name,size,mimeType"},
                timeout=35).json()
 if (metadata.get("id")!=FILE_ID or metadata.get("name")!=ZIP_NAME or
     metadata.get("mimeType")!="application/zip" or int(metadata.get("size",0))!=SIZE):
  raise ValueError("Selected Drive PTBR ZIP metadata unexpected")
 tail_len=132000
 tail=ranged(s,SIZE-tail_len,tail_len)
 end=tail.rfind(b"PK\x05\x06")
 if end<0 or end+22>len(tail):raise ValueError("ZIP EOCD not found")
 (signature,disk,cd_disk,disk_entries,total_entries,cd_size,cd_offset,comment)=struct.unpack_from("<IHHHHIIH",tail,end)
 if disk!=0 or cd_disk!=0 or end+22+comment>len(tail):
  raise ValueError("Multi-disk or malformed EOCD unsupported")
 if total_entries==0xffff or cd_size==0xffffffff or cd_offset==0xffffffff:
  locator_offset=SIZE-tail_len+end-20
  locator=ranged(s,locator_offset,20)
  if locator[:4]!=b"PK\x06\x07":raise ValueError("ZIP64 locator absent")
  _,loc_disk,record_off,disks=struct.unpack("<IIQI",locator)
  if loc_disk!=0 or disks!=1:raise ValueError("Multipart ZIP64 unsupported")
  record=ranged(s,record_off,56)
  if record[:4]!=b"PK\x06\x06":raise ValueError("ZIP64 EOCD absent")
  vals=struct.unpack("<IQHHIIQQQQ",record)
  total_entries=vals[-3]
  cd_size=vals[-2]
  cd_offset=vals[-1]
 if not (2<=total_entries<=3000 and 46<=cd_size<=1000000):
  raise ValueError("Central directory size/count unexpected")
 cd=ranged(s,cd_offset,cd_size)
 pos=0
 items=[]
 for i in range(total_entries):
  if pos+46>len(cd) or cd[pos:pos+4]!=b"PK\x01\x02":raise ValueError("Broken central dir entry")
  fields=struct.unpack_from("<I6H3I5H2I",cd,pos)
  (_sig,made,need,flags,method,mt,md,crc,comp,uncomp,nlen,xlen,clen,diskstart,inter,ext,offset)=fields
  if not(1<=nlen<=500 and xlen<=65000 and clen<=65000 and pos+46+nlen+xlen+clen<=len(cd)):
   raise ValueError("Unsafe filename or extras")
  name=cd[pos+46:pos+46+nlen].decode("utf-8","replace")
  if name.startswith("/") or any(p in ("..","") for p in name.strip("/").split("/")):
   raise ValueError("Unsafe archive name")
  if flags&1:raise ValueError("Encrypted ZIP unsupported")
  if 0xffffffff in (comp,uncomp,offset):
   # ZIP64 extra entries contain only the fields that overflowed, in order.
   extra=cd[pos+46+nlen:pos+46+nlen+xlen]
   xoff=0; zip64=None
   while xoff+4<=len(extra):
    ident, sz=struct.unpack_from("<HH",extra,xoff)
    xoff+=4
    if xoff+sz>len(extra):raise ValueError("Truncated ZIP extra")
    if ident==1:zip64=extra[xoff:xoff+sz]
    xoff+=sz
   if zip64 is None:raise ValueError("ZIP64 extra missing")
   ptr=0
   values=[uncomp,comp,offset]
   for k in range(3):
    if values[k]==0xffffffff:
     if ptr+8>len(zip64):raise ValueError("ZIP64 extra incomplete")
     values[k]=struct.unpack_from("<Q",zip64,ptr)[0];ptr+=8
   uncomp,comp,offset=values
  items.append({"name":name,"uncompressed":uncomp,"compressed":comp,"offset":offset,
                "method":method,"flags":flags,"crc32":crc})
  pos+=46+nlen+xlen+clen
 if pos!=len(cd):raise ValueError("Unexpected CD suffix")
 return items,hashlib.sha256(cd).hexdigest()
def member_zdir(s,e):
 if(e["uncompressed"]!=ZDIR_SIZE or e["method"] not in (0,8)
    or e["compressed"]>300000 or e["offset"]<0):
  raise ValueError("Translated ZDIR unusual compression or size")
 off=e["offset"]; head=ranged(s,off,30)
 if head[:4]!=b"PK\x03\x04":raise ValueError("Missing ZDIR local header")
 vals=struct.unpack("<IHHHHHIIIHH",head)
 _,vers,flags,method,*_,nlen,xlen=vals
 if method!=e["method"] or flags&1 or nlen<=0 or nlen>500 or xlen>10000:
  raise ValueError("Invalid local ZIP entry header")
 actual_name=ranged(s,off+30,nlen).decode("utf-8","replace")
 if actual_name!=e["name"]:raise ValueError("Local ZDIR name mismatch")
 raw=ranged(s,off+30+nlen+xlen,e["compressed"])
 if method==8:content=zlib.decompress(raw,-15)
 else:content=raw
 if(len(content)!=ZDIR_SIZE or zlib.crc32(content)&0xffffffff!=e["crc32"] or
    hashlib.sha256(content).hexdigest()!=ZDIR_SHA):
  raise ValueError("Selected PTBR ZDIR not equal to Shevery fingerprint")
 return content
def audit():
 ref=json.loads(Path("docs/PRE558_PAL_PTBR_HASH_COMPARISON_READONLY.json").read_text())
 if(ref.get("status")!="AUDIT_OK" or
    ref.get("translated_pal_ZDIR_sha256_reported")!=ZDIR_SHA or
    ref.get("translated_pal_ZZDATA4_bytes_reported")!=ZZDATA4_SIZE or
    ref.get("translation_attributes_resource_offset_verified") is not False):
  raise ValueError("PRE558 phone report mismatch")
 sess=session()
 entries,cd_sha=zip_directory(sess)
 zdirs=[x for x in entries if x["name"].upper().endswith("NFS/ZDIR.BIN")]
 zdata=[x for x in entries if x["name"].upper().endswith("NFS/ZZDATA4.BIN")]
 if len(zdirs)!=1 or len(zdata)!=1 or zdata[0]["uncompressed"]!=ZZDATA4_SIZE:
  raise ValueError("Expected exactly one matching PTBR NFS folder ZIP index and data member")
 zdir=member_zdir(sess,zdirs[0])
 if len(zdir)%24 or len(zdir)//24!=1388:raise ValueError("Translated ZDIR stride unexpected")
 records=[]
 names={k:[] for k in NAMES}
 zero_sector=0;nonzero_sector=0;plausible=0
 for idx,(name_hash,archive,sector,total,size,crc) in enumerate(struct.iter_unpack("<IiIIiI",zdir)):
  if sector==0:zero_sector+=1
  else:nonzero_sector+=1
  if 0<=archive<=9 and size>0:plausible+=1
  hashtext=f"{name_hash:08x}"
  for label,target in NAMES.items():
   if hashtext==target:
    names[label].append({"row":idx,"archive":archive,"sector":sector,
                         "byte_offset":sector*2048,
                         "total_field":total,"resource_size":size,
                         "checksum_hex":f"{crc:08x}"})
 attr=names["GLOBAL_ATTRIBUTES"]
 if len(attr)!=1 or attr[0]["row"]!=805 or attr[0]["archive"]!=4 or attr[0]["resource_size"]!=697856:
  raise ValueError("Attributes record does not match Shevery translated results")
 # We do not assume sector 0 means resource at offset 0 before verifying format/reference.
 return {
  "stage":"PRE561_AUTHENTICATED_PTBR_ZIP_ZDIR_DIRECT_RECORD_ANALYSIS_READONLY",
  "status":"AUDIT_OK",
  "translated_source_drive_folder":"Traducao_PTBR_2026",
  "translated_source_drive_zip_id":FILE_ID,
  "translated_zip_size_bytes":SIZE,
  "zip_central_directory_sha256":cd_sha,
  "zip_entries_total":len(entries),
  "zdir_uncompressed_bytes":len(zdir),
  "zdir_sha256":ZDIR_SHA,
  "zdir_matches_shevery_sha256":True,
  "zzdata4_member_uncompressed_bytes":zdata[0]["uncompressed"],
  "zzdata4_member_zip_crc32_hex":f"{zdata[0]['crc32']:08x}",
  "zzdata4_member_compressed_bytes":zdata[0]["compressed"],
  "zzdata4_contents_not_read":True,
  "zdir_24_byte_record_count":len(zdir)//24,
  "zdir_zero_sector_count":zero_sector,
  "zdir_nonzero_sector_count":nonzero_sector,
  "zdir_archive_0_to_9_nonzero_resource_count":plausible,
  "selected_original_hash_name_matches":names,
  "reported_zero_sector_directly_confirmed_in_translated_ZDIR_bytes":attr[0]["sector"]==0,
  "actual_guest_loader_from_ptbr_zip_executed":False,
  "phone_translation_zip_matches_installed_ZZDATA4_full_sha256":False,
  "translated_resource_offset_as_operational_proven":False,
  "user_game_files_modified":False,"save_modified":False,"APK_built":False,
  "signing_material_accessed":False,"BMW_tuning_enabled":False
 }
def main():
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try: r=audit()
 except Exception as e:
  r={"stage":"PRE561_AUTHENTICATED_PTBR_ZIP_ZDIR_DIRECT_RECORD_ANALYSIS_READONLY",
     "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:250],
     "user_game_files_modified":False,"save_modified":False,
     "APK_built":False,"signing_material_accessed":False,"BMW_tuning_enabled":False}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
 print("PRE561_STATUS",r["status"],flush=True)
 print("PRE561_ROWS",r.get("zdir_24_byte_record_count"),flush=True)
 print("PRE561_ZERO_SECTORS",r.get("zdir_zero_sector_count"),flush=True)
 print("PRE561_ATTR",r.get("selected_original_hash_name_matches",{}).get("GLOBAL_ATTRIBUTES"),flush=True)
 print("PRE561_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
