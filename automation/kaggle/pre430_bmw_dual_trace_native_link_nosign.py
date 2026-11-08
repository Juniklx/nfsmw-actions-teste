#!/usr/bin/env python3
"""PRE430: native ARM64 link preflight of PRE429 trace, NO APK or signing.

Replays V37 source in a disposable directory (not V46).
Uses PRE292 registered CMake stage, adds dual PRE429 callback markers.
Fails closed on source hashes, CMake anchors or native compiler mismatch.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
import pre288_bmw_feature_on_pal_native_preflight as native
import pre429_bmw_entry_level_correlation_dryrun as p
from pre292_bmw_main_menu_native_link_nosign import stage_trace as stage_pre292,REGISTER as PRE292_REGISTER
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre430/report.json")
MODULE="nativo/app/src/nfsmw_bmw_trace_pre430.cpp"
CMAKE="nativo/app/CMakeLists.txt"
REGISTER="target_sources(nfsmw PRIVATE src/nfsmw_bmw_trace_pre430.cpp)"
CALLBACK="NFSMW_PRE429_TRACE_LEVEL"
STAGE="START"
def sha(b:bytes):return hashlib.sha256(b).hexdigest()
def stage(root:Path):
 global STAGE
 STAGE="REPLAY_PRE292_V37_MODULES"
 prior=stage_pre292(root)
 STAGE="PRE429_TWO_GUEST_SHARDS"
 changed_sources={}
 for label in ("entry","list"):
  filename,expected,fn=p.SOURCES[label]
  path=root/"nativo/app/generated/default"/filename
  original=path.read_bytes()
  if sha(original)!=expected:raise ValueError("PRE429 pinned guest source incompatible with prior stage "+label)
  preview=p.change(original,label)
  source=original.decode("utf-8")
  body=body_for_function(source,fn)
  anchor,inject,decl=(p.ENTRY_ANCHOR,p.ENTRY_CODE,p.ENTRY_DECL) if label=="entry" else (p.COUNT_ANCHOR,p.COUNT_CODE,p.COUNT_DECL)
  if body.count(anchor)!=1:raise ValueError("PRE429 anchor missing "+label)
  newbody=body.replace(anchor,anchor+inject,1)
  newer=source.replace(body,newbody,1)
  m=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)",newer)
  if m is None:raise ValueError("Cannot insert PRE429 declaration")
  newer=newer[:m.start()]+decl+newer[m.start():]
  if sha(newer.encode())!=preview["preview_sha256"]:raise ValueError("Mismatch to PRE429 authenticated dry-run "+label)
  path.write_text(newer,encoding="utf-8")
  if sha(path.read_bytes())!=preview["preview_sha256"]:raise ValueError("Bad write readback "+label)
  changed_sources[label]={"original_sha256":expected,"staged_sha256":preview["preview_sha256"],"reversible":True}
 STAGE="PRE430_NATIVE_MODULE"
 module=root/MODULE
 if module.exists():raise ValueError("Logger already exists")
 module.parent.mkdir(parents=True,exist_ok=True)
 module.write_text(p.HELPER,encoding="utf-8")
 if sha(module.read_bytes())!=sha(p.HELPER.encode()):raise ValueError("Logger contents changed")
 STAGE="PRE430_CMAKE_REGISTRATION"
 cmake=root/CMAKE
 old=cmake.read_text(encoding="utf-8")
 if old.count(PRE292_REGISTER)!=1 or REGISTER in old:raise ValueError("Missing or duplicate PRE292 CMake anchor")
 newline="\n    "+REGISTER
 newer=old.replace(PRE292_REGISTER,PRE292_REGISTER+newline,1)
 if newer.replace(newline,"",1)!=old:raise ValueError("CMake not reversible")
 cmake.write_text(newer,encoding="utf-8")
 if cmake.read_text(encoding="utf-8").count(REGISTER)!=1:raise ValueError("PRE430 CMake registration incomplete")
 STAGE="STAGE_COMPLETE"
 return {"prior_pre292_registered":prior.get("menu_registered_once",False),
  "source_previews":changed_sources,"native_module":MODULE,
  "native_module_sha256":sha(module.read_bytes()),"cmake_registration":REGISTER,
  "cmake_registration_once":True,"flag_on_for_disposable_native_build_only":True,
  "apk_or_save_modified":False,"preserves_v46_runtime_claim":False}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
 a=ap.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 original=(native.stage_logger,native.FEATURE,native.CALLBACK,native.PAL_FILENAME)
 result={"stage":"PRE430_BMW_DUAL_MARKER_NATIVE_LINK_NO_APK","status":"FAILED",
         "apk_built":False,"signed":False,"save_modified":False,
         "signing_material_accessed":False,"base_is_full_v46":False}
 try:
  native.stage_logger=stage
  native.FEATURE=p.FEATURE
  native.CALLBACK=CALLBACK
  native.PAL_FILENAME="nfsmw_recomp.57.cpp"
  report=native.audit(Path(__file__).resolve().parents[2])
  result.update(report)
  result["stage"]="PRE430_BMW_DUAL_MARKER_NATIVE_LINK_NO_APK"
  result["base_is_full_v46"]=False
  result["pre430_second_guest_shard_compile_flag_checked"]=False
  result["pre430_guest_source_patches_are_v37_replay_based"]=True
  result["apk_built"]=False;result["signed"]=False;result["signing_material_accessed"]=False
 except Exception as e:
  result["error_type"]=type(e).__name__
  result["safe_phase"]=STAGE
  result["status"]="FAILED"
 finally:
  native.stage_logger,native.FEATURE,native.CALLBACK,native.PAL_FILENAME=original
 result["run_id"]=a.run_id;result["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
 print("PRE430_STATUS",result["status"])
 print("PRE430_PHASE",STAGE)
 print("PRE430_ERROR_TYPE",result.get("error_type","none"))
 print("PRE430_CMAKE_CONFIG",result.get("cmake_configure",{}).get("ok"))
 print("PRE430_NATIVE_BUILD",result.get("production_native_build",{}).get("ok"))
 print("PRE430_ARM64_ELF",result.get("linked_library",{}).get("arm64_elf"))
 print("PRE430_LINKED_CALLBACK_DEFINITIONS",result.get("linked_library",{}).get("defined_callback_count"))
 print("PRE430_V46_BASE",False)
 return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
