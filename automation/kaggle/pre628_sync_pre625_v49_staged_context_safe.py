#!/usr/bin/env python3
"""PRE628 canonical MD append-only recovery and V48 save-root checkpoint.
Backup first, verify exact existing bytes, append only. No game, APK or save writes.
"""
from __future__ import annotations
import argparse, hashlib, io, json, time
from pathlib import Path
from datetime import datetime, timezone
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID, PARENT, drive_client, get_meta, get_bytes

OUT=Path("/tmp/nfsmw-pre628/report.json")
HANDOFF=Path("docs/PRE627_HANDOFF_PRE625_NATIVE_PENDING_PRE626_V49_GATED_20261109.md")
MARKER="# PRE627 — Preparação de callback nativo BMW".encode("utf-8")
PREVIOUS_MARKER="# PRE623 — PRE607 validada por SHA no S24 FE".encode("utf-8")
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE628_PRE625_NATIVE_V49_STAGED_20261109.md"
EXPECTED_BYTES=953585
EXPECTED_SHA="d1422be8fc846427819e8f568e194101d86fafc7af401102583b691e76ea6f0c"
def sha(b):return hashlib.sha256(b).hexdigest()
def verify_earlier_reports():
    p624=json.loads(Path("docs/PRE624_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    p622=json.loads(Path("docs/PRE622_BMW_ATTR_HOST_VALUE_RAM_PREVIEW.json").read_text())
    report=HANDOFF.read_text(encoding="utf-8")
    stage=Path("automation/kaggle/pre625_bmw_attr_host_arm64_noapk.py").read_text(encoding="utf-8")
    build=Path("automation/kaggle/pre626_build_signed_v49_bmw_attr_diag.py").read_text(encoding="utf-8")
    if (p624.get("status")!="AUDIT_OK" or p622.get("status")!="AUDIT_OK"
        or p624.get("canonical_bytes")!=EXPECTED_BYTES
        or p624.get("canonical_sha256")!=EXPECTED_SHA
        or p624.get("new_handoff_readback_verified") is not True
        or p622.get("new_guest_memory_reads")!=0
        or p622.get("new_guest_memory_writes")!=0
        or "PRE625" not in report or "PRE626" not in report
        or "42705397176" not in report
        or "NÃO compilada" not in report
        or "pre625_bmw_attr_host_arm64_noapk.py" not in report
        or "NFSMW_PRE622_ATTR_VALUE" not in report
        or "NFSMW_V49_PRE626_BMW_ATTRIBUTE_VALUE_DIAGNOSTIC.apk" not in report
        or "gate" not in build.lower()
        or "NFSMW_PRE622_ATTR_VALUE" not in stage):
        raise ValueError("PRE624/PRE622 or PRE625/PRE626 prepared status provenance missing")

def audit():
    verify_earlier_reports()
    extra=b"\n\n---\n\n"+HANDOFF.read_bytes()
    if extra.count(MARKER)!=1 or not (2300<=len(extra)<=13000):
        raise ValueError("PRE628 handoff is incomplete or duplicated")
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
            raise ValueError("Existing PRE628 append not byte-exact or unexpected original")
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
        raise ValueError("Canonical context changed since PRE624: stop without update")
    expected=before+extra
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[PARENT]},
      fields="id,name,parents,size").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
        or get_bytes(drive,backup_id)!=before):
        raise ValueError("Backup PRE628 not bytewise identical: source untouched")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent Drive edit before PRE628 append")
    transient=0
    for attempt in range(3):
        state=get_bytes(drive,FILE_ID)
        if state==expected:break
        if state!=before:raise ValueError("Concurrent context changes during PRE628")
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
        raise ValueError("PRE628 canonical append did not pass bytewise readback")
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
       "stage":"PRE628_CANONICAL_SAVE_ROOT_CONTEXT_SYNC",
       "status":"FAILED","APK_built":False,
       "game_assets_modified":False,"save_modified":False,
       "signing_material_accessed":False,"BMW_tuning_enabled":False
    }
    try:r.update(audit())
    except Exception as e:r.update({"error_type":type(e).__name__,"error":str(e)[:260]})
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE628_STATUS",r["status"],flush=True)
    print("PRE628_READBACK",r.get("new_handoff_readback_verified",False),flush=True)
    print("PRE628_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
