#!/usr/bin/env python3
"""PRE723 fail-closed append to canonical Drive context; preserve backup and signing."""
import argparse
import hashlib
import io
import os
from pathlib import Path

CONTEXT_ID="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP_ID="1pW6c1pyY2zydZ5YOSmb10iMFTq5q2Ux-"
EXPECTED_BYTES=1339850
EXPECTED_SHA="0ce7878cc32d6b2cffc48627b54ea2f5d5cc0652dc730b073d66169a6c4b453e"
DOC=Path("docs/PRE723_V51_KAGGLE_VULKAN_SIZE_RECEIVER_IDENTITY_REAL_20261112.md")
RUN_ID="43299482411"
ZIP_SHA="439562f6a4983b5de0d032895780c70c27e1ccd1cb0d0f3a984a450c89e1fcf8"

def sha(b):return hashlib.sha256(b).hexdigest()

def compose(before:bytes,doc:str)->bytes:
    if len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA:
        raise ValueError("PRE723_CANONICAL_CONTEXT_SHA_DRIFT")
    s=before.decode("utf-8")
    if not s.endswith("\n") or "PRE722_REAL_KAGGLE_PASS" not in s[-2500:]:
        raise ValueError("PRE723_EXPECTED_PRE722_TAIL_MISSING")
    if "# PRE723 " in s or "PRE723_REAL_KAGGLE_PASS" in s:
        raise ValueError("PRE723_ALREADY_SYNCED")
    if s.count("# PRE722 ")!=1 or s.count("# PRE721 ")!=1 or s.count("# PRE720 ")!=1 or s.count("# PRE719 ")!=1 or s.count("# PRE718 ")!=1 or s.count("# PRE717 ")!=1:
        raise ValueError("PRE723_PREVIOUS_CHECKPOINT_COUNTS_WRONG")
    if not doc.startswith("# PRE723 ") or RUN_ID not in doc or ZIP_SHA not in doc:
        raise ValueError("PRE723_CHECKPOINT_CONTENT_DRIFT")
    if len(doc)>16000 or "-----BEGIN PRIVATE KEY" in doc or "NFSMW_ASSINATURA_CREDENCIAIS.properties" in doc:
        raise ValueError("PRE723_CHECKPOINT_SAFETY_GATE")
    suffix=(
      "\n\n---\n\n"
      "## ATUALIZAÇÃO VERIFICADA — PRE723 (2026-11-12)\n\n"
      "PRE723 tem run Kaggle remoto autenticado e ZIP conferido no Drive. "
      "Este bloco é mais recente que PRE722, sem modificar V51 ou assinatura permanente. "
      "O próximo gate sugerido é PRE724: avaliar a condição do emplace_back na linha 455 "
      "e o possível retry por prefixo nas linhas 523–537, sem divulgar código privado, "
      "sem alegar erro Vulkan ou ganho de FPS.\n\n"
    )
    after=(s.rstrip("\n")+suffix+doc.rstrip()+"\n\n---\n").encode("utf-8")
    if len(after)<=len(before)+500 or after==before:
        raise ValueError("PRE723_NOT_APPEND")
    if after.decode("utf-8").count("# PRE723 ")!=1:
        raise ValueError("PRE723_DUPLICATE_CHECKPOINT")
    return after

def drive():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    for k in ("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET"):
        if not os.environ.get(k):raise ValueError("PRE723_MISSING_GOOGLE_ENV")
    c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    c.refresh(Request())
    return build("drive","v3",credentials=c,cache_discovery=False)

def read_bytes(api,file_id):
    b=api.files().get_media(fileId=file_id,supportsAllDrives=True).execute(num_retries=4)
    if not isinstance(b,bytes):raise ValueError("PRE723_DRIVE_NOT_BYTES")
    return b

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    doc=DOC.read_text(encoding="utf-8")
    if a.self_test:
        assert len(EXPECTED_SHA)==64 and len(ZIP_SHA)==64 and EXPECTED_BYTES>1000000
        assert RUN_ID in doc and ZIP_SHA in doc and doc.startswith("# PRE723 ")
        assert CONTEXT_ID!=BACKUP_ID and "PRE723" in doc
        print("PRE723_CONTEXT_LOCAL_CHECKPOINT_PASS=TRUE")
        return
    if not a.apply:p.error("--apply required")
    api=drive()
    before=read_bytes(api,CONTEXT_ID)
    backup=read_bytes(api,BACKUP_ID)
    if before!=backup or len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA:
        raise ValueError("PRE723_CONTEXT_OR_BACKUP_DRIFT_NO_WRITE")
    after=compose(before,doc)
    from googleapiclient.http import MediaIoBaseUpload
    media=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False)
    written=api.files().update(fileId=CONTEXT_ID,media_body=media,
        fields="id,size,modifiedTime",supportsAllDrives=True).execute(num_retries=4)
    if written.get("id")!=CONTEXT_ID or int(written.get("size",-1))!=len(after):
        raise ValueError("PRE723_WRITE_METADATA_MISMATCH")
    rb=read_bytes(api,CONTEXT_ID)
    if rb!=after or sha(rb)!=sha(after):
        raise ValueError("PRE723_CONTEXT_READBACK_MISMATCH")
    if sha(read_bytes(api,BACKUP_ID))!=EXPECTED_SHA:
        raise ValueError("PRE723_BACKUP_MODIFIED")
    print("PRE723_CANONICAL_CONTEXT_UPDATED_AND_READBACK_VERIFIED=TRUE")
    print("PRE723_CONTEXT_ID="+CONTEXT_ID)
    print("PRE723_BACKUP_ID="+BACKUP_ID)
    print("PRE723_CONTEXT_NEW_SIZE="+str(len(rb)))
    print("PRE723_CONTEXT_NEW_SHA256="+sha(rb))
    print("PRE723_APK_OR_SIGNING_MATERIAL_MODIFIED=FALSE")

if __name__=="__main__":main()
