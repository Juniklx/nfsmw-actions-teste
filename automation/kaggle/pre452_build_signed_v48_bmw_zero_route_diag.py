#!/usr/bin/env python3
"""PRE452 signed V48: V47 source recipe plus one passive return-route logger.

Fail closed on pin mismatches, callbacks or permanent certificate.
Does NOT alter tuning counts, car upgrades, purchase, saves or game physics.
"""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys,tempfile,zipfile
from pathlib import Path
import pre434_build_signed_v47_bmw_passive_diag as v47
import pre447_bmw_lookup_route_probe_dryrun as probe
import pre448_v47_native_zero_route_preflight as native

VERSION=48
APK_NAME="NFSMW_V48_PRE452_BMW_ZERO_ROUTE_DIAGNOSTIC.apk"
REGISTER=native.REGISTER
MODULE=native.MODULE
ORIGINAL_STAGE=v47.stage_menu_with_passive_trace
ORIGINAL_VERIFY=v47.verify_and_require_both_callbacks
FLAG_DEFINE="#define "+probe.FLAG+" 1\n"

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def stage_v48_route(root:Path)->dict:
    # First reproduce the exact PRE434 V47 callback source and Nitro staging.
    prior=ORIGINAL_STAGE(root)
    if prior.get("pre434_two_guest_shards_feature_on") is not True:
        raise ValueError("PRE452 expected original V47 trace stage")
    source=root/native.LOOKUP_PATH
    original=source.read_bytes()
    if sha(original)!=probe.FILES["lookup"][1]:
        raise ValueError("PRE452 original PAL lookup hash not authenticated")
    patched=native.source_route_patch(original,{"preview_sha256":native.PIN_PRE447_SHA256})
    if sha(patched.encode())!=native.PIN_PRE447_SHA256 or patched.count(probe.DECL)!=1:
        raise ValueError("PRE452 source does not match verified PRE447")
    if patched.count(FLAG_DEFINE) or patched.count(probe.FLAG)<4:
        raise ValueError("PRE452 unexpected route feature state")
    enabled=patched.replace(probe.DECL,FLAG_DEFINE+probe.DECL,1)
    if enabled.replace(FLAG_DEFINE,"",1)!=patched:
        raise ValueError("PRE452 cannot reverse feature flag")
    source.write_text(enabled,encoding="utf-8")
    if source.read_bytes()!=enabled.encode():
        raise ValueError("PRE452 guest source readback differs")
    module=root/MODULE
    if module.exists():raise ValueError("PRE452 native callback file already exists")
    module.parent.mkdir(parents=True,exist_ok=True)
    module.write_text(native.LOGGER,encoding="utf-8")
    if module.read_bytes()!=native.LOGGER.encode():
        raise ValueError("PRE452 callback code readback differs")
    cmake=root/"nativo/app/CMakeLists.txt"
    before=cmake.read_text(encoding="utf-8")
    if before.count(native.v46.REGISTER)!=1 or REGISTER in before:
        raise ValueError("PRE452 route CMake registration preconditions not met")
    addition="\n    "+REGISTER
    changed=before.replace(native.v46.REGISTER,native.v46.REGISTER+addition,1)
    if changed.replace(addition,"",1)!=before:
        raise ValueError("PRE452 CMake change not exactly reversible")
    cmake.write_text(changed,encoding="utf-8")
    if cmake.read_text(encoding="utf-8").count(REGISTER)!=1:
        raise ValueError("PRE452 route module registration absent")
    return {**prior,
      "pre452_passive_route_staged":True,
      "pre452_route_guest_original_sha256":sha(original),
      "pre452_route_preview_off_sha256":native.PIN_PRE447_SHA256,
      "pre452_route_guest_enabled_sha256":sha(source.read_bytes()),
      "pre452_route_logger_sha256":sha(module.read_bytes()),
      "pre452_route_feature_enabled":True,
      "pre452_route_added_guest_calls":0,
      "pre452_route_added_guest_memory_ops":0,
      "pre452_original_pre429_preserved":True,
      "pre452_original_pre398_nitro_preserved":True}

