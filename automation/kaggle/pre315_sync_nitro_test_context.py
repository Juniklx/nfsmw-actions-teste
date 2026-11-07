#!/usr/bin/env python3
"""PRE315: append observed Galaxy S24 FE V39 runtime evidence to canonical context.
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
BACKUP="1U9cujhQTYEJCS5kht5u4OkO2d4A2WpPw"
MARKER="PRE315_PRE313_NITRO_ESGOTAMENTO_RECARGA_20261107"
REPORT=Path("/tmp/nfsmw-pre315/context_sync.json")
ENTRY="""

## PRE315_PRE313_NITRO_ESGOTAMENTO_RECARGA_20261107 — Teste controlado

- Usuário realizou novo teste **apenas com Nitro**, consumindo até esvaziar visualmente e aguardando recarregar completamente. Arquivo log 1.609.683 bytes, 6.880 linhas, SHA-256 `2032fe0ac3fcc7e558ec1985e828eaa7482ddc9ea9cc87c926548d568ae00eb2`; várias sessões no mesmo arquivo. Sessão nova às **14:57**, não misturar com sessões antigas.
- PRE247 Nitro (PAL `sub_82424AF0`, campo +252): sites 1 e 2, 12 amostras por site, mesmo endereço guest `0xBFA9E7FC`, valores decrescentes 0,99333334→0,92000008 de 14:57:49.329 a 49.512. Sites 3 e 4 no mesmo endereço, 12 amostras por site, valores crescentes 0,00055556→0,00666667 de 14:57:53.864 a 54.048. Site 5 não observado. Interpretação: consumo + início da recarga de Nitro, congruente com relato do usuário.
- **Limitação crítica:** logger PRE247 limita a 12 gravações por site/processo, cerca de 0,18 s por caminho; portanto **o log não mostra a chegada a 0 ou 1**. Esgotamento/recarga completos foram observação do usuário; ainda falta instrumentação de transições/min/max para comprovar logs de ciclo inteiro.
- Mesmo sem o usuário usar Speedbreaker, sites 7 e 8 do candidato `sub_8246C2F0`, campo +132, registraram o limitador: site 7 valor ~1,001→1,00067, site 8 ficou em 1,0, endereço guest `0xBFA7CD34` na sessão. Isso indica que presença do marcador 7/8 não prova acionamento de Speedbreaker.
- PRE312 GitHub run `42398849592` validou estruturalmente os 5 stores do Nitro PAL nas linhas relativas 377, 411, 508, 518 e 525 (`AUDIT_OK`). O workflow original não publicou relatório devido a discrepância de nome; nomes corrigidos e reexecução de leitura acionada.
- PRE309 política de cheats em C++ **ainda não integrada no Android**. Nenhum cheat funcional ativado e nenhum patch de leitura/escrita guest aplicado nesta rodada. Próximo passo: monitoramento de baixo volume com transições/limites e identificar store definitivo, depois integrar controles opt-in sem afetar Nitro padrão, físico, save MARCEK, controles ou assinatura.
- Relatório GitHub: `docs/PRE313_TESTE_CONTROLADO_NITRO_CONSUMO_RECARGA_20261107.md`. Preserve V40, V39 e certificado permanente.
"""
def read(d,fid):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=fid,supportsAllDrives=True),chunksize=1024*1024);done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def main():
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 result={"stage":"PRE315_V39_RUNTIME_CONTEXT_UPDATE","status":"FAILED","readback":False}
 phase="AUTH"
 try:
  c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"]);c.refresh(Request())
  d=build("drive","v3",credentials=c,cache_discovery=False)
  phase="CHECK"
  a=read(d,MAIN);b=read(d,BACKUP)
  if a!=b or len(a)<600000 or b"PRE310_PRE308_PRE309_CHEATS_20261107" not in a:raise ValueError("canonical backup mismatch or V39 log context absent")
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
 print("PRE315_STATUS",result["status"]);print("PRE315_READBACK",result["readback"]);print("PRE315_ERROR_TYPE",result.get("error_type"))
 return 0 if result["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
