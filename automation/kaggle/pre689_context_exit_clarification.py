#!/usr/bin/env python3
"""PRE689: guarded PRIVATE Drive append of user's clarification; not an APK or patch."""
import hashlib, io, json, os, datetime as dt
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

CONTEXT="1dRoE3qjSWZ4AwOaBQo97IINyecIFh6eB"
BACKUP="1PkoOFc3oFFTGe7staWiT5yslV43yzQlZ"
ROOT="1Waam42x_suvBS18b4360HOaBqKxAncvy"
LOGS="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
MARKER="## PRE689 — esclarecimento do usuário: saída normal após PRE688"
EXPECTED_TAIL="Status PRE688_REAL: ANDROID_ADB_CAPTURE_PASS; ACTIONS_AUDIT_PASS; 120HZ_SURFACEVIEW; FPS_CAP_60; IRREGULAR_PRESENT2PRESENT_BUCKETS_OBSERVED; NATIVE_4800_SWAPS_UNDER25MS; WATCHDOG_5S_AFTER_CAPTURE_CAUSE_UNKNOWN; NO_APK; NO_FPS_GAIN."
NOTE="""

---

## PRE689 — esclarecimento do usuário: saída normal após PRE688 (2026-11-11)

**Correção da interpretação de estabilidade (declaração direta do usuário):** "Eu saí do jogo, ele não travou". O usuário informou que deixou normalmente o NFSMW depois da coleta, sem observar travamento. O alerta textual do vigilante de 5 s às 00:36:36.144 ocorreu depois do término da janela PRE688 às 00:35:48.

**Conclusão corrigida:** não descrever o aviso de 5s como congelamento durante jogabilidade, crash ou deadlock comprovado. O evento é compativel com encerramento/saída para segundo plano e interrupção de progresso das threads monitoradas; o log não identifica a causa exata do aviso, nem estabelece o instante exato em que o usuário saiu. A hipótese anterior de um segundo defeito de travamento independente NÃO está sustentada por esta sessão. Não inferir que o aviso tenha ocorrido durante os 90s medidos.

**O que permanece válido:** PRE688 foi captura real aprovada de SurfaceFlinger pelo ADB sem fio sem abertura do Shevery pelo coletor (00:34:18–00:35:48), confirmada pelo GitHub Actions run 42955099751 e três arquivos privados com hash. SurfaceView informa 5412 intervalos, media 62,226 FPS, distribuídos em 8ms=597, 16ms=4184, 24–25ms=569 e demais=62. Motor C2 registrou 4800 intervalos internos em quatro janelas, majoritariamente 15–18ms, com limite 60 FPS e resolução 1920x1080. Histograma é agregado e NÃO confirma sequencia alternada nem causa da percepção de 30fps.

**Próximo gate:** priorizar captura com timestamps ordenados de apresentação (FrameTimeline/Perfetto) durante o carro parado para localizar a irregularidade sem interferência de troca de aplicativo. Tratar a possível relação entre C2 e SurfaceFlinger como hipótese até identificar o mecanismo. Não aplicar patches Vulkan, alterar modo de apresentação, reduzir gráficos, mexer em proteções térmicas ou gerar APK antes de diagnóstico rastreável.

**Versão preservada:** V51 PRE652, package io.github.nfsmwrecomp, versionCode=51; certificado permanente SHA256 1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b. Nenhum APK, fonte, shader ou save alterado nesta correção.

Status PRE689: USER_CONFIRMED_NORMAL_EXIT_NO_FREEZE; POST_CAPTURE_WATCHDOG_NOT_GAMEPLAY_HANG_EVIDENCE; PRE688_CAPTURE_STILL_PASS; PACING_CAUSE_UNKNOWN; NEXT_FRAMETIMELINE_READONLY; NO_APK; NO_FPS_GAIN.
"""
def h(b): return hashlib.sha256(b).hexdigest()
def get(d,fid):
    target=io.BytesIO();stream=MediaIoBaseDownload(target,d.files().get_media(fileId=fid),chunksize=4*1024*1024)
    done=False
    while not done: _,done=stream.next_chunk()
    return target.getvalue()
def main():
    names=("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET")
    if any(not os.environ.get(n) for n in names):raise RuntimeError("PRE689_SECRET_MISSING")
    c=Credentials(token=None,refresh_token=os.environ[names[0]],
                  client_id=os.environ[names[1]],client_secret=os.environ[names[2]],
                  token_uri="https://oauth2.googleapis.com/token")
    c.refresh(Request())
    d=build("drive","v3",credentials=c,cache_discovery=False)
    meta=d.files().get(fileId=CONTEXT,fields="id,name,mimeType,parents,size").execute()
    if meta.get("name")!="CONTEXTO_NFSMW.md" or ROOT not in meta.get("parents",[]) or meta.get("mimeType")!="text/markdown":
        raise ValueError("PRE689_CONTEXT_NOT_CANONICAL")
    before=get(d,CONTEXT)
    if str(len(before))!=meta.get("size"):raise ValueError("PRE689_SIZE_MISMATCH")
    text=before.decode("utf-8")
    if MARKER in text:
        print("PRE689_CONTEXT_ALREADY_CORRECTED=TRUE");return
    if not text.rstrip().endswith(EXPECTED_TAIL):raise ValueError("PRE689_TAIL_CHANGED_ABORT")
    if h(before)!=h(get(d,BACKUP)):raise ValueError("PRE689_BACKUP_NOT_IDENTICAL_ABORT")
    after=(text.rstrip()+NOTE).encode("utf-8")
    d.files().update(fileId=CONTEXT,media_body=MediaIoBaseUpload(io.BytesIO(after),mimetype="text/markdown",resumable=True),fields="id,size").execute()
    if h(get(d,CONTEXT))!=h(after):raise ValueError("PRE689_CONTEXT_READBACK_FAILED")
    receipt=json.dumps({
      "gate":"PRE689_NORMAL_EXIT_CORRECTION",
      "status":"PASS_USER_CLARIFICATION_ARCHIVED",
      "context_id":CONTEXT,"backup_id":BACKUP,
      "before_bytes":len(before),"after_bytes":len(after),
      "before_sha256":h(before),"after_sha256":h(after),
      "user_reported_freeze":False,
      "watchdog_is_proof_of_gameplay_hang":False,
      "PRE688_capture_still_pass":True,
      "fps_gain_proven":False,"new_apk":False,
      "github_run_id":os.environ.get("GITHUB_RUN_ID")
    },indent=2,sort_keys=True).encode("utf-8")
    name="NFSMW_PRE689_CONTEXT_USER_EXIT_CORRECTION_"+dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")+".json"
    item=d.files().create(body={"name":name,"parents":[LOGS]},
       media_body=MediaIoBaseUpload(io.BytesIO(receipt),mimetype="application/json"),fields="id,size").execute()
    if h(get(d,item["id"]))!=h(receipt):raise ValueError("PRE689_RECEIPT_READBACK_FAILED")
    print("PRE689_CONTEXT_BACKUP_GUARD=PASS")
    print("PRE689_USER_NORMAL_EXIT_CONTEXT_SYNC=PASS")
    print("PRE689_CONTEXT_READBACK=PASS")
    print("PRE689_PRE688_CAPTURE_STILL_PASS=TRUE")
    print("PRE689_NEW_APK_OR_FPS_GAIN=NONE")
if __name__=="__main__": main()
