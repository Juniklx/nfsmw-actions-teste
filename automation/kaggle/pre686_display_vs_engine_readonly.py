#!/usr/bin/env python3
"""PRE686: replay SurfaceFlinger and gameplay-log verification using private Drive.
Does not publish logs in the public GitHub repo or modify release artifacts.
"""
import datetime as dt
import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

SF_ID="1TF6_N3Vt1resirvtlvx5ei2dpFXY7im3"
LOG_ID="1BTs-Xf680UGlnVpRPC6nwT4RG7Yq_OAR"
DESTINATION="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
SF_SHA="50f94cfe3b91c19f36312b6d00054fa292fb43050d0529745c40dc0ebe2421e8"
LOG_SHA="2bf6a248629d124904049faa4aa55f4e230639d620a2a752509898c857b26ef4"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def get_bytes(d,fid):
    stream=io.BytesIO()
    dl=MediaIoBaseDownload(stream,d.files().get_media(fileId=fid),chunksize=4*1024*1024)
    done=False
    while not done:
        _,done=dl.next_chunk()
    return stream.getvalue()

def audit(sf_raw,log_raw):
    if len(sf_raw)!=23998 or sha(sf_raw)!=SF_SHA:
        raise ValueError("PRE686_SURFACEFLINGER_PIN_MISMATCH")
    if len(log_raw)!=1083737 or sha(log_raw)!=LOG_SHA:
        raise ValueError("PRE686_GAME_LOG_PIN_MISMATCH")
    sf=sf_raw.decode("utf-8")
    log=log_raw.decode("utf-8","replace")
    start=re.search(r"COLLECTION_START=([^\n]+)",sf)
    stop=re.search(r"COLLECTION_END=([^\n]+)",sf)
    layer=re.search(r"layerName = ([^\n]*SurfaceView\[io\.github\.nfsmwrecomp/[^\n]*)\ntotalFrames = (\d+)\naverageFPS = ([\d.]+)\n",sf)
    if not start or not stop or not layer:
        raise ValueError("PRE686_MISSING_CAPTURE_OR_GAME_SURFACEVIEW")
    name,frames_raw,fps_raw=layer.groups()
    frames=int(frames_raw)
    fps=float(fps_raw)
    if frames!=19672 or round(fps,3)!=61.918:
        raise ValueError("PRE686_SURFACEVIEW_FPS_OR_COUNT_CHANGED")
    hist=[]
    for line in sf[layer.end():].splitlines():
        if not re.fullmatch(r"(?:\d+ms=\d+\s*)+",line):
            break
        values={int(k):int(v) for k,v in re.findall(r"(\d+)ms=(\d+)",line)}
        n=sum(values.values())
        avg=sum(k*v for k,v in values.items())/n
        hist.append((values,n,avg))
    if len(hist)!=7:
        raise ValueError("PRE686_HISTOGRAM_COUNT_CHANGED")
    # PRE686 Termux collector incorrectly removed the histogram label lines.
    # Identify present2present uniquely by agreement with reported averageFPS.
    candidates=[i for i,(values,n,avg) in enumerate(hist)
        if n==frames and round(1000/avg,3)==fps]
    if candidates!=[0]:
        raise ValueError("PRE686_PRESENT2PRESENT_UNIDENTIFIABLE")
    values,n,avg=hist[0]
    if any(values.get(k)!=v for k,v in {8:1943,16:15698,24:770,25:999,33:52}.items()):
        raise ValueError("PRE686_PRESENT2PRESENT_BUCKETS_CHANGED")
    if "PRE686_MATCHED_NFSMW_LAYERS=5" not in sf:
        raise ValueError("PRE686_MATCHED_LAYER_COUNT_UNEXPECTED")
    if log.count("[ajustes] resolucion interna 1920x1080 y limite de FPS 60")!=1:
        raise ValueError("PRE686_GAME_1080P_CAP60_MISSING")
    if "VulkanPresenter: Created 1920x1080 swapchain" not in log or "presentation mode 1 (MAILBOX), 4 images requested" not in log:
        raise ValueError("PRE686_GAME_MAILBOX_SIGNATURE_MISSING")
    records=[]
    for m in re.finditer(r"^\[([^\]]+)\].*C2: copias=.*presentados=(\d+).*GPU ([\d.]+) ms por Swap",log,re.M):
        records.append((dt.datetime.fromisoformat(m.group(1)),int(m.group(2)),float(m.group(3))))
    if len(records)!=16 or records[0][1]!=1067 or records[-1][1]!=19060:
        raise ValueError("PRE686_GAME_C2_COUNTER_MISMATCH")
    means=[]
    for prev,cur in zip(records,records[1:]):
        dt_seconds=(cur[0]-prev[0]).total_seconds()
        means.append(round((cur[1]-prev[1])/dt_seconds,4))
    if any(not 59.9 <= f <= 60.1 for f in means[2:]):
        raise ValueError("PRE686_STABLE_MOTOR_FPS_OUTSIDE_PINNED_RANGE")
    if "[contexto] conduciendo (estado 6, tipo 0 por atributo)" not in log or "[contexto] cinematica" not in log:
        raise ValueError("PRE686_GAME_CONTEXT_MISSING")
    if "2026-11-10 22:47:22.577" not in log:
        raise ValueError("PRE686_GAMEPLAY_CONTEXT_TRANSITION_MISSING")
    return {
        "gate":"PRE686_S24FE_DISPLAY_VS_ENGINE_FRAME_PACING",
        "status":"PASS_REAL_GAME_LOG_AND_SURFACEFLINGER_LAYER_AUDIT",
        "source":{"surfaceflinger_id":SF_ID,"surfaceflinger_sha256":SF_SHA,
                  "game_log_id":LOG_ID,"game_log_sha256":LOG_SHA},
        "capture":{"start":start.group(1),"end":stop.group(1),
                   "surface_name":name,"layer_total_frames":frames,
                   "surfaceflinger_average_fps":fps,
                   "present_histogram_index_without_labels":0,
                   "present_histogram_weighted_fps":round(1000/avg,3)},
        "present_to_present_counts":{"8ms":values[8],"16ms":values[16],"24ms":values[24],
                                     "25ms":values[25],"33ms":values[33],
                                     "8_plus_24_25":values[8]+values[24]+values[25],
                                     "8_plus_24_25_percent":round(100*(values[8]+values[24]+values[25])/n,3)},
        "engine":{"internal_resolution":"1920x1080","fps_cap":60,
                  "vulkan_present":"MAILBOX","c2_windows":len(records),
                  "first_counter":records[0][1],"last_counter":records[-1][1],
                  "last_engine_gpu_ms_per_swap":records[-1][2],
                  "c2_pairwise_fps":means},
        "limits":{
            "collector_stripped_histogram_labels":True,
            "cannot_locate_irregular_intervals_in_gameplay_period":True,
            "cannot_infer_interval_temporal_order":True,
            "display_120hz_mode_directly_observed":False,
            "thermals_and_display_refreshrate_not_collected":True,
            "fps_gain_proven":False,
            "new_apk_built_or_signed":False},
        "next":"PRE687 labeled present-to-present time-scoped stationary gameplay capture; require matching game log and no thermal bypass."
    }

