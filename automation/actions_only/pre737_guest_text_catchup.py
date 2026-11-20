#!/usr/bin/env python3
"""PRE737: read-only text search of authenticated generated guest C++ in PRE99.

Scans source IN PRIVATE and reports only member names, counts and function IDs.
Does not publish extracted guest code, write game assets, or build an APK.
"""
import argparse
import hashlib
import json
import re
import tarfile
import tempfile
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from pre104_verify_backup_tar import BACKUP_ID, EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

DEST_FOLDER="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
MAX_BYTES=250 * 1024 * 1024
PATS={
    "catchup_hash_hex": re.compile(rb"(?i)0x0*10db04e6\b"),
    "catchup_hash_decimal": re.compile(rb"\b282789094\b"),
    "catchup_hash_eight_digits": re.compile(rb"(?i)\b10db04e6\b"),
    "catchup_symbol": re.compile(rb"(?i)catchup"),
    "split_immediate_high": re.compile(rb"(?i)\b0x10db\b"),
    "split_immediate_low": re.compile(rb"(?i)\b0x04e6\b")
}
FUNCTION_RE=re.compile(rb"\bsub_82[0-9A-Fa-f]{6,8}\b")
SUFFIXES=(".cpp",".h",".hpp",".c")


def inspect(path):
    result={"stage":"PRE737_AUTHENTICATED_PRE99_GUEST_SOURCE_TEXT_READONLY",
            "backup_sha_verified":True,
            "candidate_cpp_files":0,"candidate_bytes":0,
            "match_files":[],"full_guest_code_exported":False,
            "runtime_function_validated":False,
            "guest_hook_applied":False,"apk_built":False,"signing_accessed":False}
    with tarfile.open(path,"r:gz",errorlevel=2) as archive:
        for member in archive:
            low=member.name.lower()
            if not member.isfile() or not low.endswith(SUFFIXES) or not (
                "/generated/" in low or "/generated-android/" in low or "/ppc/" in low
                or "/game_recompiled/" in low):
                continue
            if not 0<=member.size<=24 * 1024 * 1024:
                continue
            result["candidate_bytes"]+=member.size
            if result["candidate_bytes"]>MAX_BYTES:
                raise ValueError("Guest source scan budget exceeded")
            stream=archive.extractfile(member)
            if stream is None:raise ValueError("Archive candidate unreadable")
            with stream: data=stream.read()
            result["candidate_cpp_files"]+=1
            by_type={}
            for name,rx in PATS.items():
                hits=list(rx.finditer(data))
                if hits:
                    matches=[]
                    for m in hits[:12]:
                        before=data[max(0,m.start()-4000):m.start()]
                        names=FUNCTION_RE.findall(before)
                        matches.append({
                            "offset":m.start(),
                            "nearby_sub_candidates":[x.decode() for x in list(dict.fromkeys(names))[-4:]]
                        })
                    by_type[name]={"count":len(hits),"samples":matches}
            if by_type:
                result["match_files"].append({
                    "member":member.name,"bytes":member.size,"patterns":by_type})
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",required=True,type=Path)
    args=p.parse_args()
    drive=drive_client()
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre737-") as td:
        archive=Path(td)/"pre99.tar.gz"
        meta=drive.files().get(fileId=BACKUP_ID,fields="id,size").execute()
        if meta.get("id")!=BACKUP_ID or int(meta.get("size",0))!=EXPECTED_BYTES:
            raise ValueError("PRE99 archive identity mismatch")
        download(drive,archive)
        digest,_md5,size=sha_file(archive)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("PRE99 archive SHA/size mismatches approved snapshot")
        report=inspect(archive)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE737_SCANNED_GUEST_FILES="+str(report["candidate_cpp_files"]))
    for pattern in PATS:
        found=sum(i["patterns"].get(pattern,{}).get("count",0) for i in report["match_files"])
        print("PRE737_"+pattern.upper()+"="+str(found))
    name="NFSMW_PRE737_GUEST_CATCHUP_SOURCE_READONLY.json"
    up=drive.files().create(
        body={"name":name,"parents":[DEST_FOLDER],"mimeType":"application/json"},
        media_body=MediaFileUpload(str(args.report),mimetype="application/json"),
        fields="id,name,parents").execute()
    if up.get("name")!=name or DEST_FOLDER not in up.get("parents",[]):
        raise ValueError("Drive report upload verification failed")
    print("PRE737_REPORT_DRIVE_ID="+up["id"])
    print("PRE737_NO_GAMEPLAY_PATCH_NO_APK_NO_SIGNING")

if __name__=="__main__":
    main()
