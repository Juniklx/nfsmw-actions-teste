#!/usr/bin/env python3
"""PRE567R: independent read-only recovery verification after Drive HTTP 502.
Do not upload/modify canonical, save, APK, game data, or signing material.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from pre480_append_canonical_context_safe import FILE_ID, PARENT, drive_client, get_bytes, get_meta

OUT=Path("/tmp/nfsmw-pre567r/report.json")
BACKUPS=(
 "1r433Ee__39JzU4UDzF6W_zNX7e87ljLH",
 "1kpu3o828D4j2AZqfrH5KbgHb0dh7ZXYx"
)
PRE_SHA="074c43bb4d3781e64b7c37bfb9efa92f5ebf1505d11227434901e0ba4f6e1f36"
PRE_SIZE=859770
MARKER="PRE567_HANDOFF_PRE566_PTBR_BMW_FILE_BACKED_20261109"
HANDOFF=Path("docs/PRE567_HANDOFF_PRE566_PTBR_BMW_FILE_BACKED_20261109.md")
def sha(b): return hashlib.sha256(b).hexdigest()

def audit():
    d=drive_client()
    meta=get_meta(d)
    if meta.get("id")!=FILE_ID or meta.get("name")!="CONTEXTO_NFSMW.md" or meta.get("parents")!=[PARENT]:
        raise ValueError("Canonical metadata changed")
    originals=[]
    for bid in BACKUPS:
        b=get_bytes(d,bid)
        if len(b)!=PRE_SIZE or sha(b)!=PRE_SHA:
            raise ValueError("PRE567 recovery backup bytes differ from PRE565")
        originals.append(b)
    if originals[0]!=originals[1]:
        raise ValueError("PRE567 backups diverge")
    handoff=HANDOFF.read_bytes()
    if handoff.count(MARKER.encode())!=1:
        raise ValueError("PRE567 handoff marker missing/duplicated")
    expected=originals[0]+b"\n\n---\n\n"+handoff
    actual=get_bytes(d,FILE_ID)
    if (len(actual)!=int(meta["size"]) or actual!=expected
        or actual.count(MARKER.encode())!=1
        or not actual.startswith(originals[0])):
        raise ValueError("PRE567 context append differs from exact expected bytes")
    return {
      "stage":"PRE567R_INDEPENDENT_CANONICAL_DRIVE_RECOVERY_READONLY",
      "status":"AUDIT_OK",
      "previous_gitHub_run_42557734548_conclusion":"failure",
      "previous_run_failure_does_not_negate_verified_drive_append":True,
      "backup_copy_count_bytewise_verified":2,
      "original_context_sha256":PRE_SHA,
      "original_context_bytes":PRE_SIZE,
      "canonical_context_bytes":len(actual),
      "canonical_context_sha256":sha(actual),
      "canonical_append_matches_pinned_gitHub_handoff":True,
      "original_context_prefix_preserved":True,
      "canonical_postreadback_verified":True,
      "canonical_or_backup_files_modified_by_PRE567R":False,
      "APK_built":False,
      "game_assets_modified":False,
      "save_modified":False,
      "signing_material_accessed":False,
      "BMW_tuning_enabled":False,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    a=ap.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try: r=audit()
    except Exception as e:
        r={"stage":"PRE567R_INDEPENDENT_CANONICAL_DRIVE_RECOVERY_READONLY",
           "status":"FAILED","error_type":type(e).__name__,"error":str(e)[:280],
           "canonical_or_backup_files_modified_by_PRE567R":False,
           "APK_built":False,"game_assets_modified":False,"save_modified":False}
    r["run_id"]=a.run_id
    r["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n")
    print("PRE567R_STATUS",r["status"],flush=True)
    print("PRE567R_CANONICAL_READBACK",r.get("canonical_postreadback_verified",False),flush=True)
    print("PRE567R_ERROR",r.get("error_type","none"),r.get("error",""),flush=True)
    return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__": raise SystemExit(main())
