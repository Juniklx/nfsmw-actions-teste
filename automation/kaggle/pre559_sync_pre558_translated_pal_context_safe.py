#!/usr/bin/env python3
"""PRE559: backup-first append handoff to canonical CONTEXTO_NFSMW.md in Drive.

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

OUT=Path("/tmp/nfsmw-pre559/report.json")
HANDOFF=Path("docs/PRE559_HANDOFF_PRE558_TRANSLATED_PAL_ZDIR_ZZDATA_HASH_DIVERGENCE_20261108.md")
MARKER="PRE559_HANDOFF_PRE558_TRANSLATED_PAL_ZDIR_ZZDATA_HASH_DIVERGENCE_20261108"
PREVIOUS="PRE556_HANDOFF_PRE555_PAL_PASTA_EXTRAIDA_HOSTPATH_20261108"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE559_PTBR_HASHES_20261108.md"
FILE_NAME="CONTEXTO_NFSMW.md"

def sync(drive):
    p558=json.loads(Path("docs/PRE558_PAL_PTBR_HASH_COMPARISON_READONLY.json").read_text())
    p556=json.loads(Path("docs/PRE556_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    evidence=json.loads(Path("docs/PRE558_SHEVERY_TRANSLATED_PAL_FINGERPRINTS_USER_REPORTED_20261108.json").read_text())
    if (p558.get("status")!="AUDIT_OK" or
        p558.get("on_device_read_this_CI") is not False or
        p558.get("original_ZDIR_row_806_transferable_to_translation") is not False or
        p558.get("translation_attributes_resource_offset_verified") is not False or
        p558.get("translated_zdir_size_difference_bytes")!=48 or
        p558.get("same_ZZDATA4_content") is not False or
        p558.get("translated_pal_ZDIR_sha256_reported")!="832a20dfdca663233f4559236048f21d5ff4e6f65780d1aa18e58b72005245bf" or
        p558.get("translated_pal_ZZDATA4_sha256_reported")!="7dd33d214ac45f4b67005685bc0c2b8555eca98a33d24216c934f077d5054951" or
        evidence.get("origin")!="Direct text output pasted by the user from Shevery in current chat; not an independent connected device read" or
        p556.get("status")!="AUDIT_OK" or
        p556.get("prior_history_bytewise_preserved") is not True or
        p556.get("postupdate_readback_bytewise_verified") is not True or
        p556.get("new_total_bytes")!=849626 or
        p556.get("new_sha256")!="67be19118bb890a25fce9ad42cd9b2e6dfe03a8020ef040309de89d863ce8ead"):
        raise ValueError("PRE558 folder fingerprints or PRE556 canonical checkpoint invalid")
    metadata=get_meta(drive)
    if (metadata.get("id")!=FILE_ID or metadata.get("name")!=FILE_NAME
        or metadata.get("mimeType")!="text/markdown"
        or metadata.get("parents")!=[PARENT]
        or not 849000<=int(metadata.get("size",0))<=2000000):
        raise ValueError("Unexpected canonical file name, folder, MIME, ID or size")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(metadata["size"]):
        raise ValueError("Canonical Drive metadata/contents size mismatch")
    previous_text=before.decode("utf-8")
    if previous_text.count(PREVIOUS)!=1:
        raise ValueError("PRE556 canonical history missing or repeated")
    if MARKER in previous_text:
        return {"status":"ALREADY_APPLIED","backup_created":False,
                "canonical_file_id":FILE_ID,"current_bytes":len(before),
                "current_sha256":sha(before),"verified_existing_marker":True}
    if not HANDOFF.is_file():raise ValueError("PRE559 exact GitHub handoff not found")
    handoff=HANDOFF.read_bytes()
    if not 2500<=len(handoff)<=16000 or handoff.count(MARKER.encode())!=1:
        raise ValueError("Unexpected PRE559 handoff identity/length")
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
        raise ValueError("PRE559 backup failed byte-for-byte verification")
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
    result={"stage":"PRE559_CANONICAL_CONTEXT_APPEND_WITH_BACKUP",
            "status":"FAILED","apk_built":False,"save_modified":False,
            "game_assets_modified":False}
    try:result.update(sync(drive_client()))
    except Exception as exc:result.update({"error_type":type(exc).__name__,
                                          "error":str(exc)[:280]})
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE559_STATUS",result["status"],flush=True)
    print("PRE559_BACKUP_ID",result.get("backup_file_id","none"),flush=True)
    print("PRE559_READBACK",result.get("postupdate_readback_bytewise_verified",False),flush=True)
    print("PRE559_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
