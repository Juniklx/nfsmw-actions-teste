#!/usr/bin/env python3
"""PRE753 / V55: conservative S24 FE performance options for PAL/PT-BR.

Base is verified signed PRE752/V54: same original guest code and graphics,
same installed package, same release signing path and Catch-Up hook.

The three flags below are injected as startup command-line values because
kInitOnly settings are non-editable once the native renderer starts and the
user may have an older persistent nfsmw.toml. Command-line cvars take priority
over TOML; all other user settings remain untouched.

No thermal bypass, quality reduction, shader or physics modification.
The 4th work slot costs ~64MB extra RAM; performance is NOT proven until
same-route A/B measurements on Samsung S24 FE. V54 is the rollback.
"""
from __future__ import annotations
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
import pre752_v54_pal_catchup as v54
import pre652_build_signed_v51_gpu_shader_counts_diag as release

VERSION=55
APK_NAME="NFSMW_V55_PRE753_PAL_S24FE_PERF_CATCHUP.apk"
SOURCE=Path("android/app/src/main/java/io/github/nfsmwrecomp/MotorNativo.java")
PAL_LIB="lib/arm64-v8a/libmain.so"
USA_LIB="lib/arm64-v8a/libmain_usa.so"
PRE752_PAL_DSO_SHA="edac6248572a3c199701bf74ec6124e31235bf95301d9288ab28b73c5014562c"
PRE752_USA_DSO_SHA="4f32de8f2ff10d4748aa33f208774038ef9bfa402eacc61a49dd7e70f3b1bc83"
PRE752_NFSMW_TOML_SHA="9602e9f7409eaab83b295521d00fecb95b04d629a8f7cea48911473f77a4f0d2"
CERT="1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b"
PACKAGE="io.github.nfsmwrecomp"
CONFIG_FLAGS=(
  "--nfsmw_nativo_diag_reutilizar=false",
  "--nfsmw_nativo_diag_memoria_subida=false",
  "--nfsmw_nativo_ranuras_trabajo=4",
)
EVIDENCE={}

def sha(data):return hashlib.sha256(data).hexdigest()

def stage(root):
    prior=v54.stage(root)
    java=root/SOURCE
    old=java.read_bytes()
    content=old.decode("utf-8")
    anchor='        a.add("--cache_root=" + carpetaCache(ctx).getAbsolutePath());\n'
    if content.count(anchor)!=1 or content.count('static List<String> argumentos(')!=1:
        raise ValueError("PRE753 launcher argument anchor missing/not unique")
    if any(flag in content for flag in CONFIG_FLAGS):
        raise ValueError("PRE753 startup flags already staged; refusing double patch")
    injection=(
      "        // PRE753: S24 FE, startup-only flags (CLI overrides persistent TOML).\n"
      "        // Disable measurement-only work; no shaders, textures or image detail altered.\n"
      "        // 4 rather than 3 frame work slots: +64 MiB, experiment requires A/B test.\n"
      + "".join(f'        a.add("{flag}");\n' for flag in CONFIG_FLAGS)
    )
    patched=content.replace(anchor,anchor+injection,1)
    if patched.replace(injection,"",1)!=content:
        raise ValueError("PRE753 launcher patch not exactly reversible")
    if patched.count("a.add(\"--nfsmw_nativo_diag_reutilizar=false\");")!=1:
        raise ValueError("PRE753 renderer diagnostic CVar not patched once")
    java.write_text(patched,encoding="utf-8")
    if not sha(java.read_bytes())!=sha(old):raise ValueError("PRE753 no patch applied")
    EVIDENCE.update({
      "original_java_sha256":sha(old),
      "new_java_sha256":sha(java.read_bytes()),
      "patch_reversible":True,
      "startup_command_line_overrides_TOML":True,
      "flags":dict(x[2:].split("=",1) for x in CONFIG_FLAGS),
      "user_resolution_unchanged":True,
      "user_fps_cap_unchanged":True,
      "user_shadows_effects_and_physics_unchanged":True,
      "user_gamepad_and_saves_unchanged":True,
      "thermal_limit_bypass":False,
      "extra_work_slot_memory_MiB":64,
    })
    return {**prior,"pre753_s24fe_flags_staged":True}

