#!/usr/bin/env python3
"""PRE690: guarded append to private NFSMW context; no APK access."""
import datetime as dt, hashlib, io, json, os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload,MediaIoBaseUpload

CONTEXT="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP="1ZM9ArNhyGtVtG9zfTbJabLXZG1N1w4p2"
ROOT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
LOGS="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
MARKER="## PRE690 — coleta ordenada por camada: preparada, não testada no Galaxy"
TAIL="Status PRE689: USER_CONFIRMED_NORMAL_EXIT_NO_FREEZE; POST_CAPTURE_WATCHDOG_NOT_GAMEPLAY_HANG_EVIDENCE; PRE688_CAPTURE_STILL_PASS; PACING_CAUSE_UNKNOWN; NEXT_FRAMETIMELINE_READONLY; NO_APK; NO_FPS_GAIN."
APPEND="""

---

## PRE690 — coleta ordenada por camada: preparada, não testada no Galaxy (2026-11-11)

PRE689 mantida: o usuario disse que saiu normalmente do NFSMW apos PRE688 e nao houve travamento percebido. O alerta do vigia de cinco segundos foi posterior a janela de medicao e nao demonstra deadlock durante jogabilidade.

PRE690: a documentacao atual do Perfetto FrameTimeline alerta que SurfaceViews nao sao suportadas no modelo documentado. Para a SurfaceView real do NFSMW, o AOSP implementa SurfaceFlinger --latency com timestamps desired_present_ns, actual_present_ns e frame_ready_ns em um historico circular por camada, tipicamente 127 quadros. Isso torna possivel experimentar sequencia ordenada de apresentacoes sem alterar o jogo, desde que a interface Samsung responda de forma valida. Fontes oficiais consultadas: https://perfetto.dev/docs/data-sources/frametimeline ; https://android.googlesource.com/platform/frameworks/native/+/refs/heads/main/services/surfaceflinger/Layer.cpp ; https://android.googlesource.com/platform/frameworks/native/+/refs/heads/master/services/surfaceflinger/SurfaceFlinger.cpp.

Ferramentas publicadas no repo Juniklx/nfsmw-actions-teste:
1. automation/termux/nfsmw_pre690_ordered_latency_adb.sh: requer apenas ADB sem fio ja pareado, uid 2000, modelo SM-S721B, escolhe uma unica SurfaceView NFSMW; apos 110 segundos faz reset do historico diagnostico SOMENTE desta camada e coleta 60 amostras em um segundo de intervalo. Salva apenas linhas da SurfaceView do jogo, sem outras camadas ou apps. Nenhuma chamada Shevery/Shizuku, root, alteracoes termicas, frequencia da tela, APK ou graficos.
2. automation/kaggle/pre690_analyze_ordered_latency.py: leitor Python que elimina timestamps repetidos das consultas circulares, identifica lacunas de amostragem, calcula intervalos e adjacencias reais de 8/24ms. Nao presume alternancia de quadros a partir do histograma PRE688.
3. .github/workflows/nfsmw-pre690-ordered-latency-synthetic.yml: gate de ADB simulado sem Secrets nem APK. Solicitado via commit 3762df7136758432b1ea9c91271bb3ff741b96b7. Conclusao do Actions ainda NAO confirmada neste registro; nao chamar PASS.

Teste local sintetico: bash -n validado; uma SurfaceView mock aceita, duas camadas mock rejeitadas, 20 amostras de timestamps foram lidas e analisadas sem interferencia no jogo. Analisador local reconstruiu 240 timestamps distintos e removeu 1188 repetidos, todos dados artificiais, NAO do S24 FE. A sintaxe do analisador publicado tambem sera testada pelo gate sintético.

PRE688 permanece a unica captura real de referencia: 5412 intervalos SurfaceView, FPS medio 62,226 e taxa informada de 120Hz; 597 de 8ms, 4184 de 16ms e 569 de 24-25ms. O motor C2 teve 4800 Swaps internos nas quatro janelas analisadas, 4685 entre 15-18ms, com cap 60 FPS, 1920x1080. O histograma de PRE688 nao informa a ordem; a causa da fluidez subjetiva ainda nao foi identificada.

PROXIMO TESTE: no Termux com ADB conectado executar o preflight da PRE690, depois arm 110 60; jogar com carro parado e nao alternar apps. Enviar arquivo NFSMW_PRE690_ORDERED_PRESENT_*.txt, status e nfsmw.log da MESMA sessao. Recusar se --latency nao for suportado ou retornar dados vazios/ambiguos.

Baseline V51 PRE652, io.github.nfsmwrecomp, versionCode 51, certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Nenhuma nova APK, mudanca grafica, assinatura, controles, saves, fisica ou protecao termica; nenhum ganho de FPS comprovado.

Status PRE690: LOCAL_SYNTHETIC_PASS; SCRIPT_AND_ANALYZER_PUBLISHED; GITHUB_SYNTHETIC_RESULT_UNVERIFIED; DEVICE_TEST_PENDING; NO_APK; NO_FPS_GAIN.
"""
def sha(b):return hashlib.sha256(b).hexdigest()
def fetch(d,id):
    b=io.BytesIO()
    t=MediaIoBaseDownload(b,d.files().get_media(fileId=id),chunksize=4*1024*1024)
    end=False
    while not end:_,end=t.next_chunk()
    return b.getvalue()
