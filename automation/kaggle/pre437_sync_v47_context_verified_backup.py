#!/usr/bin/env python3
"""PRE433: fail-closed append of BMW PRE409-PRE431 results to canonical Drive MD."""
import io,os,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload,MediaIoBaseUpload
MAIN="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP="1wsoQwGkjkooavaESe-fpjkr6UniLIxDA"
PARENT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
MARKER="PRE437_V47_PRE434_ASSINADA_E_VERIFICADA_20261108"
OUT=Path("/tmp/nfsmw-pre437/report.json")
ENTRY="""

## PRE437_V47_PRE434_ASSINADA_E_VERIFICADA_20261108 — diagnóstico de tunagem BMW (2026-11-08)

- **PRE432 confirmada**: GitHub Actions run 42465261331 `AUDIT_OK`: fonte com cadeia equivalente à V46 compilou `libmain.so` ARM64. Ambas flags dos shards `nfsmw_recomp.15.cpp` e `nfsmw_recomp.57.cpp` passaram pelo compilador; `NFSMW_PRE429_TRACE_ENTRY` e `NFSMW_PRE429_TRACE_LEVEL` tiveram uma definição cada. Não foi APK nem teste no celular.
- **PRE433 confirmada**: run 42465557317, `SYNC_OK`, atualização do contexto canônico até PRE431, com backup prévio integral preservado.
- **PRE434 primeira tentativa**: run 42481733136 falhou no `py_compile` por continuação de linha YAML, antes de build/assinatura. Correção e nova execução conforme logs.
- **PRE434 segunda tentativa FINALIZADA COM SUCESSO**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42481812845, `completed/success` (2026-11-08 13:07:10 UTC). Relatório do artefato GitHub `nfsmw-pre434-v47-bmw-passive-42481812845`: `PRE434_V47_SIGNED_AND_CALLBACKS_VERIFIED`, `signed_apk_verified=true`, `gradle_release_succeeded=true`, `drive_upload_success=true`. Signer original preservado.
- **APK V47**: `NFSMW_V47_PRE434_BMW_PASSIVE_TUNING_DIAGNOSTIC.apk`, pacote `io.github.nfsmwrecomp`, `versionCode=47`, tamanho **47.104.777 bytes**, SHA256 **`ce2de9311b80670f7f4700e426ad1a77d6cd87a836df5ae3b36d4ec872cc7461`**. Drive ID `1lkV-ZCairSEymLVa_S7kwf0CC5DhkgH8`, link https://drive.google.com/file/d/1lkV-ZCairSEymLVa_S7kwf0CC5DhkgH8/view . APK do Drive conferida bit a bit contra APK no artefato GitHub; hash e ZIP CRC conferidos.
- **Certificado PERMANENTE**, comprovado pelo relatório de validação da assinatura APK v2: SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, idêntico à V46. Relatório indica esquemas de assinatura verificados e `signed_certificate_sha256_match=true`. Nunca recriar a chave nem usar debug.
- **Biblioteca PAL `libmain.so`**: SHA256 `d009c80d94d9764b889439d3b0e64757f5911de9f68fd715b9fe53861b9d88de`, com `NFSMW_PRE429_ENTRY`, `NFSMW_PRE429_LEVEL` e `NFSMW_PRE398_GLOBAL_NITRO_FULL` presentes. Cada callback `NFSMW_PRE429_TRACE_ENTRY` e `NFSMW_PRE429_TRACE_LEVEL` possui exatamente uma definição dinâmica no ELF. Os cinco stores de Nitro full foram preservados na receita PRE398; isso **não substitui teste de funcionamento no aparelho**.
- **PRE435**: run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42483152501 `success`; analisador offline de logs com testes sintéticos. Não confirma níveis reais de BMW/Punto. Guia de teste em `docs/PRE436_V47_BMW_PASSIVE_TEST_PLAN_20261108.md`.
- **Estágio claramente separado**: V47 compilada + assinada + upload verificados; **instalação no Galaxy S24 FE ainda NÃO confirmada**, funcionamento do jogo/Nitro nesta V47 NÃO testado, níveis de upgrade de BMW e Fiat Punto NÃO medidos, tunagem NÃO corrigida. V46 PRE401 continua a baseline com Nitro infinito global confirmado por teste real PRE407; preservar V46 e save `MARCEK`.
- **Próximo passo usuário**: antes de instalar, backup integral do save `MARCEK`; instalar a V47 como atualização do mesmo pacote, sem apagar dados/desinstalar; não forçar caso Android recuse. Testar BMW M3 GTR de carreira e Fiat Punto em **processos separados**, sem compras de upgrade. Preservar dois arquivos `nfsmw.log` distintos; interpretar `NFSMW_PRE429_ENTRY` / `NFSMW_PRE429_LEVEL` com PRE435 sem inferir identidade de carro a partir de ponteiros guest. Não comprar opções `Option title`, `20/20`, `999.999.999`. Manter controle PG-9076, 1920x1080, shaders/física, cap atual 60 FPS reportado, sem contornar limites térmicos nem alegar ganho de FPS.
- **Backup documental PRE437** criado antes desta atualização: `CONTEXTO_NFSMW_BACKUP_PRE437_V47_VALIDADA_20261108.md` (Drive ID `1wsoQwGkjkooavaESe-fpjkr6UniLIxDA`). Exigir equivalência integral do backup com o arquivo canônico imediatamente antes da gravação; adendo sem apagar histórico.

"""
def sha(value):return hashlib.sha256(value).hexdigest()
def read(d,id):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=id,supportsAllDrives=True),chunksize=1024*1024)
 done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def meta(d,id):
 return d.files().get(fileId=id,fields="id,name,mimeType,parents,size",supportsAllDrives=True).execute()
