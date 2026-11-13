#!/usr/bin/env python3
"""MIG-A4: fail-closed Google Drive canonical-context append; GitHub Actions only."""
import argparse
import hashlib
import io
import os

CANON = "1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP = "1f4QST8BYi863RmGSe93jvX7OQfUBECHL"
EXPECTED_BYTES = 1396995
EXPECTED_SHA = "9eb9fac722e95ead2a33fca3c05bb2ff8ef9ced912020b56c1eb24e6ace2d726"
MARKER = "## MIG_A4_V51_SCOPED_PATCH_INVENTORY_20261113"
APPEND = """## MIG_A4_V51_SCOPED_PATCH_INVENTORY_20261113 — inventário autenticado PRE99 × V51 × fork (13/11/2026)

**Fluxo GitHub Actions-only sem Kaggle.** Tentativa inicial GitHub Actions https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43394591362 falhou exclusivamente por criação de diretório temporário sem parents=True e NÃO é resultado técnico aprovado. A correção pontual foi aplicada no script automation/actions_only/mig_a4_v51_scoped_source_inventory.py, commit 5583170c0d49b28405fbeadbe120c2fa24718f78. Segunda execução https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43394929759, job 131783448735, **completed/success**, MIG_A4_STATUS=PASS_AUTHENTICATED_SCOPED_INVENTORY.

- PRE99 autenticada no runner com SHA256 af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39; receita V51 reconstruída via PRE431/PRE638 e injeção PRE648 no renderizador SOMENTE EM MEMÓRIA, SHA V51 9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2. Fork público comparado no commit 6cc6d679b9b844a2a798981f4f47095df381be17. Auditoria cobre apenas fontes rastreadas e públicas do fork sob prefixos restritos, não fontes geradas de XEX/ISO, app_usa, shaders, assets, saves nem arquivos privados.
- 795 arquivos elegíveis; 10 tiveram mudança PRE99→receita V51. Destes, 5 arquivos V51 alterados permanecem iguais à PRE99 no fork; 5 foram alterados nos dois lados; 0 estão idênticos à V51 nos 10 arquivos; 0 novos/removidos públicos; dois arquivos com conflitos de merge textual: nativo/sdk/src/ui/overlay/settings_overlay.cpp (5 conflitos) e nativo/sdk/src/ui/windowed_app_context_sdl.cpp (1 conflito).
- Lista completa dos 10 arquivos: nativo/app/src/nfsmw_nativo_dibujos.cpp (9 hunks V51, 5 fork, ambos modificados); nativo/sdk/include/rex/input/sdl/sdl_input_driver.h (2,0, só V51); nativo/sdk/include/rex/ui/imgui_drawer.h (1,0, só V51); nativo/sdk/include/rex/ui/overlay/settings_overlay.h (1,0, só V51); nativo/sdk/src/input/input_system.cpp (2,0, só V51); nativo/sdk/src/input/sdl/sdl_input_driver.cpp (2,7, ambos); nativo/sdk/src/ui/imgui_drawer.cpp (2,0, só V51); nativo/sdk/src/ui/overlay/settings_overlay.cpp (20,12, 5 conflitos); nativo/sdk/src/ui/presenter.cpp (2,7, ambos); nativo/sdk/src/ui/windowed_app_context_sdl.cpp (1,10, 1 conflito).
- Relatório real sanitizado ZIP do GitHub artifact 14021674993 com 3.684 bytes, SHA256 561d7e6fa633d7e4b08afda113091dafedfd65f7f9f5dd09022e2d7d744885a9. CRC aprovado e Google Drive readback conferido no link https://drive.google.com/file/d/1nVo6a_EBssQj4NOnbTny4q8HeuTsARQD/view. Sem código-fonte, XEX, APK ou segredos nos artifacts.
- Documento no fork docs/MIG_A4_AUTHENTICATED_V51_PATCH_INVENTORY_20261113.md, PR #4 https://github.com/Juniklx/NFSMW-Recompiled-Mobile/pull/4 integrado na main pelo commit 16233a34b88f0af3880fb506ba68f6d6c6e137f3, APENAS DOCUMENTAÇÃO.
- Próximo gate MIG-A5: identificar semanticamente modificações V51 em entrada PG-9076/touch e reconciliação do renderizador PRE648; resolver conflitos em overlay/SDL com avaliação de funções, sem sobrescrever o upstream v0.5.7. Nenhum patch V51 foi portado ao fork neste gate.
- **Limites:** inventário não cobre toda a árvore nem arquivos excluídos por segurança. Mesclagem textual limpa não confirma equivalência funcional; receita V51 reconstruída não comprova identidade byte a byte com a APK V51 assinada. Não houve build Android/ARM64 completa, nova APK V52, novo teste Galaxy nem melhora FPS comprovada.
- Invariantes: V51 instalada preservada, package io.github.nfsmwrecomp, versionCode 51, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Nunca usar signing debug, novas chaves ou pedir senhas. Manter 1920x1080 internos, alvo até 120FPS, gráficos/shaders/efeitos/física integrais, PG-9076/touch, saves e proteções térmicas.

STATUS: MIG_A4_SCOPED_SOURCE_INVENTORY_PASS; 795_ELIGIBLE; 10_V51_PATCHED; 5_V51_ONLY; 5_BOTH_CHANGED; 2_CONFLICT_FILES; NO_V52; NO_FPS_GAIN.
"""

