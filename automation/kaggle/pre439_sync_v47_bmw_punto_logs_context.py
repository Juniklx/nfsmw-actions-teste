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
BACKUP="1wdmffYhtBpgFrDrKnS7thbO4JbMfADSn"
PARENT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
MARKER="PRE439_V47_LOGS_BMW_PUNTO_20261108"
OUT=Path("/tmp/nfsmw-pre439/report.json")
ENTRY="""

## PRE439_V47_LOGS_BMW_PUNTO_20261108 — V47: BMW versus Punto, logs de aparelho (08/11/2026)

- **Fonte real**: arquivos `nfsmw-punto.log` e `nfsmw-bmw.log`, enviados pelo usuário nesta conversa. Ambos lidos integralmente localmente, sem qualquer alteração de APK/save. **Não publicar os logs brutos em GitHub.** Relatório sem dados completos: `docs/PRE438_V47_LOGS_REAIS_BMW_VS_PUNTO_20261108.md`, commit `1e225b118fcc02c6ad3866eddf01544ecc83f4e7`.
- **Punto:** 376.962 bytes, 1.609 linhas; SHA256 `8a1a319b264c05c42596e03ae45537b2c6a4756894ef53c377aa2f20ff5b81c9`. PRE429 ENTRY às 11:01:51.248 com `manager=0x82C5D9E8`, `tuning_car=0xAD68FA50`, `pvehicle=0x00000000`. PRE292 MENU às 11:01:51.249 `type=74`. PRE429 LEVEL às 11:01:58.194: `category=4 candidate_count=4`.
- **BMW M3 GTR:** 395.130 bytes, 1.719 linhas; SHA256 `4d3f04e4b0fdb13a7328789de411fdf3b90db1312cab1ee2c028faef082e5323`. PRE429 ENTRY às 11:03:42.555 com `manager=0x82C5D9E8`, `tuning_car=0xAD68FA64`, `pvehicle=0x00000000`. PRE292 MENU às 11:03:42.556 `type=41`. PRE429 LEVEL às 11:03:48.224: `category=4 candidate_count=0`; segundo evento MENU às 11:03:59.175.
- **Comparação verificada:** a mesma categoria numérica 4 retornou uma contagem **candidata 4 no Punto e 0 na BMW** em chamadas reais. Identidade dos carros corroborada por logs PRE292 `type=74/41` e pelo contexto de sessão do usuário. Endereço-base `manager=0x82C5D9E8` idêntico. A hipótese de lista vazia para BMW nessa categoria ganhou suporte experimental, **mas não é prova formal de GetMaxLevel nem do total de pacotes compráveis**. Não extrapolar para demais categorias, não converter zero para quatro, nem criar peças fictícias. Os dois `pvehicle` na entrada foram nulos, portanto não são causa exclusiva da BMW comprovada.
- **Categoria 4:** na reconstrução pública `dbalatoni13/nfsmw` (`PhysicsUpgrades.hpp`) enum `PUT_ENGINE=4`, sugerindo Motor. A equivalência entre o argumento `category=4` da rotina PAL e o enum público **ainda não foi comprovada**. Não identificar sem prova como Motor, Transmissão, Nitro ou outro submenu na build do aparelho.
- **Outras observações:** cada log tem um aviso PRE194 C3 (`copia_duplicada=true`) e a thread de ligações de texturas desativada; nenhum `FATAL EXCEPTION`/`SIGSEGV` textual foi encontrado. Nenhum evento PRE398 Nitro global apareceu nos menus: o Nitro infinito na V47 **não foi retestado em gameplay**. Resolução interna 1920x1080 e cap 60 FPS reportados em ambos; sem ganho de FPS comprovado.
- **Estado da V47:** executar a APK com marcadores PRE429 no Galaxy S24 FE é demonstrado pelos registros de jogo, mas os logs não registram o versionCode do pacote; não afirmar teste de todas funcionalidades, estabilidade global ou correção do catálogo. V46 continua baseline real Nitro global. Preservar save MARCEK, BMW/Punto/Junkman, APKs anteriores, shaders, física e limites térmicos.
- **Próximo passo:** analisar estaticamente como a categoria 4 é mapeada na PAL e como a consulta produz zero para a BMW. Se apropriado, navegar apenas normalmente pelas demais categorias e obter dois novos logs separados, sem compras inválidas, para evitar conclusões sobre sete categorias com uma única amostra. Não invocar artificialmente `sub_823E5988` nem aplicar patches sem confirmar o estado.
- **Backup PRE439** antes deste adendo: `CONTEXTO_NFSMW_BACKUP_PRE439_LOGS_BMW_PUNTO_20261108.md` (Drive ID `1wdmffYhtBpgFrDrKnS7thbO4JbMfADSn`) criado e conferido byte a byte com o contexto canônico, exigir igual confirmação e pós-gravação.

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
 if (b["id"]!=BACKUP or b["name"]!="CONTEXTO_NFSMW_BACKUP_PRE439_LOGS_BMW_PUNTO_20261108.md" or
     PARENT not in b.get("parents",[])):raise ValueError("Backup metadata mismatch")
 original=read(d,MAIN);protected=read(d,BACKUP)
 if len(original)<650000 or original!=protected:raise ValueError("Source differs from verified backup")
 if MARKER.encode() in original:raise ValueError("Duplicate PRE439 marker")
 if b"PRE407" not in original or b"PRE408" not in original or b"PRE437_V47_PRE434_ASSINADA_E_VERIFICADA_20261108" not in original:raise ValueError("Missing prior V46/PRE437 context")
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
 print("PRE439_STATUS",r["status"],"ERROR",r.get("error_type","none"))
 print("PRE439_READBACK",r.get("readback",False))
 print("PRE439_BACKUP_UNCHANGED",r.get("backup_unchanged",False))
 print("PRE439_BYTES",r.get("new_bytes"))
 return 0 if r["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
