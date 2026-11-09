#!/usr/bin/env python3
"""PRE538: backup-first append handoff to canonical CONTEXTO_NFSMW.md in Drive.

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

OUT=Path("/tmp/nfsmw-pre538/report.json")
HANDOFF=Path("docs/PRE538_BMW_TUNING_PRE537_SIGNED_V48_PAL_SHARED_FUNCTION_BREADTH_20261108.md")
MARKER="PRE538_BMW_TUNING_PRE537_SIGNED_V48_PAL_SHARED_FUNCTION_BREADTH_20261108"
PREVIOUS="PRE536_BMW_TUNING_PRE535_SIGNED_V48_TWO_HOP_SHOP_XREF_20261108"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE538_BMW_TUNING_20261108.md"
FILE_NAME="CONTEXTO_NFSMW.md"

def sync(drive):
    p537=json.loads(Path("docs/PRE537_ORIGINAL_V48_PAL_SHARED_NODES_STRUCTURAL_TRIAGE_READONLY.json").read_text())
    prior=json.loads(Path("docs/PRE536_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    expected_apk="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
    expected_pal="f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3"
    if (p537.get("status")!="AUDIT_OK" or
        p537.get("original_signed_V48_APK_sha256")!=expected_apk or
        p537.get("original_signed_V48_PAL_libmain_sha256")!=expected_pal or
        p537.get("ELF_PLT_relocation_count")!=17107 or
        p537.get("ELF_guest_Plt_mapping_count")!=15598 or
        p537.get("ELF_guest_numeric_function_count")!=56338 or
        p537.get("all_guest_exported_bodies_scanned")!=56338 or
        p537.get("all_guest_exported_bodies_skipped_by_bounds")!=0 or
        p537.get("all_resolved_guest_BL_calls_seen")!=76786 or
        p537.get("audited_PRE535_shared_numeric_function_count")!=12 or
        p537.get("metrics_support_only_breadth_not_function_identity") is not True or
        p537.get("historical_field12_writes_proven_cash_debit") is not False or
        p537.get("candidate_SetPackage_identified") is not False or
        p537.get("actual_runtime_checkout_installation_or_save_verified") is not False or
        p537.get("safe_to_enable_BMW_tuning") is not False or
        prior.get("status")!="AUDIT_OK" or
        prior.get("new_total_bytes")!=805726 or
        prior.get("new_sha256")!="ad8ff437d106d920d20e60756a769794029ca95169e54bab4a8dd96047c44e63"):
        raise ValueError("PRE538 exact signed PAL structure or prior canonical identity gate failed")
    metadata=get_meta(drive)
    if (metadata.get("id")!=FILE_ID or metadata.get("name")!=FILE_NAME
        or metadata.get("mimeType")!="text/markdown"
        or metadata.get("parents")!=[PARENT]
        or not 805000<=int(metadata.get("size",0))<=2000000):
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
    if not HANDOFF.is_file():raise ValueError("PRE538 exact GitHub handoff not found")
    handoff=HANDOFF.read_bytes()
    if not 2500<=len(handoff)<=16000 or handoff.count(MARKER.encode())!=1:
        raise ValueError("Unexpected PRE538 handoff identity/length")
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
        raise ValueError("PRE538 backup failed byte-for-byte verification")
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
    result={"stage":"PRE538_CANONICAL_CONTEXT_APPEND_WITH_BACKUP",
            "status":"FAILED","apk_built":False,"save_modified":False,
            "game_assets_modified":False}
    try:result.update(sync(drive_client()))
    except Exception as exc:result.update({"error_type":type(exc).__name__,
                                          "error":str(exc)[:280]})
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE538_STATUS",result["status"],flush=True)
    print("PRE538_BACKUP_ID",result.get("backup_file_id","none"),flush=True)
    print("PRE538_READBACK",result.get("postupdate_readback_bytewise_verified",False),flush=True)
    print("PRE538_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