def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def compose(b: bytes) -> bytes:
    if len(b) != EXPECTED_BYTES or digest(b) != EXPECTED_SHA:
        raise ValueError("MIG_A4_CANONICAL_CHANGED_ABORT")
    s = b.decode("utf-8")
    if not s.startswith("# CONTEXTO_NFSMW.md — FLUXO ATUAL GITHUB ACTIONS ONLY"):
        raise ValueError("MIG_A4_HEADER_MISMATCH")
    if s.count("## MIG_A3_V51_FORK_THREE_WAY_20261113") != 1:
        raise ValueError("MIG_A4_PRIOR_GATE_MISSING")
    if MARKER in s:
        raise ValueError("MIG_A4_ALREADY_WRITTEN")
    return (s.rstrip("\n") + "\n\n---\n\n" + APPEND).encode("utf-8")

def read(api, fid):
    b = api.files().get_media(fileId=fid, supportsAllDrives=True).execute(num_retries=4)
    if not isinstance(b, bytes):
        raise ValueError("MIG_A4_MEDIA_NOT_BYTES")
    return b

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--apply", action="store_true")
    opts = p.parse_args()
    if opts.self_test:
        assert len(EXPECTED_SHA)==64 and EXPECTED_BYTES>1_000_000
        assert APPEND.startswith(MARKER) and "MIG_A4" in APPEND
        print("MIG_A4_CONTEXT_LOCAL_CHECK=PASS")
        return
    if not opts.apply:
        p.error("Use --apply")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    keys = ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    if not all(os.environ.get(x) for x in keys):
        raise ValueError("MIG_A4_DRIVE_OAUTH_NOT_CONFIGURED")
    creds = Credentials(
        token=None, refresh_token=os.environ[keys[0]],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ[keys[1]], client_secret=os.environ[keys[2]])
    creds.refresh(Request())
    api=build("drive","v3",credentials=creds,cache_discovery=False)
    old=read(api,CANON)
    immutable_backup=read(api,BACKUP)
    if old!=immutable_backup or len(old)!=EXPECTED_BYTES or digest(old)!=EXPECTED_SHA:
        raise ValueError("MIG_A4_BACKUP_DRIFT_ABORT")
    new=compose(old)
    upload=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=False)
    result=api.files().update(fileId=CANON,media_body=upload,fields="id,size",supportsAllDrives=True).execute(num_retries=4)
    if result.get("id")!=CANON or int(result.get("size",-1))!=len(new):
        raise ValueError("MIG_A4_DRIVE_UPDATE_METADATA_ERROR")
    if read(api,CANON)!=new or read(api,BACKUP)!=old:
        raise ValueError("MIG_A4_READBACK_ERROR")
    print("MIG_A4_CANONICAL_CONTEXT_UPDATED_AND_READBACK_VERIFIED=TRUE")
    print("MIG_A4_NEW_BYTES="+str(len(new)))
    print("MIG_A4_NEW_SHA256="+digest(new))
    print("MIG_A4_APK_MODIFIED=FALSE")
if __name__ == "__main__":
    main()
