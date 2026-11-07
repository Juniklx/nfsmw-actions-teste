#!/usr/bin/env python3
"""PRE299: in-place canonical Google Drive CONTEXTO_NFSMW.md migration.
Backup is independently created/verified before source replacement. Only
content file is changed; existing Drive ID, filename and parent stay unchanged.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import sys
from datetime import datetime,timezone
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload,MediaIoBaseUpload

FILE_ID="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP_ID="1p39ZaVJgIFGyluT-08knNaaGzViZc9IA"
PARENT_ID="1Waam42x_suvBS18b4360HOaBqKxAncvy"
EXPECTED_ORIGINAL_BYTES=567437
MARKER="PRE299_CONTEXTO_PRINCIPAL_20261107"
OUT=Path("/tmp/nfsmw-pre299/PRE299_CONTEXT_PRIMARY_DRIVE_SYNC.json")
REPO=Path(__file__).resolve().parents[2]
ADENDO=REPO/"docs/CONTEXTO_NFSMW_ADENDO_PRE286_PRE287_20261107.md"
REPORTS=[
 "docs/PRE294_CACHE_AUDITORIA_V38_V39_20261107.md",
 "docs/PRE295_PRE297_CACHE_ROLANTE_E_TESTE_SINTETICO_20261107.md",
]
HEADER="""# CONTEXTO_NFSMW.md — REFERÊNCIA PRINCIPAL DO PROJETO

> **PRE299 — 2026-11-07 | CONTEXTO CANÔNICO**
> Este é o arquivo principal, persistente, do projeto NFSMW-Recompiled-Mobile.
> **Leia esta seção atual e o adendo consolidado PRE286–PRE298 antes do histórico antigo.**
> O restante deste documento preserva o histórico original; estados antigos (PRE197/V36, DIAG39 etc.)
> são marcos históricos e não se sobrepõem às evidências mais recentes.
> Referência permanente: Google Drive, CONTEXTO_NFSMW.md (mesmo ID e pasta).
> Atualizações futuras: adicionar aqui após gates, preservando backups.

## Situação atual verificada — 2026-11-07

- **Jogo:** Need for Speed: Most Wanted (2005), recompilação estática Xbox 360, Android.
- **Dispositivo:** Samsung Galaxy S24 FE. Controles touch e ponte iPega PG-9076 V3 previamente validados, mas cada nova release precisa de teste separado. Objetivo: gráficos completos, resolução interna 1920×1080, alvo máximo de 120 FPS (logs recentes registraram limite real de 60 FPS; não confundir objetivo e configuração observada). Nunca ignorar proteções térmicas.
- **APK mais recente publicada:** **V39 PRE293**, `versionCode 39`, pacote `io.github.nfsmwrecomp`; build e assinatura permanente validados no run GitHub `42378263558` em 2026-11-07. Arquivo privado Drive `NFSMW_V39_PRE293_BMW_MAIN_MENU_PASSIVE_TRACE.apk`, ID `10Hefzqcq1ejeCpxRcyH9cQ4f_qeZevC6`, tamanho 47.102.277 bytes, link https://drive.google.com/file/d/10Hefzqcq1ejeCpxRcyH9cQ4f_qeZevC6/view. Certificado SHA-256 esperado `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. **Preservar essa chave; nunca criar outra, pedir senhas ou usar assinatura debug.**
- **V39 em teste no aparelho:** o usuário informou que iria instalar e testar a nova APK; instalação, execução do menu e correção da BMW **não confirmadas** neste ponto. Aguardar `nfsmw.log`. Não confundir APK compilada/assinada/armazenada com instalação/teste.
- **Problema BMW M3 GTR:** na V38 o usuário entrou na oficina, viu apenas `Visual` e abriu a categoria; `Peças` e `Desempenho` ausentes. PRE290 verificou que as imagens executáveis descomprimidas PT-BR e PAL diferem em 10 bytes; isso não demonstra deslocamento geral de endereços. PRE291/292 validaram código e vínculo ARM64 do logger de menu PAL; V39 adicionou diagnóstico passivo do ponto candidato `sub_82578988` e preserva outro diagnóstico de `sub_82582F70`. Marcador esperado `NFSMW_PRE292_BMW_MENU`. **Não foi aplicado desbloqueio de categorias**, nem comprovado motivo do bloqueio.
- **Caches:** PRE294 confirmou que o PRE140 só cacheia `nativo/sdk/src`; arquivos C++ gerados do jogo foram explicitamente excluídos e a restauração de cache Gradle não evita rebuild completo do motor. PRE295 e PRE295C verificaram chaves rotativas do SDK em canário, com recuperação por chave explícita e fallback; PRE295B validou readback exato; PRE296 instalou launcher/política **experimental e desligada por padrão** para objetos ARM64 do jogo; PRE297 comprovou um cache hit e SHA idêntico apenas em fonte sintética. **Nenhum ganho real de minutos do jogo comprovado.**
- **PRE298:** teste em GitHub Actions `42383054863` de duas compilações PAL reais com cache de objetos **temporário no mesmo runner**, sem salvar objetos reais na nuvem. Status na última verificação para PRE299: **em execução**; consultar conclusão/log antes de promovê-lo a aprovado. https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/42383054863 .
- **Backups/saves:** preservar `MARCEK`, arquivos originais, APKs anteriores, patches e assinatura. Não aplicar patch novamente sem fingerprint/inspeção da fonte.
- **Próximo passo sem decisão do usuário:** verificar PRE298, auditar o relatório final (hash libmain.so, contagem de hits/tempo, erro), corrigir scripts quando necessário. Não ativar cache persistente do motor nem assinar nova release sem gates. Quando o usuário enviar log da V39, analisar primeiro `NFSMW_PRE292_BMW_MENU` e o menu da BMW.
- **Fontes canônicas:** este arquivo no Google Drive é o contexto principal; GitHub mantém scripts/workflows e adendo como histórico corroborativo. GitHub: https://github.com/Juniklx/nfsmw-actions-teste/blob/main/docs/CONTEXTO_NFSMW_ADENDO_PRE286_PRE287_20261107.md .

