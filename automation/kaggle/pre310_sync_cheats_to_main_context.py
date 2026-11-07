#!/usr/bin/env python3
"""PRE310: append observed Galaxy S24 FE V39 runtime evidence to canonical context.
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
BACKUP="1BBSD57fmgYevBDEc_boWct3oBU07Sl3S"
MARKER="PRE310_V39_RUNTIME_BMW_MENU_LOG_20261107"
REPORT=Path("/tmp/nfsmw-pre310/context_sync.json")
ENTRY="""

## PRE310_PRE308_PRE309_CHEATS_20261107 — Continuidade dos cheats prioritária

- Após testar a V40 no Galaxy S24 FE, o usuário priorizou Nitro infinito, Speedbreaker infinito e dinheiro ilimitado. A V40 abriu categorias da oficina BMW, mas algumas como Transmissão exibem `Option title`, nível `20/20` e `999.999.999` sem evidência de upgrades válidos; Nitro tem aparência mais coerente. Não comprar itens experimentalmente sem backup do save.
- Novo `nfsmw.log` de 2026-11-07 inclui duas sessões, 3.241 linhas. Instrumentação PRE247 identificou **24 registros de site 7 e 24 de site 8**, mesmo endereço guest `0xBFA7CD34` nas sessões; site 7 escreveu floats `0x3F8015D8` (20x) e `0x3F802BB1` (4x), site 8 `0x3F800000` (24x). Nenhum evento 1–6 apareceu; limites da instrumentação não provam ausência de execução de outros caminhos.
- Site 7/8 pertencem ao **candidato Speedbreaker** em função PAL `sub_8246C2F0`, campo relativo +132; não são Nitro. Nitro permanece candidato `sub_82424AF0`, campo +252, sites 1–5.
- PRE308 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42396222544 `AUDIT_OK`, fonte PRE99 autenticada `nfsmw_recomp.24.cpp` SHA-256 `e5cf7f0f0b7369615432845bbbfdcf0786f6a4646b0872dfb037fc6a6c320b71`, stores speedbreaker sites 6/7/8 em linhas relativas 115/148/158. PRE308B run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42396360249 inspecionou fluxo PPC: subtração, adição, comparação e clamp de valor, justificando eventos 7→8. Não equivale à identificação de consumo de Speedbreaker; não forçar valor 1,0 sem comprovar semântica.
- PRE309 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42396555371 `AUDIT_OK`: política C++ em `automation/kaggle/pre309_cheats_optin_policy.hpp` e mock `pre309_cheats_optin_policy_mock.py` para três toggles desligados por padrão e autorização explícita/identidade/sessão validada. Valor de medidor retorna original com gates inválidos e recusa floats não finitos. Dinheiro continua pass-through, sem mexer no saldo. **Host mock apenas; não há hook integrado no jogo e NENHUM cheat ativo na V40.**
- Relatório GitHub `docs/PRE308_PRE309_CHEATS_SPEEDBREAKER_RUNTIME_E_POLITICA_20261107.md` e adendo principal atualizado. Próxima ação: nova sessão de corrida com consumo real de Nitro e Speedbreaker, coletar eventos antes de estourar cotas de logger (12 por site por processo) e instrumentação orientada a consumo, seguida de integração opt-in reversível sob build/certificado permanente.
- Proteger APKs V39/V40, save MARCEK, versãoCode crescente 41 para nova release, pacote `io.github.nfsmwrecomp`, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, gráficos 1920x1080, controles, shaders e proteções térmicas.
"""
def read(d,fid):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=fid,supportsAllDrives=True),chunksize=1024*1024);done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def main():
 REPORT.parent.mkdir(parents=True,exist_ok=True)
 result={"stage":"PRE310_V39_RUNTIME_CONTEXT_UPDATE","status":"FAILED","readback":False}
 phase="AUTH"
 try:
  c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"]);c.refresh(Request())
  d=build("drive","v3",credentials=c,cache_discovery=False)
  phase="CHECK"
  a=read(d,MAIN);b=read(d,BACKUP)
  if a!=b or len(a)<600000 or b"PRE307_PRE305_V40_MACRO_FIX_20261107" not in a:raise ValueError("canonical backup mismatch or V39 log context absent")
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
 print("PRE310_STATUS",result["status"]);print("PRE310_READBACK",result["readback"]);print("PRE310_ERROR_TYPE",result.get("error_type"))
 return 0 if result["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
