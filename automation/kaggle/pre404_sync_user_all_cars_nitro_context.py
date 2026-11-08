#!/usr/bin/env python3
"""PRE404: backup-first record user-approved all-cars global Nitro and pending signed V46 build.
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
MARKER="PRE404_PRE398_403_NITRO_GLOBAL_LIBERADO_20261107"
OUT=Path("/tmp/nfsmw-pre404/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE404_PRE398_403_NITRO_GLOBAL_LIBERADO_20261107 — requisito alterado pelo usuário

- **Decisão expressa do usuário:** aceita que **todos os carros, inclusive adversários**, possam ter Nitro infinito. Portanto Nitro **não exige mais filtro player-only**. Restrições dos outros cheats permanecem; Speedbreaker, dinheiro e outros recursos não foram autorizados por essa mudança.
- PRE392 V45 instalada/testada, mas os dois slots Nitro amostrados tinham `guest_lr=0x824252DC`. Essa descoberta não impede o **Nitro global**; não é preciso insistir na identificação do carro controlado para esse cheat.
- Novo patch `automation/kaggle/pre398_global_nitro_full_staging.py` substitui só as **cinco gravações** da rotina autenticada `sub_82424AF0` em `r31+252` para IEEE754 float 1,0 (`0x3F800000u`), em qualquer objeto que execute esses sites. Atualiza o callback PRE247 para reportar os bits efetivamente gravados e adiciona log uma vez `NFSMW_PRE398_GLOBAL_NITRO_FULL`. Não fixa slot, LR, endereço guest, não adiciona guest reads e mantém a contagem original de stores. Patch reversível e com backups isolados. Isso é uma **alteração funcional ativa**, não um diagnóstico passivo.
- **PRE399** GitHub run `42439120243`, `completed/success`, artifact `13601200565`, `AUDIT_OK`, PRE99 SHA autenticado `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`, fonte PAL SHA `eec9b82e51bbfcb573cd0f965e3ed7639bbbd291b285f9fc6d5a7d1e77cd735f`: cinco sites, reversão exata PAL e callback, 0 writes alheios, 0 novos guest LOAD/STORE. **Prova somente de fonte**, não de jogo funcionando com Nitro infinito.
- **PRE401 V46 experimental**: builder `automation/kaggle/pre401_build_signed_v46_global_nitro_full.py`, workflow `.github/workflows/nfsmw-pre401-v46-global-nitro-all-cars.yml`, run `42439306990`. APK alvo `NFSMW_V46_PRE401_GLOBAL_NITRO_FULL_ALL_CARS.apk`, pacote `io.github.nfsmwrecomp`, versionCode 46, **mesmo certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`**. A build estava `in_progress` no momento desta atualização; **NÃO afirmar APK pronta/publicada antes do relatório final e da assinatura verificada**.
- Após validar a V46, testar **exploração livre e corrida com IA**. Confirmar Nitro 100% durante uso prolongado, registrar `nfsmw.log` e verificar regressões. **Não há Nitro infinito comprovado no aparelho ainda**, nem comprovação de que todos os adversários ativem essa rotina em todo contexto.
- Preservar APKs V45 e anteriores como fallback, save `MARCEK` em backup independente, controles touch/PG-9076, resolução interna 1920x1080, shaders, texturas, efeitos, física, limites térmicos e certificado de assinatura; nenhuma alegação de ganho FPS (últimos logs cap 60).
- Relatório GitHub `docs/PRE403_GLOBAL_NITRO_ALL_CARS_V46_EXPERIMENTAL_20261107.md`.
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
    result={"stage":"PRE404_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<663000 or b"PRE397_PRE392_395_NITRO_V45_LR_PARAMETER_PROVENANCE_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE404_NITRO_20261107.md",
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
    print("PRE404_STATUS",result["status"])
    print("PRE404_READBACK",result["readback"])
    print("PRE404_PHASE",result["phase"])
    print("PRE404_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