def audit():
 c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",
               client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
 c.refresh(Request());d=build("drive","v3",credentials=c,cache_discovery=False)
 m=meta(d,MAIN);b=meta(d,BACKUP)
 if (m["id"]!=MAIN or m["name"]!="CONTEXTO_NFSMW.md" or m.get("mimeType")!="text/markdown" or
     PARENT not in m.get("parents",[])):raise ValueError("Canonical metadata mismatch")
 if (b["id"]!=BACKUP or b["name"]!="CONTEXTO_NFSMW_BACKUP_PRE437_V47_VALIDADA_20261108.md" or
     PARENT not in b.get("parents",[])):raise ValueError("Backup metadata mismatch")
 original=read(d,MAIN);protected=read(d,BACKUP)
 if len(original)<650000 or original!=protected:raise ValueError("Source differs from verified backup")
 if MARKER.encode() in original:raise ValueError("Duplicate PRE433 marker")
 if b"PRE407" not in original or b"PRE408" not in original or b"PRE433_BMW_AUDITORIAS_409_431_20261108" not in original:raise ValueError("Missing prior V46/PRE433 context")
 if read(d,MAIN)!=original:raise ValueError("Concurrent source update")
 merged=original+ENTRY.encode("utf-8")
 media=MediaIoBaseUpload(io.BytesIO(merged),mimetype="text/markdown",resumable=True,chunksize=1024*1024)
 req=d.files().update(fileId=MAIN,media_body=media,fields="id,name,parents,size",supportsAllDrives=True)
 out=None
 while out is None:_,out=req.next_chunk(num_retries=3)
 if out["id"]!=MAIN or out["name"]!="CONTEXTO_NFSMW.md":raise ValueError("Wrong updated file")
 if read(d,MAIN)!=merged or read(d,BACKUP)!=protected:raise ValueError("Readback/backup integrity failed")
 return {"status":"SYNC_OK","readback":True,"backup_unchanged":True,"backup_id":BACKUP,
         "source_sha256":sha(original),"backup_sha256":sha(protected),"updated_sha256":sha(merged),
         "old_bytes":len(original),"new_bytes":len(merged),"append_bytes":len(ENTRY.encode()),
         "apk_built":False,"save_modified":False,"signing_accessed":False}
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"readback":False,
                         "apk_built":False,"save_modified":False,"signing_accessed":False}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2)+"\n")
 print("PRE437_STATUS",r["status"],"ERROR",r.get("error_type","none"))
 print("PRE437_READBACK",r.get("readback",False))
 print("PRE437_BACKUP_UNCHANGED",r.get("backup_unchanged",False))
 print("PRE437_BYTES",r.get("new_bytes"))
 return 0 if r["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
