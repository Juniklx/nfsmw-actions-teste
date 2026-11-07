#!/usr/bin/env python3
"""PRE321: append observed Galaxy S24 FE V39 runtime evidence to canonical context.
Requires preexisting verified backup, never modifies the APK or save.
"""
from __future__ import annotations
import io,os,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload,MediaIoBaseUpload
MAIN="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP="1wBZYQYykg9oKxmbLfS-T-gJLvWC3Ew8p"
MARKER="PRE321_V41_NITRO_CICLO_RUNTIME_VALIDADO_20261107"
REPORT=Path("/tmp/nfsmw-pre321/context_sync.json")
ENTRY="""

## PRE321_V41_NITRO_CICLO_RUNTIME_VALIDADO_20261107

- Novo `nfsmw.log` fornecido pelo usuário: 2.409.694 bytes, 10.373 linhas, SHA-256 `ac17e87607723c6f98b5a553b4e7c4c99ad8a0b968eea8c6af0bb1f235b4c9bc`. **Contém sessões anteriores; resultados a seguir isolam janela nova V41 15:47:58–15:48:47.**
- Marcador `NFSMW_PRE316_NITRO_CYCLE` observado **58 vezes em execução real no Galaxy S24 FE**, comprovando a instrumentação V41. Sites 1/2 Nitro +252: 12 eventos/site, contagem acumulada 150 amostras/site, queda 0,99333334 → 0,0000008149 (praticamente 0, não zero exato) entre 15:47:58.877 e 15:48:01.363.
- Sites 3/4 Nitro +252: 17 eventos/site, 2004 amostras/site, subida 0,0005555556 → 0,9951883554 (~99,52%, não 100% literal) entre 15:48:03.410 e 15:48:45.270. Site 5 sem registro PRE316 nesta sessão. Pares 1/2 e 3/4 escrevem sequências coincidentes.
- Logger com checkpoints esparsos e transições: não pressupor que os últimos 0%/100% exatos foram registrados ou que o store final autoritativo já foi identificado. PRE247 336 ocorrências é contador do arquivo concatenado, não somente da V41. PRE246 dinheiro sem evento. Ausência de `SIGSEGV`/fatal textual no arquivo não prova robustez geral.
- **A V41 agora tem instrumentação Nitro comprovada no aparelho**, além da build/assinatura/Drive confirmados pela PRE318. **Nitro infinito, Speedbreaker infinito e dinheiro ilimitado continuam NÃO implementados funcionalmente**; política PRE309 C++ ainda sem conexão ao jogo e nenhum valor forçado.
- Próximo gate: usar relatório PRE312 com os cinco stores +252 e validar o store definitivo da lógica de consumo/recarga antes de um patch opcional, reversível e OFF=original. Manter save MARCEK, certificados permanentes, V39–V41, gráficos e controles. Relatório detalhado `docs/PRE321_V41_NITRO_CICLO_RUNTIME_20261107.md`.
"""
def read(d,fid):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=fid,supportsAllDrives=True),chunksize=1024*1024);done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def main():
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 result={"stage":"PRE321_V39_RUNTIME_CONTEXT_UPDATE","status":"FAILED","readback":False}
 phase="AUTH"
 try:
  c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"]);c.refresh(Request())
  d=build("drive","v3",credentials=c,cache_discovery=False)
  phase="CHECK"
  a=read(d,MAIN);b=read(d,BACKUP)
  if a!=b or len(a)<600000 or b"PRE320_V41_PRE318_CONCLUIDA_APK_ASSINADA_20261107" not in a:raise ValueError("canonical backup mismatch or V39 log context absent")
  if MARKER.encode() in a:raise ValueError("duplicate marker")
  phase="APPEND"
  raw=a+ENTRY.encode("utf8")
  u=MediaIoBaseUpload(io.BytesIO(raw),mimetype="text/markdown",resumable=True,chunksize=1024*1024)
  req=d.files().update(fileId=MAIN,media_body=u,fields="id,name,parents",supportsAllDrives=True)
  x=None
  while x is None:_,x=req.next_chunk(num_retries=3)
  if x["id"]!=MAIN or x["name"]!="CONTEXTO_NFSMW.md":raise ValueError("wrong target")
  phase="VERIFY"
  if read(d,MAIN)!=raw or read(d,BACKUP)!=b:raise ValueError("readback")
  result.update({"status":"SYNC_OK","readback":True,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"backup_unchanged":True})
 except Exception as e:result["error_type"]=type(e).__name__
 result["phase"]=phase;result["utc"]=datetime.now(timezone.utc).isoformat()
 REPORT.write_text(json.dumps(result,indent=2)+"\n")
 print("PRE321_STATUS",result["status"]);print("PRE321_READBACK",result["readback"]);print("PRE321_ERROR_TYPE",result.get("error_type"))
 return 0 if result["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
