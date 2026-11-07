#!/usr/bin/env python3
"""PRE320: append observed Galaxy S24 FE V39 runtime evidence to canonical context.
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
BACKUP="1vH-y3EIRuMcpB7ezQk36_cPXv2fym21w"
MARKER="PRE320_V41_PRE318_CONCLUIDA_APK_ASSINADA_20261107"
REPORT=Path("/tmp/nfsmw-pre320/context_sync.json")
ENTRY="""

## PRE320_V41_PRE318_CONCLUIDA_APK_ASSINADA_20261107

- V41 PRE318 para diagnóstico de ciclo Nitro foi **compilada e validada**, GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42400074496 `completed/success`. Log final `PRE318_V41_PASSIVE_NITRO_CYCLE_SIGNED_VERIFIED_ARTIFACT`, `APK verified: True`, `Drive upload: True`, encerramento aproximadamente 18:34:37Z de 2026-11-07.
- APK verificada na pasta `02_APKs` no Drive, `NFSMW_V41_PRE318_NITRO_CYCLE_PASSIVE.apk`, arquivo ID `10JipMDOml5ePoxqMYjR8TQ4pmQvkpda2`, 47.103.081 bytes, link https://drive.google.com/file/d/10JipMDOml5ePoxqMYjR8TQ4pmQvkpda2/view . versionCode 41, applicationId `io.github.nfsmwrecomp`; builder verificou assinatura permanente esperada SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`.
- Preservadas instrumentações V40 e `PRE247` de Nitro/Speedbreaker, gate BMW M3 GTR V40, renderização 1920x1080, controles e chave de assinatura. Novo marcador `NFSMW_PRE316_NITRO_CYCLE` validado no ELF ARM64 da APK; registra estatísticas de min/max e transições, sem reescrever guest stores/cheats nem save.
- **Ainda pendente:** instalação real V41 no Galaxy S24 FE, funcionamento e `nfsmw.log` de ciclo completo Nitro 0→100% com estatísticas. Build e assinatura não equivalem a funcionamento comprovado.
- **Próximo teste:** com backup independente confirmado do save MARCEK, instalar V41 por cima de V40 sem desinstalar, testar apenas Nitro até esvaziar e esperar recarga completa em nova sessão; enviar log, procurar `NFSMW_PRE316_NITRO_CYCLE`. Não comprar upgrades experimentais, não forçar desbloqueio ou editar save.
- **Cheats ainda desativados:** Nitro infinito, Speedbreaker infinito e dinheiro ilimitado não implementados funcionalmente na APK. A próxima etapa só pode integrar mutação opcional depois de caracterizar o store autoritativo e provar segurança.
"""
def read(d,fid):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=fid,supportsAllDrives=True),chunksize=1024*1024);done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def main():
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 result={"stage":"PRE320_V39_RUNTIME_CONTEXT_UPDATE","status":"FAILED","readback":False}
 phase="AUTH"
 try:
  c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"]);c.refresh(Request())
  d=build("drive","v3",credentials=c,cache_discovery=False)
  phase="CHECK"
  a=read(d,MAIN);b=read(d,BACKUP)
  if a!=b or len(a)<600000 or b"PRE319_PRE316_PRE318_NITRO_CYCLE_V41_20261107" not in a:raise ValueError("canonical backup mismatch or V39 log context absent")
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
 print("PRE320_STATUS",result["status"]);print("PRE320_READBACK",result["readback"]);print("PRE320_ERROR_TYPE",result.get("error_type"))
 return 0 if result["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
