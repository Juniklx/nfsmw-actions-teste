#!/usr/bin/env python3
"""PRE550: backup-first append handoff to canonical CONTEXTO_NFSMW.md in Drive.

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

OUT=Path("/tmp/nfsmw-pre550/report.json")
HANDOFF=Path("docs/PRE550_BMW_TUNING_PRE548_PRE549_PVEHICLE_HASH_ACCESSOR_GATE_20261108.md")
MARKER="PRE550_BMW_TUNING_PRE548_PRE549_PVEHICLE_HASH_ACCESSOR_GATE_20261108"
PREVIOUS="PRE547_BMW_TUNING_PRE544_PRE546_FLOAT_OUTPUT_STACK_ALIAS_REDIRECT_20261108"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE550_BMW_TUNING_20261108.md"
FILE_NAME="CONTEXTO_NFSMW.md"

def sync(drive):
    p548=json.loads(Path("docs/PRE548_ORIGINAL_PAL_GUEST_PVEHICLE_UPGRADE_FIELD_XREFS_READONLY.json").read_text())
    p549=json.loads(Path("docs/PRE549_PAL_GUEST_PVEHICLE_CLASS_HASH_ACCESSOR_READONLY.json").read_text())
    prior=json.loads(Path("docs/PRE547_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    sha99="af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39"
    pveh=p548.get("guest_PPC_lis_then_ori_or_addi_hash_candidate_counts",{}).get("pvehicle",{})
    engine=p548.get("guest_PPC_lis_then_ori_or_addi_hash_candidate_counts",{}).get("engine",{})
    if (p548.get("status")!="AUDIT_OK" or
        p548.get("PRE99_archive_sha256")!=sha99 or
        p548.get("original_guest_shards_scanned")!=129 or
        p548.get("original_guest_functions_scanned")!=56338 or
        p548.get("verified_original_pal_vpak_pvehicle_class_hash")!="4a97ec8f" or
        p548.get("guest_same_base_five_or_more_counter_offsets_match_count")!=159 or
        p548.get("guest_same_base_five_or_more_offsets_with_lwz_or_stw_store_count")!=139 or
        pveh.get("matches_total")!=16 or
        engine.get("matches_total")!=18 or
        p548.get("counter_fields_are_UPGRADE_AVAILABILITY_not_installed_package") is not True or
        p548.get("guest_PhysicsUpgrades_SetPackage_address_identified") is not False or
        p548.get("BMW_tuning_enabled") is not False or
        p549.get("status")!="AUDIT_OK" or
        p549.get("original_PRE99_archive_sha256")!=sha99 or
        p549.get("original_guest_codegen_shards_scanned")!=129 or
        p549.get("original_guest_functions_audited")!=14 or
        p549.get("pvehicle_hash_materializing_function_count")!=13 or
        p549.get("pvehicle_hash_construction_site_count")!=16 or
        p549.get("class_lookup_candidate_direct_guest_callee")!="sub_8214D958" or
        p549.get("class_lookup_candidate_original_guest_record",{}).get("guest_numeric_function")!="sub_821E02C0" or
        p549.get("original_signed_V48_PAL_pvehicle_getter_same_guest_callee_confirmed") is not True or
        p549.get("original_signed_V48_PAL_getter_reachable_from_shop_and_historical_field_writer") is not True or
        p549.get("direct_guest_SetPackage_or_checkout_identity_proven") is not False or
        p549.get("BMW_tuning_enabled") is not False or
        prior.get("status")!="AUDIT_OK" or
        prior.get("new_total_bytes")!=827240 or
        prior.get("new_sha256")!="b36481f30c4923a4d7bb81c3173ea2b44451456134b2e809d78a4113a19768e2"):
        raise ValueError("PRE548/549 authenticated original guest class/offset evidence or PRE547 exact Drive SHA changed")
    metadata=get_meta(drive)
    if (metadata.get("id")!=FILE_ID or metadata.get("name")!=FILE_NAME
        or metadata.get("mimeType")!="text/markdown"
        or metadata.get("parents")!=[PARENT]
        or not 827000<=int(metadata.get("size",0))<=2000000):
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
    if not HANDOFF.is_file():raise ValueError("PRE550 exact GitHub handoff not found")
    handoff=HANDOFF.read_bytes()
    if not 2500<=len(handoff)<=16000 or handoff.count(MARKER.encode())!=1:
        raise ValueError("Unexpected PRE550 handoff identity/length")
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
        raise ValueError("PRE550 backup failed byte-for-byte verification")
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
    result={"stage":"PRE550_CANONICAL_CONTEXT_APPEND_WITH_BACKUP",
            "status":"FAILED","apk_built":False,"save_modified":False,
            "game_assets_modified":False}
    try:result.update(sync(drive_client()))
    except Exception as exc:result.update({"error_type":type(exc).__name__,
                                          "error":str(exc)[:280]})
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE550_STATUS",result["status"],flush=True)
    print("PRE550_BACKUP_ID",result.get("backup_file_id","none"),flush=True)
    print("PRE550_READBACK",result.get("postupdate_readback_bytewise_verified",False),flush=True)
    print("PRE550_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
