#!/usr/bin/env python3
"""PRE158: publish exact signed PRE157/V32 APK without rebuild or re-sign."""
import argparse,hashlib,json,re,subprocess,time,zipfile
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from pre105_read_settings_source import drive_client
from pre127_apk_v2_certificate_audit import apk_v2_cert_sha256
from pre138_build_signed_v31_log_pal_usa import latest_tool,sdk_root,PRESERVE,REQUIRED_LIBS

APK_NAME="NFSMW_V32_PRE157_CALLBACK_MOVE_EXPERIMENTAL.apk"
SHA="47e983b7bd96308716d817dee555af787048932642f616ae237e746bc6cdb47b"
CERT="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
FOLDER="1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh"
SIZE=47101249

def hash_file(path,algo="sha256"):
    h=hashlib.new(algo)
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(8*1024*1024),b""):h.update(block)
    return h.hexdigest()

def validate(apk,original,result):
    r=json.loads(original.read_text())
    if (r.get("run_id")!="41954648085" or r.get("gradle_release_succeeded") is not True or
        r.get("signed_apk_verified") is not True or r.get("pre157_callback_move_applied") is not True or
        r.get("apk_candidate_sha256")!=SHA or r.get("error_type")!="ResumableUploadError"):
        raise ValueError("PRE157 original evidence invalid")
    if apk.stat().st_size!=SIZE or hash_file(apk)!=SHA:
        raise ValueError("PRE157 APK bytes differ")
    with zipfile.ZipFile(apk) as z:
        if z.testzip() is not None:raise ValueError("ZIP corrupted")
        for lib in REQUIRED_LIBS:
            if "lib/arm64-v8a/"+lib not in z.namelist():raise ValueError("ARM64 missing")
        for name,digest in PRESERVE.items():
            if hashlib.sha256(z.read(name)).hexdigest()!=digest:raise ValueError("Preserved asset changed")
    sdk=sdk_root()
    run=subprocess.run([str(latest_tool(sdk,"apksigner")),"verify","--verbose",str(apk)],
                       capture_output=True,text=True,timeout=120)
    if run.returncode:raise ValueError("apksigner verify failed")
    if apk_v2_cert_sha256(apk)!=CERT:raise ValueError("Permanent certificate mismatch")
    run=subprocess.run([str(latest_tool(sdk,"aapt")),"dump","badging",str(apk)],
                       capture_output=True,text=True,timeout=120)
    m=re.search(r"package:\s+name='([^']+)'\s+versionCode='(\d+)'",run.stdout)
    if run.returncode or m is None or m.groups()!=("io.github.nfsmwrecomp","32"):
        raise ValueError("Package or versionCode mismatch")
    result.update({"apk_sha256":SHA,"apk_bytes":SIZE,"apk_md5":hash_file(apk,"md5"),
                   "original_build_verified":True,"signature_verified":True,
                   "package_version_verified":True,"assets_verified":True})

def inspect(drive,result):
    q="name = '"+APK_NAME+"' and '"+FOLDER+"' in parents and trashed = false"
    ret=drive.files().list(q=q,fields="nextPageToken,files(id,name,size,md5Checksum,parents,webViewLink)",
                           pageSize=100,supportsAllDrives=True,includeItemsFromAllDrives=True).execute()
    files=ret.get("files",[])
    if ret.get("nextPageToken") or len(files)>1:raise ValueError("Ambiguous Drive entries")
    if files:
        f=files[0]
        if int(f.get("size",-1))!=SIZE or f.get("md5Checksum","").lower()!=result["apk_md5"]:
            raise ValueError("Conflicting Drive file exists")
        return f
    return None

def publish(drive,apk,result):
    old=inspect(drive,result)
    if old:
        result["reused_existing_verified_drive_file"]=True
        return old
    media=MediaFileUpload(str(apk),mimetype="application/vnd.android.package-archive",
                          chunksize=8*1024*1024,resumable=True)
    request=drive.files().create(body={"name":APK_NAME,"parents":[FOLDER],
                "mimeType":"application/vnd.android.package-archive"},media_body=media,
                fields="id,name,size,md5Checksum,parents",supportsAllDrives=True)
    final=None;retries=0
    while final is None:
        try:
            _,final=request.next_chunk(num_retries=3)
        except HttpError as e:
            retries+=1
            status=int(getattr(e.resp,"status",0))
            reason=""
            try:reason=json.loads(e.content).get("error",{}).get("errors",[{}])[0].get("reason","")
            except (ValueError,TypeError,IndexError,AttributeError):pass
            reason=str(reason)[:60]
            result.update({"last_upload_http_status":status,"last_upload_reason":reason,"upload_retries":retries})
            print("Drive upload HTTP",status,"reason",reason)
            retryable=status in (429,500,502,503,504) or (
                status==403 and reason in ("rateLimitExceeded","userRateLimitExceeded"))
            if not retryable or retries>=5:raise
            found=inspect(drive,result)
            if found:return found
            time.sleep(4*retries)
    return final

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--apk",type=Path,required=True)
    a.add_argument("--original-report",type=Path,required=True)
    a.add_argument("--report",type=Path,required=True)
    args=a.parse_args()
    result={"stage":"PRE158_RECOVER_V32","source_run":"41954648085",
      "source_artifact_id":"13383197634","status":"NOT_VERIFIED",
      "rebuild":False,"resign":False,"signing_credentials_read":False,
      "v31_changed":False,"phone_tested":False,"fps_gain_proven":False}
    try:
        validate(args.apk,args.original_report,result)
        drive=drive_client()
        f=publish(drive,args.apk,result)
        f=drive.files().get(fileId=f["id"],fields="id,name,size,md5Checksum,parents",
                             supportsAllDrives=True).execute()
        if (f.get("name")!=APK_NAME or int(f.get("size",-1))!=SIZE or
            f.get("md5Checksum","").lower()!=result["apk_md5"] or FOLDER not in f.get("parents",[])):
            raise ValueError("Drive file readback failed")
        result.update({"status":"PRE158_V32_PUBLISHED_VERIFIED","drive_upload_success":True,
                       "drive_file_id":f["id"],"drive_file_size":SIZE,"drive_md5_verified":True})
        print("PRE158 SUCCESS. APK verified in Drive, file ID:",f["id"])
    except Exception as e:
        result["error_type"]=type(e).__name__
        print("PRE158 failed safely:",type(e).__name__)
    finally:
        result["utc"]=datetime.now(timezone.utc).isoformat()
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    return 0 if result["status"]=="PRE158_V32_PUBLISHED_VERIFIED" else 1

if __name__=="__main__":raise SystemExit(main())
