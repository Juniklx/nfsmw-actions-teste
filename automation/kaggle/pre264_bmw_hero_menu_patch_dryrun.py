#!/usr/bin/env python3
"""PRE264: fail-closed source-only BMW menu patch recipe, UNAPPLIED.

This reads authenticated PRE99, changes only an IN-MEMORY copy of the PAL
CustomizeMain::BuildOptionsList candidate, then proves localized invariants.
The injection is OFF by default (compile guard). Nothing is built or signed.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, tarfile, tempfile
from pathlib import Path
from datetime import datetime,timezone
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre264/PRE264_BMW_PAL_UI_PATCH_DRYRUN.json")
SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.5.cpp"
SOURCE_SHA="26c58fa8c5b5810f2fa06bcf25d3f3f7ac131bf73692a9991a84269433b8de07"
FUNCTION="sub_82578988"
MODEL_CMP="\tcr6.compare<int32_t>(ctx.r3.s32, 41, xer);\n"
ANCHORS=[
    "// cmpwi cr6,r3,41",
    "// li r10,0",
    "// bne cr6,0x825789c0",
    "// li r10,1",
    "loc_825789C0:",
]
INJECTION=(
    "// NFSMW_PRE264_BMW_MENU_LOCAL: scoped to this menu-building guest function only.\n"
    "// Disabled by default. In future builds enable only after performance-category validation.\n"
    "#if defined(NFSMW_PRE264_BMW_MENU_ENABLE) && NFSMW_PRE264_BMW_MENU_ENABLE\n"
    "\tif (ctx.r3.s32 == 41) {\n"
    "\t\tcr6.eq = false; // Only hide HeroCar status from THIS menu category gate.\n"
    "\t}\n"
    "#endif\n"
)

def sha(raw):return hashlib.sha256(raw).hexdigest()

def patch_memory_only(raw:bytes):
    if sha(raw)!=SOURCE_SHA:raise ValueError("PAL .5 generated source SHA mismatch")
    text=raw.decode("utf-8")
    body=body_for_function(text,FUNCTION)
    if "NFSMW_PRE264_BMW_MENU_LOCAL" in text:
        raise ValueError("PRE264 duplicate patch present")
    for a in ANCHORS:
        if body.count(a)!=1:
            raise ValueError("PRE264 missing or duplicate PPC anchor: "+a)
    if body.count(MODEL_CMP)!=1:raise ValueError("PAL model comparison not unique")
    if body.count("__imp__sub_82575370(ctx, base);")!=5:
        raise ValueError("Expected three main categories across front/back rooms")
    if "ctx.lr = 0x825789B0;\n\t__imp__sub_822CC740(ctx, base);" not in body:
        raise ValueError("GetType call not anchored to exact guest PC")
    if body.count("REX_LOAD_U32(")!=7 or body.count("REX_STORE_U32(")!=3:
        raise ValueError("Unexpected original guest access count")
    patched_body=body.replace(MODEL_CMP, MODEL_CMP+INJECTION, 1)
    patched=text.replace(body,patched_body,1)
    if patched.count("NFSMW_PRE264_BMW_MENU_LOCAL")!=1:
        raise ValueError("Unexpected insertion count")
    if patched_body.replace(MODEL_CMP+INJECTION,MODEL_CMP,1)!=body:
        raise ValueError("Non-local code changes detected")
    if patched.count("REX_LOAD_U32(")!=text.count("REX_LOAD_U32("):
        raise ValueError("Unexpected guest read inserted")
    if patched.count("REX_STORE_U32(")!=text.count("REX_STORE_U32("):
        raise ValueError("Unexpected guest write inserted")
    if patched.count("__imp__sub_82575370(")!=text.count("__imp__sub_82575370("):
        raise ValueError("Existing menu calls changed")
    return {
      "pal_source_sha256":sha(raw),
      "dryrun_candidate_sha256":sha(patched.encode("utf-8")),
      "patch_marker":"NFSMW_PRE264_BMW_MENU_LOCAL",
      "patch_scope":"PAL sub_82578988 only (main customize menu)",
      "source_anchored":True,"original_read_count":body.count("REX_LOAD_U32("),
      "original_store_count":body.count("REX_STORE_U32("),
      "menu_add_option_calls":5,
      "feature_flag":"NFSMW_PRE264_BMW_MENU_ENABLE",
      "feature_flag_default":False,
      "original_source_restored_by_removing_exact_injection":True,
      "in_memory_only":True,
      "game_code_compiled":False,
      "guest_memory_reads_added":0,"guest_memory_writes_added":0,
      "changes_to_us_binary":False,
    }

def host_mock(root:Path):
    cpp=root/"pre264_bmw_menu_test.cpp"
    cpp.write_text(r"""
