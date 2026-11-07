#!/usr/bin/env python3
"""PRE339: backup and append verified PRE336-PRE338 passive Nitro evidence and current safety gate to Drive context.
No game/guest/APK/signing/save access; fail-closed on concurrent edits.
"""
from __future__ import annotations
import hashlib,io,json,os,sys
from datetime import datetime,timezone
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload,MediaIoBaseUpload

MAIN="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP_PARENT="1xYgkEI7T6xQ_UZIaq_Ota2SQbOCo_Q78"
MARKER="PRE339_NITRO_DIVERSIDADE_PASSIVA_PRE336_338_20261107"
OUT=Path("/tmp/nfsmw-pre339/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE339_NITRO_DIVERSIDADE_PASSIVA_PRE336_338_20261107 — Novas verificações CI

- A PRE335 já atualizou o contexto canônico com a infraestrutura **GitHub Actions + Kaggle + Google Drive** e provas PRE329–PRE334; esta seção acrescenta apenas verificações posteriores.
- **PRE336** (GitHub Actions run `42412305302`, `completed/success`, `AUDIT_OK`): sonda C++ host-only `pre336_nitro_address_diversity.hpp` diferencia até 16 endereços guest de destino já calculados, com slots efêmeros e contagem por site 1–5. Não desreferencia memória guest nem atribui owner; sinaliza overflow sem reutilizar slot. Aprovada **isoladamente**, não executada no S24 FE.
- **PRE337** (run `42412457916`, `completed/success`, `AUDIT_OK`): mock confirma inserção textual reversível da PRE336 no callback PRE317 após a guarda de site, antes do limite de 12 logs da PRE247, preservando PRE316 e PRE247; sem aumento de chamadas `REX_LOAD_U32`/`REX_STORE_U32`, e rejeita segunda aplicação. Nenhuma APK alterada.
- **PRE338** (run `42412580592`, `completed/success`, `AUDIT_OK`): callback passivo composto PRE317+PRE337 compilou em runner Linux via `g++ -std=c++17 -fsyntax-only` com stub de logging; nenhuma compilação ou link ARM64 do aplicativo foi comprovada por essa run.
- Relatório: `docs/PRE336_PRE337_SONDA_DIVERSIDADE_NITRO_VALIDACOES_20261107.md`; scripts `automation/kaggle/pre336_nitro_address_diversity.hpp`, `pre337_nitro_diversity_staging.py`, `pre338_nitro_composite_native_compile_mock.py`.
- **Não concluir que `0xBFA9E7FC` seja sempre do carro do jogador**. Os quatro grupos de Nitro da PRE330 não comprovam isolamento de processos. Nenhuma referência independente ao player car foi identificada.
- Nitro infinito, Speedbreaker infinito e dinheiro ilimitado continuam **não implementados** na V41. Nenhuma V42 gerada, APK Android nova instalada ou melhoria de FPS comprovada. Manter V41, save `MARCEK`, controles touch/PG-9076, gráficos, física e proteções térmicas; chave permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- Próximo gate: validar integração nativa ARM64 isolada antes de qualquer APK diagnóstica. Em teste real comparar diversidade de endereços e referência independente do carro do jogador, com estado indeterminado por padrão; somente depois planejar mutação opt-in OFF=original.
"""
def read(d,fid):
    out=io.BytesIO()
    req=d.files().get_media(fileId=fid,supportsAllDrives=True)
    downloader=MediaIoBaseDownload(out,req,chunksize=1024*1024)
    done=False
    while not done:
        _,done=downloader.next_chunk(num_retries=4)
    return out.getvalue()
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE339_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
            "game_modified":False,"apk_built":False,"signer_accessed":False}
    phase="AUTH"
    try:
        credentials=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
          token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],
          client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
        credentials.refresh(Request())
        drive=build("drive","v3",credentials=credentials,cache_discovery=False)
        phase="PRECHECK"
        meta=drive.files().get(fileId=MAIN,fields="id,name,mimeType,modifiedTime",supportsAllDrives=True).execute()
        if meta["id"]!=MAIN or meta["name"]!="CONTEXTO_NFSMW.md":raise ValueError("unexpected canonical target")
        before=read(drive,MAIN)
        if len(before)<630000 or b"PRE335_NITRO_CHEATS_GITHUB_KAGGLE_PRE329_334_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE339_NITRO_20261107.md",
              "parents":[BACKUP_PARENT]},fields="id,name,parents",supportsAllDrives=True).execute()
            backup_id=copy["id"]
            if BACKUP_PARENT not in copy.get("parents",[]):raise ValueError("backup destination mismatch")
            original_backup=read(drive,backup_id)
            if original_backup!=before:raise ValueError("backup readback mismatch")
            phase="RECHECK"
            now=drive.files().get(fileId=MAIN,fields="modifiedTime",supportsAllDrives=True).execute()
            if now.get("modifiedTime")!=meta.get("modifiedTime") or read(drive,MAIN)!=before:
                raise ValueError("canonical file changed concurrently; do not overwrite")
            phase="APPEND"
            after=before+ENTRY.encode("utf-8")
            media=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",
                                    resumable=True,chunksize=1024*1024)
            update=drive.files().update(fileId=MAIN,media_body=media,
                fields="id,name",supportsAllDrives=True)
            response=None
            while response is None:_,response=update.next_chunk(num_retries=4)
            if response.get("id")!=MAIN or response.get("name")!="CONTEXTO_NFSMW.md":
                raise ValueError("wrong update target")
            phase="VERIFY"
            if read(drive,MAIN)!=after or read(drive,backup_id)!=before:
                raise ValueError("context or backup readback differs")
            result.update({"status":"SYNC_OK","readback":True,"context_bytes":len(after),
                "context_sha256":hashlib.sha256(after).hexdigest(),
                "backup_created":True,"backup_unchanged":True})
    except Exception as error:
        result["error_type"]=type(error).__name__
    result["phase"]=phase
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE339_STATUS",result["status"])
    print("PRE339_READBACK",result["readback"])
    print("PRE339_PHASE",result["phase"])
    print("PRE339_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
