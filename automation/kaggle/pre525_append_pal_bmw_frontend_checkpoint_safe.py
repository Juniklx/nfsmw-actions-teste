#!/usr/bin/env python3
"""PRE525: backup-first append handoff to canonical CONTEXTO_NFSMW.md in Drive.

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

OUT=Path("/tmp/nfsmw-pre525/report.json")
HANDOFF=Path("docs/PRE525_BMW_TUNING_PRE520_PRE524_PAL_FRONTEND_PRICING_HANDOFF_20261108.md")
MARKER="PRE525_BMW_TUNING_PRE520_PRE524_PAL_FRONTEND_PRICING_HANDOFF_20261108"
PREVIOUS="PRE519_BMW_TUNING_PRE517_PRE518_ZDIR_EA_CHECKSUM_HANDOFF_20261108"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE525_BMW_TUNING_20261108.md"
FILE_NAME="CONTEXTO_NFSMW.md"

def sync(drive):
    proof520=json.loads(Path("docs/PRE520_ORIGINAL_PAL_ZZDATA4_SECTOR_PADDING_READONLY.json").read_text())
    proof521=json.loads(Path("docs/PRE521_USA_FE_ATTRIB_FRONTEND_CARPARTS_STRUCTURE_READONLY.json").read_text())
    proof522=json.loads(Path("docs/PRE522_USA_FE_CARPARTS_COST_ARRAYS_READONLY.json").read_text())
    proof523=json.loads(Path("docs/PRE523_ORIGINAL_PAL_FE_ATTRIB_BINARY_IDENTITY_READONLY.json").read_text())
    proof524=json.loads(Path("docs/PRE524_BMW_PC_REFERENCE_FE_PRICE_SCENARIOS_READONLY.json").read_text())
    sha="8ac09099cfc98646bbfbdb261d28b9648e3ec8b0d6bdf9d3edd6ef7bc967b528"
    if (any(x.get("status")!="AUDIT_OK" for x in (proof520,proof521,proof522,proof523,proof524))
        or proof520.get("original_padding_all_zero") is not True
        or proof520.get("original_padding_zero_byte_count")!=512
        or proof520.get("original_loader_acceptance_proven") is not False
        or proof520.get("ready_to_modify_original_game") is not False
        or proof521.get("source_sha256")!=sha
        or proof521.get("original_frontend_collection_count")!=414
        or proof521.get("original_carparts_direct_children_count")!=21
        or proof522.get("original_FE_ATTRIB_sha256")!=sha
        or proof522.get("children_with_valid_FECarPartInfo_array")!=21
        or proof522.get("children_with_category_enum_decoded")!=7
        or proof522.get("actual_BMW_shop_cost_or_purchase_verified") is not False
        or proof523.get("original_PAL_FE_resource_sha256")!=sha
        or proof523.get("original_PAL_FE_same_bytes_as_USA_proven") is not True
        or proof523.get("PAL_runtime_shop_cost_lookups_verified") is not False
        or proof524.get("candidate_BMW_single_engine_package_catalogue_level")!=4
        or proof524.get("candidate_BMW_single_engine_package_USA_reference_cost")!=98000
        or proof524.get("actual_Xbox_guest_unlock_price_formula_verified") is not False
        or proof524.get("BMW_package_purchase_unlock_status_verified") is not False
        or proof524.get("ready_to_enable_BMW_tuning") is not False):
        raise ValueError("PRE525 exact source-price, PAL resource or runtime-gate verification failed")
    metadata=get_meta(drive)
    if (metadata.get("id")!=FILE_ID or metadata.get("name")!=FILE_NAME
        or metadata.get("mimeType")!="text/markdown"
        or metadata.get("parents")!=[PARENT]
        or not 770000<=int(metadata.get("size",0))<=2000000):
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
    if not HANDOFF.is_file():raise ValueError("PRE525 exact GitHub handoff not found")
    handoff=HANDOFF.read_bytes()
    if not 2500<=len(handoff)<=16000 or handoff.count(MARKER.encode())!=1:
        raise ValueError("Unexpected PRE525 handoff identity/length")
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
        raise ValueError("PRE525 backup failed byte-for-byte verification")
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
    result={"stage":"PRE525_CANONICAL_CONTEXT_APPEND_WITH_BACKUP",
            "status":"FAILED","apk_built":False,"save_modified":False,
            "game_assets_modified":False}
    try:result.update(sync(drive_client()))
    except Exception as exc:result.update({"error_type":type(exc).__name__,
                                          "error":str(exc)[:280]})
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE525_STATUS",result["status"],flush=True)
    print("PRE525_BACKUP_ID",result.get("backup_file_id","none"),flush=True)
    print("PRE525_READBACK",result.get("postupdate_readback_bytewise_verified",False),flush=True)
    print("PRE525_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
