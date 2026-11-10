#!/usr/bin/env python3
"""PRE663: audited append-only canonical Drive checkpoint.
PRE662 proves Vulkan timestamp function pointer alias and fence-safe pool lifecycle; no isolated shader GPU time or FPS gain.
Back up bytes first, abort on any changed concurrent context or provenance.
"""
from __future__ import annotations
import argparse,hashlib,io,json,time
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

EXPECTED_BYTES=1063561
EXPECTED_SHA="73271d1a0d2ac2a9065fd4afcc11cfad0d66fc1c230b7cd4ac6adfd90bffd2f3"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE663_VULKAN_TIMESTAMP_ALIASES_20261110.md"
HANDOFF=Path("docs/PRE663_HANDOFF_PRE662_V51_VULKAN_TIMESTAMPS_ALIASES_CAPACITY_VERIFIED_20261110.md")
RELEASE=Path("docs/PRE662_V51_VULKAN_TIMESTAMP_ALIAS_LIFECYCLE_VERIFIED.json")
MARKER=b"# PRE663 "
OUT=Path("/tmp/nfsmw-pre663/context_result.json")
def sha(b):return hashlib.sha256(b).hexdigest()

def evidence():
    report=json.loads(RELEASE.read_text(encoding="utf-8"))
    source=report.get("source",{})
    code=report.get("verified_code",{})
    limits=report.get("limitations",{})
    if not (
        report.get("stage")=="PRE662_V51_VULKAN_TIMESTAMP_ALIAS_QUERY_POOL_LIFECYCLE"
        and report.get("status")=="AUDIT_OK_SOURCE_ALIAS_LIFECYCLE_EXTRACTED"
        and report.get("github_run_id")==42826615797
        and report.get("artifact_id")==13768844097
        and report.get("drive_archive_id")=="1jhIoN4Qs8Mp7POF2p_0Wvk_ES9wFCKw4"
        and report.get("archive_bytes")==32433
        and report.get("archive_sha256")=="25222b838a8b4b61801b6878896e407fbc76f6fc649bacba0f314fb2f914be3b"
        and report.get("json_sha256")=="b7d5842410cf16257b33ea3bf7da473a185dfb11f3d73aa51f48eeab469ef910"
        and report.get("archive_zip_crc_pass") is True
        and report.get("archive_remote_redownload_verified") is True
        and source.get("renderer_sha256")=="1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
        and source.get("timestamp_cpp_sha256")=="b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385"
        and source.get("binary_equivalence_with_signed_v51_libmain_not_proven") is True
        and code.get("writer_load",{}).get("line")==1033
        and "vkCmdWriteTimestamp" in code.get("writer_load",{}).get("method","")
        and code.get("reader_load",{}).get("line")==1035
        and "vkGetQueryPoolResults" in code.get("reader_load",{}).get("method","")
        and code.get("marks_per_work_slot")==128
        and code.get("per_slot_max_category_starts")==127
        and code.get("category_skip_repeated_adjacent") is True
        and code.get("query_reset_line")==4835
        and code.get("query_read_line")==4956
        and code.get("query_result_flags")=="VK_QUERY_RESULT_64_BIT"
        and code.get("query_result_wait_flag_used") is False
        and limits.get("only_source_replay_not_signed_elf_identity") is True
        and limits.get("FPS_gain_not_proven") is True
        and limits.get("no_apk_built") is True
        and limits.get("no_shader_edit") is True
    ):
        raise ValueError("PRE663 auth PRE662 Vulkan timestamp query evidence invalid")
    content=HANDOFF.read_bytes()
    for term in (
        b"# PRE663 ",b"42826615797",
        b"1jhIoN4Qs8Mp7POF2p_0Wvk_ES9wFCKw4",
        b"25222b838a8b4b61801b6878896e407fbc76f6fc649bacba0f314fb2f914be3b",
        b"vkGetDeviceProcAddr",b"escribir_marca_",b"leer_consultas_",
        b"kMarcasPorRanura=128",b"PRE664",b"2.186.797"):
        if term not in content:
            raise ValueError("PRE663 renderer alias facts absent from checkpoint")
    if not (content.count(MARKER)==1 and 4500<len(content)<10000):
        raise ValueError("PRE663 checkpoint size/uniqueness mismatch")
    return b"\n\n---\n\n"+content

def audit():
    appendix=evidence()
    drive=drive_client()
    meta=get_meta(drive)
    if not (meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
        and meta.get("parents")==[PARENT] and meta.get("mimeType")=="text/markdown"):
        raise ValueError("PRE663 unexpected canonical Drive identity")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):
        raise ValueError("PRE663 Drive metadata size mismatch")
    if MARKER in before:
        if not (before.count(MARKER)==1
          and before.endswith(appendix)
          and len(before)-len(appendix)==EXPECTED_BYTES
          and sha(before[:-len(appendix)])==EXPECTED_SHA):
            raise ValueError("PRE663 conflicting prior append, no write")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
          "canonical_sha256":sha(before),"canonical_bytes":len(before),
          "readback_identical":True}
    if (len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA
        or before.count(b"# PRE661 ")!=1):
        raise ValueError("PRE663 canonical bytes unexpectedly changed; no overwrite")
    target=before+appendix
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},
       fields="id,name,size,parents").execute()
    backup_id=backup["id"]
    if int(backup.get("size",-1))!=EXPECTED_BYTES or get_bytes(drive,backup_id)!=before:
        raise ValueError("PRE663 backup not byte-identical")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("PRE663 canonical context modified before append")
    for attempt in range(3):
        current=get_bytes(drive,FILE_ID)
        if current==target:break
        if current!=before:raise ValueError("PRE663 concurrent update during append")
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
        raise ValueError("PRE663 canonical context readback mismatch")
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
    r.update({"stage":"PRE663_V51_GPU_TIMESTAMP_LIFECYCLE_CONTEXT","run_id":args.run_id,
      "utc":datetime.now(timezone.utc).isoformat(),
      "apk_built":False,"signing_material_accessed":False,"user_saves_modified":False})
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    for key,v in (
      ("STATUS",r["status"]),
      ("CANONICAL_SHA256",r.get("canonical_sha256","none")),
      ("BACKUP_CREATED",r.get("backup_created",False)),
      ("READBACK_IDENTICAL",r.get("readback_identical",False)),
      ("ERROR_TYPE",r.get("error_type","none"))):
        print("PRE663_"+key+"="+str(v))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1

if __name__=="__main__":raise SystemExit(main())
