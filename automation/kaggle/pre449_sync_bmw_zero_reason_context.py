#!/usr/bin/env python3
"""PRE433: fail-closed append of BMW PRE409-PRE431 results to canonical Drive MD."""
import io,os,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload,MediaIoBaseUpload
MAIN="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP="1d59xpOXjscWJJdiLi20u6a08sJdSeIil"
PARENT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
MARKER="PRE449_BMW_ZERO_REASON_ROTAS_20261108"
OUT=Path("/tmp/nfsmw-pre449/report.json")
ENTRY="""

## PRE449_BMW_ZERO_REASON_ROTAS_20261108 — auditorias PRE446/PRE447 (8 nov 2026)

- **Referência de aparelho imutável**: V47 PRE434, BMW type=41, Punto type=74, ambos com sete consultas PRE429 reais nos logs PRE444/PRE445. BMW: Motor0, Transmissão0, Suspensão0, Nitro3, Pneus0, Freios0, Indução forçada0. Punto: Motor4, Transmissão4, Suspensão3, Nitro3, Pneus3, Freios4, Indução forçada3. São retornos candidatos, não peças compráveis. Nitro V47 em gameplay ainda não retestado; V46 PRE401 com Nitro global permanece baseline funcional.
- **PRE446** GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42495952223: `PRE446_STATUS AUDIT_OK`. Arquivo `automation/kaggle/pre446_bmw_zero_branch_readonly.py` leu backup PRE99 autenticado e verificou SHA256 de `sub_823E5988` (`.28.cpp`), `sub_8256F818` (`.57.cpp`), `sub_8214B858` (`.50.cpp`) e `sub_8214EDA8` (`.83.cpp`). Três saídas possíveis da consulta: (a) cadeia de descritores sem chave, zero explícito na linha relativa 52; (b) caminho que lê valor derivado do atributo na linha relativa 104, possivelmente zero ou positivo; (c) fallback explícito zero na linha relativa 144, que reúne várias subcausas. Retorno <=0 evita o laço de criação de lista em `sub_8256F818`. **Não foi identificado qual ramo foi executado para a BMW no aparelho.**
- **PRE447 primeira execução** https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42496091952: falha por comparação de linha ignorar indentação; não gerou APK nem escreveu fonte. Correção da verificação em GitHub.
- **PRE447 final** https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42496205722: `PRE447_STATUS AUDIT_OK`, prévia em memória reversível sob `NFSMW_PRE447_LOOKUP_ROUTE_ENABLE` **OFF por padrão**, C++ original `sub_823E5988` SHA256 `11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad`, prévia SHA256 `aac0b47f03a43044899a5fd7150cd0691eee79f35b2c42f413919f0c61d9d230`. Inserções antes das três saídas relativas 60/126/153, identifica rotas 1/2/3, lê apenas `ctx.lr` e `ctx.r4` já presentes na função para filtrar primeira chamada original por `lr=0x8256F83C`. Sem novas chamadas, reads ou stores guest e reversível byte a byte. **Ainda NÃO é módulo compilado/linkado, NÃO foi instalado no S24 FE, NÃO identifica o ramo de runtime da BMW e NÃO altera os dados do carro.**
- **Interpretar com cuidado**: como o Punto tem retornos positivos nas mesmas sete categorias, a ausência global e invariável da chave na tabela é menos compatível com os logs; isso é inferência, não exclusão da possibilidade porque contexto/tabela pode mudar entre sessões. Nitro da BMW é exceção positiva. Ainda não comprovar se o problema BMW está no modelo específico, nos atributos da carroceria ou em outra seleção dinâmica.
- **Relatório GitHub** `docs/PRE446_PRE447_BMW_ZERO_RETURN_ROTAS_20261108.md`, commit `fba5adc83f302c42cce0623ac6f0709b26b8d911`. Não publicar logs brutos nem saves privados.
- **Próximo gate seguro**: PRE448 deve conferir integração nativa ARM64 do callback de rotas na reconstrução fonte V47 com PRE398 Nitro, PRE429 ambos callbacks e CMake, **sem APK/assinatura**; somente se aprovada considerar uma V48 **diagnóstica**, versionCode >=48, pacote `io.github.nfsmwrecomp` e certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Não alterar lojas, upgrades, preço, física, C3, controle PG-9076, gráficos/1920x1080, limites térmicos nem editar o save `MARCEK`. Não comprar `Option title`, `20/20` ou `999.999.999`. Nunca forçar zero->4.
- **Backup PRE449** integral `CONTEXTO_NFSMW_BACKUP_PRE449_BMW_ZERO_REASON_20261108.md` no Drive ID `1d59xpOXjscWJJdiLi20u6a08sJdSeIil`, cópia previamente comparada ao contexto canônico. Somente adendo, com verificação completa de leitura.
"""
def sha(value):return hashlib.sha256(value).hexdigest()
def read(d,id):
 b=io.BytesIO();dl=MediaIoBaseDownload(b,d.files().get_media(fileId=id,supportsAllDrives=True),chunksize=1024*1024)
 done=False
 while not done:_,done=dl.next_chunk(num_retries=3)
 return b.getvalue()