#include <cassert>
#include <iostream>
static bool hero_for_main_menu(int model, bool enable) {
    bool eq=model==41;
    if (enable && model==41) eq=false;
    return eq;
}
static int category_count(int model, bool enabled, bool backroom) {
    (void)backroom;
    return hero_for_main_menu(model, enabled) ? 1 : 3;
}
int main() {
    unsigned cases=0;
    for (int m=-2;m<78;++m) for (int enable=0;enable<2;++enable)
        for (int room=0;room<2;++room) {
            bool hero=m==41;
            int expected=hero&&!enable ? 1 : 3;
            assert(category_count(m,enable,room)==expected);
            ++cases;
        }
    std::cout << "PRE264_MENU_MOCK_CASES " << cases << "\n";
}
""",encoding="utf-8")
    exe=root/"pre264"
    compile=subprocess.run(["g++","-std=c++17","-Wall","-Wextra","-Werror",
                            "-O1",str(cpp),"-o",str(exe)],capture_output=True,text=True,timeout=35)
    if compile.returncode: return {"ok":False,"compile_returncode":compile.returncode}
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
    return {"ok":run.returncode==0,"output":run.stdout.strip(),"cases":320,
            "game_code_compiled":False}

def audit(tmp:Path):
    arch=tmp/"pre99.tar.gz"
    download(drive_client(),arch)
    digest,_,size=sha_file(arch)
    if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:
        raise ValueError("PRE99 fingerprint mismatch")
    data=None
    with tarfile.open(arch,"r:gz",errorlevel=2) as tar:
        for member in tar:
            if not member.isfile() or member.name.lstrip("./")!=SOURCE:continue
            if member.size>5_000_000:raise ValueError("Unexpected PAL source size")
            f=tar.extractfile(member)
            if f is None:raise ValueError("Cannot read generated source")
            data=f.read()
            break
    if data is None:raise ValueError("Missing pinned PAL file")
    plan=patch_memory_only(data)
    mock=host_mock(tmp)
    return {
       "stage":"PRE264_BMW_PAL_CUSTOMIZE_MENU_DRYRUN",
       "status":"AUDIT_OK" if mock["ok"] else "NEEDS_REVIEW",
       "read_only":True,"verified_pre99_sha256":digest,
       "patch_preview":plan,"host_mock":mock,
       "apk_built":False,"signed":False,"game_source_persisted":False,
       "user_save_modified":False,"no_credentials":True,"usa_untouched":True,
       "not_a_release_patch":True,
       "limitations":[
         "Turning on the flag has NOT been tested in the Android game",
         "The conditional suppresses HeroCar classification only at main-menu build",
         "Not yet proven safe for opening category with zero valid packages",
         "Other hero restrictions in performance Junkman screen remain original",
         "The codegen source is regenerated on every build; a future build must apply this patch after verified restore, never directly overwrite persistent sources",
         "The flag does not distinguish an intro BMW if someone opens main customization menu during prologue; no intro customization path has been demonstrated"
       ]
    }
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    if not args.run_id.isdecimal():raise ValueError("Bad run id")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    output={"status":"FAILED","stage":"PRE264_BMW_PAL_CUSTOMIZE_MENU_DRYRUN",
            "apk_built":False,"game_source_persisted":False}
    try:
        with tempfile.TemporaryDirectory(prefix="nfsmw_pre264_") as temp:
            output=audit(Path(temp))
    except Exception as e:
        output["error_type"]=type(e).__name__
    output["run_id"]=args.run_id
    output["time_utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("PRE264_STATUS",output["status"])
    print("PRE264_GUARDED_PAL_PATCH",output.get("patch_preview",{}).get("feature_flag_default"))
    print("PRE264_HOST",output.get("host_mock"))
    if output["status"]!="AUDIT_OK":print("PRE264_ERROR",output.get("error_type"))
    return 0 if output["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
