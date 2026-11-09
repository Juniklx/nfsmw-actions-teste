#!/usr/bin/env python3
"""PRE626: build V49 passive BMW attribute-value diagnostic only AFTER PRE625
real ARM64 link gate has AUDIT_OK. Reuses PRE452 release pipeline, same
permanent certificate/package, existing Nitro and earlier diagnostic callbacks.
No BMW tunability override, no VPAK/save modifications.
"""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,tempfile,zipfile
from pathlib import Path
import pre452_build_signed_v48_bmw_zero_route_diag as pre452
import pre447_bmw_lookup_route_probe_dryrun as p447
import pre448_v47_native_zero_route_preflight as pre448
import pre625_bmw_attr_host_arm64_noapk as pre625

VERSION=49
APK_NAME="NFSMW_V49_PRE626_BMW_ATTRIBUTE_VALUE_DIAGNOSTIC.apk"
ORIGINAL_STAGE=pre452.stage_v48_route
ORIGINAL_VERIFY=pre452.verify_signed_v48
OUT_REPORT_TAG="PRE626_V49_BMW_RESOLVED_ATTRIBUTE_PASSIVE"
def sha(v):return hashlib.sha256(v).hexdigest()

def guard_pre625():
    info=json.loads(Path("docs/PRE625_BMW_HOST_ATTR_ARM64_NATIVE_LINK_RESULT.json").read_text())
    evidence=info.get("evidence",{})
    if (info.get("status")!="AUDIT_OK" or info.get("native_build_ok") is not True
      or info.get("native_arm64_elf") is not True
      or evidence.get("new_callback_exported_exactly_once") is not True
      or evidence.get("previous_3_callbacks_exported_once") is not True
      or evidence.get("new_guest_memory_ops_or_calls")!=0
      or evidence.get("guest_patch_exact_reversal_verified") is not True
      or info.get("APK_built") is not False
      or info.get("signing_material_accessed") is not False):
        raise ValueError("PRE626 requires verified PRE625 ARM64 no-sign link success")
    return info

def stage_v49(root:Path):
    original=ORIGINAL_STAGE(root)
    if (original.get("pre452_passive_route_staged") is not True
      or original.get("pre452_original_pre398_nitro_preserved") is not True):
        raise ValueError("PRE626 expected exact baseline V48 staging")
    lookup=root/pre448.LOOKUP_PATH
    already=lookup.read_text(encoding="utf-8")
    if already.count(pre452.FLAG_DEFINE)!=1:
        raise ValueError("PRE626 previous PRE447 route feature not unique")
    pure=already.replace(pre452.FLAG_DEFINE,"",1)
    if sha(pure.encode())!=pre448.PIN_PRE447_SHA256:
        raise ValueError("PRE626 preexisting PRE447 source not SHA pinned")
    staged=pre625.patch_route_sha_pinned(pure.encode())
    if staged.count(p447.DECL)!=1:
        raise ValueError("PRE626 guest patch declaration not unique")
    enabled=staged.replace(p447.DECL,pre452.FLAG_DEFINE+p447.DECL,1)
    if enabled.replace(pre452.FLAG_DEFINE,"",1)!=staged:
        raise ValueError("PRE626 feature macro not reversible")
    lookup.write_text(enabled,encoding="utf-8")
    if sha(lookup.read_bytes())!=sha(enabled.encode()):
        raise ValueError("PRE626 guest source readback mismatch")
    module=root/pre625.MODULE
    if module.exists():raise ValueError("PRE626 host callback exists")
    module.parent.mkdir(parents=True,exist_ok=True)
    module.write_text(pre625.LOGGER,encoding="utf-8")
    if sha(module.read_bytes())!=sha(pre625.LOGGER.encode()):
        raise ValueError("PRE626 host callback mismatch")
    cmake=root/"nativo/app/CMakeLists.txt"
    before=cmake.read_text(encoding="utf-8")
    if before.count(pre448.REGISTER)!=1 or pre625.REGISTER in before:
        raise ValueError("PRE626 PRE447 registration missing/duplicate")
    newline="\n    "+pre625.REGISTER
    cmake.write_text(before.replace(pre448.REGISTER,pre448.REGISTER+newline,1),encoding="utf-8")
    if cmake.read_text(encoding="utf-8").replace(newline,"",1)!=before:
        raise ValueError("PRE626 CMake not reversible")
    return {**original,
       "pre626_fourth_callback_guest_source_sha256":sha(lookup.read_bytes()),
       "pre626_fourth_callback_host_cpp_sha256":sha(module.read_bytes()),
       "pre626_previous_PRE429_PRE447_nitro_preserved":True,
       "pre626_extra_guest_memory_ops_or_calls":0,
       "pre626_game_assets_untouched":True,
       "pre626_save_untouched":True}

