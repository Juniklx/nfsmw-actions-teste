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
BACKUP="1h_jmsUo9yB3QGnY0Hn1TQJjTclHjYAVA"
PARENT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
MARKER="PRE454_V48_PRE452_SIGNED_VERIFIED_20261108"
OUT=Path("/tmp/nfsmw-pre454/report.json")
ENTRY="""

## PRE454_V48_PRE452_SIGNED_VERIFIED_20261108 — APK V48 assinada e verificada (8 nov 2026)

- **PRE452 RESULTADO FINAL**: GitHub Actions run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42498853924, `completed/success` em 2026-11-08 16:35:06 UTC; log `PRE452_STATUS VERIFIED`, `PRE452_VERSION 48`. Relatório do artefato `nfsmw-pre452-v48-zero-route-42498853924` id **13625337410**, com `status=PRE452_V48_SIGNED_ZERO_ROUTE_DIAGNOSTIC_VERIFIED`, `signed_apk_verified=true`, `permanent_certificate_verified=true`, `drive_upload_success=true`, `gradle_release_succeeded=true`.
- **APK V48 PRE452 publicada no Drive** `NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk`, Drive ID **`1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C`**, https://drive.google.com/file/d/1xPJ0er2h5CJ6Syxx89hdkbIFrbjrfI0C/view, pacote `io.github.nfsmwrecomp`, `versionCode=48`, **47.104.233 bytes**, SHA256 **`c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35`**. Metadados Drive verificados, arquivo binário baixado e comparado byte a byte com APK do GitHub Actions: **IDÊNTICOS**, ZIP 872 entradas com CRC íntegro.
- **Certificado original de release** v2 SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; relatório `apk_validation.signed_certificate_sha256_match=true`, `signed_schemes_verified=true`. O certificado corresponde às versões V46 e V47. **Nunca recriar/substituir a chave nem usar debug para release**.
- **libmain.so ARM64 verificada** SHA256 `f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3`; callbacks dinâmicos confirmados no relatório um cada `NFSMW_PRE429_TRACE_ENTRY`, `NFSMW_PRE429_TRACE_LEVEL`, `NFSMW_PRE447_ROUTE`; marcadores `NFSMW_PRE429_ENTRY`, `NFSMW_PRE429_LEVEL`, `NFSMW_PRE447_ROUTE` e `NFSMW_PRE398_GLOBAL_NITRO_FULL` presentes. A instrumentação nova é **somente diagnóstica**, não altera o retorno zero, catálogo, compras, atributos ou física.
- **Estado de teste separado**: V48 **compilada, assinada, artefato/Drive/hash verificados**. Instalação da V48 no Galaxy S24 FE **ainda NÃO confirmada**, funcionamento real da V48 **não testado**, refill infinito em gameplay da V48 **não revalidado**, melhoria de FPS e correção da tunagem **NÃO comprovadas**. V46 PRE401 continua referência comprovada de Nitro infinito; V47 PRE434 permanece versão diagnóstica previamente testada. Save `MARCEK` e APKs anteriores preservados.
- **Teste seguro seguinte**: backup integral e verificado do save `MARCEK`; instalar V48 **como atualização** da V47, sem desinstalar, limpar dados ou alterar assinatura. Testar BMW M3 GTR (type 41) e Fiat Punto (type 74) em **duas sessões separadas**, navegando normalmente nas sete categorias de Desempenho **sem comprar** itens `Option title`, `20/20`, `999.999.999`. Guardar logs originais distintos; correlacionar `NFSMW_PRE447_ROUTE` com `NFSMW_PRE429_LEVEL` por categoria/contagem, avaliando `reason=1` (descritor não encontrado), `reason=2` (caminho de leitura de atributo) e `reason=3` (fallback). Não inferir que ausência de log signifique zero, não forçar 0->4 nem criar upgrades fictícios.
- **Relatório de verificação e protocolo**: GitHub `docs/PRE453_V48_PRE452_SIGNED_VERIFIED_TEST_PROTOCOL_20261108.md`, commit `f912e4f1c8426cc9001daee6df5fd420646657ba`. Preservar controle PG-9076, resolução 1920×1080, shaders/efeitos/física, proteções térmicas. Nenhum ganho FPS demonstrado.
- **Backup completo PRE454 antes deste adendo**: Drive `CONTEXTO_NFSMW_BACKUP_PRE454_V48_VALIDADA_20261108.md` ID `1h_jmsUo9yB3QGnY0Hn1TQJjTclHjYAVA`, comparado igual ao canônico antes da atualização. Aplicar apenas adendo com verificação integral de leitura e backup.
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
 if (b["id"]!=BACKUP or b["name"]!="CONTEXTO_NFSMW_BACKUP_PRE454_V48_VALIDADA_20261108.md" or
     PARENT not in b.get("parents",[])):raise ValueError("Backup metadata mismatch")
 original=read(d,MAIN);protected=read(d,BACKUP)
 if len(original)<650000 or original!=protected:raise ValueError("Source differs from verified backup")
 if MARKER.encode() in original:raise ValueError("Duplicate PRE454 marker")
 if b"PRE407" not in original or b"PRE408" not in original or b"PRE451_PRE448_NATIVE_PASS_V48_PENDENTE_20261108" not in original:raise ValueError("Missing prior V46/PRE451 context")
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
 print("PRE454_STATUS",r["status"],"ERROR",r.get("error_type","none"))
 print("PRE454_READBACK",r.get("readback",False))
 print("PRE454_BACKUP_UNCHANGED",r.get("backup_unchanged",False))
 print("PRE454_BYTES",r.get("new_bytes"))
 return 0 if r["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
