#!/usr/bin/env python3
"""PRE650: strict backup-first append-only Drive canonical context from verified GPU gates.
No game code, APK, signing key, secrets, thermal setting or saves are accessed.
"""
from __future__ import annotations
import argparse, hashlib, io, json, time
from datetime import datetime, timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

PRE_BYTES=1026112
PRE_SHA="57d51a0d1f682d67ffdfb6960a49ab5309d42c40cbb87cfa71080be252be5442"
HANDOFF=Path("docs/PRE650_CONTEXT_PRE648_PRE649_GPU_GATES_VERIFIED_20261110.md")
PRE649=Path("docs/PRE649_V50_GPU_COUNTER_HOST_OVERHEAD_VERIFIED.json")
MARKER=b"# PRE650 "
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE650_PRE648_PRE649_GPU_20261110.md"
OUT=Path("/tmp/nfsmw-pre650/context_result.json")
def sha(b):return hashlib.sha256(b).hexdigest()

def check_evidence():
    result=json.loads(PRE649.read_text("utf-8"))
    previous=result.get("previous_gate",{})
    checks=result.get("host_checks",{})
    if not (
       result.get("status")=="AUDIT_OK_HOST_ONLY"
       and result.get("github_run_id")==42794598045
       and result.get("github_artifact_id")==13752133509
       and result.get("zip_sha256")=="33fb20d059a82b2ecc82ea8f074a86a2a4d16ae48d3f1971c4ed64040e7129b5"
       and previous.get("PRE648_run_id")==42764731926
       and previous.get("status")=="AUDIT_OK"
       and previous.get("arm64_libmain_sha256")=="214ff9b9e41ab823f4a78f172199eee330f23257eb44e65a22fdb174bd2cbb1e"
       and checks.get("static_observer_passed") is True
       and checks.get("asan_ubsan_passed") is True
       and checks.get("host_invariants_passed") is True
       and checks.get("estimated_counter_bytes")==1638400
       and result.get("limits",{}).get("android_gpu_measured") is False
       and result.get("limits",{}).get("fps_gain_proven") is False
    ):
        raise ValueError("PRE650 pinned GPU evidence invalid")
    appendix=HANDOFF.read_bytes()
    for term in [b"# PRE650 ",b"42764731926",b"42794598045",
        b"214ff9b9e41ab823f4a78f172199eee330f23257eb44e65a22fdb174bd2cbb1e",
        b"1BnK_QBzOrzALsMsQjEI6-kzLyYmA4_dp",
        b"1W1pxH9rud_uRDXZbvA-h6op_8XVTuTTF"]:
        if term not in appendix:raise ValueError("PRE650 required handoff evidence missing")
    if not (3000<len(appendix)<9000 and appendix.count(MARKER)==1):
        raise ValueError("PRE650 handoff size/uniqueness invalid")
    return b"\n\n---\n\n"+appendix

def audit():
    appendix=check_evidence()
    drive=drive_client()
    meta=get_meta(drive)
    if not (meta.get("id")==FILE_ID
       and meta.get("name")=="CONTEXTO_NFSMW.md"
       and meta.get("mimeType")=="text/markdown"
       and meta.get("parents")==[PARENT]):
        raise ValueError("PRE650 unexpected canonical context identity")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):raise ValueError("PRE650 metadata byte count mismatch")
    if MARKER in before:
        if not (before.endswith(appendix)
           and before.count(MARKER)==1
           and len(before)-len(appendix)==PRE_BYTES
           and sha(before[:-len(appendix)])==PRE_SHA):
            raise ValueError("PRE650 already exists but bytes not exactly idempotent")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
          "canonical_sha256":sha(before),"canonical_bytes":len(before),
          "readback_identical":True}
    if len(before)!=PRE_BYTES or sha(before)!=PRE_SHA:
        raise ValueError("PRE650 canonical hash or size diverged: aborting append")
    if before.count(b"# PRE648 ")!=1 or before.count(b"# PRE647 ")!=1:
        raise ValueError("PRE650 missing preceding audited checkpoints")
    expected=before+appendix
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},
       fields="id,name,size,parents").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=PRE_BYTES
      or get_bytes(drive,backup_id)!=before):
        raise ValueError("PRE650 backup mismatch: original remains untouched")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("PRE650 context changed concurrently: aborting")
    for attempt in range(3):
        current=get_bytes(drive,FILE_ID)
        if current==expected:break
        if current!=before:raise ValueError("PRE650 concurrent update, abort")
        try:
            drive.files().update(fileId=FILE_ID,supportsAllDrives=True,
                media_body=MediaIoBaseUpload(io.BytesIO(expected),
                   mimetype="text/markdown",resumable=False),
                fields="id,name,size,modifiedTime").execute()
        except HttpError as e:
            if e.resp.status not in (500,502,503,504) or attempt==2:raise
            if get_bytes(drive,FILE_ID)==expected:break
            time.sleep(2*(attempt+1))
    after=get_bytes(drive,FILE_ID)
    if not (after==expected
        and after.startswith(before)
        and after.count(MARKER)==1):
        raise ValueError("PRE650 post-write byte check failed")
    return {"status":"AUDIT_OK","backup_created":True,
      "backup_file_id":backup_id,"original_sha256":sha(before),
      "canonical_sha256":sha(after),"canonical_bytes":len(after),
      "readback_identical":True,"history_prefix_unchanged":True}

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--run-id",required=True)
    opts=a.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=audit()
    except Exception as e:
        result={"status":"FAILED","error_type":type(e).__name__,
           "error_summary":str(e)[:180] if isinstance(e,ValueError) else "Drive context operation failed"}
    result.update({"stage":"PRE650_PRE648_PRE649_CANONICAL_CONTEXT",
       "run_id":opts.run_id,"utc":datetime.now(timezone.utc).isoformat(),
       "apk_built":False,"signing_material_accessed":False,"save_modified":False})
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    for field,value in (
        ("STATUS",result["status"]),
        ("CANONICAL_SHA256",result.get("canonical_sha256","none")),
        ("BACKUP_CREATED",result.get("backup_created",False)),
        ("READBACK_IDENTICAL",result.get("readback_identical",False)),
        ("ERROR_TYPE",result.get("error_type","none"))):
        print("PRE650_"+field+"="+str(value))
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1

if __name__=="__main__":raise SystemExit(main())