def meta(d,id):
 return d.files().get(fileId=id,fields="id,name,mimeType,parents,size",supportsAllDrives=True).execute()
def audit():
 c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],token_uri="https://oauth2.googleapis.com/token",
               client_id=os.environ["GOOGLE_CLIENT_ID"],client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
 c.refresh(Request());d=build("drive","v3",credentials=c,cache_discovery=False)
 m=meta(d,MAIN);b=meta(d,BACKUP)
 if (m["id"]!=MAIN or m["name"]!="CONTEXTO_NFSMW.md" or m.get("mimeType")!="text/markdown" or
     PARENT not in m.get("parents",[])):raise ValueError("Canonical metadata mismatch")
 if (b["id"]!=BACKUP or b["name"]!="CONTEXTO_NFSMW_BACKUP_PRE449_BMW_ZERO_REASON_20261108.md" or
     PARENT not in b.get("parents",[])):raise ValueError("Backup metadata mismatch")
 original=read(d,MAIN);protected=read(d,BACKUP)
 if len(original)<650000 or original!=protected:raise ValueError("Source differs from verified backup")
 if MARKER.encode() in original:raise ValueError("Duplicate PRE449 marker")
 if b"PRE407" not in original or b"PRE408" not in original or b"PRE445_V47_BMW_PUNTO_7_CATEGORIAS_20261108" not in original:raise ValueError("Missing prior V46/PRE445 context")
 if read(d,MAIN)!=original:raise ValueError("Concurrent source update")
 merged=original+ENTRY.encode("utf-8")
 media=MediaIoBaseUpload(io.BytesIO(merged),mimetype="text/markdown",resumable=True,chunksize=1024*1024)
 req=d.files().update(fileId=MAIN,media_body=media,fields="id,name,parents,size",supportsAllDrives=True)
 out=None
 while out is None:_,out=req.next_chunk(num_retries=3)
 if out["id"]!=MAIN or out["name"]!="CONTEXTO_NFSMW.md":raise ValueError("Wrong updated file")
 if read(d,MAIN)!=merged or read(d,BACKUP)!=protected:raise ValueError("Readback/backup integrity failed")
 return {"status":"SYNC_OK","readback":True,"backup_unchanged":True,"backup_id":BACKUP,
         "source_sha256":sha(original),"backup_sha256":sha(protected),"updated_sha256":sha(merged),
         "old_bytes":len(original),"new_bytes":len(merged),"append_bytes":len(ENTRY.encode()),
         "apk_built":False,"save_modified":False,"signing_accessed":False}
def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,"readback":False,
                         "apk_built":False,"save_modified":False,"signing_accessed":False}
 r["run_id"]=a.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,indent=2)+"\n")
 print("PRE449_STATUS",r["status"],"ERROR",r.get("error_type","none"))
 print("PRE449_READBACK",r.get("readback",False))
 print("PRE449_BACKUP_UNCHANGED",r.get("backup_unchanged",False))
 print("PRE449_BYTES",r.get("new_bytes"))
 return 0 if r["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
