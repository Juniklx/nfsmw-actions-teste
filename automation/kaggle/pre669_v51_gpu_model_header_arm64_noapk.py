#!/usr/bin/env python3
"""PRE669: compile-only, reversible renderer-translation-unit connection of
the PRE666 bounded pass model. Real ARM64 libmain.so with PRE648 source recipe.
No vkCmdWriteTimestamp, new pool, device measurement, APK, signing or saves.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
import pre648_v50_shader_pass_counts_arm64_noapk as p648
import pre665_v51_gpu_draw_emission_boundaries_readonly as p665
import pre288_bmw_feature_on_pal_native_preflight as native

OUT=Path("/tmp/nfsmw-pre669/PRE669_V51_PASS_MODEL_COMPILE_ONLY_ARM64_NOAPK.json")
GATE=Path("docs/PRE668_V51_VULKAN_RENDERPASS_AND_QUERY_SCOPE_VERIFIED.json")
MODEL_HEADER=Path("automation/kaggle/pre666_pass_bounded_sampler.h")
FINAL_HEADER=Path("nativo/app/src/nfsmw_pre666_pass_bounded_sampler.h")
TAG="PRE669_COMPILE_ONLY_NO_VULKAN"
FREQ_INC='#include "nfsmw_pre648_shader_pass_counter.h"  // PRE648_DIAGNOSTIC_ONLY\n'
EXTRA=(
 '#include "nfsmw_pre666_pass_bounded_sampler.h"  // PRE669_COMPILE_ONLY_NO_VULKAN\n'
 'static_assert(!nfsmw::pre666::kDefaultEnabled, "PRE669 model MUST stay disabled");\n'
 'static_assert(nfsmw::pre666::kQueriesPerSlot == 8, "PRE669 bounded budget is exactly eight");\n'
)
ORIG=None
ORIG_VERIFY=None
EVIDENCE={}
PHASE="START"
def sha(b):return hashlib.sha256(b).hexdigest()
def gates():
  p648.require_gates()
  g=json.loads(GATE.read_text(encoding="utf-8"))
  if not(g.get("github_run_id")==42840437196
     and g.get("status")=="AUDIT_OK_SOURCE_SCOPE_AND_QUERY_LIFETIME_CANDIDATES_ONLY"
     and g.get("authenticated_source",{}).get("renderer_v51_sha256")==p665.PIN_RENDER
     and g.get("authenticated_source",{}).get("backend_sha256")==p665.PIN_DESTINOS
     and g.get("limits",{}).get("native_arm64_compiled") is False
     and g.get("limits",{}).get("apk_built") is False
     and g.get("limits",{}).get("separate_query_pool_created") is False):
      raise ValueError("PRE669 source evidence or no-APK gate missing")
  h=MODEL_HEADER.read_bytes()
  if not all(s in h for s in (
    b"namespace nfsmw::pre666",
    b"constexpr bool kDefaultEnabled = false",
    b"kMaxBurstsPerSlot = 4",
    b"kQueriesPerSlot = kMaxBurstsPerSlot * 2",
    b"BeforeEndRenderPass",
    b"BeforeEndCommandBuffer",
  )):
    raise ValueError("PRE669 verified header API changed")
  if b"vkCmdWriteTimestamp(" in h or b"VkQueryPool " in h:
    raise ValueError("PRE669 host-only header gained native Vulkan implementation")
  return sha(h)
def stage(root):
  global PHASE
  PHASE="PRE648_SOURCE_RECIPE"
  result=ORIG(root)
  cpp=root/p648.SOURCE
  out_header=root/FINAL_HEADER
  raw=cpp.read_bytes()
  if sha(raw)!=p665.PIN_RENDER:
    raise ValueError("PRE669 source SHA differs from authenticated V51 renderer")
  if out_header.exists():
    raise ValueError("PRE669 existing model header in temporary tree")
  src=raw.decode("utf-8")
  if TAG in src or src.count(FREQ_INC)!=1:
    raise ValueError("PRE669 already applied or include anchor not unique")
  patched=src.replace(FREQ_INC,FREQ_INC+EXTRA,1).encode("utf-8")
  reverse=patched.decode("utf-8").replace(FREQ_INC+EXTRA,FREQ_INC,1).encode("utf-8")
  if reverse!=raw or patched==raw or patched.count(TAG.encode("utf-8"))!=1:
    raise ValueError("PRE669 exact source byte reversal failed")
  copy=MODEL_HEADER.read_bytes()
  cpp.write_bytes(patched)
  out_header.write_bytes(copy)
  if cpp.read_bytes()!=patched or out_header.read_bytes()!=copy:
    raise ValueError("PRE669 temp source writeback failed")
  EVIDENCE.update({
     "model_header_sha256":sha(copy),
     "baseline_v51_source_sha256":sha(raw),
     "compile_only_renderer_source_sha256":sha(patched),
     "source_reverse_byte_identical":True,
     "compile_time_default_off":True,
     "separate_query_pool_created":False,
     "vulkan_commands_added":False,
     "native_runtime_sampler_calls_added":False,
     "temporary_workspace_only":True,
  })
  PHASE="NATIVE_COMPILE_READY"
  return {**result,"pre669_compile_only_header_connected_to_renderer":True}
def verify_elf(build,original_find):
  global PHASE
  PHASE="VERIFY_ARM64_ELF"
  bins=ORIG_VERIFY(build,original_find)
  if len(bins)!=1 or not native.arm64_elf(bins[0]):
    raise ValueError("PRE669 expects unique AArch64 ELF after real compile")
  data=bins[0].read_bytes()
  if b"PRE648 GPU_SHADER10s" not in data or b"NFSMW_PRE635_C3_TWOREQUEST_TRACE" not in data:
    raise ValueError("PRE669 native ELF lacks required legacy markers")
  EVIDENCE.update({"real_arm64_libmain_sha256":sha(data),
     "real_arm64_libmain_bytes":len(data),
     "pre648_frequency_diagnostic_retained":True,
     "legacy_C3_and_nitro_preserved":True,
     "model_header_compiled_in_renderer_unit":True,
     "runtime_gpu_timestamp_instrumentation_linked":False})
  PHASE="ARM64_ELF_COMPILE_ONLY_GATE_PASS"
  return bins
def main():
  global ORIG,ORIG_VERIFY,PHASE
  ap=argparse.ArgumentParser();ap.add_argument("--run-id",required=True)
  args=ap.parse_args()
  OUT.parent.mkdir(parents=True,exist_ok=True)
  try:
    if not args.run_id.isdecimal():raise ValueError("run ID must be numeric")
    header_sha=gates()
    ORIG=p648.stage_source;ORIG_VERIFY=p648.verify_elf
    try:
      p648.stage_source=stage
      p648.verify_elf=verify_elf
      PHASE="PRE648_BUILD_PIPELINE_WITH_PRE669_HEADER"
      base=p648.audit(args.run_id)
    finally:
      p648.stage_source=ORIG
      p648.verify_elf=ORIG_VERIFY
    ok=(base.get("status")=="AUDIT_OK" and base.get("native_build_ok") is True
        and base.get("native_cmake_ok") is True
        and EVIDENCE.get("model_header_sha256")==header_sha
        and EVIDENCE.get("source_reverse_byte_identical") is True
        and EVIDENCE.get("model_header_compiled_in_renderer_unit") is True
        and EVIDENCE.get("compile_time_default_off") is True)
    report={"stage":"PRE669_V51_GPU_PASS_MODEL_HEADER_COMPILE_ONLY_ARM64_NOAPK",
      "status":"AUDIT_OK_ARM64_COMPILE_ONLY_NO_GPU_COMMANDS" if ok else "NOT_APPROVED",
      "phase":PHASE,"github_run_id":int(args.run_id),
      "native_arm64_compiled":bool(ok),"arm64_elf_sha256":base.get("linked_library_sha256"),
      "native_production_compile_report":base,"evidence":EVIDENCE,
      "model_header_compile_time_default_off":True,
      "runtime_sampling_enabled":False,"vulkan_query_pool_created":False,
      "vulkan_commands_injected":False,"actual_gpu_time_measured":False,
      "apk_built":False,"signing_material_accessed":False,
      "user_saves_accessed":False,"shader_assets_changed":False,"fps_gain_proven":False,
      "next":"PRE670 implement separately gated true Vulkan pool/resource integration and test real lifecycle in isolated noAPK build before any release"}
  except Exception as ex:
    report={"stage":"PRE669_V51_GPU_PASS_MODEL_HEADER_COMPILE_ONLY_ARM64_NOAPK",
       "status":"FAILED_CLOSED","phase":PHASE,"error_type":type(ex).__name__,
       "error_summary":str(ex)[:420] if isinstance(ex,ValueError) else "Native toolchain or archive transfer failure",
       "native_arm64_compiled":False,"apk_built":False,
       "signing_material_accessed":False,"fps_gain_proven":False}
  report["utc"]=datetime.now(timezone.utc).isoformat()
  OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
  for k in ("status","phase","error_type"):
    print("PRE669_"+k.upper()+"="+str(report.get(k,"none")))
  print("PRE669_ARM64_COMPILE_ONLY="+str(report.get("native_arm64_compiled",False)))
  print("PRE669_MODEL_HEADER_COMPILED="+str(EVIDENCE.get("model_header_compiled_in_renderer_unit",False)))
  print("PRE669_APK_BUILT=false")
  print("PRE669_GPU_TIMESTAMP_INJECTED=false")
  print("PRE669_PER_SHADER_GPU_TIME_MEASURED=false")
  print("PRE669_FPS_GAIN_PROVEN=false")
  return 0 if report["status"]=="AUDIT_OK_ARM64_COMPILE_ONLY_NO_GPU_COMMANDS" else 1
if __name__=="__main__":sys.exit(main())
