#!/usr/bin/env python3
"""PRE741: inspect Xbox 360 USA guest PPC function shapes around validated anchors.

READ ONLY. Loads SHA-pinned PRE99 in ephemeral runner. Outputs small code excerpts
to a private Drive JSON for analyst review. Does not modify or publish game assets.
"""
import argparse
import json
import re
import tarfile
import tempfile
from pathlib import Path
from collections import Counter
from googleapiclient.http import MediaFileUpload
from pre104_verify_backup_tar import BACKUP_ID, EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

FOLDER="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
ANCHORS={
    "race_type_getter":"sub_820E5E28",
    "race_parameters_getter":"sub_8233A000",
    "attrib_find":"sub_821485E8",
    "attrib_get_value":"sub_82145C50",
}
# Guest C++ generated from USA PPC. These offsets are hypotheses based on the
# reconstructed PC struct and may NOT agree with X360 ABI.
OFFSET_WORDS=("0x45E4","0x45E8","0x45F4","0x4624","0x1A30",
              "0x1A2C","0x1AA8","0x10DB","0x4E6")
SOURCE_MEMBER=re.compile(r"^workspace/nativo/app/generated/default/nfsmw_recomp\.[0-9]+\.cpp$")
FUNC_HEADER=re.compile(rb"(?im)^.{0,160}\b(?:sub_82[0-9a-f]{6})\b.{0,200}[\r\n]")
FUNC_NAME=re.compile(rb"\bsub_82[0-9a-fA-F]{6}\b")
MAX_TEXT=400*1024*1024

def audit(path):
    report={"stage":"PRE741_PRIVATE_GUEST_PPC_CONTEXT_READONLY",
            "backup_sha256_verified":True,"cpp_sources_read":0,"bytes_scanned":0,
            "anchors":{k:{"pattern":v,"count":0,"sites":[]} for k,v in ANCHORS.items()},
            "offset_patterns":{o:{"count":0,"samples":[]} for o in OFFSET_WORDS},
            "no_gameplay_patch":True,"apk_built":False,"signing_accessed":False}
    regex={name:re.compile(rb"\b"+sym.encode()+rb"\b",re.I) for name,sym in ANCHORS.items()}
    off_rx={s:re.compile(rb"(?i)\b"+s.encode()+rb"\b") for s in OFFSET_WORDS}
    with tarfile.open(path,"r:gz",errorlevel=2) as tf:
        for member in tf:
            if not member.isfile() or not SOURCE_MEMBER.match(member.name):
                continue
            if not 0<member.size<=24*1024*1024:
                raise ValueError("PRE741 source exceeds per member budget")
            report["bytes_scanned"]+=member.size
            if report["bytes_scanned"]>MAX_TEXT:
                raise ValueError("PRE741 source exceeds aggregate budget")
            src=tf.extractfile(member)
            if src is None:raise ValueError("No source body")
            with src: data=src.read()
            report["cpp_sources_read"]+=1
            for name,rx in regex.items():
                locations=list(rx.finditer(data))
                report["anchors"][name]["count"]+=len(locations)
                for match in locations:
                    if len(report["anchors"][name]["sites"])>=5:break
                    start=max(0,match.start()-1000)
                    end=min(len(data),match.end()+1500)
                    report["anchors"][name]["sites"].append({
                        "file":member.name,"offset":match.start(),
                        "context":data[start:end].decode("utf-8","replace")})
            for name,rx in off_rx.items():
                locations=list(rx.finditer(data))
                report["offset_patterns"][name]["count"]+=len(locations)
                for match in locations:
                    if len(report["offset_patterns"][name]["samples"])>=12:break
                    prior=data[max(0,match.start()-500):match.start()]
                    prior_names=FUNC_NAME.findall(prior)
                    report["offset_patterns"][name]["samples"].append({
                        "file":member.name,"offset":match.start(),
                        "symbols_before":[s.decode() for s in prior_names[-3:]],
                        "context":data[max(0,match.start()-80):match.end()+140].decode("utf-8","replace")})
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",required=True,type=Path)
    o=p.parse_args()
    drive=drive_client()
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre741-") as directory:
        path=Path(directory)/"PRE99.tar.gz"
        meta=drive.files().get(fileId=BACKUP_ID,fields="id,size").execute()
        if meta.get("id")!=BACKUP_ID or int(meta.get("size",0))!=EXPECTED_BYTES:
            raise ValueError("Private source archive metadata differs")
        download(drive,path)
        sha,_md5,size=sha_file(path)
        if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("Private PRE99 snapshot identity differs")
        report=audit(path)
    o.report.parent.mkdir(parents=True,exist_ok=True)
    o.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE741_CPP_FILES="+str(report["cpp_sources_read"]))
    print("PRE741_ANCHORS="+json.dumps({k:v["count"] for k,v in report["anchors"].items()},sort_keys=True))
    print("PRE741_OFFSETS="+json.dumps({k:v["count"] for k,v in report["offset_patterns"].items()},sort_keys=True))
    name="NFSMW_PRE741_PPC_GUEST_CONTEXT_PRIVATE.json"
    up=drive.files().create(body={"name":name,"mimeType":"application/json",
                         "parents":[FOLDER]},
             media_body=MediaFileUpload(str(o.report),mimetype="application/json"),
             fields="id,name,parents").execute()
    if up.get("name")!=name or FOLDER not in up.get("parents",[]):
        raise ValueError("Private Drive report identity mismatch")
    print("PRE741_REPORT_DRIVE_ID="+up["id"])
    print("PRE741_NO_MODIFICATIONS_NO_APK_NO_SIGNING")
if __name__=="__main__":
    main()
