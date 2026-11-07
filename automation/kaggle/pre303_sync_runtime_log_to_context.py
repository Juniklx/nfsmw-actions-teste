#!/usr/bin/env python3
"""PRE303: append observed Galaxy S24 FE V39 runtime evidence to canonical context.
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
BACKUP="15F3uyo2NdwX_wVp5mO4oiNsD7mh6litZ"
MARKER="PRE303_V39_RUNTIME_BMW_MENU_LOG_20261107"
REPORT=Path("/tmp/nfsmw-pre303/context_sync.json")
ENTRY="""

## PRE303_V39_RUNTIME_BMW_MENU_LOG_20261107 — Teste no Galaxy S24 FE

- Usuário enviou `nfsmw.log` sessão de 2026-11-07 11:27:41–11:29:07, 1486 linhas, 335153 bytes, SHA-256 `2543f00a48b7e86bbcfb3d6234c922550a5f5b90b82cb09f21addd8c3219a1a7`. Contém marcador exclusivo da instrumentação PRE292 incorporada à V39; não contém versão do pacote independentemente checada por `dumpsys`.
- Às 11:29:00.056: `[NFSMW_PRE292_BMW_MENU] callsite=0x82578988 type=41 event=1`. **Prova que o fluxo do menu principal com tipo 41 executou no aparelho**; `event=1` é contador de invocação e **não significa que a opção Desempenho tenha sido liberada**.
- Foram 0 entradas `NFSMW_PRE283_BMW_VTABLE` no log. A ausência não identifica por si só se as categorias foram renderizadas ou clicadas; distinguir inferência de teste visual.
- Apareceram warnings `NtCreateFile FAILED 0xc000000f` para `D:\\FRONTEND\\PLATFORMS\\CUSTOMIZATION_SHOP.LZC`, `CSHOP_frontEndEnv.dds` e `D:\\CARS\\BMWM3GTRE46\\VINYLS.BIN`. Não provaram causalidade com ausência de categorias; podem envolver fallback de recursos.
- Às 11:28:40.481 persistiu `[NFSMW_PRE194_C3 indice_fuera=false referencia_distinta=false copia_duplicada=true]`, com desabilitação do thread de texturas pelo restante da sessão. Problema independente da oficina. O log mostra 1920x1080 e limite de 60 FPS; não comprova desempenho.
- Prioridade PRE302: auditar em fonte PAL autenticada `sub_82578988`, seus saltos após comparação de modelo 41 e pontos de criação de opções; inspecionar recursos e mapeamento antes de alteração ou V40. PRE264 é dry-run/mocking, não patch validado.
- Preservar V39 assinada, assinatura permanente, save MARCEK e versões anteriores. Mais detalhes no adendo GitHub `docs/CONTEXTO_NFSMW_ADENDO_PRE286_PRE287_20261107.md`.
"""
def read(d,fid):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=fid,supportsAllDrives=True),chunksize=1024*1024);done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def main():
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 result={"stage":"PRE303_V39_RUNTIME_CONTEXT_UPDATE","status":"FAILED","readback":False}
 phase="AUTH"
 try:
  c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"]);c.refresh(Request())
  d=build("drive","v3",credentials=c,cache_discovery=False)
  phase="CHECK"
  a=read(d,MAIN);b=read(d,BACKUP)
  if len(a)<600000 or len(b)<600000 or b"PRE300_AUDITORIA_DRIVE_20261107" not in a:raise ValueError("unexpected context")
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
 print("PRE303_STATUS",result["status"]);print("PRE303_READBACK",result["readback"]);print("PRE303_ERROR_TYPE",result.get("error_type"))
 return 0 if result["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
