#!/usr/bin/env python3
"""PRE271: default-off passive GetMaxLevel guest return logger dry-run.

The PHP? no; this reads PRE99 PAL generated C++ only and validates an
exact reversible source transformation in memory. NO game build/patch/signing
or save edits. Logging every return does not establish the car's identity.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, tarfile, tempfile
from datetime import datetime,timezone
from pathlib import Path
from pre104_verify_backup_tar import EXPECTED_BYTES,EXPECTED_SHA256,sha_file
from pre105_read_settings_source import drive_client,download
from pre239_pal_money_probe_recipe_readonly import body_for_function

OUT=Path("/tmp/nfsmw-pre271/PRE271_BMW_GETMAXLEVEL_PASSIVE_DRYRUN.json")
SOURCE="workspace/nativo/app/generated/default/nfsmw_recomp.28.cpp"
PIN="11eec8fe3d20dc5d53e262525a4cf31021c2bbfb28e2690b6372c6c3cbea4aad"
FUNCTION="sub_823E5988"
FEATURE="NFSMW_PRE271_BMW_LEVEL_DIAGNOSTIC"
NAME="NFSMW_PRE271_TRACE_GETMAXLEVEL"
DECL='\nextern "C" void '+NAME+'(unsigned int, unsigned int, int) noexcept;\n'
INIT=(
    "\t// NFSMW_PRE271_BMW_LEVELS: preserve guest arguments in host locals only.\n"
    "#if defined("+FEATURE+") && "+FEATURE+"\n"
    "\tconst unsigned int nfsmw_pre271_vehicle_guest = ctx.r3.u32;\n"
    "\tconst unsigned int nfsmw_pre271_category = ctx.r4.u32;\n"
    "#endif\n"
)
END=(
    "#if defined("+FEATURE+") && "+FEATURE+"\n"
    "\t"+NAME+"(nfsmw_pre271_vehicle_guest, nfsmw_pre271_category, ctx.r3.s32);\n"
    "#endif\n"
)
HELPER=r'''#include <atomic>
#include <cstdint>
#include <rex/logging/macros.h>

// Bounded, passive, no guest-pointer dereference.
static std::atomic<std::uint32_t> g_pre271_count[7]{};

extern "C" void NFSMW_PRE271_TRACE_GETMAXLEVEL(
    unsigned int vehicle_guest, unsigned int category, int result) noexcept {
  if (category >= 7u) return;
  auto& n = g_pre271_count[category];
  std::uint32_t seen = n.load(std::memory_order_relaxed);
  while (seen < 8u && !n.compare_exchange_weak(
      seen, seen + 1u, std::memory_order_relaxed,
      std::memory_order_relaxed)) {}
  if (seen >= 8u) return;
  REXLOG_INFO("[NFSMW_PRE271_BMW_LEVELS] category={} vehicle_guest=0x{:08X} available={}",
              category, vehicle_guest, result);
}
'''

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()

def patch(raw:bytes):
    if sha(raw)!=PIN:raise ValueError("source SHA mismatched")
    source=raw.decode("utf-8")
    if NAME in source or "NFSMW_PRE271_BMW_LEVELS" in source:
        raise ValueError("probe already present")
    body=body_for_function(source,FUNCTION)
    prefix="\tREX_FUNC_PROLOGUE();\n"
    if body.count(prefix)!=1:raise ValueError("unexpected prologue")
    returns=body.count("\treturn;\n")
    if returns!=3:raise ValueError("expected exactly three return paths")
    for guest in ("REX_LOAD_U32(","REX_STORE_U32(","REX_LOAD_U16(","REX_STORE_U16("):
        if guest not in body:raise ValueError("unexpected missing guest accesses")
    patched_body=body.replace(prefix,prefix+INIT,1)
    patched_body=patched_body.replace("\treturn;\n",END+"\treturn;\n")
    if patched_body.count(NAME+"(")!=returns:raise ValueError("missing trace exit")
    if patched_body.replace(END,"").replace(INIT,"")!=body:
        raise ValueError("probe not reversible")
    patched=source.replace(body,patched_body,1)
    defm=re.search(r"(?m)^DEFINE_REX_FUNC\(sub_[0-9A-Fa-f]{8}\)",patched)
    if defm is None:raise ValueError("missing global function preamble")
    patched=patched[:defm.start()]+DECL+patched[defm.start():]
    if patched.count(DECL)!=1:raise ValueError("declaration not unique")
    if patched.replace(DECL,"",1).replace(patched_body,body,1)!=source:
        raise ValueError("whole source no longer reversible")
    for guest in ("REX_LOAD_U32(","REX_STORE_U32(","REX_LOAD_U16(","REX_STORE_U16(","REX_LOAD_U64(","REX_STORE_U64("):
        if source.count(guest)!=patched.count(guest):
            raise ValueError("guest memory accesses changed")
    if patched.count("DEFINE_REX_FUNC(")!=source.count("DEFINE_REX_FUNC("):
        raise ValueError("function count changed")
    return {"source_before_sha256":sha(raw),"candidate_sha256":sha(patched.encode()),
       "owner":FUNCTION,"three_return_exits_instrumented":returns,
       "guest_register_inputs_saved":True,"guest_memory_accesses_added":0,
       "source_reversible":True,"feature_flag":FEATURE,
       "feature_flag_defined_by_default":False,
       "link_module_preview_name":"nfsmw_cheats_trace_pre271.cpp",
       "log_module_sha256":sha(HELPER.encode()),
       "full_function_source_unmodified_on_disk":True}

def synthetic(root):
    cpp=root/"pre271_host_mock.cpp"
    cpp.write_text(r'''
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
struct Counter {
  std::array<unsigned,7> c{};
  unsigned report(unsigned cat,int lvl) noexcept {
    if(cat>=7 || c[cat]>=8)return 0;
    ++c[cat];
    return lvl>=0?1u:1u;
  }
};
int main(){
  Counter v;
  unsigned valid=0;
  for(unsigned cat=0;cat<7;++cat) {
    for(int i=0;i<15;++i)valid+=v.report(cat,i);
    assert(v.c[cat]==8);
  }
  for(unsigned i=7;i<20;++i)assert(v.report(i,0)==0);
  assert(valid==56);
  std::cout<<"PRE271_PASSIVE_LOG_BOUNDED_56_OK\n";
}
''',encoding="utf-8")
    exe=root/"pre271_mock"
    cc=subprocess.run(["g++","-std=c++17","-O1","-Wall","-Wextra","-Werror",
                       str(cpp),"-o",str(exe)],capture_output=True,text=True,timeout=30)
    if cc.returncode:return {"ok":False,"phase":"compile","diagnostic":cc.stderr[-700:]}
    rr=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
    return {"ok":rr.returncode==0,"result":rr.stdout.strip(),
            "count_per_category_cap":8,"total_bounded_messages":56,
            "game_code_compiled":False}

def audit():
    with tempfile.TemporaryDirectory(prefix="pre271_") as d:
        root=Path(d)
        tarpath=root/"pre99.tar.gz"
        download(drive_client(),tarpath)
        digest,_,size=sha_file(tarpath)
        if digest!=EXPECTED_SHA256 or size!=EXPECTED_BYTES:raise ValueError("PRE99 hash mismatch")
        blob=None
        with tarfile.open(tarpath,"r:gz",errorlevel=2) as tar:
            for member in tar:
                if member.name.lstrip("./")!=SOURCE or not member.isfile():continue
                if member.size>7_000_000:raise ValueError("oversized PAL source")
                fp=tar.extractfile(member)
                if fp is None:raise ValueError("unreadable PAL source")
                blob=fp.read()
                break
        if blob is None:raise ValueError("missing source")
        result=patch(blob)
        host=synthetic(root)
        return {"stage":"PRE271_BMW_GETMAXLEVEL_PASSIVE_LOGGER_DRYRUN",
            "status":"AUDIT_OK" if host["ok"] else "NEEDS_REVIEW",
            "pre99_sha256_verified":digest,
            "patch_preview":result,
            "passive_logger_host_test":host,
            "no_runtime_levels_observed":True,
            "no_apk_built":True,"source_written_to_repo":False,"save_modified":False,
            "signer_accessed":False,
            "limitations":[
              "Logger is OFF by default; no executable game source was patched",
              "The GetMaxLevel helper may not run for BMW when Performance menu is hidden",
              "Logged guest vehicle pointer is not a car model and requires independent correlation",
              "A separate future build must register logging module in CMake and link correctly",
              "Host mock validates rate cap but does not exercise Android rendering, callbacks, or BMW physics",
              "Do not announce actual BMW package levels or remove HeroCar block without observed data",
            ]}
def main():
    p=argparse.ArgumentParser();p.add_argument("--run-id",required=True)
    a=p.parse_args()
    if not a.run_id.isdecimal():raise ValueError("invalid run-id")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"stage":"PRE271_BMW_GETMAXLEVEL_PASSIVE_LOGGER_DRYRUN",
            "status":"FAILED","no_apk_built":True,"source_written_to_repo":False}
    try:result=audit()
    except Exception as e:result["error_type"]=type(e).__name__
    result["run_id"]=a.run_id
    result["utc"]=datetime.now(timezone.utc).isoformat()
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PRE271_STATUS",result["status"])
    print("PRE271_EXITS",result.get("patch_preview",{}).get("three_return_exits_instrumented"))
    print("PRE271_HOST",result.get("passive_logger_host_test",{}).get("result"))
    print("PRE271_REAL_BMW_VALUES_KNOWN",False)
    if result["status"]!="AUDIT_OK":print("PRE271_ERROR",result.get("error_type"))
    return 0 if result["status"]=="AUDIT_OK" else 1
if __name__=="__main__":
    sys.exit(main())
