#!/usr/bin/env python3
"""PRE726 fail-closed append to canonical Drive context; preserve backup and signing."""
import argparse
import hashlib
import io
import os
from pathlib import Path

CONTEXT_ID="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP_ID="1y719NlqKER1GcB9HYu7fPa62kdq9X1tS"
EXPECTED_BYTES=1358792
EXPECTED_SHA="6d5ef5679cfa1b314ea4eb4ae6a40fa59d34b99859d326e959136219f01786a3"
DOC=Path("docs/PRE726_V51_KAGGLE_VULKAN_REQUESTED_MAP_ALIAS_DRIVER_ORIGIN_REAL_20261112.md")
RUN_ID="43307644388"
ZIP_SHA="6b6cef8af0385b2ab8efe1501a0064ad5562ae1923db9bec457b15a3b47f6bf7"

def sha(b):return hashlib.sha256(b).hexdigest()

def compose(before:bytes,doc:str)->bytes:
    if len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA:
        raise ValueError("PRE726_CANONICAL_CONTEXT_SHA_DRIFT")
    s=before.decode("utf-8")
    if not s.endswith("\n") or "PRE725_REAL_KAGGLE_PASS" not in s[-2500:]:
        raise ValueError("PRE726_EXPECTED_PRE725_TAIL_MISSING")
    if "# PRE726 " in s or "PRE726_REAL_KAGGLE_PASS" in s:
        raise ValueError("PRE726_ALREADY_SYNCED")
    if s.count("# PRE725 ")!=1 or s.count("# PRE724 ")!=1 or s.count("# PRE723 ")!=1 or s.count("# PRE722 ")!=1 or s.count("# PRE721 ")!=1 or s.count("# PRE720 ")!=1 or s.count("# PRE719 ")!=1 or s.count("# PRE718 ")!=1 or s.count("# PRE717 ")!=1:
        raise ValueError("PRE726_PREVIOUS_CHECKPOINT_COUNTS_WRONG")
    if not doc.startswith("# PRE726 ") or RUN_ID not in doc or ZIP_SHA not in doc:
        raise ValueError("PRE726_CHECKPOINT_CONTENT_DRIFT")
    if len(doc)>16000 or "-----BEGIN PRIVATE KEY" in doc or "NFSMW_ASSINATURA_CREDENCIAIS.properties" in doc:
        raise ValueError("PRE726_CHECKPOINT_SAFETY_GATE")
    suffix=(
      "\n\n---\n\n"
      "## ATUALIZAÇÃO VERIFICADA — PRE726 (2026-11-12)\n\n"
      "PRE726 tem run Kaggle remoto autenticado e ZIP conferido no Drive. "
      "Este bloco é mais recente que PRE725, sem modificar V51 ou assinatura permanente. "
      "O próximo gate sugerido é PRE727: verificar com logs existentes nomes Vulkan efetivamente habilitados "
      "e distinguir valores solicitados, anunciados e habilitados, sem divulgar código privado, "
      "sem alegar erro Vulkan ou ganho de FPS.\n\n"
    )
    after=(s.rstrip("\n")+suffix+doc.rstrip()+"\n\n---\n").encode("utf-8")
    if len(after)<=len(before)+500 or after==before:
        raise ValueError("PRE726_NOT_APPEND")
    if after.decode("utf-8").count("# PRE726 ")!=1:
        raise ValueError("PRE726_DUPLICATE_CHECKPOINT")
    return after

def drive():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    for k in ("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET"):
        if not os.environ.get(k):raise ValueError("PRE726_MISSING_GOOGLE_ENV")
    c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    c.refresh(Request())
    return build("drive","v3",credentials=c,cache_discovery=False)

def read_bytes(api,file_id):
    b=api.files().get_media(fileId=file_id,supportsAllDrives=True).execute(num_retries=4)
    if not isinstance(b,bytes):raise ValueError("PRE726_DRIVE_NOT_BYTES")
    return b

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    doc=DOC.read_text(encoding="utf-8")
    if a.self_test:
        assert len(EXPECTED_SHA)==64 and len(ZIP_SHA)==64 and EXPECTED_BYTES>1000000
        assert RUN_ID in doc and ZIP_SHA in doc and doc.startswith("# PRE726 ")
        assert CONTEXT_ID!=BACKUP_ID and "PRE726" in doc
        print("PRE726_CONTEXT_LOCAL_CHECKPOINT_PASS=TRUE")
        return
    if not a.apply:p.error("--apply required")
    api=drive()
    before=read_bytes(api,CONTEXT_ID)
    backup=read_bytes(api,BACKUP_ID)
    if before!=backup or len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA:
        raise ValueError("PRE726_CONTEXT_OR_BACKUP_DRIFT_NO_WRITE")
    after=compose(before,doc)
    from googleapiclient.http import MediaIoBaseUpload
    media=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False)
    written=api.files().update(fileId=CONTEXT_ID,media_body=media,
        fields="id,size,modifiedTime",supportsAllDrives=True).execute(num_retries=4)
    if written.get("id")!=CONTEXT_ID or int(written.get("size",-1))!=len(after):
        raise ValueError("PRE726_WRITE_METADATA_MISMATCH")
    rb=read_bytes(api,CONTEXT_ID)
    if rb!=after or sha(rb)!=sha(after):
        raise ValueError("PRE726_CONTEXT_READBACK_MISMATCH")
    if sha(read_bytes(api,BACKUP_ID))!=EXPECTED_SHA:
        raise ValueError("PRE726_BACKUP_MODIFIED")
    print("PRE726_CANONICAL_CONTEXT_UPDATED_AND_READBACK_VERIFIED=TRUE")
    print("PRE726_CONTEXT_ID="+CONTEXT_ID)
    print("PRE726_BACKUP_ID="+BACKUP_ID)
    print("PRE726_CONTEXT_NEW_SIZE="+str(len(rb)))
    print("PRE726_CONTEXT_NEW_SHA256="+sha(rb))
    print("PRE726_APK_OR_SIGNING_MATERIAL_MODIFIED=FALSE")

if __name__=="__main__":main()
