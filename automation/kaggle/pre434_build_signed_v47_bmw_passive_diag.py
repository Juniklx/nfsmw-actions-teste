#!/usr/bin/env python3
"""PRE434 V47: signed diagnostic APK extending exact V46 recipe with passive BMW logs.

Fail closed. Preserve V46 Nitro patch and existing certificate.
Never alter user saves, buy parts, patch upgrades, or replace V46 APK.
"""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,sys,tempfile,zipfile
from pathlib import Path
import pre401_build_signed_v46_global_nitro_full as baseline
import pre429_bmw_entry_level_correlation_dryrun as probe
from pre431_v46_source_dual_trace_compat_readonly import install_probe

VERSION=47
APK_NAME="NFSMW_V47_PRE434_BMW_PASSIVE_TUNING_DIAGNOSTIC.apk"
REGISTER="target_sources(nfsmw PRIVATE src/nfsmw_bmw_trace_pre431.cpp)"
ORIGINAL_STAGE=baseline.stage_menu_trace
ORIGINAL_VERIFY=baseline.verify_apk

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def stage_menu_with_passive_trace(root:Path)->dict:
    # PRE401 remains in charge of all original patches and the Nitro cheat.
    original=ORIGINAL_STAGE(root)
    if original.get("menu_registered_once") is not True:
        raise ValueError("PRE434 prior PRE292 menu stage failed")
    prepared=install_probe(root) # SHA-pinned, reversible, two guest shards + one CMake registration
    if prepared.get("cmake_registration_count")!=1:
        raise ValueError("PRE434 passive module not registered exactly once")
    if (root/"nativo/app/CMakeLists.txt").read_text(encoding="utf-8").count(REGISTER)!=1:
        raise ValueError("PRE434 missing native callback CMake target")
    staged={}
    for label in ("entry","list"):
        filename,pin,func=probe.SOURCES[label]
        path=root/"nativo/app/generated/default"/filename
        raw=path.read_bytes()
        if sha(raw)!=prepared["source_reviews"][label]["after_sha256"]:
            raise ValueError("PRE434 guest callback stage SHA mismatch "+label)
        src=raw.decode("utf-8")
        declaration=probe.ENTRY_DECL if label=="entry" else probe.COUNT_DECL
        directive="#define "+probe.FEATURE+" 1\n"
        if src.count(declaration)!=1 or directive in src:
            raise ValueError("PRE434 guest trace flag ambiguity "+label)
        modified=src.replace(declaration,directive+declaration,1)
        if (modified.replace(directive,"",1)!=src or
            modified.count(directive)!=1 or
            modified.count(probe.FEATURE)<2):
            raise ValueError("PRE434 feature cannot reverse "+label)
        path.write_text(modified,encoding="utf-8")
        if path.read_bytes()!=modified.encode("utf-8"):
            raise ValueError("PRE434 guest shard staging readback error "+label)
        staged[label]={"path":filename,"pre_flag_sha256":sha(raw),
                       "feature_on_sha256":sha(path.read_bytes()),"enabled":True,
                       "new_guest_memory_ops":0}
    return {**original,
      "pre434_dual_trace_sources":staged,
      "pre434_dual_trace_native_callback":prepared["native_module"],
      "pre434_two_guest_shards_feature_on":True,
      "pre434_original_nitro_unchanged":True}

def verify_and_require_both_callbacks(apk:Path,sdk:Path,v30:dict,progress:dict)->dict:
    # Enforces PRE401 permanent signer, package, versionCode=47, ZIP, preserved assets.
    result=ORIGINAL_VERIFY(apk,sdk,v30,progress)
    with zipfile.ZipFile(apk,"r") as archive:
        lib=archive.read("lib/arm64-v8a/libmain.so")
    for marker in (b"NFSMW_PRE429_ENTRY",b"NFSMW_PRE429_LEVEL"):
        if marker not in lib:
            raise ValueError("PRE434 missing passive BMW event marker in libmain")
    ndk=sdk/"ndk/28.2.13676358/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
    if not ndk.is_file():
        raise ValueError("PRE434 pinned llvm-nm not installed")
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre434-symbols-") as directory:
        path=Path(directory)/"libmain.so";path.write_bytes(lib)
        inspected=subprocess.run([str(ndk),"-D","--defined-only",str(path)],
                        capture_output=True,text=True,check=False,timeout=120)
    if inspected.returncode!=0:
        raise ValueError("PRE434 ARM64 dynamic symbol inspection failed")
    expected={}
    for function in ("NFSMW_PRE429_TRACE_ENTRY","NFSMW_PRE429_TRACE_LEVEL"):
        matches=re.findall(r"(?m)^[0-9a-fA-F]+\s+[Tt]\s+"+
                    re.escape(function)+r"$",inspected.stdout)
        expected[function]=len(matches)
        if len(matches)!=1:
            raise ValueError("PRE434 passive callback absent or duplicated: "+function)
    progress["pre434_bmw_passive"]={
        "both_event_markers_in_signed_apk":True,
        "callback_dynamic_definitions":expected,
        "libmain_sha256":sha(lib),
        "new_game_logic_or_guest_memory_access_added":False,
        "car_identity_and_upgrades_runtime_verified":False
    }
    return result

def main()->int:
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument("--report",required=True)
    opts,_=parser.parse_known_args()
    baseline.VERSION_CODE=VERSION
    baseline.APK_NAME=APK_NAME
    baseline.stage_menu_trace=stage_menu_with_passive_trace
    baseline.verify_apk=verify_and_require_both_callbacks
    code=baseline.main()
    # PRE401 writes its own sanitary report at the requested location.
    report_path=Path(opts.report)
    if report_path.exists():
        report=json.loads(report_path.read_text(encoding="utf-8"))
        report["pre434_stage"]="PRE434_V47_BMW_PASSIVE_TUNING_DIAGNOSTIC"
        report["pre434_previous_v46_preserved"]=True
        report["pre434_passive_trace_only"]=True
        report["pre434_version_code"]=VERSION
        report["pre434_filename"]=APK_NAME
        report["pre434_signed_verified"]=bool(
           code==0 and report.get("signed_apk_verified") and
           report.get("pre434_bmw_passive",{}).get("both_event_markers_in_signed_apk"))
        if report["pre434_signed_verified"]:
            report["status"]="PRE434_V47_SIGNED_AND_CALLBACKS_VERIFIED"
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PRE434_STATUS", "APK_VERIFIED" if code==0 else "FAILED_OR_INCOMPLETE")
    print("PRE434_VERSION",VERSION)
    print("PRE434_CERT_POLICY","PERMANENT_OR_FAIL_CLOSED")
    print("PRE434_NO_SAVE_EDITS",True)
    return code

if __name__=="__main__":
    raise SystemExit(main())
