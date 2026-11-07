#!/usr/bin/env python3
"""PRE325: append observed Galaxy S24 FE V39 runtime evidence to canonical context.
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
BACKUP="1NNUt0UujEN5Wm-_fMtl7KeqVF2k891tL"
MARKER="PRE325_PRE323_PRE324_NITRO_OWNER_LIMITS_20261107"
REPORT=Path("/tmp/nfsmw-pre325/context_sync.json")
ENTRY="""

## PRE325_PRE323_PRE324_NITRO_OWNER_LIMITS_20261107 — Auditorias verificadas

- PRE323 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42403902852 `success / AUDIT_OK`, autenticou fonte PAL `sub_82424AF0`: `r31.u64=ctx.r3.u64` na linha relativa 32, ou seja, o ponteiro do medidor Nitro vem do primeiro argumento da função, sem comprovação de que seja veículo do jogador.
- `f30` usado como limite inferior vem de `lfs f30,-4788(r28)`, fonte dados globais (linha 100); `f28` inicialmente de `lfs f28,156(r28)` (linha 292) e sofre `fadds f28,f0,f28` (linha 405). Valor concreto dos limites, entidade/owner e validade em todos os modos ainda não verificados. PRE323B readback run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42404018936 mostrou fragmentos PPC autênticos.
- PRE324 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42404187781 `success / AUDIT_OK`, varreu shards C++ gerados do PAL PRE99 e encontrou **uma** referência literal à rotina/endereço `sub_82424AF0`: sua definição, sem named direct call. Possibilidade de dispatch indireto por vtable ainda é hipótese, NÃO prova de origem de objeto, e não contradiz log V41 com 58 eventos `NFSMW_PRE316_NITRO_CYCLE`.
- As rotinas do Nitro continuam **intactas** no jogo. Sites 2/4 são stores pós-limite para consumo/recarga, mas não sabemos ainda se o objeto r31 corresponde sempre ao carro do jogador; NÃO ativar substituição indiscriminada.
- Nitro infinito, Speedbreaker infinito e dinheiro ilimitado NÃO são cheats funcionais na V41. PRE309 política C++ host-only; sem APK V42 e sem alteração de save pela auditoria. Próximo passo é identificar owner/dispatch e testar solução opt-in fail-closed OFF=original, preservando backup independente do save `MARCEK`, APK V41, certificado release permanente e controles.
- Relatório GitHub `docs/PRE323_PRE324_LIMITES_NITRO_OWNER_20261107.md`.
"""
def read(d,fid):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=fid,supportsAllDrives=True),chunksize=1024*1024);done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def main():
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 result={"stage":"PRE325_V39_RUNTIME_CONTEXT_UPDATE","status":"FAILED","readback":False}
 phase="AUTH"
 try:
  c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"]);c.refresh(Request())
  d=build("drive","v3",credentials=c,cache_discovery=False)
  phase="CHECK"
  a=read(d,MAIN);b=read(d,BACKUP)
  if a!=b or len(a)<600000 or b"PRE321_V41_NITRO_CICLO_RUNTIME_VALIDADO_20261107" not in a:raise ValueError("canonical backup mismatch or V39 log context absent")
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
 print("PRE325_STATUS",result["status"]);print("PRE325_READBACK",result["readback"]);print("PRE325_ERROR_TYPE",result.get("error_type"))
 return 0 if result["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
