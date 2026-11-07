#!/usr/bin/env python3
"""PRE335: backup and append verified PRE329-PRE334 + CI workflow state to Drive context.
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
MARKER="PRE335_NITRO_CHEATS_GITHUB_KAGGLE_PRE329_334_20261107"
OUT=Path("/tmp/nfsmw-pre335/CONTEXT_SYNC_STATUS.json")
ENTRY="""

## PRE335_NITRO_CHEATS_GITHUB_KAGGLE_PRE329_334_20261107 — Fluxo e auditorias verificadas

- **Fluxo operacional atual:** repositorio GitHub `Juniklx/nfsmw-actions-teste`; GitHub Actions executa auditorias e builds com scripts em `automation/kaggle/`, mas **estar nesse diretorio nao significa que a etapa rodou no Kaggle**. Kaggle permanece ambiente das etapas explicitamente orquestradas para ele; Drive `NFSMW_Android` armazena contexto, backups, APKs e logs. Resultado de job só é confirmado por run/log/artifact, não por commit de trigger.
- **Readback GitHub Actions (PRE328) validado:** status sanitizado em `docs/generated/PRE328_PRE325_SANITIZED_STATUS.json`, `PRE328_PRE327_SANITIZED_STATUS.json` e subsequentemente PRE332–PRE334; permite localizar run_id e recuperar logs/artefatos reais. Nunca publicar credenciais ou endereços brutos nessas saídas resumidas.
- **PRE325:** run `42407721044` `AUDIT_OK`; cinco refs a `sub_82424AF0`: declaração, tabela init, definição PAL, registro runtime, e contexto da edição USA com `ctx.lr=0x82424AF0`. **Nenhum named direct caller PAL e owner desconhecido.**
- **PRE327:** run `42407723203` `AUDIT_OK` mas a busca binária analisou só `sdk/thirdparty/sdl3/test/moose.dat` (56.320 bytes), sem correspondências; **inconclusiva para vtable do jogo**.
- **PRE329:** `nfsmw.log` original V41, SHA-256 `ac17e87607723c6f98b5a553b4e7c4c99ad8a0b968eea8c6af0bb1f235b4c9bc`, 2.409.694 bytes, 10.373 linhas. Em 15:47:58–15:48:47, sites Nitro 1/2/3/4 PRE247 escreveram no **mesmo endereço guest observado** `0xBFA9E7FC`, 12 registros por site. Base implicita `0xBFA9E700` via `r31=ctx.r3` e offset +252. É evidência de destino de escrita nessa sessão, NÃO do proprietário do carro.
- **PRE330:** no arquivo concatenado foram encontrados quatro grupos temporais iniciados 14:53:07, 14:57:49, 15:05:09 e 15:47:58: 192 registros PRE247 Nitro (48 por grupo), todos com endereço `0xBFA9E7FC`. Os grupos **não comprovam quatro processos independentes**, e PRE247 limita registros a 12/site/processo.
- **PRE332:** run inicial `42410914389` encontrou apenas função Nitro num shard; correção para todos os 129 shards PAL, run `42411097708` `AUDIT_OK`, encontrou sete funções próximas por endereço em arquivos diferentes. Só `sub_82424AF0` mencionou deslocamento +252 entre as sete. Proximidade de código não prova mesma classe.
- **PRE333:** run `42411376197` `AUDIT_OK`, 129 shards PAL; 315 combinações de offsets candidatas distribuídas por 301 funções; entre seis correspondências aos cinco offsets {52,72,88,252,296}, a maioria era coincidência estrutural, NÃO rotina Nitro identificada.
- **PRE334:** run `42411632872` `AUDIT_OK`; qualificação dirigida às seis correspondências completas de offsets: **somente** `sub_82424AF0` reproduziu atribuição inicial de r3, LOAD e STORE em +252 e LOAD +296. Isso corrobora identificação da função Nitro; **não prova owner do jogador nem autoriza mutação**. Outros 309 candidatos da PRE333 não foram qualificados na PRE334.
- **Arquivos de evidência:** `docs/PRE329_V41_CORRELACAO_RUNTIME_ENDERECOS_NITRO_20261107.md`, `docs/PRE330_V41_QUATRO_GRUPOS_NITRO_ENDERECO_20261107.md`, `docs/PRE331_PLANO_PROVA_OWNER_NITRO_20261107.md`, `docs/PRE332_AUDITORIA_VIZINHANCA_PAL_NITRO_20261107.md`, `docs/PRE333_CANDIDATOS_LAYOUT_NITRO_PAL_20261107.md`, `docs/PRE334_NITRO_CANDIDATOS_QUALIFICACAO_PAL_20261107.md`.
- **Estado do jogo:** V41 PRE318 assinada/instalada/testada com Nitro ciclo diagnosticado na S24 FE. Cheats Nitro infinito, Speedbreaker infinito e dinheiro ilimitado permanecem **não funcionais**. Nenhuma V42 criada. Não modificar save `MARCEK`, APK V39–V41, controle PG-9076/touch, gráficos, física ou proteções térmicas. Manter assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, pacote `io.github.nfsmwrecomp`.
- **Próximo gate:** demonstrar em runtime referencia independente ao carro controlado pelo jogador e diferenciar NPC/IA, ou manter classificação indeterminada; só depois considerar sonda passiva/reversível e eventualmente Nitro opt-in fail-closed OFF=original. Não usar endereço guest fixo como seletor de player.
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
    result={"stage":"PRE335_CANONICAL_CONTEXT_SYNC","status":"FAILED","readback":False,
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
        if len(before)<630000 or b"PRE325_PRE323_PRE324_NITRO_OWNER_LIMITS_20261107" not in before:
            raise ValueError("unexpected or stale canonical source")
        if MARKER.encode() in before:
            result.update({"status":"ALREADY_PRESENT","readback":True,"context_bytes":len(before),
                           "context_sha256":hashlib.sha256(before).hexdigest()})
        else:
            phase="BACKUP"
            copy=drive.files().copy(fileId=MAIN,body={
              "name":"CONTEXTO_NFSMW_BACKUP_ANTES_PRE335_NITRO_20261107.md",
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
    print("PRE335_STATUS",result["status"])
    print("PRE335_READBACK",result["readback"])
    print("PRE335_PHASE",result["phase"])
    print("PRE335_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"] in ("SYNC_OK","ALREADY_PRESENT") else 1
if __name__=="__main__":sys.exit(main())
