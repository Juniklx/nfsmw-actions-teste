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
BACKUP="1yGb14iapQRTUdr8HfTSv1tFBRwE-071C"
PARENT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
MARKER="PRE451_PRE448_NATIVE_PASS_V48_PENDENTE_20261108"
OUT=Path("/tmp/nfsmw-pre451/report.json")
ENTRY="""

## PRE451_PRE448_NATIVE_PASS_V48_PENDENTE_20261108 — teste nativo PRE448 e início de V48 (8 nov 2026)

- **PRE448 RESULTADO FINAL VERIFICADO:** GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42496806174, concluída `success` em 2026-11-08 16:10:52 UTC. Log: `PRE448_STATUS AUDIT_OK`, `PRE448_PHASE PRE448_NATIVE_VALIDATED`, `PRE448_CMAKE_CONFIG True`, `PRE448_NATIVE_LINK True`, `PRE448_ELF_ARM64 True`, `PRE448_ALL_MARKERS True`, `PRE448_NO_APK True`. CMake/NDK compilaram e vincularam o motor `libmain.so` ARM64 numa árvore descartável com cadeia fonte equivalente à V47, Nitro PRE398 e dois marcadores PRE429 preservados.
- **Definições de callbacks no ELF:** `NFSMW_PRE429_TRACE_ENTRY=1`, `NFSMW_PRE429_TRACE_LEVEL=1`, `NFSMW_PRE447_ROUTE=1`. A instrumentação de rota observa a primeira chamada existente de `sub_823E5988` e registra (categoria 0..6, razão 1/2/3, valor candidato) sem novas chamadas guest ou leituras/escritas guest. O evento é limitado e serve só a diagnóstico, **não corrige upgrades**.
- **Limitação da PRE448:** compilação nativa NÃO é APK, NÃO comprova funcionamento no celular ou identificação da rota real que a BMW utiliza. Nenhuma instalação, assinatura ou save `MARCEK` foi afetado pelo teste.
- **PRE452 V48 diagnóstica acionada** pelo gatilho `automation/kaggle/pre452_requests/start_20261108.json` no GitHub Actions: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42498853924. **Execução em andamento nesta atualização; não afirmar sucesso/assinatura/publicação sem relatório final.** Script `automation/kaggle/pre452_build_signed_v48_bmw_zero_route_diag.py`, workflow `.github/workflows/nfsmw-pre452-v48-bmw-zero-route-signed.yml`.
- **Requisitos de segurança V48:** pacote `io.github.nfsmwrecomp`, `versionCode=48`, certificado **permanente inalterado** SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. O script reaproveita receita de build V47 PRE434 + PRE401, instala somente logger de rota com verificação SHA PRE447 e exige dois callbacks PRE429, um callback PRE447, marcador Nitro PRE398 e assinatura antes de declarar APK válida. APK pretendida `NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk` (ainda não confirmada no Drive).
- **Não alterar** contagens candidatas, lojas, custos, upgrades, carro da BMW, Nitro, física, C3/SDL, gráficos, resolução interna 1920x1080, controle PG-9076, proteções térmicas ou saves. V46 PRE401 continua a referência com Nitro infinito validado no gameplay; V47 PRE434 continua diagnóstica comprovadamente instalada/testada no S24 FE. Nunca recriar a chave permanente nem usar assinatura debug.
- **Evidência prévia V47:** PRE444/PRE445: BMW (type 41) retornou `0,0,0,3,0,0,0` em sete categorias; Punto (type 74) retornou `4,4,3,3,3,4,3`. **São contagens candidatas e não peças necessariamente compráveis**. A causa da diferença de seis categorias ainda não está identificada, apesar de PRE446 mapear três retornos e PRE447 testar a prévia.
- **Próximo passo:** conferir logs de conclusão PRE452, relatório de hash/assinação/callbacks e presença real no Drive, sem assumir sucesso por status preliminar. Se aprovada, backup do save MARCEK antes de instalar V48 como atualização; testar BMW e Fiat Punto separadamente nas sete categorias sem comprar itens `Option title`, `20/20`, `999.999.999`, preservando os dois `nfsmw.log` com linhas `NFSMW_PRE447_ROUTE`. Nenhum ganho FPS ou correção BMW comprovado.
- **Relatório GitHub**: `docs/PRE450_PRE448_NATIVE_PASS_PRE452_V48_INICIADA_20261108.md`, commit `e22d361fd451173aa8025de39de5809ea7d2875d`. Backup integral do contexto antes deste adendo no Drive `CONTEXTO_NFSMW_BACKUP_PRE451_PRE448_NATIVE_20261108.md` (ID `1yGb14iapQRTUdr8HfTSv1tFBRwE-071C`), comparado byte a byte com original. Exigir adendo append-only e readback.
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
 if (b["id"]!=BACKUP or b["name"]!="CONTEXTO_NFSMW_BACKUP_PRE451_PRE448_NATIVE_20261108.md" or
     PARENT not in b.get("parents",[])):raise ValueError("Backup metadata mismatch")
 original=read(d,MAIN);protected=read(d,BACKUP)
 if len(original)<650000 or original!=protected:raise ValueError("Source differs from verified backup")
 if MARKER.encode() in original:raise ValueError("Duplicate PRE451 marker")
 if b"PRE407" not in original or b"PRE408" not in original or b"PRE449_BMW_ZERO_REASON_ROTAS_20261108" not in original:raise ValueError("Missing prior V46/PRE449 context")
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
 print("PRE451_STATUS",r["status"],"ERROR",r.get("error_type","none"))
 print("PRE451_READBACK",r.get("readback",False))
 print("PRE451_BACKUP_UNCHANGED",r.get("backup_unchanged",False))
 print("PRE451_BYTES",r.get("new_bytes"))
 return 0 if r["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
