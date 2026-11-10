#!/usr/bin/env python3
"""PRE652: fail-closed V51 GPU shader/pass draw FREQUENCY diagnostic.
PRE638 V50 staged recipe -> PRE648 *same exact* ARM64 tested insertion.
No shader/SPIR-V/physics/controls/thermal changes; logs aggregate per 10 s.
Always use the original PERMANENT release certificate and increasing versionCode.
NOT proof of FPS improvement or of per-shader GPU time.
"""
from __future__ import annotations
import argparse,hashlib,json,zipfile
from pathlib import Path

import pre626_build_signed_v49_bmw_attr_diag as v49
import pre638_build_signed_v50_c3_two_request_diag as v50
import pre648_v50_shader_pass_counts_arm64_noapk as shader

VERSION=51
APK_NAME="NFSMW_V51_PRE652_GPU_SHADER_PASS_FREQUENCY_DIAGNOSTIC.apk"
SOURCE_SHA="9a76c240852b0cc5c6c80ef608cab3d9302c75368b3237440905caec873dbee2"
HEADER_SHA="9df6eda58b7585e90192baf18c4bd9e12d4d3cb862c5efb1066577b24ec71dfe"
EXPECTED_CERT="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
EXPECTED_PACKAGE="io.github.nfsmwrecomp"
GATE=Path("docs/PRE651_V51_GPU_RELEASE_PREFLIGHT_VERIFIED.json")
EXPECTED_GATE_RUN=None  # actual run pinned in the file below; do not invent it

