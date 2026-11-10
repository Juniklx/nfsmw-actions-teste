#!/usr/bin/env python3
"""PRE640 canonical context append: V50 PRE638 signed and Drive uploaded; phone test pending.
Backup verified original first; byte-exact idempotent append only.
No APK, signing key, game source, ISO or save changes.
"""
from __future__ import annotations
import argparse,hashlib,io,json,time
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

EXPECTED_BYTES=983596
EXPECTED_SHA="7b5b5d979b8dc63ca179392cb8c4f183e869ddc77f645aec20b0c9651f2da92d"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE640_V50_SIGNED_20261110.md"
HANDOFF=Path("docs/PRE640_HANDOFF_V50_PRE638_SIGNED_DRIVE_VERIFIED_TEST_PENDING_20261110.md")
MARKER="# PRE640 — V50 PRE638 compilada".encode("utf-8")
PRE638=Path("docs/PRE638_V50_SIGNED_RELEASE_RESULT.json")
OUT=Path("/tmp/nfsmw-pre640/report.json")
def sha(b):return hashlib.sha256(b).hexdigest()

def validate_evidence():
    record=json.loads(PRE638.read_text(encoding="utf-8"))
    app=record.get("app",{})
    gates=record.get("gates",{})
    runtime=record.get("runtime",{})
    expected_gates=("gradle_release_succeeded","signed_apk_verified",
        "permanent_certificate_verified","apk_v2_certificate_verified",
        "apk_zip_crc_verified","arm64_markers_verified",
        "all_four_bmw_callbacks_exported_once","pal_usa_shaders_preserved",
        "pre398_nitro_marker_present","pre194_c3_guard_present",
        "pre635_trace_marker_present","drive_upload_success",
        "drive_upload_remote_md5_matches")
    if not (
        record.get("status")=="PRE638_V50_SIGNED_DIAGNOSTIC_VERIFIED"
        and record.get("run_id")=="42748358853"
        and record.get("run_conclusion")=="success"
        and app.get("drive_file_id")=="1mxqUtzhAWDc6zeJt5cwJrhsWzfOnNucC"
        and app.get("size_bytes")==47104881
        and app.get("sha256")=="7c49f6c95af5bf20b81c2df0622ce236532edadc70d4619e12021e87b74df4fe"
        and app.get("md5")=="9d4754757fed72fa62b4cfce871af6a1"
        and app.get("version_code")==50
        and app.get("package_id")=="io.github.nfsmwrecomp"
        and app.get("certificate_sha256")=="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
        and app.get("native_libmain_sha256")=="0032ea2058f0400a1c06a948fa1c649cea45e941000bb787c10c8e350924bb4a"
        and all(gates.get(x) is True for x in expected_gates)
        and gates.get("c3_fallback_bypass") is False
        and runtime.get("v50_gameplay_tested") is False
        and runtime.get("fps_gain_verified") is False
    ):
        raise ValueError("PRE638 release evidence invalid; not touching canonical context")
    handoff=HANDOFF.read_bytes()
    if (handoff.count(MARKER)!=1
        or b"42748358853" not in handoff
        or b"PRE638" not in handoff
        or b"nfsmw.log" not in handoff
        or b"7c49f6c95af5bf20b81c2df0622ce236532edadc70d4619e12021e87b74df4fe" not in handoff
        or not (3200<=len(handoff)<=9000)):
        raise ValueError("PRE640 handoff incomplete or missing signed APK facts")
    return handoff

def audit():
    handoff=validate_evidence()
    appendix=b"\n\n---\n\n"+handoff
    drive=drive_client()
    meta=get_meta(drive)
    if (meta.get("id")!=FILE_ID or meta.get("name")!="CONTEXTO_NFSMW.md"
        or meta.get("mimeType")!="text/markdown"
        or meta.get("parents")!=[PARENT]):
        raise ValueError("Canonical context metadata unexpected")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):raise ValueError("Canonical size mismatch")
    if MARKER in before:
        if (before.count(MARKER)!=1 or not before.endswith(appendix)
            or len(before)-len(appendix)!=EXPECTED_BYTES
            or sha(before[:-len(appendix)])!=EXPECTED_SHA):
            raise ValueError("Existing PRE640 not byte-exactly idempotent")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
            "canonical_bytes":len(before),"canonical_sha256":sha(before),
            "readback_identical":True}
    if (len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA
        or before.count(b"# PRE639")!=1):
        raise ValueError("Canonical context changed or PRE639 checkpoint missing: no write")
    # Independently confirm the exact V50 archive already exists on canonical Drive.
    info=json.loads(PRE638.read_text(encoding="utf-8"))
    app=info["app"]
    remote=drive.files().get(fileId=app["drive_file_id"],supportsAllDrives=True,
        fields="id,name,size,md5Checksum,parents,trashed").execute()
    if not (remote.get("id")==app["drive_file_id"]
        and remote.get("name")==app["name"]
        and int(remote.get("size",-1))==app["size_bytes"]
        and remote.get("md5Checksum","").lower()==app["md5"]
        and remote.get("parents")==[app["parent_folder_id"]]
        and remote.get("trashed") is False):
        raise ValueError("PRE638 signed APK Drive identity/size/MD5 mismatch; no context write")
    expected=before+appendix
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},
       fields="id,name,size,parents").execute()
    backup_id=backup["id"]
    if (int(backup.get("size",-1))!=EXPECTED_BYTES
       or get_bytes(drive,backup_id)!=before):
        raise ValueError("Context backup not readback-identical; no overwrite")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("Concurrent editor changed context before write")
    for attempt in range(3):
        current=get_bytes(drive,FILE_ID)
        if current==expected:break
        if current!=before:raise ValueError("Concurrent context change during append")
        try:
            drive.files().update(fileId=FILE_ID,supportsAllDrives=True,
              media_body=MediaIoBaseUpload(io.BytesIO(expected),
              mimetype="text/markdown",resumable=False),
              fields="id,name,size,modifiedTime").execute()
        except HttpError as e:
            if e.resp.status not in (500,502,503,504) or attempt==2:raise
            if get_bytes(drive,FILE_ID)==expected:break
            time.sleep(2*(attempt+1))
    after=get_bytes(drive,FILE_ID)
    if after!=expected or not after.startswith(before) or after.count(MARKER)!=1:
        raise ValueError("PRE640 remote context readback mismatch")
    return {"status":"AUDIT_OK","backup_created":True,
       "backup_file_id":backup_id,"original_sha256":sha(before),
       "canonical_bytes":len(after),"canonical_sha256":sha(after),
       "readback_identical":True,"previous_context_preserved":True}

def main():
    a=argparse.ArgumentParser();a.add_argument("--run-id",required=True)
    opts=a.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:
        r={"status":"FAILED","error_type":type(e).__name__,
            "error":str(e)[:170] if isinstance(e,ValueError) else "Drive context operation failed"}
    r.update({"stage":"PRE640_CANONICAL_CONTEXT_SYNC","run_id":opts.run_id,
      "utc":datetime.now(timezone.utc).isoformat(),"apk_built":False,
      "signing_material_accessed":False,"user_save_modified":False})
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE640_STATUS="+r["status"])
    print("PRE640_CANONICAL_SHA256="+str(r.get("canonical_sha256","none")))
    print("PRE640_BACKUP_CREATED="+str(r.get("backup_created",False)))
    print("PRE640_ERROR_TYPE="+str(r.get("error_type","none")))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1
if __name__=="__main__":raise SystemExit(main())
