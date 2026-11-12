#!/usr/bin/env python3
"""PRE715: append a verified sanitized checkpoint to the existing Drive context.
The authenticated Drive update is fail-closed, preserves the SAME Drive ID,
checks a previously created independent backup, and does not access APK or keys.
"""
import argparse
import hashlib
import io
import os
import re
from pathlib import Path

CONTEXT_ID="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP_ID="1YqB_d-_0Qf25H5YFOeFO51iwNIzK8ClB"
BEFORE_SIZE=1297810
BEFORE_SHA="836205ff75f040336b48ce046590b9a6a1cdd0c0187e1c5965835f9987779f16"
CHECKPOINT=Path("docs/PRE715_V51_KAGGLE_CPP_PRECEDENCE_BOOL_POINTER_TYPES_REAL_20261112.md")
OLD="- **Próximo gate PRE715:** confirmar precedência e tipos C++ da condição negada, a natureza de \`second\` e o tipo/lifetime do vetor da linha 356, se possível com AST autenticada; caso contrário registrar \`NOT_VERIFIED\`. Não modificar APK, MAILBOX, qualidade gráfica, assinatura ou proteções térmicas."
NEW=(
"- **PRE715 concluída no Kaggle:** [run 43268860669](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43268860669) \`completed/success\`. "
"Em V51 autenticada, o dispositivo apresenta \`std::unordered_map\` com sintaxe \`bool*\` na declaração de \`requested_extensions\` (linha 155); "
"na instância, \`std::vector<bool*>\` na linha 356 corresponde ao receptor de \`push_back\` da linha 456. "
"Compilação/execução **sintética** C++20 confirmou precedência de \`! * iter->second\`, mas **não existe AST da fonte real** nem prova de habilitação Vulkan runtime. "
"[ZIP real no Drive](https://drive.google.com/file/d/1RWv7h2NL9BJ45REHj_PG34dg12Ani4Ct/view) com SHA/CRC conferidos.\n"
"- **Próximo gate PRE716:** identificar escopo/vida útil dos ponteiros de \`std::vector<bool*>\` e relação com \`VkInstanceCreateInfo\`; "
"recuperar origem de \`requested_extensions\` na instância sem expor código. Sem V52 nem alterações de gráficos ou políticas térmicas."
)
def sha(b):return hashlib.sha256(b).hexdigest()
def render(before,checkpoint):
    if len(before)!=BEFORE_SIZE or sha(before)!=BEFORE_SHA:
        raise ValueError("PRE715_CANONICAL_CONTEXT_HASH_OR_SIZE_DRIFT")
    s=before.decode("utf-8")
    if s.count(OLD)!=1:
        raise ValueError("PRE715_CONTEXT_HEADER_ANCHOR_MISSING_OR_DUPLICATE")
    if "colab" in s.lower() or "/content" in s:
        raise ValueError("PRE715_CONTEXT_HAS_LEGACY_EXECUTION_INSTRUCTIONS")
    if not checkpoint.startswith("# PRE715 "):
        raise ValueError("PRE715_CHECKPOINT_HEADER_MISMATCH")
    if "62b34aee9d7aa13d9e015f5257f1d134e1bbda8b6f1981e9c72868acb5b0f233" not in checkpoint:
        raise ValueError("PRE715_CHECKPOINT_SHA_MISSING")
    s=s.replace(OLD,NEW,1)
    s=s.rstrip("\n")+"\n\n---\n\n"+checkpoint.rstrip()+"\n"
    if "colab" in s.lower() or "/content" in s:
        raise ValueError("PRE715_NEW_CONTEXT_HAS_LEGACY_INSTRUCTIONS")
    assert s.count("PRE715 — tipos lexicais e precedência C++")==1
    return s.encode("utf-8")
def drive():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds=Credentials(token=None,
       refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
       token_uri="https://oauth2.googleapis.com/token",
       client_id=os.environ["GOOGLE_CLIENT_ID"],
       client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    creds.refresh(Request())
    return build("drive","v3",credentials=creds,cache_discovery=False)
def get_bytes(drive,id):
    data=drive.files().get_media(fileId=id,supportsAllDrives=True).execute(num_retries=4)
    if not isinstance(data,bytes):raise ValueError("PRE715_DRIVE_DOWNLOAD_NOT_BYTES")
    return data
def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--self-test",action="store_true")
    arg.add_argument("--apply",action="store_true")
    args=arg.parse_args()
    if args.self_test:
        assert CONTEXT_ID!=BACKUP_ID and re.fullmatch("[0-9a-f]{64}",BEFORE_SHA)
        assert "PRE715 concluída no Kaggle" in NEW
        assert CHECKPOINT.is_file()
        print("PRE715_CONTEXT_SYNTHETIC=PASS")
        return
    if not args.apply:arg.error("explicit --apply is required")
    checkpoint=CHECKPOINT.read_text(encoding="utf-8")
    g=drive()
    old=get_bytes(g,CONTEXT_ID)
    # Independently validate the backup created BEFORE the attempted update.
    backup=get_bytes(g,BACKUP_ID)
    if len(backup)!=BEFORE_SIZE or sha(backup)!=BEFORE_SHA or backup!=old:
        raise ValueError("PRE715_DRIVE_BACKUP_MISMATCH_OR_CANONICAL_CHANGED")
    replacement=render(old,checkpoint)
    from googleapiclient.http import MediaIoBaseUpload
    media=MediaIoBaseUpload(io.BytesIO(replacement),mimetype="text/markdown",resumable=False)
    updated=g.files().update(fileId=CONTEXT_ID,media_body=media,
      fields="id,size,modifiedTime",supportsAllDrives=True).execute(num_retries=4)
    if updated.get("id")!=CONTEXT_ID or int(updated.get("size",-1))!=len(replacement):
        raise ValueError("PRE715_DRIVE_UPDATE_METADATA_MISMATCH")
    roundtrip=get_bytes(g,CONTEXT_ID)
    if roundtrip!=replacement:
        raise ValueError("PRE715_DRIVE_READBACK_SHA_MISMATCH")
    # Backup remains unchanged.
    if sha(get_bytes(g,BACKUP_ID))!=BEFORE_SHA:
        raise ValueError("PRE715_BACKUP_CHANGED_AFTER_UPDATE")
    print("PRE715_CONTEXT_UPDATED_AND_READBACK_VERIFIED=TRUE")
    print("PRE715_CONTEXT_CANONICAL_ID="+CONTEXT_ID)
    print("PRE715_CONTEXT_BYTES="+str(len(roundtrip)))
    print("PRE715_CONTEXT_SHA256="+sha(roundtrip))
    print("PRE715_BACKUP_ID="+BACKUP_ID)
    print("PRE715_CONTEXT_APK_MODIFIED=FALSE")
if __name__=="__main__":main()
