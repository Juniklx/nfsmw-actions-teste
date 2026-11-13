#!/usr/bin/env python3
"""MIG-A5: fail-closed Google Drive canonical-context append; GitHub Actions only."""
import argparse
import hashlib
import io
import os

CANON = "1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP = "1dmq9WJnmiHP5o2SjeYQCjPoAS1GuvVCO"
EXPECTED_BYTES = 1401039
EXPECTED_SHA = "f95fdb71459c9817a4927c3eed5acda16afab21ffc71ba0f4b2402f19a7d9068"
MARKER = "## MIG_A5_PRIVATE_SDK_INPUT_PRE170_PORT_20261113"
APPEND = """## MIG_A5_PRIVATE_SDK_INPUT_PRE170_PORT_20261113 — código PRE170 isolado para validação (13/11/2026)

**Fluxo apenas GitHub Actions, sem Kaggle.** Executada restauração autenticada de PRE99 + receita V51 e auditoria limitada a três arquivos públicos de SDK/entrada; run GitHub https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43451194001, job 131973489939, completed/success. O arquivo de comparação foi salvo no Drive privado, id 1G-8AJwIyDvwZbOIGZcT83FE9juA5M0VO, https://drive.google.com/file/d/1G-8AJwIyDvwZbOIGZcT83FE9juA5M0VO/view, ZIP com 18.451 bytes, SHA-256 b209b369cbbcb92620457fe9e155f50dda8fac77ece4be5f5e7b76edf6558159, CRC e readback autenticados. O ZIP contém apenas diffs e versões SDK dos três arquivos para revisão interna; NÃO publicar como artifact GitHub. O artifact público 14051376028 contém somente metadados JSON (1.248 bytes).

- Três arquivos confrontados PRE99 × receita V51 × fork v0.5.7: nativo/sdk/include/rex/input/sdl/sdl_input_driver.h (2 hunks V51, 0 fork), nativo/sdk/src/input/input_system.cpp (2 V51, 0 fork), nativo/sdk/src/input/sdl/sdl_input_driver.cpp (2 V51, 7 fork). Mesclagem textual limpa nos três; isso não prova correção funcional.
- Identificadas mudanças **PRE170** no header/driver SDL: estado atômico sdl_next_pump_ns_ e limitação para Android de novas solicitações SDL_PumpEvents a uma janela de no mínimo 8ms (steady_clock + compare_exchange_weak). A operação do iPega PG-9076/touch com esse throttle na nova base ainda NÃO foi testada. Sem benchmark de wakeup/FPS.
- Identificada **PRE364** no input_system.cpp: apenas instrumentação XInput para até 256 mudanças digitais, com logging. Decisão de MIG-A5: NÃO portar PRE364 nesta fase, para evitar carga diagnóstica sem finalidade funcional de release.
- Migração de código **somente em branch isolada** feature/mig-a5-pre170-android-sdl-pump do fork Juniklx/NFSMW-Recompiled-Mobile, PR **#5 draft** https://github.com/Juniklx/NFSMW-Recompiled-Mobile/pull/5, head 75d18109a4b0b15e79248f12bc82872c4a1a7e6b; nenhuma mesclagem em main, nenhuma substituição de APK/saves/assinatura. Dois arquivos SDK foram modificados: sdl_input_driver.h e sdl_input_driver.cpp. O input_system.cpp ficou inalterado. Código novo do upstream no driver foi preservado.
- Testes source-only e algoritmo atômico C++20 sintético em GitHub Actions https://github.com/Juniklx/NFSMW-Recompiled-Mobile/actions/runs/43452479081, completed/success, e execução do pull_request https://github.com/Juniklx/NFSMW-Recompiled-Mobile/actions/runs/43452750252, completed/success. Header SHA256 6b532f228805dbd57aaaa3d4e19d6febf784506ebacd6b80216af254cae2f5ca idêntico ao reconstruído V51; bloco PRE170 de QueueControllerUpdate SHA256 0831a7b2e99a702b3dc2d0a7b6f8f961059ca2b261ab0999ad1e4a92322d07d4 idêntico ao bloco V51 autenticado. Teste sintético confirmou gate de 8ms e somente uma concessão em concorrência controlada, mas não reproduz SDK SDL3 real no Android.
- Houve uma falha intermediária do novo teste de bloco de código no run 43452411262 por escape incorreto de newline no script do guard; corrigida no commit ab35113809ad5dc1a08871b5718148a0a876e2a2, com run subsequente PASS. Não é falha de Android, SDL ou código C++.
- **Limites:** ainda não foi compilado C++ nativo SDK em NDK ARM64 nem empacotado/assinado APK V52; o PR draft deve permanecer não mesclado até validação de compilação e teste de PG-9076/touch, hotplug, latência, gráficos e fluidez. O throttle pode alterar latência/tempo de atualização SDL. A receita V51 autenticada não demonstra equivalência binária com libmain.so instalada.
- **Próximo gate MIG-A6:** preparar compilação real ARM64 de SDK/arquivos modificados usando somente GitHub Actions e dependências verificadas, sem ISO/XEX/assets/chave nos artifacts públicos; conferir vínculo com ponte Android e integridade dos outros patches locais, resolver conflitos de UI/renderização antes da futura APK. Conservar V51 instalada io.github.nfsmwrecomp versionCode 51, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Fork main original ainda usa versionCode 16 e assinatura debug; nunca distribuí-lo como atualização. Resolução interna 1920x1080, alvo máximo 120FPS, shaders/efeitos/física/saves/PG-9076/touch/proteções térmicas intactos.

STATUS: MIG_A5_PRIVATE_SDK_PATCH_REVIEW_PASS; PRE170_DRAFT_PR_5_SOURCE_GUARD_PASS; PRE364_EXCLUDED; ARM64_BUILD_NOT_PROVEN; PR_NOT_MERGED; NO_V52; NO_FPS_GAIN.
"""

