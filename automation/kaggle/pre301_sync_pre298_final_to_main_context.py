#!/usr/bin/env python3
"""PRE301: append verified PRE298 final findings to canonical Drive context with backup.
Does not read, alter or publish game data, signing material or saves.
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
MARKER="PRE301_PRE298_FINAL_CACHE_REPRODUCIBILITY"
REPORT=Path("/tmp/nfsmw-pre301/drive_context_append.json")
ENTRY="""

## PRE301_PRE298_FINAL_CACHE_REPRODUCIBILITY — 2026-11-07

- PRE298 GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42383054863 **completed/success**, mas o sucesso refere-se a duas builds ARM64 PAL, **não ao cache**. Relatório extraído via PRE298B https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42387021709 .
- Iteração 1: 1330,06 s (22min10s), 49 compilações cacheáveis, **0 hits**, 49 misses. `libmain.so` 116.758.848 bytes, SHA-256 `74068d1a512c34b134a16838faf5f6ef12f36cd7182f29ea29ab8efd961a81fc`.
- Iteração 2: 1378,91 s (22min59s), 98 chamadas cacheáveis acumuladas, **0 hits**, 98 misses. `libmain.so` 116.758.816 bytes, SHA-256 `4357e9ddd42d9c97d26ffebde39fa2d50228f15af397b48b758f810eb2331299`.
- A segunda foi 48,85 s mais lenta; DSOs diferem por 32 bytes e SHA. **Cache de objetos do jogo PRE296 NÃO APROVADO PARA RELEASE OU PERSISTÊNCIA**. PRE295C do cache SDK continua um canário, não otimização comprovada de tempo do jogo.
- Hipóteses ainda não comprovadas: caminhos temporários diferentes, flags, dependências CMake/cabeçalhos, metadados ELF. Próxima análise somente leitura: `compile_commands.json`, `ccache` em modo debug filtrado, fonte normalizada, seções ELF e hash; antes de ativar cache exigir hits reais, equivalência e ganho temporal medido.
- Artefato técnico: https://github.com/Juniklx/nfsmw-actions-teste/blob/main/docs/PRE298_RESULTADO_REAL_PAL_CACHE_SEM_HITS_20261107.md .
- PRE300 Drive audit preservada; V39 continua a última APK validada no Drive, sem modificação de assinatura, saves MARCEK, jogo ou gráficos.
"""
def sha(x):return hashlib.sha256(x).hexdigest()
def drive():
 c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
 c.refresh(Request())
 return build("drive","v3",credentials=c,cache_discovery=False)
def read(d,i):
 b=io.BytesIO();r=MediaIoBaseDownload(b,d.files().get_media(fileId=i,supportsAllDrives=True),chunksize=1024*1024)
 done=False
 while not done:_,done=r.next_chunk(num_retries=4)
 return b.getvalue()
def main():
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 r={"stage":"PRE301_SYNC_PRE298_FINAL","status":"FAILED","main_id":MAIN,"backup_id":BACKUP,"readback":False}
 phase="CONNECT"
 try:
  d=drive()
  phase="VERIFY_BACKUP"
  a=read(d,MAIN);b=read(d,BACKUP)
  if a!=b or len(a)<600000:raise ValueError("canonical context/backup mismatch")
  if MARKER.encode() in a:raise ValueError("already synced")
  if b"PRE300_AUDITORIA_DRIVE_20261107" not in a:raise ValueError("PRE300 context not present")
  new=a+ENTRY.encode("utf-8")
  phase="UPDATE_IN_PLACE"
  u=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=True,chunksize=1024*1024)
  request=d.files().update(fileId=MAIN,media_body=u,fields="id,name,parents,size",supportsAllDrives=True)
  meta=None
  while meta is None:_,meta=request.next_chunk(num_retries=4)
  if meta.get("id")!=MAIN or meta.get("name")!="CONTEXTO_NFSMW.md":raise ValueError("unexpected Drive metadata")
  phase="READBACK"
  if read(d,MAIN)!=new or read(d,BACKUP)!=b:raise ValueError("Drive readback mismatch")
  r.update({"status":"SYNC_OK","readback":True,"sha256":sha(new),"bytes":len(new),"backup_unchanged":True})
 except Exception as exc:r["error_type"]=type(exc).__name__
 r["phase"]=phase;r["utc"]=datetime.now(timezone.utc).isoformat()
 REPORT.write_text(json.dumps(r,indent=2)+"\n")
 print("PRE301_STATUS",r["status"])
 print("PRE301_READBACK",r["readback"])
 print("PRE301_PHASE",r["phase"])
 print("PRE301_ERROR_TYPE",r.get("error_type"))
 return 0 if r["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
