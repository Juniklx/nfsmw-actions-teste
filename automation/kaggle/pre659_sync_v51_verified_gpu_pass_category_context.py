#!/usr/bin/env python3
"""PRE659: audited append-only canonical Drive checkpoint.
PRE658 authentic categories and GPU time per pass group, not per individual shader; V51 phone versionCode not directly read.
Back up bytes first, abort on any changed concurrent context or provenance.
"""
from __future__ import annotations
import argparse,hashlib,io,json,time
from datetime import datetime,timezone
from pathlib import Path
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from pre480_append_canonical_context_safe import FILE_ID,PARENT,drive_client,get_meta,get_bytes

EXPECTED_BYTES=1053110
EXPECTED_SHA="74e22c2cc58c8da869bc0c7fc1905ceabe38698548aa821b0cf0ed7dac08af5d"
BACKUP_FOLDER="1qVch202E6KrVUiNCcZbenK4MbqqaC8vQ"
BACKUP_NAME="CONTEXTO_NFSMW_BACKUP_ANTES_PRE659_GPU_PASS_C2_MEASUREMENTS_20261110.md"
HANDOFF=Path("docs/PRE659_HANDOFF_PRE658_V51_GPU_CATEGORY_SOURCE_C2_READONLY_VERIFIED_20261110.md")
RELEASE=Path("docs/PRE658_V51_PASS_CATEGORY_GPU_COST_VERIFIED.json")
MARKER=b"# PRE659 "
OUT=Path("/tmp/nfsmw-pre659/context_result.json")
def sha(b):return hashlib.sha256(b).hexdigest()

def evidence():
    report=json.loads(RELEASE.read_text(encoding="utf-8"))
    source=report.get("base_source",{})
    log=report.get("runtime_device_log",{})
    pack=report.get("report_archive_drive_id")
    means=report.get("c2_gpu_ms_per_swap_mean_unweighted_7_intervals",{})
    cats=report.get("categories",{})
    tops=report.get("lower_bound_top_shader_pairs",[])
    if not (
        report.get("stage")=="PRE658_V51_PAL_RENDER_PASS_CATEGORY_AND_C2_GPU_TIME"
        and report.get("status")=="AUDIT_OK_READONLY_SOURCE_AND_REAL_C2"
        and report.get("github_run_id")==42815591562
        and report.get("github_artifact_id")==13764545634
        and pack=="1TmD89Ye5ntL9O5CMXFFroiEU_Wa0gPDk"
        and report.get("report_archive_sha256")=="fba3ab1dd3368b4aa105fe02d34faa562518474e2d38b87bfed474674021d88d"
        and report.get("report_json_sha256")=="14a54de3855f58413e30302c1aa8cf619ef95c3d9eb511d818d5ff9ca1c8b787"
        and source.get("stage_source_sha256")=="1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
        and source.get("function_sha256")=="ccdaf2ddacbcc21cd421db935f2bc9cca7073b6c052bd2483d8072e8191b5f1e"
        and source.get("numeric_constants_defined_in")=="nativo/app/src/nfsmw_nativo_dibujos.h"
        and log.get("PRE656_run_id")==42813194428
        and log.get("original_log_drive_id")=="1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd"
        and log.get("sha256")=="649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7"
        and log.get("c2_intervals")==7
        and cats.get("p1",{}).get("name")=="kGpuSombras"
        and cats.get("p2",{}).get("name")=="kGpuEscena"
        and cats.get("p3",{}).get("name")=="kGpuReflejo"
        and cats.get("p4",{}).get("name")=="kGpu320"
        and cats.get("p8",{}).get("name")=="kGpuEscenaSinProfundidad"
        and len(tops)>=6
        and (tops[0].get("p"),tops[0].get("vs"),tops[0].get("ps"),tops[0].get("draws"))
            ==(2,62,58,2186797)
        and 2.5<means.get("scene",0)<2.8
        and 1.8<means.get("copies",0)<2.1
        and report.get("boundary",{}).get("fps_gain_unproven") is True
        and report.get("boundary",{}).get("subshader_gpu_duration_unknown") is True
        and report.get("boundary",{}).get("apk_built") is False
        and report.get("boundary",{}).get("shaders_modified") is False
    ):
        raise ValueError("PRE659 authentic PRE658 source/C2 report evidence mismatch")
    content=HANDOFF.read_bytes()
    for term in (b"# PRE659 ",b"42815591562",
        b"1TmD89Ye5ntL9O5CMXFFroiEU_Wa0gPDk",
        b"fba3ab1dd3368b4aa105fe02d34faa562518474e2d38b87bfed474674021d88d",
        b"CategoriaDeDestino",b"kGpuEscena",b"kGpuSombras",
        b"2.186.797",b"PRE660",b"120 FPS"):
        if term not in content:
            raise ValueError("PRE659 category/GPU evidence missing from handoff")
    if not (content.count(MARKER)==1 and 4500<len(content)<12000):
        raise ValueError("PRE659 category handoff size or uniqueness invalid")
    return b"\n\n---\n\n"+content