def main():
    names=("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET")
    if any(not os.environ.get(n) for n in names):raise RuntimeError("PRE690_OAUTH_SECRET_MISSING")
    c=Credentials(token=None,refresh_token=os.environ[names[0]],
       client_id=os.environ[names[1]],client_secret=os.environ[names[2]],
       token_uri="https://oauth2.googleapis.com/token")
    c.refresh(Request())
    d=build("drive","v3",credentials=c,cache_discovery=False)
    meta=d.files().get(fileId=CONTEXT,fields="id,name,mimeType,size,parents").execute()
    if meta.get("name")!="CONTEXTO_NFSMW.md" or meta.get("mimeType")!="text/markdown" or ROOT not in meta.get("parents",[]):
        raise ValueError("PRE690_CANONICAL_ID_INVALID")
    original=fetch(d,CONTEXT)
    if meta.get("size")!=str(len(original)):raise ValueError("PRE690_CONTEXT_CONCURRENT_CHANGE")
    content=original.decode("utf-8")
    if MARKER in content:
        print("PRE690_CONTEXT_ALREADY_STAGED=TRUE");return
    if not content.rstrip().endswith(TAIL):
        raise ValueError("PRE690_CONTEXT_TAIL_CHANGED_REFUSE")
    if sha(fetch(d,BACKUP))!=sha(original):
        raise ValueError("PRE690_BACKUP_MISMATCH_REFUSE")
    updated=(content.rstrip()+APPEND).encode("utf-8")
    d.files().update(fileId=CONTEXT,
        media_body=MediaIoBaseUpload(io.BytesIO(updated),mimetype="text/markdown",resumable=True),
        fields="id,size").execute()
    if sha(fetch(d,CONTEXT))!=sha(updated):
        raise ValueError("PRE690_CONTEXT_READBACK_MISMATCH")
    receipt=json.dumps({
        "stage":"PRE690_CONTEXT_STAGING",
        "status":"PASS",
        "run_id":os.environ.get("GITHUB_RUN_ID"),
        "context_id":CONTEXT,"backup_id":BACKUP,
        "before_sha256":sha(original),"after_sha256":sha(updated),
        "real_device_capture":False,
        "synthetic_ci_result_confirmed":False,
        "new_apk":False,"fps_gain_proven":False
    },sort_keys=True,indent=2).encode("utf-8")
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    meta=d.files().create(
      body={"name":"NFSMW_PRE690_CONTEXT_STAGING_"+stamp+".json","parents":[LOGS]},
      media_body=MediaIoBaseUpload(io.BytesIO(receipt),mimetype="application/json"),
      fields="id,size").execute()
    if sha(fetch(d,meta["id"]))!=sha(receipt):
        raise ValueError("PRE690_RECEIPT_READBACK_FAILED")
    print("PRE690_BACKUP_MATCH=PASS")
    print("PRE690_CONTEXT_READBACK=PASS")
    print("PRE690_PRIVATE_RECEIPT_READBACK=PASS")
    print("PRE690_NO_APK_OR_FPS_GAIN=TRUE")
if __name__=="__main__":main()
