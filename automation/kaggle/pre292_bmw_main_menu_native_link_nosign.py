#!/usr/bin/env python3
"""PRE292: integrate feature-ON PRE291 main-menu trace in an isolated ARM64 nfsmw build.
No Android APK, game runtime test, signing, save or persistent source patch.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from datetime import datetime, timezone
from pre264_bmw_hero_menu_patch_dryrun import SOURCE,SOURCE_SHA,FUNCTION,MODEL_CMP,ANCHORS
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre291_bmw_main_menu_passive_trace_dryrun import (
 TRACE_FLAG,TRACE_CALLBACK,MARKER,PROTOTYPE,INJECTION)
from pre284_v37_full_passive_vtable_link_preflight import (
 stage_logger as stage_pre283, PRE284_TARGET, CMAKE_REL)
import pre288_bmw_feature_on_pal_native_preflight as native

OUT=Path("/tmp/nfsmw-pre292/PRE292_BMW_MENU_REAL_PAL_NATIVE_LINK.json")
MODULE_REL="nativo/app/src/nfsmw_bmw_menu_trace_pre292.cpp"
REGISTER="target_sources(nfsmw PRIVATE src/nfsmw_bmw_menu_trace_pre292.cpp)"
MARKER_NATIVE="NFSMW_PRE292_BMW_MENU"
# Maximum 16 total events across all car types, without reading any game memory.
LOGGER=r'''#include <atomic>
#include <cstdint>
#include <rex/logging/macros.h>
static std::atomic<unsigned> g_pre292_events{0u};
extern "C" void NFSMW_PRE291_BMW_MAIN_MENU_TRACE(unsigned model_type,
                                                   unsigned callsite) noexcept {
  unsigned n=g_pre292_events.fetch_add(1u,std::memory_order_relaxed);
  if(n>=16u) return;
  REXLOG_INFO("[NFSMW_PRE292_BMW_MENU] callsite=0x{:08X} type={} event={}",
              callsite,model_type,n+1u);
}
'''
def sha(data):return hashlib.sha256(data).hexdigest()
def check(ok,message):
    if not ok:raise ValueError(message)

def stage_trace(root:Path):
    prior=stage_pre283(root)
    path=root/SOURCE.removeprefix("workspace/")
    old=path.read_bytes()
    check(sha(old)==SOURCE_SHA,"PAL menu generated file SHA mismatch after V37 replay")
    text=old.decode("utf8")
    check(MARKER not in text and TRACE_CALLBACK not in text,"PRE292 already present")
    body=body_for_function(text,FUNCTION)
    check(body.count(MODEL_CMP)==1,"No unique model41 compare")
    check(all(body.count(anchor)==1 for anchor in ANCHORS),"PPC anchors differ")
    check(body.count("__imp__sub_82575370(ctx, base);")==5,"Unexpected menu option calls")
    check(body.find("ctx.lr = 0x825789B0;")<body.find(MODEL_CMP),"type call ordering differs")
    newer=body.replace(MODEL_CMP,MODEL_CMP+INJECTION,1)
    modified=text.replace(body,newer,1)
    anchor=re.search(r"(?m)^DEFINE_REX_FUNC\\(sub_[0-9A-Fa-f]{8}\\)",modified)
    check(anchor is not None,"No generated function declaration")
    modified=modified[:anchor.start()]+PROTOTYPE+modified[anchor.start():]
    check(modified.count(TRACE_CALLBACK+"(")==2,"Callback call/prototype not unique")
    check(modified.replace(PROTOTYPE,"",1).replace(newer,body,1)==text,
          "Trace changes are not exactly reversible")
    for needle in ("REX_LOAD_U32(","REX_STORE_U32(","__imp__sub_82575370(ctx, base);"):
        check(modified.count(needle)==text.count(needle),"Original guest operation changed")
    path.write_text(modified,encoding="utf8")
    check(path.read_text(encoding="utf8")==modified,"Generated source staging mismatch")
    module=root/MODULE_REL
    check(not module.exists(),"Native menu logger exists unexpectedly")
    module.write_text(LOGGER,encoding="utf8")
    cfile=root/CMAKE_REL
    cmake=cfile.read_text(encoding="utf8")
    check(cmake.count(PRE284_TARGET)==1 and REGISTER not in cmake,
          "Expected previous logger CMake line once")
    patched=cmake.replace(PRE284_TARGET,PRE284_TARGET+"\\n    "+REGISTER,1)
    check(patched.replace("\\n    "+REGISTER,"",1)==cmake,"CMake patch not reversible")
    cfile.write_text(patched,encoding="utf8")
    check(cfile.read_text(encoding="utf8").count(REGISTER)==1,"CMake registration not unique")
    return {"pre283_logger_preserved":prior,
       "menu_source_sha256_before":sha(old),
       "menu_source_sha256_after":sha(path.read_bytes()),
       "menu_function":FUNCTION,
       "menu_trace_flag":TRACE_FLAG,"menu_callback":TRACE_CALLBACK,
       "menu_logger_module":MODULE_REL,
       "menu_logger_sha256":sha(module.read_bytes()),
       "menu_registered_once":True,
       "original_guest_ops_unchanged":True,
       "source_patch_reversible":True,
       "logs_maximum_events":16,
       "no_guest_memory_added":True,"no_game_behavior_changes":True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
    a=ap.parse_args()
    if not a.run_id.isdecimal():raise ValueError("Bad run id")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE292_BMW_MENU_FEATURE_ON_REAL_PAL_NATIVE_LINK",
            "status":"FAILED","apk_built":False,"signed":False,
            "save_modified":False,"signing_material_accessed":False}
    orig=(native.stage_logger,native.FEATURE,native.CALLBACK,native.PAL_FILENAME)
    try:
        native.stage_logger=stage_trace
        native.FEATURE=TRACE_FLAG
        native.CALLBACK=TRACE_CALLBACK
        native.PAL_FILENAME=Path(SOURCE).name
        result=native.audit(Path(__file__).resolve().parent)
        result["stage"]="PRE292_BMW_MENU_FEATURE_ON_REAL_PAL_NATIVE_LINK"
        result["pre292_trace_site"]="main-menu candidate sub_82578988"
        result["pre292_runtime_proven"]=False
        result["pre292_apk_created"]=False
        result["pre292_model_gate_modified"]=False
        result["pre292_previous_pre283_feature_flag_off"]=True
        result["pre292_signer_accessed"]=False
    except Exception as exc:
        result["error_type"]=type(exc).__name__
    finally:
        native.stage_logger,native.FEATURE,native.CALLBACK,native.PAL_FILENAME=orig
    result["run_id"]=a.run_id
    result["timestamp"]=datetime.now(timezone.utc).isoformat()
    # No sensitive build stdout; pre288 logs already sanitize output.
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("PRE292_STATUS",result["status"])
    print("PRE292_CONFIG",result.get("cmake_configure",{}).get("ok"))
    print("PRE292_TARGET",result.get("selected_native_target"))
    print("PRE292_LIBMAIN_LINKED",result.get("linked_library",{}).get("arm64_elf"))
    print("PRE292_CALLBACK_DEFINITIONS",result.get("linked_library",{}).get("defined_callback_count"))
    print("PRE292_GUEST_FLAG",result.get("pal_feature_flag",{}).get("passed_to_pal_compiler"))
    print("PRE292_APK_BUILT",False)
    if result["status"]!="AUDIT_OK":
        print("PRE292_BLOCKED_PHASE",result.get("status"))
        print("PRE292_ERROR_TYPE",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
