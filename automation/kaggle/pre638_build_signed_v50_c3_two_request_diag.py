#!/usr/bin/env python3
"""PRE638: build signed V50 passive C3 two-request diagnostic using exact V49
recipe and permanently pinned release signer. Requires PRE637 real ARM64 gate.
No C3 fallback bypass, graphics/physics/control/Nitro/save changes.
Do NOT treat the diagnostic as proof of an FPS gain or as a C3 fix.
"""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess,tempfile,zipfile
from pathlib import Path

import pre626_build_signed_v49_bmw_attr_diag as v49
import pre635_c3_duplicate_request_trace_dryrun as p635
from pre194_c3_guard_pal_diagnostic_patch import PATCHED_SHA as PRE194_SHA

VERSION=50
APK_NAME="NFSMW_V50_PRE638_C3_TWO_REQUEST_DIAGNOSTIC.apk"
EXPECTED_CERT="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
PIN_PRE637="b8748dbf74f8fddb1bf3151801b50fe24e159c0f4d9fa6f84f0f675791d0cc9e"
PIN_PRE635="1f890953380502abd0cfc7d140a102bbd7470aff6ca2d37b039a16d9c6ffeb92"
PIN_PRE99="af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39"
PIN_RUN="42745476208"
GATE_PATH=Path("docs/PRE637_V49_C3_ARM64_NATIVE_RESULT.json")
PAL_C3=Path("nativo/app/src/nfsmw_nativo_dibujos.cpp")
ORIGINAL_STAGE=v49.stage_v49
ORIGINAL_VERIFY=v49.verify_v49

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def require_pre637():
    if not GATE_PATH.is_file():
        raise ValueError("PRE638 PRE637 pinned ARM64 evidence unavailable")
    record=json.loads(GATE_PATH.read_text(encoding="utf-8"))
    evidence=record.get("evidence",{})
    expected_callbacks={
        "NFSMW_PRE429_TRACE_ENTRY",
        "NFSMW_PRE429_TRACE_LEVEL",
        "NFSMW_PRE447_ROUTE",
        "NFSMW_PRE622_ATTR_VALUE",
    }
    counts=evidence.get("callback_counts")
    if not (
        record.get("stage")=="PRE637_V49_PRE635_ARM64_NATIVE_NO_APK"
        and record.get("run_id")==PIN_RUN
        and record.get("status")=="AUDIT_OK"
        and record.get("phase")=="ARM64_NATIVE_LINK_AND_SYMBOLS_PASS"
        and record.get("PRE99_sha256")==PIN_PRE99
        and record.get("native_cmake_ok") is True
        and record.get("native_build_ok") is True
        and record.get("native_arm64_elf") is True
        and record.get("real_linked_library_sha256")==PIN_PRE637
        and evidence.get("arm64_elf_sha256")==PIN_PRE637
        and evidence.get("pre194_original_sha256")==PRE194_SHA
        and evidence.get("pre635_candidate_source_sha256")==PIN_PRE635
        and evidence.get("pre635_exact_reversal_verified") is True
        and evidence.get("pre635_marker_linked_in_actual_elf") is True
        and evidence.get("pre194_fallback_marker_present") is True
        and evidence.get("pre398_nitro_marker_present") is True
        and evidence.get("pre398_nitro_preserved") is True
        and evidence.get("all_4_bmw_callbacks_exported_once") is True
        and isinstance(counts,dict) and set(counts)==expected_callbacks
        and all(x==1 for x in counts.values())
        and record.get("APK_built") is False
        and record.get("signed") is False
        and record.get("signing_material_accessed") is False
        and record.get("save_modified") is False
        and record.get("game_assets_modified") is False
    ):
        raise ValueError("PRE638 refuses stale/incomplete PRE637 release evidence")
    return record

def stage_v50(root:Path)->dict:
    base=ORIGINAL_STAGE(root)
    if not (
        base.get("pre626_previous_PRE429_PRE447_nitro_preserved") is True
        and base.get("pre626_game_assets_untouched") is True
        and base.get("pre626_save_untouched") is True
    ):
        raise ValueError("PRE638 base V49 stage is not verified")
    source=root/PAL_C3
    original=source.read_bytes()
    if sha(original)!=PRE194_SHA:
        raise ValueError("PRE638 V49 C3 source is not authenticated PRE194 SHA")
    candidate=p635.patch_p194(original)
    if sha(candidate)!=PIN_PRE635:
        raise ValueError("PRE638 PRE635 candidate source SHA mismatch")
    if candidate.replace(p635.NEW.encode(),p635.OLD.encode(),1)!=original:
        raise ValueError("PRE638 PRE635 diagnostic is not exactly reversible")
    # PRE635 keeps original ApagarEnlaces/return false, and is bounded by C3 guard.
    if candidate.count(b'ApagarEnlaces(fmt::format(')!=original.count(b'ApagarEnlaces(fmt::format('):
        raise ValueError("PRE638 C3 fallback count changed")
    if candidate.count(b'return false;')!=original.count(b'return false;'):
        raise ValueError("PRE638 C3 fallback return count changed")
    source.write_bytes(candidate)
    if sha(source.read_bytes())!=PIN_PRE635:
        raise ValueError("PRE638 C3 source writeback failed")
    return {
        **base,
        "pre638_v49_source_recipe_verified":True,
        "pre638_original_pre194_c3_sha256":sha(original),
        "pre638_c3_two_request_patch_sha256":sha(candidate),
        "pre638_c3_exact_reversal":True,
        "pre638_only_new_modification":"PAL_C3_GUARD_METADATA_LOG_ONLY",
        "pre638_c3_fallback_bypass":False,
        "pre638_v49_callbacks_nitro_preserved":True,
        "pre638_game_assets_modified":False,
        "pre638_save_modified":False,
    }

