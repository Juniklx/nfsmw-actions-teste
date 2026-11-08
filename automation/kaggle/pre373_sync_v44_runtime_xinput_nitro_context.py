#!/usr/bin/env python3
"""PRE373: backup-first append verified V44 runtime XInput/Nitro correlation.
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
MARKER="PRE373_PRE372_V44_RUNTIME_XINPUT_NITRO_20261107"
OUT=Path("/tmp/nfsmw-pre373/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE373_PRE372_V44_RUNTIME_XINPUT_NITRO_20261107 — Duas correlações controle/Nitro em V44

- **V44 PRE370 comprovadamente executada no Galaxy S24 FE** no novo `nfsmw.log` enviado pelo usuário. Arquivo SHA-256 `533f6619bf133225a69c7976e74420f1819e4e6b3950d6f6dd3f6ad11ee2eba2`, 1.353.757 bytes, 5.640 linhas; contém sessão anterior V43 iniciada 20:19:41 e **nova V44 iniciada 22:04:03.721**, indo até 22:06:38.702 em 2026-11-07. Não somar as duas sessões.
- **Somente V44:** 139 transições `NFSMW_PRE364_XINPUT_USER0`, 154 checkpoints `NFSMW_PRE348_NITRO_SLOT_VALUES`, 58 `NFSMW_PRE336_NITRO_DIVERSITY` (4 slots, sem overflow), 184 `NFSMW_PRE316_NITRO_CYCLE`. Os quatro slots tiveram sites 1/2 de consumo e 3/4 de recarga.
- **Duas correspondências temporais reproduzidas:** 22:04:39.351 `seq=23 buttons=0x2000`, seguido de primeiro consumo `site=1 slot=1` às 22:04:39.368 (**17 ms**). Às 22:05:58.967 `seq=123 buttons=0x2000`, seguido de primeiro consumo `site=1 slot=2` às 22:05:58.985 (**18 ms**). Outras 9 pressões do bit 0x2000 foram vistas, mas a PRE348 amostra apenas ordinais potências de dois e não permite inferir ausência de consumo em cada toque.
- **Inferência forte porém NÃO comprovação semântica:** bit XInput 0x2000 é candidato a comando Nitro no controle; slot 1 e posteriormente slot 2 podem representar o carro controlado pelo jogador em contextos diferentes. **Não fixar nenhum slot ou endereço**: slots são atribuídos pela ordem de observação, e o log não demonstra troca de carro nem identidade estrutural player-car. `owner_verified=false`, `nitro_button_verified=false` até prova mais forte. Cheats continuam OFF.
- Uma falha C3 texturas em V44 às 22:04:36.451; nenhum `FATAL EXCEPTION` ou `SIGSEGV` textual na janela. Startup 1920×1080 internos, cap 60 FPS, sem ganho comprovado.
- Relatório GitHub `docs/PRE372_V44_RUNTIME_XINPUT_NITRO_CORRELACAO_20261107.md`. Auditoria JSON local `PRE372_V44_CORRELACAO_INPUT_NITRO.json` fornecida ao usuário.
- Próximo gate: confirmar com usuário se o teste teve **exploração livre primeiro e corrida com IA depois** (somente se necessário); procurar referência estrutural independente a veículo controlado ou ligação inequívoca XInput↔carro. Não modificar `sub_82424AF0` indiscriminadamente; preservar V43 e V44, save MARCEK, assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, controles, gráficos, física e proteções térmicas.
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
    result={"stage":"PRE373_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<654000 or b"PRE369_PRE357_365_XINPUT_NITRO_V44_DIAGNOSTICO_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE373_NITRO_20261107.md",
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
    print("PRE373_STATUS",result["status"])
    print("PRE373_READBACK",result["readback"])
    print("PRE373_PHASE",result["phase"])
    print("PRE373_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
