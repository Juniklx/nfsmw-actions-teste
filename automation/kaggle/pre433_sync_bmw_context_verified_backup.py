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
BACKUP="1-XN2wEYtIz2AKhQ4ylzomgErmh0pB-3c"
PARENT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
MARKER="PRE433_BMW_AUDITORIAS_409_431_20261108"
OUT=Path("/tmp/nfsmw-pre433/report.json")
ENTRY="""

## PRE433_BMW_AUDITORIAS_409_431_20261108 — Estado BMW após auditorias (8 nov 2026)

- Referência V46 PRE401 permanece a APK comprovadamente funcional com Nitro infinito global no Galaxy S24 FE (PRE407). Pacote io.github.nfsmwrecomp, versionCode 46, APK SHA256 ac3676127d922b3c981aac6fffb87690c64bb9c0139fb983bd3ad8e017459eb7 e certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Resolução interna 1920x1080 preservada; 120 FPS não comprovados. C3 texturas permanece problema separado. Guardar backups, save MARCEK e V46.
- BMW M3 GTR de Razor no save MARCEK: bypass de menu PRE305/V40 tornou acessíveis Peças/Desempenho, mas Transmissão apresentou Option title, 20/20 e 999.999.999 sem prova de pacotes válidos. Não comprar opções inválidas nem fabricar níveis; Fiat Punto é referência comparativa.
- PRE409–421: análise estática PAL da lista construída por sub_8256F818 (nfsmw_recomp.57.cpp, 230 linhas), chamada pela configuração sub_82582F70 (nfsmw_recomp.11.cpp, 1231 linhas). A lista é percorrida pelo chamador, mas seus níveis reais para BMW não foram medidos. PRE420 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42448680708 ; PRE421 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42449552113.
- PRE422–423: busca de nomes de GetPerformancePartsList não resolveu símbolo de alto nível; PRE423 localizou funções por endereço. Runs 42450058794 e 42450444929. PRE424 corrigida run 42450782110 localizou sub_82581BD8 chamando sub_82582F70; primeira tentativa 42450728963 foi PARTIAL por regex.
- PRE425 run 42451057300 mostrou duas chamadas a sub_823E5988 pelo montador de lista, com endereço-base global. Essa função grava contadores de referência guest; nunca invocá-la artificialmente só para obter níveis.
- PRE426 run 42451276573 aprovou em memória prévia passiva limitada de registro de tipo de categoria e contagem candidata, sem APK ou níveis reais.
- PRE427 run 42451519154 confirmou mesmo endereço-base global em sub_8256B440 (entrada tuning) e sub_8256F818 (lista). sub_8256CB60 devolve 3 ou 4 conforme categoria 0–6; não identifica modelo. PRE428 run 42451675734 analisou auxiliares sub_8214B858 e sub_8214EDA8 com acessos a atributos e referências.
- PRE429 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42451836847, AUDIT_OK e mock host PASS_114_EVENTS: dois marcadores passivos, reversíveis, flag NFSMW_PRE429_TUNING_LEVEL_TRACE_ENABLE desligada por padrão. Um captura endereço base e ponteiros guest opacos do carro/pvehicle na entrada da personalização; outro registra categoria 0–6 e contagem candidata após chamada normal já existente. Nenhum modelo BMW/Fiat ou valor real foi aferido no aparelho.
- PRE430 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42452283511: AUDIT_OK, CMake e compilação libmain.so ARM64 aprovada, ELF ARM64 e um callback definido. Base de source V37, não a cadeia completa V46; nem ambos os callbacks foram comprovados pela auditoria. Sem APK/assinatura.
- PRE431 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42465096292: AUDIT_OK. Reproduziu em árvore descartável a sequência de patches de fonte da V46, PRE317, PRE337, PRE349, PRE389, PRE398 e PRE364, com bypass localizado do menu modelo 41. Confirmou cinco stores Nitro 1.0 preservados e dois marcadores PRE429 reversíveis em fontes com hashes conferidos; módulo CMake registrado. NÃO compilou a biblioteca, APK nem assinatura; não provou equivalência binária com V46.
- PRE432 run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42465261331 foi acionada para compilar/libmain.so com fonte V46 e conferir flags em ambos shards e duas definições dos callbacks; RESULTADO AINDA PENDENTE na redação deste registro. Conferir os logs atuais antes de afirmar sucesso.
- Próximo passo: se PRE432 validar ambos callbacks, planejar diagnóstico V47 somente passivo para comparar BMW e Fiat Punto em sessões separadas e com save MARCEK protegido. Não mexer em física, preço, compra, C3, controle, qualidade, limites térmicos ou Nitro. Qualquer APK nova exige versionCode >46 e certificado permanente idêntico, nunca debug ou chave recriada. Este adendo no contexto não cria APK.
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
 if (b["id"]!=BACKUP or b["name"]!="CONTEXTO_NFSMW_BACKUP_PRE433_20261108.md" or
     PARENT not in b.get("parents",[])):raise ValueError("Backup metadata mismatch")
 original=read(d,MAIN);protected=read(d,BACKUP)
 if len(original)<650000 or original!=protected:raise ValueError("Source differs from verified backup")
 if MARKER.encode() in original:raise ValueError("Duplicate PRE433 marker")
 if b"PRE407" not in original or b"PRE408" not in original:raise ValueError("Missing prior V46 context")
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
 print("PRE433_STATUS",r["status"],"ERROR",r.get("error_type","none"))
 print("PRE433_READBACK",r.get("readback",False))
 print("PRE433_BACKUP_UNCHANGED",r.get("backup_unchanged",False))
 print("PRE433_BYTES",r.get("new_bytes"))
 return 0 if r["status"]=="SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
