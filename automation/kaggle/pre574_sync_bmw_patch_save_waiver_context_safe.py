#!/usr/bin/env python3
"""PRE574 canonical MD append-only recovery and V48 save-root checkpoint.
Backup first, verify exact existing bytes, append only. No game, APK or save writes.
"""
from __future__ import annotations
import argparse, hashlib, io, json, time
from pathlib import Path
from datetime import datetime, timezone
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID, PARENT, drive_client, get_meta, get_bytes

OUT=Path("/tmp/nfsmw-pre574/report.json")
HANDOFF=Path("docs/PRE574_HANDOFF_PRE572_PRE573_USER_ACCEPTS_NEW_SAVE_20261109.md")
MARKER=b"PRE574_HANDOFF_PRE572_PRE573_USER_ACCEPTS_NEW_SAVE_20261109"
PREVIOUS_MARKER=b"PRE571_HANDOFF_PRE567R_PRE570_V48_SAVE_ISOLATION_GATE_20261109"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE574_BMW_PATCH_AND_SAVE_WAIVER_20261109.md"
EXPECTED_BYTES=870337
EXPECTED_SHA="62ce36223f666a0fba614a2de21e177c31930b71b470387c2ea12770d32e2a02"
def sha(b):return hashlib.sha256(b).hexdigest()
def verify_earlier_reports():
    r571=json.loads(Path("docs/PRE571_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    r572=json.loads(Path("docs/PRE572_PTBR_BMW_PRIVATE_PATCH_BUNDLE_METADATA.json").read_text())
    r573=json.loads(Path("docs/PRE573_SHEVERY_SCRIPTS_STATIC_PREFLIGHT_RESULT.json").read_text())
    if (any(x.get("status")!="AUDIT_OK" for x in (r571,r572,r573))
        or r571.get("canonical_sha256")!=EXPECTED_SHA
        or r571.get("canonical_bytes")!=EXPECTED_BYTES
        or r571.get("new_handoff_readback_verified") is not True
        or r572.get("patch_bundle_total_bytes")!=731680
        or r572.get("translated_full_archive_expected_modified_sha256")!="4eca61a0969bd1311e7b664f073ecaab50c950b43b10bb4438858ff3c57b665e"
        or r572.get("original_ptbr_phone_folder_modified") is not False
        or r572.get("save_modified") is not False
        or r572.get("guest_loader_executed") is not False
        or r572.get("save_isolation_requirement_waived_by_user") is not True
        or r573.get("shell_syntax_tested") is not True
        or r573.get("synthetic_wrong_hash_fail_closed_gate") is not True
        or r573.get("on_device_script_executed") is not False):
        raise ValueError("PRE571-PRE573 prerequisite evidence missing")

def audit():
    verify_earlier_reports()
    extra=b"\n\n---\n\n"+HANDOFF.read_bytes()
    if extra.count(MARKER)!=1 or not (2300<=len(extra)<=13000):
        raise ValueError("PRE574 handoff is incomplete or duplicated")
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
            raise ValueError("Existing PRE574 append not byte-exact or unexpected original")
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
        raise ValueError("Canonical context changed since PRE571: stop without update")
    expected=before+extra
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[PARENT]},
      fields="id,name,parents,size").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
        or get_bytes(drive,backup_id)!=before):
        raise ValueError("Backup PRE574 not bytewise identical: source untouched")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent Drive edit before PRE574 append")
    transient=0
    for attempt in range(3):
        state=get_bytes(drive,FILE_ID)
        if state==expected:break
        if state!=before:raise ValueError("Concurrent context changes during PRE574")
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
        raise ValueError("PRE574 canonical append did not pass bytewise readback")
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
       "stage":"PRE574_CANONICAL_SAVE_ROOT_CONTEXT_SYNC",
       "status":"FAILED","APK_built":False,
       "game_assets_modified":False,"save_modified":False,
       "signing_material_accessed":False,"BMW_tuning_enabled":False
    }
    try:r.update(audit())
    except Exception as e:r.update({"error_type":type(e).__name__,"error":str(e)[:260]})
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE574_STATUS",r["status"],flush=True)
    print("PRE574_READBACK",r.get("new_handoff_readback_verified",False),flush=True)
    print("PRE574_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
