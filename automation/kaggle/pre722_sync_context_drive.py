#!/usr/bin/env python3
"""PRE722 fail-closed append to canonical Drive context; preserve backup and signing."""
import argparse
import hashlib
import io
import os
from pathlib import Path

CONTEXT_ID="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP_ID="1HsTdIzP8oS0wD8SBzMQwdACd2Ti52KDp"
EXPECTED_BYTES=1334432
EXPECTED_SHA="bf0aff7561e3d9a8d74d30350673a5f6d895c6c5324811b6d3588b951f8a6cd9"
DOC=Path("docs/PRE722_V51_KAGGLE_VULKAN_COUNT_CAST_ARGUMENT_ORIGIN_REAL_20261112.md")
RUN_ID="43295701230"
ZIP_SHA="e741ee56d3b037f2dd375dd5a720dc3fdb4d972b41a0374c18783c550c283ade"

def sha(b):return hashlib.sha256(b).hexdigest()

def compose(before:bytes,doc:str)->bytes:
    if len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA:
        raise ValueError("PRE722_CANONICAL_CONTEXT_SHA_DRIFT")
    s=before.decode("utf-8")
    if not s.endswith("\n") or "PRE721_REAL_KAGGLE_PASS" not in s[-2500:]:
        raise ValueError("PRE722_EXPECTED_PRE721_TAIL_MISSING")
    if "# PRE722 " in s or "PRE722_REAL_KAGGLE_PASS" in s:
        raise ValueError("PRE722_ALREADY_SYNCED")
    if s.count("# PRE721 ")!=1 or s.count("# PRE720 ")!=1 or s.count("# PRE719 ")!=1 or s.count("# PRE718 ")!=1 or s.count("# PRE717 ")!=1:
        raise ValueError("PRE722_PREVIOUS_CHECKPOINT_COUNTS_WRONG")
    if not doc.startswith("# PRE722 ") or RUN_ID not in doc or ZIP_SHA not in doc:
        raise ValueError("PRE722_CHECKPOINT_CONTENT_DRIFT")
    if len(doc)>16000 or "-----BEGIN PRIVATE KEY" in doc or "NFSMW_ASSINATURA_CREDENCIAIS.properties" in doc:
        raise ValueError("PRE722_CHECKPOINT_SAFETY_GATE")
    suffix=(
      "\n\n---\n\n"
      "## ATUALIZAÇÃO VERIFICADA — PRE722 (2026-11-12)\n\n"
      "PRE722 tem run Kaggle remoto autenticado e ZIP conferido no Drive. "
      "Este bloco é mais recente que PRE721, sem modificar V51 ou assinatura permanente. "
      "O próximo gate sugerido é PRE723: identificar o receptor da chamada .size() na linha 355 "
      "e compará-lo ao vetor de nomes na linha 501, sem divulgar código privado, "
      "sem alegar erro Vulkan ou ganho de FPS.\n\n"
    )
    after=(s.rstrip("\n")+suffix+doc.rstrip()+"\n\n---\n").encode("utf-8")
    if len(after)<=len(before)+500 or after==before:
        raise ValueError("PRE722_NOT_APPEND")
    if after.decode("utf-8").count("# PRE722 ")!=1:
        raise ValueError("PRE722_DUPLICATE_CHECKPOINT")
    return after

def drive():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    for k in ("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET"):
        if not os.environ.get(k):raise ValueError("PRE722_MISSING_GOOGLE_ENV")
    c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    c.refresh(Request())
    return build("drive","v3",credentials=c,cache_discovery=False)

def read_bytes(api,file_id):
    b=api.files().get_media(fileId=file_id,supportsAllDrives=True).execute(num_retries=4)
    if not isinstance(b,bytes):raise ValueError("PRE722_DRIVE_NOT_BYTES")
    return b

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    doc=DOC.read_text(encoding="utf-8")
    if a.self_test:
        assert len(EXPECTED_SHA)==64 and len(ZIP_SHA)==64 and EXPECTED_BYTES>1000000
        assert RUN_ID in doc and ZIP_SHA in doc and doc.startswith("# PRE722 ")
        assert CONTEXT_ID!=BACKUP_ID and "PRE722" in doc
        print("PRE722_CONTEXT_LOCAL_CHECKPOINT_PASS=TRUE")
        return
    if not a.apply:p.error("--apply required")
    api=drive()
    before=read_bytes(api,CONTEXT_ID)
    backup=read_bytes(api,BACKUP_ID)
    if before!=backup or len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA:
        raise ValueError("PRE722_CONTEXT_OR_BACKUP_DRIFT_NO_WRITE")
    after=compose(before,doc)
    from googleapiclient.http import MediaIoBaseUpload
    media=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=False)
    written=api.files().update(fileId=CONTEXT_ID,media_body=media,
        fields="id,size,modifiedTime",supportsAllDrives=True).execute(num_retries=4)
    if written.get("id")!=CONTEXT_ID or int(written.get("size",-1))!=len(after):
        raise ValueError("PRE722_WRITE_METADATA_MISMATCH")
    rb=read_bytes(api,CONTEXT_ID)
    if rb!=after or sha(rb)!=sha(after):
        raise ValueError("PRE722_CONTEXT_READBACK_MISMATCH")
    if sha(read_bytes(api,BACKUP_ID))!=EXPECTED_SHA:
        raise ValueError("PRE722_BACKUP_MODIFIED")
    print("PRE722_CANONICAL_CONTEXT_UPDATED_AND_READBACK_VERIFIED=TRUE")
    print("PRE722_CONTEXT_ID="+CONTEXT_ID)
    print("PRE722_BACKUP_ID="+BACKUP_ID)
    print("PRE722_CONTEXT_NEW_SIZE="+str(len(rb)))
    print("PRE722_CONTEXT_NEW_SHA256="+sha(rb))
    print("PRE722_APK_OR_SIGNING_MATERIAL_MODIFIED=FALSE")

if __name__=="__main__":main()
