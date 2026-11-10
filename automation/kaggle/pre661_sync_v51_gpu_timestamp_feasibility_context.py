#!/usr/bin/env python3
"""PRE661: audited append-only canonical Drive checkpoint.
PRE660 authentic Vulkan timestamp query infrastructure but not a complete per-shader measurement or FPS gain.
Back up bytes first, abort on any changed concurrent context or provenance.
"""
from __future__ import annotations
import argparse,hashlib,io,json,time
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

EXPECTED_BYTES=1058995
EXPECTED_SHA="fddbcd2475be6fcfa4411330a551e5077cdbae2e8b4464c1e7d21c6fb3be0f23"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE661_VULKAN_TIMESTAMP_SOURCE_20261110.md"
HANDOFF=Path("docs/PRE661_HANDOFF_PRE660_V51_TIMESTAMP_QUERY_SOURCE_VERIFIED_20261110.md")
RELEASE=Path("docs/PRE660_V51_GPU_VULKAN_TIMESTAMP_FEASIBILITY_VERIFIED.json")
MARKER=b"# PRE661 "
OUT=Path("/tmp/nfsmw-pre661/context_result.json")
def sha(b):return hashlib.sha256(b).hexdigest()

def evidence():
    report=json.loads(RELEASE.read_text(encoding="utf-8"))
    source=report.get("source",{})
    findings=report.get("findings",{})
    limits=report.get("limits",{})
    if not (
        report.get("stage")=="PRE660_V51_GPU_SHADER_TIMESTAMP_QUERY_FEASIBILITY"
        and report.get("status")=="AUDIT_OK_STATIC_VULKAN_TIMESTAMP_SUPPORT"
        and report.get("github_run_id")==42817191509
        and report.get("artifact_id")==13766041629
        and report.get("archive_drive_id")=="1qtKOFP08kkL9cQfiDDrj8lSyC-HwjLrj"
        and report.get("archive_sha256")=="7c6d3819f20bfd3a333aebcf694d2dd4d35edf8f418a09e615bfe9b5d7c0b387"
        and report.get("json_sha256")=="868a1eeade88b5255321ee927d2c663efb5ec0d5a8b47601a4d2c18ee8c19e4a"
        and source.get("pal_v50_source_sha256")=="1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
        and source.get("exact_signed_v51_binary_equivalence_not_proven") is True
        and findings.get("gpu_marker_hits")==13
        and findings.get("query_pool_create_hits")==5
        and findings.get("query_pool_reset_hits")==5
        and findings.get("timestamp_query_type_hits")==1
        and findings.get("explicit_vkCmdWriteTimestamp_function_call_matches")==0
        and findings.get("explicit_vkGetQueryPoolResults_function_call_matches")==0
        and findings.get("writer_and_reader_implementation_not_yet_resolved") is True
        and limits.get("per_shader_GPU_time_measured") is False
        and limits.get("apk_built") is False
        and limits.get("fps_gain_proven") is False
    ):
        raise ValueError("PRE661 GPU timestamp evidence/source/run mismatch")
    content=HANDOFF.read_bytes()
    for term in (
        b"# PRE661 ",b"42817191509",b"1qtKOFP08kkL9cQfiDDrj8lSyC-HwjLrj",
        b"7c6d3819f20bfd3a333aebcf694d2dd4d35edf8f418a09e615bfe9b5d7c0b387",
        b"MarcarGpu",b"VK_QUERY_TYPE_TIMESTAMP",b"PRE662",b"2.186.797"):
        if term not in content:raise ValueError("PRE661 signed source/measurement facts missing")
    if not (content.count(MARKER)==1 and 3800<len(content)<10000):
        raise ValueError("PRE661 checkpoint size/uniqueness invalid")
    return b"\n\n---\n\n"+content

def audit():
    appendix=evidence()
    drive=drive_client()
    meta=get_meta(drive)
    if not (meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
        and meta.get("parents")==[PARENT] and meta.get("mimeType")=="text/markdown"):
        raise ValueError("PRE661 unexpected canonical Drive identity")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):
        raise ValueError("PRE661 Drive metadata size mismatch")
    if MARKER in before:
        if not (before.count(MARKER)==1
          and before.endswith(appendix)
          and len(before)-len(appendix)==EXPECTED_BYTES
          and sha(before[:-len(appendix)])==EXPECTED_SHA):
            raise ValueError("PRE661 conflicting prior append, no write")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
          "canonical_sha256":sha(before),"canonical_bytes":len(before),
          "readback_identical":True}
    if (len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA
        or before.count(b"# PRE659 ")!=1):
        raise ValueError("PRE661 canonical bytes unexpectedly changed; no overwrite")
    target=before+appendix
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},
       fields="id,name,size,parents").execute()
    backup_id=backup["id"]
    if int(backup.get("size",-1))!=EXPECTED_BYTES or get_bytes(drive,backup_id)!=before:
        raise ValueError("PRE661 backup not byte-identical")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("PRE661 canonical context modified before append")
    for attempt in range(3):
        current=get_bytes(drive,FILE_ID)
        if current==target:break
        if current!=before:raise ValueError("PRE661 concurrent update during append")
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
        raise ValueError("PRE661 canonical context readback mismatch")
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
    r.update({"stage":"PRE661_V51_GPU_TIMESTAMP_SOURCE_CONTEXT","run_id":args.run_id,
      "utc":datetime.now(timezone.utc).isoformat(),
      "apk_built":False,"signing_material_accessed":False,"user_saves_modified":False})
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    for key,v in (
      ("STATUS",r["status"]),
      ("CANONICAL_SHA256",r.get("canonical_sha256","none")),
      ("BACKUP_CREATED",r.get("backup_created",False)),
      ("READBACK_IDENTICAL",r.get("readback_identical",False)),
      ("ERROR_TYPE",r.get("error_type","none"))):
        print("PRE661_"+key+"="+str(v))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1

if __name__=="__main__":raise SystemExit(main())
