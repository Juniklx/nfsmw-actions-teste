#!/usr/bin/env python3
"""PRE369: backup and append verified player input route and V44 pending build evidence.
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
MARKER="PRE369_PRE357_365_XINPUT_NITRO_V44_DIAGNOSTICO_20261107"
OUT=Path("/tmp/nfsmw-pre369/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE369_PRE357_365_XINPUT_NITRO_V44_DIAGNOSTICO_20261107 — Rota de entrada do jogador e nova instrumentação

- **Ponto de partida:** V43 PRE352 instalada e executada no Galaxy S24 FE com PRE348 funcional. No teste PRE355 o usuário esgotou o Nitro e deixou recarregar até 100%; slot 1 é candidato contextual, mas nenhum owner comprovado. Não programar filtro `slot==1`.
- **PRE357** run `42425715809`, `AUDIT_OK`, artifact `13594523981`: varredura de snapshot PRE99 autenticado, **46 arquivos de input**, 11.092 linhas, 13 com correspondências/190 hits. Encontrou `sdl_input_driver.cpp` e `xam_input.cpp`; sem identificar botão Nitro.
- **PRE359/PRE361** runs `42425869079` e `42426056579` `AUDIT_OK`: `XamInputGetState_entry` encaminha para `input_system()->GetState(actual_user_index,input_state)`; `XINPUT_FLAG_ANY_USER` é direcionado ao índice 0. Os eventos SDL de botão passam por `OnControllerDeviceButtonChangedLocked`, que traduz para XInput. Somente eventos SDL não cobrem necessariamente entrada por toque.
- **PRE362** run `42426195916`, `AUDIT_OK`, artifact `13595088364`: 20 fontes de input SDK verificadas (16 com matches). `nativo/sdk/src/input/input_system.cpp` SHA-256 `ee84079f668806af48f3a739d53213523c77c55ed202eebe8c3110c474c7432a`; `InputSystem::GetState` agrega estados nativos em `merged` usando `GetDeviceState`/`MergeInto` e o copia para `out_state`. **É ponto para medir comando no host sem novas leituras guest**.
- **PRE364/PRE365**: staging reversível `automation/kaggle/pre364_xinput_user0_passive_staging.py` observa até **256 transições** de bits XInput + cruzamentos de limiar dos gatilhos para usuário 0; marcador `NFSMW_PRE364_XINPUT_USER0`, sem alterar entregas do estado ao jogo. PRE365 run `42426480964` `AUDIT_OK`, artifact `13594659520`, comprovou SHA original e reversão byte exata, sem operações guest adicionais. Isso não prova Nitro button nem owner.
- **PRE367/V44**: builder GitHub `automation/kaggle/pre367_build_signed_v44_nitro_input_correlation_passive.py`, workflow `.github/workflows/nfsmw-pre367-v44-nitro-input-correlation-passive.yml`, run `42426649208`. `versionCode=44`, pacote `io.github.nfsmwrecomp`, APK nome alvo `NFSMW_V44_PRE367_NITRO_INPUT_CORRELATION_PASSIVE.apk`; preserva a chave permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Verificações requerem marcadores PRE316/PRE336/PRE348/PRE364 e assinatura original. **A build estava em andamento ao preparar esta atualização; não afirmar APK criada, assinada ou instalada até validar artefato.**
- **Próximo teste após eventual validação da V44**: confirmar backup independente do save `MARCEK`, instalar sobre V43 sem desinstalar; registrar pressões e solturas deliberadas de Nitro e comparar `NFSMW_PRE364_XINPUT_USER0` versus `NFSMW_PRE348_NITRO_SLOT_VALUES` em exploração livre e corrida com IA. Correlação temporal não equivale, isoladamente, a prova estrutural de player car. Sem a prova e caso negativo IA, Nitro infinito, Speedbreaker infinito e dinheiro ilimitado continuam OFF; nenhuma mutação global da função `sub_82424AF0`.
- Relatório GitHub `docs/PRE357_PRE368_PLAYER_INPUT_NITRO_V44_PROGRESSO_20261107.md`. Preservar V41–V43, touch/PG-9076, 1920×1080, shaders, efeitos, física e proteção térmica; não prometer ganho FPS. As últimas sessões observaram cap configurado de 60 apesar de meta 120, sem otimização nesta etapa.
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
    result={"stage":"PRE369_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<650000 or b"PRE356_PRE355_V43_NITRO_SLOTS_RUNTIME_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE369_NITRO_20261107.md",
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
    print("PRE369_STATUS",result["status"])
    print("PRE369_READBACK",result["readback"])
    print("PRE369_PHASE",result["phase"])
    print("PRE369_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
