#!/usr/bin/env python3
"""PRE740: look for authenticated guest function anchors in private generated C++.

Only SHA-pinned PRE99; text only, read-only. No static PPC instruction changes.
Reports are private. Address hits are clues, not validated function signatures.
"""
import argparse
import json
import re
import tarfile
import tempfile
from collections import Counter
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from pre104_verify_backup_tar import BACKUP_ID, EXPECTED_BYTES, EXPECTED_SHA256, sha_file
from pre105_read_settings_source import drive_client, download

FOLDER="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
ANCHORS={
  "attrib_lookup":0x821485E8,
  "attrib_value":0x82145C50,
  "race_status_global":0x82A2CB18,
  "race_type_getter":0x820E5E28,
  "gameflow_state":0x82A39AD8,
  "race_param_type_getter":0x8233A000,
}
FUNC=re.compile(rb"(?i)\b(?:sub|func|function)_82[0-9a-f]{6,8}\b")
MAX_READ=400*1024*1024
MAX_MATCH=24


def anchor_patterns(address):
    tokens=[
      rb"\b0x0*"+format(address,"x").encode()+rb"\b",
      rb"\b"+format(address,"x").encode()+rb"\b",
      rb"\b"+str(address).encode()+rb"\b",
      rb"\bsub_"+format(address,"x").encode()+rb"\b",
    ]
    return re.compile(b"(?:"+b"|".join(tokens)+b")",re.IGNORECASE)


def scan(archive_file):
    info={"stage":"PRE740_PRIVATE_GUEST_STATIC_ANCHOR_SCAN",
          "archive_verified_sha256":True,
          "files_scanned":0,"bytes_scanned":0,
          "anchor_hits":{}, "generated_symbols":Counter(),
          "source_changed":False,"gameplay_patch_applied":False,
          "apk_built":False,"signing_accessed":False}
    patterns={k:anchor_patterns(v) for k,v in ANCHORS.items()}
    with tarfile.open(archive_file,"r:gz",errorlevel=2) as tf:
        for member in tf:
            low=member.name.lower()
            if not member.isfile() or not low.endswith((".cpp",".cc",".h",".hpp")) or not (
                "/generated/" in low or "/generated-android/" in low or "/ppc/" in low
                or "/game_recompiled/" in low):
                continue
            if member.size<0 or member.size>24*1024*1024:continue
            info["bytes_scanned"]+=member.size
            if info["bytes_scanned"]>MAX_READ:raise ValueError("Generated text budget exceeded")
            f=tf.extractfile(member)
            if f is None:raise ValueError("Unreadable source")
            with f: data=f.read()
            info["files_scanned"]+=1
            info["generated_symbols"]["sub_82_tokens"]+=len(FUNC.findall(data))
            for name,pat in patterns.items():
                found=list(pat.finditer(data))
                if not found:continue
                summary=info["anchor_hits"].setdefault(name,{"count":0,"sample_locations":[]})
                summary["count"]+=len(found)
                for hit in found:
                    if len(summary["sample_locations"])>=MAX_MATCH:break
                    # Addresses and nearby symbol identities only; never copy code lines.
                    prior=data[max(0,hit.start()-10000):hit.start()]
                    functions=FUNC.findall(prior)
                    nearby=list(dict.fromkeys(v.decode("ascii").lower() for v in functions[-8:]))
                    summary["sample_locations"].append({
                        "source_member":member.name,
                        "offset_in_file":hit.start(),
                        "candidate_enclosing_functions":nearby[-4:],
                    })
    info["generated_symbols"]=dict(info["generated_symbols"])
    return info


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,required=True)
    opts=p.parse_args()
    drive=drive_client()
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre740-") as directory:
        tar=Path(directory)/"pre99.tar.gz"
        metadata=drive.files().get(fileId=BACKUP_ID,fields="id,size").execute()
        if metadata.get("id")!=BACKUP_ID or int(metadata.get("size",0))!=EXPECTED_BYTES:
            raise ValueError("PRE99 metadata mismatch")
        download(drive,tar)
        sha,_md5,size=sha_file(tar)
        if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("PRE99 integrity mismatch")
        report=scan(tar)
    opts.report.parent.mkdir(parents=True,exist_ok=True)
    opts.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE740_FILES="+str(report["files_scanned"]))
    print("PRE740_ANCHORS="+json.dumps({k:v["count"] for k,v in report["anchor_hits"].items()},sort_keys=True))
    name="NFSMW_PRE740_GUEST_RUNTIME_ANCHORS_READONLY.json"
    uploaded=drive.files().create(body={"name":name,"mimeType":"application/json",
               "parents":[FOLDER]},media_body=MediaFileUpload(str(opts.report),mimetype="application/json"),
               fields="id,name,parents").execute()
    if uploaded.get("name")!=name or FOLDER not in uploaded.get("parents",[]):
        raise ValueError("Drive report readback mismatch")
    print("PRE740_REPORT_DRIVE_ID="+uploaded["id"])
    print("PRE740_NO_PATCH_NO_APK_NO_SIGNING")
if __name__=="__main__":
    main()
