#!/usr/bin/env python3
"""PRE319: append observed Galaxy S24 FE V39 runtime evidence to canonical context.
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
BACKUP="11p3k2ReCJWqvOwbxdIQk_H2BTKYjh1KB"
MARKER="PRE319_PRE316_PRE318_NITRO_CYCLE_V41_20261107"
REPORT=Path("/tmp/nfsmw-pre319/context_sync.json")
ENTRY="""

## PRE319_PRE316_PRE318_NITRO_CYCLE_V41_20261107 — Monitor passivo de ciclo

- PRE313: usuário testou esgotamento completo do Nitro e recarga até 100%; PRE247 capturou apenas primeiros 12 stores/site. PRE312 PRE99 autenticado (Nitro PAL `sub_82424AF0`, campo +252, 5 sites) foi auditado; stores e valores originais devem ficar intocados.
- PRE316 criou monitor C++ de telemetria passiva de Nitro com mínimo/máximo, contador, mudanças de faixa e checkpoints esparsos de contagem, exclusivamente sobre os bits de float já calculados e escritos pelo jogo (sem novos guest loads/stores). PRE317 integra o monitor ao logger existente PRE247 apenas em árvore temporária autenticada, com reversibilidade e checagem de source SHA original.
- Testes C++ host PRE316 e PRE317 na run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42399887087 **success**: `PRE316_STATUS AUDIT_OK` (4 grupos) e `PRE317_STATUS AUDIT_OK` (57 logs sintéticos durante centenas/milhares de amostras, volume limitado). Essa aprovação não significa código NDK nem cheats no APK.
- PRE318 V41 **diagnóstica** preparada com `versionCode 41`, package `io.github.nfsmwrecomp`, mesmo certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, gate BMW V40 preservado, logger `NFSMW_PRE316_NITRO_CYCLE` requerido no ELF PAL. Run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42400074496 está EM EXECUÇÃO no momento desta atualização. **Não declarar V41 compilada, assinada, publicada ou testada até conclusão verificada**.
- Os três cheats Nitro infinito, Speedbreaker infinito e dinheiro ilimitado **continuam NÃO IMPLEMENTADOS FUNCIONALMENTE** na APK; PRE309 política de ativação existe somente em testes host, não conectada ao jogo. Não mexer no save MARCEK, compra de peças, gráficos, controles, shaders ou limites térmicos.
- Próxima ação: verificar run PRE318 e se houver APK validada/salva, fazer backup independente do save e testar ciclo Nitro no S24 FE com novo `nfsmw.log`. Relatório técnico GitHub: `docs/PRE316_PRE318_NITRO_MONITOR_CICLO_COMPLETO_V41_20261107.md`.
"""
def read(d,fid):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=fid,supportsAllDrives=True),chunksize=1024*1024);done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def main():
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 result={"stage":"PRE319_V39_RUNTIME_CONTEXT_UPDATE","status":"FAILED","readback":False}
 phase="AUTH"
 try:
  c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"]);c.refresh(Request())
  d=build("drive","v3",credentials=c,cache_discovery=False)
  phase="CHECK"
  a=read(d,MAIN);b=read(d,BACKUP)
  if a!=b or len(a)<600000 or b"PRE315_PRE313_NITRO_ESGOTAMENTO_RECARGA_20261107" not in a:raise ValueError("canonical backup mismatch or V39 log context absent")
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
 print("PRE319_STATUS",result["status"]);print("PRE319_READBACK",result["readback"]);print("PRE319_ERROR_TYPE",result.get("error_type"))
 return 0 if result["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
