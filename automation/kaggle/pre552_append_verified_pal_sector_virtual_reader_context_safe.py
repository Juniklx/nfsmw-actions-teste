#!/usr/bin/env python3
"""PRE552: backup-first append handoff to canonical CONTEXTO_NFSMW.md in Drive.

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

OUT=Path("/tmp/nfsmw-pre552/report.json")
HANDOFF=Path("docs/PRE552_BMW_TUNING_PRE551_PAL_ZZDATA4_FULL_CRC_RAM_VIRTUAL_RESOURCE_GATE_20261108.md")
MARKER="PRE552_BMW_TUNING_PRE551_PAL_ZZDATA4_FULL_CRC_RAM_VIRTUAL_RESOURCE_GATE_20261108"
PREVIOUS="PRE550_BMW_TUNING_PRE548_PRE549_PVEHICLE_HASH_ACCESSOR_GATE_20261108"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE552_BMW_TUNING_20261108.md"
FILE_NAME="CONTEXTO_NFSMW.md"

def sync(drive):
    p551=json.loads(Path("docs/PRE551_PAL_ORIGINAL_ZZDATA4_PADDING_AND_VIRTUAL_RESOURCE_READONLY.json").read_text())
    prior=json.loads(Path("docs/PRE550_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (p551.get("status")!="AUDIT_OK" or
        p551.get("PAL_game_original_ZIP_id")!="1sF5irZpUNfN5Z2p4L53eMVISBeh8MfRz" or
        p551.get("source_pal_original_VPAK_sha256")!="9f4b04a221232e614b927a870e25da7db100477a7e425114b87082f46e8b99ad" or
        p551.get("source_pal_original_VPAK_bytes")!=697856 or
        p551.get("source_pal_original_EA_resource_hash_hex")!="296ad9ed" or
        p551.get("source_PAL_original_ZDIR_sha256")!="7f37d29f958454ec73d5dbd30068a6acb23cf92d5056fa2d944ca5c87c6637ee" or
        p551.get("zip_original_ZZDATA4_uncompressed_bytes")!=401068032 or
        p551.get("zip_original_ZZDATA4_compressed_bytes_read")!=261097565 or
        p551.get("zip_original_ZZDATA4_CRC32_hex")!="b46a396c" or
        p551.get("original_pal_ZZDATA4_expected_CRC32_validated") is not True or
        p551.get("original_resource_reserved_sector_bytes_captured")!=698368 or
        p551.get("original_pal_ZZDATA_sector_padding_all_zero_verified") is not True or
        p551.get("original_pal_ZZDATA_sector_padding_zero_bytes")!=512 or
        p551.get("synthetic_remaining_sector_padding_zero_bytes")!=364 or
        p551.get("isolated_synthetic_RAM_resource_readback_SHA256")!="d4fa0e98ba9bd2ee637d768d00a42d7e5a06c6d74df4581d6730f98dad31d8f6" or
        p551.get("isolated_synthetic_RAM_ZDIR_EA_hash_hex")!="4d05584a" or
        p551.get("synthetic_ZDIR_record_sha256")!="6d0b1744073a50756dcdd296ff5c7ede7dfba35b7a9928e0de5be28f3a18fa78" or
        p551.get("original_pal_ZDIR_in_ram_resource_lookup_verified") is not True or
        p551.get("actual_game_guest_loader_executed") is not False or
        p551.get("actual_game_guest_VLT_ExpN_RefSpec_accepted") is not False or
        p551.get("actual_game_engine_power_modified") is not False or
        p551.get("on_device_ISO_selection_verified") is not False or
        p551.get("runtime_purchase_or_save_persistence_verified") is not False or
        p551.get("no_original_game_file_written_or_changed") is not True or
        p551.get("BMW_tuning_enabled") is not False or
        prior.get("status")!="AUDIT_OK" or
        prior.get("new_total_bytes")!=834187 or
        prior.get("new_sha256")!="33733023e743cac5cc8206fe45891455e6f8d3c951b9d7cdae835f3765f7b72d"):
        raise ValueError("PRE551 PAL full-ZZDATA4, virtual-read, actual-loader caution or PRE550 canonical identity gate failed")
    metadata=get_meta(drive)
    if (metadata.get("id")!=FILE_ID or metadata.get("name")!=FILE_NAME
        or metadata.get("mimeType")!="text/markdown"
        or metadata.get("parents")!=[PARENT]
        or not 834000<=int(metadata.get("size",0))<=2000000):
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
    if not HANDOFF.is_file():raise ValueError("PRE552 exact GitHub handoff not found")
    handoff=HANDOFF.read_bytes()
    if not 2500<=len(handoff)<=16000 or handoff.count(MARKER.encode())!=1:
        raise ValueError("Unexpected PRE552 handoff identity/length")
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
        raise ValueError("PRE552 backup failed byte-for-byte verification")
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
    result={"stage":"PRE552_CANONICAL_CONTEXT_APPEND_WITH_BACKUP",
            "status":"FAILED","apk_built":False,"save_modified":False,
            "game_assets_modified":False}
    try:result.update(sync(drive_client()))
    except Exception as exc:result.update({"error_type":type(exc).__name__,
                                          "error":str(exc)[:280]})
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE552_STATUS",result["status"],flush=True)
    print("PRE552_BACKUP_ID",result.get("backup_file_id","none"),flush=True)
    print("PRE552_READBACK",result.get("postupdate_readback_bytewise_verified",False),flush=True)
    print("PRE552_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
