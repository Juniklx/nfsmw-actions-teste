#!/usr/bin/env python3
"""PRE432: V46 source-equivalent ARM64 native-link proof for BOTH PRE429 callbacks.

Build original PAL libmain.so in ephemeral NDK workspace. No Gradle, APK,
signing credentials, game saves or production source writes.
"""
from __future__ import annotations
import argparse,json,re,shlex,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
import pre288_bmw_feature_on_pal_native_preflight as native
import pre431_v46_source_dual_trace_compat_readonly as v46
from pre285_bmw_arm64_ndk_logger_preflight import find_ndk

OUT=Path("/tmp/nfsmw-pre432/report.json")
EXPECTED={
 "nfsmw_recomp.15.cpp":"NFSMW_PRE429_TRACE_ENTRY",
 "nfsmw_recomp.57.cpp":"NFSMW_PRE429_TRACE_LEVEL",
}
FLAG="-D"+v46.FEATURE+"=1"
EXTRA={}
PHASE="INITIAL"

def inspect_linked_outputs(build:Path,upstream):
 global PHASE,EXTRA
 PHASE="PRE432_VERIFY_BOTH_COMPILE_COMMANDS"
 outputs=upstream(build)
 if len(outputs)!=1:raise ValueError("Expected one original PAL libmain.so")
 commands_path=build/"compile_commands.json"
 if not commands_path.is_file():raise ValueError("compile_commands.json missing")
 commands=json.loads(commands_path.read_text(encoding="utf-8"))
 compilation={}
 for file,symbol in EXPECTED.items():
  matched=[c for c in commands if Path(c.get("file","")).name==file]
  if len(matched)!=1:raise ValueError("PRE432 "+file+" compile command not unique")
  c=matched[0]
  args=c.get("arguments") or shlex.split(c.get("command",""))
  enabled=FLAG in args
  compilation[file]={"compile_command_count":1,"on_flag_passed":enabled,"symbol_expected":symbol}
  if not enabled:raise ValueError("PRE432 missing feature flag "+file)
 PHASE="PRE432_VERIFY_BOTH_NATIVE_SYMBOL_DEFINITIONS"
 so=outputs[0]
 info=find_ndk()
 nm=info["ndk"]/"toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
 run=subprocess.run([str(nm),"-D","--defined-only",str(so)],
        capture_output=True,text=True,timeout=90,env=native.clean_env())
 if run.returncode:raise ValueError("llvm-nm dynamic symbol table read failed")
 symbols={}
 for symbol in EXPECTED.values():
  found=re.findall(r"(?m)^[0-9a-fA-F]+\s+[Tt]\s+"+re.escape(symbol)+r"$",run.stdout)
  symbols[symbol]=len(found)
  if len(found)!=1:raise ValueError("PRE432 callback not defined exactly once "+symbol)
 EXTRA={"on_flag_passed_to_both_guest_shards":True,
        "compile_commands":compilation,"native_callback_definitions":symbols,
        "both_callbacks_defined_exactly_once":True}
 PHASE="PRE432_NATIVE_VALIDATION_COMPLETE"
 return outputs

def audit():
 global PHASE,EXTRA
 before=(native.replay_v37,native.stage_logger,native.find_outputs,
         native.FEATURE,native.CALLBACK,native.PAL_FILENAME)
 try:
  PHASE="PRE432_AUTHENTICATED_V46_REPLAY"
  original_find=native.find_outputs
  native.replay_v37=v46.replay_v46_sources
  native.stage_logger=v46.install_probe
  native.find_outputs=lambda build:inspect_linked_outputs(build,original_find)
  native.FEATURE=v46.FEATURE
  native.CALLBACK=EXPECTED["nfsmw_recomp.57.cpp"]
  native.PAL_FILENAME="nfsmw_recomp.57.cpp"
  result=native.audit(Path(__file__).resolve().parents[2])
  result["pre432_native_evidence"]=EXTRA
  result["status"]="AUDIT_OK" if (
      result.get("status")=="AUDIT_OK" and
      EXTRA.get("on_flag_passed_to_both_guest_shards") is True and
      EXTRA.get("both_callbacks_defined_exactly_once") is True
   ) else "NEEDS_REVIEW"
  result["stage"]="PRE432_V46_SOURCE_CHAIN_DUAL_NATIVE_ARM64_LINK_NO_APK"
  result["v46_source_chain_replayed"]=True
  result["identical_to_v46_signed_apk_proven"]=False
  result["apk_built"]=False;result["signed"]=False
  result["saves_accessed"]=False;result["signing_material_accessed"]=False
  return result
 finally:
  (native.replay_v37,native.stage_logger,native.find_outputs,
   native.FEATURE,native.CALLBACK,native.PAL_FILENAME)=before

def main():
 global PHASE
 p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);args=p.parse_args()
 OUT.parent.mkdir(parents=True,exist_ok=True)
 try:r=audit()
 except Exception as e:
  r={"status":"FAILED","error_type":type(e).__name__,"safe_phase":PHASE,
     "source_chain_linked":False,"apk_built":False,"signed":False,
     "saves_accessed":False,"signing_material_accessed":False}
  # Only disclose a fixed safe reason, never paths, environment or passwords.
  msg=str(e)
  if msg.startswith(("PRE432 ","Expected one original","compile_commands.json",
                   "llvm-nm dynamic symbol table")):r["known_reason"]=msg[:180]
 r["run_id"]=args.run_id;r["utc"]=datetime.now(timezone.utc).isoformat()
 OUT.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n")
 print("PRE432_STATUS",r["status"],"ERROR_TYPE",r.get("error_type","none"))
 print("PRE432_PHASE",PHASE)
 print("PRE432_REASON",r.get("known_reason","none"))
 print("PRE432_CONFIG",r.get("cmake_configure",{}).get("ok"))
 print("PRE432_NATIVE_BUILD",r.get("production_native_build",{}).get("ok"))
 print("PRE432_ARM64_ELF",r.get("linked_library",{}).get("arm64_elf"))
 print("PRE432_BOTH_SHARD_FLAGS",r.get("pre432_native_evidence",{}).get("on_flag_passed_to_both_guest_shards"))
 print("PRE432_BOTH_CALLBACKS",r.get("pre432_native_evidence",{}).get("native_callback_definitions"))
 print("PRE432_NO_APK",True)
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
