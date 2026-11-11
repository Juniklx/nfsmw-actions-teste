#!/usr/bin/env python3
"""PRE688 private Drive context sync, backup-guarded, no game binary access."""
import datetime as dt
import hashlib,io,json,os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload,MediaIoBaseUpload

CONTEXT="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP="1lQi4sEDac3zunZm7vdfZlqenAZyU47C6"
ROOT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
LOGS="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
MARKER="## PRE687-PRE688 — Shevery interrompeu a coleta; ADB preparado"
TAIL="Status PRE686: REAL_SURFACEVIEW_CAPTURE_PASS; ACTIONS_REPLAY_PASS; ENGINE_C2_60FPS_OBSERVED; DISPLAY_INTERVALS_8_16_24MS_OBSERVED; GAMEPLAY_ONLY_UNCONFIRMED; CAUSE_UNPROVEN; NO_APK; FPS_GAIN_UNPROVEN."
APPEND="""
---

## PRE687-PRE688 — Shevery interrompeu a coleta; ADB preparado (2026-11-10/11)

PRE687 — COLETA INCONCLUSIVA: o usuario confirmou que Shevery abriu automaticamente duas vezes durante o teste e voltou ao jogo apos cada abertura. Arquivos recebidos: nfsmw.log (788568 bytes, SHA256 ced48603d4260d58047a56bfcc0ae434c2fda348b792fe48a379fa470762f317) e NFSMW_PRE687_CAPTURE_20261110_235045.status.txt (28819 bytes, SHA256 f0bd15f5e3a2a6984350af21c6675afa1587b88592bc8106ef5196896f9030fd). NAO publicar logs brutos no GitHub publico.

Eventos reais do jogo: superficie Vulkan desatualizada em 23:52:39.304 e 23:54:11.756; nova swapchain Vulkan MAILBOX 1920x1080 criada em 23:52:39.342 e 23:54:11.779. Esses eventos sao compativeis com alternancia inesperada de apps, mas a causa nao esta comprovada. O vigilante registrou 5s sem progresso de nenhuma das 17 threads em 23:54:28.778, e 20s em 23:54:43.803. Isso e um aviso real de falta de progresso, nao prova de deadlock causado por Shevery.

Arquivo PRE687 status contem PRE687_NO_LABELED_PRESENT_TO_PRESENT_HISTOGRAM=TRUE e NAO contem PRE687_CAPTURE_SUCCESS. O bloco SurfaceView do jogo inclui displayRefreshRate=120 fps, totalFrames=5346 e averageFPS=62.241, mas a coleta contem as duas interrupcoes; NAO e amostra de jogabilidade continua, nem PASS da PRE687.

PRE688 — SOMENTE PREPARADA: script publico automation/termux/nfsmw_pre688_adb_surfaceflinger.sh criado no repo Juniklx/nfsmw-actions-teste, commit 950a6308585bd16c97db4f6282ccc13f56eaee2d. Alternativa por Termux mais ADB sem fio pareado, sem chamadas Shevery, Shizuku ou rish. Faz preflight uid shell=2000, coleta temporizada de dumpsys SurfaceFlinger --timestats, filtra apenas SurfaceView do NFSMW e preserva rotulo present2present. Rejeita mais de uma camada NFSMW, nao salva dump global bruto e desativa contadores no final. Nao altera APK, kernel, clocks, temperatura ou frequencia de tela.

VALIDACAO LIMITADA: copia local passou bash -n e teste ADB sintetico: uma camada NFSMW PASS, duas camadas FAIL-CLOSED, nenhuma outra camada incluida no arquivo salvo. Workflow sintetico criado no GitHub em .github/workflows/nfsmw-pre688-adb-collector-preflight.yml; solicitacao de execucao pelo commit f9870cda470a4de8c31e1f2b5ef3c50284bf8648. Conclusao de GitHub Actions ainda nao confirmada neste registro. Nao declarar teste real no Galaxy.

PROXIMO PASSO: parear ADB sem fio no proprio telefone, verificar adb devices e adb shell id via Termux, coletar 90s no carro parado sem trocar aplicativos, e enviar NFSMW_PRE688_PRESENT2PRESENT_*.txt e novo nfsmw.log da mesma sessao. Conferir horario, ausencia de nova superficie outdated e alertas 5s/20s antes de comparar histograma da tela aos Swaps internos. Se ADB local nao estiver acessivel, registrar bloqueio e usar computador com ADB.

Release preservada: V51 PRE652, io.github.nfsmwrecomp, versionCode 51, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Sem V52, reducao grafica, alteracao de saves, fisica, controle ou bypass termico. FPS_GAIN_UNPROVEN.

Status PRE688: PRE687_INCONCLUSIVE; SHEVERY_INTERRUPTS_USER_CONFIRMED; WATCHDOG_5S_20S_OBSERVED_CAUSE_UNKNOWN; ADB_COLLECTOR_STAGED; REAL_DEVICE_TEST_PENDING.
"""

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(d, fid):
    output=io.BytesIO()
    downloader=MediaIoBaseDownload(output,d.files().get_media(fileId=fid),chunksize=4*1024*1024)
    done=False
    while not done:
        _,done=downloader.next_chunk()
    return output.getvalue()

