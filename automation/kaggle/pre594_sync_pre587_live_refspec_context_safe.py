#!/usr/bin/env python3
"""PRE594 canonical MD append-only recovery and V48 save-root checkpoint.
Backup first, verify exact existing bytes, append only. No game, APK or save writes.
"""
from __future__ import annotations
import argparse, hashlib, io, json, time
from pathlib import Path
from datetime import datetime, timezone
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID, PARENT, drive_client, get_meta, get_bytes

OUT=Path("/tmp/nfsmw-pre594/report.json")
HANDOFF=Path("docs/PRE593_HANDOFF_PRE587_LIVE_SUCCESS_PRE591_592_REFSPEC_CONTROL_20261109.md")
MARKER=b"PRE593_HANDOFF_PRE587_LIVE_SUCCESS_PRE591_592_REFSPEC_CONTROL_20261109"
PREVIOUS_MARKER=b"PRE588_HANDOFF_PRE586_UNLINKED_VLT_PRE587_20261109"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE594_PRE587_LIVE_REFSPEC_ONLY_20261109.md"
EXPECTED_BYTES=902251
EXPECTED_SHA="65e46fae8ecd398bbb4c858a92ed9fd20c7e1b61d49cf95eeb26493e8841a907"
def sha(b):return hashlib.sha256(b).hexdigest()
def verify_earlier_reports():
    previous=json.loads(Path("docs/PRE589_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    p591=json.loads(Path("docs/PRE591_BMW_REFSPEC_POINTER_ONLY_PRIVATE_METADATA.json").read_text())
    p592=json.loads(Path("docs/PRE592_SHEVERY_REFSPEC_POINTER_ONLY_STATIC_PREFLIGHT_RESULT.json").read_text())
    handoff=HANDOFF.read_text(encoding="utf-8")
    if (any(p.get("status")!="AUDIT_OK" for p in (previous,p591,p592))
        or previous.get("canonical_bytes")!=EXPECTED_BYTES
        or previous.get("canonical_sha256")!=EXPECTED_SHA
        or previous.get("new_handoff_readback_verified") is not True
        or p591.get("candidate_VPAK_size")!=698004
        or p591.get("BMW_pvehicle_motor_upgrade_count_zero") is not True
        or p591.get("active_BMW_pvehicle_refspec_points_to_two_ref_array") is not True
        or p591.get("guest_loader_executed") is not False
        or p591.get("original_translated_game_files_modified") is not False
        or p592.get("actual_device_experiment_executed") is not False
        or p592.get("wrong_hash_aborted_without_file_write") is not True
        or "509900a226ef281ab92a8567d818cb38e5afdb98a434bc77d0216fea384a2957" not in handoff
        or "522e15940379c8b746ab3c77e771fd22352b0b408cbf6264cf64e99f8a378c29" not in handoff
        or "PRE587_RESTORE=ORIGINAIS_VERIFICADOS" not in handoff):
        raise ValueError("PRE589-PRE592 source evidence and live device log summary missing")

def audit():
    verify_earlier_reports()
    extra=b"\n\n---\n\n"+HANDOFF.read_bytes()
    if extra.count(MARKER)!=1 or not (2300<=len(extra)<=13000):
        raise ValueError("PRE594 handoff is incomplete or duplicated")
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
            raise ValueError("Existing PRE594 append not byte-exact or unexpected original")
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
        raise ValueError("Canonical context changed since PRE589: stop without update")
    expected=before+extra
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[PARENT]},
      fields="id,name,parents,size").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
        or get_bytes(drive,backup_id)!=before):
        raise ValueError("Backup PRE594 not bytewise identical: source untouched")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent Drive edit before PRE594 append")
    transient=0
    for attempt in range(3):
        state=get_bytes(drive,FILE_ID)
        if state==expected:break
        if state!=before:raise ValueError("Concurrent context changes during PRE594")
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
        raise ValueError("PRE594 canonical append did not pass bytewise readback")
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
       "stage":"PRE594_CANONICAL_SAVE_ROOT_CONTEXT_SYNC",
       "status":"FAILED","APK_built":False,
       "game_assets_modified":False,"save_modified":False,
       "signing_material_accessed":False,"BMW_tuning_enabled":False
    }
    try:r.update(audit())
    except Exception as e:r.update({"error_type":type(e).__name__,"error":str(e)[:260]})
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE594_STATUS",r["status"],flush=True)
    print("PRE594_READBACK",r.get("new_handoff_readback_verified",False),flush=True)
    print("PRE594_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
