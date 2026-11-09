#!/usr/bin/env python3
"""PRE630 canonical MD append-only recovery and V48 save-root checkpoint.
Backup first, verify exact existing bytes, append only. No game, APK or save writes.
"""
from __future__ import annotations
import argparse, hashlib, io, json, time
from pathlib import Path
from datetime import datetime, timezone
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID, PARENT, drive_client, get_meta, get_bytes

OUT=Path("/tmp/nfsmw-pre630/report.json")
HANDOFF=Path("docs/PRE629_HANDOFF_PRE625_NATIVE_SUCCESS_PRE626_V49_RUNNING_20261109.md")
MARKER="# PRE629 — PRE625 ARM64 aprovado".encode("utf-8")
PREVIOUS_MARKER="# PRE627 — Preparação de callback nativo BMW".encode("utf-8")
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE630_PRE625_ARM64_PASS_V49_RUNNING_20261109.md"
EXPECTED_BYTES=959741
EXPECTED_SHA="a8793ca61b87823541b0173f04dc6773d9de07a7ee1cc40bc8a10ddbd0051f61"
def sha(b):return hashlib.sha256(b).hexdigest()
def verify_earlier_reports():
    p628=json.loads(Path("docs/PRE628_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    p625=json.loads(Path("docs/PRE625_BMW_HOST_ATTR_ARM64_NATIVE_LINK_RESULT.json").read_text())
    p622=json.loads(Path("docs/PRE622_BMW_ATTR_HOST_VALUE_RAM_PREVIEW.json").read_text())
    handoff=HANDOFF.read_text(encoding="utf-8")
    attrs=p625.get("evidence",{})
    if (p628.get("status")!="AUDIT_OK"
        or p628.get("canonical_bytes")!=EXPECTED_BYTES
        or p628.get("canonical_sha256")!=EXPECTED_SHA
        or p628.get("new_handoff_readback_verified") is not True
        or p625.get("status")!="AUDIT_OK"
        or p625.get("native_build_ok") is not True
        or p625.get("native_arm64_elf") is not True
        or attrs.get("new_callback_exported_exactly_once") is not True
        or attrs.get("previous_3_callbacks_exported_once") is not True
        or attrs.get("new_guest_memory_ops_or_calls")!=0
        or p625.get("APK_built") is not False
        or p625.get("signing_material_accessed") is not False
        or p622.get("status")!="AUDIT_OK"
        or "42705397176" not in handoff
        or "42709319413" not in handoff
        or "73c631fb28722ad2716147249f92aaab621f5c62f5720624ba5f11bf86335652" not in handoff
        or "in_progress" not in handoff
        or "não declarar sucesso" not in handoff.lower()
        or "Nenhum APK novo instalado" not in handoff
        or "versionCode=49" not in handoff):
        raise ValueError("PRE628/PRE625 live ARM64 report or current PRE626 build checkpoint invalid")

def audit():
    verify_earlier_reports()
    extra=b"\n\n---\n\n"+HANDOFF.read_bytes()
    if extra.count(MARKER)!=1 or not (2300<=len(extra)<=13000):
        raise ValueError("PRE630 handoff is incomplete or duplicated")
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
            raise ValueError("Existing PRE630 append not byte-exact or unexpected original")
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
        raise ValueError("Canonical context changed since PRE628: stop without update")
    expected=before+extra
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[PARENT]},
      fields="id,name,parents,size").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
        or get_bytes(drive,backup_id)!=before):
        raise ValueError("Backup PRE630 not bytewise identical: source untouched")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent Drive edit before PRE630 append")
    transient=0
    for attempt in range(3):
        state=get_bytes(drive,FILE_ID)
        if state==expected:break
        if state!=before:raise ValueError("Concurrent context changes during PRE630")
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
        raise ValueError("PRE630 canonical append did not pass bytewise readback")
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
       "stage":"PRE630_CANONICAL_SAVE_ROOT_CONTEXT_SYNC",
       "status":"FAILED","APK_built":False,
       "game_assets_modified":False,"save_modified":False,
       "signing_material_accessed":False,"BMW_tuning_enabled":False
    }
    try:r.update(audit())
    except Exception as e:r.update({"error_type":type(e).__name__,"error":str(e)[:260]})
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE630_STATUS",r["status"],flush=True)
    print("PRE630_READBACK",r.get("new_handoff_readback_verified",False),flush=True)
    print("PRE630_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
