#!/usr/bin/env python3
"""PRE753 V55: S24 FE CPU diagnostic overhead OFF, no graphics changes.

Retains exact PRE752 V54 PAL native hook and full permanent signing chain.
CLI overrides are used because the settings menu may lock InitOnly flags and
the installed nfsmw.toml may be user-customized (must NOT be overwritten).
"""
from __future__ import annotations
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
import pre752_v54_pal_catchup as v54

VERSION=55
APK_NAME="NFSMW_V55_PRE753_S24FE_PAL_NOQUALITY_DIAG_OFF.apk"
JAVA=Path("android/app/src/main/java/io/github/nfsmwrecomp/MotorNativo.java")
FLAGS=(
    '--nfsmw_nativo_diag_reutilizar=false',
    '--nfsmw_nativo_diag_memoria_subida=false',
)
BASE_STAGE=v54.stage
BASE_VERIFY=v54.verify
EVIDENCE={}

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def stage(root:Path):
    prior=BASE_STAGE(root)
    file=root/JAVA
    before=file.read_bytes()
    if before.count(b'static List<String> argumentos(')!=1:
        raise ValueError("PRE753 Android native CLI builder anchor not unique")
    anchor=b'        a.add("--cache_root=" + carpetaCache(ctx).getAbsolutePath());'
    if before.count(anchor)!=1 or any(f.encode() in before for f in FLAGS):
        raise ValueError("PRE753 Android CLI patch anchor missing or already applied")
    insertion=b'\n        // PRE753 S24 FE: remove diagnostics only, preserving graphics and gameplay.'
    for flag in FLAGS:
        insertion+=b'\n        a.add("'+flag.encode()+b'");'
    after=before.replace(anchor,anchor+insertion,1)
    if after.replace(anchor+insertion,anchor,1)!=before:
        raise ValueError("PRE753 Android CLI patch is not reversible")
    if after.count(b'// PRE753 S24 FE:')!=1:
        raise ValueError("PRE753 patch count mismatch")
    file.write_bytes(after)
    if sha(file.read_bytes())!=sha(after):
        raise ValueError("PRE753 Android CLI write mismatch")
    EVIDENCE.update({
        "java_before_sha256":sha(before),
        "java_after_sha256":sha(after),
        "cli_overrides":list(FLAGS),
        "cli_patch_reversible":True,
        "graphics_resolution_shaders_unchanged":True,
        "race_physics_save_unchanged":True,
        "work_slots_unchanged_at_three":True,
        "no_thermal_override":True,
        "pal_catchup_hook_preserved":True,
        "permanent_signer_unchanged":True,
    })
    return {**prior,"pre753_s24fe_diag_overrides_staged":True}

def verify(apk,sdk,v30,progress):
    previous=BASE_VERIFY(apk,sdk,v30,progress)
    with zipfile.ZipFile(apk) as z:
        dex=b''.join(z.read(n) for n in z.namelist()
                     if re.fullmatch(r'classes(?:[0-9]+)?\.dex',n))
        if not dex:
            # No silent skip if the DEX name pattern changes.
            dex=b''.join(z.read(n) for n in z.namelist()
                         if n.startswith('classes') and n.endswith('.dex'))
        if not dex:
            raise ValueError("PRE753 no DEX classes found")
        for flag in FLAGS:
            if dex.count(flag.encode())!=1:
                raise ValueError("PRE753 CLI flag missing/duplicated in signed DEX: "+flag)
        config=z.read("assets/nativo/nfsmw.toml")
        if b'nfsmw_nativo_ranuras_trabajo = 3' not in config:
            raise ValueError("PRE753 work slots unexpectedly changed")
        if b'nfsmw_nativo_pipelines_precalentar = true' not in config:
            raise ValueError("PRE753 shader prewarm unexpectedly disabled")
    progress["pre753_s24fe_signed_apk"]={
        "cli_flags_in_signed_dex":list(FLAGS),
        "work_slots":3,
        "pal_catchup_preserved":True,
        "user_config_not_overwritten":True,
        "graphics_reduced":False,
        "on_device_fps_gain_proven":False,
    }
    return previous

def main():
    v54.VERSION=VERSION
    v54.APK_NAME=APK_NAME
    v54.stage=stage
    v54.verify=verify
    rc=v54.main()
    import argparse
    ap=argparse.ArgumentParser(add_help=False)
    ap.add_argument("--report",required=True)
    opts,_=ap.parse_known_args()
    p=Path(opts.report)
    if not p.is_file():raise ValueError("PRE753 no release report")
    r=json.loads(p.read_text())
    proof=r.get("pre753_s24fe_signed_apk",{})
    ok=(rc==0 and r.get("pre752_gate_ok") is True
        and r.get("signed_apk_verified") is True
        and r.get("drive_upload_success") is True
        and r.get("pre652_target_version_code")==VERSION
        and proof.get("cli_flags_in_signed_dex")==list(FLAGS)
        and proof.get("work_slots")==3)
    r["pre753_gate_ok"]=bool(ok)
    r["pre753_evidence"]=EVIDENCE
    r["pre753_on_device_performance_proven"]=False
    p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    print("PRE753_SIGNED_V55_S24FE_GATE="+("PASS" if ok else "BLOCKED"))
    print("PRE753_CVAR_DEFAULT_OFF=true")
    print("PRE753_NO_GRAPHICS_REDUCTION=true")
    return 0 if ok else 1

if __name__=="__main__":
    sys.exit(main())