def verify_signed_v48(apk:Path,sdk:Path,v30:dict,progress:dict)->dict:
    # PRE401 then PRE434 verification: fixed package, v48, zip, sha,
    # same permanent certificate, unchanged game assets, both PRE429 callbacks.
    result=ORIGINAL_VERIFY(apk,sdk,v30,progress)
    with zipfile.ZipFile(apk,"r") as z:
        lib=z.read("lib/arm64-v8a/libmain.so")
    expected_markers=(b"NFSMW_PRE429_ENTRY",b"NFSMW_PRE429_LEVEL",
        b"NFSMW_PRE447_ROUTE",b"NFSMW_PRE398_GLOBAL_NITRO_FULL")
    for tag in expected_markers:
        if tag not in lib:raise ValueError("PRE452 expected marker missing from signed APK")
    nm=sdk/"ndk/28.2.13676358/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
    if not nm.is_file():raise ValueError("PRE452 pinned llvm-nm unavailable")
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre452-elf-audit-") as d:
        so=Path(d)/"libmain.so";so.write_bytes(lib)
        cp=subprocess.run([str(nm),"-D","--defined-only",str(so)],
            capture_output=True,text=True,timeout=120,check=False)
    if cp.returncode:raise ValueError("PRE452 cannot inspect native ELF symbol table")
    callbacks={}
    for fn in native.EXPECTED_CALLBACKS:
        refs=re.findall(r"(?m)^[0-9A-Fa-f]+\s+[Tt]\s+"+re.escape(fn)+r"$",cp.stdout)
        callbacks[fn]=len(refs)
        if len(refs)!=1:raise ValueError("PRE452 missing/duplicate callback "+fn)
    progress["pre452_bmw_zero_route_diagnostic"]={
        "signed_apk_has_all_three_callbacks_once":True,
        "callback_definition_counts":callbacks,
        "libmain_sha256":sha(lib),
        "all_four_markers_present":True,
        "route_function_called_by_game_tested":False,
        "tuning_car_count_modified":False,
        "save_modified":False}
    return result

def main()->int:
    args=argparse.ArgumentParser(add_help=False)
    args.add_argument("--report",required=True)
    opts,_=args.parse_known_args()
    v47.VERSION=VERSION
    v47.APK_NAME=APK_NAME
    v47.stage_menu_with_passive_trace=stage_v48_route
    v47.verify_and_require_both_callbacks=verify_signed_v48
    code=v47.main()
    path=Path(opts.report)
    if path.is_file():
        report=json.loads(path.read_text(encoding="utf-8"))
        report["pre452_stage"]="V48_BMW_ZERO_ROUTE_SIGNED_DIAGNOSTIC"
        report["pre452_version_code"]=VERSION
        report["pre452_filename"]=APK_NAME
        report["pre452_previous_v47_apk_preserved"]=True
        report["pre452_no_user_save_edits"]=True
        progress=report.get("pre452_bmw_zero_route_diagnostic",{})
        verified=(code==0 and report.get("signed_apk_verified") is True
            and report.get("permanent_certificate_verified") is True
            and progress.get("signed_apk_has_all_three_callbacks_once") is True)
        report["pre452_signed_and_all_callbacks_verified"]=verified
        if verified:
            report["status"]="PRE452_V48_SIGNED_ZERO_ROUTE_DIAGNOSTIC_VERIFIED"
        elif code==0:
            report["status"]="PRE452_BLOCKED_MISSING_RELEASE_EVIDENCE"
            code=1
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE452_STATUS", "VERIFIED" if code==0 else "FAILED_OR_NOT_VERIFIED")
    print("PRE452_VERSION",VERSION)
    print("PRE452_CERT_POLICY","EXISTING_PERMANENT_CERT_ONLY")
    print("PRE452_NO_SAVE_CHANGES",True)
    return code
if __name__=="__main__":raise SystemExit(main())
