#!/usr/bin/env python3
"""PRE556: backup-first append handoff to canonical CONTEXTO_NFSMW.md in Drive.

Mutates only the designated Markdown context file, preserving all prior bytes
and confirming exact readback. Never touches APK, VPAK, guest memory, saves.
"""
from __future__ import annotations
import argparse, io, json, time
from pathlib import Path
from datetime import datetime,timezone
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import (
    FILE_ID, PARENT, sha, drive_client, get_bytes, get_meta)

OUT=Path("/tmp/nfsmw-pre553/report.json")
HANDOFF=Path("docs/PRE556_HANDOFF_PRE555_PAL_PASTA_EXTRAIDA_HOSTPATH_20261108.md")
MARKER="PRE556_HANDOFF_PRE555_PAL_PASTA_EXTRAIDA_HOSTPATH_20261108"
PREVIOUS="PRE553_CORRECAO_HISTORICA_PRE520_PRE551_PAL_PADDING_VIRTUAL_READ_20261108"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE556_BMW_PAL_PASTA_20261108.md"
FILE_NAME="CONTEXTO_NFSMW.md"

def sync(drive):
    p555=json.loads(Path("docs/PRE555_PAL_EXTRACTED_FOLDER_HOSTPATH_VFS_READONLY.json").read_text())
    p553=json.loads(Path("docs/PRE553_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    note=Path("docs/PRE554_SHEVERY_ANDROID_DEVICE_EVIDENCE_READONLY_20261108.md").read_text()
    if (p555.get("status")!="AUDIT_OK" or
        p555.get("PRE99_regular_file_or_URI_uses_discimage_else_folder_uses_hostpath_code_verified") is not True or
        p555.get("PRE99_guest_kernel_vfs_host_entry_file_read_code_anchors_verified") is not True or
        len(p555.get("PRE99_source_code_anchor_index",{}))!=6 or
        p555.get("v48_current_runtime_hostpath_mount_traced") is not False or
        p555.get("translation_extracted_folder_bytes_match_original_PAL_ZIP_proven") is not False or
        p555.get("actual_guest_ZDIR_VPAK_loader_execution_proven") is not False or
        p555.get("BMW_tuning_enabled") is not False or
        "Sim estou executando via pasta extraída" not in note or
        p553.get("status")!="AUDIT_OK" or
        p553.get("prior_history_bytewise_preserved") is not True or
        p553.get("postupdate_readback_bytewise_verified") is not True or
        p553.get("new_total_bytes")!=844481 or
        p553.get("new_sha256")!="d19cedf297bf9450b938ae68f6f8b597138ef12281765e39ca40d5409e1cf4f2"):
        raise ValueError("PRE555 authenticated folder source gate or PRE553 canonical baseline invalid")
    metadata=get_meta(drive)
    if (metadata.get("id")!=FILE_ID or metadata.get("name")!=FILE_NAME
        or metadata.get("mimeType")!="text/markdown"
        or metadata.get("parents")!=[PARENT]
        or not 844000<=int(metadata.get("size",0))<=2000000):
        raise ValueError("Unexpected canonical file name, folder, MIME, ID or size")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(metadata["size"]):
        raise ValueError("Canonical Drive metadata/contents size mismatch")
    previous_text=before.decode("utf-8")
    if previous_text.count(PREVIOUS)!=1:
        raise ValueError("PRE553 canonical history missing or repeated")
    if MARKER in previous_text:
        return {"status":"ALREADY_APPLIED","backup_created":False,
                "canonical_file_id":FILE_ID,"current_bytes":len(before),
                "current_sha256":sha(before),"verified_existing_marker":True}
    if not HANDOFF.is_file():raise ValueError("PRE556 exact GitHub handoff not found")
    handoff=HANDOFF.read_bytes()
    if not 2500<=len(handoff)<=16000 or handoff.count(MARKER.encode())!=1:
        raise ValueError("Unexpected PRE556 handoff identity/length")
    # Use the published, reviewed document, not interpolated or guessed text.
    appendix=b"\n\n---\n\n"+handoff
    candidate=before+appendix
    if not candidate.startswith(before) or candidate.count(MARKER.encode())!=1:
        raise ValueError("Append-only invariant failed")

    # Existing source remains protected by a bytewise verified fresh Drive backup.
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
        body={"name":BACKUP_NAME,"parents":[PARENT]},
        fields="id,name,size,parents").execute()
    backup_id=backup["id"]
    result={"backup_created":True,"backup_reused":False,
        "backup_file_id":backup_id,
        "backup_name":BACKUP_NAME,"canonical_before_bytes":len(before),
        "canonical_before_sha256":sha(before)}
    if (int(backup.get("size",0))!=len(before) or
        sha(get_bytes(drive,backup_id))!=sha(before)):
        raise ValueError("PRE556 backup failed byte-for-byte verification")
    # Avoid clobbering another user's edit made between initial read and copy.
    fresh_meta=get_meta(drive)
    if (fresh_meta.get("modifiedTime")!=metadata.get("modifiedTime")
        or sha(get_bytes(drive,FILE_ID))!=sha(before)):
        raise ValueError("Concurrent context edit detected; source not overwritten")
    # HTTP502 may occur after upload is applied. On each transient failure,
    # read the actual canonical bytes, and retry only if it is still EXACTLY
    # equal to the initial snapshot. Never clobber a concurrent edit.
    uploaded=False
    transient_failures=0
    for attempt in range(3):
        fresh=get_bytes(drive,FILE_ID)
        if fresh==candidate:
            uploaded=True
            break
        if fresh!=before:
            raise ValueError("Concurrent Drive modification detected during retry")
        media=MediaIoBaseUpload(io.BytesIO(candidate),
                                mimetype="text/markdown",resumable=False)
        try:
            updated=drive.files().update(fileId=FILE_ID,
                supportsAllDrives=True,media_body=media,
                fields="id,name,size,modifiedTime").execute()
            if updated.get("id")!=FILE_ID:
                raise ValueError("Unexpected canonical Drive update target")
            uploaded=True
            break
        except HttpError as exc:
            if int(exc.resp.status) not in (500,502,503,504):
                raise
            transient_failures+=1
            actual=get_bytes(drive,FILE_ID)
            if actual==candidate:
                uploaded=True
                break
            if actual!=before:
                raise ValueError("Concurrent Drive bytes changed after HTTP5xx")
            if attempt==2:
                raise
            time.sleep(2*(attempt+1))
    if not uploaded:
        raise ValueError("Unable to verify a safe canonical upload")
    result["transient_http_failures"]=transient_failures
    after=get_bytes(drive,FILE_ID)
    if (after!=candidate or
        after[:len(before)]!=before or
        after.count(MARKER.encode())!=1):
        raise ValueError("Post-update exact readback does not match; backup retained")
    result.update({"status":"AUDIT_OK","append_bytes":len(appendix),
      "new_total_bytes":len(after),"new_sha256":sha(after),
      "prior_history_bytewise_preserved":True,
      "postupdate_readback_bytewise_verified":True,
      "canonical_file_id":FILE_ID})
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE556_CANONICAL_CONTEXT_APPEND_WITH_BACKUP",
            "status":"FAILED","apk_built":False,"save_modified":False,
            "game_assets_modified":False}
    try:result.update(sync(drive_client()))
    except Exception as exc:result.update({"error_type":type(exc).__name__,
                                          "error":str(exc)[:280]})
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE556_STATUS",result["status"],flush=True)
    print("PRE556_BACKUP_ID",result.get("backup_file_id","none"),flush=True)
    print("PRE556_READBACK",result.get("postupdate_readback_bytewise_verified",False),flush=True)
    print("PRE556_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
