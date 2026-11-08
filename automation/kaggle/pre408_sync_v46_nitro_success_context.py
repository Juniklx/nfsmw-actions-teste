#!/usr/bin/env python3
"""PRE408: backup-first record V46 Nitro global successful S24 FE runtime test and 82/82 full samples.
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
MARKER="PRE408_PRE407_V46_NITRO_GLOBAL_FUNCIONAL_NO_S24FE_20261108"
OUT=Path("/tmp/nfsmw-pre408/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE408_PRE407_V46_NITRO_GLOBAL_FUNCIONAL_NO_S24FE_20261108 — usuário confirmou sucesso e log 82/82

- **RESULTADO COMPROVADO POR USUÁRIO E LOG:** no Galaxy S24 FE, o usuário declarou **"Deu certo"** ao experimentar a V46 PRE401 com Nitro infinito global; `nfsmw.log` novo conferido (529.809 bytes, 2.238 linhas, SHA-256 `f7955f5e7dcd69dec69660e3c2a50ceb41dd779b9952f3f2c1169713e338fbd7`), de 2026-11-08 00:14:05.210 até 00:16:06.986. Instalação, execução, marcador ativo e **funcionamento prático do Nitro infinito relatado pelo usuário**.
- `NFSMW_PRE398_GLOBAL_NITRO_FULL` aparece às 00:14:30.053 como `active=1 affects_all_objects=1 full_bits=0x3F800000`. A PRE348 mediu **82/82 checkpoints em `0x3F800000` (float32 1,0 = 100%)** para **quatro slots distintos** de Nitro (PRE336 `distinct=4`, `overflow=false`), sites 1 e 2 em cada slot. Distribuição slot 1: 20, slot 2: 22, slot 3: 20, slot 4: 20. PRE316 24 entradas min/max/last com `0x3F800000`. PRE364 65 eventos XInput; `buttons=0x2000` em seis eventos. O log prova a aplicação a múltiplos destinos, mas **não mapeia individualmente os slots a adversários específicos nem prova todas as rotas possíveis**.
- O requisito Nitro player-only foi abandonado **com autorização expressa anterior** do usuário para afetar todos os carros, incluindo IA. **Nitro infinito global está funcional e testado na V46**; os outros cheats continuam sem alteração/autorizações novas. Não recriar versão para tentar encontrar player owner de Nitro; V46 é baseline.
- Ressalva independente: **PRE194 C3 texturas** disparou às 00:14:26.183 com `copia_duplicada=true`, desativando o hilo de enlaces de texturas no restante da sessão. Nenhuma string `FATAL EXCEPTION` ou `SIGSEGV` neste log; **isso não implica estabilidade completa ou correção do C3**.
- Resolução interna 1920x1080 mantida, cap de **60 FPS** reportado (120 FPS não comprovado). Preservar shaders, efeitos, física, controle touch/PG-9076 e proteções térmicas.
- APK V46 `NFSMW_V46_PRE401_GLOBAL_NITRO_FULL_ALL_CARS.apk`, pacote `io.github.nfsmwrecomp`, versionCode 46, assinatura PERMANENTE certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, APK SHA256 `ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7`; Drive `https://drive.google.com/file/d/1UEmKsia6yhGBleO9eCFkeLbRz54myj4M/view`. V45 e anteriores são fallback; preservar save `MARCEK` e backups.
- Relatório GitHub `docs/PRE407_V46_NITRO_GLOBAL_FUNCIONANDO_NO_S24FE_20261108.md`; auditoria local `PRE407_V46_NITRO_GLOBAL_TESTE_REAL.json`.
- **Próximo passo:** tratar a V46 como primeira versão com Nitro infinito comprovadamente funcional. Acompanhamento do C3 de texturas e melhorias outras somente separadamente. Se houver nova APK, incrementar versionCode de 46, preservar certificado permanente e novos logs/evidências.
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
    result={"stage":"PRE408_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<668000 or b"PRE406_PRE405_V46_NITRO_GLOBAL_APK_VERIFICADA_20261108" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE408_NITRO_20261107.md",
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
    print("PRE408_STATUS",result["status"])
    print("PRE408_READBACK",result["readback"])
    print("PRE408_PHASE",result["phase"])
    print("PRE408_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
