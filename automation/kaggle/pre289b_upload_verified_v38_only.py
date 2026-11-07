#!/usr/bin/env python3
"""PRE289B: upload-only recovery of the verified PRE289 V38 GitHub artifact.
No source restore/build, signing, key access, modification of save or APK.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from pre105_read_settings_source import drive_client
from pre289_build_signed_v38_bmw_passive import (
    APK_NAME, DEST_FOLDER, CERT_SHA, EXPECTED_PACKAGE, VERSION_CODE,
    apk_v2_cert_sha256
)

OUT=Path("/tmp/nfsmw-pre289b/PRE289B_V38_UPLOAD_ONLY_RECOVERY.json")
EXPECTED_RUN=42354940551

def hash_file(path,which="sha256"):
    h=hashlib.new(which)
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def static_check(apk:Path,report:dict,sdk:Path):
    if str(report.get("run_id"))!=str(EXPECTED_RUN):
        raise ValueError("PRE289 original run does not match")
    valid=report.get("apk_validation") or {}
    if report.get("signed_apk_verified") is not True or report.get("pre289_bmw_logger_in_signed_apk") is not True:
        raise ValueError("PRE289 report is missing successful signed+BMW marker gates")
    if valid.get("signed_certificate_sha256_match") is not True or valid.get("version_code")!=VERSION_CODE:
        raise ValueError("PRE289 signer/version gates missing")
    if valid.get("package_id")!=EXPECTED_PACKAGE:
        raise ValueError("PRE289 package mismatch")
    if not apk.is_file() or apk.stat().st_size!=valid.get("apk_size"):
        raise ValueError("APK missing or size disagrees with PRE289 evidence")
    if hash_file(apk)!=valid.get("apk_sha256"):
        raise ValueError("APK SHA256 differs from PRE289 signed artifact")
    with zipfile.ZipFile(apk) as z:
        if z.testzip() is not None:raise ValueError("APK ZIP CRC error")
        game=z.read("lib/arm64-v8a/libmain.so")
        if b"NFSMW_PRE283_BMW_VTABLE" not in game:
            raise ValueError("BMW callback marker missing")
        if hashlib.sha256(game).hexdigest()!=valid.get("pre194_pal_main_sha256"):
            raise ValueError("PAL library differs from PRE289 report")
    apksigner=sdk/"build-tools/36.0.0/apksigner"
    aapt=sdk/"build-tools/36.0.0/aapt"
    if not apksigner.is_file() or not aapt.is_file():raise FileNotFoundError("Pinned Android build tools missing")
    signed=subprocess.run([str(apksigner),"verify","--verbose","--print-certs",str(apk)],
        capture_output=True,text=True,timeout=120)
    if signed.returncode!=0 or "Verifies" not in signed.stdout:
        raise ValueError("apksigner verify failed")
    if apk_v2_cert_sha256(apk)!=CERT_SHA:
        raise ValueError("Permanent v2 signing certificate differs")
    badges=subprocess.run([str(aapt),"dump","badging",str(apk)],
        capture_output=True,text=True,timeout=90)
    match=re.search(r"package:\s+name='([^']+)'\s+versionCode='(\d+)'",badges.stdout)
    if badges.returncode!=0 or not match or match.group(1)!=EXPECTED_PACKAGE or int(match.group(2))!=VERSION_CODE:
        raise ValueError("AAPT package/version mismatched")
    return {"sha256":hash_file(apk),"md5":hash_file(apk,"md5"),
            "size":apk.stat().st_size,"package":EXPECTED_PACKAGE,
            "versionCode":VERSION_CODE,"certificate_sha256":CERT_SHA,
            "bmw_marker_verified":True,"signed_v2_verified":True}

def find_existing(d,md5:str,size:int):
    # Search only the verified destination folder, and never replace files.
    query="name = '"+APK_NAME.replace("'","\\'")+"' and '"+DEST_FOLDER+"' in parents and trashed = false"
    found=d.files().list(q=query,fields="nextPageToken,files(id,name,size,md5Checksum,webViewLink,parents)",
          pageSize=100,supportsAllDrives=True,includeItemsFromAllDrives=True).execute().get("files",[])
    if len(found)>1:raise ValueError("Multiple destination files share name; stop")
    if not found:return None
    f=found[0]
    if int(f.get("size",-1))!=size or f.get("md5Checksum","").lower()!=md5:
        raise ValueError("Drive filename occupied by different bytes")
    return f

def upload(d,apk:Path,local:dict):
    existing=find_existing(d,local["md5"],local["size"])
    if existing:return {"id":existing["id"],"url":existing.get("webViewLink"),"reused_existing":True}
    # Retry only transient Drive upload errors; confirm possible partial success
    # by remote MD5 before another create request.
    for attempt in range(1,4):
        try:
            media=MediaFileUpload(str(apk),mimetype="application/vnd.android.package-archive",
                                  resumable=True,chunksize=4*1024*1024)
            operation=d.files().create(body={"name":APK_NAME,"parents":[DEST_FOLDER],
              "mimeType":"application/vnd.android.package-archive"},media_body=media,
              fields="id,name,size,md5Checksum,webViewLink,parents",supportsAllDrives=True)
            response=None
            while response is None:
                _progress,response=operation.next_chunk(num_retries=4)
            check=find_existing(d,local["md5"],local["size"])
            if check is None or check["id"]!=response.get("id"):
                raise ValueError("Drive upload readback missing or mismatched")
            return {"id":check["id"],"url":check.get("webViewLink"),
                    "reused_existing":False,"attempts":attempt}
        except Exception as exc:
            existing=find_existing(d,local["md5"],local["size"])
            if existing:return {"id":existing["id"],"url":existing.get("webViewLink"),
                                "reused_existing":True,"attempts":attempt}
            status=getattr(getattr(exc,"resp",None),"status",None)
            if not (status in (429,500,502,503,504) or isinstance(exc,(TimeoutError,ConnectionError))):
                raise
            if attempt==3:raise
            time.sleep(min(attempt*3,9))
    raise RuntimeError("Upload attempts exhausted")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apk",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE289B_V38_UPLOAD_ONLY","status":"FAILED",
      "original_run_id":EXPECTED_RUN,"new_build":False,"signed_again":False,
      "save_modified":False,"signing_key_accessed":False,
      "utc":datetime.now(timezone.utc).isoformat()}
    try:
        original=json.loads(args.report.read_text(encoding="utf-8"))
        sdk=Path(os.getenv("ANDROID_HOME") or os.getenv("ANDROID_SDK_ROOT") or "/usr/local/lib/android/sdk")
        checked=static_check(args.apk,original,sdk)
        result["artifact_verified"]=checked
        d=drive_client()
        result["drive_upload"]=upload(d,args.apk,checked)
        result["status"]="AUDIT_OK"
    except Exception as ex:
        result["error_type"]=type(ex).__name__
        result["http_status"]=getattr(getattr(ex,"resp",None),"status",None)
        result["status"]="UPLOAD_OR_VALIDATION_FAILED"
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE289B_STATUS",result["status"])
    print("PRE289B_APK_VERIFIED",bool(result.get("artifact_verified")))
    print("PRE289B_DRIVE_FILE_ID",result.get("drive_upload",{}).get("id"))
    print("PRE289B_ERROR_TYPE",result.get("error_type"))
    print("PRE289B_HTTP_STATUS",result.get("http_status"))
    return 0 if result["status"]=="AUDIT_OK" else 1

if __name__=="__main__":sys.exit(main())
