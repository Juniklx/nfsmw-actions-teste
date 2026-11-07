#!/usr/bin/env python3
"""PRE306: append observed Galaxy S24 FE V39 runtime evidence to canonical context.
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
BACKUP="1dGu3cJ_GoVcddHUawwV7eKK1-QHm_TPh"
MARKER="PRE306_V39_RUNTIME_BMW_MENU_LOG_20261107"
REPORT=Path("/tmp/nfsmw-pre306/context_sync.json")
ENTRY="""

## PRE306_PRE302_PRE305_BMW_MENU_GATE_20261107 — Estrutura comprovada, V40 experimental

- No log real V39, `[NFSMW_PRE292_BMW_MENU] callsite=0x82578988 type=41 event=1` confirmou execução da função candidata no Galaxy S24 FE.
- PRE302 GitHub Actions run 42389794686 `AUDIT_OK`: inspecionou PRE99 autenticado (`nfsmw_recomp.5.cpp` SHA-256 `26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07`) e confirmou `r10=1` para modelo 41, dois ramos alternativos de bloqueio e 5 chamadas estáticas que adicionam opções.
- PRE302B run 42389945142 e PRE302C run 42390047927: caso global 0 bloqueia chamadas 1/2, caso global não-zero bloqueia chamadas 3/4 quando `r10=1`. Essas quatro chamadas criam IDs 2049 e 2050, em modos distintos. Chamada 5 adiciona ID 2051 fora dos bloqueios.
- PRE304 run 42390247261 `AUDIT_OK`: modelo 41 permite apenas opção 2051; outro modelo permite opções 2049, 2050 e 2051, nos dois valores da condição global. Vincular 2051 a `Visual` é inferência coerente com relato, não mapeamento de nomes verificado.
- PRE305: experimento isolado V40 preparado `automation/kaggle/pre305_build_signed_v40_bmw_menu_gate_experimental.py`. Apenas muda classificação HeroCar do modelo 41 dentro de `sub_82578988` PAL, via `NFSMW_PRE264_BMW_MENU_ENABLE` no builder, sem reescrever saves nem rotinas de upgrades. Mantém logger V39 e assinatura permanente. GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42390457193 **em andamento no momento deste registro**. NÃO declarar APK V40 pronta/instalada/funcional até certificação e teste.
- **Risco experimental:** mostrar as categorias não garante que selecionar Peças ou Desempenho funcione para BMW especial. Antes de executar a APK experimental no aparelho, preservar cópia independente do save `MARCEK`; manter V39 anterior e chave/certificado permanente. Não desinstalar aplicativo como forma de reverter sem backup do save.
- Próximo passo técnico: verificar build PRE305 (assinatura, versionCode 40, SHA e upload Drive); depois testar entrada no menu sem alterar save e coletar log. Qualquer falha do builder deve ser corrigida sem reaplicar patch às cegas.
"""
def read(d,fid):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=fid,supportsAllDrives=True),chunksize=1024*1024);done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def main():
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 result={"stage":"PRE306_V39_RUNTIME_CONTEXT_UPDATE","status":"FAILED","readback":False}
 phase="AUTH"
 try:
  c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"]);c.refresh(Request())
  d=build("drive","v3",credentials=c,cache_discovery=False)
  phase="CHECK"
  a=read(d,MAIN);b=read(d,BACKUP)
  if a!=b or len(a)<600000 or b"PRE303_V39_RUNTIME_BMW_MENU_LOG_20261107" not in a:raise ValueError("canonical backup mismatch or V39 log context absent")
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
 print("PRE306_STATUS",result["status"]);print("PRE306_READBACK",result["readback"]);print("PRE306_ERROR_TYPE",result.get("error_type"))
 return 0 if result["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
