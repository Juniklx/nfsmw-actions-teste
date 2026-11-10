#!/usr/bin/env python3
"""PRE655: audited append-only canonical Drive checkpoint.
A PRE652 dispatch is NOT an approved signed APK; do not invent its outcome.
Back up bytes first, abort on any changed concurrent context or provenance.
"""
from __future__ import annotations
import argparse,hashlib,io,json,time
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

EXPECTED_BYTES=1041267
EXPECTED_SHA="372c1146dcac0a5c80818083c33d45ae3d6286727d4f4a742420573d363508a4"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE655_V51_SIGNED_20261110.md"
HANDOFF=Path("docs/PRE655_V51_PRE652_SIGNED_GPU_SHADER_RELEASE_DRIVE_VERIFIED_20261110.md")
RELEASE=Path("docs/PRE652_V51_SIGNED_GPU_SHADER_DIAGNOSTIC_VERIFIED.json")
BUILD=Path("automation/kaggle/pre652_build_signed_v51_gpu_shader_counts_diag.py")
MARKER=b"# PRE655 "
OUT=Path("/tmp/nfsmw-pre655/context_result.json")
def sha(b):return hashlib.sha256(b).hexdigest()

def evidence():
    record=json.loads(RELEASE.read_text(encoding="utf-8"))
    app=record.get("apk",{})
    archive=record.get("archive",{})
    verify=record.get("verification",{})
    limits=record.get("runtime",{})
    if not (
      record.get("stage")=="PRE652_V51_SIGNED_GPU_SHADER_PASS_DRAW_FREQUENCY"
      and record.get("status")=="SIGNED_AND_DRIVE_VERIFIED"
      and record.get("github_run_id")==42798909503
      and record.get("corrected_preflight_run_id")==42798605525
      and app.get("drive_file_id")=="1H3bUAka0s8f7PR0vi2FYj81Pm7uYc6Ws"
      and app.get("name")=="NFSMW_V51_PRE652_GPU_SHADER_PASS_FREQUENCY_DIAGNOSTIC.apk"
      and app.get("bytes")==47104417
      and app.get("sha256")=="207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b"
      and app.get("version_code")==51
      and app.get("package_id")=="io.github.nfsmwrecomp"
      and app.get("permanent_certificate_sha256")=="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
      and app.get("native_pal_libmain_sha256")=="190b0c01f94b6a27f39a2f52a5ad63523ee8e158dd740e182e63a6f8905d234c"
      and archive.get("drive_file_id")=="12uffGCVyOb3Jncg7yTn7kKu8yqg1-0Rw"
      and archive.get("zip_sha256")=="8c471496792465c536e8e73e637a77dd58d35ad0f864b696a09955cee6e5ae6f"
      and verify.get("signed_apk_verified") is True
      and verify.get("independent_drive_redownload_sha256_matched") is True
      and verify.get("four_bmw_callbacks_exported_once") is True
      and verify.get("pal_usa_shader_assets_identical_to_preserved_expected_hashes") is True
      and limits.get("installed_on_samsung_s24_fe") is False
      and limits.get("phone_shader_usage_counts_collected") is False
      and limits.get("fps_gain_verified") is False
    ):
        raise ValueError("PRE655 V51 signed release evidence differs from independent verification")
    content=HANDOFF.read_bytes()
    for term in (
      b"# PRE655 ",b"42798909503",b"42798605525",
      b"1H3bUAka0s8f7PR0vi2FYj81Pm7uYc6Ws",
      b"12uffGCVyOb3Jncg7yTn7kKu8yqg1-0Rw",
      b"207934b667d7023bdbd7334bd448ff0ba1bcf6af5aedf5964f92ef146d127c5b",
      b"1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b",
      b"PRE648 GPU_SHADER10s",
    ):
        if term not in content:raise ValueError("PRE655 required signed artifact evidence missing")
    if not (content.count(MARKER)==1 and 4000<len(content)<10000):
        raise ValueError("PRE655 handoff size/uniqueness invalid")
    return b"\n\n---\n\n"+content

def audit():
    appendix=evidence()
    drive=drive_client()
    meta=get_meta(drive)
    if not (meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
        and meta.get("parents")==[PARENT] and meta.get("mimeType")=="text/markdown"):
        raise ValueError("PRE655 unexpected canonical Drive identity")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):
        raise ValueError("PRE655 Drive metadata size mismatch")
    if MARKER in before:
        if not (before.count(MARKER)==1
          and before.endswith(appendix)
          and len(before)-len(appendix)==EXPECTED_BYTES
          and sha(before[:-len(appendix)])==EXPECTED_SHA):
            raise ValueError("PRE655 conflicting prior append, no write")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
          "canonical_sha256":sha(before),"canonical_bytes":len(before),
          "readback_identical":True}
    if (len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA
        or before.count(b"# PRE654 ")!=1):
        raise ValueError("PRE655 canonical bytes unexpectedly changed; no overwrite")
    target=before+appendix
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},
       fields="id,name,size,parents").execute()
    backup_id=backup["id"]
    if int(backup.get("size",-1))!=EXPECTED_BYTES or get_bytes(drive,backup_id)!=before:
        raise ValueError("PRE655 backup not byte-identical")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("PRE655 canonical context modified before append")
    for attempt in range(3):
        current=get_bytes(drive,FILE_ID)
        if current==target:break
        if current!=before:raise ValueError("PRE655 concurrent update during append")
        try:
            drive.files().update(fileId=FILE_ID,supportsAllDrives=True,
              media_body=MediaIoBaseUpload(io.BytesIO(target),
                 mimetype="text/markdown",resumable=False),
              fields="id,name,size,modifiedTime").execute()
        except HttpError as exc:
            if exc.resp.status not in (500,502,503,504) or attempt==2:raise
            if get_bytes(drive,FILE_ID)==target:break
            time.sleep(2*(attempt+1))
    after=get_bytes(drive,FILE_ID)
    if not (after==target
      and after.startswith(before)
      and after.count(MARKER)==1):
        raise ValueError("PRE655 canonical context readback mismatch")
    return {"status":"AUDIT_OK","backup_created":True,
      "backup_file_id":backup_id,"original_sha256":sha(before),
      "canonical_sha256":sha(after),"canonical_bytes":len(after),
      "readback_identical":True,"prefix_history_unchanged":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True)
    args=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:r=audit()
    except Exception as e:r={"status":"FAILED","error_type":type(e).__name__,
        "error_summary":str(e)[:170] if isinstance(e,ValueError) else "Drive backup/read/write error"}
    r.update({"stage":"PRE655_V51_SIGNED_RELEASE_CONTEXT","run_id":args.run_id,
      "utc":datetime.now(timezone.utc).isoformat(),
      "apk_built":False,"signing_material_accessed":False,"user_saves_modified":False})
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    for key,v in (
      ("STATUS",r["status"]),
      ("CANONICAL_SHA256",r.get("canonical_sha256","none")),
      ("BACKUP_CREATED",r.get("backup_created",False)),
      ("READBACK_IDENTICAL",r.get("readback_identical",False)),
      ("ERROR_TYPE",r.get("error_type","none"))):
        print("PRE655_"+key+"="+str(v))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1

if __name__=="__main__":raise SystemExit(main())
