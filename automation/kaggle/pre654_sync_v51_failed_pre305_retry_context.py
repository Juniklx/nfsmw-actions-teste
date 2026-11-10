#!/usr/bin/env python3
"""PRE654: audited append-only canonical Drive checkpoint.
A PRE652 dispatch is NOT an approved signed APK; do not invent its outcome.
Back up bytes first, abort on any changed concurrent context or provenance.
"""
from __future__ import annotations
import argparse,hashlib,io,json,time
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

EXPECTED_BYTES=1035702
EXPECTED_SHA="6c1e7b5c201b30b63295886e1c0cf4ef29827a6cd69fd6b4241e41c76ff714c1"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE654_PRE652_RETRY_20261110.md"
HANDOFF=Path("docs/PRE654_V51_PRE652_FAILURE_FIX_RETRY_IN_PROGRESS_20261110.md")
PRE651=Path("docs/PRE651_V51_GPU_RELEASE_PREFLIGHT_VERIFIED.json")
BUILD=Path("automation/kaggle/pre652_build_signed_v51_gpu_shader_counts_diag.py")
MARKER=b"# PRE654 "
OUT=Path("/tmp/nfsmw-pre654/context_result.json")
def sha(b):return hashlib.sha256(b).hexdigest()

def evidence():
    r=json.loads(PRE651.read_text(encoding="utf-8"))
    required=(r.get("stage")=="PRE651_V51_GPU_RELEASE_PREFLIGHT"
       and r.get("status")=="AUDIT_OK_NO_APK"
       and r.get("github_run_id")=="42798605525"
       and r.get("zip_sha256")=="1ecba3e5c7fef96c073d272d56c3f3bf9ca924338e4f8e94e5fd03a66a0ab305"
       and r.get("archive_drive_id")=="17doJ3BNHwxHeClS-LpqvBVcny-sfwQVN"
       and r.get("target_version_code")==51
       and r.get("package_id")=="io.github.nfsmwrecomp"
       and r.get("certificate_sha256")=="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
       and r.get("preflight_approved") is True
       and r.get("apk_built") is False
       and r.get("signing_material_accessed") is False
       and r.get("fps_gain_proven") is False
       and sha(BUILD.read_bytes())==r.get("checks",{}).get("pre652_builder_sha256"))
    if not required:raise ValueError("PRE654 PRE651 evidence or signed V51 recipe changed")
    content=HANDOFF.read_bytes()
    if not (content.count(MARKER)==1
       and 3500<len(content)<12000
       and b"42798605525" in content
       and b"42798909503" in content
       and b"SEM resultado confirmado" in content
       and b"17doJ3BNHwxHeClS-LpqvBVcny-sfwQVN" in content):
        raise ValueError("PRE654 handoff incomplete or improperly claims a signed V51")
    return b"\n\n---\n\n"+content

def audit():
    appendix=evidence()
    drive=drive_client()
    meta=get_meta(drive)
    if not (meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
        and meta.get("parents")==[PARENT] and meta.get("mimeType")=="text/markdown"):
        raise ValueError("PRE654 unexpected canonical Drive identity")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):
        raise ValueError("PRE654 Drive metadata size mismatch")
    if MARKER in before:
        if not (before.count(MARKER)==1
          and before.endswith(appendix)
          and len(before)-len(appendix)==EXPECTED_BYTES
          and sha(before[:-len(appendix)])==EXPECTED_SHA):
            raise ValueError("PRE654 conflicting prior append, no write")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
          "canonical_sha256":sha(before),"canonical_bytes":len(before),
          "readback_identical":True}
    if (len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA
        or before.count(b"# PRE653 ")!=1):
        raise ValueError("PRE654 canonical bytes unexpectedly changed; no overwrite")
    target=before+appendix
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},
       fields="id,name,size,parents").execute()
    backup_id=backup["id"]
    if int(backup.get("size",-1))!=EXPECTED_BYTES or get_bytes(drive,backup_id)!=before:
        raise ValueError("PRE654 backup not byte-identical")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("PRE654 canonical context modified before append")
    for attempt in range(3):
        current=get_bytes(drive,FILE_ID)
        if current==target:break
        if current!=before:raise ValueError("PRE654 concurrent update during append")
        try:
            drive.files().update(fileId=FILE_ID,supportsAllDrives=True,
              media_body=MediaIoBaseUpload(io.BytesIO(target),
                 mimetype="text/markdown",resumable=False),
              fields="id,name,size,modifiedTime").execute()
        except HttpError as exc:
            if exc.resp.status not in (500,502,503,504) or attempt==2:raise
            if get_bytes(drive,FILE_ID)==target:break
            time.sleep(2*(attempt+1))
    after=get_bytes(drive,FILE_ID)
    if not (after==target
      and after.startswith(before)
      and after.count(MARKER)==1):
        raise ValueError("PRE654 canonical context readback mismatch")
    return {"status":"AUDIT_OK","backup_created":True,
      "backup_file_id":backup_id,"original_sha256":sha(before),
      "canonical_sha256":sha(after),"canonical_bytes":len(after),
      "readback_identical":True,"prefix_history_unchanged":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,
        "error_summary":str(e)[:170] if isinstance(e,ValueError) else "Drive backup/read/write error"}
    r.update({"stage":"PRE654_V51_PREFLIGHT_CONTEXT","run_id":args.run_id,
      "utc":datetime.now(timezone.utc).isoformat(),
      "apk_built":False,"signing_material_accessed":False,"user_saves_modified":False})
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    for key,v in (
      ("STATUS",r["status"]),
      ("CANONICAL_SHA256",r.get("canonical_sha256","none")),
      ("BACKUP_CREATED",r.get("backup_created",False)),
      ("READBACK_IDENTICAL",r.get("readback_identical",False)),
      ("ERROR_TYPE",r.get("error_type","none"))):
        print("PRE654_"+key+"="+str(v))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1

if __name__=="__main__":raise SystemExit(main())
