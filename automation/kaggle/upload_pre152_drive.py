#!/usr/bin/env python3
"""PRE152: upload three verified diagnostic files to Drive, without replacements."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, sys

FOLDER="1tmIzbpCbTQrNT59p0tWHiW_KdGGpHCCB"
FILES=[
("scripts/nfsmw_pre152_v31_surfaceflinger_pareado.sh","18324df2bfd8cff12e982262a93b294e97e1c0bf91d9f01360e7bdfc00c08ba4","text/plain"),
("scripts/nfsmw_pre152_analisar_timestats.py","dbf57fee9458e9ed2cdc9165851bf57e6e63a461dafa412391d7d72f259f8e27","text/plain"),
("reports/RELATORIO_NFSMW_PRE152_AUDITORIA_SF_V31_E_PREPARO_COLETA_20261104.md","4a170ac2409f70decadf7443d8ed414010ecbab1e25161212c80f166395a64e0","text/markdown"),
]
RESULT=Path("/tmp/nfsmw_pre152_drive_upload.json")
state={"stage":"PRE152_DRIVE_PUBLICATION","status":"FAILED","folder_id":FOLDER,"files":[],"apk_modified":False,"secrets_logged":False}
try:
    for path, expected, _ in FILES:
        actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        if actual!=expected:raise ValueError("source bytes do not match expected checksums")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    auth=Credentials(token=None,refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"])
    auth.refresh(Request())
    drive=build("drive","v3",credentials=auth,cache_discovery=False)
    folder=drive.files().get(fileId=FOLDER,fields="id,name,mimeType",supportsAllDrives=True).execute()
    if folder.get("name")!="03_Scripts_e_Patches" or folder.get("mimeType")!="application/vnd.google-apps.folder":
        raise ValueError("wrong Drive folder")
    for path, expected, mime in FILES:
        name=Path(path).name
        row={"name":name,"sha256":expected,"status":"PENDING"}
        state["files"].append(row)
        q="name = '"+name+"' and '"+FOLDER+"' in parents and trashed = false"
        objects=drive.files().list(q=q,fields="files(id,name)",supportsAllDrives=True,
            includeItemsFromAllDrives=True,page_size=100).execute().get("files",[])
        if len(objects)>1:raise ValueError("duplicate target files")
        if objects:
            file_id=objects[0]["id"]
            row["status"]="VERIFY_EXISTING"
        else:
            created=drive.files().create(body={"name":name,"parents":[FOLDER],"mimeType":mime},
                media_body=MediaFileUpload(path,mimetype=mime,resumable=False),
                fields="id",supportsAllDrives=True).execute()
            file_id=created["id"]
            row["status"]="VERIFY_NEW"
        row["file_id"]=file_id
        fetched=drive.files().get_media(fileId=file_id,supportsAllDrives=True).execute()
        if isinstance(fetched,str):fetched=fetched.encode("utf-8")
        if hashlib.sha256(fetched).hexdigest()!=expected:
            raise ValueError("Drive byte readback mismatch")
        row["status"]="VERIFIED"
    state["status"]="THREE_VERIFIED"
except Exception as exc:
    state["error_type"]=type(exc).__name__
    response=getattr(exc,"resp",None)
    state["http_status"]=getattr(response,"status",None)
finally:
    state["time_utc"]=datetime.now(timezone.utc).isoformat()
    RESULT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE152 Drive result:",state["status"],state.get("error_type"),state.get("http_status"))
sys.exit(0 if state["status"]=="THREE_VERIFIED" else 1)