def audit():
    appendix=evidence()
    drive=drive_client()
    meta=get_meta(drive)
    if not (meta.get("id")==FILE_ID and meta.get("name")=="CONTEXTO_NFSMW.md"
        and meta.get("parents")==[PARENT] and meta.get("mimeType")=="text/markdown"):
        raise ValueError("PRE659 unexpected canonical Drive identity")
    before=get_bytes(drive,FILE_ID)
    if len(before)!=int(meta["size"]):
        raise ValueError("PRE659 Drive metadata size mismatch")
    if MARKER in before:
        if not (before.count(MARKER)==1
          and before.endswith(appendix)
          and len(before)-len(appendix)==EXPECTED_BYTES
          and sha(before[:-len(appendix)])==EXPECTED_SHA):
            raise ValueError("PRE659 conflicting prior append, no write")
        return {"status":"ALREADY_APPLIED_VERIFIED","backup_created":False,
          "canonical_sha256":sha(before),"canonical_bytes":len(before),
          "readback_identical":True}
    if (len(before)!=EXPECTED_BYTES or sha(before)!=EXPECTED_SHA
        or before.count(b"# PRE657 ")!=1):
        raise ValueError("PRE659 canonical bytes unexpectedly changed; no overwrite")
    target=before+appendix
    backup=drive.files().copy(fileId=FILE_ID,supportsAllDrives=True,
       body={"name":BACKUP_NAME,"parents":[BACKUP_FOLDER]},
       fields="id,name,size,parents").execute()
    backup_id=backup["id"]
    if int(backup.get("size",-1))!=EXPECTED_BYTES or get_bytes(drive,backup_id)!=before:
        raise ValueError("PRE659 backup not byte-identical")
    fresh=get_meta(drive)
    if (fresh.get("modifiedTime")!=meta.get("modifiedTime")
        or get_bytes(drive,FILE_ID)!=before):
        raise ValueError("PRE659 canonical context modified before append")
    for attempt in range(3):
        current=get_bytes(drive,FILE_ID)
        if current==target:break
        if current!=before:raise ValueError("PRE659 concurrent update during append")
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
        raise ValueError("PRE659 canonical context readback mismatch")
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
    r.update({"stage":"PRE659_V51_GPU_CATEGORY_C2_CONTEXT","run_id":args.run_id,
      "utc":datetime.now(timezone.utc).isoformat(),
      "apk_built":False,"signing_material_accessed":False,"user_saves_modified":False})
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    for key,v in (
      ("STATUS",r["status"]),
      ("CANONICAL_SHA256",r.get("canonical_sha256","none")),
      ("BACKUP_CREATED",r.get("backup_created",False)),
      ("READBACK_IDENTICAL",r.get("readback_identical",False)),
      ("ERROR_TYPE",r.get("error_type","none"))):
        print("PRE659_"+key+"="+str(v))
    return 0 if r["status"] in ("AUDIT_OK","ALREADY_APPLIED_VERIFIED") else 1

if __name__=="__main__":raise SystemExit(main())
