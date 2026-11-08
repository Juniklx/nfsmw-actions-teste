#!/usr/bin/env python3
"""PRE406: backup-first record verified signed V46 global Nitro APK, device test pending.
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
MARKER="PRE406_PRE405_V46_NITRO_GLOBAL_APK_VERIFICADA_20261108"
OUT=Path("/tmp/nfsmw-pre406/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE406_PRE405_V46_NITRO_GLOBAL_APK_VERIFICADA_20261108 — build experimental pronta, funcionamento pendente

- GitHub Actions PRE401 run `42439306990` **completed/success**; artifact `13601234697` contém relatório JSON e APK. `versionCode=46`, pacote `io.github.nfsmwrecomp`, `NFSMW_V46_PRE401_GLOBAL_NITRO_FULL_ALL_CARS.apk`.
- APK verificada localmente do artifact GitHub, **47.105.541 bytes**, SHA-256 `ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`, ZIP CRC íntegro (872 entradas). Relatório `apk_validation.signed_certificate_sha256_match=true`, `signed_schemes_verified=true`, certificado v2 **permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`**. Sem criar chave nova.
- Marcador `NFSMW_PRE398_GLOBAL_NITRO_FULL` confirmado em `lib/arm64-v8a/libmain.so` junto com PRE348/PRE383; PRE364 em `librexruntime.so`. Fonte PRE398 substituiu os cinco stores do medidor `r31+252` por float `1.0` (`0x3F800000u`) para todos os veículos que utilizarem essa rotina, **sem filtro de jogador/IA**, conforme autorização expressa. Não alterou stores Speedbreaker/dinheiro, gráficos, física, proteções térmicas nem saves.
- **Drive** `1UEmKsia6yhGBleO9eCFkeLbRz54myj4M`, URL `https://drive.google.com/file/d/1UEmKsia6yhGBleO9eCFkeLbRz54myj4M/view`, pasta `1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh`, metadados de 47.105.541 bytes e nome correto confirmados; relatório `remote_md5_matches=true`.
- **IMPORTANTE:** a V46 foi compilada, assinada e publicada, mas instalação, execução, Nitro 100% durante uso prolongado e comportamento da IA **ainda estão PENDENTES** no S24 FE. Não anunciar cheat funcional até teste real. Nenhuma melhoria de FPS comprovada.
- **Próximo passo:** backup independente do save `MARCEK`, instalar **sobre V45 sem desinstalar**, testar Nitro longo em exploração livre, depois corrida com IA e entregar o novo `nfsmw.log`; separar sessão V46 de prefixos V43/V44/V45. A V45 é rollback conhecido. Relatório GitHub `docs/PRE405_V46_GLOBAL_NITRO_RELEASE_VALIDATED_20261108.md`.
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
    result={"stage":"PRE406_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<666000 or b"PRE404_PRE398_403_NITRO_GLOBAL_LIBERADO_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE406_NITRO_20261107.md",
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
    print("PRE406_STATUS",result["status"])
    print("PRE406_READBACK",result["readback"])
    print("PRE406_PHASE",result["phase"])
    print("PRE406_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