def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def compose(b: bytes) -> bytes:
    if len(b) != EXPECTED_BYTES or digest(b) != EXPECTED_SHA:
        raise ValueError("MIG_A5_CANONICAL_CHANGED_ABORT")
    s = b.decode("utf-8")
    if not s.startswith("# CONTEXTO_NFSMW.md — FLUXO ATUAL GITHUB ACTIONS ONLY"):
        raise ValueError("MIG_A5_HEADER_MISMATCH")
    if s.count("## MIG_A4_V51_SCOPED_PATCH_INVENTORY_20261113") != 1:
        raise ValueError("MIG_A5_PRIOR_GATE_MISSING")
    if MARKER in s:
        raise ValueError("MIG_A5_ALREADY_WRITTEN")
    return (s.rstrip("\n") + "\n\n---\n\n" + APPEND).encode("utf-8")

def read(api, fid):
    b = api.files().get_media(fileId=fid, supportsAllDrives=True).execute(num_retries=4)
    if not isinstance(b, bytes):
        raise ValueError("MIG_A5_MEDIA_NOT_BYTES")
    return b

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--apply", action="store_true")
    opts = p.parse_args()
    if opts.self_test:
        assert len(EXPECTED_SHA)==64 and EXPECTED_BYTES>1_000_000
        assert APPEND.startswith(MARKER) and "MIG_A5" in APPEND
        print("MIG_A5_CONTEXT_LOCAL_CHECK=PASS")
        return
    if not opts.apply:
        p.error("Use --apply")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    keys = ("GOOGLE_REFRESH_TOKEN", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    if not all(os.environ.get(x) for x in keys):
        raise ValueError("MIG_A5_DRIVE_OAUTH_NOT_CONFIGURED")
    creds = Credentials(
        token=None, refresh_token=os.environ[keys[0]],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ[keys[1]], client_secret=os.environ[keys[2]])
    creds.refresh(Request())
    api=build("drive","v3",credentials=creds,cache_discovery=False)
    old=read(api,CANON)
    immutable_backup=read(api,BACKUP)
    if old!=immutable_backup or len(old)!=EXPECTED_BYTES or digest(old)!=EXPECTED_SHA:
        raise ValueError("MIG_A5_BACKUP_DRIFT_ABORT")
    new=compose(old)
    upload=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=False)
    result=api.files().update(fileId=CANON,media_body=upload,fields="id,size",supportsAllDrives=True).execute(num_retries=4)
    if result.get("id")!=CANON or int(result.get("size",-1))!=len(new):
        raise ValueError("MIG_A5_DRIVE_UPDATE_METADATA_ERROR")
    if read(api,CANON)!=new or read(api,BACKUP)!=old:
        raise ValueError("MIG_A5_READBACK_ERROR")
    print("MIG_A5_CANONICAL_CONTEXT_UPDATED_AND_READBACK_VERIFIED=TRUE")
    print("MIG_A5_NEW_BYTES="+str(len(new)))
    print("MIG_A5_NEW_SHA256="+digest(new))
    print("MIG_A5_APK_MODIFIED=FALSE")
if __name__ == "__main__":
    main()