def verify_v50(apk:Path,sdk:Path,v30:dict,progress:dict)->dict:
    previous=ORIGINAL_VERIFY(apk,sdk,v30,progress)
    with zipfile.ZipFile(apk,"r") as archive:
        if archive.testzip() is not None:
            raise ValueError("PRE638 signed APK ZIP CRC invalid")
        lib=archive.read("lib/arm64-v8a/libmain.so")
        required=[
            b"NFSMW_PRE635_C3_TWOREQUEST_TRACE",
            b"NFSMW_PRE194_C3",
            b"NFSMW_PRE398_GLOBAL_NITRO_FULL",
            b"NFSMW_PRE429_ENTRY",
            b"NFSMW_PRE429_LEVEL",
            b"NFSMW_PRE447_ROUTE",
            b"NFSMW_PRE622_ATTR_VALUE",
        ]
        if any(m not in lib for m in required):
            raise ValueError("PRE638 signed PAL libmain missing C3/Nitro/BMW markers")
        if b'copia_duplicada' not in lib or b'referencia_distinta' not in lib:
            raise ValueError("PRE638 C3 predicate/guard markers missing")
        # PRE401 VERIFY_APK already checks unchanged PAL/USA shader assets,
        # libmain_usa.so, package, release certificate and versionCode.
    nm=sdk/"ndk/28.2.13676358/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
    if not nm.is_file():
        raise ValueError("PRE638 pinned llvm-nm not found")
    with tempfile.TemporaryDirectory(prefix="nfsmw-pre638-elf-audit-") as work:
        tmp=Path(work)/"libmain.so"
        tmp.write_bytes(lib)
        inspected=subprocess.run([str(nm),"-D","--defined-only",str(tmp)],
            capture_output=True,text=True,timeout=120,check=False)
    if inspected.returncode:
        raise ValueError("PRE638 cannot verify prior native callbacks")
    counts={}
    for name in ("NFSMW_PRE429_TRACE_ENTRY","NFSMW_PRE429_TRACE_LEVEL",
                 "NFSMW_PRE447_ROUTE","NFSMW_PRE622_ATTR_VALUE"):
        count=len(re.findall(r"(?m)^[0-9a-fA-F]+\s+[Tt]\s+"+
                             re.escape(name)+r"$",inspected.stdout))
        if count!=1:
            raise ValueError("PRE638 prior BMW callback missing/duplicated: "+name)
        counts[name]=count
    # Previous layer PRE401 uses CERT_SHA constant and aapt; do not trust a
    # plausible-but-false 'verified' marker alone.
    if progress.get("apk_v2_certificate_sha256")!=EXPECTED_CERT:
        raise ValueError("PRE638 signing certificate differs from permanent identity")
    progress["pre638_c3_two_request_diagnostic"]={
       "v50_c3_marker_in_signed_libmain":True,
       "pre194_c3_guard_present":True,
       "pre398_nitro_preserved":True,
       "all_4_bmw_callbacks_exported_once":True,
       "callback_counts":counts,
       "signed_pal_libmain_sha256":sha(lib),
       "c3_fallback_bypass":False,
       "new_game_assets_created":False,
       "user_save_modified":False,
       "no_fps_improvement_claimed":True,
       "guest_runtime_executed":False,
    }
    return previous

def main()->int:
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument("--report",required=True)
    options,_=parser.parse_known_args()
    require_pre637()
    # Entrypoint remains the identical PRE401->PRE434->PRE452->PRE626
    # permanently-signed Android release path, with V50 identity.
    v49.VERSION=VERSION
    v49.APK_NAME=APK_NAME
    v49.stage_v49=stage_v50
    v49.verify_v49=verify_v50
    result=v49.main()
    report_path=Path(options.report)
    if report_path.exists():
        report=json.loads(report_path.read_text(encoding="utf-8"))
        evidence=report.get("pre638_c3_two_request_diagnostic",{})
        valid=(result==0 and report.get("signed_apk_verified") is True
           and report.get("permanent_certificate_verified") is True
           and report.get("apk_v2_certificate_sha256")==EXPECTED_CERT
           and evidence.get("v50_c3_marker_in_signed_libmain") is True
           and evidence.get("pre194_c3_guard_present") is True
           and evidence.get("pre398_nitro_preserved") is True
           and evidence.get("all_4_bmw_callbacks_exported_once") is True)
        report.update({
            "pre638_stage":"V50_C3_TWO_REQUEST_DIAGNOSTIC",
            "pre638_source_gate_run_id":PIN_RUN,
            "pre638_previous_V49_preserved":True,
            "pre638_expected_version_code":VERSION,
            "pre638_expected_certificate_sha256":EXPECTED_CERT,
            "pre638_release_approved":valid,
            "pre638_guest_runtime_tested":False,
            "pre638_c3_bug_fixed":False,
            "pre638_fps_gain_verified":False,
            "pre638_no_save_modifications":True,
            "pre638_no_thermal_bypass":True,
            "status":"PRE638_V50_SIGNED_DIAGNOSTIC_VERIFIED" if valid
                     else "PRE638_V50_NOT_VERIFIED",
        })
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
        if not valid and result==0:
            result=1
    print("PRE638_STATUS="+("VERIFIED" if result==0 else "BLOCKED_OR_FAILED"))
    print("PRE638_VERSION_CODE=50")
    print("PRE638_CERT_POLICY=ORIGINAL_PERMANENT_CERT_ONLY")
    print("PRE638_C3_DIAGNOSTIC_NOT_A_FIX=true")
    return result
if __name__=="__main__":
    raise SystemExit(main())
