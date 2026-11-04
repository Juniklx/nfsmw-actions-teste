#!/usr/bin/env python3
"""PRE151 canonical Google Drive context sync with integrity checks and backup."""
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CONTEXT_ID = "1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
CONTEXT_PARENT = "1Waam42x_suvBS18b4360HOaBqKxAncvy"
BACKUP_FOLDER = "1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
APPENDIX_PATH = Path("automation/kaggle/ADENDO_CONTEXTO_PRE151_20261104.md")
REPORT_PATH = Path("reports/RELATORIO_NFSMW_PRE151_V31_PRE150_CORRELACAO_TERMICA_20261104.md")
REPORT_SHA256 = "45f3d2d0771205c99408bc5a5cd642abf4fce9f3796f313a90dd51a824d68594"
MARKER = "## ATUALIZAÇÃO — 2026-11-04: PRE151 — coleta PRE150 V31 executada e correlação Vulkan/térmica"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def get_drive():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    c = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    )
    c.refresh(Request())
    return build("drive", "v3", credentials=c, cache_discovery=False)

def run():
    status = {"stage":"PRE151","state":"UNCONFIRMED","phase":"START",
              "original_content_preserved":False,"created_backup":False,
              "build_executed":False,"signing_key_accessed":False,
              "credentials_logged":False}
    output = Path(os.environ.get("PRE151_STATUS_PATH", "/tmp/pre151-context-status.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        status["phase"]="CHECK_INPUTS"
        appendix = APPENDIX_PATH.read_bytes()
        report=REPORT_PATH.read_bytes()
        if digest(report)!=REPORT_SHA256 or MARKER.encode() not in appendix:
            raise ValueError("input mismatch")
        if not (1500 < len(appendix) < 8000) or b"versionCode" not in appendix:
            raise ValueError("appendix structure")
        run_id = os.environ.get("GITHUB_RUN_ID","")
        if not re.fullmatch(r"[0-9]+",run_id):
            raise ValueError("run id invalid")
        status["report_sha256"] = digest(report)
        status["phase"]="READ_CANONICAL"
        drive = get_drive()
        meta = drive.files().get(fileId=CONTEXT_ID,fields="id,name,size,mimeType,md5Checksum,parents",supportsAllDrives=True).execute()
        if (meta.get("id")!=CONTEXT_ID or meta.get("name")!="CONTEXTO_NFSMW.md"
            or CONTEXT_PARENT not in meta.get("parents",[])
            or meta.get("mimeType") not in ["text/plain","text/markdown"]
            or int(meta.get("size",0))<340000):
            raise ValueError("unexpected canonical metadata")
        original=drive.files().get_media(fileId=CONTEXT_ID,supportsAllDrives=True).execute()
        if isinstance(original,str): original=original.encode("utf-8")
        if (int(meta["size"])!=len(original) or
            hashlib.md5(original).hexdigest()!=meta.get("md5Checksum","").lower() or
            not original.startswith(b"# CONTEXTO DO PROJETO")):
            raise ValueError("canonical integrity mismatch")
        status["old_sha256"]=digest(original)
        status["old_bytes"]=len(original)
        if MARKER.encode("utf-8") in original:
            status["state"]="ALREADY_PRESENT_VERIFIED"
            status["original_content_preserved"]=True
            status["phase"]="DONE"
            return status
        if "PRE150" not in original.decode("utf-8"):
            raise ValueError("missing PRE150 section")
        status["phase"]="VERIFY_EXISTING_BACKUP"
        backup_id="19Lvuf7p9i2Du9nS8ioDh0F3OfpF-FLYz"
        backup_name="CONTEXTO_NFSMW_BACKUP_ANTES_PRE151_20261104.md"
        backup=drive.files().get(fileId=backup_id,fields="id,name,size,md5Checksum,parents",supportsAllDrives=True).execute()
        if (backup.get("name")!=backup_name or BACKUP_FOLDER not in backup.get("parents",[])
            or int(backup.get("size",-1))!=len(original)
            or backup.get("md5Checksum","").lower()!=hashlib.md5(original).hexdigest()):
            raise ValueError("existing Drive backup not identical")
        status["created_backup"]=False
        status["verified_existing_backup"]=True
        status["backup_drive_id"]=backup_id
        status["phase"]="RECHECK_CANONICAL"
        latest=drive.files().get(fileId=CONTEXT_ID,fields="id,size,md5Checksum",supportsAllDrives=True).execute()
        if (int(latest.get("size",-1))!=len(original)
            or latest.get("md5Checksum","").lower()!=hashlib.md5(original).hexdigest()):
            raise RuntimeError("canonical changed before append")
        status["phase"]="APPEND"
        updated=original+(b"" if original.endswith(b"\n") else b"\n")+b"\n"+appendix
        from googleapiclient.http import MediaIoBaseUpload
        drive.files().update(fileId=CONTEXT_ID,media_body=MediaIoBaseUpload(io.BytesIO(updated),mimetype=meta["mimeType"],resumable=False),supportsAllDrives=True,fields="id,size,md5Checksum").execute()
        status["phase"]="VERIFY_READBACK"
        readback=drive.files().get_media(fileId=CONTEXT_ID,supportsAllDrives=True).execute()
        if isinstance(readback,str):readback=readback.encode("utf-8")
        if readback!=updated or not readback.startswith(original):
            raise RuntimeError("canonical readback differs")
        status["state"]="CANONICAL_UPDATED_VERIFIED"
        status["original_content_preserved"]=True
        status["new_bytes"]=len(readback)
        status["new_sha256"]=digest(readback)
        status["phase"]="DONE"
    except Exception as exc:
        status["state"]="FAILED_NOT_CONFIRMED"
        status["error_type"]=type(exc).__name__
        resp=getattr(exc,"resp",None)
        if resp is not None:status["google_http_status"]=getattr(resp,"status",None)
        # Sanitized failure reporting: never print exception text, credentials or Drive URLs.
        print("PRE151 sync failure phase="+str(status["phase"])+" type="+type(exc).__name__)
    finally:
        status["utc"]=datetime.now(timezone.utc).isoformat()
        output.write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE151 sync final state="+str(status["state"]))
    return status

if __name__=="__main__":
    value=run()
    sys.exit(0 if value["state"] in ("CANONICAL_UPDATED_VERIFIED","ALREADY_PRESENT_VERIFIED") else 1)
