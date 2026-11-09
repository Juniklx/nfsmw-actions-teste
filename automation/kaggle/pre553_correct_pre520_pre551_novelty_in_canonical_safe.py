#!/usr/bin/env python3
"""PRE553: backup-first append handoff to canonical CONTEXTO_NFSMW.md in Drive.

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
HANDOFF=Path("docs/PRE553_CORRECAO_HISTORICA_PRE520_PRE551_PAL_PADDING_VIRTUAL_READ_20261108.md")
MARKER="PRE553_CORRECAO_HISTORICA_PRE520_PRE551_PAL_PADDING_VIRTUAL_READ_20261108"
PREVIOUS="PRE552_BMW_TUNING_PRE551_PAL_ZZDATA4_FULL_CRC_RAM_VIRTUAL_RESOURCE_GATE_20261108"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE553_BMW_TUNING_20261108.md"
FILE_NAME="CONTEXTO_NFSMW.md"

def sync(drive):
    p520=json.loads(Path("docs/PRE520_ORIGINAL_PAL_ZZDATA4_SECTOR_PADDING_READONLY.json").read_text())
    p551=json.loads(Path("docs/PRE551_PAL_ORIGINAL_ZZDATA4_PADDING_AND_VIRTUAL_RESOURCE_READONLY.json").read_text())
    prior=json.loads(Path("docs/PRE552_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (p520.get("status")!="AUDIT_OK" or
        p520.get("full_member_crc32_verified") is not True or
        p520.get("full_member_uncompressed_size_verified") is not True or
        p520.get("original_PAL_ZZDATA4_member_CRC32")!="b46a396c" or
        p520.get("original_PAL_ZZDATA4_member_bytes")!=401068032 or
        p520.get("original_PAL_VPAK_sha256")!="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad" or
        p520.get("original_padding_bytes")!=512 or
        p520.get("original_padding_zero_byte_count")!=512 or
        p520.get("original_padding_all_zero") is not True or
        p520.get("candidate_remaining_bytes")!=364 or
        p520.get("VPAK_overlay_created") is not False or
        p520.get("original_loader_acceptance_proven") is not False or
        p551.get("status")!="AUDIT_OK" or
        p551.get("PAL_game_original_ZIP_id")!=p520.get("source_zip_drive_id") or
        p551.get("zip_original_ZZDATA4_CRC32_hex")!=p520.get("original_PAL_ZZDATA4_member_CRC32") or
        p551.get("zip_original_ZZDATA4_uncompressed_bytes")!=p520.get("original_PAL_ZZDATA4_member_bytes") or
        p551.get("source_pal_original_VPAK_sha256")!=p520.get("original_PAL_VPAK_sha256") or
        p551.get("original_pal_ZZDATA_sector_padding_zero_bytes")!=p520.get("original_padding_zero_byte_count") or
        p551.get("synthetic_remaining_sector_padding_zero_bytes")!=p520.get("candidate_remaining_bytes") or
        p551.get("original_pal_ZDIR_in_ram_resource_lookup_verified") is not True or
        p551.get("actual_game_guest_loader_executed") is not False or
        p551.get("actual_game_guest_VLT_ExpN_RefSpec_accepted") is not False or
        p551.get("BMW_tuning_enabled") is not False or
        prior.get("status")!="AUDIT_OK" or
        prior.get("new_total_bytes")!=840568 or
        prior.get("new_sha256")!="95932aaf08cd9e85f00f208441a1fa3399d379c2711cba212a66b9ec11f360c9"):
        raise ValueError("PRE553 original PRE520 padding and PRE551 independent recheck disagree; cannot apply chronology correction")
    metadata=get_meta(drive)
    if (metadata.get("id")!=FILE_ID or metadata.get("name")!=FILE_NAME
        or metadata.get("mimeType")!="text/markdown"
        or metadata.get("parents")!=[PARENT]
        or not 840000<=int(metadata.get("size",0))<=2000000):
        raise ValueError("Unexpected canonical file name, folder, MIME, ID or size")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(metadata["size"]):
        raise ValueError("Canonical Drive metadata/contents size mismatch")
    previous_text=before.decode("utf-8")
    if previous_text.count(PREVIOUS)!=1:
        raise ValueError("PRE480 append history missing or repeated")
    if MARKER in previous_text:
        return {"status":"ALREADY_APPLIED","backup_created":False,
                "canonical_file_id":FILE_ID,"current_bytes":len(before),
                "current_sha256":sha(before),"verified_existing_marker":True}
    if not HANDOFF.is_file():raise ValueError("PRE553 exact GitHub handoff not found")
    handoff=HANDOFF.read_bytes()
    if not 2500<=len(handoff)<=16000 or handoff.count(MARKER.encode())!=1:
        raise ValueError("Unexpected PRE553 handoff identity/length")
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
        raise ValueError("PRE553 backup failed byte-for-byte verification")
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
    result={"stage":"PRE553_CANONICAL_CONTEXT_APPEND_WITH_BACKUP",
            "status":"FAILED","apk_built":False,"save_modified":False,
            "game_assets_modified":False}
    try:result.update(sync(drive_client()))
    except Exception as exc:result.update({"error_type":type(exc).__name__,
                                          "error":str(exc)[:280]})
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE553_STATUS",result["status"],flush=True)
    print("PRE553_BACKUP_ID",result.get("backup_file_id","none"),flush=True)
    print("PRE553_READBACK",result.get("postupdate_readback_bytewise_verified",False),flush=True)
    print("PRE553_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
