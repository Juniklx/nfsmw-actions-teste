#!/usr/bin/env python3
"""PRE397: backup-first canonical context append V45 LR runtime plus authenticated Nitro parameter source audits.
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
MARKER="PRE397_PRE392_395_NITRO_V45_LR_PARAMETER_PROVENANCE_20261107"
OUT=Path("/tmp/nfsmw-pre397/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE397_PRE392_395_NITRO_V45_LR_PARAMETER_PROVENANCE_20261107 — V45 executada, LR rejeitado e fontes auditadas

- **V45 PRE390 validada e executada no Samsung Galaxy S24 FE:** pacote `io.github.nfsmwrecomp`, versionCode 45, certificado permanente original SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Relatório GitHub `docs/PRE392_V45_RUNTIME_NITRO_LR_UNICO_DOIS_SLOTS_20261107.md`. O usuário enviou `nfsmw.log` SHA256 `60101bab4e30ba36b5ddc6f44bc19f6fd0dd495af0ac01cd4f08e48fd42140e7`; a sessão **V45 é a terceira**, iniciada 23:17:38.348, não confundir com as sessões anteriores V43/V44 concatenadas.
- **PRE392 runtime V45:** 20 registros `PRE383_NITRO_CALLSITE` distribuídos em dois slots (11 no slot 1, nove no slot 2). **Todos os 20 apresentaram o mesmo guest LR `0x824252DC`**, logo LR isolado **não discrimina os objetos observados** nem serve como filtro player-only. PRE336 `distinct=2`, `overflow=false`, e a PRE364 XInput `0x2000` antecede primeiro consumo de Nitro em slot 1 por 16 ms e em slot 2 por 17 ms. Correlação temporal é hipótese contextual, **não referência estrutural comprovada ao jogador**. `owner_verified=false`, `cheat_enabled=false`.
- **PRE393** run GitHub `42438407333` `completed/success`, artifact `13599918607`, leitura fonte PAL autenticada `nfsmw_recomp.66.cpp`, SHA256 `eec9b82e51bbfcb573cd0f965e3ed7639bbbd291b285f9fc6d5a7d1e77cd735f`: os três loads de `r31+296` em linhas relativas 136,267,370 alimentam estruturas lidas via registradores r30/r11/r8, offsets `+28,+24,+12,+20`, `+16,+0`, `+4` e cálculos em ponto flutuante. **Inferência**: provável estrutura de parâmetros do Nitro, não owner verificado. Relatório `docs/PRE393_NITRO_296_FLOAT_PARAMETER_DATAFLOW_20261107.md`.
- **PRE395** run `42438573836` `completed/success`, artifact `13600129527`, `AUDIT_OK`: `r26.u64=ctx.r4.u64` na linha relativa 37, com leituras float `r26+20` nos trechos 279/391; `r28` é construído de base constante nas linhas 90–92 e fornece floats em offsets `-4788,-4,0,+156`. `r31+136` aparece nos trechos relativos 148/174 e é comparado ao inteiro `2` como condição de fluxo. **`ctx.r4` é parâmetro adicional de entrada, tipo e owner desconhecidos**; campo 136 também sem classe semântica comprovada. Relatório `docs/PRE395_NITRO_R4_R26_R28_FIELD136_ORIGIN_20261107.md`.
- **Decisão:** não usar `LR`, slot fixo, endereço guest fixo, `+296`, `+136`, nem `r4` como filtro player-only sem vínculo independente e teste negativo contra IA. Nitro infinito, Speedbreaker e dinheiro permanecem OFF; V45 segue APK de referência. Nenhuma nova APK ou patch game foi criado por PRE393/PRE395.
- **Próximo gate técnico:** investigar identidade do argumento de entrada `ctx.r4` (função chamadora/despacho, se identificável) ou referência de carro controlado em outra estrutura, sem atribuir tipo por analogia. Se for necessário novo teste runtime, deve ser observação passiva, limitada, com prova fail-closed. Eventual V46 requer versionCode 46, **mesmo certificado permanente** e preservar save `MARCEK`, controle PG-9076/touch, 1920×1080, shaders, efeitos, física e proteções térmicas. Cap 60 FPS visto em logs V45 não demonstra meta de 120 atingida.
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
    result={"stage":"PRE397_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<660000 or b"PRE388_PRE374_387_NITRO_LR_PLAYER_OWNER_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE397_NITRO_20261107.md",
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
    print("PRE397_STATUS",result["status"])
    print("PRE397_READBACK",result["readback"])
    print("PRE397_PHASE",result["phase"])
    print("PRE397_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
