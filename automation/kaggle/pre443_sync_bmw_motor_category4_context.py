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
BACKUP="1V180yUWKxdKLSrzvktChx8h5BXskmikS"
PARENT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
MARKER="PRE443_MOTOR_BMW_CATEGORIA4_PAL_20261108"
OUT=Path("/tmp/nfsmw-pre443/report.json")
ENTRY="""

## PRE443_MOTOR_BMW_CATEGORIA4_PAL_20261108 — mapeamento PAL e diagnóstico de retorno zero (8 nov 2026)

- **Base experimental**: V47 PRE434 no Galaxy S24 FE, logs individuais BMW M3 GTR (`type=41`) e Fiat Punto (`type=74`), documentados e sincronizados pela PRE438/PRE439. Na consulta de tipo interno 4, `candidate_count=0` para BMW e `candidate_count=4` para Punto. Não extrapolar para outros tipos.
- **PRE440 read-only**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42489165527, `AUDIT_OK`. Fontes PAL PRE99 com SHA-256 autenticados. O chamador `sub_82582F70` passa a categoria via `r24` para `sub_8256F818`; esta chama `sub_823E5988` e, se o retorno é <=0, desvia antes do laço de alocação das opções da lista. Logo, o zero observado da BMW interrompe essa criação normal de opções para a consulta específica.
- **PRE441 + PRE441B read-only**: https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42489366761 e https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42489540474, ambos `AUDIT_OK`. Switch PAL do chamador calcula `[screen+324] - 513`, casos 0..6, e define `r24` nesta ordem: menu 513 (Motor) -> 4; 514 (Transmissão) -> 3; 515 (Suspensão) -> 2; 516 (Nitro) -> 6; 517 (Pneus) -> 0; 518 (Freios) -> 1; 519 (Indução forçada) -> 5. Essa correspondência é verificada na PAL e consistente com a reconstrução pública `dbalatoni13/nfsmw`, `PhysicsUpgrades.hpp` e `CarCustomize.cpp`. **O tipo interno 4 corresponde a Motor**, mas também é o valor inicial/default de `r24`; o log não contém `[screen+324]`, logo não prova por si só qual submenu visual foi aberto.
- **Possíveis causas do zero PAL**: `sub_823E5988` percorre descritores de atributo por categoria, tem retorno zero se categoria não encontrada e outros caminhos que retornam zero ao resolver atributo; chama `sub_8214B858` e `sub_8214EDA8`. A `sub_8214B858` lê um campo do descritor de contexto, compara com zero e pode retornar indicador falso. A PRE429 observou apenas o resultado total, **não qual ramo produziu o zero da BMW**. O `pvehicle=0` do evento de entrada foi observado também no Punto e não prova permanência do ponteiro nulo ou causa exclusiva BMW.
- **Sem alteração de lógica**: nenhuma build APK nova, assinatura, simulação de upgrades, compra, edição de save, alteração de Nitro/C3/física ou novo acesso a memória guest. `sub_823E5988` não deve ser chamada artificialmente (há alterações de contador de referência guest). Não converter 0 para 4, não criar placeholders e não comprar opções `Option title`, `20/20`, `999.999.999`.
- **Relatório técnico GitHub**: `docs/PRE442_V47_BMW_MOTOR_CATEGORIA4_CAUSAS_ZERO_20261108.md`, commit `f0af2019fbc0b12b3382cfa84bef8867f89ccfbf`. V46 PRE401 mantém Nitro infinito global realmente testado; V47 permanece diagnóstica, com Nitro ainda não retestado em gameplay nesta versão.
- **Próximo passo**: com a V47 já instalada, navegar normalmente nas demais seis categorias para BMW/Punto, sem compra, com sessões e logs separados; categoria sem log não é categoria sem upgrade. Investigar estática/passivamente o ramo específico que produz zero apenas se essa coleta não resolver a questão. Preservar `MARCEK`, APKs anteriores, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, resolução 1920x1080, shaders/efeitos/física, controle PG-9076 e limites térmicos; não declarar aumento de FPS.
- **Backup de contexto PRE443**: `CONTEXTO_NFSMW_BACKUP_PRE443_MOTOR_BMW_PAL_20261108.md` no Drive, ID `1V180yUWKxdKLSrzvktChx8h5BXskmikS`, cópia integral já conferida idêntica antes da alteração. Verificar leitura após o adendo e não apagar histórico.
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
 if (b["id"]!=BACKUP or b["name"]!="CONTEXTO_NFSMW_BACKUP_PRE443_MOTOR_BMW_PAL_20261108.md" or
     PARENT not in b.get("parents",[])):raise ValueError("Backup metadata mismatch")
 original=read(d,MAIN);protected=read(d,BACKUP)
 if len(original)<650000 or original!=protected:raise ValueError("Source differs from verified backup")
 if MARKER.encode() in original:raise ValueError("Duplicate PRE439 marker")
 if b"PRE407" not in original or b"PRE408" not in original or b"PRE439_V47_LOGS_BMW_PUNTO_20261108" not in original:raise ValueError("Missing prior V46/PRE437 context")
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
 print("PRE443_STATUS",r["status"],"ERROR",r.get("error_type","none"))
 print("PRE443_READBACK",r.get("readback",False))
 print("PRE443_BACKUP_UNCHANGED",r.get("backup_unchanged",False))
 print("PRE443_BYTES",r.get("new_bytes"))
 return 0 if r["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
