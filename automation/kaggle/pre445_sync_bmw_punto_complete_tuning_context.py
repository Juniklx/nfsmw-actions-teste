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
BACKUP="1Y3GtOvYAMsEY2Ui1dkz7cK3Sr_xcmjkL"
PARENT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
MARKER="PRE445_V47_BMW_PUNTO_7_CATEGORIAS_20261108"
OUT=Path("/tmp/nfsmw-pre445/report.json")
ENTRY="""

## PRE445_V47_BMW_PUNTO_7_CATEGORIAS_20261108 — testes reais de tunagem completa (08/11/2026)

- **Fonte privada lida integralmente:** `nfsmw-bmw_tunningcompleta.log` (323.448 bytes, 1.530 linhas, SHA256 `53f47d001306b4af18c0860eebe1f21b02b97036e496a1e575bdcbf169cd4779`) e `nfsmw-punto_tunningcompleta.log` (338.773 bytes, 1.531 linhas, SHA256 `c7f84341264605dd9c1065ccca9aa1d6471533f835fe8a2e7f0e37fc4f2519ca`). Arquivos enviados pelo usuário, sessões separadas, análise local sem modificação de APK/save, **logs brutos não publicados no GitHub**. Marcadores `NFSMW_PRE292_BMW_MENU`: BMW `type=41` e Fiat Punto `type=74`. Um `NFSMW_PRE429_ENTRY` e sete `NFSMW_PRE429_LEVEL` em cada sessão, todos com `manager=0x82C5D9E8`.
- **Sete contagens candidatas reais**, conforme mapeamento PAL PRE441B, na ordem registrada pelo jogo: Motor `type=4` -> BMW **0**, Punto **4**; Transmissão `3` -> **0/4**; Suspensão `2` -> **0/3**; Nitro `6` -> **3/3**; Pneus `0` -> **0/3**; Freios `1` -> **0/4**; Indução forçada `5` -> **0/3** (sempre BMW/Punto). Todas as sete categorias foram **observadas**, não estimadas. `candidate_count` não equivale automaticamente a número de peças instaláveis, catálogo válido ou nível real de compra.
- **Conclusão verificada:** BMW retorna zero em **seis de sete** consultas do caminho normal do catálogo, enquanto Nitro é a única consulta com retorno positivo, **3**, igual ao Punto. PRE440 mostrou que contagem <=0 faz `sub_8256F818` saltar a criação normal dos itens da lista. O **ramo exato** de `sub_823E5988` responsável pelo zero da BMW ainda não foi identificado; causas plausíveis são descritor de categoria ausente, lookup de atributo sem resultado ou atributo configurado com valor zero. Não afirmar que a BMW não pode ser melhorada por outro caminho, nem forçar resultados 0->4, nem instalar opção inválida.
- **Nitro PRE398 no log BMW:** `[NFSMW_PRE398_GLOBAL_NITRO_FULL] active=1 affects_all_objects=1 full_bits=0x3F800000` surgiu **uma vez**. Isso atesta execução do trecho instrumentado na sessão da BMW, **não** prova Nitro infinito em toda corrida nesta versão. O marcador **não apareceu** no log do Punto; ausência não prova falha de Nitro.
- **Outros achados:** ambos os eventos PRE429_ENTRY têm `pvehicle=0x00000000`; não prova que permaneça nulo ou seja a causa dos zeros. Ambos contêm uma ocorrência de erro PRE194 C3 com `copia_duplicada=true`, thread de links de texturas desativada como fallback. Não apareceram os textos literais `FATAL EXCEPTION` nem `SIGSEGV`; estabilidade geral não comprovada. Ambos reportam **1920x1080 internos e limite configurado de 60 FPS**, sem ganho de FPS demonstrado.
- **Relatório sem logs privados:** GitHub `docs/PRE444_V47_LOGS_TUNING_SET_CATEGORIAS_20261108.md`, commit `d69b3616331a875a4cf3c93988e78692f3247f3f`. Arquivos locais para download: `NFSMW_PRE444_BMW_PUNTO_7_CATEGORIAS_20261108.md` e `.json`.
- **Próximo passo:** preservar V47 diagnóstica, V46 PRE401 com Nitro global já validado em gameplay, save `MARCEK`, Fiat Punto e BMW. Estudar o motivo do zero na `sub_823E5988` com auditoria somente leitura e, se necessário, projetar uma prévia reversível de instrumentação de saídas, sem chamadas guest extras. **Não criar V48 antes de provar necessidade e compatibilidade**, não substituir assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, nem alterar shaders, efeitos, física, controle PG-9076, resolução ou limites térmicos. Não comprar entradas `Option title`, `20/20`, `999.999.999`.
- **Backup canônico completo antes deste adendo:** Drive `CONTEXTO_NFSMW_BACKUP_PRE445_7_CATEGORIAS_BMW_PUNTO_20261108.md`, ID `1Y3GtOvYAMsEY2Ui1dkz7cK3Sr_xcmjkL`; conferido byte a byte igual ao contexto atual antes de gravar. A atualização deve ser append-only, com readback integral e preservação do backup.
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
 if (b["id"]!=BACKUP or b["name"]!="CONTEXTO_NFSMW_BACKUP_PRE445_7_CATEGORIAS_BMW_PUNTO_20261108.md" or
     PARENT not in b.get("parents",[])):raise ValueError("Backup metadata mismatch")
 original=read(d,MAIN);protected=read(d,BACKUP)
 if len(original)<650000 or original!=protected:raise ValueError("Source differs from verified backup")
 if MARKER.encode() in original:raise ValueError("Duplicate PRE445 marker")
 if b"PRE407" not in original or b"PRE408" not in original or b"PRE443_MOTOR_BMW_CATEGORIA4_PAL_20261108" not in original:raise ValueError("Missing prior V46/PRE443 context")
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
 print("PRE445_STATUS",r["status"],"ERROR",r.get("error_type","none"))
 print("PRE445_READBACK",r.get("readback",False))
 print("PRE445_BACKUP_UNCHANGED",r.get("backup_unchanged",False))
 print("PRE445_BYTES",r.get("new_bytes"))
 return 0 if r["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
