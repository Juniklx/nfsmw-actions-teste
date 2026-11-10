#!/usr/bin/env python3
"""PRE671 isolated native ARM64 compile-only Vulkan timestamp-pool adapter.
Source: authenticated PRE99/PRE638/PRE648 V51 recipe, no existing source edits.
The separate VkQueryPool adapter is COMPILED AS HEADER ONLY; not constructed,
invoked, created or enabled in the renderer runtime. No APK/keys/user saves.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
import pre648_v50_shader_pass_counts_arm64_noapk as p648
import pre665_v51_gpu_draw_emission_boundaries_readonly as p665
import pre288_bmw_feature_on_pal_native_preflight as native

OUT=Path("/tmp/nfsmw-pre671/PRE671_V51_VULKAN_POOL_ADAPTER_ARM64_NOAPK.json")
GATE668=Path("docs/PRE668_V51_VULKAN_RENDERPASS_AND_QUERY_SCOPE_VERIFIED.json")
GATE670=Path("docs/PRE670_V51_DEDICATED_TIMESTAMP_HOST_RESOURCE_SAFETY_VERIFIED.json")
HEADER=Path("automation/kaggle/pre671_vk_separate_timestamp_pool_compile_only.h")
DST=Path("nativo/app/src/nfsmw_pre671_vk_pool_compile_only.h")
ANCHOR='#include "nfsmw_pre648_shader_pass_counter.h"  // PRE648_DIAGNOSTIC_ONLY\n'
INSERT=(
 '#include "nfsmw_pre671_vk_pool_compile_only.h"  // PRE671_VULKAN_COMPILE_ONLY_DEFAULT_OFF\n'
 'static_assert(!nfsmw::pre671::kDefaultEnabled, "PRE671 must be disabled by default");\n'
 'static_assert(nfsmw::pre671::kQueriesPerSlot == 8, "PRE671 must use isolated eight-query budget");\n'
 'static_assert(nfsmw::pre671::kMaxPairsPerSlot == 4, "PRE671 four bounded pairs per slot");\n'
 'static_assert(sizeof(nfsmw::pre671::Adapter)>0, "PRE671 Vulkan adapter must parse in native AArch64 TU");\n'
)
PHASE="START"
EVIDENCE={}
ORIGINAL_STAGE=None
ORIGINAL_VERIFY=None
def sha(b):return hashlib.sha256(b).hexdigest()
def gate():
  p648.require_gates()
  a=json.loads(GATE668.read_text())
  b=json.loads(GATE670.read_text())
  if not (
    a.get("github_run_id")==42840437196
    and a.get("status")=="AUDIT_OK_SOURCE_SCOPE_AND_QUERY_LIFETIME_CANDIDATES_ONLY"
    and a.get("authenticated_source",{}).get("renderer_v51_sha256")==p665.PIN_RENDER
    and a.get("authenticated_source",{}).get("backend_sha256")==p665.PIN_DESTINOS
    and a.get("limits",{}).get("separate_query_pool_created") is False
    and b.get("github_run_id")==42848964021
    and b.get("status")=="HOST_PASS_CHECKED_FENCE_RESOURCE_GUARDS_ONLY"
    and b.get("findings",{}).get("native_pool_created") is False
    and b.get("findings",{}).get("apk_built") is False
    and b.get("findings",{}).get("host_asan_ubsan_pass") is True
  ): raise ValueError("PRE671 prior source/host gates do not match")
  raw=HEADER.read_bytes()
  required=(
    b"#include <vulkan/vulkan.h>",
    b"static constexpr bool kDefaultEnabled = false",
    b"PFN_vkCreateQueryPool",
    b"PFN_vkDestroyQueryPool",
    b"PFN_vkCmdResetQueryPool",
    b"PFN_vkCmdWriteTimestamp",
    b"PFN_vkGetQueryPoolResults",
    b"PFN_vkDeviceWaitIdle",
    b"actual_previous_fence_result != VK_SUCCESS",
    b"actual_fence_result != VK_SUCCESS",
    b"VK_QUERY_RESULT_WITH_AVAILABILITY_BIT",
    b"VK_QUERY_TYPE_TIMESTAMP",
    b"VK_NOT_READY",
    b"VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT",
    b"VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT",
    b"request_enable",
    b"queue_family_timestamp_valid_bits",
  )
  if not all(x in raw for x in required):raise ValueError("PRE671 native header missing required Vulkan fence/pool API")
  return sha(raw)
def stage(root):
  global PHASE
  PHASE="AUTHENTICATED_V51_REPLAY"
  result=ORIGINAL_STAGE(root)
  cpp=root/p648.SOURCE
  dst=root/DST
  before=cpp.read_bytes()
  if sha(before)!=p665.PIN_RENDER:raise ValueError("PRE671 unexpected renderer V51 fingerprint")
  if dst.exists():raise ValueError("PRE671 adapter already exists in temporary workspace")
  original=before.decode("utf-8")
  if original.count(ANCHOR)!=1 or "PRE671_VULKAN_COMPILE_ONLY_DEFAULT_OFF" in original:
    raise ValueError("PRE671 non-unique include anchor/double patch")
  new=original.replace(ANCHOR,ANCHOR+INSERT,1)
  if new.count("PRE671_VULKAN_COMPILE_ONLY_DEFAULT_OFF")!=1:
    raise ValueError("PRE671 source integration mismatch")
  restored=new.replace(ANCHOR+INSERT,ANCHOR,1).encode("utf-8")
  if restored!=before:raise ValueError("PRE671 source not byte-reversible")
  header=HEADER.read_bytes()
  cpp.write_bytes(new.encode("utf-8"))
  dst.write_bytes(header)
  if cpp.read_bytes()!=new.encode("utf-8") or dst.read_bytes()!=header:
    raise ValueError("PRE671 source written incompletely")
  EVIDENCE.update({
     "baseline_renderer_sha256":sha(before),
     "patched_compile_only_renderer_sha256":sha(new.encode("utf-8")),
     "vulkan_adapter_header_sha256":sha(header),
     "source_reverse_byte_identical":True,
     "vulkan_declarations_parsed_in_renderer_arm64_TU":True,
     "adapter_compiled_only_not_called":True,
     "adapter_runtime_constructed":False,
     "runtime_vk_query_pool_created":False,
     "runtime_vk_timestamp_written":False,
     "C2_query_pool_modified":False,
     "native_renderer_has_no_new_draw_submission_calls":True,
     "default_enabled":False,
     "only_temporary_source_tree_modified":True,
  })
  PHASE="ARM64_COMPILE_READY"
  return {**result,"pre671_compile_only_adapter_parse_in_renderer":True}
def verify_elf(build,original_find):
  global PHASE
  PHASE="REAL_AARCH64_ELF_VALIDATION"
  bins=ORIGINAL_VERIFY(build,original_find)
  if len(bins)!=1 or not native.arm64_elf(bins[0]):
    raise ValueError("PRE671 AArch64 ELF missing")
  data=bins[0].read_bytes()
  for marker in (
    b"PRE648 GPU_SHADER10s",
    b"NFSMW_PRE635_C3_TWOREQUEST_TRACE",
    b"NFSMW_PRE194_C3",
    b"NFSMW_PRE398_GLOBAL_NITRO_FULL"
  ):
    if marker not in data:raise ValueError("PRE671 old diagnostic/guard missing from ELF")
  EVIDENCE.update({"linked_real_arm64_libmain_bytes":len(data),
                   "linked_real_arm64_libmain_sha256":sha(data),
                   "all_existing_native_guard_markers_preserved":True})
  PHASE="REAL_ARM64_NOAPK_GATE_PASS"
  return bins
def main():
  global ORIGINAL_STAGE,ORIGINAL_VERIFY,PHASE
  ap=argparse.ArgumentParser()
  ap.add_argument("--run-id",required=True)
  arg=ap.parse_args()
  OUT.parent.mkdir(parents=True,exist_ok=True)
  try:
    if not arg.run_id.isdecimal():raise ValueError("run ID is not numeric")
    pin=gate()
    ORIGINAL_STAGE=p648.stage_source
    ORIGINAL_VERIFY=p648.verify_elf
    try:
      p648.stage_source=stage
      p648.verify_elf=verify_elf
      PHASE="BUILD_NATIVE_AARCH64_SOURCE_REPLAY"
      base=p648.audit(arg.run_id)
    finally:
      p648.stage_source=ORIGINAL_STAGE
      p648.verify_elf=ORIGINAL_VERIFY
    good=(base.get("status")=="AUDIT_OK"
      and base.get("native_cmake_ok") is True
      and base.get("native_build_ok") is True
      and EVIDENCE.get("vulkan_adapter_header_sha256")==pin
      and EVIDENCE.get("source_reverse_byte_identical") is True
      and EVIDENCE.get("all_existing_native_guard_markers_preserved") is True
      and base.get("linked_library_sha256")==EVIDENCE.get("linked_real_arm64_libmain_sha256")
      and EVIDENCE.get("adapter_runtime_constructed") is False)
    report={
      "stage":"PRE671_V51_VULKAN_NATIVE_SEPARATE_POOL_ADAPTER_COMPILE_ONLY",
      "status":"AUDIT_OK_AARCH64_COMPILE_ONLY_NO_RUNTIME_VULKAN_POOL" if good else "NOT_APPROVED",
      "phase":PHASE,"github_run_id":int(arg.run_id),"native_arm64_compiled":bool(good),
      "arm64_elf_sha256":base.get("linked_library_sha256"),
      "native_production_compile_report":base,"evidence":EVIDENCE,
      "query_pool_created":False,"timestamp_queries_recorded":False,
      "runtime_device_timestamp_capabilities_checked":False,
      "adapter_called_at_runtime":False,"gpu_time_measured":False,"apk_built":False,
      "signing_material_accessed":False,"user_saves_accessed":False,
      "shader_spirv_modified":False,"fps_gain_proven":False,
      "next":"PRE672 audit native Vulkan real-callsite integration/fence error behavior and host simulation; no APK, no release until device gates"}
  except Exception as exc:
    report={"stage":"PRE671_V51_VULKAN_NATIVE_SEPARATE_POOL_ADAPTER_COMPILE_ONLY",
      "status":"FAILED_CLOSED","phase":PHASE,"error_type":type(exc).__name__,
      "error_summary":str(exc)[:400] if isinstance(exc,ValueError) else "native toolchain/replay exception",
      "native_arm64_compiled":False,"apk_built":False,"signing_material_accessed":False,
      "fps_gain_proven":False}
  report["utc"]=datetime.now(timezone.utc).isoformat()
  OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
  for k in ("status","phase","error_type"):
    print("PRE671_"+k.upper()+"="+str(report.get(k,"none")))
  print("PRE671_AARCH64_COMPILE="+str(report.get("native_arm64_compiled",False)))
  print("PRE671_ADAPTER_DEFAULT_ENABLED=false")
  print("PRE671_RUNTIME_POOL_CREATED=false")
  print("PRE671_REAL_GPU_MEASURED=false")
  print("PRE671_APK_BUILT=false")
  print("PRE671_FPS_GAIN_PROVEN=false")
  return 0 if report["status"]=="AUDIT_OK_AARCH64_COMPILE_ONLY_NO_RUNTIME_VULKAN_POOL" else 1
if __name__=="__main__":sys.exit(main())