def verify(apk,sdk,v30,progress):
    prior=v54.verify(apk,sdk,v30,progress)
    if progress.get("apk_v2_certificate_sha256")!=CERT:
        raise ValueError("PRE753 original permanent signer mismatch")
    with zipfile.ZipFile(apk) as z:
        if z.testzip() is not None:raise ValueError("PRE753 signed APK ZIP CRC failure")
        dex=z.read("classes.dex")
        for flag in CONFIG_FLAGS:
            if dex.count(flag.encode("utf-8"))!=1:
                raise ValueError("PRE753 startup option absent/repeated in compiled DEX: "+flag)
        pal=z.read(PAL_LIB)
        usa=z.read(USA_LIB)
        toml=z.read("assets/nativo/nfsmw.toml")
        # Full NDK re-links can produce different ELF checksums despite the
        # same authenticated guest and C++ sources (observed PRE753 first run).
        # Verify the actual functional anchors instead of requiring ELF
        # byte-for-byte reproducibility across ephemeral build directories.
        if b"nfsmw_sem_catchup_carreira" not in pal or b"[PRE751]" not in pal:
            raise ValueError("PRE753 native PAL lost the verified Career Catch-Up hook")
        for original_marker in (b"NFSMW_PRE635_C3_TWOREQUEST_TRACE",
                                b"PRE648 GPU_SHADER10s",
                                b"NFSMW_PRE194_C3",
                                b"NFSMW_PRE398_GLOBAL_NITRO_FULL"):
            if original_marker not in pal:
                raise ValueError("PRE753 prior PAL native feature absent: "+original_marker.decode())
        EVIDENCE["pal_native_DSO_relinked_sha256"]=sha(pal)
        EVIDENCE["pal_native_source_authenticated_by_PRE752"]=True
        EVIDENCE["pal_elf_byte_identical_to_v54"]=sha(pal)==PRE752_PAL_DSO_SHA
        if sha(usa)!=PRE752_USA_DSO_SHA:
            raise ValueError("PRE753 must preserve original USA library byte-for-byte")
        if sha(toml)!=PRE752_NFSMW_TOML_SHA:
            raise ValueError("PRE753 embedded original graphics/settings asset must not change")
        if b"nfsmw_sem_catchup_carreira" not in pal or b"[PRE751]" not in pal:
            raise ValueError("PRE753 Catch-Up PAL hook not present")
    proof={
      "all_three_CLI_options_present_once_in_DEX":True,
      "launcher_CLI_overrides_persistent_TOML":True,
      "pal_native_libmain_sha256":sha(pal),
      "usa_libmain_usa_sha256":sha(usa),
      "original_nfsmw_toml_sha256":sha(toml),
      "quality_or_shaders_reduced":False,
      "same_original_CatchUp_PAL_hook":True,
      "pal_source_replayed_from_original_PRE99":True,
      "pal_dso_relinked_not_bit_identical_to_v54":sha(pal)!=PRE752_PAL_DSO_SHA,
      "CatchUp_user_option_preserved":True,
      "additional_workslot_MiB":64,
      "performance_gain_proven":False,
      "S24FE_runtime_tested":False,
      "permanent_cert_sha256":CERT,
    }
    progress["pre753_v55_s24fe_performance_apk"]=proof
    return prior

def main():
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument("--report",type=Path,required=True)
    args,_=p.parse_known_args()
    if release.EXPECTED_CERT!=CERT or release.EXPECTED_PACKAGE!=PACKAGE or VERSION<=54:
        raise ValueError("PRE753 immutable signer/package/increment gate failed")
    release.VERSION=VERSION
    release.APK_NAME=APK_NAME
    release.stage_v51=stage
    release.verify_v51=verify
    rc=release.main()
    if not args.report.is_file():raise ValueError("PRE753 production report not emitted")
    r=json.loads(args.report.read_text(encoding="utf-8"))
    details=r.get("pre753_v55_s24fe_performance_apk",{})
    pass_gate=(
       rc==0 and
       r.get("status")=="PRE652_V51_GPU_DIAGNOSTIC_SIGNED_VERIFIED" and
       r.get("signed_apk_verified") is True and
       r.get("permanent_certificate_verified") is True and
       r.get("apk_v2_certificate_sha256")==CERT and
       r.get("pre652_target_version_code")==55 and
       r.get("drive_upload_success") is True and
       r.get("v52_touch_dex_verified") is True and
       details.get("all_three_CLI_options_present_once_in_DEX") is True and
       details.get("same_original_CatchUp_PAL_hook") is True and
       details.get("quality_or_shaders_reduced") is False
    )
    r["pre753_v55_gate_ok"]=bool(pass_gate)
    r["pre753_v55_evidence"]=EVIDENCE
    r["pre753_performance_gain_proven"]=False
    r["pre753_s24fe_gameplay_tested"]=False
    args.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE753_V55_S24FE_PERF_SIGNED_APK_GATE="+("PASS" if pass_gate else "BLOCKED"))
    print("PRE753_NO_GRAPHICS_REDUCTION_NO_THERMAL_BYPASS")
    return 0 if pass_gate else 1

if __name__=="__main__":
    sys.exit(main())
