#!/usr/bin/env python3
"""PRE448 — native ARM64 link of V47-equivalent + PRE447 lookup-route diagnostics.

Immutable source archive PRE99 is restored to a disposable build workspace.
No Gradle, APK, signing material, user saves, or edits to persistent game source.
All three passive callbacks must be exported exactly once by the actual ELF.
"""
from __future__ import annotations
import argparse,hashlib,json,re,shlex,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
import pre288_bmw_feature_on_pal_native_preflight as native
import pre431_v46_source_dual_trace_compat_readonly as v46
import pre429_bmw_entry_level_correlation_dryrun as p429
import pre447_bmw_lookup_route_probe_dryrun as p447
from pre239_pal_money_probe_recipe_readonly import body_for_function
from pre285_bmw_arm64_ndk_logger_preflight import find_ndk

OUT=Path("/tmp/nfsmw-pre448/report.json")
PATH_ROOT="nativo/app/generated/default/"
LOOKUP_PATH=PATH_ROOT+p447.FILES["lookup"][0]
BUILDER_PATH=PATH_ROOT+p447.FILES["builder"][0]
FEATURE_DEFINE="-D"+p447.FLAG+"=1"
MODULE="nativo/app/src/nfsmw_bmw_route_pre448.cpp"
REGISTER="target_sources(nfsmw PRIVATE src/nfsmw_bmw_route_pre448.cpp)"
EXPECTED_CALLBACKS=(
  "NFSMW_PRE429_TRACE_ENTRY",
  "NFSMW_PRE429_TRACE_LEVEL",
  "NFSMW_PRE447_ROUTE",
)
EXPECTED_SHARDS={
  "nfsmw_recomp.15.cpp":"NFSMW_PRE429_TRACE_ENTRY",
  "nfsmw_recomp.57.cpp":"NFSMW_PRE429_TRACE_LEVEL",
  "nfsmw_recomp.28.cpp":"NFSMW_PRE447_ROUTE",
}
PIN_PRE447_SHA256="aac0b47f03a43044899a5fd7150cd0691eee79f35b2c42f413919f0c61d9d230"
MARKERS=(b"NFSMW_PRE429_ENTRY",b"NFSMW_PRE429_LEVEL",
         b"NFSMW_PRE447_ROUTE",b"NFSMW_PRE398_GLOBAL_NITRO_FULL")
LOGGER=r"""#include <atomic>
#include <cstdint>
#include <rex/logging/macros.h>
// Pure host telemetry: only values supplied by an existing guest return site.
// No guest memory access or guest function call in this callback.
static std::atomic<std::uint32_t> g_pre448_route_logs{0};
extern "C" void NFSMW_PRE447_ROUTE(unsigned caller, unsigned category,
                                      unsigned reason, int candidate) noexcept {
  if(caller!=0x8256F83Cu || category>6u || reason<1u || reason>3u)return;
  const auto n=g_pre448_route_logs.fetch_add(1u,std::memory_order_relaxed);
  if(n>=112u)return;
  REXLOG_INFO("[NFSMW_PRE447_ROUTE] caller=0x{:08X} category={} reason={} candidate_count={}",
              caller,category,reason,candidate);
}
"""
STAGE="INIT"
EVIDENCE={}
def sha(blob:bytes)->str:return hashlib.sha256(blob).hexdigest()
def source_route_patch(original:bytes,preview:dict)->str:
    """Reproduce PRE447's SHA-pinned preview byte-for-byte without running guest code."""
    text=original.decode("utf-8")
    body=body_for_function(text,p447.FILES["lookup"][2])
    lines=body.splitlines(keepends=True)
    exits=[i+1 for i,line in enumerate(lines) if line.strip()=="return;"]
    if exits!=[60,126,153]:raise ValueError("PRE448 route returns moved")
    expanded=[]
    for i,line in enumerate(lines,1):
        if line.strip()=="uint32_t ea{};":expanded.append(p447.LOCAL)
        if i in exits:expanded.append(p447.trace(exits.index(i)+1))
        expanded.append(line)
    new_body="".join(expanded)
    staged=text.replace(body,new_body,1)
    match=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9a-fA-F]{8}\)",staged)
    if match is None:raise ValueError("PRE448 missing guest declaration anchor")
    staged=staged[:match.start()]+p447.DECL+staged[match.start():]
    if sha(staged.encode())!=preview["preview_sha256"] or preview["preview_sha256"]!=PIN_PRE447_SHA256:
        raise ValueError("PRE448 route preview SHA differs from PRE447 run")
    if staged.replace(p447.DECL,"",1).replace(new_body,body,1)!=text:
        raise ValueError("PRE448 route edit not exactly reversible")
    return staged

