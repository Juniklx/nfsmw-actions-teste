#!/usr/bin/env python3
"""PRE683: verify native flag references in signed V51 and the PRE656 log observability gap.
The presence of strings does NOT prove live flags, correct pixel output or FPS improvement.
This script does not mutate source, APK, settings or signing materials.
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

APK_ID="1H3bUAka0s8f7PR0vi2FYj81Pm7uYc6Ws"
APK_SIZE=47104417
APK_SHA="207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b"
LOG_ID="1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd"
LOG_SIZE=576129
LOG_SHA="649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7"
PRIVATE_OUTPUT="1yw1Z83O0d83CoQccjYREYfhxAF17eHD-"
LIBRARIES=("lib/arm64-v8a/libmain.so","lib/arm64-v8a/libmain_usa.so")
FLAGS=(
 "nfsmw_nativo_sin_desenfoque",
 "nfsmw_nativo_pcf_barato",
 "nfsmw_sombras_sin_vegetacion",
 "nfsmw_nativo_sombras_escala",
 "nfsmw_sombras_corte",
)
def sha(b):
    return hashlib.sha256(b).hexdigest()

def evaluate(apk,log):
    if len(apk)!=APK_SIZE or sha(apk)!=APK_SHA:
        raise ValueError("PRE683_APK_PIN_MISMATCH")
    if len(log)!=LOG_SIZE or sha(log)!=LOG_SHA:
        raise ValueError("PRE683_LOG_PIN_MISMATCH")
    libs={}
    with zipfile.ZipFile(io.BytesIO(apk)) as z:
        if z.testzip() is not None:
            raise ValueError("PRE683_APK_ZIP_CRC_FAILURE")
        for name in LIBRARIES:
            binary=z.read(name)
            absent=[flag for flag in FLAGS if flag.encode() not in binary]
            if absent: raise ValueError("PRE683_NATIVE_FLAG_NAMES_MISSING: "+name)
            libs[name]={"size_bytes":len(binary),"sha256":sha(binary),
                        "flag_names_present":list(FLAGS)}
        dex=z.read("classes.dex")
        missing=[flag for flag in FLAGS if ("--"+flag+"=").encode() not in dex]
        if missing: raise ValueError("PRE683_DEX_FLAGS_MISSING: "+",".join(missing))
        dex_sha=sha(dex)
    s=log.decode("utf-8",errors="replace")
    m=re.search(r"\[ajustes\] resolucion interna (\d+x\d+) y limite de FPS (\d+)",s)
    if m is None or m.groups()!=("1920x1080","60"):
        raise ValueError("PRE683_LOG_RESOLUTION_AND_FPS_MISMATCH")
    active_values={flag:bool(re.search(re.escape(flag)+r"\s*[=:]",s)) for flag in FLAGS}
    if any(active_values.values()):
        raise ValueError("PRE683_RUNTIME_LOG_CONTENT_CHANGED_REVIEW_REQUIRED")
    return {
        "gate":"PRE683_V51_NATIVE_GRAPHICS_LOG_OBSERVABILITY",
        "status":"PASS_STATIC_SUPPORT__LIVE_GRAPHICS_FLAGS_NOT_OBSERVED",
        "utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "github_run":os.environ.get("GITHUB_RUN_ID"),
        "pin":{"apk":{"id":APK_ID,"bytes":APK_SIZE,"sha256":APK_SHA},
               "log":{"id":LOG_ID,"bytes":LOG_SIZE,"sha256":LOG_SHA}},
        "apk_zip_crc":"PASS",
        "signed_v51_native_libraries":libs,
        "dex_sha256":dex_sha,
        "dex_argument_names_present":list(FLAGS),
        "pre656_runtime_log":{
          "resolution":"1920x1080","fps_cap":60,
          "explicit_graphics_flag_values_present":active_values,
          "combined_cube_and_blur_timing_bucket_only":"320 (cubo y desenfoque)" in s,
        },
        "limits":{
          "embedded_names_are_not_live_cvar_values":True,
          "pre656_blur_and_shadow_values_proven":False,
          "user_screenshot_is_ui_only":True,
          "android_preferences_accessed":False,
          "runtime_argv_collected":False,
          "pixel_fidelity_proven":False,
          "apk_or_shaders_changed":False,
          "fps_improvement_proven":False,
        },
        "recommended_next_gate":"PRE684: first authenticate exact V51 source and then prepare reversible startup CVar diagnostics; build only with permanent signing certificate, increasing versionCode.",
    }

def drive():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    names=("GOOGLE_REFRESH_TOKEN","GOOGLE_CLIENT_ID","GOOGLE_CLIENT_SECRET")
    missing=[k for k in names if not os.environ.get(k)]
    if missing: raise RuntimeError("PRE683_MISSING_SECRETS="+",".join(missing))
    credentials=Credentials(token=None,refresh_token=os.environ[names[0]],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ[names[1]],client_secret=os.environ[names[2]])
    credentials.refresh(Request())
    return build("drive","v3",credentials=credentials,cache_discovery=False)

def download(d,id):
    from googleapiclient.http import MediaIoBaseDownload
    out=io.BytesIO()
    dl=MediaIoBaseDownload(out,d.files().get_media(fileId=id),chunksize=4*1024*1024)
    done=False
    while not done: _,done=dl.next_chunk()
    return out.getvalue()

def main():
    from googleapiclient.http import MediaFileUpload
    d=drive()
    result=evaluate(download(d,APK_ID),download(d,LOG_ID))
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre683_") as td:
        name="NFSMW_PRE683_V51_NATIVE_GRAPHICS_"+stamp+".zip"
        archive=Path(td)/name
        with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("PRE683_REPORT.json",json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
            z.writestr("PRE683_SUMMARY.md",
                "PRE683: Binary references for graphic flags confirmed in real V51 APK.\n"
                "The PRE656 log does not expose the live blur, PCF or vegetation-shadow values.\n"
                "No patch, APK, signature, game data or FPS benchmark changes.\n")
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None: raise ValueError("PRE683_OUTPUT_ZIP_BAD_CRC")
        uploaded=d.files().create(body={"name":name,"parents":[PRIVATE_OUTPUT]},
            media_body=MediaFileUpload(str(archive),mimetype="application/zip",resumable=True),
            fields="id,size").execute()
        if uploaded.get("size")!=str(archive.stat().st_size):
            raise ValueError("PRE683_DRIVE_UPLOAD_SIZE_MISMATCH")
        if sha(download(d,uploaded["id"]))!=sha(archive.read_bytes()):
            raise ValueError("PRE683_DRIVE_READBACK_MISMATCH")
    print("PRE683_V51_NATIVE_BINARY_GRAPHICS_FLAGS=PASS")
    print("PRE683_V51_DEX_GRAPHICS_ARGUMENT_NAMES=PASS")
    print("PRE683_PRE656_RUNTIME_EFFECT_FLAG_VALUES=NOT_OBSERVED")
    print("PRE683_PRIVATE_DRIVE_READBACK=PASS")
    print("PRE683_NEW_APK_OR_FPS_GAIN=NONE")

if __name__=="__main__":
    main()
