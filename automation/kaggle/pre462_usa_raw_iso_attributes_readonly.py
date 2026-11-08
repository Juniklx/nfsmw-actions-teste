#!/usr/bin/env python3
"""PRE462: independently verify USA ISO XDVDFS resources and bounded BMW tuning
attribute file header by strict byte ranges. Never publish assets or alter game.
USA is a reference ONLY; no claim it equals PAL runtime data.
"""
from __future__ import annotations
import argparse, hashlib, json, re, struct
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from pre459_pal_zip_car_catalog_readonly import session
ISO_ID="1eDWuZTPrtfzk-2qD1l1YgN6GYg-_9mfr"
ISO_SIZE=7834892288
PARTITION_BASE=0x0FD90000
SECTOR=2048
ROOT_OFFSET=1791664128
ROOT_SHA="679b0b7f4ebacdc44b755410f2ab4a204ad7f9797d6d83ea8684c38c33e698af"
EXPECTED_NFS_SECTOR=746936
NAMES={"GLOBAL\\ATTRIBUTES.BIN":0x9775379A,"GLOBAL\\FE_ATTRIB.BIN":0x80BE7B63,
       "GLOBAL\\GLOBALB.LZC":0x4C939B36,"GLOBAL\\GLOBALB.BUN":0x4C937012,
       "GLOBAL\\GLOBALA.BUN":0x4C815791}
OUT=Path("/tmp/nfsmw-pre462/report.json")
class Reader:
    def __init__(self):
        self.session=session();self.total=0;self.requests=0
    def read(self,start,length):
        if length<=0 or length>1024*1024 or start<0 or start+length>ISO_SIZE:
            raise ValueError("Range outside data bounds")
        if self.total+length>2*1024*1024:
            raise ValueError("Transfer budget 2 MiB exceeded")
        end=start+length-1
        url="https://www.googleapis.com/drive/v3/files/"+ISO_ID
        with self.session.get(url,params={"alt":"media"},
             headers={"Range":f"bytes={start}-{end}"},stream=True,
             timeout=(20,65),allow_redirects=False) as response:
            if response.status_code!=206:
                raise ValueError("Strict HTTP206 required: "+str(response.status_code))
            if response.headers.get("Content-Range","").strip()!=f"bytes {start}-{end}/{ISO_SIZE}":
                raise ValueError("HTTP Content-Range identity mismatch")
            data=response.raw.read(length+1,decode_content=False)
        if len(data)!=length:raise ValueError("Received unexpected range length")
        self.requests+=1;self.total+=length
        return data

def dir_entries(data):
    found=[];seen=set();stack=[0]
    while stack:
        i=stack.pop()
        if i in seen:continue
        seen.add(i)
        if len(seen)>500 or i<0 or i+14>len(data):
            raise ValueError("Directory table bounds error")
        left,right,sector,size,attr,nlen=struct.unpack_from("<HHIIBB",data,i)
        if nlen<1 or nlen>170 or i+14+nlen>len(data):
            raise ValueError("Invalid directory name")
        name=data[i+14:i+14+nlen].decode("latin-1","replace")
        found.append({"name":name,"sector":sector,"size":size,
                      "is_dir":bool(attr&0x10)})
        for p in (left,right):
            if p not in (0,65535):
                j=p*4
                if j>=len(data):raise ValueError("Directory pointer out of bounds")
                stack.append(j)
    return found

def iso_offset(entry):
    return PARTITION_BASE+entry["sector"]*SECTOR

