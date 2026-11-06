#!/usr/bin/env python3
"""PRE246 preflight: disposable restored PRE99, no Android build, no signing."""
from __future__ import annotations
import json,sys,tarfile,tempfile
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_SHA256,EXPECTED_BYTES,sha_file
from pre105_read_settings_source import drive_client,download
from pre107_restore_isolated import restore
from pre246_passive_money_probe_patch import apply
OUT=Path("/tmp/nfsmw-pre246-preflight/NFSMW_PRE246_PASSIVE_MONEY_TRACE_PREFLIGHT.json")
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 out={"stage":"PRE246_PASSIVE_MONEY_TRACE_PREFLIGHT","status":"FAILED","phase":"START",
      "apk_built":False,"saves_changed":False,"signer_accessed":False,
      "gameplay_cheats_enabled":False,"drive_files_modified":False}
 try:
  with tempfile.TemporaryDirectory(prefix="nfsmw_pre246_preflight_") as td:
   path=Path(td)/"pre99.tar.gz"
   out["phase"]="GET_PINNED_PRE99"
   download(drive_client(),path)
   sh,_,sz=sha_file(path)
   if sh!=EXPECTED_SHA256 or sz!=EXPECTED_BYTES:raise ValueError("Unexpected PRE99 SHA")
   out["pre99_verified"]=True
   folder=Path(td)/"restore"
   folder.mkdir()
   out["phase"]="RESTORE_EPHEMERAL"
   restore(path,folder)
   out["phase"]="PATCH_DISPOSABLE_RESTORED_TREE"
   out["transformation"]=apply(folder/"workspace")
   out["status"]="AUDIT_OK"
   out["phase"]="COMPLETE"
 except Exception as e:
  out["error_type"]=type(e).__name__
  out["failed_phase"]=out["phase"]
  print("PRE246_PREFLIGHT_ERROR",type(e).__name__,out["phase"])
 OUT.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("PRE246_PREFLIGHT_STATUS",out["status"])
 print("PRE246_TRACE_SITES",out.get("transformation",{}).get("money_traces",0))
 return 0 if out["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
 sys.exit(main())
