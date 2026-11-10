#!/usr/bin/env python3
"""PRE673: compile-only, default-OFF, V51 renderer with authenticated PRE671
Vulkan native adapter plus PRE672 host capability guards. C++ compile-time
consistency only; no guard callsite, no VkQueryPool instance, no APK.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from datetime import datetime,timezone
from pathlib import Path
import pre671_v51_native_vulkan_adapter_arm64_noapk as p671
import pre648_v50_shader_pass_counts_arm64_noapk as p648
import pre288_bmw_feature_on_pal_native_preflight as native
OUT=Path("/tmp/nfsmw-pre673/PRE673_V51_VULKAN_ADAPTER_GUARD_REAL_ARM64_NOAPK.json")
GUARD=Path("automation/kaggle/pre672_gpu_timestamp_capability_failclosed_host.h")
PIN=Path("docs/PRE672_V51_VULKAN_MULTIVIEW_TILE_FENCE_HOST_GUARD_VERIFIED.json")
OLD_PIN=Path("docs/PRE671_V51_NATIVE_VULKAN_ARM64_COMPILE_GATE_VERIFIED.json")
DST=Path("nativo/app/src/nfsmw_pre673_gpu_guards_compile_only.h")
PRE671_INC='#include "nfsmw_pre671_vk_pool_compile_only.h"  // PRE671_VULKAN_COMPILE_ONLY_DEFAULT_OFF\n'
EXTRA=(
 '#include "nfsmw_pre673_gpu_guards_compile_only.h"  // PRE673_GPU_GUARD_COMPILE_ONLY_DEFAULT_OFF\n'
 'static_assert(!nfsmw::pre672::kDefaultEnabled, "PRE673 GPU guard must remain default OFF");\n'
 'static_assert(nfsmw::pre672::kQueriesPerSlot == nfsmw::pre671::kQueriesPerSlot, "PRE673 query budget mismatch");\n'
 'static_assert(nfsmw::pre672::kPairsPerSlot == nfsmw::pre671::kMaxPairsPerSlot, "PRE673 pair budget mismatch");\n'
 'static_assert(nfsmw::pre672::kMaxSlots == nfsmw::pre671::kMaxSlots, "PRE673 slot budget mismatch");\n'
 'static_assert(sizeof(nfsmw::pre672::GuardedLifecycle) > 0, "PRE673 guard model not parsed");\n'
)
PHASE="START"
EVIDENCE={}
ORIG_STAGE=None
ORIG_VERIFY=None
def sha(x):return hashlib.sha256(x).hexdigest()
def preflight():
    a=json.loads(PIN.read_text())
    b=json.loads(OLD_PIN.read_text())
    raw=GUARD.read_bytes()
    if not(
        a.get("github_run_id")==42860554425
        and a.get("status")=="PASS_HOST_VULKAN_CAPABILITY_AND_LIFECYCLE_DENY_BY_DEFAULT"
        and a.get("code_sha256",{}).get(str(GUARD))==sha(raw)
        and a.get("limits",{}).get("host_only") is True
        and b.get("github_run_id")==42853007076
        and b.get("status")=="AUDIT_OK_AARCH64_COMPILE_ONLY_NO_RUNTIME_VULKAN_POOL"
        and b.get("vulkan_adapter_header_sha256")=="8f371e041303eab3a83592ce0440cf245b843b04b270bb5e072eab9a54fb1584"
    ):raise ValueError("PRE673 prior ARM64 and host capability pins are not authentic")
    for required in (b"namespace nfsmw::pre672",b"constexpr bool kDefaultEnabled = false",
        b"subpass_multiview_status_known",b"per_tile_mode_status_known",
        b"per_tile_mode_active = true",b"vkCmdResetQueryPool",b"ReadyToEndRenderPass",
        b"VkFenceOutcome::Success",b"QueryOutcome::Error",b"kMaxSlots = 16"):
        if required not in raw: raise ValueError("PRE673 guard missing "+required.decode())
    return sha(raw)
def stage(root):
    global PHASE
    PHASE="PRE671_AUTHENTICATED_STAGE"
    out=ORIG_STAGE(root)
    cpp=root/p648.SOURCE
    dst=root/DST
    old=cpp.read_bytes()
    if dst.exists():raise ValueError("PRE673 guard header unexpectedly exists")
    txt=old.decode("utf-8")
    if txt.count(PRE671_INC)!=1 or "PRE673_GPU_GUARD_COMPILE_ONLY_DEFAULT_OFF" in txt:
        raise ValueError("PRE673 original PRE671 adapter include missing/non-unique")
    patched=txt.replace(PRE671_INC,PRE671_INC+EXTRA,1)
    if patched.count("PRE673_GPU_GUARD_COMPILE_ONLY_DEFAULT_OFF")!=1:
        raise ValueError("PRE673 malformed include integration")
    if patched.replace(PRE671_INC+EXTRA,PRE671_INC,1).encode("utf-8")!=old:
        raise ValueError("PRE673 reverse is not byte-for-byte identical")
    data=GUARD.read_bytes()
    cpp.write_bytes(patched.encode("utf-8"))
    dst.write_bytes(data)
    if dst.read_bytes()!=data or cpp.read_bytes()!=patched.encode("utf-8"):
        raise ValueError("PRE673 file write mismatch")
    EVIDENCE.update({
        "pre672_guard_sha256":sha(data),
        "pre673_temporary_renderer_sha256":sha(patched.encode("utf-8")),
        "pre673_reverse_to_pre671_byte_identical":True,
        "runtime_guard_constructed":False,
        "native_guards_compiled_only_not_called":True,
        "pre671_separate_vk_query_pool_created":False,
        "vk_timestamp_runtime_calls_added":False,
        "C2_timestamp_pool_modified":False,
        "default_enabled":False,
        "safety_modes_checked_by_runtime":False,
        "real_gpu_timestamps_recorded":False,
    })
    PHASE="AARCH64_COMPILATION"
    return {**out,"pre673_compile_only_gpu_guards_in_renderer":True}
def verify(build,origfind):
    global PHASE
    PHASE="AARCH64_LINKED_ELF_CHECK"
    bins=ORIG_VERIFY(build,origfind)
    if len(bins)!=1 or not native.arm64_elf(bins[0]):
        raise ValueError("PRE673 AArch64 ELF missing")
    dat=bins[0].read_bytes()
    for m in (b"PRE648 GPU_SHADER10s",b"NFSMW_PRE635_C3_TWOREQUEST_TRACE",
              b"NFSMW_PRE194_C3",b"NFSMW_PRE398_GLOBAL_NITRO_FULL"):
        if m not in dat:raise ValueError("PRE673 original native guard marker missing")
    EVIDENCE.update({
        "arm64_elf_bytes":len(dat),"arm64_elf_sha256":sha(dat),
        "native_previous_diagnostic_markers_intact":True,
    })
    PHASE="AARCH64_COMPILE_ONLY_COMPLETE"
    return bins
def main():
    global ORIG_STAGE,ORIG_VERIFY,PHASE
    ap=argparse.ArgumentParser()
    ap.add_argument("--run-id",required=True)
    args=ap.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:
        if not args.run_id.isdecimal():raise ValueError("invalid GitHub run id")
        guardsha=preflight()
        ORIG_STAGE=p671.stage
        ORIG_VERIFY=p671.verify_elf
        try:
            p671.stage=stage
            p671.verify_elf=verify
            old_argv=sys.argv
            try:
                sys.argv=[old_argv[0],"--run-id",args.run_id]
                rc=p671.main()
            finally:
                sys.argv=old_argv
        finally:
            p671.stage=ORIG_STAGE
            p671.verify_elf=ORIG_VERIFY
        b=json.loads(p671.OUT.read_text())
        ok=(rc==0 and b.get("status")=="AUDIT_OK_AARCH64_COMPILE_ONLY_NO_RUNTIME_VULKAN_POOL"
            and EVIDENCE.get("pre672_guard_sha256")==guardsha
            and EVIDENCE.get("pre673_reverse_to_pre671_byte_identical") is True
            and EVIDENCE.get("native_previous_diagnostic_markers_intact") is True
            and EVIDENCE.get("arm64_elf_sha256")==b.get("arm64_elf_sha256")
            and EVIDENCE.get("arm64_elf_bytes",0)>50_000_000)
        report={
            "status":"PASS_REAL_ARM64_ADAPTER_AND_CAPABILITY_GUARD_COMPILE_ONLY_NOAPK" if ok else "NOT_APPROVED",
            "phase":PHASE,"github_run_id":int(args.run_id),
            "native_arm64_compiled":bool(ok),
            "arm64_elf_sha256":EVIDENCE.get("arm64_elf_sha256"),
            "source_stage_report":b,
            "evidence":EVIDENCE,
            "runtime_capability_checks_executed":False,
            "real_gpu_timestamps":False,
            "real_vulkan_pool_created":False,
            "apk_built":False,"signing_material_accessed":False,
            "user_saves_modified":False,"shader_spirv_modified":False,
            "fps_gain_proven":False,
            "next":"Inspect SpeedBreaker techniques read-only; then real Android GPU caps and frame pacing evidence before enabling optional timestamp paths"
        }
    except Exception as e:
        report={"status":"FAILED_CLOSED","phase":PHASE,
            "error_type":type(e).__name__,
            "error_summary":str(e)[:400] if isinstance(e,ValueError) else "native source/toolchain exception",
            "native_arm64_compiled":False,"apk_built":False,"fps_gain_proven":False}
    report.update({"stage":"PRE673_V51_REAL_AARCH64_GPU_GUARDS_AND_SEPARATE_VULKAN_ADAPTER_COMPILE_ONLY",
                   "utc":datetime.now(timezone.utc).isoformat()})
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    for key in ("status","phase","error_type"):
        print("PRE673_"+key.upper()+"="+str(report.get(key,"none")))
    print("PRE673_ARM64_COMPILED="+str(report.get("native_arm64_compiled",False)))
    print("PRE673_DEFAULT_ENABLED=false")
    print("PRE673_VULKAN_POOL_CREATED=false")
    print("PRE673_GPU_TIME_MEASURED=false")
    print("PRE673_APK_CREATED=false")
    return 0 if report["status"]=="PASS_REAL_ARM64_ADAPTER_AND_CAPABILITY_GUARD_COMPILE_ONLY_NOAPK" else 1
if __name__=="__main__":raise SystemExit(main())
