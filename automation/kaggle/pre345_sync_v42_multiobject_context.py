#!/usr/bin/env python3
"""PRE345: backup and append verified V42 four-target Nitro diagnostic evidence.
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
MARKER="PRE345_PRE344_V42_QUATRO_DESTINOS_NITRO_20261107"
OUT=Path("/tmp/nfsmw-pre345/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE345_PRE344_V42_QUATRO_DESTINOS_NITRO_20261107 — Runtime V42, owner em aberto

- **Novo nfsmw.log do usuário**, SHA-256 `6bb43f510a3818b23a7c5b3430f9f53c93c3a6bb35e1c0e5638f728c25085441`, 794.852 bytes, 3.074 linhas, janela 19:30:10–19:33:18 em 2026-11-07; análise local passiva.
- PRE336: **62 registros, `distinct=4`, `overflow=false`**, slots efêmeros 1, 2, 3, 4; todos atingem máscara `0x0F` (sites 1/2/3/4). Primeira observação: 19:31:12.654, 19:31:20.826, 19:31:53.458 e 19:31:58.397, respectivamente. Site 5 sem registro.
- A PRE343 anterior mostrou apenas **1** destino na exploração livre que o usuário afirmou ser **sem adversários**. No novo arquivo, 4 endereços distintos em uma única sessão indicam que a função Nitro processa múltiplas instâncias, mas **não comprovam 4 carros, nem qual slot pertence ao jogador ou a IA**. O log não fornece prova independente do modo de jogo nem de número de participantes.
- PRE247, limitado a 12 logs/site, mostrou endereço guest `0xBFB0BF7C` para sites Nitro 1/2/3/4; diferente de `0xBFA9E7FC` da V41/PRE343. Não fixar endereços; PRE336 não divulga endereço bruto dos slots posteriores.
- PRE316 teve 188 registros agregados, 45/site nos sites 1/2 e 49/site em 3/4; checkpoints máximos observados 1024 consumo e 8192 recarga. Essas contagens **não são separadas por objeto**.
- Dois erros C3 não relacionados diretamente ao Nitro no log: thread de texturas desabilitada por inconsistência de índice em voo em 19:30:34; amostragem de fingerprint desabilitada por divergência em 19:31:03. Nenhum `FATAL EXCEPTION` ou `SIGSEGV` textual na janela. Startup `1920x1080` internos mas `limite FPS 60`, contra meta 120; não inferir ganho FPS.
- **Bloqueio do cheat Nitro infinito:** não intervir indiscriminadamente em `sub_82424AF0` pois processa ao menos quatro destinos. Exigir referência independente do veículo do jogador e teste negativo com IA, `owner=indeterminado` em caso de dúvida, OFF=original e sem alterar save `MARCEK`.
- Relatório GitHub `docs/PRE344_V42_NITRO_QUATRO_DESTINOS_RUNTIME_20261107.md`. V42 permanece diagnóstica assinada, sem cheat funcional; V41 preservada. Próxima versão deve manter certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` e incrementar versionCode se houver novo APK.
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
    result={"stage":"PRE345_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<643000 or b"PRE342_V42_PRE340_APK_ASSINADA_VERIFICADA_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE345_NITRO_20261107.md",
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
    print("PRE345_STATUS",result["status"])
    print("PRE345_READBACK",result["readback"])
    print("PRE345_PHASE",result["phase"])
    print("PRE345_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
