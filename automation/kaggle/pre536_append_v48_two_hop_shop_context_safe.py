#!/usr/bin/env python3
"""PRE536: backup-first append handoff to canonical CONTEXTO_NFSMW.md in Drive.

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

OUT=Path("/tmp/nfsmw-pre536/report.json")
HANDOFF=Path("docs/PRE536_BMW_TUNING_PRE535_SIGNED_V48_TWO_HOP_SHOP_XREF_20261108.md")
MARKER="PRE536_BMW_TUNING_PRE535_SIGNED_V48_TWO_HOP_SHOP_XREF_20261108"
PREVIOUS="PRE534_BMW_TUNING_PRE531_PRE533_V48_PAL_ELF_GUEST_CALLGRAPH_20261108"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE536_BMW_TUNING_20261108.md"
FILE_NAME="CONTEXTO_NFSMW.md"

def sync(drive):
    p535=json.loads(Path("docs/PRE535_V48_PAL_SHOP_TWO_HOP_PLT_GRAPH_READONLY.json").read_text())
    prior=json.loads(Path("docs/PRE534_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    original_apk_sha="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
    original_pal_sha="f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3"
    if (p535.get("status")!="AUDIT_OK" or
        p535.get("published_original_V48_apk_sha256")!=original_apk_sha or
        p535.get("published_original_V48_PAL_libmain_sha256")!=original_pal_sha or
        p535.get("original_elf_numeric_guest_function_count")!=56338 or
        p535.get("original_elf_PLT_jump_slot_count")!=17107 or
        p535.get("original_elf_guest_PLT_relocation_count")!=15598 or
        p535.get("original_elf_relocation_types")!={"1026":17107} or
        p535.get("target_root_count")!=5 or
        p535.get("first_hop_neighbor_functions_inspected")!=72 or
        p535.get("total_distinct_functions_inspected")!=76 or
        p535.get("guest_root_two_hop_intersection_count")!=12 or
        p535.get("all_intersections_are_static_and_not_symbol_semantics") is not True or
        p535.get("guest_SetPackage_guest_address_proven") is not False or
        p535.get("guest_checkout_transaction_path_proven") is not False or
        p535.get("guest_BMW_engine_refspec_accepted") is not False or
        p535.get("BMW_tuning_enabled") is not False or
        prior.get("status")!="AUDIT_OK" or
        prior.get("new_total_bytes")!=800575 or
        prior.get("new_sha256")!="3000382209442332af4a9dba75133cbbdf889583c8efcef8102159a86d600867"):
        raise ValueError("PRE535 original V48 signed-ELF two-hop evidence or PRE534 canonical hash differs")
    metadata=get_meta(drive)
    if (metadata.get("id")!=FILE_ID or metadata.get("name")!=FILE_NAME
        or metadata.get("mimeType")!="text/markdown"
        or metadata.get("parents")!=[PARENT]
        or not 800000<=int(metadata.get("size",0))<=2000000):
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
    if not HANDOFF.is_file():raise ValueError("PRE536 exact GitHub handoff not found")
    handoff=HANDOFF.read_bytes()
    if not 2500<=len(handoff)<=16000 or handoff.count(MARKER.encode())!=1:
        raise ValueError("Unexpected PRE536 handoff identity/length")
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
        raise ValueError("PRE536 backup failed byte-for-byte verification")
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
    result={"stage":"PRE536_CANONICAL_CONTEXT_APPEND_WITH_BACKUP",
            "status":"FAILED","apk_built":False,"save_modified":False,
            "game_assets_modified":False}
    try:result.update(sync(drive_client()))
    except Exception as exc:result.update({"error_type":type(exc).__name__,
                                          "error":str(exc)[:280]})
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE536_STATUS",result["status"],flush=True)
    print("PRE536_BACKUP_ID",result.get("backup_file_id","none"),flush=True)
    print("PRE536_READBACK",result.get("postupdate_readback_bytewise_verified",False),flush=True)
    print("PRE536_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
