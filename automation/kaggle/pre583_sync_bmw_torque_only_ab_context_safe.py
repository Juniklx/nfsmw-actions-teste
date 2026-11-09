#!/usr/bin/env python3
"""PRE583 canonical MD append-only recovery and V48 save-root checkpoint.
Backup first, verify exact existing bytes, append only. No game, APK or save writes.
"""
from __future__ import annotations
import argparse, hashlib, io, json, time
from pathlib import Path
from datetime import datetime, timezone
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID, PARENT, drive_client, get_meta, get_bytes

OUT=Path("/tmp/nfsmw-pre583/report.json")
HANDOFF=Path("docs/PRE582_HANDOFF_PRE579_PRE581_BMW_TORQUE_ONLY_20261109.md")
MARKER=b"PRE582_HANDOFF_PRE579_PRE581_BMW_TORQUE_ONLY_20261109"
PREVIOUS_MARKER=b"PRE577_HANDOFF_PRE573_ON_DEVICE_LOG_MARCEK_20261109"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE583_BMW_STOCK_MOTOR_CONTROL_20261109.md"
EXPECTED_BYTES=885141
EXPECTED_SHA="cf39c6f28c5b8a15c2843d860a6b56efbc61e5a021aa211cd32d7ee02caf7406"
def sha(b):return hashlib.sha256(b).hexdigest()
def verify_earlier_reports():
    p578=json.loads(Path("docs/PRE578_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    p580=json.loads(Path("docs/PRE580_PTBR_BMW_MOTOR_ONLY_PRIVATE_CONTROL_METADATA.json").read_text())
    p581=json.loads(Path("docs/PRE581_SHEVERY_TORQUE_ONLY_STATIC_PREFLIGHT_RESULT.json").read_text())
    note=HANDOFF.read_text(encoding="utf-8")
    if (any(p.get("status")!="AUDIT_OK" for p in (p578,p580,p581))
        or p578.get("canonical_bytes")!=EXPECTED_BYTES
        or p578.get("canonical_sha256")!=EXPECTED_SHA
        or p578.get("new_handoff_readback_verified") is not True
        or p580.get("candidate_VPAK_bytes")!=697856
        or p580.get("changed_resource_byte_count")!=24
        or p580.get("new_engine_collection_added") is not False
        or p580.get("original_VLT_bytes_unchanged") is not True
        or p580.get("user_phone_files_modified") is not False
        or p581.get("actual_device_experiment_executed") is not False
        or "83522f3f328bc9385c8fb9ebf20b6f0b668f4a7519db08a4d38d4881ffa37cde" not in note
        or "95dff1f0e8f72ac54b3039d7627f406bf90b67fe66bee937776846464ea054aa" not in note):
        raise ValueError("PRE578/PRE580/PRE581 evidence and user A/B not pinned")

def audit():
    verify_earlier_reports()
    extra=b"\n\n---\n\n"+HANDOFF.read_bytes()
    if extra.count(MARKER)!=1 or not (2300<=len(extra)<=13000):
        raise ValueError("PRE583 handoff is incomplete or duplicated")
    drive=drive_client()
    meta=get_meta(drive)
    if (meta.get("id")!=FILE_ID or meta.get("name")!="CONTEXTO_NFSMW.md"
        or meta.get("mimeType")!="text/markdown" or meta.get("parents")!=[PARENT]):
        raise ValueError("Canonical Drive file identity or parent changed")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):raise ValueError("Canonical size/readback inconsistent")
    # On retry after a confirmed successful write, do not append twice.
    if MARKER in before:
        prefix=before[:-len(extra)] if before.endswith(extra) else b""
        if (len(prefix)!=EXPECTED_BYTES or sha(prefix)!=EXPECTED_SHA
            or before.count(MARKER)!=1 or not prefix.count(PREVIOUS_MARKER)==1):
            raise ValueError("Existing PRE583 append not byte-exact or unexpected original")
        return {
          "status":"ALREADY_APPLIED_VERIFIED",
          "backup_created_this_run":False,
          "original_context_sha256":EXPECTED_SHA,
          "original_context_bytes":EXPECTED_BYTES,
          "canonical_bytes":len(before),
          "canonical_sha256":sha(before),
          "prior_context_prefix_preserved":True,
          "new_handoff_readback_verified":True
        }
    if (len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA
        or before.count(PREVIOUS_MARKER)!=1):
        raise ValueError("Canonical context changed since PRE578: stop without update")
    expected=before+extra
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[PARENT]},
      fields="id,name,parents,size").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
        or get_bytes(drive,backup_id)!=before):
        raise ValueError("Backup PRE583 not bytewise identical: source untouched")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent Drive edit before PRE583 append")
    transient=0
    for attempt in range(3):
        state=get_bytes(drive,FILE_ID)
        if state==expected:break
        if state!=before:raise ValueError("Concurrent context changes during PRE583")
        media=MediaIoBaseUpload(io.BytesIO(expected),mimetype="text/markdown",resumable=False)
        try:
            drive.files().update(fileId=FILE_ID,supportsAllDrives=True,
               media_body=media,fields="id,name,size,modifiedTime").execute()
        except HttpError as exc:
            if int(exc.resp.status) not in (500,502,503,504):raise
            transient+=1
            current=get_bytes(drive,FILE_ID)
            if current==expected:break
            if current!=before:raise ValueError("Concurrent edit after transient upload error")
            if attempt==2:raise
            time.sleep(2*(attempt+1))
    after=get_bytes(drive,FILE_ID)
    if (after!=expected or after[:EXPECTED_BYTES]!=before
        or after.count(MARKER)!=1):
        raise ValueError("PRE583 canonical append did not pass bytewise readback")
    return {
      "status":"AUDIT_OK",
      "backup_created_this_run":True,
      "backup_file_id":backup_id,
      "original_context_sha256":EXPECTED_SHA,
      "original_context_bytes":EXPECTED_BYTES,
      "canonical_bytes":len(after),
      "canonical_sha256":sha(after),
      "prior_context_prefix_preserved":True,
      "new_handoff_readback_verified":True,
      "transient_http_failures":transient
    }

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--run-id",required=True)
    a=parser.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    r={
       "stage":"PRE583_CANONICAL_SAVE_ROOT_CONTEXT_SYNC",
       "status":"FAILED","APK_built":False,
       "game_assets_modified":False,"save_modified":False,
       "signing_material_accessed":False,"BMW_tuning_enabled":False
    }
    try:r.update(audit())
    except Exception as e:r.update({"error_type":type(e).__name__,"error":str(e)[:260]})
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE583_STATUS",r["status"],flush=True)
    print("PRE583_READBACK",r.get("new_handoff_readback_verified",False),flush=True)
    print("PRE583_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
