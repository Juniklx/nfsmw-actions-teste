#!/usr/bin/env python3
"""PRE342: backup and append verified signed V42 release evidence to Drive context.
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
MARKER="PRE342_V42_PRE340_APK_ASSINADA_VERIFICADA_20261107"
OUT=Path("/tmp/nfsmw-pre342/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE342_V42_PRE340_APK_ASSINADA_VERIFICADA_20261107 — Release diagnóstico validado

- **V42 PRE340 compilada/assinada/publicada**: GitHub Actions run `42413667387`, job `128526993478`, `completed/success`, relatório `PRE340_V42_PASSIVE_NITRO_DIVERSITY_SIGNED_VERIFIED_ARTIFACT` e `phase=COMPLETE`. Artefato `13590129971` contém APK e JSON de verificação.
- **APK**: `NFSMW_V42_PRE340_NITRO_DIVERSITY_PASSIVE.apk`; `versionCode=42`, `io.github.nfsmwrecomp`, 47.103.185 bytes, SHA-256 `5bcb301663149f516d60b1327d9b51992ddf1698cd71a7a571d5190a9d037c1a`. SHA-256 calculado independentemente nos bytes do artifact GitHub e do arquivo baixado do Drive: correspondência confirmada.
- **Drive**: ID `1fZ4_4iBNuVEKKkMBmRTgH81WHSALrN3V`, https://drive.google.com/file/d/1fZ4_4iBNuVEKKkMBmRTgH81WHSALrN3V/view ; `remote_md5_matches=true` e `folder_verified=true` no relatório do builder. Cópia Drive verificada por SHA-256 independente.
- **Certificado permanente preservado**: SHA-256 do certificado APK v2 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Bibliotecas ARM64 exigidas presentes (10); shaders PAL/USA e library USA preservados. Marcadores `NFSMW_PRE316_NITRO_CYCLE` e `NFSMW_PRE336_NITRO_DIVERSITY` verificados dentro de `libmain.so` assinado.
- Staging PRE337: `guest_stores_rewritten=0`, `extra_guest_loads=0`, `cheat_enabled=false`, `owner_verified=false`, `reverse_exact=true`. A V42 adiciona diagnóstico passivo do destino de stores Nitro, não cheat.
- **PENDENTE**: instalar a V42 sobre a V41 no Galaxy S24 FE **sem desinstalar**, com backup independente do save `MARCEK`; comprovar abertura do jogo, Nitro consumindo/recarregando, novos logs `NFSMW_PRE336_NITRO_DIVERSITY` e relação real jogador/NPC. **Instalação, funcionamento V42, ganho FPS e Nitro infinito NÃO estão comprovados**.
- Relatório técnico: `docs/PRE340_V42_APK_ASSINADA_PUBLICADA_VERIFICADA_20261107.md`. Preservar V41, saves, PG-9076/touch, gráficos 1920x1080, física e proteção térmica. Próxima versão, se necessária, deve manter a chave original e incrementar versionCode.
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
    result={"stage":"PRE342_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<640000 or b"PRE339_NITRO_DIVERSIDADE_PASSIVA_PRE336_338_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE342_NITRO_20261107.md",
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
    print("PRE342_STATUS",result["status"])
    print("PRE342_READBACK",result["readback"])
    print("PRE342_PHASE",result["phase"])
    print("PRE342_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