def main():
    names=("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET")
    if any(not os.environ.get(n) for n in names):
        raise RuntimeError("PRE688_CONTEXT_MISSING_GOOGLE_SECRET")
    creds=Credentials(token=None,refresh_token=os.environ[names[0]],
        client_id=os.environ[names[1]],client_secret=os.environ[names[2]],
        token_uri="https://oauth2.googleapis.com/token")
    creds.refresh(Request())
    drive=build("drive","v3",credentials=creds,cache_discovery=False)
    meta=drive.files().get(fileId=CONTEXT,fields="id,name,mimeType,size,parents").execute()
    if (meta.get("id")!=CONTEXT or meta.get("name")!="CONTEXTO_NFSMW.md"
        or meta.get("mimeType")!="text/markdown" or ROOT not in meta.get("parents",[])):
        raise ValueError("PRE688_CONTEXT_CANONICAL_ID_MISMATCH")
    current=read(drive,CONTEXT)
    if meta.get("size")!=str(len(current)):
        raise ValueError("PRE688_CONTEXT_SIZE_CHANGED")
    text=current.decode("utf-8")
    if MARKER in text:
        print("PRE688_CONTEXT_ALREADY_PRESENT=TRUE")
        return
    if not text.rstrip().endswith(TAIL):
        raise ValueError("PRE688_CONTEXT_UNEXPECTED_TAIL_STOP")
    if sha(read(drive,BACKUP))!=sha(current):
        raise ValueError("PRE688_CONTEXT_CHANGED_SINCE_BACKUP_STOP")
    new=(text.rstrip()+"\n\n"+APPEND.lstrip()).encode("utf-8")
    drive.files().update(fileId=CONTEXT,
        media_body=MediaIoBaseUpload(io.BytesIO(new),mimetype="text/markdown",resumable=True),
        fields="id,size").execute()
    if sha(read(drive,CONTEXT))!=sha(new):
        raise ValueError("PRE688_CONTEXT_READBACK_FAILED")
    receipt=json.dumps({
        "gate":"PRE688_CONTEXT_SYNC","result":"PASS",
        "run_id":os.environ.get("GITHUB_RUN_ID"),
        "context_id":CONTEXT,"backup_id":BACKUP,
        "before_sha256":sha(current),"after_sha256":sha(new),
        "PRE687_capture_inconclusive":True,"PRE688_device_capture_tested":False,
        "APK_or_signing_modified":False
    },indent=2,sort_keys=True).encode("utf-8")
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    result=drive.files().create(
        body={"name":"NFSMW_PRE688_CONTEXT_SYNC_"+stamp+".json","parents":[LOGS]},
        media_body=MediaIoBaseUpload(io.BytesIO(receipt),mimetype="application/json"),
        fields="id,size").execute()
    if sha(read(drive,result["id"]))!=sha(receipt):
        raise ValueError("PRE688_CONTEXT_RECEIPT_READBACK_FAILED")
    print("PRE688_CONTEXT_BACKUP_AND_READBACK=PASS")
    print("PRE688_CONTEXT_UPDATED_IN_PLACE=PASS")
    print("PRE688_REAL_DEVICE_CAPTURE=NOT_PERFORMED")
    print("PRE688_NEW_APK_OR_FPS_GAIN=NONE")

if __name__=="__main__":
    main()
