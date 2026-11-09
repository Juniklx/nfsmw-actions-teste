#!/usr/bin/env python3
"""PRE625: authenticated ARM64 native-link gate for PRE622 passive attribute logger.
Uses PRE448 reconstructed PRE429+PRE447 baseline in a disposable source tree.
No APK, permanent key, game archive, save mutation, or source publication.
"""
import argparse,hashlib,json,re,shlex,subprocess
from pathlib import Path
from datetime import datetime,timezone
import pre288_bmw_feature_on_pal_native_preflight as native
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre447_bmw_lookup_route_probe_dryrun as p447
import pre448_v47_native_zero_route_preflight as old
import pre622_bmw_attr_host_value_probe_ram_only as p622
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre285_bmw_arm64_ndk_logger_preflight import find_ndk

OUT=Path("/tmp/nfsmw-pre625/report.json")
MODULE="nativo/app/src/nfsmw_bmw_attr_value_pre625.cpp"
REGISTER="target_sources(nfsmw PRIVATE src/nfsmw_bmw_attr_value_pre625.cpp)"
DEFINE="#define "+p622.FLAG+" 1\n"
LOGGER=r"""#include <atomic>
#include <cstdint>
#include <rex/logging/macros.h>
// Values delivered from existing guest REX_LOAD, no guest-pointer dereference.
static std::atomic<std::uint32_t> g_pre625_lines{0};
extern "C" void NFSMW_PRE622_ATTR_VALUE(unsigned caller, unsigned category,
                                         unsigned address, int value) noexcept {
  if (caller != 0x8256F83Cu || category > 6u) return;
  if (g_pre625_lines.fetch_add(1u, std::memory_order_relaxed) >= 128u) return;
  REXLOG_INFO("[NFSMW_PRE622_ATTR_VALUE] caller=0x{:08X} category={} addr=0x{:08X} value={}",
              caller,category,address,value);
}
"""
INFO={}
PHASE="START"
def sha(b):return hashlib.sha256(b).hexdigest()

def patch_route_sha_pinned(raw):
    if sha(raw)!=old.PIN_PRE447_SHA256:
        raise ValueError("PRE625 expected original PRE447 route source SHA")
    src=raw.decode("utf-8")
    if p622.FLAG in src or p622.SYMBOL in src:
        raise ValueError("PRE625 duplicate callback/feature")
    body=body_for_function(src,p622.FNAME)
    lines=body.splitlines(keepends=True)
    initial=[i for i,l in enumerate(lines) if l.strip()=="uint32_t ea{};"]
    reads=[i for i,l in enumerate(lines) if
           "ctx.r3.u64 = REX_LOAD_U32(ctx.r11.u32 + 0);" in l]
    if len(initial)!=1 or len(reads)!=1 or src.count("NFSMW_PRE447_ROUTE(")!=4:
        raise ValueError("PRE625 original route site or local variable moved")
    pieces=[]
    for i,l in enumerate(lines):
        if i==initial[0]:pieces.append(p622.LOCAL)
        pieces.append(l)
        if i==reads[0]:pieces.append(p622.TRACE)
    patched_body="".join(pieces)
    patched=src.replace(body,patched_body,1)
    m=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)",patched)
    if m is None:raise ValueError("PRE625 no guest declaration anchor")
    decl=DEFINE+p622.DECL
    patched=patched[:m.start()]+decl+patched[m.start():]
    if patched.count(p622.SYMBOL+"(")!=2 or patched.count(DEFINE)!=1:
        raise ValueError("PRE625 declaration and call not unique")
    for op in p622.OPS:
        if patched.count(op)!=src.count(op):
            raise ValueError("PRE625 guest load/store count changed "+op)
    if patched.replace(decl,"",1).replace(patched_body,body,1)!=src:
        raise ValueError("PRE625 not reversible")
    return patched

def stage(root):
    global PHASE,INFO
    PHASE="PRE448_REPLAY"
    base=old.stage_all_callbacks(root)
    if base.get("no_gameplay_modifications") is not True:
        raise ValueError("PRE625 inherited source is not a no-gameplay-mod patch")
    PHASE="PRE625_PINNED_GUEST_SOURCE"
    guest=root/old.LOOKUP_PATH
    before=guest.read_bytes()
    changed=patch_route_sha_pinned(before)
    guest.write_text(changed,encoding="utf-8")
    if sha(guest.read_bytes())!=sha(changed.encode()):
        raise ValueError("PRE625 guest readback failed")
    PHASE="PRE625_REGISTER_CALLBACK"
    cpp=root/MODULE
    if cpp.exists():raise ValueError("PRE625 native file already exists")
    cpp.parent.mkdir(parents=True,exist_ok=True)
    cpp.write_text(LOGGER,encoding="utf-8")
    cmake=root/"nativo/app/CMakeLists.txt"
    original=cmake.read_text(encoding="utf-8")
    if original.count(old.REGISTER)!=1 or REGISTER in original:
        raise ValueError("PRE625 previous CMake module anchor missing")
    addition="\n    "+REGISTER
    cmake.write_text(original.replace(old.REGISTER,old.REGISTER+addition,1),encoding="utf-8")
    if cmake.read_text(encoding="utf-8").replace(addition,"",1)!=original:
        raise ValueError("PRE625 CMake change not reversible")
    INFO={
      "old_PRE429_PRE447_source_hooks_retained":True,
      "new_shard_sha256":sha(guest.read_bytes()),
      "native_cpp_sha256":sha(cpp.read_bytes()),
      "callback_registered_once":True,
      "guest_patch_exact_reversal_verified":True,
      "new_guest_memory_ops_or_calls":0,
      "host_callback_no_guest_pointer_dereference":True,
      "logger_max_lines":128,
      "source_reconstructed_in_disposable_native_workspace":True
    }
    PHASE="PRE625_STAGE_READY"
    return {**base,**INFO}

