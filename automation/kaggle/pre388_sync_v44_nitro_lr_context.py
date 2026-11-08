#!/usr/bin/env python3
"""PRE388: backup-first append player-confirmed V44 test and LR canary verified milestones.
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
MARKER="PRE388_PRE374_387_NITRO_LR_PLAYER_OWNER_20261107"
OUT=Path("/tmp/nfsmw-pre388/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE388_PRE374_387_NITRO_LR_PLAYER_OWNER_20261107 — Contexto confirmado e provas de fonte

- Usuário confirmou **exploração livre com somente seu carro, seguida de corrida com adversários**, nessa ordem durante a V44. PRE372 correlacionou XInput `0x2000` e consumo Nitro no slot 1 (22:04:39.351→39.368, 17 ms) e depois no slot 2 (22:05:58.967→58.985, 18 ms). Essa concordância fortalece a hipótese de identidade contextual, **não prova owner estrutural** nem torna slot estável. Relatório `docs/PRE372_V44_RUNTIME_XINPUT_NITRO_CORRELACAO_20261107.md` recebeu adendo PRE374.
- PRE375 run `42433536119`, `AUDIT_OK`: 129 shards PAL PRE99 SHA autenticado, função `sub_82424AF0` com 545 linhas em `nfsmw_recomp.66.cpp`, `r31=ctx.r3` relativo 32, loads e stores do medidor em `+252` e cargas da estrutura `+296`. Busca textual localizou apenas a definição do símbolo; chamadas indiretas/virtuais continuam possíveis.
- PRE377 run `42433732833`, `AUDIT_OK`: `ctx.r12.u64=ctx.lr` aparece no prólogo antes das alterações internas do LR; esse é candidato à captura passiva do **endereço de retorno de entrada**.
- PRE379/PRE382 source canary corrigida run `42434040838`, `AUDIT_OK`: proposta reversível em memória `NFSMW_PRE379_NITRO_ENTRY_TRACE(ctx.lr,ctx.r3)`, SHA original PAL preservado, 0 novos LOAD/STORE guest, nenhum arquivo guest modificado nem APK criada. Primeira canary PRE380 havia falhado por âncora textual e foi substituída.
- PRE383/PRE386 callback nativo usa mapa de endereços já registrado pela PRE336 e `base+252` para correlacionar LR a **slot efêmero**, com desconhecido por padrão e limite de amostras. PRE384 primeira compilação mock falhou por `\\n` literal em comentário; após correção de formatação, run `42434391604` `completed/success`, artifact `13599070670`, `AUDIT_OK`: compilação `g++` com logging stub, reversão exata e sem acesso adicional à memória emulada.
- **Nenhuma dessas etapas comprova owner de jogador, Nitro infinito ou execução de callback no ARM64.** Nenhuma V45 criada; V44 permanece diagnóstica instalada/testada. Relatório `docs/PRE387_NITRO_CALLSITE_PROVENIANCE_LR_STAGING_20261107.md`.
- Próximo gate: auditar ordenação dos patches do construtor V44 e testar composição em workspace temporário autenticado; antes de eventual V45, provar compilação ARM64 do callback e manter flag OFF. Uma eventual V45 exige versionCode 45 e certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Sem editar save `MARCEK`, shaders, resolução 1920×1080, controle PG-9076/touch, física ou proteção térmica. Não presumir melhoria FPS (cap runtime anterior 60).
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
    result={"stage":"PRE388_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<657000 or b"PRE373_PRE372_V44_RUNTIME_XINPUT_NITRO_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE388_NITRO_20261107.md",
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
    print("PRE388_STATUS",result["status"])
    print("PRE388_READBACK",result["readback"])
    print("PRE388_PHASE",result["phase"])
    print("PRE388_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
