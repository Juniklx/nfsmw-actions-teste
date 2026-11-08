#!/usr/bin/env python3
"""PRE384 host-only composite C++ compile of PRE383 callback, no APK."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
from pre383_nitro_lr_slot_callback_staging import baseline,inject,reverse
from pre317_nitro_cycle_staging import HEADER as CYCLE_HEADER
from pre337_nitro_diversity_staging import HEADER as DIVERSITY_HEADER
from pre349_nitro_slot_value_staging import HEADER as VALUES_HEADER
OUT=Path("/tmp/nfsmw-pre384/PRE384_NITRO_LR_SLOT_HOST_COMPILE.json")
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    before=baseline();after=inject(before)
    assert reverse(after)==before
    for op in ("REX_LOAD_U32(","REX_STORE_U32("):
        assert before.count(op)==after.count(op)
    assert "NFSMW_PRE383_NITRO_CALLSITE" in after
    with tempfile.TemporaryDirectory(prefix="pre384_") as td:
        root=Path(td);cpp=root/"nfsmw_cheats_trace_pre247.cpp"
        cpp.write_text(after,encoding="utf8")
        for h in (CYCLE_HEADER,DIVERSITY_HEADER,VALUES_HEADER):
            (root/h.name).write_bytes(h.read_bytes())
        logger=root/"rex/logging/macros.h";logger.parent.mkdir(parents=True)
        logger.write_text("#pragma once\n#define REXLOG_INFO(...) do {} while (0)\n")
        subprocess.run(["g++","-std=c++17","-O2","-Wall","-Wextra","-Werror",
                        "-pthread","-fsyntax-only","-I",str(root),str(cpp)],
                       check=True,capture_output=True,text=True,timeout=40)
    result={"stage":"PRE384_NITRO_LR_SLOT_HOST_COMPILE","status":"AUDIT_OK",
      "stage_reverse_exact":True,"native_host_syntax":"success",
      "extra_guest_reads":0,"guest_stores_rewritten":0,
      "caller_lr_is_owner_proof":False,"owner_verified":False,
      "apk_built":False,"runtime_tested":False,
      "note":"Native host stub compilation is not ARM64/Android game compilation. Does not demonstrate distinct caller LRs between player and AI."}
    OUT.write_text(json.dumps(result,indent=2)+"\n")
    print("PRE384_STATUS",result["status"])
    print("PRE384_GUEST_ACCESS_DELTA 0")
    return 0
if __name__=="__main__":raise SystemExit(main())
