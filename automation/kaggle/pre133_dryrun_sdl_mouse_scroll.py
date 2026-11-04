#!/usr/bin/env python3
"""PRE133: exact PRE99->PRE117->PRE128->PRE131->PRE133 ARM64 dry-run."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download,SOURCE_NAME,SOURCE_SHA256
from pre107_restore_isolated import restore
from pre117_one_scroll_android_dryrun import propose as pre117
from pre128_android_touch_scroll_visual_patch import propose as pre128
from pre131_native_touch_and_modern_ui_patch import proposal
from pre133_mouse_bridge_swipe_patch import propose as correct_android_swipe
from pre112_cpp_syntax_isolated import get_candidate_includes,compile_syntax
from pre113b_android_arm64_syntax import locate_toolchain,NDK_REVISION,ANDROID_API
from pre118_audit_build_tree import EXPECTED_PRE117_SHA

def digest(b):return hashlib.sha256(b).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--run-id",required=True);p.add_argument("--report",required=True)
    a=p.parse_args()
    if not re.fullmatch(r"\d+",a.run_id):raise ValueError("Invalid run id")
    report_path=Path(a.report)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    d={"stage":"PRE133_NATIVE_TOUCH_MODERN_UI_DRYRUN","run_id":a.run_id,
       "status":"NOT_VALIDATED","phase":"INIT","pre99_verified":False,
       "pre117_verified":False,"pre128_verified":False,
       "pre133_sources_patched_in_isolated_runner":False,
       "arm64_settings_syntax_ok":False,"arm64_imgui_drawer_syntax_ok":False,
       "key_accessed":False,"apk_built":False,"drive_modified":False,
       "original_source_modified":False,"phone_touch_verified":False,
       "mobile_theme_verified_on_device":False}
    try:
        d["phase"]="NDK"
        _,compiler=locate_toolchain()
        d["ndk_revision"]=NDK_REVISION
        d["android_api"]=ANDROID_API
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre133_",dir="/tmp") as tmp:
            home=Path(tmp)
            if shutil.disk_usage(home).free<4*1024**3:
                raise RuntimeError("Insufficient ephemeral disk")
            arc=home/"pre99.tar.gz"
            dest=home/"restored";dest.mkdir()
            d["phase"]="DOWNLOAD_PRE99"
            download(drive_client(),arc)
            d["phase"]="VERIFY_PRE99"
            sha,_md5,n=sha_file(arc)
            if sha!=EXPECTED_SHA256 or n!=EXPECTED_BYTES:
                raise ValueError("PRE99 hash mismatch")
            d["pre99_verified"]=True
            d["phase"]="RESTORE_PRE99"
            restore(arc,dest)
            arc.unlink(missing_ok=True)
            src=dest/SOURCE_NAME
            original=src.read_bytes()
            if digest(original)!=SOURCE_SHA256:
                raise ValueError("Settings PRE92 source mismatch")
            d["phase"]="APPLY_PRE117_PRE128_MEMORY"
            a117,_diff=pre117(original.decode("utf-8"))
            if digest(a117.encode())!=EXPECTED_PRE117_SHA:raise ValueError("PRE117 mismatch")
            d["pre117_verified"]=True
            a128=pre128(a117)
            d["pre128_source_sha"]=digest(a128.encode())
            if d["pre128_source_sha"]!="cf3cc930904303ec3b4a081f9987a1ced478697678fcab90b056f07ba0b4957d":
                raise ValueError("PRE128 mismatch")
            d["pre128_verified"]=True
            root=dest/"workspace"
            drawer=root/"nativo/sdk/src/ui/imgui_drawer.cpp"
            drawer_h=root/"nativo/sdk/include/rex/ui/imgui_drawer.h"
            settings_h=root/"nativo/sdk/include/rex/ui/overlay/settings_overlay.h"
            font=root/"android/app/src/main/res/font/michroma.ttf"
            d["phase"]="PRE133_EXACT_PATCH_EPHEMERAL"
            changes=proposal(a128.encode(),drawer.read_bytes(),drawer_h.read_bytes(),
                             settings_h.read_bytes(),font.read_bytes())
            hashes={}
            for relative,data in changes.items():
                target=dest/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(data)
                hashes[relative]=digest(data)
            d["pre131_patch_file_hashes"]=hashes
            d["phase"]="APPLY_PRE133_FOCUSED_SDL_MOUSE_BRIDGE"
            fixed=correct_android_swipe(src.read_bytes())
            src.write_bytes(fixed)
            hashes["workspace/nativo/sdk/src/ui/overlay/settings_overlay.cpp"]=digest(fixed)
            d["pre133_source_sha256"]=digest(fixed)
            d["patch_file_hashes"]=hashes
            d["pre133_sources_patched_in_isolated_runner"]=True
            d["phase"]="ARM64_CXX23_SYNTAX"
            includes=get_candidate_includes(dest)
            x=compile_syntax(str(compiler),src,includes,timeout=240)
            y=compile_syntax(str(compiler),drawer,includes,timeout=240)
            d["arm64_settings_syntax"]=x
            d["arm64_imgui_drawer_syntax"]=y
            d["arm64_settings_syntax_ok"]=x.get("passed") is True
            d["arm64_imgui_drawer_syntax_ok"]=y.get("passed") is True
            if d["arm64_settings_syntax_ok"] and d["arm64_imgui_drawer_syntax_ok"]:
                d["status"]="PRE133_ANDROID_ARM64_SYNTAX_PASSED"
                d["phase"]="COMPLETE"
            else:
                d["status"]="PRE133_ANDROID_ARM64_SYNTAX_FAILED"
    except Exception as e:
        d["error_type"]=type(e).__name__
        # Never echo source, file bytes, credentials or raw exception text.
    finally:
        d["recorded_utc"]=datetime.now(timezone.utc).isoformat()
        report_path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("PRE133:",d["status"],"phase:",d["phase"],
              "settings syntax:",d["arm64_settings_syntax_ok"],
              "drawer syntax:",d["arm64_imgui_drawer_syntax_ok"])
    return 0 if d["status"]=="PRE133_ANDROID_ARM64_SYNTAX_PASSED" else 1

if __name__=="__main__":raise SystemExit(main())