## Política para novos chats e atualização do contexto

1. Ler primeiro este cabeçalho e o adendo consolidado ao final; o histórico mais antigo contém hipóteses corrigidas e etapas ultrapassadas.
2. Se o usuário escrever `Executei` ou `Deu erro`, consultar o log **mais recente** no Google Drive/GitHub antes de sugerir outro patch.
3. Distinguir auditoria sintética, build C++/ARM64, APK assinada, APK instalada, funcionamento no S24 FE e ganho de FPS demonstrado.
4. Preferir GitHub Actions e scripts reproduzíveis (Google Colab quando necessário); preservar credenciais, logs privados, backups e patches.
5. Ao concluir etapa, atualizar **este CONTEXTO_NFSMW.md do Drive**, registrando run/commit, evidências e próximos passos; manter histórico. Não deixar apenas o adendo GitHub atualizado.

---

## HISTÓRICO ANTERIOR PRESERVADO (o estado abaixo não substitui a situação atual)

"""
ENDING="""\n\n---\n\n# ADENDO RECENTE CONSOLIDADO NO DOCUMENTO PRINCIPAL — PRE286 a PRE298

> Conteúdo sincronizado com o adendo verificado do GitHub em 2026-11-07.
> Em caso de divergência, conferir a data e os logs GitHub Actions/Drive.

