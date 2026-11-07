#!/usr/bin/env python3
"""PRE354: backup and append verified PRE346/PRE350 and V43 build pending stage.
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
MARKER="PRE354_PRE346_PRE350_V43_NITRO_SLOTS_20261107"
OUT=Path("/tmp/nfsmw-pre354/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE354_PRE346_PRE350_V43_NITRO_SLOTS_20261107 — Busca owner e compilação diagnóstica

- O usuário confirmou que o teste PRE344 da V42 ocorreu numa **corrida com quatro carros no total (seu veículo + três carros controlados pela IA)**; PRE336 registrou quatro destinos distintos, com sites de consumo e recarga 1–4 em cada destino. Isso sugere um medidor por veículo no cenário observado, mas não identifica qual slot é do jogador.
- PRE346 run `42421838788` `success/AUDIT_OK`: snapshot PRE99 autenticado; **1.134 fontes nativas examinadas**, **zero referências nomeadas** explícitas a player car/vehicle nos diretórios auditados. Esse resultado não exclui um ponteiro do jogador em código recompilado anônimo, vtables ou símbolos não preservados.
- PRE348: novo observador passivo C++ `pre348_nitro_slot_values.hpp`, utilizando somente `stored_f32_bits` e slot recuperado da tabela PRE336. Registra checkpoints de valores por slot e site (1–5), sem registrar endereço bruto, sem leitura guest adicional e sem modificar stores.
- PRE349: staging reversível na fonte PRE337 do callback PRE247, com checagens de integridade e duplicação; PRE350 run `42422168386`, `completed/success`, validou mock C++, staging Python, reversão e compilação `g++ -fsyntax-only` do callback composto PRE317+PRE337+PRE349. Isso ainda não comprova execução ARM64 no telefone.
- PRE352: derivada da V42 com `versionCode=43`, pacote `io.github.nfsmwrecomp`, nome alvo `NFSMW_V43_PRE352_NITRO_SLOT_VALUES_PASSIVE.apk`, mesmo certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Disparo GitHub Actions run `42422376260`. **No instante desta atualização, a etapa de build estava em andamento; não afirmar APK gerada ou assinada sem verificar relatório e artefato final.**
- Detalhes: `docs/PRE346_PRE353_NITRO_OWNER_V43_DIAGNOSTICO_20261107.md`. A V43 é exclusivamente diagnóstica para comparar atividade individual durante pressões deliberadas de Nitro. Não usar correlação temporal como prova definitiva de identidade se IA puder reproduzir sinais similares.
- Até comprovação independente player/NPC, Nitro infinito, Speedbreaker infinito e dinheiro ilimitado permanecem **não funcionais**; qualquer mutação global em `sub_82424AF0` é proibida. Preservar V42, V41, save `MARCEK`, controle PG-9076/touch, resolução 1920x1080, efeitos, física e proteção térmica. Não modificar nem recriar a chave permanente.
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
    result={"stage":"PRE354_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<645000 or b"PRE345_PRE344_V42_QUATRO_DESTINOS_NITRO_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE354_NITRO_20261107.md",
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
    print("PRE354_STATUS",result["status"])
    print("PRE354_READBACK",result["readback"])
    print("PRE354_PHASE",result["phase"])
    print("PRE354_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
