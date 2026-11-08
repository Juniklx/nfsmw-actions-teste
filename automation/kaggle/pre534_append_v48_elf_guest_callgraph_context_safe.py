#!/usr/bin/env python3
"""PRE534: backup-first append handoff to canonical CONTEXTO_NFSMW.md in Drive.

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

OUT=Path("/tmp/nfsmw-pre534/report.json")
HANDOFF=Path("docs/PRE534_BMW_TUNING_PRE531_PRE533_V48_PAL_ELF_GUEST_CALLGRAPH_20261108.md")
MARKER="PRE534_BMW_TUNING_PRE531_PRE533_V48_PAL_ELF_GUEST_CALLGRAPH_20261108"
PREVIOUS="PRE530_BMW_TUNING_PRE528_PRE529_GUEST_PAL_CALLGRAPH_20261108"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE534_BMW_TUNING_20261108.md"
FILE_NAME="CONTEXTO_NFSMW.md"

def sync(drive):
    p531=json.loads(Path("docs/PRE531_ORIGINAL_V48_PAL_GUEST_ELF_SYMBOLS_READONLY.json").read_text())
    p532=json.loads(Path("docs/PRE532_AUTHENTIC_V48_PAL_GUEST_ARM64_CALLGRAPH_READONLY.json").read_text())
    p533=json.loads(Path("docs/PRE533_ORIGINAL_V48_PAL_GUEST_RELOCATED_PLT_CALLGRAPH_READONLY.json").read_text())
    previous=json.loads(Path("docs/PRE530_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    original_apk_sha="c642f95b4a60b9ccf5d8fbd98802afffc0a2247ec5a0783b54cd8083ec55bd35"
    original_pal_elf_sha="f39870144295c98cb05b9e8649a378e968fccb5bf479b653d0654158e92316a3"
    expected_pal_count=9
    libs=p531.get("libraries",[])
    pal=next((x for x in libs if x.get("zip_entry")=="lib/arm64-v8a/libmain.so"),None)
    if (p531.get("status")!="AUDIT_OK" or
        p532.get("status")!="AUDIT_OK" or
        p533.get("status")!="AUDIT_OK" or
        previous.get("status")!="AUDIT_OK" or
        previous.get("new_total_bytes")!=793913 or
        previous.get("new_sha256")!="a73e5ca586866f89496c23cabc16870245328c56a6416e3ae0f56f6c4da58afa" or
        p531.get("original_V48_apk_sha256")!=original_apk_sha or
        p531.get("authenticated_exact_V48_apk") is not True or
        not pal or pal.get("sha256")!=original_pal_elf_sha or
        len([x for x in pal.get("guest_target_elf_symbol_matches",{}).values() if len(x)==2])!=expected_pal_count or
        p531.get("guest_SetPackage_function_identity_verified") is not False or
        p532.get("exact_published_V48_apk_sha256")!=original_apk_sha or
        p532.get("aggregate_direct_BL_in_targets")!=189 or
        p532.get("source_matched_guest_calls_total")!=0 or
        p533.get("exact_published_V48_apk_sha256")!=original_apk_sha or
        p533.get("original_PAL_libmain_sha256")!=original_pal_elf_sha or
        p533.get("original_PAL_ELF_PLT_canonical_layout_verified") is not True or
        p533.get("original_PAL_ELF_rela_PLT_record_count")!=17107 or
        p533.get("original_PAL_ELF_guest_PLT_relocation_name_count")!=15598 or
        p533.get("original_PAL_ELF_rela_PLT_types")!={"1026":17107} or
        p533.get("source_matched_guest_calls_total")!=164 or
        p533.get("guest_Xbox_360_SetPackage_address_identified") is not False or
        p533.get("safe_to_patch_or_buy_BMW") is not False):
        raise ValueError("PRE534 exact original V48 ELF provenance, PLT xref or release-safety proof failed")
    metadata=get_meta(drive)
    if (metadata.get("id")!=FILE_ID or metadata.get("name")!=FILE_NAME
        or metadata.get("mimeType")!="text/markdown"
        or metadata.get("parents")!=[PARENT]
        or not 793000<=int(metadata.get("size",0))<=2000000):
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
    if not HANDOFF.is_file():raise ValueError("PRE534 exact GitHub handoff not found")
    handoff=HANDOFF.read_bytes()
    if not 2500<=len(handoff)<=16000 or handoff.count(MARKER.encode())!=1:
        raise ValueError("Unexpected PRE534 handoff identity/length")
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
        raise ValueError("PRE534 backup failed byte-for-byte verification")
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
    result={"stage":"PRE534_CANONICAL_CONTEXT_APPEND_WITH_BACKUP",
            "status":"FAILED","apk_built":False,"save_modified":False,
            "game_assets_modified":False}
    try:result.update(sync(drive_client()))
    except Exception as exc:result.update({"error_type":type(exc).__name__,
                                          "error":str(exc)[:280]})
    result["run_id"]=args.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE534_STATUS",result["status"],flush=True)
    print("PRE534_BACKUP_ID",result.get("backup_file_id","none"),flush=True)
    print("PRE534_READBACK",result.get("postupdate_readback_bytewise_verified",False),flush=True)
    print("PRE534_ERROR",result.get("error","none"),flush=True)
    return 0 if result["status"] in ("AUDIT_OK","ALREADY_APPLIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
