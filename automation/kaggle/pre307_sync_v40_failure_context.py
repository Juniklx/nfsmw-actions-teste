#!/usr/bin/env python3
"""PRE307: append observed Galaxy S24 FE V39 runtime evidence to canonical context.
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
BACKUP="1mHcsCeLkrlxsXa4I_uUFjujUzQc0t5tw"
MARKER="PRE307_V39_RUNTIME_BMW_MENU_LOG_20261107"
REPORT=Path("/tmp/nfsmw-pre307/context_sync.json")
ENTRY="""

## PRE307_PRE305_V40_MACRO_FIX_20261107 — Falha e correção experimental

- PRE305 V40 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42390457193 terminou em falha Gradle: `PRE170_GRADLE_BUILD_FALHOU`, APK não validada, upload Drive não executado. Log isolado no PRE305B https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42392051414 demonstrou erro Clang na fonte PAL gerada, linha 22762: `token is not a valid binary operator in a preprocessor subexpression`. O problema foi um `\\n` literal na diretiva `#define NFSMW_PRE264_BMW_MENU_ENABLE 1`, em vez de quebra de linha. Falha não relacionada a chaves/certificado/Drive.
- Correção aplicada no script de build experimental: duas ocorrências da string de macro ajustadas para quebra de linha real, mais guarda que valida exatamente uma linha `#define` correta e ausência de barra-n literal. Todos os patches são reconstruídos em runner isolado de fonte PRE99 com SHA verificado.
- PRE305B teste C++ sintético run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42392338077 terminou `success`, marcadores `PRE305B_MACRO_AST_OK True` e `PRE305B_SYNTHETIC_CPP_COMPILE_OK True`. Gate anexado ao workflow V40 antes de Gradle.
- Nova execução PRE305 V40: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42392404962 foi disparada, ainda em andamento quando registrado. **Não afirmar APK V40 compilada, assinada, publicada ou testada** até ler log/relatório da execução.
- V39 permanece APK de referência; manter pacote `io.github.nfsmwrecomp`, assinatura permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, save MARCEK e controles.
"""
def read(d,fid):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=fid,supportsAllDrives=True),chunksize=1024*1024);done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def main():
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 result={"stage":"PRE307_V39_RUNTIME_CONTEXT_UPDATE","status":"FAILED","readback":False}
 phase="AUTH"
 try:
  c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"]);c.refresh(Request())
  d=build("drive","v3",credentials=c,cache_discovery=False)
  phase="CHECK"
  a=read(d,MAIN);b=read(d,BACKUP)
  if a!=b or len(a)<600000 or b"PRE306_PRE302_PRE305_BMW_MENU_GATE_20261107" not in a:raise ValueError("canonical backup mismatch or V39 log context absent")
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
 print("PRE307_STATUS",result["status"]);print("PRE307_READBACK",result["readback"]);print("PRE307_ERROR_TYPE",result.get("error_type"))
 return 0 if result["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
