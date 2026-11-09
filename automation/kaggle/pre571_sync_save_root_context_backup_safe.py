#!/usr/bin/env python3
"""PRE571 canonical MD append-only recovery and V48 save-root checkpoint.
Backup first, verify exact existing bytes, append only. No game, APK or save writes.
"""
from __future__ import annotations
import argparse, hashlib, io, json, time
from pathlib import Path
from datetime import datetime, timezone
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID, PARENT, drive_client, get_meta, get_bytes

OUT=Path("/tmp/nfsmw-pre571/report.json")
HANDOFF=Path("docs/PRE571_HANDOFF_PRE567R_PRE570_V48_SAVE_ISOLATION_GATE_20261109.md")
MARKER=b"PRE571_HANDOFF_PRE567R_PRE570_V48_SAVE_ISOLATION_GATE_20261109"
PREVIOUS_MARKER=b"PRE567_HANDOFF_PRE566_PTBR_BMW_FILE_BACKED_20261109"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE571_SAVE_ROOT_20261109.md"
EXPECTED_BYTES=864277
EXPECTED_SHA="7227982889c1cbcadb6ce41eb7408289f42d5305eecc5afdcf848f5a4a5c5be4"
def sha(b):return hashlib.sha256(b).hexdigest()
def verify_earlier_reports():
    r567=json.loads(Path("docs/PRE567R_DRIVE_RECOVERY_READONLY_RESULT.json").read_text())
    r568=json.loads(Path("docs/PRE568_V48_ANDROID_SAVE_ROOT_STATIC_READONLY.json").read_text())
    r569=json.loads(Path("docs/PRE569_V48_SAVE_IMPORT_STATIC_READONLY.json").read_text())
    r570=json.loads(Path("docs/PRE570_V48_SAVE_IMPORT_STATIC_READONLY.json").read_text())
    if (any(x.get("status")!="AUDIT_OK" for x in (r567,r568,r569,r570))
        or r567.get("canonical_context_sha256")!=EXPECTED_SHA
        or r567.get("canonical_context_bytes")!=EXPECTED_BYTES
        or r567.get("canonical_postreadback_verified") is not True
        or r568.get("current_v48_native_user_root_method_exists") is not True
        or r568.get("current_v48_game_data_root_method_exists") is not True
        or r568.get("safe_disposable_profile_isolation_proven") is not False
        or r569.get("partidas_method_present") is not True
        or r569.get("MARCEK_save_isolation_proven") is not False
        or r570.get("copy_tree_method_present") is not True
        or r570.get("safe_to_run_with_MARCEK") is not False):
        raise ValueError("PRE567R to PRE570 prerequisite evidence missing")

def audit():
    verify_earlier_reports()
    extra=b"\n\n---\n\n"+HANDOFF.read_bytes()
    if extra.count(MARKER)!=1 or not (2300<=len(extra)<=13000):
        raise ValueError("PRE571 handoff is incomplete or duplicated")
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
            raise ValueError("Existing PRE571 append not byte-exact or unexpected original")
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
        raise ValueError("Canonical context changed since PRE567R: stop without update")
    expected=before+extra
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[PARENT]},
      fields="id,name,parents,size").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
        or get_bytes(drive,backup_id)!=before):
        raise ValueError("Backup PRE571 not bytewise identical: source untouched")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent Drive edit before PRE571 append")
    transient=0
    for attempt in range(3):
        state=get_bytes(drive,FILE_ID)
        if state==expected:break
        if state!=before:raise ValueError("Concurrent context changes during PRE571")
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
        raise ValueError("PRE571 canonical append did not pass bytewise readback")
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
       "stage":"PRE571_CANONICAL_SAVE_ROOT_CONTEXT_SYNC",
       "status":"FAILED","APK_built":False,
       "game_assets_modified":False,"save_modified":False,
       "signing_material_accessed":False,"BMW_tuning_enabled":False
    }
    try:r.update(audit())
    except Exception as e:r.update({"error_type":type(e).__name__,"error":str(e)[:260]})
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE571_STATUS",r["status"],flush=True)
    print("PRE571_READBACK",r.get("new_handoff_readback_verified",False),flush=True)
    print("PRE571_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
