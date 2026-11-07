#!/usr/bin/env python3
"""PRE317 isolated source staging and genuine C++ callback compilation.
No PRE99 download, no Android build, no signer/saves/game guest code.
"""
from pathlib import Path
import sys,tempfile,subprocess,json
from pre247_pal_meter_passive_probe_patch import CPP_TEXT
from pre317_nitro_cycle_staging import inject,HEADER,HEADER_NAME
OUT=Path("/tmp/nfsmw-pre317/PRE317_NITRO_CYCLE_STAGING_MOCK.json")
MOCK=r"""#pragma once
#include <atomic>
extern std::atomic<unsigned> mock_log_count;
template<class... A> void mock_log(const char*,A&&...) noexcept {
  mock_log_count.fetch_add(1,std::memory_order_relaxed);
}
#define REXLOG_INFO(...) mock_log(__VA_ARGS__)
"""
MAIN=r"""#include <atomic>
#include <cstdint>
#include <iostream>
std::atomic<unsigned> mock_log_count{0};
extern "C" void NFSMW_PRE247_TRACE_METER(std::uint32_t,std::uint32_t,std::uint32_t) noexcept;
static std::uint32_t bits(float f) noexcept {
 std::uint32_t u;__builtin_memcpy(&u,&f,4);return u;
}
int main(){
 for(int n=0;n<=180;n++)
  NFSMW_PRE247_TRACE_METER(1,0x12340000,bits(float(180-n)/180.f));
 for(int n=0;n<=180;n++)
  NFSMW_PRE247_TRACE_METER(3,0x12340000,bits(float(n)/180.f));
 // 12 original PRE247 logs/site preserved; extra bounded PRE316 events.
 auto records=mock_log_count.load();
 if (records<30 || records>140) return 21;
 for(int i=0;i<40000;i++)
  NFSMW_PRE247_TRACE_METER(1,0x12340000,bits(0.5f));
 if(mock_log_count.load()>140) return 22;
 NFSMW_PRE247_TRACE_METER(0,0,0);
 NFSMW_PRE247_TRACE_METER(9,0,0);
 std::cout<<"PRE317_SYNTHETIC_LOG_CAP_OK "<<mock_log_count.load()<<"\n";
}
"""
def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 r={"stage":"PRE317_PASSIVE_NITRO_STAGE_CXX_MOCK","status":"FAILED",
    "apk_built":False,"signer_accessed":False,"saves_changed":False,
    "game_source_modified":False,"cheats_enabled":False}
 try:
  modified=inject(CPP_TEXT)
  with tempfile.TemporaryDirectory(prefix="nfsmw_pre317_") as t:
   p=Path(t);(p/"rex/logging").mkdir(parents=True)
   (p/"rex/logging/macros.h").write_text(MOCK)
   (p/"meter.cpp").write_text(modified)
   (p/HEADER_NAME).write_bytes(HEADER.read_bytes())
   (p/"main.cpp").write_text(MAIN)
   b=subprocess.run(["g++","-std=c++20","-Wall","-Wextra","-Werror","-pedantic",
       "-O2","-pthread","-I",str(p),
       str(p/"meter.cpp"),str(p/"main.cpp"),"-o",str(p/"runner")],
       capture_output=True,text=True,timeout=30)
   if b.returncode:raise ValueError("CXX_COMPILATION_FAILED")
   q=subprocess.run([str(p/"runner")],capture_output=True,text=True,timeout=25)
   if q.returncode or "PRE317_SYNTHETIC_LOG_CAP_OK" not in q.stdout:
    raise ValueError("SYNTHETIC_CALLBACK_FAILED")
   r["mock_output"]=q.stdout.strip()
  r["status"]="AUDIT_OK"
 except Exception as e:r["error_type"]=type(e).__name__;r["safe_failure"]=str(e)[:90]
 OUT.write_text(json.dumps(r,indent=2)+"\n")
 print("PRE317_STATUS",r["status"])
 print("PRE317_RESULT",r.get("mock_output"))
 print("PRE317_FAILURE",r.get("safe_failure"))
 return 0 if r["status"]=="AUDIT_OK" else 1
if __name__=="__main__":sys.exit(main())