def audit():
    r=Reader()
    metadata=r.session.get("https://www.googleapis.com/drive/v3/files/"+ISO_ID,
                 params={"fields":"id,name,size,md5Checksum"},timeout=25).json()
    if metadata.get("id")!=ISO_ID or int(metadata.get("size",0))!=ISO_SIZE:
        raise ValueError("USA ISO identity/size mismatch")
    root=r.read(ROOT_OFFSET,2048)
    if hashlib.sha256(root).hexdigest()!=ROOT_SHA:
        raise ValueError("PRE216 XDVDFS root SHA mismatch")
    top=dir_entries(root)
    nfs=[x for x in top if x["name"].upper()=="NFS" and x["is_dir"]]
    if len(nfs)!=1 or nfs[0]["sector"]!=EXPECTED_NFS_SECTOR or nfs[0]["size"]!=2048:
        raise ValueError("PRE216 NFS directory entry changed")
    tree=r.read(iso_offset(nfs[0]),nfs[0]["size"])
    children=dir_entries(tree)
    names={x["name"].upper():x for x in children}
    z=names.get("ZDIR.BIN")
    if not z or z["is_dir"] or z["size"]>100000 or z["size"]<24:
        raise ValueError("USA ZDIR is unavailable or suspicious")
    zdir=r.read(iso_offset(z),z["size"])
    if len(zdir)%24:raise ValueError("USA ZDIR not a 24-byte record file")
    zz={i:names.get("ZZDATA"+str(i)+".BIN") for i in range(10)}
    if not all(zz.values()):raise ValueError("Missing USA ZZDATA files")
    records=[]
    valid=0
    for h,archive,sector,total,size,crc in struct.iter_unpack("<IiIIiI",zdir):
        e=zz.get(archive)
        is_valid=e is not None and not e["is_dir"] and size>=0 and (sector*SECTOR+size)<=e["size"]
        records.append({"hash":h,"archive":archive,"offset":sector*SECTOR,"size":size,
                        "location_valid":is_valid})
        valid+=int(is_valid)
    targets={}
    for title,h in NAMES.items():
        found=[x for x in records if x["hash"]==h and x["location_valid"]]
        targets[title]={"entries":len(found),"locations":[
            {"archive":x["archive"],"offset":x["offset"],"size":x["size"]} for x in found[:3]]}
    selected=[x for x in records if x["hash"]==NAMES["GLOBAL\\ATTRIBUTES.BIN"] and
              x["location_valid"] and x["size"]<=950000 and x["size"]>1000]
    sample=None
    if len(selected)==1:
        e=selected[0];file=zz[e["archive"]]
        raw=r.read(iso_offset(file)+e["offset"],min(e["size"],131072))
        sample={
          "resource":"GLOBAL\\ATTRIBUTES.BIN",
          "bytes_inspected":len(raw),"total_resource_size":e["size"],
          "first_16_bytes_hex":raw[:16].hex(),
          "first_4_big_endian":int.from_bytes(raw[:4],"big"),
          "first_4_little_endian":int.from_bytes(raw[:4],"little"),
          "head_sha256":hashlib.sha256(raw).hexdigest(),
          "ascii_bmw_occurrences":len(re.findall(rb"(?i)BMW|M3GTR",raw)),
          "ascii_upgrade_occurrences":len(re.findall(rb"(?i)UPGRADE|TUNING|ENGINE",raw)),
          "zero_byte_count":raw.count(b"\x00"),
        }
    return {
      "stage":"PRE462_USA_XDVDFS_CATALOG_REFERENCE_READONLY","status":"AUDIT_OK",
      "source_drive_file_id":ISO_ID,
      "usa_independent_of_pal":True,"usa_not_proven_equal_to_pal":True,
      "nfs_directory_entries":len(children),
      "nfs_directory_names":[{"name":x["name"],"size":x["size"]} for x in children],
      "zdir_sha256":hashlib.sha256(zdir).hexdigest(),
      "zdir_size":len(zdir),"zdir_records":len(records),"valid_zzdata_locations":valid,
      "resource_candidates":targets,"attribute_sample_metadata":sample,
      "strict_http_206_requests":r.requests,"bytes_transferred":r.total,
      "raw_game_assets_uploaded":False,"apk_built":False,"save_modified":False,
      "bmw_parts_proven_compatible":False,"feature_enabled":False
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try: result=audit()
    except Exception as e: result={"stage":"PRE462_USA_XDVDFS_CATALOG_REFERENCE_READONLY",
      "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:260],
      "apk_built":False,"save_modified":False}
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE462_STATUS",result["status"],flush=True)
    print("PRE462_INDEX",result.get("zdir_records","unknown"),"VALID",result.get("valid_zzdata_locations","unknown"),flush=True)
    print("PRE462_ATTRIB_SAMPLE",result.get("attribute_sample_metadata","none"),flush=True)
    print("PRE462_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
