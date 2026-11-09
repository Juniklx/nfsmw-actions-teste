#!/usr/bin/env python3
"""PRE631 canonical MD append-only recovery and V48 save-root checkpoint.
Backup first, verify exact existing bytes, append only. No game, APK or save writes.
"""
from __future__ import annotations
import argparse, hashlib, io, json, time
from pathlib import Path
from datetime import datetime, timezone
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID, PARENT, drive_client, get_meta, get_bytes

OUT=Path("/tmp/nfsmw-pre631/report.json")
HANDOFF=Path("docs/PRE631_HANDOFF_PRE626_V49_SIGNED_UPLOADED_DIAG_TEST_PENDING_20261109.md")
MARKER="# PRE631 — PRE626 V49 diagnóstica assinada".encode("utf-8")
PREVIOUS_MARKER="# PRE629 — PRE625 ARM64 aprovado".encode("utf-8")
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_PRE631_PRE626_V49_SIGNED_VERIFIED_20261109.md"
EXPECTED_BYTES=965210
EXPECTED_SHA="b2e6d3ead5a123dc69a0d9a1a7fa43565cbd8fb976503714d38d79683441704f"
def sha(b):return hashlib.sha256(b).hexdigest()
def verify_earlier_reports():
    p630=json.loads(Path("docs/PRE630_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    p625=json.loads(Path("docs/PRE625_BMW_HOST_ATTR_ARM64_NATIVE_LINK_RESULT.json").read_text())
    e=p625.get("evidence",{})
    handoff=HANDOFF.read_text(encoding="utf-8")
    if not (p630.get("status")=="AUDIT_OK"
         and p630.get("canonical_bytes")==EXPECTED_BYTES
         and p630.get("canonical_sha256")==EXPECTED_SHA
         and p630.get("new_handoff_readback_verified") is True
         and p625.get("status")=="AUDIT_OK"
         and p625.get("native_arm64_elf") is True
         and e.get("new_callback_exported_exactly_once") is True
         and e.get("previous_3_callbacks_exported_once") is True
         and e.get("new_guest_memory_ops_or_calls")==0
         and p625.get("APK_built") is False
         and "42709319413" in handoff
         and "PRE626_V49_SIGNED_ATTR_DIAGNOSTIC_VERIFIED" in handoff
         and "0fad0c82d9ef5ff591c7f23b32fdab513fe16483756e32a6dd4aab5d4f18447a" in handoff
         and "NÃO instalada/testada" in handoff):
        raise ValueError("PRE631 prior canonical or V49 release evidence mismatch")

def check_remote_v49_apk(drive):
    m=drive.files().get(fileId="1sa__qEk1t6ZF2_qrgy9MZEx6G4ixZpkh",supportsAllDrives=True,
       fields="id,name,size,md5Checksum,parents,trashed").execute()
    if not (m.get("id")=="1sa__qEk1t6ZF2_qrgy9MZEx6G4ixZpkh"
         and m.get("name")=="NFSMW_V49_PRE626_BMW_ATTRIBUTE_VALUE_DIAGNOSTIC.apk"
         and int(m.get("size",-1))==47103605
         and m.get("md5Checksum","").lower()=="395c60462ddeec7fc0b4648016ea32e0"
         and m.get("parents")==["1ac3fI_ahnp3yp7kU4JvsgDdsKkpy5tBh"]
         and m.get("trashed") is False):
        raise ValueError("PRE631 Drive V49 APK identity, folder or MD5 mismatch")

def audit():
    verify_earlier_reports()
    extra=b"\n\n---\n\n"+HANDOFF.read_bytes()
    if extra.count(MARKER)!=1 or not (2300<=len(extra)<=13000):
        raise ValueError("PRE631 handoff is incomplete or duplicated")
    drive=drive_client()
    check_remote_v49_apk(drive)
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
            raise ValueError("Existing PRE631 append not byte-exact or unexpected original")
        return {
          "status":"ALREADY_APPLIED_VERIFIED",
          "apk_drive_md5_verified":True,
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
        raise ValueError("Canonical context changed since PRE628: stop without update")
    expected=before+extra
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
      body={"name":BACKUP_NAME,"parents":[PARENT]},
      fields="id,name,parents,size").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
        or get_bytes(drive,backup_id)!=before):
        raise ValueError("Backup PRE631 not bytewise identical: source untouched")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent Drive edit before PRE631 append")
    transient=0
    for attempt in range(3):
        state=get_bytes(drive,FILE_ID)
        if state==expected:break
        if state!=before:raise ValueError("Concurrent context changes during PRE631")
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
        raise ValueError("PRE631 canonical append did not pass bytewise readback")
    return {
      "status":"AUDIT_OK",
      "apk_drive_md5_verified":True,
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
       "stage":"PRE631_CANONICAL_SAVE_ROOT_CONTEXT_SYNC",
       "status":"FAILED","APK_built":False,
       "game_assets_modified":False,"save_modified":False,
       "signing_material_accessed":False,"BMW_tuning_enabled":False
    }
    try:r.update(audit())
    except Exception as e:r.update({"error_type":type(e).__name__,"error":str(e)[:260]})
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE631_STATUS",r["status"],flush=True)
    print("PRE631_READBACK",r.get("new_handoff_readback_verified",False),flush=True)
    print("PRE631_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
