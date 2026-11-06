#!/usr/bin/env python3
"""PRE199: generate isolated private Kaggle source-symbol audit.
Read only PRE99; do not restore, patch, build, touch saves, or access signing.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

KERNEL = "juniklx/nfsmw-pre199-cheats-readonly"
NOTEBOOK = "nfsmw_pre199_cheats_readonly.ipynb"

CELL = r'''
from __future__ import annotations
import hashlib, json, re, tarfile, tempfile
from pathlib import Path
from datetime import datetime, timezone

RUN_ID = "__RUN_ID__"
BACKUP_ID = "1qXEY5JXUdvZB4CuqPvXARz8TY-FArdzb"
EXPECTED_BYTES = 874780689
EXPECTED_SHA256 = "af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39"
LOG_FOLDER_ID = "1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
PINS = {
    "workspace/nativo/app/src/nfsmw_nativo_dibujos.cpp": "046ea454634d84169ccda0237c347d17020a63da027878d4fd21f7a3520251e2",
    "workspace/nativo/app_usa/src/nfsmw_nativo_dibujos.cpp": "92e0a15836217a535c6f81e2461381616f46c331c83201cabd14a71c2d8c2342",
    "workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp": "5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034"
}
REGEX = {
    "nitro": re.compile(r"\b(?:nitro|nitrous|nitrous_oxide|nitrousoxide|n2o|nos)\b", re.I),
    "speedbreaker": re.compile(r"\b(?:speed[\s_-]?breaker|speed[\s_-]?break|slow[\s_-]?mo(?:tion)?|bullet[\s_-]?time|time[\s_-]?dilation)\b", re.I),
    "dinheiro": re.compile(r"\b(?:cash|money|bankroll|career_cash|bank_balance|wallet|dinheiro)\b", re.I),
}
EXTENSIONS = {".cpp",".c",".cc",".cxx",".h",".hpp",".inl",".ipp",".java",".kt",".json",".cmake",".gradle",".kts"}
SPECIAL_NAMES = {"CMakeLists.txt"}
MAX_FILE_BYTES = 6000000
MAX_MATCHES_PER_FILE = 10
MAX_FILE_RECORDS_PER_GROUP = 160
report = {
    "stage": "PRE199_CHEATS_KAGGLE_READONLY",
    "github_run_id": RUN_ID,
    "status": "NAO_VALIDADO",
    "mode": "READ_ONLY",
    "backup_sha256_valid": False,
    "source_hashes_valid": False,
    "no_build": True,
    "no_source_patch": True,
    "no_signing_credentials_accessed": True,
    "v36_unchanged": True,
    "no_save_changes": True,
    "matches_only_indicators_not_offsets": True,
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
}
phase = "START"
try:
    from kaggle_secrets import UserSecretsClient
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
    phase = "KAGGLE_SECRETS"
    s = UserSecretsClient()
    values = {}
    for name in ("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET"):
        values[name] = s.get_secret(name)
        if not values[name]:
            raise ValueError("Google auth secret not configured")
    phase = "GOOGLE_AUTH"
    credentials = Credentials(token=None,
        refresh_token=values["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=values["GOOGLE_CLIENT_ID"],
        client_secret=values["GOOGLE_CLIENT_SECRET"])
    credentials.refresh(Request())
    drive = build("drive","v3",credentials=credentials,cache_discovery=False)
    del values
    phase = "DOWNLOAD_PRE99"
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre199_") as folder:
        archive = Path(folder) / "PRE99.tar.gz"
        with archive.open("wb") as f:
            dl = MediaIoBaseDownload(f, drive.files().get_media(fileId=BACKUP_ID,supportsAllDrives=True), chunksize=8*1024*1024)
            done = False
            while not done:
                _, done = dl.next_chunk(num_retries=4)
        phase = "VERIFY_PRE99"
        h = hashlib.sha256()
        size = 0
        with archive.open("rb") as f:
            for block in iter(lambda:f.read(8*1024*1024),b""):
                h.update(block)
                size += len(block)
        if size != EXPECTED_BYTES or h.hexdigest() != EXPECTED_SHA256:
            raise ValueError("Authenticated PRE99 digest mismatch")
        report["backup_sha256_valid"] = True
        report["backup_sha256"] = EXPECTED_SHA256
        phase = "AUDIT_SOURCE"
        scanned=0
        skipped_large=0
        hits={name:[] for name in REGEX}
        hits_total={name:0 for name in REGEX}
        pins_found={}
        ui_candidates=[]
        with tarfile.open(archive,"r:gz",errorlevel=2) as tf:
            for member in tf:
                name=member.name.lstrip("./")
                if not member.isfile():
                    continue
                if not (name.startswith("workspace/nativo/") or name.startswith("workspace/android/")):
                    continue
                if name in PINS and member.size>MAX_FILE_BYTES:
                    raise ValueError("Pinned source unexpectedly large")
                p=Path(name)
                if p.suffix.lower() not in EXTENSIONS and p.name not in SPECIAL_NAMES:
                    continue
                lower=name.lower()
                if any(s in lower for s in ("/.git/","/build/","/outputs/","/node_modules/",
                      "/.gradle/","/signing/","keystore","password","secret","credential")):
                    continue
                if member.size>MAX_FILE_BYTES:
                    skipped_large+=1
                    continue
                f=tf.extractfile(member)
                if f is None:continue
                data=f.read()
                if len(data)!=member.size:raise RuntimeError("Short archive member read")
                digest=hashlib.sha256(data).hexdigest()
                scanned+=1
                if name in PINS:
                    pins_found[name]=digest
                if "settings_overlay" in p.name or "rex_app" in p.name or p.name=="CMakeLists.txt":
                    if len(ui_candidates)<45:
                        ui_candidates.append({"path":name,"sha256":digest})
                lines=data.decode("utf-8","replace").splitlines()
                for category,rx in REGEX.items():
                    numbers=[i for i,line in enumerate(lines,1) if rx.search(line)]
                    if not numbers:continue
                    hits_total[category]+=len(numbers)
                    if len(hits[category])<MAX_FILE_RECORDS_PER_GROUP:
                        hits[category].append({"path":name,"sha256":digest,
                            "line_numbers":numbers[:MAX_MATCHES_PER_FILE],
                            "matches_in_file":len(numbers)})
        report["source_files_scanned"]=scanned
        report["skipped_oversize_sources"]=skipped_large
        report["source_hashes_valid"]=set(pins_found)==set(PINS) and all(pins_found[k]==v for k,v in PINS.items())
        report["pinned_sources"]=pins_found
        report["occurrences_by_category"]=hits_total
        report["source_candidates_by_category"]=hits
        report["ui_integration_candidates"]=ui_candidates
        report["report_is_truncated"]=any(len(v)>=MAX_FILE_RECORDS_PER_GROUP for v in hits.values())
        if not report["source_hashes_valid"]:
            raise ValueError("Pinned source digest mismatch or missing")
        report["status"]="AUDIT_OK"
        phase="REPORT_WRITE"
        output=Path("/kaggle/working/NFSMW_PRE199_CHEATS_READONLY.json")
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        # Optional new report upload: never update/overwrite an existing file.
        phase="OPTIONAL_REPORT_UPLOAD"
        try:
            media=MediaFileUpload(str(output),mimetype="application/json",resumable=False)
            created=drive.files().create(body={"name":"NFSMW_PRE199_CHEATS_READONLY_"+RUN_ID+".json","parents":[LOG_FOLDER_ID]},
                media_body=media,fields="id,name,size",supportsAllDrives=True).execute()
            report["new_drive_report_id"]=created.get("id")
            report["drive_report_uploaded"]=True
        except Exception as upload_error:
            report["drive_report_uploaded"]=False
            report["drive_report_upload_error_type"]=type(upload_error).__name__
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
except Exception as exc:
    report["status"]="FAILED"
    report["failure_phase"]=phase
    report["failure_type"]=type(exc).__name__
finally:
    output=Path("/kaggle/working/NFSMW_PRE199_CHEATS_READONLY.json")
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE199_STATUS",report["status"])
    print("PRE199_SOURCE_SCANNED",report.get("source_files_scanned",0))
    print("PRE199_SHA_VERIFIED",report["backup_sha256_valid"], report["source_hashes_valid"])
    print("PRE199_OUTPUT",output.name)
'''

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",required=True)
    parser.add_argument("--output",required=True)
    args=parser.parse_args()
    if not re.fullmatch(r"[0-9]+",args.run_id):
        raise ValueError("Numeric GitHub run id required")
    out=Path(args.output)
    out.mkdir(parents=True,exist_ok=True)
    code=CELL.replace("__RUN_ID__",args.run_id)
    compile(code,"<PRE199 Kaggle cell>","exec")
    nb={
        "nbformat":4,"nbformat_minor":5,
        "metadata":{"kernelspec":{"name":"python3","display_name":"Python 3","language":"python"},"language_info":{"name":"python"}},
        "cells":[
            {"cell_type":"markdown","id":"pre199-intro","metadata":{},"source":["NFSMW PRE199 isolated read-only cheats source audit. No build or signing."]},
            {"cell_type":"code","id":"pre199-audit","metadata":{},"execution_count":None,"outputs":[],"source":code.splitlines(keepends=True)}
        ]
    }
    meta={
        "id":KERNEL,"title":"NFSMW PRE199 Cheats Readonly","code_file":NOTEBOOK,
        "language":"python","kernel_type":"notebook","is_private":True,
        "enable_gpu":False,"enable_internet":True,
        "dataset_sources":[],"competition_sources":[],"kernel_sources":[],"model_sources":[]
    }
    (out/NOTEBOOK).write_text(json.dumps(nb,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"kernel-metadata.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE199 private Kaggle kernel prepared:",KERNEL)

if __name__=="__main__":
    main()