def check_native(build,original_find):
    global PHASE
    PHASE="PRE625_VERIFY_LINKED_ARM64"
    outputs=old.review_native_elf(build,original_find)
    so=outputs[0]
    cc=json.loads((build/"compile_commands.json").read_text())
    shards=[x for x in cc if Path(x.get("file","")).name=="nfsmw_recomp.28.cpp"]
    hosts=[x for x in cc if Path(x.get("file","")).name==Path(MODULE).name]
    if len(shards)!=1 or len(hosts)!=1:
        raise ValueError("PRE625 guest or native module not compiled exactly once")
    args=shards[0].get("arguments") or shlex.split(shards[0].get("command",""))
    if "-D"+p447.FLAG+"=1" not in args:
        raise ValueError("PRE625 PRE447 route flag missing in compilation")
    nm=find_ndk()["ndk"]/"toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
    p=subprocess.run([str(nm),"-D","--defined-only",str(so)],capture_output=True,
                     text=True,timeout=90,env=native.clean_env())
    if p.returncode:
        raise ValueError("PRE625 llvm-nm inspection failed")
    matches=re.findall(r"(?m)^[0-9A-Fa-f]+\s+[Tt]\s+"+re.escape(p622.SYMBOL)+r"$",p.stdout)
    if len(matches)!=1 or b"NFSMW_PRE622_ATTR_VALUE" not in so.read_bytes():
        raise ValueError("PRE625 new callback not uniquely exported")
    if old.EVIDENCE.get("all_callbacks_defined_once") is not True:
        raise ValueError("PRE625 old native callbacks missing")
    INFO.update({
      "new_callback_exported_exactly_once":True,
      "previous_3_callbacks_exported_once":True,
      "elf_arm64_sha256":sha(so.read_bytes()),
      "feature_flag_present_in_compiled_guest":True,
      "native_module_compiled_once":True
    })
    PHASE="PRE625_ARM64_LINK_OK"
    return outputs

def audit():
    global PHASE
    p622_report=json.loads(Path("docs/PRE622_BMW_ATTR_HOST_VALUE_RAM_PREVIEW.json").read_text())
    p624=json.loads(Path("docs/PRE624_CANONICAL_CONTEXT_SYNC_RESULT.json").read_text())
    if (p622_report.get("status")!="AUDIT_OK"
       or p622_report.get("new_guest_memory_reads")!=0
       or p622_report.get("source_reverted_bit_for_bit") is not True
       or p624.get("status")!="AUDIT_OK"
       or p624.get("new_handoff_readback_verified") is not True):
        raise ValueError("PRE625 source/prior context evidence missing")
    state=(native.replay_v37,native.stage_logger,native.find_outputs,
           native.FEATURE,native.CALLBACK,native.PAL_FILENAME)
    finder=native.find_outputs
    try:
        native.replay_v37=v46.replay_v46_sources
        native.stage_logger=stage
        native.find_outputs=lambda build:check_native(build,finder)
        native.FEATURE=p447.FLAG
        native.CALLBACK=p622.SYMBOL
        native.PAL_FILENAME=p447.FILES["lookup"][0]
        PHASE="REBUILD_SOURCE_AND_COMPILE"
        report=native.audit(Path(__file__).resolve().parents[2])
        ok=(report.get("status")=="AUDIT_OK"
           and INFO.get("new_callback_exported_exactly_once") is True
           and INFO.get("previous_3_callbacks_exported_once") is True)
        return {
           "stage":"PRE625_BMW_EXTRA_HOST_CALLBACK_ARM64_NO_APK",
           "status":"AUDIT_OK" if ok else "NEEDS_REVIEW",
           "source_archive_sha256":report.get("backup_sha256"),
           "native_cmake_ok":report.get("cmake_configure",{}).get("ok"),
           "native_build_ok":report.get("production_native_build",{}).get("ok"),
           "native_arm64_elf":report.get("linked_library",{}).get("arm64_elf"),
           "evidence":INFO,
           "source_equivalent_to_V47_48_not_bit_identical_signed_APK":True,
           "APK_built":False,"signed":False,"save_modified":False,
           "game_assets_modified":False,"signing_material_accessed":False,
           "guest_runtime_executed":False,"tuning_enabled":False
        }
    finally:
        (native.replay_v37,native.stage_logger,native.find_outputs,
         native.FEATURE,native.CALLBACK,native.PAL_FILENAME)=state

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:res=audit()
    except Exception as e:
       res={"stage":"PRE625_BMW_EXTRA_HOST_CALLBACK_ARM64_NO_APK","status":"FAILED",
            "phase":PHASE,"error_type":type(e).__name__,"error":str(e)[:230],
            "APK_built":False,"signed":False,"save_modified":False,
            "game_assets_modified":False,"signing_material_accessed":False}
    res["run_id"]=a.run_id;res["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n")
    print("PRE625_STATUS",res["status"],"PHASE",PHASE)
    print("PRE625_ERROR",res.get("error_type","none"),res.get("error",""))
    return 0 if res["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
