#!/usr/bin/env python3
"""PRE685 guarded private context append using independently checked Drive backup."""
import datetime as dt
import hashlib
import io
import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

CONTEXT_ID="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP_ID="1QxGq0kqiJnaMaKgERZgMO3JaMifNGEAB"
ROOT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
LOGS="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
MARKER="# PRE685 — histogramas reais de Swaps e limite de evidencia de fluidez"
APPEND="""
---

# PRE685 — histogramas reais de Swaps e limite de evidencia de fluidez (2026-11-10)

- PRE685 GitHub Actions run 42939712263, job 130258342439, completed/success. Disparo automatico pelo commit ddcf87777464753eac7e9eb2e9093a303ee5665a. Auditoria de log somente leitura, sem build, patches nem APK nova.
- Relatorio privado Drive: NFSMW_PRE685_V51_SWAP_PACING_20261111_013251.zip, ID 1DXBieBfXNtcN1JsOqI2BrT43b2rUISke, 3026 bytes, SHA256 038bdcb72df154691c3a3d747d413e13f800d11cf64c1cf43a3e9619718278ae, ZIP CRC PASS; contem PRE685_REPORT.json, PRE685_WINDOW_HISTOGRAMS.csv e PRE685_README.md.
- Insumo autentico: log PRE656 Galaxy S24 FE, Drive 1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd, 576129 bytes, SHA256 649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7. Nao houve uma nova execucao do jogo nesta auditoria.
- O log PRE656 ja continha histogramas de intervalos entre Swaps do motor. 7 janelas de ~20 segundos verificadas e conferidas com contador cumulativo presentados. Nas 5 finais: 6002 intervalos; 5784 (96,368%) de 15 a 18 ms; 162 de 18 a 25 ms; 56 abaixo de 15 ms; zero acima de 25 ms. Estas janelas englobam cinematica, transicao e jogabilidade.
- Nas 2 ultimas janelas inteiramente posteriores ao retorno a jogabilidade com carro parado: 2401 intervalos, 2314 (96,377%) de 15 a 18 ms, 64 de 18 a 25 ms, 23 abaixo de 15 ms e zero acima de 25 ms. FPS estimados pela variacao de presentados/tempo: 59,994 e 59,999.
- Nas 2 primeiras janelas, com carregamento/menus/transicoes, ocorreram respectivamente 8 e 5 intervalos acima de 25 ms, pior quadro do motor 99,9 ms e 109,8 ms.
- A sessao PRE656 informa resolucao interna 1920x1080, limite 60 FPS, modo de video listado 1280x720 60 Hz, swapchain Vulkan 1920x1080, MAILBOX, 4 imagens solicitadas e mensagem de ausencia de vsync implicito. Existe linha de filtragem anisotropica 16x. Flags efetivas de desfoque/PCF/sombra vegetacao permanecem desconhecidas.
- Interpretacao essencial: esses intervalos SAO histogramas internos entre Swaps do motor; NAO SAO timestamps reais de composicao/apresentacao na tela Android/SurfaceFlinger. Nao descartam sensacao de 30 FPS em outras sessoes, duplicacao de quadros na exibicao ou variacao entre instantes. Nao representam prova de fluidez percebida, diagnostico de causa, pixel equivalence ou ganho de FPS.
- Proximo gate PRE686: coletar frametimes de exibicao no S24 FE via leitura passiva SurfaceFlinger/Perfetto, com permissoes e superficie identificadas, junto a novo nfsmw.log da mesma sessao e telemetria termica acessivel. Sem alterar clocks, politicas termicas, shaders ou efeitos.
- Release preservada: V51 PRE652, io.github.nfsmwrecomp, versionCode=51, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b; todos os dados, controles, fisica e graficos mantidos. Sem nova APK, assinatura ou ganho FPS comprovado.

Status PRE685: ACTIONS_PASS; ENGINE_SWAP_INTERVALS_OBSERVED; DISPLAY_FRAME_TIMESTAMPS_NOT_OBSERVED; RUNTIME_BLUR_SHADOW_FLAGS_UNKNOWN; NO_BUILD; FPS_GAIN_UNPROVEN.
"""

