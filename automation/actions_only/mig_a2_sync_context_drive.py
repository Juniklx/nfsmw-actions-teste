#!/usr/bin/env python3
"""MIG-A2: fail-closed Google Drive canonical-context append; GitHub Actions only."""
import argparse
import hashlib
import io
import os

CANON = "1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP = "1L514kj5KBhuPhg6Nn2EmnRTr8AZ8vmso"
EXPECTED_BYTES = 1390543
EXPECTED_SHA = "ff37c18eb6e4d87351c5bbca2e6bd9b1693a1a78845caee4c97b0b34d7ab6c9f"
MARKER = "## MIG_A2_V51_FORK_FINGERPRINTS_20261113"
APPEND = """## MIG_A2_V51_FORK_FINGERPRINTS_20261113 — comparação autenticada 13/11/2026

**GitHub Actions-only real, sem Kaggle.** O PR #1 da infraestrutura foi aprovado e integrado à main de Juniklx/NFSMW-Recompiled-Mobile no commit d4efb324a04d6c253447de59cd42eca5951b5f0f. O PR #2 https://github.com/Juniklx/NFSMW-Recompiled-Mobile/pull/2 com comparador, fingerprints PRE696 e relatório de auditoria também foi integrado, commit 13373b70642a19adf232cd9ba39fc7ecb2275dc8.

- Fonte de referência V51: ZIP da PRE696 autenticado, SHA-256 d06e06d4dda54d4b50924ec5a404ef396c91cef2166f7b9e055f4b5910154075, Drive ID 1JeOiiM0kei3dyLheQ2q5gNsNito5d4ku; CRC aprovado. Contém SHA/metadata de sete arquivos reconstruídos por receita PRE99+PRE431+PRE638+PRE648, NAO codigo-fonte completo nem prova de equivalencia binaria com APK V51.
- GitHub Action MIG-A2 https://github.com/Juniklx/NFSMW-Recompiled-Mobile/actions/runs/43361469978 e validacao PR 43361706718, ambos completed/success. Comparacao de sete arquivos reais do checkout do fork v0.5.7 (somente hashes e tamanhos): IDENTICAL=1; DIFFERENT=6; MISSING=0. Arquivo identico: nativo/app/src/nfsmw_ajustes_graficos.cpp. Arquivos divergentes: nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp; nativo/sdk/include/rex/ui/vulkan/presenter.h; nativo/app/src/nfsmw_nativo_sistema.cpp; nativo/app/src/nfsmw_nativo_destinos.cpp; android/app/src/main/java/io/github/nfsmwrecomp/MotorNativo.java; android/app/src/main/java/io/github/nfsmwrecomp/Ajustes.java.
- Relatorio JSON do run GitHub artifact 14008522077; ZIP 1.471 bytes, SHA-256 d81a79a9a08e78bde8da5c6b8e4dad35f9cac947eb7e87c27c0c8f7bb4a035ff, CRC aprovado. Copia privada no Drive https://drive.google.com/file/d/1DHAyIkPsCEYk6uopDPv6b9hFjJJN1_Zy/view , bytes/hash readback verificados. Documento no fork: docs/MIG_A2_V51_SOURCE_FINGERPRINTS_20261113.md.
- Um hash diferente NAO comprova a falta de patch da V51; pode ser mudanca posterior do upstream. Sem diff semantico nem fonte V51 restaurada neste novo gate; NENHUM patch da V51 copiado ao fork. O renderer V51 reconstruido em memoria (PRE648) tem hash especifico e nao deve ser confundido com identidade binaria do APK.
- Proximo gate MIG-A3: gerar diff de hunks limitado, privado, em workflow GitHub Actions autenticando PRE99+replay V51, comparando com fork v0.5.7; classificar separadamente melhorias upstream, patches locais e conflitos sem expor codigo do jogo em logs ou GitHub publico. Depois portar somente alteracoes seguras e licenciadas por PR pequenos.
- Sem APK V52, sem build arm64 completa, sem nova assinatura ou progresso FPS. V51 instalada: package io.github.nfsmwrecomp; versionCode=51; certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. O fork ainda contem versionCode=16 e configuracao release de assinatura debug: nao usar para atualizar. Manter 1920x1080, alvo 120 FPS, qualidade total, shaders, efeitos, fisica, saves, touch, PG-9076 e protecao termica.

**STATUS:** MIG_A2_SOURCE_HASH_COMPARISON_PASS; SAME=1/7; DIFF=6/7; PR1_MERGED; PR2_MERGED; MIG_A3_SEMANTIC_RECONCILIATION_PENDING; NO_V52; NO_FPS_GAIN.
"""

def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def compose(b: bytes) -> bytes:
    if len(b) != EXPECTED_BYTES or digest(b) != EXPECTED_SHA:
        raise ValueError("MIG_A2_CANONICAL_CHANGED_ABORT")
    s = b.decode("utf-8")
    if not s.startswith("# CONTEXTO_NFSMW.md — FLUXO ATUAL GITHUB ACTIONS ONLY"):
        raise ValueError("MIG_A2_HEADER_MISMATCH")
    if s.count("## MIG_A1_ACTIONS_ONLY_MIGRATED_20261113") != 1:
        raise ValueError("MIG_A2_PRIOR_GATE_MISSING")
    if MARKER in s:
        raise ValueError("MIG_A2_ALREADY_WRITTEN")
    return (s.rstrip("\n") + "\n\n---\n\n" + APPEND).encode("utf-8")

def read(api, fid):
    b = api.files().get_media(fileId=fid, supportsAllDrives=True).execute(num_retries=4)
    if not isinstance(b, bytes):
        raise ValueError("MIG_A2_MEDIA_NOT_BYTES")
    return b

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--apply", action="store_true")
    opts = p.parse_args()
    if opts.self_test:
        assert len(EXPECTED_SHA)==64 and EXPECTED_BYTES>1_000_000
        assert APPEND.startswith(MARKER) and "MIG_A3" in APPEND
        print("MIG_A2_CONTEXT_LOCAL_CHECK=PASS")
        return
    if not opts.apply:
        p.error("Use --apply")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    keys = ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    if not all(os.environ.get(x) for x in keys):
        raise ValueError("MIG_A2_DRIVE_OAUTH_NOT_CONFIGURED")
    creds = Credentials(
        token=None, refresh_token=os.environ[keys[0]],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ[keys[1]], client_secret=os.environ[keys[2]])
    creds.refresh(Request())
    api=build("drive","v3",credentials=creds,cache_discovery=False)
    old=read(api,CANON)
    immutable_backup=read(api,BACKUP)
    if old!=immutable_backup or len(old)!=EXPECTED_BYTES or digest(old)!=EXPECTED_SHA:
        raise ValueError("MIG_A2_BACKUP_DRIFT_ABORT")
    new=compose(old)
    upload=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=False)
    result=api.files().update(fileId=CANON,media_body=upload,fields="id,size",supportsAllDrives=True).execute(num_retries=4)
    if result.get("id")!=CANON or int(result.get("size",-1))!=len(new):
        raise ValueError("MIG_A2_DRIVE_UPDATE_METADATA_ERROR")
    if read(api,CANON)!=new or read(api,BACKUP)!=old:
        raise ValueError("MIG_A2_READBACK_ERROR")
    print("MIG_A2_CANONICAL_CONTEXT_UPDATED_AND_READBACK_VERIFIED=TRUE")
    print("MIG_A2_NEW_BYTES="+str(len(new)))
    print("MIG_A2_NEW_SHA256="+digest(new))
    print("MIG_A2_APK_MODIFIED=FALSE")
if __name__ == "__main__":
    main()
