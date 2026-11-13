#!/usr/bin/env python3
"""MIG-A3: fail-closed Google Drive canonical-context append; GitHub Actions only."""
import argparse
import hashlib
import io
import os

CANON = "1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP = "1plQ6GvVpkbW5qTH8Rv-qZW744P_7wh0y"
EXPECTED_BYTES = 1393672
EXPECTED_SHA = "4f4a8c7c2de75315bdb1f568e1037291a8e8aa46c8d040b2dbb4b1a074b1cbf9"
MARKER = "## MIG_A3_V51_FORK_THREE_WAY_20261113"
APPEND = """## MIG_A3_V51_FORK_THREE_WAY_20261113 — três vias PRE99 × V51 × fork (13/11/2026)

**Gate real concluído com sucesso, somente GitHub Actions, sem Kaggle.** Run https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43362701434 , job 131679714249, completed/success. Código auditor automation/actions_only/mig_a3_v51_three_way_audit.py; workflow .github/workflows/nfsmw-mig-a3-v51-fork-three-way.yml, com PRE99 Drive autenticado no SHA-256 af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39, replay de PRE431/PRE638/PRE648/PRE652 e fork v0.5.7 no commit imutável 13373b70642a19adf232cd9ba39fc7ecb2275dc8.

- **Resultado 3-way autenticamente executado:** 7 arquivos confrontados: PRE99→receita V51, 0 alterados; PRE99→fork v0.5.7, 6 alterados; 1 idêntico nos três; 0 arquivos com conflitos textuais Git (7 merges limpos). V51 não contém patch exclusivo da receita nesses 7 arquivos, **não nos demais arquivos do motor**. Não substituir esses seis arquivos novos pelas versões antigas. Nenhum arquivo-fonte foi publicado no relatório, só hashes, tamanhos, contagem de hunks e categorias; nenhum patch aplicado ao fork.
- Hunks PRE99→fork: nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp=6; nativo/sdk/include/rex/ui/vulkan/presenter.h=3; nativo/app/src/nfsmw_ajustes_graficos.cpp=0 (idêntico); nativo/app/src/nfsmw_nativo_sistema.cpp=3; nativo/app/src/nfsmw_nativo_destinos.cpp=26; android/app/src/main/java/io/github/nfsmwrecomp/MotorNativo.java=1; android/app/src/main/java/io/github/nfsmwrecomp/Ajustes.java=3. Todos PRE99→V51 têm 0 hunks.
- Artefato real GitHub ID 14009380825, ZIP de 2.562 bytes SHA-256 f86f53009b26bd139d76f87f6d5785b53de15c4559a7715050b48ef2360394d5; CRC aprovado, upload e readback conferidos no Drive: https://drive.google.com/file/d/1Ab0uboQDlFpa2EiYh58xWQucoWpRvLDN/view . Documento permanente no fork docs/MIG_A3_V51_THREE_WAY_SOURCE_EVIDENCE_20261113.md, PR #3 https://github.com/Juniklx/NFSMW-Recompiled-Mobile/pull/3 integrado no commit 6cc6d679b9b844a2a798981f4f47095df381be17.
- **Limites:** usar git merge-file -p sem conflito demonstra somente compatibilidade textual. Receita V51 autenticada não comprova igualdade binária com libmain.so da V51 instalada. Ainda não houve diff de toda árvore, build ARM64, validação de execução no telefone, benchmark, novo APK, nem assinatura. Renderizador `nativo/app/src/nfsmw_nativo_dibujos.cpp` tem patch V51 PRE648 em memória e não está entre esses 7 arquivos. Há vários outros patches locais ainda não migrados.
- **Próximo MIG-A4:** inventariar mudanças reais PRE99→V51 no conjunto seguro de fontes e comparar com fork, sem publicar código gerado de XEX/ISO, assets, material de assinatura, saves, executáveis/ROM, nem conteúdo privado. Só migrar patches autenticados e semanticamente revisados, preservar upstream novo, V3 iPega PG-9076/touch e correções de estabilidade.
- Preservar V51 instalada io.github.nfsmwrecomp versionCode 51, certificado SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b; nenhuma V52. Resolução interna 1920x1080, alvo máximo 120 FPS, gráficos, shaders, efeitos, física, saves e proteção térmica inalterados.

STATUS: MIG_A3_THREE_WAY_PASS; V51_CHANGED_IN_7=0; FORK_CHANGED_IN_7=6; CONFLICTS=0; NO_V52; NO_FPS_GAIN.
"""

def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def compose(b: bytes) -> bytes:
    if len(b) != EXPECTED_BYTES or digest(b) != EXPECTED_SHA:
        raise ValueError("MIG_A3_CANONICAL_CHANGED_ABORT")
    s = b.decode("utf-8")
    if not s.startswith("# CONTEXTO_NFSMW.md — FLUXO ATUAL GITHUB ACTIONS ONLY"):
        raise ValueError("MIG_A3_HEADER_MISMATCH")
    if s.count("## MIG_A2_V51_FORK_FINGERPRINTS_20261113") != 1:
        raise ValueError("MIG_A3_PRIOR_GATE_MISSING")
    if MARKER in s:
        raise ValueError("MIG_A3_ALREADY_WRITTEN")
    return (s.rstrip("\n") + "\n\n---\n\n" + APPEND).encode("utf-8")

def read(api, fid):
    b = api.files().get_media(fileId=fid, supportsAllDrives=True).execute(num_retries=4)
    if not isinstance(b, bytes):
        raise ValueError("MIG_A3_MEDIA_NOT_BYTES")
    return b

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--apply", action="store_true")
    opts = p.parse_args()
    if opts.self_test:
        assert len(EXPECTED_SHA)==64 and EXPECTED_BYTES>1_000_000
        assert APPEND.startswith(MARKER) and "MIG_A3" in APPEND
        print("MIG_A3_CONTEXT_LOCAL_CHECK=PASS")
        return
    if not opts.apply:
        p.error("Use --apply")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    keys = ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    if not all(os.environ.get(x) for x in keys):
        raise ValueError("MIG_A3_DRIVE_OAUTH_NOT_CONFIGURED")
    creds = Credentials(
        token=None, refresh_token=os.environ[keys[0]],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ[keys[1]], client_secret=os.environ[keys[2]])
    creds.refresh(Request())
    api=build("drive","v3",credentials=creds,cache_discovery=False)
    old=read(api,CANON)
    immutable_backup=read(api,BACKUP)
    if old!=immutable_backup or len(old)!=EXPECTED_BYTES or digest(old)!=EXPECTED_SHA:
        raise ValueError("MIG_A3_BACKUP_DRIFT_ABORT")
    new=compose(old)
    upload=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=False)
    result=api.files().update(fileId=CANON,media_body=upload,fields="id,size",supportsAllDrives=True).execute(num_retries=4)
    if result.get("id")!=CANON or int(result.get("size",-1))!=len(new):
        raise ValueError("MIG_A3_DRIVE_UPDATE_METADATA_ERROR")
    if read(api,CANON)!=new or read(api,BACKUP)!=old:
        raise ValueError("MIG_A3_READBACK_ERROR")
    print("MIG_A3_CANONICAL_CONTEXT_UPDATED_AND_READBACK_VERIFIED=TRUE")
    print("MIG_A3_NEW_BYTES="+str(len(new)))
    print("MIG_A3_NEW_SHA256="+digest(new))
    print("MIG_A3_APK_MODIFIED=FALSE")
if __name__ == "__main__":
    main()