def sha(b):
    return hashlib.sha256(b).hexdigest()

def get_bytes(d,fid):
    stream=io.BytesIO()
    downloader=MediaIoBaseDownload(stream,d.files().get_media(fileId=fid),chunksize=4*1024*1024)
    done=False
    while not done:
        _,done=downloader.next_chunk()
    return stream.getvalue()

def main():
    names=("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET")
    if any(not os.environ.get(n) for n in names):
        raise ValueError("PRE685_CONTEXT_REQUIRED_OAUTH_SECRET_MISSING")
    cred=Credentials(token=None,refresh_token=os.environ[names[0]],client_id=os.environ[names[1]],
        client_secret=os.environ[names[2]],token_uri="https://oauth2.googleapis.com/token")
    cred.refresh(Request())
    drive=build("drive","v3",credentials=cred,cache_discovery=False)
    meta=drive.files().get(fileId=CONTEXT_ID,fields="id,name,mimeType,size,parents").execute()
    if (meta.get("id")!=CONTEXT_ID or meta.get("name")!="CONTEXTO_NFSMW.md"
        or meta.get("mimeType")!="text/markdown" or ROOT not in meta.get("parents",[])):
        raise ValueError("PRE685_CONTEXT_TARGET_ID_OR_PARENT_UNEXPECTED")
    current=get_bytes(drive,CONTEXT_ID)
    if meta.get("size")!=str(len(current)):
        raise ValueError("PRE685_CONTEXT_SIZE_INCONSISTENCY")
    source=current.decode("utf-8")
    if MARKER in source:
        print("PRE685_CANONICAL_CONTEXT_ALREADY_CURRENT=TRUE")
        return
    last="Status PRE684: ACTIONS_PASS; C2_GPU_AGGREGATED_ANALYZED; PAL_PRE648_EXECUTION_INDICATED; LIVE_GRAPHICS_CVARS_UNVERIFIED; NO_BUILD; FPS_GAIN_UNPROVEN."
    if not source.rstrip().endswith(last):
        raise ValueError("PRE685_CANONICAL_CONTEXT_TAIL_CHANGED_REFUSE")
    if sha(get_bytes(drive,BACKUP_ID))!=sha(current):
        raise ValueError("PRE685_CANONICAL_CONTEXT_CHANGED_SINCE_BACKUP_REFUSE")
    updated=(source.rstrip()+"\n\n"+APPEND.lstrip()).encode("utf-8")
    drive.files().update(fileId=CONTEXT_ID,
        media_body=MediaIoBaseUpload(io.BytesIO(updated),mimetype="text/markdown",resumable=True),
        fields="id,size").execute()
    if sha(get_bytes(drive,CONTEXT_ID))!=sha(updated):
        raise ValueError("PRE685_CANONICAL_CONTEXT_READBACK_MISMATCH")
    receipt=json.dumps({
        "gate":"PRE685_CANONICAL_CONTEXT_SYNC","status":"PASS",
        "audit_run_id":"42939712263","sync_run_id":os.environ.get("GITHUB_RUN_ID"),
        "context_id":CONTEXT_ID,"backup_id":BACKUP_ID,
        "original_sha256":sha(current),"updated_sha256":sha(updated),
        "apk_or_signing_changed":False,
    },sort_keys=True,indent=2).encode("utf-8")
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    created=drive.files().create(
        body={"name":"NFSMW_PRE685_CONTEXT_SYNC_"+stamp+".json","parents":[LOGS]},
        media_body=MediaIoBaseUpload(io.BytesIO(receipt),mimetype="application/json"),
        fields="id,size").execute()
    if sha(get_bytes(drive,created["id"]))!=sha(receipt):
        raise ValueError("PRE685_CONTEXT_RECEIPT_READBACK_MISMATCH")
    print("PRE685_CONTEXT_BACKUP_READBACK=PASS")
    print("PRE685_CONTEXT_INPLACE_SHA256_READBACK=PASS")
    print("PRE685_CONTEXT_RECEIPT_PRIVATE=PASS")
    print("PRE685_APK_BUILD_SIGNING=NONE")

if __name__=="__main__":
    main()
