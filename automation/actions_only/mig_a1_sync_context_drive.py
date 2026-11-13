#!/usr/bin/env python3
"""Fail-closed Drive context synchronization for Actions-only migration MIG-A1."""
import argparse, hashlib, io, os
OLD_HASH="30dad0c331e3492ed06e895043356d152a885651adfc98befc55b2d435bc1d2b"
OLD_BYTES=1387355
CANON="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP="11yd6ryDia3eZX6gMx6EZf4wbrWu5PTlC"
MARK="MIG_A1_ACTIONS_ONLY_MIGRATED_20261113"

HEAD="""# CONTEXTO_NFSMW.md — FLUXO ATUAL GITHUB ACTIONS ONLY (13/11/2026)

> ATUALIZAÇÃO OPERACIONAL PRIORITÁRIA: por decisão do usuário, usar somente GitHub Actions, sem iniciar novos notebooks Kaggle. Código alterado diretamente no fork Juniklx/NFSMW-Recompiled-Mobile, com PRs e testes. O Google Drive continua sendo repositório privado de APKs, backups, logs e contexto. Workflows Kaggle e instruções históricas abaixo estão DESATIVADOS COMO PLANO OPERACIONAL. O fork v0.5.7 ainda não contém automaticamente os patches da V51 assinada. O novo Actions passou apenas preflight de fonte: nenhuma build ARM64 completa e nenhuma APK V52 foram validadas. Ler adendo MIG-A1 ao final do arquivo.

---

"""

TAIL="""## MIG_A1_ACTIONS_ONLY_MIGRATED_20261113 — Migração validada em 13/11/2026

Decisão: GitHub Actions será o único executor de CI e builds futuros; não disparar mais notebooks Kaggle. Preservar os workflows, logs e notebooks antigos como histórico no repositório Juniklx/nfsmw-actions-teste.

- Fork público diretamente editável: https://github.com/Juniklx/NFSMW-Recompiled-Mobile ; main idêntico ao upstream victorgbd/NFSMW-Recompiled-Mobile no commit 3ac2fb698576d8889ade19660c38d0fd25f2c5a5, v0.5.7. Não contém automaticamente os patches exclusivos da APK V51.
- Branch criada: ci/actions-only-migration. PR rascunho: https://github.com/Juniklx/NFSMW-Recompiled-Mobile/pull/1 . Contém exclusivamente o novo workflow .github/workflows/nfsmw-actions-only-preflight.yml, script tools/ci/actions_only_preflight.py e documento docs/CI_ACTIONS_ONLY_NFSMW.md. Sem patches de renderização, Java, controle ou assinatura.
- GitHub Actions do fork, sem Kaggle: runs 43359748696 e 43359786157, ambos success. Preflight SOURCE_ONLY, ok=true, tracked_files=2799, pacote io.github.nfsmwrecomp; sintaxe Python e shell verificada. Nenhuma compilação ARM64 do jogo ou teste S24 FE foi feito.
- Impedimento deliberado de release: o Gradle da v0.5.7 ainda tem versionCode 16 e assinatura debug; a V51 instalada usa versionCode 51 e certificado SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. É proibido publicar a build upstream como atualização da V51; futuras versões devem usar a MESMA chave permanente e versionCode superior a 51, sem expor chave, senha ou materiais privados.
- Viabilidade: runner Ubuntu público padrão 4 vCPU, 16 GB RAM, 14 GB SSD, limite de 6 h por job. ISO USA de ~7,8 GB e ZIP PAL ~5,6 GB mais SDK/NDK e objetos podem exceder disco. Provar orçamento e restauração autenticada de dados privados antes de implementar build completa; sem incluir ISO, XEX, fontes derivadas, APK assinada privada ou P12 em repositório/artifacts públicos.
- Próximo passo: verificar PR #1, auditar diffs entre a receita de fonte V51 autenticada e v0.5.7, migrar patches por PRs isolados, e construir no Actions após gates de recursos/segurança. Preservar a V51, 1920x1080, 120 FPS alvo, shaders, efeitos, física, touch, controle PG-9076, saves e limites térmicos. Nenhuma melhoria FPS foi medida com o novo CI.

STATUS: MIG_A1_SOURCE_PREFLIGHT_SUCCESS; FULL_BUILD_NOT_VERIFIED; V51_SOURCE_NOT_MERGED; NO_V52; NO_APK; NO_FPS_GAIN.
"""
def digest(x):return hashlib.sha256(x).hexdigest()
def compose(blob):
 if len(blob)!=OLD_BYTES or digest(blob)!=OLD_HASH:raise ValueError("MIG_A1_CANON_DRIFT")
 s=blob.decode("utf-8")
 if not s.startswith("# CONTEXTO_NFSMW.md — AMBIENTE ATUAL KAGGLE + GITHUB ACTIONS"):raise ValueError("MIG_A1_OLD_HEADER_DRIFT")
 if MARK in s or s.count("## ATUALIZAÇÃO VERIFICADA — UPSTREAM V0.5.7")!=1:raise ValueError("MIG_A1_PREEXISTING_OR_MISSING")
 out=(HEAD+s.rstrip("\n")+"\n\n---\n\n"+TAIL).encode("utf-8")
 if out.count(MARK.encode())!=1:raise ValueError("MIG_A1_MARKER_COUNT")
 return out
def read(api, file_id):
 b=api.files().get_media(fileId=file_id,supportsAllDrives=True).execute(num_retries=4)
 if not isinstance(b,bytes):raise ValueError("MIG_A1_NOT_BYTES")
 return b
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--self-test",action="store_true")
 p.add_argument("--apply",action="store_true")
 a=p.parse_args()
 if a.self_test:
  assert len(OLD_HASH)==64 and OLD_BYTES>1000000 and MARK in TAIL and HEAD.startswith("# CONTEXTO_NFSMW")
  print("MIG_A1_LOCAL_PREFLIGHT_PASS=TRUE");return
 if not a.apply:p.error("use --apply")
 from google.oauth2.credentials import Credentials
 from google.auth.transport.requests import Request
 from googleapiclient.discovery import build
 from googleapiclient.http import MediaIoBaseUpload
 keys=["GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET"]
 if any(not os.getenv(k) for k in keys):raise ValueError("MIG_A1_AUTH_MISSING")
 credentials=Credentials(token=None,refresh_token=os.environ[keys[0]],token_uri="https://oauth2.googleapis.com/token",client_id=os.environ[keys[1]],client_secret=os.environ[keys[2]])
 credentials.refresh(Request())
 api=build("drive","v3",credentials=credentials,cache_discovery=False)
 old=read(api,CANON);backup=read(api,BACKUP)
 if old!=backup or len(old)!=OLD_BYTES or digest(old)!=OLD_HASH:raise ValueError("MIG_A1_BACKUP_FAIL_CLOSED")
 new=compose(old)
 response=api.files().update(fileId=CANON,media_body=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=False),fields="id,size",supportsAllDrives=True).execute(num_retries=4)
 if response.get("id")!=CANON or int(response.get("size",0))!=len(new):raise ValueError("MIG_A1_METADATA_MISMATCH")
 if read(api,CANON)!=new or read(api,BACKUP)!=old:raise ValueError("MIG_A1_READBACK_MISMATCH")
 print("MIG_A1_CANONICAL_CONTEXT_UPDATED_AND_READBACK_PASS=TRUE")
 print("MIG_A1_NEW_BYTES="+str(len(new)))
 print("MIG_A1_NEW_SHA256="+digest(new))
 print("MIG_A1_NO_APK_SOURCE_SIGNING_MODIFICATIONS=TRUE")
if __name__=="__main__":main()