"""
def sha(raw):return hashlib.sha256(raw).hexdigest()
def api():
    c=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    c.refresh(Request())
    return build("drive","v3",credentials=c,cache_discovery=False)
def raw_fetch(d,file_id):
    handle=io.BytesIO()
    downloader=MediaIoBaseDownload(handle,d.files().get_media(fileId=file_id,
               supportsAllDrives=True),chunksize=1024*1024)
    done=False
    while not done:
        _,done=downloader.next_chunk(num_retries=4)
    return handle.getvalue()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True);a=ap.parse_args()
    if not a.run_id.isdecimal():raise ValueError("invalid run ID")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE299_CONTEXT_PRIMARY_DRIVE_SYNC",
      "status":"FAILED","file_id":FILE_ID,"backup_id":BACKUP_ID,
      "changed_apk":False,"changed_save":False,"changed_signing":False}
    phase="INIT"
    try:
        phase="VERIFY_GITHUB_SOURCES"
        addendum=ADENDO.read_text(encoding="utf8")
        if len(addendum)<20000 or "PRE295C" not in addendum or "PRE298" not in addendum:
            raise ValueError("recent addendum missing expected evidence")
        reports=[]
        for n in REPORTS:
            p=REPO/n
            c=p.read_text(encoding="utf8")
            if len(c)<3000:raise ValueError("supporting report truncated")
            reports.append((n,c))
        phase="DRIVE_CONNECT"
        d=api()
        origmeta=d.files().get(fileId=FILE_ID,
               fields="id,name,size,mimeType,parents,md5Checksum",
               supportsAllDrives=True).execute()
        backmeta=d.files().get(fileId=BACKUP_ID,
               fields="id,name,size,mimeType,parents,md5Checksum",
               supportsAllDrives=True).execute()
        if origmeta.get("name")!="CONTEXTO_NFSMW.md" or origmeta.get("mimeType")!="text/markdown":
            raise ValueError("canonical file metadata mismatch")
        if PARENT_ID not in origmeta.get("parents",[]):
            raise ValueError("canonical folder mismatch")
        if backmeta.get("name")!="CONTEXTO_NFSMW_BACKUP_PRE299_20261107.md":
            raise ValueError("backup metadata mismatch")
        if PARENT_ID not in backmeta.get("parents",[]):
            raise ValueError("backup not in same folder")
        phase="VERIFY_BACKUP_AND_ORIGINAL"
        original=raw_fetch(d,FILE_ID)
        backup=raw_fetch(d,BACKUP_ID)
        if len(original)!=EXPECTED_ORIGINAL_BYTES or sha(original)!=sha(backup):
            raise ValueError("original size/backup digest mismatch; refuse replacement")
        if not original.startswith(b"# CONTEXTO DO PROJETO"):
            raise ValueError("unexpected original file heading")
        if MARKER.encode() in original:
            raise ValueError("canonical file already updated; no duplicate sync allowed")
        phase="STAGE_CANONICAL_CONTENT"
        source=original.decode("utf-8")
        report["original_sha256"]=sha(original)
        report["backup_sha256"]=sha(backup)
        output=(HEADER.replace("PRE299 —","PRE299_CONTEXTO_PRINCIPAL_20261107 —")
                +source+ENDING+addendum+"\n\n")
        output+="\n## Relatórios técnicos recentes incorporados à referência principal\n"
        for filename,content in reports:
            output+="\n### "+filename+"\n\n"+content+"\n"
        raw=output.encode("utf8")
        if len(raw)<=len(original) or output.count(MARKER)!=1:
            raise ValueError("canonical content consolidation failed")
        report["expected_new_sha256"]=sha(raw)
        report["expected_new_bytes"]=len(raw)
        phase="UPDATE_EXISTING_DRIVE_FILE"
        media=MediaIoBaseUpload(io.BytesIO(raw),mimetype="text/markdown",
                                 resumable=True,chunksize=1024*1024)
        request=d.files().update(fileId=FILE_ID,media_body=media,
                  fields="id,name,mimeType,size,parents,md5Checksum",
                  supportsAllDrives=True)
        reply=None
        while reply is None:
            _,reply=request.next_chunk(num_retries=4)
        if reply.get("id")!=FILE_ID or reply.get("name")!="CONTEXTO_NFSMW.md":
            raise ValueError("Drive update returned unexpected canonical ID/name")
        phase="READBACK"
        remote=raw_fetch(d,FILE_ID)
        if sha(remote)!=sha(raw) or remote!=raw:
            raise ValueError("Drive canonical readback mismatch")
        after=d.files().get(fileId=FILE_ID,
                fields="id,name,mimeType,size,parents,md5Checksum",
                supportsAllDrives=True).execute()
        if PARENT_ID not in after.get("parents",[]) or after.get("name")!="CONTEXTO_NFSMW.md":
            raise ValueError("Drive file moved/renamed unexpectedly")
        if raw_fetch(d,BACKUP_ID)!=backup:
            raise ValueError("Backup changed unexpectedly")
        report.update({"status":"PRIMARY_CONTEXT_SYNC_OK",
           "readback_verified":True,"same_original_id":True,
           "same_parent_folder":True,"backup_unchanged":True,
           "new_sha256":sha(remote),"new_bytes":len(remote),
           "recent_addendum_included":True,"two_cache_reports_included":True})
    except Exception as exc:
        report["error_type"]=type(exc).__name__
    report["phase"]=phase
    report["run_id"]=a.run_id
    report["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                   encoding="utf8")
    print("PRE299_STATUS",report["status"])
    print("PRE299_PHASE",phase)
    print("PRE299_BACKUP_UNCHANGED",report.get("backup_unchanged"))
    print("PRE299_SAME_ID",report.get("same_original_id"))
    print("PRE299_READBACK",report.get("readback_verified"))
    print("PRE299_BYTES",report.get("new_bytes"))
    print("PRE299_ERROR_TYPE",report.get("error_type"))
    return 0 if report["status"]=="PRIMARY_CONTEXT_SYNC_OK" else 1
if __name__=="__main__":sys.exit(main())
