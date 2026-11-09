#!/usr/bin/env python3
"""PRE611 canonical MD append-only recovery and V48 save-root checkpoint.
Backup first, verify exact existing bytes, append only. No game, APK or save writes.
"""
from __future__ import annotations
import argparse, hashlib, io, json, time
from pathlib import Path
from datetime import datetime, timezone
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID, PARENT, drive_client, get_meta, get_bytes

OUT=Path("/tmp/nfsmw-pre611/report.json")
HANDOFF=Path("docs/PRE610_HANDOFF_PRE607_LIVE_MARCEK_CORRUPT_LOG_20261109.md")
MARKER="# PRE610 — RESULTADO REAL PRE607".encode("utf-8")
PREVIOUS_MARKER=b"PRE608_HANDOFF_PRE604_607_BMW_CHILD_ENGINE_PARENT_20261109"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE611_PRE607_MARCEK_REJECTION_20261109.md"
EXPECTED_BYTES=928681
EXPECTED_SHA="64369a4ecf7fed685b0593f8ec9e87ad725fc50d7365a3fa01782ca88066c701"
def sha(b):return hashlib.sha256(b).hexdigest()
def verify_earlier_reports():
    previous=json.loads(Path("docs/PRE609_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    p606=json.loads(Path("docs/PRE606_BMW_CORRECTED_PARENT_PRIVATE_PTBR_METADATA.json").read_text())
    p607=json.loads(Path("docs/PRE607_SHEVERY_CHILD_ENGINE_PARENT_STATIC_PREFLIGHT_RESULT.json").read_text())
    handoff=HANDOFF.read_text(encoding="utf-8")
    if (any(x.get("status")!="AUDIT_OK" for x in (previous,p606,p607))
        or previous.get("canonical_bytes")!=EXPECTED_BYTES
        or previous.get("canonical_sha256")!=EXPECTED_SHA
        or previous.get("new_handoff_readback_verified") is not True
        or p606.get("phone_guest_tested") is not False
        or p606.get("candidate_VPAK_sha256")!="11c122bf9b32011fd3955498517e51f2f1f11551bc2bbd9f448201bc4ef862f3"
        or p606.get("translated_full_archive_expected_modified_sha256")!="1ed79d0f031d400002da8db6153ee84188d717e33f093a501f7a6bdfc0e5e146"
        or p607.get("wrong_hash_aborted_without_file_write") is not True
        or p607.get("actual_device_experiment_executed") is not False
        or "489ba96f60d3eccdbd9e7d5b456e6c39a4f582a430787529e1dd9ab834e7c033" not in handoff
        or "219.076 bytes" not in handoff
        or "07:53:21.442" not in handoff
        or "PRE607_RESTORE=ORIGINAIS_VERIFICADOS" not in handoff
        or "PENDENTE" not in handoff
        or "não confirma" not in handoff.lower() and "não" not in handoff.lower()):
        raise ValueError("PRE609/PRE606/PRE607 or uploaded PRE607 live log checkpoints invalid")

def audit():
    verify_earlier_reports()
    extra=b"\n\n---\n\n"+HANDOFF.read_bytes()
    if extra.count(MARKER)!=1 or not (2300<=len(extra)<=13000):
        raise ValueError("PRE611 handoff is incomplete or duplicated")
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
            raise ValueError("Existing PRE611 append not byte-exact or unexpected original")
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
        raise ValueError("Canonical context changed since PRE609: stop without update")
    expected=before+extra
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[PARENT]},
      fields="id,name,parents,size").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
        or get_bytes(drive,backup_id)!=before):
        raise ValueError("Backup PRE611 not bytewise identical: source untouched")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent Drive edit before PRE611 append")
    transient=0
    for attempt in range(3):
        state=get_bytes(drive,FILE_ID)
        if state==expected:break
        if state!=before:raise ValueError("Concurrent context changes during PRE611")
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
        raise ValueError("PRE611 canonical append did not pass bytewise readback")
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
       "stage":"PRE611_CANONICAL_SAVE_ROOT_CONTEXT_SYNC",
       "status":"FAILED","APK_built":False,
       "game_assets_modified":False,"save_modified":False,
       "signing_material_accessed":False,"BMW_tuning_enabled":False
    }
    try:r.update(audit())
    except Exception as e:r.update({"error_type":type(e).__name__,"error":str(e)[:260]})
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE611_STATUS",r["status"],flush=True)
    print("PRE611_READBACK",r.get("new_handoff_readback_verified",False),flush=True)
    print("PRE611_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
