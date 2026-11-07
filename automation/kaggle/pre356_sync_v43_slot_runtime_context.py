#!/usr/bin/env python3
"""PRE356: backup and append verified V43 runtime Nitro per-slot results.
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
MARKER="PRE356_PRE355_V43_NITRO_SLOTS_RUNTIME_20261107"
OUT=Path("/tmp/nfsmw-pre356/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE356_PRE355_V43_NITRO_SLOTS_RUNTIME_20261107 — Log real do teste V43

- O usuário enviou novo `nfsmw.log`; análise passiva PRE355: **SHA-256 `b39ff5738a948800dfc94831b0241d705fa216c7d8543fa34d2016a006a04974`, 668.545 bytes**, iniciado em 20:19:41.096, último timestamp completo 20:22:27.418, arquivo terminando com linha incompleta. **A janela pode estar truncada.**
- V43 executou no aparelho com marcador PRE348: 108 registros `NFSMW_PRE348_NITRO_SLOT_VALUES`; PRE336: 50 registros, `distinct=3`, `overflow=false`; PRE316: 180; PRE247: 72. Somente slots 1, 2, 3 observados nesta janela; **isso não prova a quantidade de veículos presentes** nem contraria necessariamente os quatro objetos registrados na V42/PRE344.
- Os pares de sites Nitro 1/2 e 3/4 reproduziram os mesmos valores por slot. `slot=1` teve consumo em checkpoints 0,99333→0,14667 entre 20:21:51 e 20:21:55; recarga 0,00056→0,54778 a partir de 20:21:58. `slot=2` teve consumo checkpoint 0,99667→0,98667 (mínimo checkpoint 0,89333), e `slot=3` 0,99667→0,78000; ambos começam a ter consumo registrado por volta de 20:22:04. Cada slot possui contagem própria de amostras, mas a amostragem por potência de dois NÃO captura todos os estados.
- **Esclarecimento posterior do usuário:** ele esgotou o Nitro deliberadamente, aguardou a recarga visual até 100% e só depois fechou o jogo. Portanto os valores PRE348 de último checkpoint (ex. ~14,67% consumo e ~54,78% recarga do slot 1) **não representam o último valor do medidor antes de sair**; os logs são amostrados em potências de dois e o arquivo termina incompleto. Slots 2 e 3 são candidatos a rivais, mas não estão classificados, e os três slots NÃO equivalem automaticamente a três oponentes.\n- **Hipótese, NÃO prova:** slot 1 pode ser o veículo do jogador por consumir primeiro e por mais tempo. Não há vinculação semântica/player-car pointer nem anotação do instante exato da ação do usuário. Não inferir jogador pelo número de slot ou por endereço fixo.
- Dois erros de C3 texturas: 20:21:04.794 thread de links desligada, 20:21:37.495 amostragem de fingerprint desligada. `FATAL EXCEPTION` e `SIGSEGV` não aparecem neste recorte, mas o log termina incompleto.
- Resolução interna `1920×1080`, limite de **60 FPS** no startup (meta do projeto é 120 FPS); nenhum ganho comprovado.
- Relatório detalhado GitHub `docs/PRE355_V43_NITRO_SLOTS_RUNTIME_20261107.md`; auditoria local JSON `PRE355_V43_NITRO_SLOTS_AUDITORIA.json`.
- **Estado atual:** V43 PRE352 compilada, permanentemente assinada, instalada/executada pelo usuário e com PRE348 funcional no Galaxy S24 FE; cheats não implementados. V42/V41 preservadas, save `MARCEK` intocado, controle PG-9076/touch, gráficos/efeitos/física e proteções térmicas sem mudanças nesta análise.
- Próxima verificação: confirmar cenário e ação temporal do Nitro no teste V43; não alterar função `sub_82424AF0` indiscriminadamente enquanto `owner_verified=false`. Nova APK requer versionCode acima de 43 e mesmo certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
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
    result={"stage":"PRE356_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<648000 or b"PRE354_PRE346_PRE350_V43_NITRO_SLOTS_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE356_NITRO_20261107.md",
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
    print("PRE356_STATUS",result["status"])
    print("PRE356_READBACK",result["readback"])
    print("PRE356_PHASE",result["phase"])
    print("PRE356_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
