#!/usr/bin/env python3
"""PRE603 canonical MD append-only recovery and V48 save-root checkpoint.
Backup first, verify exact existing bytes, append only. No game, APK or save writes.
"""
from __future__ import annotations
import argparse, hashlib, io, json, time
from pathlib import Path
from datetime import datetime, timezone
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID, PARENT, drive_client, get_meta, get_bytes

OUT=Path("/tmp/nfsmw-pre603/report.json")
HANDOFF=Path("docs/PRE602_HANDOFF_PRE599_PRE601_PPC_GUEST_FALSE_POSITIVES_20261109.md")
MARKER=b"PRE602_HANDOFF_PRE599_PRE601_PPC_GUEST_FALSE_POSITIVES_20261109"
PREVIOUS_MARKER=b"PRE597_HANDOFF_PRE592_DEVICE_LOAD_AND_COUNTER_ONE_BYTE_20261109"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE603_PPC_GUEST_FALSE_POSITIVES_20261109.md"
EXPECTED_BYTES=915789
EXPECTED_SHA="879e842da9e1360c2b7f274f4cf4b94af3c1eba9dc5ae6a78942247bf7ff9aab"
def sha(b):return hashlib.sha256(b).hexdigest()
def verify_earlier_reports():
    previous=json.loads(Path("docs/PRE598_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    p599=json.loads(Path("docs/PRE599_BMW_GUEST_COUNTER_PPC_PROVENANCE_READONLY.json").read_text())
    p600=json.loads(Path("docs/PRE600_GUEST_COUNTER_BRANCH_CANDIDATES_READONLY.json").read_text())
    p601=json.loads(Path("docs/PRE601_TWO_GUEST_COUNTER_FUNCTION_CALLERS_READONLY.json").read_text())
    handoff=HANDOFF.read_text(encoding="utf-8")
    if (any(x.get("status")!="AUDIT_OK" for x in (previous,p599,p600,p601))
        or previous.get("canonical_bytes")!=EXPECTED_BYTES
        or previous.get("canonical_sha256")!=EXPECTED_SHA
        or previous.get("new_handoff_readback_verified") is not True
        or p599.get("guest_function_count")!=56338
        or p599.get("exact_GetMaxLevel_identity_proven") is not False
        or p600.get("generated_files_visited")!=129
        or p600.get("engine_counter_offset_40_load_site_count_across_all_56k")!=1587
        or p600.get("vtable_dispatch_shape_count")!=193
        or p600.get("candidate_direct_compare_branch_non_vtable_count")!=512
        or p600.get("exact_GetMaxLevel_function_identified") is not False
        or p601.get("direct_caller_counts")!={"sub_8216A928":1,"sub_821EFC18":0}
        or p601.get("GetMaxLevel_identified") is not False
        or p601.get("pvehicle_base_register_proven") is not False
        or p601.get("original_generated_source_uploaded") is not False
        or "PRE601" not in handoff
        or "PRE592_RESTORE=ORIGINAIS_VERIFICADOS" not in handoff
        or "af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39" not in handoff):
        raise ValueError("PRE598/PRE599/PRE600/PRE601 evidence missing or unsupported semantics")

def audit():
    verify_earlier_reports()
    extra=b"\n\n---\n\n"+HANDOFF.read_bytes()
    if extra.count(MARKER)!=1 or not (2300<=len(extra)<=13000):
        raise ValueError("PRE603 handoff is incomplete or duplicated")
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
            raise ValueError("Existing PRE603 append not byte-exact or unexpected original")
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
        raise ValueError("Canonical context changed since PRE598: stop without update")
    expected=before+extra
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[PARENT]},
      fields="id,name,parents,size").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
        or get_bytes(drive,backup_id)!=before):
        raise ValueError("Backup PRE603 not bytewise identical: source untouched")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent Drive edit before PRE603 append")
    transient=0
    for attempt in range(3):
        state=get_bytes(drive,FILE_ID)
        if state==expected:break
        if state!=before:raise ValueError("Concurrent context changes during PRE603")
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
        raise ValueError("PRE603 canonical append did not pass bytewise readback")
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
       "stage":"PRE603_CANONICAL_SAVE_ROOT_CONTEXT_SYNC",
       "status":"FAILED","APK_built":False,
       "game_assets_modified":False,"save_modified":False,
       "signing_material_accessed":False,"BMW_tuning_enabled":False
    }
    try:r.update(audit())
    except Exception as e:r.update({"error_type":type(e).__name__,"error":str(e)[:260]})
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE603_STATUS",r["status"],flush=True)
    print("PRE603_READBACK",r.get("new_handoff_readback_verified",False),flush=True)
    print("PRE603_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
