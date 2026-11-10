#!/usr/bin/env python3
"""PRE657: audited append-only canonical Drive checkpoint.
V51 PRE648 counter execution is demonstrated by first phone log; package-manager versionCode has not been read.
Back up bytes first, abort on any changed concurrent context or provenance.
"""
from __future__ import annotations
import argparse,hashlib,io,json,time
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

EXPECTED_BYTES=1046854
EXPECTED_SHA="7b7ff7175f8a98f8a029a666bbcec8d843f19ca261a1918d443ffb2fde0ccc79"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE657_V51_FIRST_GPU_RUNTIME_LOG_20261110.md"
HANDOFF=Path("docs/PRE657_HANDOFF_PRE656_V51_ONDEVICE_SHADER_LOG_VERIFIED_20261110.md")
RELEASE=Path("docs/PRE656_V51_REAL_SHADER_LOG_VERIFIED.json")
MARKER=b"# PRE657 "
OUT=Path("/tmp/nfsmw-pre657/context_result.json")
def sha(b):return hashlib.sha256(b).hexdigest()

def evidence():
    record=json.loads(RELEASE.read_text(encoding="utf-8"))
    log=record.get("original_uploaded_log",{})
    audit=record.get("audit_report",{})
    counts=record.get("counts",{})
    top=record.get("top_observed_lower_bounds",[])
    if not (
      record.get("stage")=="PRE656_V51_GPU_SHADER_PASS_REAL_DEVICE_LOG"
      and record.get("status")=="AUDIT_OK_REAL_DEVICE_LOG_READONLY"
      and record.get("github_run")==42813194428
      and record.get("github_artifact_id")==13763071983
      and log.get("drive_id")=="1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd"
      and log.get("bytes")==576129
      and log.get("sha256")=="649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7"
      and log.get("drive_redownload_byte_equal") is True
      and audit.get("drive_id")=="11rs1L0E1W_xvem4ipVT2675dPH-3clTe"
      and audit.get("bytes")==6637
      and audit.get("sha256")=="998999374d628e6e380bbc25418410acf8a6cbdfded55cb414d9c9669c3765c3"
      and audit.get("zip_crc_pass") is True
      and counts.get("windows")==14
      and counts.get("total_draws")==14265243
      and counts.get("normal")==14258146
      and counts.get("deferred_sky")==7097
      and counts.get("invalid")==0
      and counts.get("reported_top12_draws")==11432370
      and counts.get("all_pair_totals_are_lower_bounds") is True
      and len(top)>=2
      and top[0].get("category")==2 and top[0].get("vs")==62 and top[0].get("ps")==58
      and top[0].get("draws")==2186797
      and record.get("limits",{}).get("no_fps_gain_proven") is True
      and record.get("limits",{}).get("per_shader_gpu_time_not_measured") is True
      and record.get("limits",{}).get("no_apk_built") is True
    ):
        raise ValueError("PRE657 authenticated log/SPIR-V/Drive report evidence mismatch")
    content=HANDOFF.read_bytes()
    for term in (
       b"# PRE657 ",b"42813194428",
       b"1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd",
       b"11rs1L0E1W_xvem4ipVT2675dPH-3clTe",
       b"649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7",
       b"14.265.243",b"2.186.797",b"120 FPS",b"PRE658",
    ):
        if term not in content:
            raise ValueError("PRE657 required real V51 shader log checkpoint evidence missing")
    if not (content.count(MARKER)==1 and 4500<len(content)<12000):
        raise ValueError("PRE657 handoff size/uniqueness invalid")
    return b"\n\n---\n\n"+content

def audit():
    appendix=evidence()
    drive=drive_client()
    meta=get_meta(drive)
    if not (meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
        and meta.get("parents")==[PARENT] and meta.get("mimeType")=="text/markdown"):
        raise ValueError("PRE657 unexpected canonical Drive identity")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):
        raise ValueError("PRE657 Drive metadata size mismatch")
    if MARKER in before:
        if not (before.count(MARKER)==1
          and before.endswith(appendix)
          and len(before)-len(appendix)==EXPECTED_BYTES
          and sha(before[:-len(appendix)])==EXPECTED_SHA):
            raise ValueError("PRE657 conflicting prior append, no write")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
          "canonical_sha256":sha(before),"canonical_bytes":len(before),
          "readback_identical":True}
    if (len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA
        or before.count(b"# PRE655 ")!=1):
        raise ValueError("PRE657 canonical bytes unexpectedly changed; no overwrite")
    target=before+appendix
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},
       fields="id,name,size,parents").execute()
    backup_id=backup["id"]
    if int(backup.get("size",-1))!=EXPECTED_BYTES or get_bytes(drive,backup_id)!=before:
        raise ValueError("PRE657 backup not byte-identical")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("PRE657 canonical context modified before append")
    for attempt in range(3):
        current=get_bytes(drive,FILE_ID)
        if current==target:break
        if current!=before:raise ValueError("PRE657 concurrent update during append")
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
        raise ValueError("PRE657 canonical context readback mismatch")
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
    r.update({"stage":"PRE657_V51_SIGNED_RELEASE_CONTEXT","run_id":args.run_id,
      "utc":datetime.now(timezone.utc).isoformat(),
      "apk_built":False,"signing_material_accessed":False,"user_saves_modified":False})
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    for key,v in (
      ("STATUS",r["status"]),
      ("CANONICAL_SHA256",r.get("canonical_sha256","none")),
      ("BACKUP_CREATED",r.get("backup_created",False)),
      ("READBACK_IDENTICAL",r.get("readback_identical",False)),
      ("ERROR_TYPE",r.get("error_type","none"))):
        print("PRE657_"+key+"="+str(v))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1

if __name__=="__main__":raise SystemExit(main())
