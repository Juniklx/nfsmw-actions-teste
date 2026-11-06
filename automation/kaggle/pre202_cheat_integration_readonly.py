#!/usr/bin/env python3
"""PRE202: inspect verified integration points for a future opt-in cheat module.
No code changes, game save reads, APK builds, or signing.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, re, tarfile, tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download

OUT=Path("/tmp/nfsmw-pre202")
TARGETS=[
"workspace/nativo/app/src/nfsmw_app.h",
"workspace/nativo/app_usa/src/nfsmw_app.h",
"workspace/nativo/app/src/nfsmw_recortes_carrera.cpp",
"workspace/nativo/app_usa/src/nfsmw_recortes_carrera.cpp",
"workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp",
"workspace/nativo/sdk/include/rex/hook.h",
"workspace/nativo/app/generated/default/sources.cmake",
"workspace/nativo/app_usa/generated/default/sources.cmake",
"workspace/nativo/app/src/main.cpp",
"workspace/nativo/app_usa/src/main.cpp",
"workspace/android/app/src/main/java/io/github/nfsmwrecomp/TouchControllerView.java"
]
PINS={
"workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp":"5509b4ad8de3f78522e0d5718ab853fbaff79ea4ff9184173a969b63eb3ab034",
"workspace/nativo/app/src/nfsmw_recortes_carrera.cpp":"4902e1489464b04172410f9b3235958c944d628c1a2917a42de6ef0fa6fbb78b",
"workspace/nativo/app_usa/src/nfsmw_recortes_carrera.cpp":"c0c22d9ec794760fe0094b6e6b8671e58d0e91b3e7a76fc96a4e1400d3295591"}
KEYS={
"recompiler_hooks":r"REX_HOOK_RAW|REX_HOOK|REX_EXTERN|REX_FUNC",
"configuration_flags":r"REXCVAR_DEFINE|REXCVAR_GET|cvar|SaveConfig",
"settings_ui":r"ImGui::Checkbox|ImGui::Begin|ImGui::End|OnDraw|SaveConfig|REXCVAR",
"build_sources":r"nfsmw_recortes_carrera|nfsmw_app|generated|sources.cmake|target_sources|add_library",
"controls":r"ICONO_NITRO|ICONO_RELOJ|Speedbreaker|gamepad|ButtonControl"
}
compiled={k:re.compile(v,re.I) for k,v in KEYS.items()}
def analyze(name,b):
    lines=b.decode("utf-8","replace").splitlines()
    result={"path":name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"total_lines":len(lines),
        "hits":{}}
    for category,regex in compiled.items():
        indices=[i for i,s in enumerate(lines,1) if regex.search(s)]
        if indices:
            result["hits"][category]={
                "total":len(indices),
                "lines":indices[:45],
                "excerpts":[{"line":i,"text":lines[i-1].strip()[:190]} for i in indices[:13]]
            }
    if name.endswith("sources.cmake"):
        result["first_35_lines"]=[{"line":i,"text":s[:180]} for i,s in enumerate(lines[:35],1)]
    return result
def audit():
    with tempfile.TemporaryDirectory(prefix="pre202_") as temp:
        archive=Path(temp)/"PRE99.tar.gz"
        download(drive_client(),archive)
        sha,_,size=sha_file(archive)
        if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
            raise ValueError("PRE99 integrity changed")
        found={}
        with tarfile.open(archive,"r:gz") as tf:
            for m in tf:
                name=m.name.lstrip("./")
                if not m.isfile() or name not in TARGETS:continue
                if m.size>4000000:raise ValueError("Unexpected integration file size")
                f=tf.extractfile(m)
                if f is None:raise ValueError("Integration source unreadable")
                data=f.read()
                if len(data)!=m.size:raise ValueError("Truncated integration source")
                found[name]=analyze(name,data)
        if set(found)!=set(TARGETS):
            raise ValueError("Missing expected integration files")
        if any(found[k]["sha256"]!=v for k,v in PINS.items()):
            raise ValueError("Pinned source checksum mismatch")
        return {"stage":"PRE202_CHEAT_INTEGRATION_READONLY",
            "status":"AUDIT_OK","backup_sha256_valid":True,
            "exact_sources_pinned":True,"read_only":True,"apk_built":False,
            "game_source_modified":False,"signing_accessed":False,
            "saves_modified":False,"baseline":"PRE99, not proof of V36 source identity",
            "files":found,"limitations":["No guest nitro meter address verified",
            "No guest speedbreaker reserve address verified",
            "No guest career balance address verified",
            "No feature patch or runtime test performed"]}
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",required=True)
    args=parser.parse_args()
    if not args.run_id.isdecimal():
        raise ValueError("Numeric GitHub run id expected")
    OUT.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE202_CHEAT_INTEGRATION_READONLY","status":"FAILED",
            "read_only":True,"apk_built":False,"game_source_modified":False,"signing_accessed":False}
    try:
        report=audit()
    except Exception as e:
        report["error_type"]=type(e).__name__
    report["run_id"]=args.run_id
    (OUT/"PRE202_INTEGRATION_READONLY.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE202",report["status"],"FILES",len(report.get("files",{})),
          "BACKUP_VERIFIED",report.get("backup_sha256_valid",False))
    if "error_type" in report:print("PRE202_ERROR_TYPE",report["error_type"])
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
