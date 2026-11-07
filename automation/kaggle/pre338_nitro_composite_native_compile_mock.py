#!/usr/bin/env python3
"""PRE338: native-only compile test of composed PRE317+PRE337 passive logger.

No PRE99 download, no game binaries or guest memory, no APK/signing/save.
An isolated temporary stub supplies only rex/logging/macros.h.
"""
from pathlib import Path
import os, subprocess, tempfile, json
from pre247_pal_meter_passive_probe_patch import CPP_TEXT
from pre317_nitro_cycle_staging import inject as pre317_inject
from pre337_nitro_diversity_staging import inject as pre337_inject
from pre317_nitro_cycle_staging import HEADER as PRE316_HEADER
from pre337_nitro_diversity_staging import HEADER as PRE336_HEADER

def main():
    before=pre317_inject(CPP_TEXT)
    composed=pre337_inject(before)
    assert composed.count("NFSMW_PRE247_CHEATS_DIAG")==1
    assert composed.count("NFSMW_PRE316_NITRO_CYCLE")==1
    assert composed.count("NFSMW_PRE336_NITRO_DIVERSITY")==1
    assert composed.count("REX_STORE_U32(")==0
    assert composed.count("REX_LOAD_U32(")==0
    with tempfile.TemporaryDirectory(prefix="nfsmw_pre338_") as td:
        root=Path(td)
        cpp=root/"nfsmw_cheats_trace_pre247.cpp"
        cpp.write_text(composed,encoding="utf-8")
        (root/PRE316_HEADER.name).write_bytes(PRE316_HEADER.read_bytes())
        (root/PRE336_HEADER.name).write_bytes(PRE336_HEADER.read_bytes())
        macros=root/"rex/logging/macros.h"
        macros.parent.mkdir(parents=True,exist_ok=True)
        macros.write_text("#pragma once\n#define REXLOG_INFO(...) do {} while (0)\n",encoding="utf-8")
        cmd=["g++","-std=c++17","-O2","-Wall","-Wextra","-Werror",
             "-pthread","-fsyntax-only","-I",str(root),str(cpp)]
        subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=40)
    report={"stage":"PRE338_COMPOSITE_PASSIVE_NATIVE_COMPILE",
        "status":"AUDIT_OK","composition_exact":True,
        "markers_preserved":True,"extra_guest_loads":0,"guest_stores_rewritten":0,
        "owner_verified":False,"apk_built":False,"signer_accessed":False,
        "scope":"Host g++ syntax-only, stub logger; not ARM64 linker or Android runtime"}
    dest=Path("/tmp/nfsmw-pre338/PRE338_REPORT.json")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("PRE338_STATUS AUDIT_OK")
    print("PRE338_COMPOSITE_NATIVE_SYNTAX success")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
