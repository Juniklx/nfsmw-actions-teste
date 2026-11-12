#!/usr/bin/env python3
"""Append verified PRE717-PRE719 checkpoints to the same canonical Drive markdown file.
No source, APK, credentials, or key modification. Fail closed on SHA or backup drift.
"""
import argparse
import hashlib
import io
import os
from pathlib import Path

CONTEXT_ID="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP_ID="14oiuGnMTou0r5-EyB1C8oiNG4Eq0YMl6"
BEFORE_BYTES=1311450
BEFORE_SHA256="a8665027e433ac783d97ced6d0aa4bf040b97895f7cf327c5ff82e64bbb1ff76"
CHECKPOINT_FILES=[
 Path("docs/PRE717_V51_KAGGLE_VULKAN_INSTANCE_RETRY_SOURCE_REAL_20261112.md"),
 Path("docs/PRE718_V51_KAGGLE_VULKAN_INSTANCE_POINTER_FALLBACK_REAL_20261112.md"),
 Path("docs/PRE719_V51_KAGGLE_VULKAN_POINTER_COUNT_MUTATIONS_REAL_20261112.md"),
]
RUN_IDS=["43280564101","43284212530","43287455419"]
EXPECTED_ZIP_SHA=[
 "3b26ffaac23c102c85f422f5166eac93b882575e02552149db38c60b5ee32555",
 "d11aa23b1fb7852821637d223bd882c53a9ae1e5d6f60ffe126dbfd7ca35c393",
 "3f812b9cd8825b67dbc8e9e20c177f909093563cd5a76ad453aa344df7b54c41",
]
def sha(x): return hashlib.sha256(x).hexdigest()

def compose(before:bytes,docs:list[str])->bytes:
    if len(before)!=BEFORE_BYTES or sha(before)!=BEFORE_SHA256:
        raise ValueError("PRE719_CANONICAL_CONTEXT_CHANGED_OR_WRONG_SHA")
    original=before.decode("utf-8")
    if not original.endswith("\n") or "**Próxima PRE717:**" not in original[-6000:]:
        raise ValueError("PRE719_CANONICAL_TAIL_ANCHOR_DRIFT")
    if any(("# PRE717 " in original,"# PRE718 " in original,"# PRE719 " in original)):
        raise ValueError("PRE719_CONTEXT_ALREADY_HAS_NEW_CHECKPOINTS")
    if len(docs)!=3: raise ValueError("PRE719_NOT_THREE_CHECKPOINTS")
    for index,doc in enumerate(docs):
        if not doc.startswith(("# PRE717 ","# PRE718 ","# PRE719 ")[index]):
            raise ValueError("PRE719_CHECKPOINT_HEADING_DRIFT_"+str(index))
        if RUN_IDS[index] not in doc or EXPECTED_ZIP_SHA[index] not in doc:
            raise ValueError("PRE719_CHECKPOINT_EVIDENCE_MISSING_"+str(index))
        if len(doc)>20000 or "-----BEGIN PRIVATE KEY" in doc or "NFSMW_ASSINATURA_CREDENCIAIS.properties" in doc:
            raise ValueError("PRE719_CHECKPOINT_SAFETY_OR_SIZE")
    suffix=(
     "\n\n---\n\n"
     "## ATUALIZAÇÕES VERIFICADAS — PRE717, PRE718 e PRE719 (2026-11-12)\n\n"
     "**Este bloco é posterior à PRE716 e substitui apenas o próximo passo histórico daquela etapa.** "
     "A V51 e sua assinatura não foram alteradas; análises exclusivamente lexicais, sem AST/CFG ou runtime Vulkan comprovados. "
     "Os artefatos têm hashes e links de Drive verificados. "
     "O próximo gate é PRE720: forma do \`for\` da linha 531 e RHS de \`enabledExtensionCount\` na linha 535.\n\n"
    )
    for doc in docs: suffix+=doc.rstrip()+"\n\n---\n\n"
    new=(original.rstrip("\n")+suffix.rstrip()+"\n").encode("utf-8")
    if new==before or len(new)<len(before)+1000:
        raise ValueError("PRE719_APPEND_UNEXPECTED")
    check=new.decode("utf-8")
    if any(check.count("# "+stage+" ")!=1 for stage in ("PRE717","PRE718","PRE719")):
        raise ValueError("PRE719_NOT_EXACTLY_ONCE")
    return new

def client():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    for key in ("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET"):
        if not os.environ.get(key): raise ValueError("MISSING_REQUIRED_GOOGLE_CREDENTIAL_ENV")
    c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    c.refresh(Request())
    return build("drive","v3",credentials=c,cache_discovery=False)

def get_bytes(service,file_id):
    data=service.files().get_media(fileId=file_id,supportsAllDrives=True).execute(num_retries=4)
    if not isinstance(data,bytes):raise ValueError("PRE719_DRIVE_BYTES_NOT_AVAILABLE")
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--apply",action="store_true")
    args=p.parse_args()
    docs=[f.read_text(encoding="utf-8") for f in CHECKPOINT_FILES]
    if args.self_test:
        assert CONTEXT_ID!=BACKUP_ID
        assert len(BEFORE_SHA256)==64 and BEFORE_BYTES>1000000
        assert len(docs)==3 and all(id in d for id,d in zip(RUN_IDS,docs))
        synthetic=("prefix\n\n**Próxima PRE717:** historical checkpoint\n").encode("utf8")
        # Test the appendix structure without weakening the real file SHA gate.
        assert all(d.startswith("# PRE"+str(717+i)+" ") for i,d in enumerate(docs))
        print("PRE719_CONTEXT_LOCAL_CHECKPOINTS=PASS")
        return
    if not args.apply:p.error("explicit --apply required")
    api=client()
    before=get_bytes(api,CONTEXT_ID)
    backup=get_bytes(api,BACKUP_ID)
    if before!=backup or len(backup)!=BEFORE_BYTES or sha(backup)!=BEFORE_SHA256:
        raise ValueError("PRE719_BACKUP_OR_CANONICAL_CONTEXT_DRIFT")
    replacement=compose(before,docs)
    from googleapiclient.http import MediaIoBaseUpload
    payload=MediaIoBaseUpload(io.BytesIO(replacement),mimetype="text/markdown",resumable=False)
    write=api.files().update(fileId=CONTEXT_ID,media_body=payload,
        fields="id,size,modifiedTime",supportsAllDrives=True).execute(num_retries=4)
    if write.get("id")!=CONTEXT_ID or int(write.get("size",-1))!=len(replacement):
        raise ValueError("PRE719_CONTEXT_UPDATE_METADATA_MISMATCH")
    readback=get_bytes(api,CONTEXT_ID)
    if readback!=replacement or sha(readback)!=sha(replacement):
        raise ValueError("PRE719_CONTEXT_READBACK_MISMATCH")
    if sha(get_bytes(api,BACKUP_ID))!=BEFORE_SHA256:
        raise ValueError("PRE719_BACKUP_CHANGED_AFTER_WRITE")
    print("PRE719_CANONICAL_CONTEXT_UPDATED_AND_READBACK_VERIFIED=TRUE")
    print("PRE719_CONTEXT_ID="+CONTEXT_ID)
    print("PRE719_BACKUP_ID="+BACKUP_ID)
    print("PRE719_CONTEXT_NEW_SIZE="+str(len(readback)))
    print("PRE719_CONTEXT_NEW_SHA256="+sha(readback))
    print("PRE719_APK_OR_SIGNING_MATERIAL_MODIFIED=FALSE")

if __name__=="__main__": main()
