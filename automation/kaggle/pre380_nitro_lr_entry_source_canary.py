#!/usr/bin/env python3
"""PRE380: authenticated PRE99 Nitro LR entry patch proposal canary (no writes).
"""
import json,tarfile,tempfile,sys
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre242_pal_float_dataflow_readonly import TARGETS
from pre379_nitro_lr_entry_staging import verify_raw,propose,reverse
OUT=Path("/tmp/nfsmw-pre380/PRE380_NITRO_LR_ENTRY_PROPOSAL.json")
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE380_NITRO_LR_ENTRY_SOURCE_CANARY","status":"FAILED",
      "read_only":True,"owner_verified":False,"apk_built":False,"cheat_enabled":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre380_") as td:
            archive=Path(td)/"pre99.tar.gz";download(drive_client(),archive)
            sha,_,size=sha_file(archive)
            if sha!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 archive mismatch")
            with tarfile.open(archive,"r:gz") as tf:
                f=tf.extractfile(tf.getmember(TARGETS["nitro"]["file"]))
                if f is None:raise ValueError("Nitro source missing")
                raw=f.read()
            result.update(verify_raw(raw))
            result["status"]="AUDIT_OK"
            result["pre99_sha256"]=sha
            result["no_disk_source_changes"]=True
    except Exception as exc:result["error_type"]=type(exc).__name__
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print("PRE380_STATUS",result["status"])
    print("PRE380_REVERSE_EXACT",result.get("reverse_exact",False))
    print("PRE380_OWNER_VERIFIED",False)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
