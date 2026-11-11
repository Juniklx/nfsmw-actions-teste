#!/usr/bin/env python3
"""PRE685: audit actual V51 PRE656 Swap interval histograms without building an APK.

Private log remains on transient runner and in private Drive. Histogram buckets
are engine Swap observations, NOT display frame-present timestamps, nor exact
percentiles or a benchmark of user-perceived smoothness.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
import zipfile

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

LOG_FILE_ID="1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd"
LOG_SHA256="649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7"
LOG_BYTES=576129
OUTPUT_FOLDER="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
BUCKETS=("<15 ms","15-18","18-25","25-30","30-36","36-50","50-60",
         "60-75","75-100","100-150",">=150")
HIST_MARK="C2: intervalos entre Swaps:"
PRESENT_MARK="C2: copias="
HIST_RE=re.compile(r"^(.+?); peor fotograma ([0-9]+(?:\.[0-9]+)?) ms; trabajos solapados en la GPU (\d+)$")
STAMP=re.compile(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d{3})\]")
CONTEXT_RE=re.compile(r"\[contexto\] (conduciendo|cinematica|menus)\b")
GPUTIME_RE=re.compile(r"GPU ([0-9]+(?:\.[0-9]+)?) ms por Swap")
CAP_RE=re.compile(r"\[ajustes\] resolucion interna (\d+x\d+) y limite de FPS (\d+): modo de video (\d+x\d+) a ([0-9.]+) Hz")
ANISO_RE=re.compile(r"filtrado anisotropico (\d+) en los samplers lineales con mips")

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def timestamp(line):
    match=STAMP.match(line)
    if not match:
        raise ValueError("PRE685_LOG_TIMESTAMP_FORMAT")
    # This is wall time in the original log; no display clock synchronization proven.
    return datetime.strptime(match.group(1),"%Y-%m-%d %H:%M:%S.%f")

def parse_hist(line):
    payload=line.split(HIST_MARK,1)[1].strip()
    matched=HIST_RE.fullmatch(payload)
    if not matched:
        raise ValueError("PRE685_HISTOGRAM_SCHEMA_MISMATCH")
    pieces=matched.group(1).split(" | ")
    if len(pieces)!=len(BUCKETS):
        raise ValueError("PRE685_UNEXPECTED_BUCKET_COUNT")
    parsed={}
    for expected,piece in zip(BUCKETS,pieces):
        name,number=piece.rsplit(" ",1)
        if name!=expected or not number.isdigit():
            raise ValueError("PRE685_UNEXPECTED_BUCKET_NAME_OR_VALUE")
        parsed[name]=int(number)
    return parsed,float(matched.group(2)),int(matched.group(3))

def analyze(raw):
    if len(raw)!=LOG_BYTES or sha(raw)!=LOG_SHA256:
        raise ValueError("PRE685_ORIGINAL_LOG_PIN_MISMATCH")
    lines=raw.decode("utf-8","replace").splitlines()
    hist=[line for line in lines if HIST_MARK in line]
    presentation=[line for line in lines if PRESENT_MARK in line and "presentados=" in line]
    contexts=[]
    for line in lines:
        m=CONTEXT_RE.search(line)
        if m:
            contexts.append((timestamp(line),m.group(1)))
    if len(hist)!=7 or len(presentation)!=7:
        raise ValueError("PRE685_EXPECTED_7_C2_SNAPSHOTS")
    if len(contexts)<4:
        raise ValueError("PRE685_CONTEXT_TRANSITIONS_MISSING")
    cap=[m for line in lines for m in [CAP_RE.search(line)] if m]
    if len(cap)!=1 or cap[0].groups()!=("1920x1080","60","1280x720","60.000000"):
        raise ValueError("PRE685_RESOLUTION_AND_FPS_PIN_MISMATCH")
    presenter=[line for line in lines if "VulkanPresenter: Created" in line]
    if len(presenter)!=1 or not all(t in presenter[0] for t in ("1920x1080","presentation mode 1 (MAILBOX)","4 images requested")):
        raise ValueError("PRE685_PRESENTER_INFO_UNEXPECTED")
    vsync=[line for line in lines if "vsync implicito no" in line]
    if not vsync:
        raise ValueError("PRE685_VSYNC_IMPLICIT_OBSERVABILITY_MISSING")
    aniso=any(ANISO_RE.search(line) and int(ANISO_RE.search(line).group(1))==16 for line in lines)
    windows=[]
    previous=None
    for index,(hline,pline) in enumerate(zip(hist,presentation)):
        htime=timestamp(hline)
        ptime=timestamp(pline)
        if abs((htime-ptime).total_seconds())>0.020:
            raise ValueError("PRE685_HIST_PRESENT_MISALIGNED")
        counts,worst,overlap=parse_hist(hline)
        m=re.search(r"presentados=(\d+)",pline)
        gm=GPUTIME_RE.search(pline)
        if not m or not gm:
            raise ValueError("PRE685_PRESENTATION_COUNTER_MISSING")
        current=int(m.group(1))
        expected=current-previous["counter"] if previous else current-1
        total=sum(counts.values())
        if total!=expected:
            raise ValueError("PRE685_BUCKET_COUNT_VS_COUNTER_MISMATCH")
        elapsed=(htime-previous["timestamp"]).total_seconds() if previous else None
        estimated_fps=round(expected/elapsed,3) if elapsed is not None else None
        time_start=previous["timestamp"] if previous else timestamp(lines[0])
        transitions=[kind for t,kind in contexts if time_start<t<=htime]
        active_before=[kind for t,kind in contexts if t<=time_start]
        state=active_before[-1] if active_before else "unknown"
        if transitions:
            state="mixed_transition"
        after_25=sum(counts[name] for name in BUCKETS[3:])
        windows.append({
            "window":index+1,
            "ending_log_time":htime.isoformat(sep=" "),
            "duration_since_previous_snapshot_s":round(elapsed,3) if elapsed is not None else None,
            "presentados_cumulative":current,
            "swap_intervals":total,
            "fps_estimated_from_cumulative_counter":estimated_fps,
            "engine_scene_state":state,
            "bucket_counts":counts,
            "share_15_18_pct":round(100*counts["15-18"]/total,3),
            "over_25_ms_intervals":after_25,
            "worst_engine_frame_ms":worst,
            "gpu_per_swap_aggregated_ms":float(gm.group(1)),
            "gpu_overlap_jobs":overlap,
        })
        previous={"counter":current,"timestamp":htime}
    if [w["swap_intervals"] for w in windows]!=[1062,1186,1200,1201,1200,1200,1201]:
        raise ValueError("PRE685_UNEXPECTED_PER_WINDOW_COUNTS")
    # Windows 3-7 have no >25ms inter-Swap observations in this capture.
    post_warmup=windows[2:]
    # Last two 20s snapshots are entirely after 08:55:37, when gameplay resumed.
    driving=windows[-2:]
    if not all(w["engine_scene_state"]=="conduciendo" for w in driving):
        raise ValueError("PRE685_LAST_TWO_WINDOWS_NOT_GAMEPLAY")
    def summary(group):
        count=sum(w["swap_intervals"] for w in group)
        bins={key:sum(w["bucket_counts"][key] for w in group) for key in BUCKETS}
        return {
            "windows":[w["window"] for w in group],
            "interval_count":count,
            "bucket_counts":bins,
            "15_to_18ms_count":bins["15-18"],
            "15_to_18ms_percent":round(100*bins["15-18"]/count,3),
            "over_25ms_count":sum(bins[k] for k in BUCKETS[3:]),
            "above_18ms_count":sum(bins[k] for k in BUCKETS[2:]),
        }
    five=summary(post_warmup)
    two=summary(driving)
    if five["interval_count"]!=6002 or five["15_to_18ms_count"]!=5784 or five["over_25ms_count"]!=0:
        raise ValueError("PRE685_STABLE_WINDOW_INTEGRITY_FAILED")
    if two["interval_count"]!=2401 or two["over_25ms_count"]!=0:
        raise ValueError("PRE685_GAMEPLAY_WINDOW_INTEGRITY_FAILED")
    return {
        "gate":"PRE685_SIGNED_V51_PRE656_SWAP_INTERVAL_AUDIT",
        "status":"PASS_ENGINE_SWAP_HISTOGRAMS__DISPLAY_PRESENTATION_UNVERIFIED",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "github_run_id":os.environ.get("GITHUB_RUN_ID"),
        "input":{"private_log_id":LOG_FILE_ID,"size":len(raw),"sha256":sha(raw)},
        "scene_transitions":[{"time":t.isoformat(sep=" "),"state":state} for t,state in contexts],
        "launch":{"internal_resolution":"1920x1080","fps_limit":60,
                  "selected_video_mode":"1280x720 @ 60 Hz",
                  "vulkan_swapchain":"1920x1080",
                  "present_mode":"MAILBOX",
                  "swapchain_images_requested":4,
                  "presenter_log_explicitly_says_no_implicit_vsync":True,
                  "anisotropic_16x_line_observed":aniso},
        "windows":windows,
        "last_five_windows":five,
        "last_two_gameplay_windows":two,
        "limits":{
            "engine_histograms_are_not_android_surfaceflinger_present_timestamps":True,
            "individual_swap_timestamps_available":False,
            "exact_percentiles_or_frame_pacing_at_screen_computed":False,
            "30fps_feeling_in_other_sessions_ruled_out":False,
            "mobile_cvars_for_blur_or_shadows_observed":False,
            "apk_built_or_patched":False,
            "graphics_or_thermal_settings_modified":False,
            "fps_gain_claimed":False,
        },
        "next_gate":"Collect actual Android frame-present timing and a new game log in same session; no APK or shader changes before comparing.",
    }

def google_drive():
    names=("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET")
    missing=[x for x in names if not os.environ.get(x)]
    if missing:
        raise RuntimeError("PRE685_MISSING_SECRET_NAMES: "+",".join(missing))
    cred=Credentials(token=None,refresh_token=os.environ[names[0]],
        client_id=os.environ[names[1]],client_secret=os.environ[names[2]],
        token_uri="https://oauth2.googleapis.com/token")
    cred.refresh(Request())
    return build("drive","v3",credentials=cred,cache_discovery=False)

def fetch(drive,file_id):
    output=io.BytesIO()
    dl=MediaIoBaseDownload(output,drive.files().get_media(fileId=file_id),chunksize=4*1024*1024)
    done=False
    while not done:
        _,done=dl.next_chunk()
    return output.getvalue()

def main():
    drive=google_drive()
    report=analyze(fetch(drive,LOG_FILE_ID))
    stamp=datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre685_") as td:
        path=Path(td)/("NFSMW_PRE685_V51_SWAP_PACING_"+stamp+".zip")
        csv_io=io.StringIO()
        fieldnames=["window","ending_log_time","engine_scene_state","duration_since_previous_snapshot_s",
                    "presentados_cumulative","swap_intervals","fps_estimated_from_cumulative_counter",
                    "share_15_18_pct","over_25_ms_intervals","worst_engine_frame_ms",
                    "gpu_per_swap_aggregated_ms","gpu_overlap_jobs"]+list(BUCKETS)
        writer=csv.DictWriter(csv_io,fieldnames=fieldnames,lineterminator="\n")
        writer.writeheader()
        for w in report["windows"]:
            data={field:w.get(field) for field in fieldnames if field not in BUCKETS}
            data.update(w["bucket_counts"])
            writer.writerow(data)
        markdown=(
          "# PRE685 — histogramas de Swaps (V51 PRE656)\n\n"
          "Nos cinco intervalos finais de cerca de 20 segundos, "
          "5784 dos 6002 intervalos entre Swaps ficaram em 15-18 ms; "
          "nenhum ultrapassou 25 ms.\n\n"
          "Nas ultimas duas janelas inteiramente posteriores ao retorno "
          "a jogabilidade, os 2401 intervalos tambem ficaram ate 25 ms.\n\n"
          "O log informa Vulkan MAILBOX, quatro imagens solicitadas, 1080p, "
          "cap de 60 FPS e ausencia de VSync implicito. Sao observacoes do "
          "motor, nao provas dos instantes de exibicao na tela Android.\n\n"
          "Sem nova APK, patch, assinatura, reducao grafica ou ganho FPS.\n"
        )
        with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("PRE685_REPORT.json",json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False))
            z.writestr("PRE685_WINDOW_HISTOGRAMS.csv",csv_io.getvalue())
            z.writestr("PRE685_README.md",markdown)
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                raise ValueError("PRE685_OUTPUT_ZIP_BAD_CRC")
        saved=drive.files().create(
            body={"name":path.name,"parents":[OUTPUT_FOLDER]},
            media_body=MediaFileUpload(str(path),mimetype="application/zip",resumable=True),
            fields="id,size").execute()
        if saved.get("size")!=str(path.stat().st_size):
            raise ValueError("PRE685_PRIVATE_UPLOAD_SIZE_MISMATCH")
        if sha(fetch(drive,saved["id"]))!=sha(path.read_bytes()):
            raise ValueError("PRE685_PRIVATE_DRIVE_READBACK_MISMATCH")
    print("PRE685_AUTHENTIC_PRE656_LOG_SHA256=PASS")
    print("PRE685_SWAP_HISTOGRAM_7_WINDOWS=PASS")
    print("PRE685_LAST_FIVE_WINDOWS_6002_SWAPS=PASS")
    print("PRE685_LAST_TWO_GAMEPLAY_WINDOWS_2401_SWAPS=PASS")
    print("PRE685_PRIVATE_REPORT_SHA256_READBACK=PASS")
    print("PRE685_ANDROID_DISPLAY_FRAME_TIMESTAMPS=NOT_OBSERVED")
    print("PRE685_NEW_APK_PATCH_OR_FPS_GAIN=NONE")

if __name__=="__main__":
    main()