def digest(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def require_pre651():
    if not GATE.is_file():
        raise ValueError("PRE652 refuses release: verified PRE651 preflight report absent")
    x=json.loads(GATE.read_text(encoding="utf-8"))
    if not (
       x.get("stage")=="PRE651_V51_GPU_RELEASE_PREFLIGHT"
       and x.get("status")=="AUDIT_OK_NO_APK"
       and x.get("preflight_approved") is True
       and x.get("target_version_code")==51
       and x.get("package_id")==EXPECTED_PACKAGE
       and x.get("certificate_sha256")==EXPECTED_CERT
       and x.get("approved_source_sha256")==SOURCE_SHA
       and x.get("approved_counter_header_sha256")==HEADER_SHA
       and x.get("pre648_verified_arm64_sha256")=="214ff9b9e41ab823f4a78f172199eee330f23257eb44e65a22fdb174bd2cbb1e"
       and x.get("pre638_signed_v50_apk_sha256")=="7c49f6c95af5bf20b81c2df0622ce236532edadc70d4619e12021e87b74df4fe"
       and x.get("pre649_host_sanitizers") is True
       and x.get("signing_material_accessed") is False
       and x.get("apk_built") is False
       and x.get("fps_gain_proven") is False
       and isinstance(x.get("github_run_id"),str)
       and x["github_run_id"].isdigit()
    ):
        raise ValueError("PRE652 fails closed: PRE651 authenticated release prerequisites invalid")
    v50.require_pre637()
    if digest(shader.HEADER.read_bytes())!=HEADER_SHA:
        raise ValueError("PRE652 diagnostic header has changed since real PRE648 ARM64 gate")
    return x

def stage_v51(root:Path)->dict:
    staged=shader.stage_source(root)
    source=root/shader.SOURCE
    header=root/shader.DEST_HEADER
    if not (source.is_file() and header.is_file()
        and digest(source.read_bytes())==SOURCE_SHA
        and digest(header.read_bytes())==HEADER_SHA
        and staged.get("pre648_pre638_replay_verified") is True
        and staged.get("pre638_c3_fallback_bypass") is False
        and staged.get("pre638_v49_callbacks_nitro_preserved") is True
        and staged.get("pre638_save_modified") is False):
        raise ValueError("PRE652 source stage diverged from PRE648 real ARM64 tested diagnostics")
    if (not shader.EVIDENCE.get("pre648_source_exact_reverse_verified")
       or shader.EVIDENCE.get("pre648_counter_fixed_size_bytes")!=1638400):
        raise ValueError("PRE652 SHA-pinned diagnostic no longer reversible/bounded")
    return {**staged,
       "pre652_version_code":VERSION,
       "pre652_diagnostic_arm64_source_sha256":SOURCE_SHA,
       "pre652_counter_header_sha256":HEADER_SHA,
       "pre652_only_frequency_diagnostics":True,
       "pre652_no_shader_asset_changes":True,
       "pre652_no_gameplay_or_thermal_changes":True,
       "pre652_saves_modified":False}

def verify_v51(apk:Path,sdk:Path,v30:dict,progress:dict)->dict:
    original=v50.verify_v50(apk,sdk,v30,progress)
    if progress.get("apk_v2_certificate_sha256")!=EXPECTED_CERT:
        raise ValueError("PRE652 refusing different certificate")
    with zipfile.ZipFile(apk,"r") as z:
        if z.testzip() is not None:
            raise ValueError("PRE652 APK ZIP CRC invalid")
        lib=z.read("lib/arm64-v8a/libmain.so")
        for marker in (
          b"PRE648 GPU_SHADER10s",
          b"NFSMW_PRE635_C3_TWOREQUEST_TRACE",
          b"NFSMW_PRE194_C3",
          b"NFSMW_PRE398_GLOBAL_NITRO_FULL",
        ):
            if marker not in lib:
                raise ValueError("PRE652 linked PAL libmain lacks legacy/diagnostic marker")
    if progress.get("pre638_c3_two_request_diagnostic",{}).get("all_4_bmw_callbacks_exported_once") is not True:
        raise ValueError("PRE652 previous four BMW native callbacks not verified")
    progress["pre652_shader_frequency_diagnostic"]={
        "diagnostic_marker_in_signed_pal_libmain":True,
        "pre648_counter_fixed_size_bytes":1638400,
        "pre648_counter_summary_interval_seconds":10,
        "pre635_c3_guard_present":True,
        "pre398_global_nitro_present":True,
        "pre626_four_bmw_callbacks_preserved":True,
        "signed_pal_libmain_sha256":digest(lib),
        "shader_assets_modified":False,
        "saves_modified":False,
        "fps_gain_proven":False,
        "gpu_time_per_shader_measured":False,
        "on_device_log_collected":False,
    }
    return original

def main()->int:
    ap=argparse.ArgumentParser(add_help=False)
    ap.add_argument("--report",required=True)
    args,_=ap.parse_known_args()
    require_pre651()
    # Ensure exactly the previously proven PRE626/PRE638 release chain, rather
    # than installing a new signing, asset or Gradle provider.
    v49.VERSION=VERSION
    v49.APK_NAME=APK_NAME
    v49.stage_v49=stage_v51
    v49.verify_v49=verify_v51
    ret=v49.main()
    report=Path(args.report)
    if not report.exists():
        raise ValueError("PRE652 base release workflow returned no signed-APK report")
    r=json.loads(report.read_text(encoding="utf-8"))
    diag=r.get("pre652_shader_frequency_diagnostic",{})
    ok=(ret==0
      and r.get("signed_apk_verified") is True
      and r.get("permanent_certificate_verified") is True
      and r.get("apk_v2_certificate_sha256")==EXPECTED_CERT
      and diag.get("diagnostic_marker_in_signed_pal_libmain") is True
      and diag.get("pre626_four_bmw_callbacks_preserved") is True
      and r.get("drive_upload_success") is True)
    r.update({
       "pre652_stage":"V51_SHADER_PASS_DRAW_FREQUENCY_ONLY",
       "pre652_target_version_code":VERSION,
       "pre652_expected_package":EXPECTED_PACKAGE,
       "pre652_expected_certificate_sha256":EXPECTED_CERT,
       "pre652_release_approved":bool(ok),
       "pre652_v50_source_bit_identical_to_signed_elf_proven":False,
       "pre652_android_gameplay_tested":False,
       "pre652_runtime_gpu_draw_counts_obtained":False,
       "pre652_gpu_timing_per_shader_obtained":False,
       "pre652_fps_gain_verified":False,
       "pre652_no_thermal_override":True,
       "pre652_no_shader_spirv_optimization":True,
       "status":"PRE652_V51_GPU_DIAGNOSTIC_SIGNED_VERIFIED" if ok else
                "PRE652_V51_GPU_DIAGNOSTIC_NOT_VERIFIED"})
    report.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE652_STATUS="+("VERIFIED" if ok else "NOT_VERIFIED"))
    print("PRE652_VERSION_CODE="+str(VERSION))
    print("PRE652_CERT_POLICY=ORIGINAL_PERMANENT_ONLY")
    print("PRE652_GPU_FREQUENCIES_ON_PHONE_MEASURED=false")
    print("PRE652_FPS_GAIN_PROVEN=false")
    return 0 if ok else 1

if __name__=="__main__":raise SystemExit(main())
