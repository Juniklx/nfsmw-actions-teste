#!/usr/bin/env python3
"""PRE365 read-only PRE99 source canary for PRE364 user0 input logger.
No source modification outside a disposable in-memory string, no APK.
"""
from pathlib import Path
import tarfile,tempfile,json,hashlib
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre364_xinput_user0_passive_staging import (
 SOURCE,PRE99_SHA,MARKER,inject,reverse,sha)
OUT=Path("/tmp/nfsmw-pre365/PRE365_XINPUT_NATIVE_SOURCE_CANARY.json")
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    report={"stage":"PRE365_XINPUT_HOST_SOURCE_CANARY","status":"FAILED",
        "read_only":True,"owner_verified":False,"nitro_button_verified":False,
        "guest_loads_added":0,"guest_stores_rewritten":0,"apk_built":False}
    try:
        with tempfile.TemporaryDirectory(prefix="pre365_") as td:
            tar_path=Path(td)/"pre99.tar.gz"
            download(drive_client(),tar_path)
            digest,_,size=sha_file(tar_path)
            if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
                raise ValueError("PRE99 archive mismatch")
            with tarfile.open(tar_path,"r:gz") as tf:
                member=tf.getmember("workspace/"+SOURCE)
                file=tf.extractfile(member)
                if file is None:raise ValueError("source read unavailable")
                raw=file.read()
            if sha(raw)!=PRE99_SHA:raise ValueError("PRE99 host InputSystem.cpp SHA mismatch")
            original=raw.decode("utf-8")
            staged=inject(original)
            if reverse(staged)!=original:raise ValueError("PRE364 reverse mismatch")
            if staged.count(MARKER)!=1:raise ValueError("marker count mismatch")
            if original.count("*out_state = merged;")!=staged.count("*out_state = merged;"):
                raise ValueError("state output store changed")
            report.update({"status":"AUDIT_OK","pre99_sha256":digest,
              "original_sha256":sha(raw),
              "staged_sha256":hashlib.sha256(staged.encode()).hexdigest(),
              "exact_reversal":True,"original_output_assignment_preserved":True,
              "bounded_log_events":256,
              "limitation":"This tests exact textual stage in authenticated original native source. No ARM64 compile, phone button mapping or player-car owner proof."})
    except Exception as e:report["error_type"]=type(e).__name__
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("PRE365_STATUS",report["status"])
    print("PRE365_ORIGINAL_SOURCE_VERIFIED",report.get("original_sha256")==PRE99_SHA)
    print("PRE365_OWNER_VERIFIED",False)
    return 0 if report["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