def main():
    names=["GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET"]
    if any(not os.environ.get(n) for n in names):
        raise ValueError("PRE686_MISSING_GOOGLE_OAUTH_SECRET")
    cred=Credentials(token=None,refresh_token=os.environ[names[0]],
        client_id=os.environ[names[1]],client_secret=os.environ[names[2]],
        token_uri="https://oauth2.googleapis.com/token")
    cred.refresh(Request())
    d=build("drive","v3",credentials=cred,cache_discovery=False)
    report=audit(get_bytes(d,SF_ID),get_bytes(d,LOG_ID))
    report["github_run_id"]=os.environ.get("GITHUB_RUN_ID")
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/("NFSMW_PRE686_ACTIONS_DISPLAY_VS_ENGINE_"+stamp+".zip")
        with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("PRE686_REPORT.json",json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2))
            archive.writestr("PRE686_README.md",
                "# PRE686 — auditoria read-only\n\n"
                "Arquivo privado, sem logs brutos.\n\n"
                "Os intervalos de apresentacao da SurfaceView incluem 1943 de ~8ms, "
                "15698 de ~16ms e 1769 de ~24-25ms. "
                "O motor registra ~60FPS estaveis nas janelas C2 posteriores.\n\n"
                "O histograma nao preserva ordem nem permite atribuir os intervalos "
                "ao carro parado; nao confirma refresh real a 120Hz.\n"
                "Nao houve alteracao de APK, fonte ou assinatura.\n")
        with zipfile.ZipFile(p) as archive:
            if archive.testzip() is not None:
                raise ValueError("PRE686_ZIP_CRC_FAIL")
        metadata=d.files().create(
            body={"name":p.name,"parents":[DESTINATION]},
            media_body=MediaFileUpload(str(p),mimetype="application/zip",resumable=True),
            fields="id,size").execute()
        if str(p.stat().st_size)!=metadata.get("size") or sha(get_bytes(d,metadata["id"]))!=sha(p.read_bytes()):
            raise ValueError("PRE686_PRIVATE_UPLOAD_READBACK_MISMATCH")
    print("PRE686_REAL_LOG_AND_SURFACEFLINGER_PINS=PASS")
    print("PRE686_PRESENT_TO_PRESENT_IDENTIFIED_BY_REPORTED_AVERAGE_FPS=PASS")
    print("PRE686_8_16_24MS_MODALITY_OBSERVED=TRUE")
    print("PRE686_120HZ_DISPLAY_MODE_DIRECTLY_OBSERVED=FALSE")
    print("PRE686_PRIVATE_DRIVE_REPORT_SHA256_READBACK=PASS")
    print("PRE686_NEW_APK_PATCH_OR_FPS_GAIN=NONE")

if __name__=="__main__":
    main()