def stage_all_callbacks(root:Path)->dict:
    global STAGE
    STAGE="PRE448_CONFIRM_PRE447_PINNED_PREVIEW"
    lookup=root/LOOKUP_PATH
    builder=root/BUILDER_PATH
    orig_lookup=lookup.read_bytes()
    orig_builder=builder.read_bytes()
    preview=p447.preview(orig_lookup,orig_builder)
    if preview["preview_sha256"]!=PIN_PRE447_SHA256 or preview["enabled_by_default"] is not False:
        raise ValueError("PRE448 expected default-OFF PRE447 preview mismatch")
    patched_route=source_route_patch(orig_lookup,preview)
    STAGE="PRE448_REPLAY_V47_PRE429"
    previous=v46.install_probe(root)
    if previous.get("cmake_registration_count")!=1 or len(previous["source_reviews"])!=2:
        raise ValueError("PRE448 missing original V47 PRE429 modules")
    # The original V47's PRE434 launcher explicitly enabled both PRE429 shards
    # after the default-OFF, authenticated PRE429 staging.
    enabled={}
    for key in ("entry","list"):
        filename,_,_=p429.SOURCES[key]
        file=root/PATH_ROOT/filename
        raw=file.read_bytes()
        if sha(raw)!=previous["source_reviews"][key]["after_sha256"]:
            raise ValueError("PRE448 unexpected PRE429 guest SHA: "+key)
        decl=p429.ENTRY_DECL if key=="entry" else p429.COUNT_DECL
        directive="#define "+p429.FEATURE+" 1\n"
        source=raw.decode("utf-8")
        if source.count(decl)!=1 or directive in source:
            raise ValueError("PRE448 PRE429 flag conflict: "+key)
        next_source=source.replace(decl,directive+decl,1)
        if next_source.replace(directive,"",1)!=source:
            raise ValueError("PRE448 PRE429 not exactly reversible")
        file.write_text(next_source,encoding="utf-8")
        if file.read_bytes()!=next_source.encode("utf-8"):
            raise ValueError("PRE448 PRE429 staging readback failed")
        enabled[key]={"source":filename,"feature_enabled":True,"sha256":sha(file.read_bytes())}
    STAGE="PRE448_STAGING_LOOKUP_ROUTE"
    # Never touch source outside this disposable native workspace.
    if lookup.read_bytes()!=orig_lookup:raise ValueError("PRE448 lookup source changed unexpectedly")
    lookup.write_text(patched_route,encoding="utf-8")
    if sha(lookup.read_bytes())!=PIN_PRE447_SHA256:
        raise ValueError("PRE448 route guest SHA readback failed")
    module=root/MODULE
    if module.exists():raise ValueError("PRE448 native logger module already exists")
    module.parent.mkdir(parents=True,exist_ok=True)
    module.write_text(LOGGER,encoding="utf-8")
    if module.read_bytes()!=LOGGER.encode("utf-8"):
        raise ValueError("PRE448 native module readback mismatch")
    cmake=root/"nativo/app/CMakeLists.txt"
    original_cmake=cmake.read_text(encoding="utf-8")
    if original_cmake.count(v46.REGISTER)!=1 or REGISTER in original_cmake:
        raise ValueError("PRE448 expected CMake target registration missing/duplicate")
    added="\n    "+REGISTER
    new_cmake=original_cmake.replace(v46.REGISTER,v46.REGISTER+added,1)
    if new_cmake.replace(added,"",1)!=original_cmake:
        raise ValueError("PRE448 CMake not exactly reversible")
    cmake.write_text(new_cmake,encoding="utf-8")
    if cmake.read_text(encoding="utf-8").count(REGISTER)!=1:
        raise ValueError("PRE448 route module absent in CMake")
    STAGE="PRE448_NATIVE_STAGING_COMPLETE"
    return {"v47_previous_callbacks":enabled,
            "v47_pre429_native_module":previous["native_module"],
            "route_preview_sha256":preview["preview_sha256"],
            "route_native_module":MODULE,"route_native_module_sha256":sha(module.read_bytes()),
            "route_feature_default_off":True,"route_feature_on_for_disposable_build_only":True,
            "route_cmake_registration_exactly_once":True,
            "no_new_guest_memory_ops_or_calls":True,
            "no_gameplay_modifications":True}

