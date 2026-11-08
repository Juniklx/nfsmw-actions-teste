#!/usr/bin/env python3
"""PRE459: read ZIP64 directory for user's PAL game archive via STRICT HTTP 206.
Only file names/metadata; never download or publish game assets or executables.
"""
import argparse, hashlib, json, os, struct, sys
from pathlib import Path
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request, AuthorizedSession

FILE_ID="1sF5irZpUNfN5Z2p4L53eMVISBeh8MfRz"
SIZE=5567403879
EXPECTED_CD_SHA="a74f69e40ec0cc84ff58fcbf9fcccdd7353996c75592779ec63f09cf7dfdc7d6"
API="https://www.googleapis.com/drive/v3/files/"+FILE_ID
OUT=Path("/tmp/nfsmw-pre459/report.json")

def session():
    c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    c.refresh(Request())
    return AuthorizedSession(c)

def read_range(sess,start,length):
    if length<1 or length>300000 or start<0 or start+length>SIZE:
        raise ValueError("Out-of-bounds or over-budget byte range")
    end=start+length-1
    with sess.get(API,params={"alt":"media"},
         headers={"Range":f"bytes={start}-{end}"},stream=True,
         timeout=(20,50),allow_redirects=False) as response:
        if response.status_code!=206:raise ValueError("Strict range rejected HTTP "+str(response.status_code))
        expected=f"bytes {start}-{end}/{SIZE}"
        if response.headers.get("Content-Range","").strip()!=expected:
            raise ValueError("Range response mismatch")
        data=response.raw.read(length+1,decode_content=False)
        if len(data)!=length:raise ValueError("Ranged content truncated/oversized")
        return data

def inspect(sess):
    meta=sess.get(API,params={"fields":"id,name,size,mimeType,md5Checksum"},
                  timeout=35).json()
    if meta.get("id")!=FILE_ID or int(meta.get("size",0))!=SIZE:
        raise ValueError("Archive metadata identity or size changed")
    tail_len=140000
    tail=read_range(sess,SIZE-tail_len,tail_len)
    pos=tail.rfind(b"PK\\x05\\x06")
    if pos<0 or pos+22>len(tail):raise ValueError("ZIP EOCD absent")
    fields=struct.unpack_from("<IHHHHIIH",tail,pos)
    disk,cd_disk,count,cd_size,cd_offset=fields[1],fields[2],fields[4],fields[5],fields[6]
    if disk or cd_disk:raise ValueError("Multipart ZIP unsupported")
    if count==0xFFFF or cd_offset==0xFFFFFFFF or cd_size==0xFFFFFFFF:
        locator_at=SIZE-tail_len+pos-20
        locator=read_range(sess,locator_at,20)
        if locator[:4]!=b"PK\\x06\\x07":raise ValueError("ZIP64 locator absent")
        _sig,_disk,record_off,_disks=struct.unpack("<IIQI",locator)
        record=read_range(sess,record_off,56)
        if record[:4]!=b"PK\\x06\\x06":raise ValueError("ZIP64 record absent")
        vals=struct.unpack("<IQHHIIQQQQ",record)
        count,cd_size,cd_offset=vals[-3:]
    if count!=53 or not (1<=cd_size<=100000):
        raise ValueError("ZIP directory does not match PRE212 count/size bounds")
    cd=read_range(sess,cd_offset,cd_size)
    cd_sha=hashlib.sha256(cd).hexdigest()
    if cd_sha!=EXPECTED_CD_SHA:raise ValueError("PRE212 central directory SHA changed")
    pos=0; entries=[]
    for i in range(count):
        if pos+46>len(cd) or cd[pos:pos+4]!=b"PK\\x01\\x02":
            raise ValueError("Unexpected ZIP directory member")
        vals=struct.unpack_from("<I6H3I5H2I",cd,pos)
        (_,made,need,flags,method,mt,md,crc,csize,usize,nlen,xlen,clen,diskno,ia,ea,offset)=vals
        if nlen>4096 or xlen>65535 or clen>65535:raise ValueError("Invalid member length")
        end=pos+46+nlen+xlen+clen
        if end>len(cd):raise ValueError("Member extends beyond directory")
        name=cd[pos+46:pos+46+nlen].decode("utf-8","replace")
        if not name or name.startswith("/") or ".." in name.split("/") or chr(0) in name:
            raise ValueError("Unsafe member name")
        entries.append({"name":name[:250],"uncompressed_bytes":usize,
                        "compressed_bytes":csize,"method":method,
                        "flags":flags,"crc32":f"{crc:08x}",
                        "xex":name.lower().endswith(".xex")})
        pos=end
    if len(entries)!=53 or not any(e["xex"] for e in entries):
        raise ValueError("Unexpected archive layout")
    return {"source_name":meta.get("name"),"source_size":SIZE,
            "source_file_id":FILE_ID,"cd_sha256":cd_sha,
            "central_dir_offset":cd_offset,"central_dir_bytes":cd_size,
            "entry_count":len(entries),"entries":entries,
            "data_bytes_read_max":140000+20+56+cd_size,
            "assets_downloaded":False,"executable_extracted":False}

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try: result={"status":"AUDIT_OK","stage":"PRE459_PAL_ZIP_CATALOG_PATHS_ONLY",
                 **inspect(session())}
    except Exception as e:
        result={"status":"FAILED","stage":"PRE459_PAL_ZIP_CATALOG_PATHS_ONLY",
                "error_type":type(e).__name__,"error":str(e)[:200]}
    result.update({"run_id":a.run_id,"utc":datetime.now(timezone.utc).isoformat(),
                   "apk_built":False,"save_touched":False})
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\\n")
    print("PRE459_STATUS",result["status"],flush=True)
    print("PRE459_DIR_ENTRIES",result.get("entry_count","no"),flush=True)
    print("PRE459_ERROR",result.get("error_type","none"),flush=True)
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":sys.exit(main())
