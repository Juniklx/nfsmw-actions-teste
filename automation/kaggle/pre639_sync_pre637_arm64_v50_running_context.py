#!/usr/bin/env python3
"""PRE639 canonical context append: PRE637 ARM64 passed, PRE638 release running.
Backup verified original first; byte-exact idempotent append only.
No APK, signing key, game source, ISO or save changes.
"""
from __future__ import annotations
import argparse,hashlib,io,json,time
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

EXPECTED_BYTES=980115
EXPECTED_SHA="7ba28e1c2445fae93505e72ac983f05a270ca61d63f07643f0d49501bb3f3e7b"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE639_PRE637_20261110.md"
HANDOFF=Path("docs/PRE639_HANDOFF_PRE637_ARM64_APPROVED_PRE638_V50_RUNNING_20261110.md")
MARKER=b"# PRE639 \xe2\x80\x94 PRE637 ARM64 aprovada"
PRE637=Path("docs/PRE637_V49_C3_ARM64_NATIVE_RESULT.json")
OUT=Path("/tmp/nfsmw-pre639/report.json")
def sha(b):return hashlib.sha256(b).hexdigest()

def validate_evidence():
    j=json.loads(PRE637.read_text(encoding="utf-8"))
    e=j.get("evidence",{})
    if not (j.get("status")=="AUDIT_OK"
      and j.get("run_id")=="42745476208"
      and j.get("native_build_ok") is True
      and j.get("native_arm64_elf") is True
      and j.get("real_linked_library_sha256")=="b8748dbf74f8fddb1bf3151801b50fe24e159c0f4d9fa6f84f0f675791d0cc9e"
      and e.get("pre635_marker_linked_in_actual_elf") is True
      and e.get("all_4_bmw_callbacks_exported_once") is True
      and j.get("APK_built") is False and j.get("signing_material_accessed") is False):
        raise ValueError("PRE637 evidence not acceptable for context")
    handoff=HANDOFF.read_bytes()
    if (handoff.count(MARKER)!=1
        or b"42748358853" not in handoff
        or b"42745476208" not in handoff
        or b"PRE638" not in handoff
        or b"sem APK V50 comprovada" not in handoff
        or not (2300<=len(handoff)<=7000)):
        raise ValueError("PRE639 handoff record incomplete or contradictory")
    return handoff

def audit():
    handoff=validate_evidence()
    appendix=b"\n\n---\n\n"+handoff
    drive=drive_client()
    meta=get_meta(drive)
    if (meta.get("id")!=FILE_ID or meta.get("name")!="CONTEXTO_NFSMW.md"
        or meta.get("mimeType")!="text/markdown"
        or meta.get("parents")!=[PARENT]):
        raise ValueError("Canonical context metadata unexpected")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):raise ValueError("Canonical size mismatch")
    if MARKER in before:
        if (before.count(MARKER)!=1 or not before.endswith(appendix)
            or len(before)-len(appendix)!=EXPECTED_BYTES
            or sha(before[:-len(appendix)])!=EXPECTED_SHA):
            raise ValueError("Existing PRE639 not byte-exactly idempotent")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
            "canonical_bytes":len(before),"canonical_sha256":sha(before),
            "readback_identical":True}
    if len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA:
        raise ValueError("Canonical context changed: no write")
    expected=before+appendix
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},
       fields="id,name,size,parents").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
       or get_bytes(drive,backup_id)!=before):
        raise ValueError("Context backup not readback-identical; no overwrite")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent editor changed context before write")
    for attempt in range(3):
        current=get_bytes(drive,FILE_ID)
        if current==expected:break
        if current!=before:raise ValueError("Concurrent context change during append")
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
    if after!=expected or not after.startswith(before) or after.count(MARKER)!=1:
        raise ValueError("PRE639 remote context readback mismatch")
    return {"status":"AUDIT_OK","backup_created":True,
       "backup_file_id":backup_id,"original_sha256":sha(before),
       "canonical_bytes":len(after),"canonical_sha256":sha(after),
       "readback_identical":True,"previous_context_preserved":True}

def main():
    a=argparse.ArgumentParser();a.add_argument("--run-id",required=True)
    opts=a.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"status":"FAILED","error_type":type(e).__name__,
            "error":str(e)[:170] if isinstance(e,ValueError) else "Drive context operation failed"}
    r.update({"stage":"PRE639_CANONICAL_CONTEXT_SYNC","run_id":opts.run_id,
      "utc":datetime.now(timezone.utc).isoformat(),"apk_built":False,
      "signing_material_accessed":False,"user_save_modified":False})
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE639_STATUS="+r["status"])
    print("PRE639_CANONICAL_SHA256="+str(r.get("canonical_sha256","none")))
    print("PRE639_BACKUP_CREATED="+str(r.get("backup_created",False)))
    print("PRE639_ERROR_TYPE="+str(r.get("error_type","none")))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