def verify_v49(apk:Path,sdk:Path,v30:dict,progress:dict):
    result=ORIGINAL_VERIFY(apk,sdk,v30,progress)
    with zipfile.ZipFile(apk,"r") as z:
        native=z.read("lib/arm64-v8a/libmain.so")
    required=(b"NFSMW_PRE429_ENTRY",b"NFSMW_PRE429_LEVEL",
      b"NFSMW_PRE447_ROUTE",b"NFSMW_PRE622_ATTR_VALUE",
      b"NFSMW_PRE398_GLOBAL_NITRO_FULL")
    if any(marker not in native for marker in required):
        raise ValueError("PRE626 earlier Nitro or fourth native diagnostic marker missing")
    nm=sdk/"ndk/28.2.13676358/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
    if not nm.is_file():raise ValueError("PRE626 missing pinned NDK nm")
    with tempfile.TemporaryDirectory(prefix="pre626-v49-elf-") as td:
        so=Path(td)/"libmain.so";so.write_bytes(native)
        r=subprocess.run([str(nm),"-D","--defined-only",str(so)],capture_output=True,
                         text=True,timeout=120)
    if r.returncode:raise ValueError("PRE626 nm check failed")
    defs={}
    for symbol in ("NFSMW_PRE429_TRACE_ENTRY","NFSMW_PRE429_TRACE_LEVEL",
                   "NFSMW_PRE447_ROUTE","NFSMW_PRE622_ATTR_VALUE"):
        n=len(re.findall(r"(?m)^[0-9A-Fa-f]+\s+[Tt]\s+"+re.escape(symbol)+r"$",r.stdout))
        if n!=1:raise ValueError("PRE626 callback not uniquely exported "+symbol)
        defs[symbol]=n
    progress["pre626_bmw_attr_diag"]={
      "native_callbacks_exported_once":defs,
      "five_required_Nitro_and_diagnostic_markers":True,
      "libmain_sha256":sha(native),
      "new_BMW_tuning_packages_created":False,
      "game_asset_modified":False,"save_modified":False}
    return result

def main():
    args=argparse.ArgumentParser(add_help=False)
    args.add_argument("--report",required=True)
    options,_=args.parse_known_args()
    guard_pre625()
    pre452.VERSION=VERSION
    pre452.APK_NAME=APK_NAME
    pre452.stage_v48_route=stage_v49
    pre452.verify_signed_v48=verify_v49
    ret=pre452.main()
    reportpath=Path(options.report)
    if reportpath.exists():
        info=json.loads(reportpath.read_text(encoding="utf-8"))
        evidence=info.get("pre626_bmw_attr_diag",{})
        yes=(ret==0 and info.get("signed_apk_verified") is True
             and info.get("permanent_certificate_verified") is True
             and evidence.get("five_required_Nitro_and_diagnostic_markers") is True
             and len(evidence.get("native_callbacks_exported_once",{}))==4)
        info["pre626_stage"]=OUT_REPORT_TAG
        info["pre626_version_code"]=VERSION
        info["pre626_signed_all_four_callbacks_verified"]=yes
        info["pre626_tuning_packages_enabled"]=False
        info["pre626_no_save_edits"]=True
        if yes:
            info["status"]="PRE626_V49_SIGNED_ATTR_DIAGNOSTIC_VERIFIED"
        elif ret==0:
            ret=1
            info["status"]="PRE626_V49_BLOCKED_MISSING_CERT_OR_CALLBACK"
        reportpath.write_text(json.dumps(info,indent=2,ensure_ascii=False)+"\n")
    print("PRE626_STATUS", "VERIFIED" if ret==0 else "FAILED")
    print("PRE626_VERSION_CODE",VERSION)
    print("PRE626_CERT","PERMANENT_OR_FAIL_CLOSED")
    print("PRE626_NO_TUNING_OVERRIDE",True)
    return ret
if __name__=="__main__":
    raise SystemExit(main())