def review_native_elf(build:Path,upstream):
    global STAGE,EVIDENCE
    STAGE="PRE448_LINKED_ELF_AND_SHARDS_AUDIT"
    outputs=upstream(build)
    if len(outputs)!=1:raise ValueError("PRE448 expected unique game libmain.so")
    so=outputs[0]
    cc=build/"compile_commands.json"
    if not cc.is_file():raise ValueError("PRE448 compile_commands.json absent")
    commands=json.loads(cc.read_text(encoding="utf-8"))
    checked={}
    for filename,symbol in EXPECTED_SHARDS.items():
        matches=[x for x in commands if Path(x.get("file","")).name==filename]
        if len(matches)!=1:raise ValueError("PRE448 guest compilation not unique: "+filename)
        args=matches[0].get("arguments") or shlex.split(matches[0].get("command",""))
        if filename=="nfsmw_recomp.28.cpp" and FEATURE_DEFINE not in args:
            raise ValueError("PRE448 route feature absent in guest compile command")
        checked[filename]={"compiled_once":True,"symbol_expected":symbol,
                            "route_macro_passed":FEATURE_DEFINE in args}
    ndk=find_ndk()["ndk"]
    nm=ndk/"toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-nm"
    run=subprocess.run([str(nm),"-D","--defined-only",str(so)],capture_output=True,
                      text=True,timeout=95,env=native.clean_env())
    if run.returncode:raise ValueError("PRE448 cannot inspect ARM64 symbol table")
    symbols={}
    for name in EXPECTED_CALLBACKS:
        match=re.findall(r"(?m)^[0-9a-fA-F]+\s+[Tt]\s+"+re.escape(name)+r"$",run.stdout)
        symbols[name]=len(match)
        if len(match)!=1:raise ValueError("PRE448 missing or duplicate native callback "+name)
    raw=so.read_bytes()
    markers={}
    for marker in MARKERS:
        key=marker.decode("ascii")
        markers[key]=marker in raw
        if not markers[key]:raise ValueError("PRE448 missing native diagnostic/Nitro marker "+key)
    EVIDENCE={"all_callbacks_defined_once":True,"callback_definition_counts":symbols,
              "all_expected_markers_present":True,"native_markers":markers,
              "guest_compile_commands":checked,
              "arm64_elf_sha256":sha(raw)}
    STAGE="PRE448_NATIVE_VALIDATED"
    return outputs

def audit():
    global STAGE,EVIDENCE
    before=(native.replay_v37,native.stage_logger,native.find_outputs,
            native.FEATURE,native.CALLBACK,native.PAL_FILENAME)
    original_outputs=native.find_outputs
    try:
        STAGE="PRE448_REPLAY_FULL_V46_BASE"
        native.replay_v37=v46.replay_v46_sources
        native.stage_logger=stage_all_callbacks
        native.find_outputs=lambda b:review_native_elf(b,original_outputs)
        native.FEATURE=p447.FLAG
        native.CALLBACK=p447.NAME
        native.PAL_FILENAME=p447.FILES["lookup"][0]
        result=native.audit(Path(__file__).resolve().parents[2])
        result["stage"]="PRE448_V47_EQUIVALENT_BMW_ZERO_ROUTE_ARM64_NO_APK"
        result["status"]="AUDIT_OK" if (
            result.get("status")=="AUDIT_OK" and
            EVIDENCE.get("all_callbacks_defined_once") and
            EVIDENCE.get("all_expected_markers_present")
        ) else "NEEDS_REVIEW"
        result["pre448_elf_evidence"]=EVIDENCE
        result["replayed_v47_equivalent_source_chain"]=True
        result["exact_v47_signed_apk_binary_proven"]=False
        result["new_apk_generated"]=False
        result["signing_accessed"]=False
        result["save_accessed"]=False
        result["device_gameplay_tested"]=False
        return result
    finally:
        (native.replay_v37,native.stage_logger,native.find_outputs,
         native.FEATURE,native.CALLBACK,native.PAL_FILENAME)=before

def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True);a=p.parse_args()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    try:result=audit()
    except Exception as e:
        result={"status":"FAILED","phase":STAGE,"error_type":type(e).__name__,
                "reason":str(e)[:190] if str(e).startswith("PRE448 ") else "Native gate failed",
                "new_apk_generated":False,"signing_accessed":False,"save_accessed":False}
    result["run_id"]=a.run_id;result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("PRE448_STATUS",result["status"])
    print("PRE448_PHASE",STAGE)
    print("PRE448_ERROR_TYPE",result.get("error_type","none"))
    print("PRE448_REASON",result.get("reason","none"))
    print("PRE448_CMAKE_CONFIG",result.get("cmake_configure",{}).get("ok"))
    print("PRE448_NATIVE_LINK",result.get("production_native_build",{}).get("ok"))
    print("PRE448_ELF_ARM64",result.get("linked_library",{}).get("arm64_elf"))
    print("PRE448_ALL_THREE_CALLBACKS",result.get("pre448_elf_evidence",{}).get("callback_definition_counts"))
    print("PRE448_ALL_MARKERS",result.get("pre448_elf_evidence",{}).get("all_expected_markers_present"))
    print("PRE448_NO_APK",True)
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":raise SystemExit(main())
